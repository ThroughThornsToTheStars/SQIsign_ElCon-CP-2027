"""Apply the organizer's named styles and section geometry to Pandoc output."""
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def node(name, **attrs):
    return E.Element(W + name, {W + k: str(v) for k, v in attrs.items()})


def props(p):
    pr = p.find(W + "pPr")
    if pr is None:
        pr = node("pPr")
        p.insert(0, pr)
    return pr


def set_style(p, style):
    pr = props(p)
    for current in pr.findall(W + "pStyle"):
        pr.remove(current)
    pr.insert(0, node("pStyle", val=style))


def text(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def author_row(authors):
    if not authors:
        authors = [dict(name="PRELIMINARY — author details pending", department="", organization="",
                        location="", contact="")] * 2
    if len(authors) != 2:
        raise ValueError("This submission requires two author records")
    table = node("tbl")
    settings = node("tblPr")
    settings.append(node("tblW", type="pct", w=5000))
    table.append(settings)
    grid = node("tblGrid")
    grid.extend([node("gridCol", w=5050), node("gridCol", w=5050)])
    table.append(grid)
    row = node("tr")
    table.append(row)
    for author in authors:
        cell = node("tc")
        row.append(cell)
        p = node("p")
        cell.append(p)
        props(p).append(node("jc", val="center"))
        for field in ("name", "department", "organization", "location", "contact"):
            if not author.get(field):
                continue
            r = node("r")
            fmt = node("rPr")
            fmt.append(node("rFonts", ascii="Times New Roman", hAnsi="Times New Roman"))
            if field in ("department", "organization"):
                fmt.append(node("i"))
            fmt.append(node("sz", val=18))
            r.append(fmt)
            if field != "name":
                r.append(node("br"))
            t = node("t")
            t.text = author[field]
            r.append(t)
            p.append(r)
    return table


def fit_table(table, width):
    """Fit simple pipe tables at the native font size, including the profile column."""
    grid = table.find(W+"tblGrid")
    rows = table.findall(W+"tr")
    if grid is None or not rows:
        return
    cols = grid.findall(W+"gridCol")
    cells = [r.findall(W+"tc") for r in rows]
    if not cols or any(len(row) != len(cols) for row in cells):
        return  # retain Pandoc's grid for spanned cells
    weights = [max(4, max(len(token) for cell in col for token in (text(cell).split() or [""]))) + 2
               for col in zip(*cells)]
    for i, column in enumerate(zip(*cells)):
        if text(column[0]).startswith("RSS / HWM"):
            weights[i] = max(weights[i], len("3192 / 3212") + 2)
    widths = [round(width*w/sum(weights)) for w in weights]
    widths[-1] += width - sum(widths)
    for col, value in zip(cols, widths):
        col.set(W+"w", str(value))
    for row in cells:
        for cell, value in zip(row, widths):
            prop = cell.find(W+"tcPr")
            if prop is None:
                prop = node("tcPr")
                cell.insert(0, prop)
            cell_width = prop.find(W+"tcW")
            if cell_width is None:
                cell_width = node("tcW")
                prop.insert(0, cell_width)
            cell_width.set(W+"type", "dxa")
            cell_width.set(W+"w", str(value))


def apply(reference, generated, output, config):
    with ZipFile(reference) as ref, ZipFile(generated) as src:
        original = E.fromstring(ref.read("word/document.xml"))
        styles = E.fromstring(src.read("word/styles.xml"))
        ids = {s.find(W+"name").get(W+"val").lower(): s.get(W+"styleId")
               for s in styles.findall(W+"style") if s.find(W+"name") is not None}
        sections = original.findall(".//" + W + "sectPr")
        body_section = next(s for s in sections if s.find(W+"cols") is not None
                            and s.find(W+"cols").get(W+"num") == "2")

        def geometry(base, columns):
            section = deepcopy(base)
            for child in list(section):
                if E.QName(child).localname in {"headerReference", "footerReference", "printerSettings", "titlePg"}:
                    section.remove(child)
            cols = section.find(W+"cols")
            if cols is None:
                cols = node("cols")
                after = next((e for e in section if E.QName(e).localname in {"formProt", "vAlign", "noEndnote", "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid", "sectPrChange"}), None)
                if after is None:
                    section.append(cols)
                else:
                    after.addprevious(cols)
            for child in list(cols):
                cols.remove(child)
            cols.set(W+"num", str(columns))
            cols.set(W+"equalWidth", "1")
            typ = section.find(W+"type")
            if typ is None:
                typ = node("type")
                section.insert(0, typ)
            typ.set(W+"val", "continuous")
            return section

        def boundary(section):
            p = node("p")
            pr = props(p)
            pr.append(node("spacing", before=0, after=0, line=20, lineRule="exact"))
            pr.append(section)
            return p

        doc = E.fromstring(src.read("word/document.xml"))
        body = doc.find(W+"body")
        old = body.find(W+"sectPr")
        if old is not None:
            body.remove(old)
        columns = 2
        size = body_section.find(W+"pgSz")
        mar = body_section.find(W+"pgMar")
        full_width = int(size.get(W+"w")) - int(mar.get(W+"left")) - int(mar.get(W+"right"))
        column_width = (full_width - int(body_section.find(W+"cols").get(W+"space", "360"))) // 2
        titled = False
        subsection = 0
        for p in list(body):
            if p.tag == W+"tbl":
                fit_table(p, full_width if columns == 1 else column_width)
            if p.tag != W+"p":
                continue
            val = text(p)
            style = p.find(W+"pPr/"+W+"pStyle")
            current = style.get(W+"val", "") if style is not None else ""
            if not titled and val:
                set_style(p, ids["paper title"])
                row = author_row(config["authors"])
                p.addnext(row)
                row.addnext(boundary(geometry(sections[0], 1)))
                titled = True
            elif val in ("SQI-LAYOUT-WIDE", "SQI-LAYOUT-END"):
                target = 1 if val.endswith("WIDE") else 2
                if columns == target:
                    raise ValueError("Unbalanced wide section")
                body.replace(p, boundary(geometry(body_section, columns)))
                columns = target
            elif val.startswith("Abstract—"):
                set_style(p, ids["abstract"])
                if config["keywords"]:
                    keywords = node("p")
                    set_style(keywords, ids["keywords"])
                    r = node("r")
                    r.append(node("t"))
                    r[0].text = "Keywords—" + ", ".join(config["keywords"])
                    keywords.append(r)
                    p.addnext(keywords)
            elif current == ids.get("equation"):
                width = full_width if columns == 1 else column_width
                pr = props(p)
                jc = pr.find(W+"jc")
                if jc is None:
                    jc = node("jc")
                    pr.append(jc)
                jc.set(W+"val", "left")
                tabs = node("tabs")
                eq_style = next(st for st in styles.findall(W+"style") if st.get(W+"styleId") == current)
                for tab in eq_style.findall(W+"pPr/"+W+"tabs/"+W+"tab"):
                    if tab.get(W+"pos") != str(width):
                        tabs.append(node("tab", val="clear", pos=tab.get(W+"pos")))
                tabs.append(node("tab", val="right", pos=width))
                for run in p.iter(W+"r"):
                    fmt = run.find(W+"rPr")
                    if fmt is None:
                        fmt = node("rPr")
                        run.insert(0, fmt)
                    fmt.append(node("rFonts", ascii="Times New Roman", hAnsi="Times New Roman", cs="Times New Roman"))
                props(p).append(tabs)
                for run in reversed(p.findall(W+"r")):
                    if text(run).strip().startswith("("):
                        run.insert(1 if run.find(W+"rPr") is not None else 0, node("tab"))
                        break
            elif val == "References":
                set_style(p, ids["heading 5"])
            elif current == ids.get("heading 2") or current == "Heading2":
                set_style(p, ids["heading 1"])
                subsection = 0
            elif current == ids.get("heading 3") or current == "Heading3":
                set_style(p, ids["heading 2"])
                first_text = next(p.iter(W+"t"))
                first_text.text = chr(ord("A") + subsection) + ".  " + (first_text.text or "")
                subsection += 1
            elif current in ("Caption", "ImageCaption", "TableCaption") or val.startswith(("Fig. ", "Table ")):
                set_style(p, ids["figure caption" if val.startswith("Fig.") else "table head"])
            elif current == "Bibliography":
                set_style(p, ids["references"])
            elif current in ("", "BodyText", "FirstParagraph") and val:
                set_style(p, ids["body text"])
            # Template headings, captions and references have their own list
            # numbering. The source/CSL already supplies the visible numbers.
            if (current in ("Heading3", ids.get("heading 3")) or val.startswith(("Fig. ", "Table ", "[")) or
                (current in ("Heading2", ids.get("heading 2")) and val.split(". ")[0] in
                 ("I","II","III","IV","V","VI","VII","VIII","IX","X"))):
                pr = props(p)
                num = pr.find(W+"numPr")
                if num is None:
                    num = node("numPr")
                    idx = 1 if pr.find(W+"pStyle") is not None else 0
                    pr.insert(idx, num)
                for child in list(num):
                    num.remove(child)
                num.append(node("numId", val=0))
        if columns != 2 or not titled:
            raise ValueError("Incomplete Word layout")
        for p in body.findall(".//"+W+"tc/"+W+"p"):
            if p.find(".//"+W+"sz") is None:
                set_style(p, ids["table copy"])
        targets = {e.get(W+"name") for e in body.iter(W+"bookmarkStart")}
        links = {e.get(W+"anchor") for e in body.iter(W+"hyperlink") if e.get(W+"anchor")}
        if links - targets:
            raise ValueError("Unresolved Word bookmark(s): " + ", ".join(sorted(links-targets)))
        body.append(geometry(body_section, 2))
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as out:
            for name in src.namelist():
                data = E.tostring(doc, encoding="UTF-8", xml_declaration=True) if name == "word/document.xml" else src.read(name)
                out.writestr(name, data)
