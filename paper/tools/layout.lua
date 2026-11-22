-- Keep scientific content in the AST. Only labels and Word section boundaries
-- are added here. Traverse links after collecting targets (forward references).
local counts = {fig=0, tbl=0, eq=0}
local labels = {}
local function roman(n)
  local s = ""
  for _, pair in ipairs({{1000,"M"},{900,"CM"},{500,"D"},{400,"CD"},
    {100,"C"},{90,"XC"},{50,"L"},{40,"XL"},{10,"X"},{9,"IX"},{5,"V"},{4,"IV"},{1,"I"}}) do
    while n >= pair[1] do s = s .. pair[2]; n = n - pair[1] end
  end
  return s
end
local function label(id, kind)
  if id == "" then error("Missing identifier for " .. kind) end
  if labels[id] then error("Duplicate identifier: " .. id) end
  counts[kind] = counts[kind] + 1
  local n = counts[kind]
  labels[id] = ({tbl="Table " .. roman(n), fig="Fig. " .. n, eq="(" .. n .. ")"})[kind]
  return labels[id]
end
local function prefix(cap, value)
  local block = cap.long[1]
  if not block or not block.content then error("Caption required: " .. value) end
  block.content:insert(1, pandoc.Space())
  block.content:insert(1, pandoc.Str(value .. "."))
  cap.long[1] = block
  return cap
end
local function marker(name)
  return pandoc.Para({pandoc.Str("SQI-LAYOUT-" .. name)})
end
function Pandoc(doc)
  doc = doc:walk({
    Figure = function(f)
      f.caption = prefix(f.caption, label(f.identifier,"fig"))
      return f
    end,
    Div = function(d)
      if d.identifier:match("^tbl:") then
        local t = d.content[1]
        if t.t ~= "Table" then error("Expected a captioned Markdown table") end
        t.caption = prefix(t.caption, label(d.identifier,"tbl"))
        d.content[1] = t
      elseif d.classes:includes("equation") then
        local p = d.content[1]
        if #d.content ~= 1 or p.t ~= "Para" or #p.content == 0 then
          error("Expected one display formula in " .. d.identifier)
        end
        p.content:insert(pandoc.Space())
        local number = pandoc.Str(label(d.identifier,"eq"))
        if FORMAT == "docx" then
          number = pandoc.Span({number}, {["custom-style"]="Equation Number"})
        end
        p.content:insert(number)
        d.content[1] = p
        d.attributes["custom-style"] = "equation"
      end
      if d.classes:includes("newpage") and FORMAT == "docx" then
        d.content:insert(1,marker("PAGE"))
      end
      if d.classes:includes("wide") and FORMAT == "docx" then
        d.content:insert(1,marker("WIDE"))
        d.content:insert(marker("END"))
      end
      return d
    end
  })
  return doc:walk({Link=function(l)
    if l.target:match("^#") then
      local id = l.target:sub(2)
      if labels[id] and pandoc.utils.stringify(l.content) == "#" then
        l.content = {pandoc.Str(labels[id])}
      end
    end
    return l
  end})
end
