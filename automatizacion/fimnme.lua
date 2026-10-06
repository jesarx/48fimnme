-- =============================================================================
--  fimnme.lua — Filtro Pandoc para el Programa General del FIMNME
--
--  Convierte la estructura del Markdown en las macros de la plantilla
--  automatizacion/plantilla/fimnme.latex:
--
--    \part{...}                      → página de parte
--    \portadacapitulo{VIE | NOV 6}   → página divisoria del día
--    ## VIE | NOV 6, 20:00 h - Título → encabezado de concierto (+ índice,
--                                       marcador PDF y cabecera de página)
--    ### Programa / Personas compositoras / Intérpretes ...  → secciones
--    **Compositor** + lista de obras → programa con duraciones alineadas
--    #### Nombre (País, año) + foto   → ficha biográfica con foto
--    ##### *Obra*                     → título de nota al programa
--
--  Además:
--    * genera la leyenda de estrenos (* / **) según las marcas que realmente
--      aparecen en cada programa;
--    * alimenta el índice onomástico de personas compositoras (makeindex);
--    * usa las fotos ya recortadas por automatizacion/preparar_imagenes.py;
--    * descarta los \clearpage y \vfill manuales: la paginación la decide
--      la plantilla.
-- =============================================================================

local stringify = pandoc.utils.stringify

-- -----------------------------------------------------------------------------
-- Utilidades
-- -----------------------------------------------------------------------------

local function trim(s)
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function raw(s)
  return pandoc.RawBlock("latex", s)
end

local function rawi(s)
  return pandoc.RawInline("latex", s)
end

-- Caracteres CJK: se envuelven para usar una fuente que los tenga.
local function envolver_cjk(inlines)
  return pandoc.Inlines(inlines):walk({
    Str = function(el)
      if not el.text:find("[\228-\233][\128-\191][\128-\191]") then return nil end
      local out = pandoc.List()
      local buf, cjk = "", false
      for _, c in utf8.codes(el.text) do
        local ch = utf8.char(c)
        local es = c >= 0x2E80 and c <= 0x9FFF
        if es ~= cjk and buf ~= "" then
          out:insert(cjk and rawi("\\textocjk{" .. buf .. "}") or pandoc.Str(buf))
          buf = ""
        end
        cjk = es
        buf = buf .. ch
      end
      if buf ~= "" then
        out:insert(cjk and rawi("\\textocjk{" .. buf .. "}") or pandoc.Str(buf))
      end
      return out
    end,
  })
end

-- Inlines → LaTeX (los caracteres CJK siempre van con su fuente)
local function latex(inlines)
  if inlines == nil or #inlines == 0 then return "" end
  local doc = pandoc.Pandoc({ pandoc.Plain(envolver_cjk(inlines)) })
  local s = pandoc.write(doc, "latex", { wrap_text = "wrap-none" })
  return trim(s)
end

-- Bloques → LaTeX
local function latex_blocks(blocks)
  local doc = pandoc.Pandoc(blocks):walk({ Inlines = function(il) return envolver_cjk(il) end })
  local s = pandoc.write(doc, "latex", { wrap_text = "wrap-none" })
  return trim(s)
end

-- Texto plano seguro para LaTeX (para cabeceras e índices)
local function escape(s)
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("([#%%&_{}%$])", "\\%1")
  s = s:gsub("~", "\\textasciitilde{}")
  s = s:gsub("%^", "\\textasciicircum{}")
  return s
end

local function urldecode(s)
  if not s then return s end
  return (s:gsub("%%(%x%x)", function(h) return string.char(tonumber(h, 16)) end))
end

local function strip_trailing_space(inlines)
  while #inlines > 0 do
    local t = inlines[#inlines].t
    if t == "Space" or t == "SoftBreak" or t == "LineBreak" then
      inlines:remove(#inlines)
    else
      break
    end
  end
  while #inlines > 0 do
    local t = inlines[1].t
    if t == "Space" or t == "SoftBreak" or t == "LineBreak" then
      inlines:remove(1)
    else
      break
    end
  end
  return inlines
end

-- Quita acentos y pasa a minúsculas (clave de orden del índice)
local ACENTOS = {
  ["á"]="a", ["à"]="a", ["â"]="a", ["ä"]="a", ["ã"]="a", ["å"]="a",
  ["é"]="e", ["è"]="e", ["ê"]="e", ["ë"]="e",
  ["í"]="i", ["ì"]="i", ["î"]="i", ["ï"]="i",
  ["ó"]="o", ["ò"]="o", ["ô"]="o", ["ö"]="o", ["õ"]="o", ["ø"]="o",
  ["ú"]="u", ["ù"]="u", ["û"]="u", ["ü"]="u",
  ["ñ"]="n", ["ç"]="c", ["ć"]="c", ["ř"]="r", ["ß"]="ss", ["ý"]="y",
  ["Á"]="a", ["À"]="a", ["Â"]="a", ["Ä"]="a", ["Å"]="a",
  ["É"]="e", ["Í"]="i", ["Ó"]="o", ["Ö"]="o", ["Ú"]="u", ["Ü"]="u", ["Ñ"]="n",
}
local function clave_orden(s)
  s = pandoc.text.lower(s)
  for k, v in pairs(ACENTOS) do s = s:gsub(k, v) end
  s = s:gsub("[^%w ,]", "")
  return s
end


-- -----------------------------------------------------------------------------
-- Configuración
-- -----------------------------------------------------------------------------

local MANIFIESTO = {}   -- ruta original → { ruta procesada, tipo }
local function cargar_manifiesto()
  local f = io.open("build/fotos/manifiesto.tsv", "r")
  if not f then
    io.stderr:write("Aviso: falta build/fotos/manifiesto.tsv; ejecute preparar_imagenes.py\n")
    return
  end
  for linea in f:lines() do
    local orig, dest, tipo = linea:match("^([^\t]+)\t([^\t]+)\t?([^\t]*)$")
    if orig then MANIFIESTO[orig] = { dest, tipo ~= "" and tipo or "circulo" } end
  end
  f:close()
end

local NOMBRES_INDICE = {}   -- "Nombre Apellido" → "Apellido, Nombre" ("-" = omitir)
local PARTES_CON_DIVISORES = {}  -- partes con página divisoria para cada día

-- Secciones de nivel ## que se componen centradas (créditos y directorio)
local SECCIONES_CENTRADAS = { ["creditos"] = true, ["directorio"] = true }
local SECCIONES_SEDES = { ["sedes"] = true }

-- Claves normalizadas con clave_orden (sin tildes, en minúsculas)
local SECCIONES_FICHA = {
  ["personas compositoras"] = "comp",
  ["interpretes"] = "int",
  ["direccion y solistas"] = "int",
  ["solistas"] = "int",
  ["direccion"] = "int",
}

-- -----------------------------------------------------------------------------
-- Fechas:  "VIE | NOV 6, 20:00 h"  /  "VIE | NOV 13, 19:00 h / DOM | NOV 15, 12:00 h"
-- -----------------------------------------------------------------------------

local MES_NUM = { OCT = 10, NOV = 11, DIC = 12 }
local MES_NOMBRE = { OCT = "octubre", NOV = "noviembre", DIC = "diciembre" }
local DIA_NOMBRE = { LUN = "Lunes", MAR = "Martes", ["MIÉ"] = "Miércoles", JUE = "Jueves",
                     VIE = "Viernes", ["SÁB"] = "Sábado", DOM = "Domingo" }

local function divisor_dia(f, texto_indice)
  return string.format("\\divisordia{%s}{%s}{%s}{%s}",
    DIA_NOMBRE[f.dia] or f.dia, f.num, MES_NOMBRE[f.mes] or f.mes, texto_indice or "")
end

local function parse_una_fecha(s, mes_defecto)
  s = trim(s)
  local dia, mes, num, resto = s:match("^([^%s|,]+)%s*|%s*(%a+)%s+(%d+)(.*)$")
  if not dia then
    dia, num, resto = s:match("^([^%s|,]+)%s+(%d+)(.*)$")
    mes = mes_defecto
  end
  if not dia then return nil end
  local hora = resto and resto:match("(%d%d?:%d%d)")
  return { dia = dia, mes = mes or "NOV", num = num, hora = hora }
end

local function parse_fechas(s, mes_defecto)
  local fechas = {}
  for parte in (s .. "/"):gmatch("([^/]+)/") do
    local f = parse_una_fecha(parte, mes_defecto)
    if not f then return nil end
    table.insert(fechas, f)
  end
  if #fechas == 0 then return nil end
  return fechas
end

local function fecha_texto(f)        -- VIE | NOV 6
  return f.dia .. " | " .. f.mes .. " " .. f.num
end

local function fecha_hora_texto(f)   -- VIE | NOV 6 · 20:00 h
  local s = fecha_texto(f)
  if f.hora then s = s .. " · " .. f.hora .. " h" end
  return s
end

local function fecha_clave(f)
  local h = f.hora or "00:00"
  local hh, mm = h:match("(%d+):(%d+)")
  return string.format("%02d%02d%02d%02d", MES_NUM[f.mes] or 0, tonumber(f.num), tonumber(hh), tonumber(mm))
end

-- Separa "FECHA - Título" en la primera aparición de " - "
local function partir_encabezado(texto)
  local a, b = texto:find(" %- ")
  if not a then return nil, texto end
  return texto:sub(1, a - 1), texto:sub(b + 1)
end

-- Igual que partir_encabezado pero sobre inlines (para conservar cursivas)
local function partir_inlines(inlines)
  for i = 1, #inlines - 2 do
    if inlines[i].t == "Space" and inlines[i + 1].t == "Str" and inlines[i + 1].text == "-"
       and inlines[i + 2].t == "Space" then
      local izq, der = pandoc.List(), pandoc.List()
      for j = 1, i - 1 do izq:insert(inlines[j]) end
      for j = i + 3, #inlines do der:insert(inlines[j]) end
      return izq, der
    end
  end
  return nil, inlines
end

-- -----------------------------------------------------------------------------
-- Índice onomástico
-- -----------------------------------------------------------------------------

local function nombre_indice(nombre)
  nombre = trim(nombre:gsub("%s+", " "))
  local o = NOMBRES_INDICE[nombre]
  if o == "-" then return nil end
  if o then return o end
  local palabras = {}
  for w in nombre:gmatch("%S+") do table.insert(palabras, w) end
  if #palabras < 2 then return nombre end
  return palabras[#palabras] .. ", " .. table.concat(palabras, " ", 1, #palabras - 1)
end

local function escape_indice(s)
  s = escape(s)
  return (s:gsub('([!@|"])', '"%1'))
end

local function entrada_indice(nombre, sufijo)
  local display = nombre_indice(nombre)
  if not display then return "" end
  return "\\index{" .. escape_indice(clave_orden(display)) .. "@" ..
         escape_indice(display) .. (sufijo or "") .. "}"
end

-- -----------------------------------------------------------------------------
-- Programa: obras, duraciones y leyenda de estrenos
-- -----------------------------------------------------------------------------

local function es_leyenda(texto)
  local t = texto:gsub("[%*•\\]", ""):gsub("quad", ""):gsub("par", " ")
  t = trim(t:gsub("%s+", " "))
  if t == "" then return false end
  t = t:gsub("Estreno mundial", ""):gsub("Estreno en México", "")
  return trim(t) == ""
end

local function marcas_en(inlines, marcas)
  for _, el in ipairs(inlines) do
    if el.t == "Str" then
      local s = el.text
      if s:find("%*%*") then marcas.mexico = true; s = s:gsub("%*%*", "") end
      if s:find("%*") then marcas.mundial = true end
    end
  end
end

local function leyenda_latex(marcas)
  local partes = {}
  if marcas.mundial then table.insert(partes, "* Estreno mundial") end
  if marcas.mexico then table.insert(partes, "** Estreno en México") end
  if #partes == 0 then return nil end
  return "\\leyenda{" .. table.concat(partes, "\\quad ") .. "}"
end

-- Separa los inlines de un elemento de lista en título / duración / créditos
local function partir_obra(inlines)
  local titulo, dur, cred = pandoc.List(), "", pandoc.List()
  local i, n = 1, #inlines
  local encontrado = false
  while i <= n do
    local el = inlines[i]
    if el.t == "RawInline" and el.text:match("^\\hfill") then
      encontrado = true
      dur = el.text:gsub("^\\hfill%s*", "")
      i = i + 1
      -- La duración continúa en los Str siguientes (p. ej. "10" + "’")
      while i <= n and inlines[i].t == "Str" and (dur == "" or not dur:find("[’']$")) do
        dur = dur .. inlines[i].text
        i = i + 1
      end
      -- Resto: créditos
      for j = i, n do cred:insert(inlines[j]) end
      break
    else
      titulo:insert(el)
    end
    i = i + 1
  end
  if not encontrado then titulo = inlines end
  return strip_trailing_space(titulo), trim(dur), strip_trailing_space(cred)
end

local function tiene_anio(inlines)
  return stringify(inlines):find("%(%d%d%d%d") ~= nil
end

-- Convierte una BulletList del programa en el entorno «obras»
local function lista_obras(lista, marcas)
  local out = { "\\begin{obras}" }
  local anterior = false
  local function obra(t)
    -- un poco de aire entre los movimientos de una obra y la obra siguiente
    if out[#out]:match("^\\movimiento") then table.insert(out, "\\trasmovimientos") end
    table.insert(out, t)
  end
  for _, item in ipairs(lista.content) do
    local primero = item[1]
    local inl = (primero and (primero.t == "Plain" or primero.t == "Para")) and primero.content or pandoc.List()
    local titulo, dur, cred = partir_obra(inl)
    if not es_leyenda(stringify(inl)) then marcas_en(inl, marcas) end
    if es_leyenda(stringify(inl)) and dur == "" then
      -- leyenda escrita como viñeta («- Estreno mundial»): se descarta
      marcas.declaradas = (marcas.declaradas or "") .. stringify(inl)
    elseif dur == "" and not tiene_anio(titulo) and anterior then
      table.insert(out, "\\movimiento{" .. latex(titulo) .. "}")
    else
      obra("\\obra{" .. latex(titulo) .. "}{" .. escape(dur) .. "}{" .. latex(cred) .. "}")
      anterior = true
    end
    -- Bloques restantes del elemento: sublistas (movimientos) o texto
    for k = 2, #item do
      local b = item[k]
      if b.t == "BulletList" or b.t == "OrderedList" then
        for _, sub in ipairs(b.content) do
          local s = sub[1] and sub[1].content or pandoc.List()
          marcas_en(s, marcas)
          local t2, d2, c2 = partir_obra(s)
          if d2 ~= "" then
            obra("\\obra{" .. latex(t2) .. "}{" .. escape(d2) .. "}{" .. latex(c2) .. "}")
          else
            table.insert(out, "\\movimiento{" .. latex(t2) .. "}")
          end
        end
      elseif b.content then
        table.insert(out, "\\movimiento{" .. latex(b.content) .. "}")
      end
    end
  end
  if #out == 1 then return raw("") end
  table.insert(out, "\\end{obras}")
  return raw(table.concat(out, "\n"))
end

-- -----------------------------------------------------------------------------
-- Fichas biográficas
-- -----------------------------------------------------------------------------

-- "Kaija Saariaho (Finlandia, 1952 – Francia, 2023)" → nombre, detalle
local function partir_ficha(inlines)
  local n = #inlines
  if n > 0 and inlines[n].t == "Str" and inlines[n].text:match("%)$") then
    -- buscar el Str que abre el paréntesis final
    for i = n, 1, -1 do
      local el = inlines[i]
      if el.t == "Str" and el.text:match("^%(") then
        local nombre, detalle = pandoc.List(), pandoc.List()
        for j = 1, i - 1 do nombre:insert(inlines[j]) end
        for j = i, n do detalle:insert(inlines[j]) end
        local d = latex(detalle):gsub("^%(", ""):gsub("%)$", "")
        return strip_trailing_space(nombre), d
      end
    end
  end
  return inlines, ""
end

local function imagen_sola(bloque)
  if bloque and bloque.t == "Para" and #bloque.content == 1 and bloque.content[1].t == "Image" then
    return bloque.content[1]
  end
  return nil
end

local function resolver_foto(src)
  local ruta = urldecode(src)
  local m = MANIFIESTO[ruta]
  if m then return m[1], m[2] end
  io.stderr:write("Aviso: foto no encontrada en el manifiesto: " .. ruta .. "\n")
  return nil, nil
end

-- Logotipos de los conciertos: build/logos/manifiesto.tsv, que genera
-- automatizacion/preparar_logos.py (clave «src|atributos», como allá).
local LOGOS = {}
local function cargar_logos()
  local f = io.open("build/logos/manifiesto.tsv", "r")
  if not f then
    io.stderr:write("Aviso: falta build/logos/manifiesto.tsv; ejecute preparar_logos.py\n")
    return
  end
  for linea in f:lines() do
    local k, ruta, w, h = linea:match("^(.-)\t(.-)\t(%d+)\t(%d+)$")
    if k then
      LOGOS[k] = LOGOS[k] or {}
      table.insert(LOGOS[k], { ruta = ruta, w = tonumber(w), h = tonumber(h) })
    end
  end
  f:close()
end

-- Tamaño de un logotipo (mm) según su proporción, para que todos se vean
-- del mismo tamaño: los cuadrados, más altos; los alargados, más bajos.
local function medida_logo(w, h)
  local r = w / h
  local alto = math.max(4.6, math.min(10.5 * r ^ -0.45, 11.5))
  local ancho = alto * r
  if ancho > 32 then ancho, alto = 32, 32 / r end
  return ancho, alto
end

-- Bloque «::: logos» → \logo{...}\logosep \logo{...}
local function logos_latex(div)
  local items = {}
  div:walk({ Image = function(img)
    local partes = {}
    for _, k in ipairs({ "pagina", "partir", "realce", "recorte" }) do
      if img.attributes[k] then partes[#partes + 1] = k .. "=" .. img.attributes[k] end
    end
    local piezas = LOGOS[img.src .. "|" .. table.concat(partes, ";")]
    if not piezas then
      io.stderr:write("Aviso: logotipo no preparado: " .. img.src .. "\n")
    else
      for _, p in ipairs(piezas) do
        local ancho, alto = medida_logo(p.w, p.h)
        items[#items + 1] = string.format("\\logo{%s}{%.2fmm}{%.2fmm}", p.ruta, ancho, alto)
      end
    end
  end })
  return table.concat(items, "\\logosep ")
end

-- -----------------------------------------------------------------------------
-- Recorrido principal
-- -----------------------------------------------------------------------------

function Pandoc(doc)
  cargar_manifiesto()
  cargar_logos()
  local mi = doc.meta["indice-onomastico"]
  if mi then
    for k, v in pairs(mi) do NOMBRES_INDICE[k] = stringify(v) end
  end
  local pd = doc.meta["divisores-por-dia"]
  if pd then
    for _, v in ipairs(pd) do PARTES_CON_DIVISORES[clave_orden(stringify(v))] = true end
  end

  local bloques = doc.blocks
  local out = pandoc.List()
  local function emit(b) out:insert(b) end

  -- Estado
  local parte = ""            -- título de la parte actual (en mayúsculas)
  local seccion = nil          -- sección ### actual (en minúsculas)
  local en_programa = false
  local marcas = {}
  local cabecera = ""          -- texto de la cabecera del concierto actual
  local mes_actual = "NOV"
  local dia_toc = nil          -- último día escrito en el índice
  local indice_abierto = nil   -- compositor con rango de índice abierto
  local mayor = nil            -- sección ## sin fecha en curso (sedes, créditos...)
  local concierto_abierto = nil -- número del concierto en curso (para el ajuste fino)
  local tras_lista = false      -- el programa acaba de listar obras (intérpretes a continuación)
  local bloque_int = false      -- dentro de un bloque de intérpretes del programa
  local en_semblanza = false    -- dentro del texto de una semblanza (tras una ficha)
  local en_nota = false         -- dentro de una nota al programa (recuadro verde)
  local nota_solo_cita = false  -- la nota consiste solo en una cita
  local seccion_abierta = nil   -- id de la sección de semblanzas en curso (ajuste fino)
  local prog_ini = 0            -- posición en «out» donde empieza el programa
  local logos_concierto = nil   -- logotipos del concierto en curso (para el programa)
  local solo_programa = false   -- el concierto no tiene más secciones que el programa
  -- Compositores que aparecen más de una vez: la primera ficha con semblanza
  -- lleva la foto y el texto; las siguientes, solo «Ver pág. N».
  local bio_compositor = {}     -- clave del nombre → etiqueta de su primera semblanza
  local saltando_bio = false    -- omitiendo el texto de una semblanza repetida
  -- Semblanzas de intérpretes y notas al programa que se repiten tal cual
  -- (mismo nombre u obra y el mismo texto): las siguientes, «Ver pág. N».
  local bio_persona = {}        -- clave del nombre → { {etiqueta, palabras, n}, ... }
  local nota_vista = {}         -- compositor|obra → { {etiqueta, palabras, n}, ... }
  local num_etiqueta = 0
  local ultimo_comp = ""        -- compositor de la ficha en curso (para sus notas)
  local seccion_previa = nil    -- «programa», «referencias» u «otra» (en el concierto)
  local num_seccion = 0
  local secciones_mayor = 0     -- secciones ### dentro de la sección ## sin fecha actual
  local dia_divisor = nil      -- último día con página divisoria
  local num_concierto = 0

  -- Fechas secundarias (conciertos que se repiten otro día): se listan
  -- también en el índice general bajo ese día.
  local secundarias = {}       -- clave de día → lista de {hora, titulo, etiqueta}
  local pendientes = {}        -- secundarias del día en curso aún no escritas

  local function siguiente_es_texto(k)
    k = k + 1
    while bloques[k] and bloques[k].t == "RawBlock" do k = k + 1 end
    local bk = bloques[k]
    return bk ~= nil and (bk.t == "Para" or bk.t == "Plain" or bk.t == "BlockQuote")
  end

  -- Palabras del texto que sigue a un encabezado (hasta el siguiente)
  local function palabras_desde(k)
    local set, cuenta = {}, 0
    while bloques[k] and bloques[k].t ~= "Header" do
      local bk = bloques[k]
      if bk.t ~= "RawBlock" and bk.t ~= "HorizontalRule" and not imagen_sola(bk) then
        for w in stringify(bk):lower():gmatch("[%w\128-\255]+") do
          if not set[w] then set[w] = true; cuenta = cuenta + 1 end
        end
      end
      k = k + 1
    end
    return set, cuenta
  end

  -- ¿El texto que empieza en k ya se compuso bajo esta clave? (≥ 90 % de
  -- palabras en común). Devuelve la etiqueta de la primera aparición.
  local function ya_visto(tabla, clave, k)
    local lista = tabla[clave]
    if not lista then return nil end
    local p, np = palabras_desde(k)
    if np == 0 then return nil end
    for _, v in ipairs(lista) do
      local comun = 0
      for w in pairs(p) do if v.palabras[w] then comun = comun + 1 end end
      if comun / (np + v.n - comun) >= 0.9 then return v.etiqueta end
    end
    return nil
  end

  local function registrar(tabla, clave, k, prefijo)
    num_etiqueta = num_etiqueta + 1
    local p, np = palabras_desde(k)
    local etiqueta = prefijo .. num_etiqueta
    tabla[clave] = tabla[clave] or {}
    table.insert(tabla[clave], { etiqueta = etiqueta, palabras = p, n = np })
    return etiqueta
  end

  local function clave_nota(h)
    return ultimo_comp .. "|" .. clave_orden(stringify(h.content))
  end

  local function cerrar_indice()
    if indice_abierto then
      emit(raw(entrada_indice(indice_abierto, "|)")))
      indice_abierto = nil
    end
  end

  local function cerrar_nota()
    if en_nota then
      emit(raw("\\end{notaobratexto}"))
      en_nota = false
    end
  end

  local function es_firma(b)
    return b and b.t == "Para" and b.content[1] and b.content[1].t == "RawInline"
      and trim(b.content[1].text) == "\\hfill"
  end

  -- Abre el recuadro de una nota al programa (solo dentro de un concierto).
  -- Si la nota es únicamente una cita, sus párrafos no se sangran.
  local function abrir_nota(desde)
    cerrar_nota()
    if not concierto_abierto then return end
    local solo, hay = true, false
    local k = desde
    while bloques[k] and bloques[k].t ~= "Header" and bloques[k].t ~= "HorizontalRule" do
      local bk = bloques[k]
      if bk.t == "BlockQuote" then hay = true
      elseif not es_firma(bk) and not (bk.t == "RawBlock") then solo = false end
      k = k + 1
    end
    nota_solo_cita = solo and hay
    emit(raw("\\begin{notaobratexto}"))
    en_nota = true
  end

  local function cerrar_semblanza()
    cerrar_nota()
    if en_semblanza then
      emit(raw("\\end{semblanza}"))
      en_semblanza = false
    end
  end

  local function abrir_semblanza()
    cerrar_semblanza()
    emit(raw("\\begin{semblanza}"))
    en_semblanza = true
  end

  -- Nota al programa (encabezado en b, texto desde i + 1). Si la misma nota
  -- de la misma obra ya apareció, solo su título y «Ver pág. N».
  local function emitir_nota(b, i)
    local clave = clave_nota(b)
    local ref = concierto_abierto and ya_visto(nota_vista, clave, i + 1)
    if ref then
      emit(raw("\\notaver{" .. latex(b.content) .. "}{" .. ref .. "}"))
      saltando_bio = true
    else
      local marca = ""
      if concierto_abierto and siguiente_es_texto(i) then
        marca = "\\phantomsection\\label{" .. registrar(nota_vista, clave, i + 1, "nota:") .. "}"
      end
      emit(raw("\\notaobra{" .. latex(b.content) .. "}" .. marca))
      abrir_nota(i + 1)
    end
  end

  -- Cierra el bloque de intérpretes; «sigue» indica que el programa continúa
  -- con otro grupo de obras (se deja un respiro para separarlos).
  local function cerrar_bloque_int(sigue)
    if bloque_int then
      emit(raw("\\end{interpretes}"))
      bloque_int = false
      if sigue then emit(raw("\\separadorgrupo")) end
    end
  end

  local function cerrar_programa()
    cerrar_bloque_int(false)
    if en_programa then
      local d = marcas.declaradas or ""
      local dm = d:find("mundial") ~= nil
      local dx = d:find("México") ~= nil
      if d ~= "" and ((dm and not marcas.mundial) or (dx and not marcas.mexico) or
         (marcas.mundial and not dm) or (marcas.mexico and not dx)) then
        io.stderr:write(string.format("Leyenda de estrenos: %s | declarada [%s%s] marcas [%s%s]\n",
          cabecera, dm and "*" or "", dx and "**" or "",
          marcas.mundial and "*" or "", marcas.mexico and "**" or ""))
      end
      -- quitar espaciadores colgantes al final del programa
      while #out > 0 and out[#out].t == "RawBlock" and out[#out].text == "\\par\\addvspace{1.8mm}" do
        out:remove(#out)
      end
      -- Última lista de obras y bloque final de intérpretes
      local ultima_lista, bloque_final
      for k = prog_ini + 1, #out do
        if out[k].t == "RawBlock" and out[k].text:match("^\\begin{obras}") then ultima_lista = k end
      end
      for k = (ultima_lista or #out) + 1, #out do
        if out[k].t == "RawBlock" and out[k].text == "\\begin{interpretes}" then bloque_final = k; break end
      end
      -- ¿Cuántos bloques de intérpretes tiene el programa?
      local bloques_int = 0
      for k = prog_ini + 1, #out do
        if out[k].t == "RawBlock" and out[k].text == "\\begin{interpretes}" then bloques_int = bloques_int + 1 end
      end
      if bloques_int > 1 then
        -- Varios grupos de obras con distintos intérpretes: cada grupo se
        -- mantiene entero en una página (si cabe) y sus intérpretes junto a él.
        bloque_final = nil
        local function estimar(desde, hasta)
          local r = 0
          for k = desde, hasta do
            local e = out[k]
            local t = (e.t == "RawBlock") and e.text or stringify(e)
            if e.t == "RawBlock" then
              for _ in t:gmatch("\\compositor{") do r = r + 1.35 end
              for titulo in t:gmatch("\\obra{(.-)}{") do r = r + (#titulo > 70 and 2 or 1) + 0.1 end
              for _ in t:gmatch("\\movimiento{") do r = r + 0.9 end
              for _ in t:gmatch("\\solista{") do r = r + 1.1 end
              for _ in t:gmatch("\\leyendaobras{") do r = r + 1.6 end
              if t == "\\begin{interpretes}" then r = r + 0.8 end
            else
              local lineas = 1
              for _ in t:gmatch("\n") do lineas = lineas + 1 end
              if e.t == "Para" then
                lineas = 1
                for _, x in ipairs(e.content) do if x.t == "LineBreak" then lineas = lineas + 1 end end
              end
              r = r + lineas * 0.95 + 0.3
            end
          end
          return math.ceil(r)
        end
        local inicio = prog_ini + 1
        local cortes = {}
        for k = prog_ini + 1, #out + 1 do
          local e = out[k]
          if k == #out + 1 or (e.t == "RawBlock" and e.text == "\\separadorgrupo") then
            table.insert(cortes, { inicio, k - 1 })
            inicio = k + 1
          end
        end
        -- Marcas para el ajuste fino: si un grupo queda solo en su página,
        -- sus intérpretes van al pie (y, si es el último, la leyenda de
        -- estrenos va antes, tras las obras).
        local leyenda = leyenda_latex(marcas)
        for c = #cortes, 1, -1 do
          local a, z = cortes[c][1], cortes[c][2]
          local lineas = estimar(a, z)
          if concierto_abierto then
            local id = concierto_abierto .. "}{" .. c
            local bloque, comp
            for k = a, z do
              local e = out[k]
              if e.t == "RawBlock" and e.text == "\\begin{interpretes}" then bloque = k end
              if not comp and e.t == "RawBlock" and e.text:match("^\\compositor{") then comp = k end
            end
            out:insert(z + 1, raw("\\grupofin{" .. id .. "}"))
            if bloque then
              local ultimo = c == #cortes
              out:insert(bloque, raw("\\grupoint{" .. id .. "}{" .. (ultimo and 1 or 0) .. "}{" ..
                ((ultimo and leyenda) or "") .. "}"))
            end
            out:insert(comp and comp + 1 or a, raw("\\grupoini{" .. id .. "}"))
          end
          if lineas < 30 then out:insert(a, raw("\\inigrupo{" .. lineas .. "}")) end
        end
      end
      -- Si todo el programa lo tocan los mismos intérpretes, van al pie de la página
      if bloque_final then
        local marca = concierto_abierto and ("\\marcapos{pre:" .. concierto_abierto .. "}") or ""
        out:insert(bloque_final, raw("\\par" .. marca .. "\\vspace*{\\fill}"))
      end
      -- La leyenda de estrenos cierra la lista de obras
      local l = leyenda_latex(marcas)
      if l and bloques_int > 1 then
        -- varios grupos: la leyenda cierra el programa, tras el último grupo
        -- (salvo que ese grupo vaya al pie de la página: entonces va antes)
        emit(raw((l:gsub("^\\leyenda", concierto_abierto and "\\leyendagrupos" or "\\leyendafinal"))))
        l = nil
      end
      if l then
        local k = ultima_lista and ultima_lista + 1
        if k and out[k] and out[k].t == "RawBlock" and out[k].text:match("^\\notaprograma") then
          -- después de las notas breves que acompañan a la última obra
          while out[k] and out[k].t == "RawBlock" and out[k].text:match("^\\notaprograma") do k = k + 1 end
          out:insert(k, raw(l))
        elseif ultima_lista then
          -- como último renglón de la lista de obras (sin corte de página)
          local txt = out[ultima_lista].text
          out[ultima_lista] = raw((txt:gsub("\\end{obras}$", (l:gsub("^\\leyenda", "\\leyendaobras")) .. "\n\\end{obras}")))
        else
          emit(raw(l))
        end
      end
      -- Si la franja de logotipos no cabe al final del concierto (decisión
      -- del ajuste fino), va al pie del programa.
      if concierto_abierto and logos_concierto and logos_concierto ~= "" then
        -- con el bloque de intérpretes al pie, la franja va debajo de él
        -- («fil» cede ante su «fill»); sin él, la franja misma va al pie y
        -- «pre» marca el fin de las obras para el ajuste fino
        local orden = bloque_final and "fil" or "fill"
        if solo_programa then
          if not bloque_final then emit(raw("\\par\\marcapos{pre:" .. concierto_abierto .. "}")) end
          emit(raw("\\logosalpie[" .. orden .. "]{" .. logos_concierto .. "}"))
        else
          emit(raw("\\logosprograma{" .. concierto_abierto .. "}{" .. orden .. "}{" .. logos_concierto .. "}"))
        end
      end
      if concierto_abierto then emit(raw("\\finprograma{" .. concierto_abierto .. "}")) end
      emit(raw("\\end{bloqueprograma}"))
      en_programa = false
    end
  end

  local function cerrar_seccion()
    cerrar_semblanza()
    cerrar_indice()
    cerrar_programa()
    if seccion_abierta then
      emit(raw("\\finseccion{" .. seccion_abierta .. "}"))
      seccion_abierta = nil
    end
    seccion = nil
  end

  local function cerrar_concierto()
    concierto_abierto = nil
  end

  local function cerrar_mayor()
    cerrar_seccion()
    cerrar_concierto()
    if mayor and SECCIONES_CENTRADAS[mayor] then
      emit(raw("\\end{creditos}"))
    end
    mayor = nil
  end

  local function escribir_pendientes(hasta)
    local resto = {}
    for _, p in ipairs(pendientes) do
      if hasta == nil or p.clave < hasta then
        emit(raw("\\addtocontents{toc}{\\protect\\contentsline{concierto}{\\protect\\numberline{" ..
          p.hora .. "}" .. p.titulo .. "}{\\protect\\pageref{" .. p.etiqueta .. "}}{" .. p.etiqueta .. "}}"))
      else
        table.insert(resto, p)
      end
    end
    pendientes = resto
  end

  local function dia_en_indice(f)
    local clave = f.mes .. f.num
    if dia_toc ~= clave then
      escribir_pendientes(nil)
      dia_toc = clave
      pendientes = secundarias[clave] or {}
      return true
    end
    return false
  end

  -- Pre-pasada: conciertos con más de una fecha
  do
    local mes = "NOV"
    for _, b in ipairs(bloques) do
      if b.t == "Header" and b.level == 2 then
        local izq = partir_encabezado(stringify(b.content))
        local fs = izq and parse_fechas(izq, mes)
        if fs then
          mes = fs[1].mes
          num_concierto = num_concierto + 1
          for k = 2, #fs do
            local _, der = partir_inlines(b.content)
            local clave = fs[k].mes .. fs[k].num
            secundarias[clave] = secundarias[clave] or {}
            table.insert(secundarias[clave], {
              hora = fs[k].hora or "",
              clave = fecha_clave(fs[k]),
              titulo = latex(envolver_cjk(der)) .. " {\\color{verdegris}(también " ..
                       escape(fecha_texto(fs[1])) .. ")}",
              etiqueta = "concierto:" .. num_concierto,
            })
          end
        end
      end
    end
    num_concierto = 0
  end

  local i, n = 1, #bloques

  while i <= n do
    local b = bloques[i]
    local siguiente = bloques[i + 1]
    if saltando_bio and (b.t == "Header" or b.t == "Div"
                         or (b.t == "RawBlock" and not b.text:match("^%s*\\clearpage"))) then
      saltando_bio = false
    end
    if saltando_bio then
      i = i + 1
      goto continuar
    end

    -- ----------------------------------------------------------- LOGOS --
    -- «::: logos» al final de un concierto: franja de logotipos al pie de su
    -- última página (en las actividades académicas, a continuación).
    if b.t == "Div" and b.classes:includes("logos") then
      cerrar_semblanza()
      cerrar_indice()
      cerrar_programa()
      local items = logos_latex(b)
      if concierto_abierto and solo_programa then
        -- ya se compuso al pie del programa
      elseif items ~= "" and concierto_abierto then
        -- el fin de la sección se marca antes de los logotipos: el ajuste
        -- fino sigue viendo dónde acaba el texto, y aparte si la franja
        -- quedó sola en otra página
        local sid = seccion_abierta or ""
        if seccion_abierta then
          emit(raw("\\finseccion{" .. seccion_abierta .. "}"))
          seccion_abierta = nil
        end
        emit(raw("\\logosconcierto{" .. sid .. "}{" .. items .. "}"))
      elseif items ~= "" then
        emit(raw("\\logosactividad{" .. items .. "}"))
      end
      i = i + 1

    -- ---------------------------------------------------------------- RAW --
    elseif b.t == "RawBlock" and (b.format == "latex" or b.format == "tex") then
      local t = trim(b.text)
      local titulo_parte = t:match("^\\part%*?{(.-)}$")
      local divisor = t:match("^\\portadacapitulo{(.-)}$")
      if t == "\\clearpage" or t == "\\newpage" or t == "\\pagebreak" then
        -- la paginación la decide la plantilla
      elseif t == "\\vfill" or t:match("^\\vfill%s*$") then
        if en_programa then emit(raw("\\par\\addvspace{1.8mm}")) end
      elseif t == "\\par" then
        -- nada
      elseif t == "\\printindex" then
        cerrar_mayor()
        emit(b)
      elseif titulo_parte then
        cerrar_mayor()
        dia_divisor = nil
        escribir_pendientes(nil)
        dia_toc = nil
        parte = titulo_parte
        local texto = titulo_parte:gsub("|", "\\textbar{}")
        local subtitulo = ""
        if siguiente and (siguiente.t == "Para" or siguiente.t == "Plain") then
          subtitulo = latex(siguiente.content)
          i = i + 1
        end
        emit(raw("\\parte{" .. texto .. "}{" .. texto .. "}{" .. subtitulo .. "}"))
        cabecera = ""
      elseif divisor then
        cerrar_mayor()
        local f = parse_una_fecha(divisor, mes_actual)
        if f and PARTES_CON_DIVISORES[clave_orden(parte)] then
          -- se generan automáticamente
        elseif f then
          dia_divisor = f.mes .. f.num
          mes_actual = f.mes
          emit(raw(divisor_dia(f, dia_en_indice(f) and escape(fecha_texto(f)) or "")))
        elseif clave_orden(divisor) ~= "programa general" then
          emit(raw("\\divisor{" .. divisor .. "}"))
        end
      else
        emit(b)
      end
      i = i + 1

    -- ------------------------------------------------------------- HEADER --
    elseif b.t == "Header" and b.level <= 2 then
      cerrar_mayor()
      local inl = envolver_cjk(b.content)
      local texto = stringify(b.content)
      local izq_txt = partir_encabezado(texto)
      local fechas = izq_txt and parse_fechas(izq_txt, mes_actual)
      if fechas then
        local _, der = partir_inlines(inl)
        local f = fechas[1]
        mes_actual = f.mes
        num_concierto = num_concierto + 1
        local etiqueta = "concierto:" .. num_concierto
        -- Página divisoria automática al cambiar de día
        if PARTES_CON_DIVISORES[clave_orden(parte)] and dia_divisor ~= f.mes .. f.num then
          dia_divisor = f.mes .. f.num
          local nuevo = dia_en_indice(f)
          emit(raw(divisor_dia(f, nuevo and escape(fecha_texto(f)) or "")))
        end
        -- Día en el índice general
        if dia_en_indice(f) then
          emit(raw("\\addtocontents{toc}{\\protect\\contentsline{dia}{" ..
            escape(fecha_texto(f)) .. "}{}{}}"))
        end
        escribir_pendientes(fecha_clave(f))
        local kicker = {}
        for _, ff in ipairs(fechas) do table.insert(kicker, escape(fecha_hora_texto(ff))) end
        local titulo = latex(der)
        local titulo_txt = stringify(der)
        cabecera = escape(fecha_texto(f) .. " · " .. titulo_txt)
        local toc_titulo = titulo
        local macro = (clave_orden(parte) == "actividades academicas") and "\\actividadacademica" or "\\concierto"
        -- etiqueta estable para referencias desde el Markdown:
        -- \pageref{conc:mie-nov-18-electroacustica-i}
        local estable = "conc:" .. clave_orden(fecha_texto(f) .. " " .. titulo_txt):gsub("[^%w]+", "-"):gsub("^-+", ""):gsub("-+$", "")
        emit(raw(string.format("%s{%s}{%s}{%s}{%s}{%s}{%s}\\hypertarget{%s}{}\\label{%s}\\label{" .. estable .. "}",
          macro,
          table.concat(kicker, "\\quad/\\quad "), titulo, cabecera,
          f.hora or "", toc_titulo,
          escape(fecha_texto(f) .. " · " .. titulo_txt), etiqueta, etiqueta)))
        if macro == "\\concierto" then
          concierto_abierto = num_concierto
          seccion_previa = nil
          -- logotipos del concierto (el bloque «::: logos» va al final): se
          -- preparan ya por si hay que ponerlos al pie del programa
          logos_concierto = nil
          solo_programa = true
          local k = i + 1
          while bloques[k] and not (bloques[k].t == "Header" and bloques[k].level <= 2)
                and not (bloques[k].t == "RawBlock" and bloques[k].text:match("^\\part")) do
            local bk = bloques[k]
            if bk.t == "Div" and bk.classes:includes("logos") then
              logos_concierto = logos_latex(bk)
            elseif bk.t == "Header" and bk.level == 3 and clave_orden(stringify(bk.content)) ~= "programa" then
              solo_programa = false
            end
            k = k + 1
          end
          emit(raw("\\iniconcierto{" .. num_concierto .. "}"))
        end
        -- Lugar: primer párrafo tras el encabezado
        if siguiente and (siguiente.t == "Para" or siguiente.t == "Plain")
           and siguiente.content[1] and siguiente.content[1].t ~= "Strong"
           and #stringify(siguiente.content) < 160 then
          local lugar = latex(strip_trailing_space(siguiente.content))
          i = i + 1
          -- Un segundo párrafo breve antes de las secciones (p. ej. otra fecha
          -- y otra sede del mismo concierto) también forma parte del lugar.
          local otro, tras = bloques[i + 1], bloques[i + 2]
          if otro and otro.t == "Para" and otro.content[1] and otro.content[1].t ~= "Strong"
             and #stringify(otro.content) < 160 and tras
             and (tras.t == "Header" or tras.t == "HorizontalRule") then
            lugar = lugar .. "\\par\\vspace{1mm}" .. latex(strip_trailing_space(otro.content))
            i = i + 1
          end
          emit(raw("\\lugar{" .. lugar .. "}"))
          -- el filete del lugar sustituye a un «---» inmediato
          if bloques[i + 1] and bloques[i + 1].t == "HorizontalRule" then i = i + 1 end
        end
      else
        -- Sección sin fecha (Coloquio, Sedes, Créditos, Directorio...)
        cabecera = escape(texto)
        emit(raw(string.format("\\seccionmayor{%s}{%s}{%s}", latex(inl), cabecera, escape(texto))))
        mayor = clave_orden(texto)
        secciones_mayor = 0
        if SECCIONES_CENTRADAS[mayor] then emit(raw("\\begin{creditos}")) end
      end
      i = i + 1

    elseif b.t == "Header" and b.level == 3 then
      cerrar_seccion()
      local texto = stringify(b.content)
      seccion = clave_orden(texto)
      if mayor and (SECCIONES_CENTRADAS[mayor] or SECCIONES_SEDES[mayor]) then
        emit(raw("\\grupocreditos{" .. latex(b.content) .. "}\\marcador{3}{" .. escape(texto) .. "}"))
      elseif seccion ~= "programa" and concierto_abierto then
        -- Personas compositoras, Intérpretes...: cada sección en página nueva.
        -- Una sección que solo tiene referencias «Ver pág.» (fichas y notas
        -- que ya aparecieron) sigue en la página, salvo justo después del
        -- programa; y la sección que viene tras ella también puede seguir.
        local tipo_sec = SECCIONES_FICHA[seccion]
        local solo_referencias = tipo_sec ~= nil
        local comp_previo = ultimo_comp
        local k = i + 1
        while solo_referencias and bloques[k] and not (bloques[k].t == "Header" and bloques[k].level <= 3) do
          local bk = bloques[k]
          if bk.t == "Header" then
            if bk.level == 4 then
              local cl = clave_orden(stringify((partir_ficha(bk.content))))
              local t = k + 1
              if imagen_sola(bloques[t]) then t = t + 1 end
              if tipo_sec == "comp" then
                ultimo_comp = cl
                if not bio_compositor[cl] then solo_referencias = false end
              elseif not ya_visto(bio_persona, cl, t) then
                solo_referencias = false
              end
            elseif not ya_visto(nota_vista, clave_nota(bk), k + 1) then
              solo_referencias = false
            end
          end
          k = k + 1
        end
        ultimo_comp = comp_previo
        local inicio = "\\clearpage"
        if solo_referencias and seccion_previa ~= "programa" then
          inicio = "\\necesito{6\\baselineskip}\\par\\addvspace{7mm}"
        elseif seccion_previa == "referencias" then
          inicio = "\\necesito{14\\baselineskip}\\par\\addvspace{8mm}"
        end
        seccion_previa = solo_referencias and "referencias" or "otra"
        num_seccion = num_seccion + 1
        seccion_abierta = concierto_abierto .. "-" .. num_seccion
        emit(raw(inicio .. "\\iniseccion{" .. seccion_abierta .. "}"))
        local titulo_sec = latex(b.content)
        if seccion == "interpretes" then
          -- con una sola ficha, en singular
          local fichas, k = 0, i + 1
          while bloques[k] and not (bloques[k].t == "Header" and bloques[k].level <= 3) do
            if bloques[k].t == "Header" and bloques[k].level == 4 then fichas = fichas + 1 end
            k = k + 1
          end
          if fichas == 1 then titulo_sec = "Intérprete" end
        end
        emit(raw("\\seccion{" .. titulo_sec .. "}{3}"))
        -- «Notas al programa» generales del concierto: en el recuadro verde
        if seccion == "notas al programa" then abrir_nota(i + 1) end
      else
        -- en el Coloquio, cada sección después de la primera en página nueva
        if seccion ~= "programa" and mayor and secciones_mayor > 0 then emit(raw("\\clearpage")) end
        emit(raw("\\seccion{" .. latex(b.content) .. "}{3}"))
      end
      if mayor then secciones_mayor = secciones_mayor + 1 end
      if seccion == "programa" then
        seccion_previa = "programa"
        en_programa = true
        marcas = {}
        tras_lista = false
        emit(raw("\\begin{bloqueprograma}"))
        prog_ini = #out
      end
      i = i + 1

    elseif b.t == "Header" and b.level == 4 then
      cerrar_semblanza()
      cerrar_indice()
      cerrar_programa()
      local tipo = seccion and SECCIONES_FICHA[seccion]
      local texto = stringify(b.content)
      local izq_txt = partir_encabezado(texto)
      local fechas = izq_txt and parse_fechas(izq_txt, mes_actual)
      if tipo then
        local inl = envolver_cjk(b.content)
        local nombre, detalle = partir_ficha(inl)
        local nombre_tex = latex(nombre)
        local img = imagen_sola(siguiente)
        local foto
        if img then
          foto = resolver_foto(img.src)
          i = i + 1
        end
        local marca = "\\marcador{4}{" .. escape(stringify(nombre)) .. "}"
        if tipo == "comp" then
          indice_abierto = stringify(nombre)
          marca = marca .. entrada_indice(indice_abierto, "|(")
        end
        local clave = clave_orden(stringify(nombre))
        local tiene_bio = siguiente_es_texto(i)
        if tipo == "comp" then ultimo_comp = clave end
        -- ¿Ya apareció? Compositores: por el nombre; intérpretes: nombre y
        -- la misma semblanza (puede haber aparecido antes como compositor).
        local ref
        if tipo == "comp" then ref = bio_compositor[clave]
        elseif tiene_bio then ref = ya_visto(bio_persona, clave, i + 1) end
        if ref then
          -- nombre y referencia a la primera semblanza
          emit(raw(string.format("\\fichaver{%s}{%s}{%s}%s", nombre_tex, detalle,
            ref, marca)))
          saltando_bio = true
        else
          if tiene_bio then
            local et = registrar(bio_persona, clave, i + 1, "bio:")
            if tipo == "comp" then bio_compositor[clave] = et end
            marca = marca .. "\\phantomsection\\label{" .. et .. "}"
          end
          if foto then
            emit(raw(string.format("\\ficha{%s}{%s}{%s}%s", foto, nombre_tex, detalle, marca)))
          else
            emit(raw(string.format("\\fichasola{%s}{%s}%s", nombre_tex, detalle, marca)))
          end
          abrir_semblanza()
        end
      elseif fechas then
        local _, der = partir_inlines(b.content)
        local kicker = {}
        for _, ff in ipairs(fechas) do table.insert(kicker, escape(fecha_hora_texto(ff))) end
        emit(raw("\\actividad{" .. table.concat(kicker, "\\quad/\\quad ") .. "}{" .. latex(der) .. "}"))
      else
        emitir_nota(b, i)
      end
      i = i + 1

    elseif b.t == "Header" then
      cerrar_semblanza()
      cerrar_programa()
      emitir_nota(b, i)
      i = i + 1

    -- Ficha cuyo nombre viene en negritas en lugar de «####»
    elseif seccion and SECCIONES_FICHA[seccion] and (b.t == "Para" or b.t == "Plain")
           and #b.content == 1 and b.content[1].t == "Strong" and imagen_sola(siguiente) then
      cerrar_semblanza()
      cerrar_indice()
      local nombre = b.content[1].content
      local foto = resolver_foto(imagen_sola(siguiente).src)
      local marca = "\\marcador{4}{" .. escape(stringify(nombre)) .. "}"
      if SECCIONES_FICHA[seccion] == "comp" then
        indice_abierto = stringify(nombre)
        marca = marca .. entrada_indice(indice_abierto, "|(")
      end
      if foto then
        emit(raw(string.format("\\ficha{%s}{%s}{}%s", foto, latex(nombre), marca)))
      else
        emit(raw(string.format("\\fichasola{%s}{}%s", latex(nombre), marca)))
      end
      abrir_semblanza()
      i = i + 2

    -- ------------------------------------------------------------ PROGRAMA --
    elseif en_programa and b.t == "BulletList" then
      cerrar_bloque_int(true)
      emit(lista_obras(b, marcas))
      tras_lista = true
      i = i + 1

    elseif en_programa and (b.t == "Para" or b.t == "Plain") and #b.content == 1
           and b.content[1].t == "Span" and b.content[1].classes:includes("solista") then
      -- [**Nombre**, instrumento]{.solista}: solista de la obra anterior
      emit(raw("\\solista{" .. latex(b.content[1].content) .. "}"))
      i = i + 1

    elseif en_programa and (b.t == "Para" or b.t == "Plain") then
      local txt = trim(stringify(b.content))
      if es_leyenda(txt) then
        -- se regenera automáticamente al final del programa
        marcas.declaradas = (marcas.declaradas or "") .. txt
      elseif txt == "INTERMEDIO" then
        cerrar_bloque_int(false)
        emit(raw("\\intermedio"))
        tras_lista = false
      elseif b.content[1] and b.content[1].t == "Strong" and siguiente and siguiente.t == "BulletList" then
        cerrar_bloque_int(true)
        local nombre = b.content[1].content
        local resto = pandoc.List()
        for k = 2, #b.content do resto:insert(b.content[k]) end
        local sep = (resto[1] and resto[1].t == "Space") and " " or ""
        emit(raw("\\compositor{" .. latex(nombre) .. "}{" .. sep .. latex(strip_trailing_space(resto)) .. "}" ..
                 entrada_indice(stringify(nombre))))
      else
        local c = strip_trailing_space(b.content)
        if #c == 1 and c[1].t == "Emph" then
          -- Nota del programa en cursivas (duración, patrocinio...)
          cerrar_bloque_int(false)
          emit(raw("\\notaprograma{" .. latex(c[1].content) .. "}"))
        else
          -- Intérpretes de las obras anteriores
          if tras_lista and not bloque_int then
            emit(raw("\\begin{interpretes}"))
            bloque_int = true
          end
          marcas_en(c, marcas)
          b.content = envolver_cjk(c)
          emit(b)
          tras_lista = false
        end
      end
      i = i + 1

    -- -------------------------------------------------------------- OTROS --
    elseif b.t == "HorizontalRule" and en_programa then
      -- «---» en el programa: separa grupos de obras con distintos intérpretes
      -- (si va justo después de las obras, los intérpretes vienen a continuación)
      if bloque_int then
        cerrar_bloque_int(true)
        tras_lista = false
      end
      i = i + 1

    elseif b.t == "HorizontalRule" then
      cerrar_semblanza()
      cerrar_bloque_int(false)
      -- antes de una sección o de un concierto sobra: estos empiezan página
      local sig = bloques[i + 1]
      if not (sig and sig.t == "Header" and sig.level <= 3) and sig then
        emit(raw("\\separador"))
      end
      tras_lista = false
      i = i + 1

    elseif b.t == "BlockQuote" and en_nota and nota_solo_cita then
      -- la nota es solo una cita: sus párrafos van tal cual en el recuadro
      for _, q in ipairs(b.content) do
        if q.t == "Para" or q.t == "Plain" then q.content = envolver_cjk(strip_trailing_space(q.content)) end
        emit(q)
      end
      i = i + 1

    elseif imagen_sola(b) then
      local foto = resolver_foto(imagen_sola(b).src)
      if foto then
        emit(raw("\\par\\begin{center}\\circulofoto{" .. foto .. "}{\\diametrofoto}\\end{center}"))
      end
      i = i + 1

    elseif b.t == "Para" and b.content[1] and b.content[1].t == "RawInline"
           and b.content[1].text:match("^\\hfill") and trim(b.content[1].text) == "\\hfill" then
      local resto = pandoc.List()
      for k = 2, #b.content do resto:insert(b.content[k]) end
      emit(raw("\\firma{" .. latex(strip_trailing_space(resto)) .. "}"))
      i = i + 1

    elseif en_semblanza and (b.t == "Para" or b.t == "Plain") and #b.content == 1
           and b.content[1].t == "Strong" and #stringify(b.content) < 60 then
      -- subtítulo dentro de una semblanza (p. ej. «Integrantes»): no se
      -- queda solo al pie de la página
      emit(raw("\\subtitulosemblanza{" .. latex(b.content[1].content) .. "}"))
      i = i + 1

    elseif (b.t == "Para" or b.t == "Plain") and mayor and SECCIONES_SEDES[mayor] and
           b.content[1] and b.content[1].t == "Strong" then
      local nombre = b.content[1].content
      local resto = pandoc.List()
      for k = 2, #b.content do resto:insert(b.content[k]) end
      emit(raw("\\entradasede{" .. latex(nombre) .. "}{" .. latex(strip_trailing_space(resto)) .. "}"))
      i = i + 1

    else
      if b.t == "Para" or b.t == "Plain" then
        b.content = envolver_cjk(strip_trailing_space(b.content))
      end
      emit(b)
      i = i + 1
    end
    ::continuar::
  end

  cerrar_mayor()
  escribir_pendientes(nil)
  return pandoc.Pandoc(out, doc.meta)
end
