"""Build inside paper/build. Only validated outputs acquire their public names."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import yaml
from lxml import etree as ET
from PIL import Image
from word import apply

BUILD = Path("build").resolve()
PDF = "CP2_Kretov_Adaptation.pdf"


def run(*args, capture=False, **kwargs):
    print("+", *map(str, args), flush=True)
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE if capture else None,
                          **kwargs).stdout


def file(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Missing input: {path}")
    return path


def digest(p):
    return hashlib.sha256(p.read_bytes()).digest()


def panels(paths, stage):
    images = []
    for i, path in enumerate(paths):
        prefix = stage / f"panel-{i}"
        if not re.search(r"^Pages:\s+1$", run("pdfinfo", file(path), capture=True), re.M):
            raise ValueError(f"Expected a one-page panel: {path}")
        run("pdftoppm", "-r", "300", "-png", "-singlefile", path, prefix)
        with Image.open(prefix.with_suffix(".png")) as img:
            images.append(img.convert("RGB"))
    joined = Image.new("RGB", (sum(i.width for i in images), max(i.height for i in images)), "white")
    offset = 0
    for img in images:
        joined.paste(img, (offset, 0))
        offset += img.width
    joined.save(stage / "signing-panels.png")


def walk(o):
    if isinstance(o, list):
        for item in o:
            yield from walk(item)
    elif isinstance(o, dict):
        yield o
        for item in o.values():
            yield from walk(item)


def audit(pdf, stage, config, expected_numbers):
    bbox = ET.fromstring(subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"]))
    pages = bbox.xpath("//*[local-name()='page']")
    if not pages:
        raise ValueError("Empty PDF")
    all_text = []
    for i, page in enumerate(pages, 1):
        words = page.xpath(".//*[local-name()='word']")
        if not words:
            raise ValueError(f"Empty page {i}")
        for word in words:
            for low, high, dim in [("xMin","xMax","width"),("yMin","yMax","height")]:
                if float(word.get(low)) < 0 or float(word.get(high)) > float(page.get(dim)) + 0.1:
                    raise ValueError(f"Text outside page {i}: {word.text}")
        all_text.append(" ".join(w.text or "" for w in words))
    # Visible ink against the physical page edge includes raster/vector graphics.
    run("pdftoppm", "-r", "85", "-gray", "-png", pdf, stage / "page")
    for path in stage.glob("page-*.png"):
        with Image.open(path) as img:
            mask = img.convert("L").point(lambda x: 255 if x < 192 else 0)
            box = mask.getbbox()
            if not box or min(box[0], box[1], img.width-box[2], img.height-box[3]) < 4:
                raise ValueError(f"Possible clipping: {path.name}")
    extracted = " ".join(all_text)
    missing = [n for n in expected_numbers if n not in extracted]
    if missing:
        raise ValueError("Table values missing in PDF: " + ", ".join(sorted(missing)))
    if "\ufffd" in extracted or re.search(r'SQI-LAYOUT-|\?\?\s*\[', extracted):
        raise ValueError("Unresolved layout marker, glyph or reference in PDF")
    print(f"PDF: {len(pages)} pages. Page edges and {len(expected_numbers)} distinct decimal table values checked.")
    # A body spanning 3–6 partially filled pages may need a manual count.
    start = next((i for i,t in enumerate(all_text) if "Introduction" in t), None)
    end = next((i for i,t in enumerate(all_text) if re.search(r"\bReferences\b", t, re.I)), None)
    if start is not None and end is not None:
        span = end-start+1
        print(f"Body spans pages {start+1}–{end+1} including partial pages (target 3–6 body pages).")
        if span < 3 or span > 8:
            print("WARNING: body outside the organizer's 3–6 page range. Review without shortening automatically.")


def build():
    cfg = yaml.safe_load(file("manuscript.yaml").read_text())
    sources = cfg["sources"]
    if not isinstance(sources, list) or not sources or len(set(sources)) != len(sources):
        raise ValueError("sources must be an ordered, nonempty list with unique paths")
    files = list(map(file, [*sources, cfg["template"], cfg["bibliography"], cfg["csl"], *cfg["panels"]]))
    watched = {p: digest(p) for p in set(files) | {p for p in Path(".").rglob("*")
               if p.is_file() and "build" not in p.parts and "__pycache__" not in p.parts}}
    md = "\n\n".join(p.read_text() for p in map(Path, sources))
    if cfg["authors"] and (len(cfg["authors"]) != 2 or any(
            not isinstance(a, dict) or not all(isinstance(a.get(k), str) and a[k].strip()
            for k in ("name", "department", "organization", "location", "contact")) for a in cfg["authors"])):
        raise ValueError("Supply five nonempty author fields per record, or leave authors: [] for a proof.")
    if not cfg["authors"] or not cfg["keywords"]:
        print("PRELIMINARY: author metadata or keywords pending.")
    tools = ["pandoc", "soffice", "pdfinfo", "pdftoppm", "pdftotext", "fc-match"]
    missing = [tool for tool in tools if not shutil.which(tool)]
    if missing:
        raise ValueError("Install missing executables: " + ", ".join(missing) + " (see BUILD.md)")
    with TemporaryDirectory(dir=BUILD) as tmp:
        stage = Path(tmp)
        run("pandoc", "--version")
        run("soffice", "--version")
        if "times new roman" not in run("fc-match", "-f", "%{family}", "Times New Roman", capture=True).lower():
            print("PRELIMINARY: Times New Roman unavailable; font substitution changes pagination.")
        panels(cfg["panels"], stage)
        image_assets = {}
        reader = "markdown-smart"  # preserve quotes, minus signs, and literal dots
        ast = json.loads(run("pandoc", "-f", reader, "-t", "json", capture=True, input=md))
        keys = [entry["id"] for entry in json.loads(run("pandoc", "--fail-if-warnings", "-f", "biblatex", "-t", "csljson",
                                                        cfg["bibliography"], capture=True))]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate bibliography keys")
        anchors, links, values = set(), [], set()
        for obj in walk(ast):
            kind, content = obj.get("t"), obj.get("c")
            if isinstance(content, list) and content and isinstance(content[0], list) and len(content[0]) == 3 and isinstance(content[0][0], str):
                ident = content[0][0]
                if ident:
                    if ident in anchors:
                        raise ValueError(f"Duplicate identifier: {ident}")
                    anchors.add(ident)
            if kind == "Table":
                values.update(n["c"] for n in walk(content) if n.get("t") == "Str"
                              and re.fullmatch(r"\d+\.\d+", n["c"]))
            if kind == "Cite":
                for cite in content[0]:
                    if cite["citationId"] not in keys:
                        raise ValueError("Missing bibliography key: " + cite["citationId"])
            if kind in ("Link", "Image"):
                target = content[2][0]
                if target.startswith("#"):
                    links.append(target[1:])
                elif kind == "Image":
                    path = stage/"signing-panels.png" if target == "build/signing-panels.png" else file(target)
                    if path.suffix.lower() == ".pdf":
                        if not re.search(r"^Pages:\s+1$", run("pdfinfo", path, capture=True), re.M):
                            raise ValueError(f"Figure must be one PDF page: {path}")
                        prefix = stage / ("figure-" + digest(path).hex())
                        watched[path] = digest(path)
                        run("pdftoppm", "-singlefile", "-png", "-r", "300", path, prefix)
                        path = prefix.with_suffix(".png")
                        image_assets[path] = "build/" + path.name
                    content[2][0] = str(path.resolve())
                elif not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    file(target)
                    content[2][0] = os.path.relpath(Path(target).resolve(), BUILD)
        if set(links) - anchors:
            raise ValueError("Missing cross-reference targets: " + ", ".join(set(links)-anchors))
        converted = stage/"reference"
        converted.mkdir()
        office = ["soffice", f"-env:UserInstallation={(stage/'profile').as_uri()}", "--headless"]
        run(*office, "--convert-to", "docx:Office Open XML Text", "--outdir", converted, Path(cfg["template"]).resolve())
        reference = file(converted / Path(cfg["template"]).name)
        opts = ["pandoc", "-f", "json", "--fail-if-warnings", "--lua-filter=tools/layout.lua", "--citeproc",
                "--bibliography", cfg["bibliography"], "--csl", cfg["csl"], "-M", "reference-section-title=References"]
        data = json.dumps(ast)
        tex_data = data.replace(str(stage/"signing-panels.png"), "build/signing-panels.png")
        for asset, relative in image_assets.items():
            tex_data = tex_data.replace(str(asset), relative)
        run(*opts, "-t", "latex", "-s", "-o", stage/"manuscript.tex", input=tex_data)
        run(*opts, "--reference-doc", reference, "-o", stage/"body.docx", input=data)
        apply(reference, stage/"body.docx", stage/"manuscript.docx", cfg)
        run(*office, "--convert-to", "pdf:writer_pdf_Export", "--outdir", stage, stage/"manuscript.docx")
        audit(file(stage/"manuscript.pdf"), stage, cfg, values)
        if any(digest(p) != before for p,before in watched.items()):
            raise ValueError("An input changed during the build; retry.")
        for asset in image_assets:
            asset.replace(BUILD / asset.name)
        for src,dst in [("signing-panels.png","signing-panels.png"),("manuscript.tex","manuscript.tex"),
                        ("manuscript.docx","manuscript.docx"),("manuscript.pdf",PDF)]:
            (stage/src).replace(BUILD/dst)


if __name__ == "__main__":
    try:
        build()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, StopIteration) as exc:
        sys.exit(f"Build failed: {exc}. Previous successful outputs, if any, are retained.")
