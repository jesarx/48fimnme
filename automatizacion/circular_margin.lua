-- circular_margin.lua

local pagebreak_sections = {
  ["personas compositoras"] = true,
  ["intérpretes"] = true,
  ["interpretes"] = true,
  ["dirección y solistas"] = true,
  ["direccion y solistas"] = true
}

local function normalize_title(text)
  return pandoc.text.lower(text):gsub("^%s*(.-)%s*$", "%1")
end

local function urldecode(s)
  if not s then return s end
  s = s:gsub('+', ' ')
  s = s:gsub('%%(%x%x)', function(h)
    return string.char(tonumber(h, 16))
  end)
  return s
end

-- Detecta si el bloque es una imagen que solicita plana completa
local function get_fullpage_image_src(block)
  if block.t == "Para" and #block.content == 1 and block.content[1].t == "Image" then
    local caption_text = pandoc.utils.stringify(block.content[1].caption)
    if caption_text:lower():match("^%s*plana%s*$") then
      return block.content[1].src
    end
  end
  return nil
end

-- Detecta si el bloque es una imagen circular regular
local function get_biography_image_src(block)
  if block.t == "Para" and #block.content == 1 and block.content[1].t == "Image" then
    local caption_text = pandoc.utils.stringify(block.content[1].caption)
    if not caption_text:lower():match("^%s*plana%s*$") then
      return block.content[1].src
    end
  end
  return nil
end

-- Reemplazo de \latex o \LaTeX en texto plano por el macro oficial de LaTeX
local function replace_latex_macros(inlines)
  local new_inlines = {}
  for _, inline in ipairs(inlines) do
    if inline.t == "Str" then
      if inline.text == "\\latex" or inline.text == "\\LaTeX" then
        table.insert(new_inlines, pandoc.RawInline('latex', '\\LaTeX{}'))
      else
        table.insert(new_inlines, inline)
      end
    else
      table.insert(new_inlines, inline)
    end
  end
  return new_inlines
end

function Pandoc(doc)
  local new_blocks = {}
  local i = 1
  local n = #doc.blocks

  while i <= n do
    local block = doc.blocks[i]

    -- 1. Gestión de encabezados y saltos de página (##)
    if block.t == "Header" then
      if block.level == 2 then
        local title = normalize_title(pandoc.utils.stringify(block))
        if pagebreak_sections[title] then
          table.insert(new_blocks, pandoc.RawBlock('latex', '\\clearpage'))
        end
      end
      block.content = replace_latex_macros(block.content)
      table.insert(new_blocks, block)
      i = i + 1

    else
      local fullpage_src = get_fullpage_image_src(block)
      local bio_src = get_biography_image_src(block)

      -- 2. Plana completa a sangre con recorte y centrado automático
      if fullpage_src then
        local img_src = urldecode(fullpage_src)
        local latex_plana = string.format(
          '\\clearpage\\thispagestyle{empty}%%\n' ..
          '\\begin{tikzpicture}[remember picture, overlay]\n' ..
          '  \\clip (current page.south west) rectangle (current page.north east);\n' ..
          '  \\node[inner sep=0pt] at (current page.center) {%%\n' ..
          '    \\includegraphics[width=\\paperwidth,height=\\paperheight,keepaspectratio=false]{"%s"}%%\n' ..
          '  };\n' ..
          '\\end{tikzpicture}%%\n' ..
          '\\clearpage',
          img_src
        )
        table.insert(new_blocks, pandoc.RawBlock('latex', latex_plana))
        i = i + 1

      -- 3. Imagen biográfica para párrafo con margen y reducción de fuente
      elseif bio_src then
        local img_src = urldecode(bio_src)
        local next_block = doc.blocks[i + 1]

        if next_block and next_block.t == "Para" then
          next_block.content = replace_latex_macros(next_block.content)
          table.insert(
            next_block.content,
            1,
            pandoc.RawInline('latex', '{\\footnotesize \\fotopar{"' .. img_src .. '"} ')
          )
          table.insert(
            next_block.content,
            pandoc.RawInline('latex', '\\par}')
          )
          table.insert(new_blocks, next_block)
          i = i + 2
        else
          table.insert(new_blocks, block)
          i = i + 1
        end

      else
        if block.content then
          block.content = replace_latex_macros(block.content)
        end
        table.insert(new_blocks, block)
        i = i + 1
      end
    end
  end

  return pandoc.Pandoc(new_blocks, doc.meta)
end
