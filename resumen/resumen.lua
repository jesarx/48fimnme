-- =============================================================================
--  resumen.lua — Programa resumido del 48º FIMNME
--
--  Lee el mismo fimnme2026-programa.md que el programa general y genera una
--  versión muy concentrada (plantilla resumen/resumen.latex):
--
--    * Agenda (una página): fecha, hora, título y sede de cada concierto y
--      actividad, con una clave de sedes y sus direcciones.
--    * Programas: intérpretes y personas compositoras de cada concierto
--      («Obras de A, B y C», sin los títulos) y cuántos estrenos tiene; sin
--      semblanzas ni notas.
--    * Página final con todos los logotipos del programa general.
--
--  Sedes y direcciones salen de la sección «## Sedes» del Markdown.
-- =============================================================================

local stringify = pandoc.utils.stringify
package.path = "automatizacion/?.lua;" .. package.path
local tipografia = require("tipografia")

local function trim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end
local function raw(s) return pandoc.RawBlock("latex", s) end

-- Caracteres CJK con su fuente (p. ej. 樗栎)
local function envolver_cjk(inlines)
  return pandoc.Inlines(inlines):walk({
    Str = function(el)
      if not el.text:find("[\228-\233][\128-\191][\128-\191]") then return nil end
      local out, buf, cjk = pandoc.List(), "", false
      for _, c in utf8.codes(el.text) do
        local es = c >= 0x2E80 and c <= 0x9FFF
        if es ~= cjk and buf ~= "" then
          out:insert(cjk and pandoc.RawInline("latex", "\\textocjk{" .. buf .. "}") or pandoc.Str(buf))
          buf = ""
        end
        cjk = es
        buf = buf .. utf8.char(c)
      end
      if buf ~= "" then
        out:insert(cjk and pandoc.RawInline("latex", "\\textocjk{" .. buf .. "}") or pandoc.Str(buf))
      end
      return out
    end,
  })
end

local function latex(inlines)
  if not inlines or #inlines == 0 then return "" end
  local s = pandoc.write(pandoc.Pandoc({ pandoc.Plain(envolver_cjk(inlines)) }), "latex",
    { wrap_text = "wrap-none" })
  return trim(s)
end

local function escape(s)
  s = s:gsub("\\", "\\textbackslash{}"):gsub("([#%%&_{}%$])", "\\%1")
  return s
end

-- Un nombre (de compositor o de intérprete) sin cortarse entre renglones
-- (la misma regla del Programa general: tipografia.nombres)
local function nombre_latex(inlines)
  return latex(tipografia.componer(tipografia.nombres(pandoc.Inlines(inlines), 40)))
end

-- Papeles de quienes participan en una actividad académica
local PAPELES = {
  imparte = true, imparten = true, ponente = true, ponentes = true, moderador = true,
  moderadora = true, moderan = true, presentador = true, presentadora = true,
  presentadores = true, presentadoras = true, participante = true, participantes = true,
}

-- Un intérprete: «Nombre, papel» → el nombre sin cortarse y el papel (el
-- instrumento, «director»…) en un peso más ligero (\\papel). El papel es lo
-- que sigue a la última coma de primer nivel y empieza con minúscula.
local function interprete_latex(xs)
  for k = #xs - 2, 1, -1 do
    local a, b, c = xs[k], xs[k + 1], xs[k + 2]
    if a.t == "Str" and a.text:sub(-1) == "," and (b.t == "Space" or b.t == "SoftBreak")
       and c.t == "Str" and c.text:match("^%l") then
      local nombre, papel = pandoc.Inlines({}), pandoc.Inlines({})
      for j = 1, k - 1 do nombre:insert(xs[j]) end
      if a.text ~= "," then nombre:insert(pandoc.Str(a.text:sub(1, -2))) end
      for j = k + 2, #xs do papel:insert(xs[j]) end
      return nombre_latex(nombre) .. ", \\papel{" .. latex(papel) .. "}"
    end
  end
  return nombre_latex(xs)
end

-- Varios intérpretes en un renglón («A, violín; B, piano»): cada uno por
-- separado → { {texto=, latex=}, … }
local function interpretes_de(inlines)
  local partes, actual = {}, pandoc.Inlines({})
  local function cerrar()
    while #actual > 0 and (actual[1].t == "Space" or actual[1].t == "SoftBreak") do actual:remove(1) end
    if #actual > 0 then
      partes[#partes + 1] = { texto = trim(stringify(actual)), latex = interprete_latex(actual) }
    end
    actual = pandoc.Inlines({})
  end
  for _, el in ipairs(pandoc.Inlines(inlines)) do
    if el.t == "Str" and el.text:sub(-1) == ";" then
      if el.text ~= ";" then actual:insert(pandoc.Str(el.text:sub(1, -2))) end
      cerrar()
    else
      actual:insert(el)
    end
  end
  cerrar()
  return partes
end

local function interpretes_latex(inlines)
  local ls = {}
  for _, p in ipairs(interpretes_de(inlines)) do ls[#ls + 1] = p.latex end
  return table.concat(ls, "; ")
end

-- minúsculas sin acentos, para comparar
local function clave(s)
  s = s:lower()
  local rep = { ["á"] = "a", ["é"] = "e", ["í"] = "i", ["ó"] = "o", ["ú"] = "u",
    ["ü"] = "u", ["ñ"] = "n", ["Á"] = "a", ["É"] = "e", ["Í"] = "i", ["Ó"] = "o",
    ["Ú"] = "u", ["Ñ"] = "n" }
  for a, b in pairs(rep) do s = s:gsub(a, b) end
  return s
end

-- Párrafo → renglones (separados por saltos de línea)
local function renglones(inlines)
  local out, cur = {}, pandoc.List()
  for _, el in ipairs(inlines) do
    if el.t == "LineBreak" then
      out[#out + 1] = cur; cur = pandoc.List()
    elseif not (el.t == "SoftBreak" and #cur == 0) then
      cur:insert(el.t == "SoftBreak" and pandoc.Space() or el)
    end
  end
  if #cur > 0 then out[#out + 1] = cur end
  -- quitar espacios sobrantes en los extremos
  for k, r in ipairs(out) do
    while #r > 0 and (r[1].t == "Space") do r:remove(1) end
    while #r > 0 and (r[#r].t == "Space") do r:remove(#r) end
    out[k] = r
  end
  return out
end

-- -----------------------------------------------------------------------------
-- Fechas: «VIE | NOV 6, 20 h - Título» (una o dos fechas). Las horas se
-- escriben «12 h» y, si no son en punto, «13:30 h»; dentro se guardan como
-- «12:00».
-- -----------------------------------------------------------------------------
local MESES = { OCT = 10, NOV = 11, DIC = 12 }

local function hora_texto(h)   -- «20:00» → «20 h»; «13:30» → «13:30 h»
  return (h:gsub(":00$", "")) .. " h"
end

local function partir_encabezado(texto)
  local izq, titulo = texto:match("^(.-%d h) %- (.*)$")
  if not izq then return nil end
  local fechas = {}
  for dia, mes, num, hora in izq:gmatch("(%S+) | (%u+) (%d+), (%d[%d:]*) h") do
    if not hora:find(":") then hora = hora .. ":00" end
    fechas[#fechas + 1] = { dia = dia, mes = mes, num = tonumber(num), hora = hora,
      orden = (MESES[mes] or 0) * 1000000 + tonumber(num) * 10000 + tonumber((hora:gsub(":", ""))) }
  end
  if #fechas == 0 then return nil end
  return fechas, titulo
end

-- Título del encabezado con su formato (cursivas): lo que sigue a « - »
local function titulo_latex(inlines, titulo)
  for k = 2, #inlines - 1 do
    local el = inlines[k]
    if el.t == "Str" and el.text == "-" and inlines[k - 1].t == "Space" and inlines[k + 1].t == "Space" then
      local resto = pandoc.Inlines({})
      for j = k + 2, #inlines do resto:insert(inlines[j]) end
      -- sin nombres cortados ni una palabra sola en el último renglón (en la
      -- agenda, a dos columnas, los de más de 26 letras se parten en dos)
      return latex(tipografia.componer(tipografia.atar_final(tipografia.nombres(resto, 26), 1, 26)))
    end
  end
  return escape(titulo)
end

local function etiqueta_dia(f)
  if f.mes ~= "NOV" then return f.num .. " " .. f.mes end
  return f.dia .. " " .. f.num
end

-- -----------------------------------------------------------------------------
-- Sedes: palabra clave que aparece en la sede del concierto y en «## Sedes»
-- (el orden importa: «música y danza» antes que «escuela superior de música»).
-- -----------------------------------------------------------------------------
local CLAVES_SEDE = {
  "bellas artes", "museo nacional de arte", "jardin escenico", "carrillo gil",
  "conservatorio nacional", "musica y danza", "escuela superior de musica",
  "arte contemporaneo", "nezahualcoyotl", "simon bolivar", "facultad de musica",
  "rafael galvan", "antigua sede del senado", "sor juana", "cenart", "artes sonoras",
  "artes de yucatan", "domingo soler", "bicentenario", "tlaqna",
  "convento del carmen", "rodolfo morales", "san pablo",
}

local function palabra_sede(texto)
  local c = clave(texto)
  for _, k in ipairs(CLAVES_SEDE) do
    if c:find(k, 1, true) then return k end
  end
  return nil
end

-- -----------------------------------------------------------------------------
-- Obras
-- -----------------------------------------------------------------------------
local function tiene_anio(s) return s:find("%(%d%d%d%d") ~= nil or s:find("%d%d%d%d%)") ~= nil end

-- Separa título (inlines antes de \hfill) y si tiene duración
local function partir_obra(inlines)
  local titulo = pandoc.List()
  for _, el in ipairs(inlines) do
    if el.t == "RawInline" and el.text:match("^\\hfill") then return titulo, true end
    titulo:insert(el)
  end
  return titulo, false
end

-- Título condensado: sin año ni subtítulo, con las marcas de estreno
local function titulo_corto(inlines)
  local s = latex(inlines)
  local marcas = ""
  local base, m = s:match("^(.-)%s*%([^()]*%d%d%d%d[^()]*%)%s*(%**)%s*$")
  if base then s, marcas = base, m
  else
    base, m = s:match("^(.-)(%*+)%s*$")
    if base then s, marcas = base, m end
  end
  -- \emph{Título}, subtítulo  →  \emph{Título}
  if s:sub(1, 6) == "\\emph{" then
    local nivel, k = 0, 6
    for j = 6, #s do
      local ch = s:sub(j, j)
      if ch == "{" then nivel = nivel + 1 elseif ch == "}" then nivel = nivel - 1 end
      if nivel == 0 then k = j; break end
    end
    local resto = s:sub(k + 1)
    if resto:match("^,") or resto:match("^%s*{%[}") or resto:match("^%s*%(") then
      s = s:sub(1, k)
    end
  end
  s = trim(s:gsub(",%s*$", ""))
  return s, marcas
end

-- -----------------------------------------------------------------------------
-- Intérpretes: de un conjunto se dan el nombre y la dirección, no la lista
-- de integrantes (renglones que siguen al nombre en negritas del conjunto,
-- en el mismo párrafo o en el siguiente). Las demás personas van todas.
-- -----------------------------------------------------------------------------
local function condensar_interpretes(lineas)
  local out, textos = {}, {}
  for _, l in ipairs(lineas) do
    if l.integrante and not clave(l.texto):find("direc") then
      -- integrante de un conjunto ya nombrado: se omite
    else
      out[#out + 1] = l.latex
      textos[#textos + 1] = l.texto
    end
  end
  return table.concat(out, "; "), table.concat(textos, "; ")
end

-- -----------------------------------------------------------------------------
-- Logotipos (página final): los mismos bloques «::: logos» del programa
-- general, sin repetir y en orden de aparición. Se usan las copias ligeras
-- que deja resumen/reducir_logos.py en build/resumen/logos/.
-- -----------------------------------------------------------------------------
local function logos_de(doc)
  local manifiesto = {}
  local f = io.open("build/logos/manifiesto.tsv", "r")
  if not f then
    io.stderr:write("Aviso: falta build/logos/manifiesto.tsv; ejecute preparar_logos.py\n")
    return {}
  end
  for linea in f:lines() do
    local k, ruta, w, h = linea:match("^(.-)\t(.-)\t(%d+)\t(%d+)$")
    if k then
      manifiesto[k] = manifiesto[k] or {}
      table.insert(manifiesto[k], { ruta = ruta, w = tonumber(w), h = tonumber(h) })
    end
  end
  f:close()
  local items, vistos = {}, {}
  doc.blocks:walk({ Div = function(div)
    if not div.classes:includes("logos") then return nil end
    div:walk({ Image = function(img)
      local partes = {}
      for _, k in ipairs({ "pagina", "partir", "realce", "recorte" }) do
        if img.attributes[k] then partes[#partes + 1] = k .. "=" .. img.attributes[k] end
      end
      for _, p in ipairs(manifiesto[img.src .. "|" .. table.concat(partes, ";")] or {}) do
        if not vistos[p.ruta] then
          vistos[p.ruta] = true
          -- el mismo tamaño que en el programa general: ninguno mayor que
          -- los de Cultura e INBAL de la pleca (máx. 6,5 mm de alto, 20 de ancho)
          local r = p.w / p.h
          local alto = math.max(3.2, math.min(6.5 * r ^ -0.45, 6.5))
          local ancho = alto * r
          if ancho > 20 then ancho, alto = 20, 20 / r end
          local ligera = p.ruta:gsub("^build/logos/", "build/resumen/logos/")
          items[#items + 1] = string.format("\\logo{%s}{%.2fmm}{%.2fmm}",
            ligera, ancho, alto)
        end
      end
    end })
  end })
  return items
end

-- -----------------------------------------------------------------------------
-- Lectura del documento
-- -----------------------------------------------------------------------------
function Pandoc(doc)
  local bloques = doc.blocks
  local eventos, sedes = {}, {}
  local parte, mayor = nil, nil
  local ev = nil              -- evento en curso
  local en_programa = false
  local grupo = nil           -- grupo de obras en curso
  local tras_obras = false

  local function nuevo_grupo()
    grupo = { obras = {}, interpretes = {} }
    table.insert(ev.grupos, grupo)
    tras_obras = false
  end

  -- Sede de cada fecha: el renglón de la sede («Palacio de Bellas Artes, Sala
  -- Principal») con los que siguen (ciudad y estado), y aparte ese renglón solo
  local function sede_de(parrafos)
    local res, solos = {}, {}
    for _, p in ipairs(parrafos) do
      local rs = renglones(p.content)
      local lugar
      for k, r in ipairs(rs) do
        local t = stringify(r)
        if palabra_sede(t) then
          lugar = t
          solos[#res + 1] = t
          for j = k + 1, #rs do lugar = lugar .. ", " .. stringify(rs[j]) end
          break
        end
      end
      if lugar then res[#res + 1] = lugar end
    end
    return res, solos
  end

  local i, n = 1, #bloques
  while i <= n do
    local b = bloques[i]
    local sig = bloques[i + 1]

    if b.t == "RawBlock" then
      local p = b.text:match("^\\part%*?{(.-)}")
      if p then parte = p; mayor = nil; ev = nil; en_programa = false end

    elseif b.t == "Header" and (b.level == 2 or (b.level == 4 and mayor == "coloquio")) then
      local texto = stringify(b.content)
      local fechas, titulo = partir_encabezado(texto)
      en_programa = false
      if fechas then
        local tipo = "concierto"
        if mayor == "coloquio" then tipo = "coloquio"
        elseif clave(parte or ""):find("actividades") then tipo = "actividad" end
        ev = { parte = parte, fechas = fechas, titulo = titulo, tipo = tipo,
               titulo_tex = titulo_latex(b.content, titulo),
               grupos = {}, extra = {}, n = #eventos + 1 }
        -- sedes: párrafo(s) que siguen al encabezado (uno por fecha)
        local parrafos, k = {}, i + 1
        while bloques[k] and (bloques[k].t == "Para" or bloques[k].t == "Plain")
              and palabra_sede(stringify(bloques[k].content)) and #parrafos < #fechas do
          parrafos[#parrafos + 1] = bloques[k]
          k = k + 1
        end
        ev.lugares, ev.renglones_sede = sede_de(parrafos)
        if #ev.lugares == 0 then io.stderr:write("Sin sede: " .. texto .. "\n") end
        i = k - 1
        table.insert(eventos, ev)
      else
        ev = nil
        if b.level == 2 then
          local c = clave(texto)
          mayor = c:find("coloquio") and "coloquio" or (c == "sedes" and "sedes") or c
        end
      end

    elseif b.t == "Header" and b.level == 3 then
      local texto = stringify(b.content)
      en_programa = ev ~= nil and ev.tipo == "concierto" and clave(texto) == "programa"
      if en_programa then grupo = nil end

    elseif b.t == "Header" then
      en_programa = false

    elseif mayor == "sedes" and (b.t == "Para" or b.t == "Plain") and b.content[1]
           and b.content[1].t == "Strong" then
      local rs = renglones(b.content)
      sedes[#sedes + 1] = { nombre = stringify(rs[1]), direccion = rs[2] and stringify(rs[2]) or "",
                            palabra = palabra_sede(stringify(rs[1])), salas = {} }

    elseif ev and ev.tipo ~= "concierto" and (b.t == "Para" or b.t == "Plain") then
      -- actividades académicas: sus párrafos breves (subtítulo, libro,
      -- participantes); coloquio: solo los párrafos con participantes
      local t = clave(stringify(b.content))
      if #t < 300 and (ev.tipo == "actividad" or t:find("ponente") or t:find("moderador")
                       or t:find("participantes")) then
        -- el papel («ponente», «moderadora»…), más ligero que los nombres,
        -- como el de los intérpretes; los nombres, sin cortarse
        local sin_saltos = pandoc.Inlines(b.content):walk({
          LineBreak = function() return pandoc.Space() end,
          SoftBreak = function() return pandoc.Space() end,
          Strong = function(el)
            if stringify(el):match("^%l") then
              return pandoc.RawInline("latex", "\\papel{" .. latex(el.content) .. "}")
            end
          end })
        -- y el que va en texto normal tras una coma («…, imparte»)
        local partes, actual = {}, pandoc.Inlines({})
        local function cerrar(sep)
          for k = #actual - 2, 1, -1 do
            local x, y, z = actual[k], actual[k + 1], actual[k + 2]
            local primera = z.t == "Str" and clave(z.text):gsub("%p", "") or ""
            if x.t == "Str" and x.text:sub(-1) == "," and y.t == "Space" and PAPELES[primera] then
              local papel = pandoc.Inlines({})
              for j = k + 2, #actual do papel:insert(actual[j]) end
              for j = #actual, k + 2, -1 do actual:remove(j) end
              actual:insert(pandoc.RawInline("latex", "\\papel{" .. latex(papel) .. "}"))
              break
            end
          end
          partes[#partes + 1] = nombre_latex(actual) .. sep
          actual = pandoc.Inlines({})
        end
        for _, el in ipairs(sin_saltos) do
          if el.t == "Str" and el.text:sub(-1) == ";" then
            if el.text ~= ";" then actual:insert(pandoc.Str(el.text:sub(1, -2))) end
            cerrar("; ")
          else
            actual:insert(el)
          end
        end
        cerrar("")
        table.insert(ev.extra, table.concat(partes))
      end

    elseif en_programa and ev then
      if b.t == "HorizontalRule" then
        tras_obras = true
      elseif (b.t == "Para" or b.t == "Plain") and #b.content == 1 and b.content[1].t == "Strong"
             and sig and sig.t == "BulletList" then
        -- compositor
        if not grupo or tras_obras then nuevo_grupo() end
        table.insert(grupo.obras, { compositor = nombre_latex(b.content[1].content),
          nombre = trim(stringify(b.content[1].content)), titulos = {} })
      elseif b.t == "BulletList" then
        -- obras sin compositor encabezándolas (p. ej. una improvisación)
        if not grupo or tras_obras then nuevo_grupo() end
        if #grupo.obras == 0 then
          table.insert(grupo.obras, { compositor = "", nombre = "", titulos = {} })
        end
        local actual = grupo.obras[#grupo.obras]
        local hay_obra = #actual.titulos > 0
        for _, item in ipairs(b.content) do
          local primero = item[1]
          local inl = (primero and (primero.t == "Plain" or primero.t == "Para")) and primero.content or pandoc.List()
          local titulo, con_dur = partir_obra(inl)
          local txt = stringify(titulo)
          if txt:find("Estreno mundial") or txt:find("Estreno en México") then
            -- leyenda escrita como viñeta
          elseif not con_dur and not tiene_anio(txt) and hay_obra then
            -- movimiento: se omite
          else
            local texto, marcas = titulo_corto(titulo)
            table.insert(actual.titulos, { texto = texto, marcas = marcas })
            hay_obra = true
          end
        end
      elseif (b.t == "Para" or b.t == "Plain") and b.content[1] and b.content[1].t == "Span"
             and b.content[1].classes:includes("solista") then
        -- solista de la última obra
        if grupo and #grupo.obras > 0 then
          local actual = grupo.obras[#grupo.obras]
          local ultima = actual.titulos[#actual.titulos]
          if ultima then
            local sin_negritas = pandoc.Inlines(b.content[1].content):walk({
              Strong = function(el) return el.content end })
            ultima.solistas = ultima.solistas or {}
            for _, sol in ipairs(interpretes_de(sin_negritas)) do table.insert(ultima.solistas, sol) end
          end
        end
      elseif (b.t == "Para" or b.t == "Plain") and grupo then
        local t = trim(stringify(b.content))
        local solo_cursiva = #b.content == 1 and b.content[1].t == "Emph"
        local rs = renglones(b.content)
        -- prosa (texto largo sin saltos de línea) no es una lista de intérpretes
        local prosa = #rs == 1 and #t >= 260
        if t ~= "" and not solo_cursiva and not t:match("^INTERMEDIO") and not prosa then
          -- ¿lista de integrantes de un conjunto? (renglones sin negritas que
          -- siguen al nombre del conjunto, en el mismo párrafo o en el anterior).
          -- Los de conjuntos pequeños (hasta tres) se conservan.
          local tras_nombre = grupo.ultimo_nombre_solo and not (rs[1][1] and rs[1][1].t == "Strong")
          local conjunto = rs[1][1] and rs[1][1].t == "Strong" and #rs > 1
          local miembros = 0
          for k, r in ipairs(rs) do
            if not (r[1] and r[1].t == "Strong") and (tras_nombre or (conjunto and k > 1)) then
              miembros = miembros + 1
            end
          end
          for k, r in ipairs(rs) do
            local rt = trim(stringify(r))
            if rt ~= "" and rt ~= "INTERMEDIO" then
              local negrita = r[1] and r[1].t == "Strong"
              local sin_saltos = pandoc.Inlines(r):walk({ LineBreak = function() return pandoc.Space() end })
              table.insert(grupo.interpretes, { texto = rt, latex = interpretes_latex(sin_saltos),
                integrante = not negrita and miembros > 3 and (tras_nombre or (conjunto and k > 1)) })
            end
          end
          -- un nombre de conjunto solo (p. ej. «**Black Noise Ensamble**»)
          grupo.ultimo_nombre_solo = #rs == 1 and #b.content == 1 and b.content[1].t == "Strong"
          tras_obras = true
        end
      end
    end
    i = i + 1
  end

  if os.getenv("RESUMEN_DEPURAR") then
    for _, e in ipairs(eventos) do
      local nobras = 0
      for _, g in ipairs(e.grupos) do for _, o in ipairs(g.obras) do nobras = nobras + #o.titulos end end
      io.stderr:write(string.format("%s\t%d\n", e.titulo, nobras))
    end
  end

  -- ---------------------------------------------------------------------------
  -- Clave de sedes: letras en el orden de «## Sedes»; una por sala usada
  -- ---------------------------------------------------------------------------
  local por_palabra = {}
  for _, s in ipairs(sedes) do if s.palabra then por_palabra[s.palabra] = s end end
  -- La sala: lo que sigue al nombre del recinto («Palacio de Bellas Artes,
  -- Sala Principal» → «Sala Principal»; «Casa Rafael Galván, UAM» → nada)
  local function sala_de(renglon, sede)
    local partes = {}
    for parte in (renglon .. ","):gmatch("%s*([^,]+),") do partes[#partes + 1] = trim(parte) end
    local k = 1
    while partes[k] and clave(sede.nombre):find(clave(partes[k]), 1, true) do k = k + 1 end
    return table.concat(partes, ", ", k)
  end
  for _, e in ipairs(eventos) do
    e.claves = {}
    for k, lugar in ipairs(e.lugares) do
      local sede = por_palabra[palabra_sede(lugar)]
      if sede then
        local sala = sala_de(e.renglones_sede[k] or lugar, sede)
        if not sede.salas[sala] then
          sede.salas[sala] = { orden = #sede.salas + 1 }
          table.insert(sede.salas, sala)
        end
        e.claves[k] = { sede = sede, sala = sala }
      else
        io.stderr:write("Sede no encontrada en «## Sedes»: " .. lugar .. "\n")
      end
    end
  end
  local letra = 0
  local LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  for _, s in ipairs(sedes) do
    for _, sala in ipairs(s.salas) do
      letra = letra + 1
      s.salas[sala].letra = LETRAS:sub(letra, letra)
    end
  end
  local function letra_de(e, k)
    local c = e.claves[k] or e.claves[1]
    return c and c.sede.salas[c.sala].letra or ""
  end

  -- ---------------------------------------------------------------------------
  -- Agenda
  -- ---------------------------------------------------------------------------
  local out = {}
  local function emit(s) out[#out + 1] = s end

  local function seccion_agenda(nombre, filtro)
    local filas = {}
    for _, e in ipairs(eventos) do
      if filtro(e) then
        for k, f in ipairs(e.fechas) do
          filas[#filas + 1] = { e = e, f = f, k = k }
        end
      end
    end
    if #filas == 0 then return end
    table.sort(filas, function(a, b)
      if a.f.orden ~= b.f.orden then return a.f.orden < b.f.orden end
      return a.e.n < b.e.n
    end)
    emit("\\agendaparte{" .. nombre .. "}")
    local dia_previo
    for _, r in ipairs(filas) do
      local dia = etiqueta_dia(r.f)
      local macro = r.e.tipo == "concierto" and "\\ev" or "\\act"
      emit(string.format("%s{%s}{%s}{%s}{%s}", macro,
        dia ~= dia_previo and escape(dia) or "", hora_texto(r.f.hora), r.e.titulo_tex, letra_de(r.e, r.k)))
      dia_previo = dia
    end
  end

  local function es(p) return function(e) return clave(e.parte or ""):find(p) ~= nil end end
  emit("\\begin{agenda}")
  seccion_agenda("Ciudad de México", function(e)
    return es("ciudad de mexico")(e) or e.tipo ~= "concierto"
  end)
  seccion_agenda("En los estados", function(e) return e.tipo == "concierto" and es("estados")(e) end)
  seccion_agenda("Ecos del Foro", function(e) return e.tipo == "concierto" and es("ecos")(e) end)
  emit("\\agendaparte{Sedes}\\label{sedes}")
  for _, s in ipairs(sedes) do
    if #s.salas > 0 then
      local direccion = s.direccion:gsub(", Ciudad de México$", "")
      for k, sala in ipairs(s.salas) do
        local nombre = escape(s.nombre)
        if sala ~= "" then nombre = nombre .. ", " .. escape(sala) end
        emit(string.format("\\sede{%s}{%s}{%s}", s.salas[sala].letra, nombre,
          k == 1 and escape(direccion) or ""))
      end
    end
  end
  emit("\\end{agenda}")

  -- ---------------------------------------------------------------------------
  -- Programas: por concierto, sus intérpretes y las personas compositoras
  -- («Obras de A, B y C»), sin los títulos; y cuántos estrenos tiene.
  -- ---------------------------------------------------------------------------
  -- «A, B y C»; «e» ante /i/ (Iván, Ignacio, Hilda; no Iannis)
  local function unir(items)
    if #items <= 1 then return items[1] and items[1].latex or "" end
    local ult = items[#items].texto
    local conj = "y"
    local resto
    if ult:sub(1, 1) == "I" then resto = ult:sub(2)
    elseif ult:sub(1, 2) == "Í" then resto = ult:sub(3)
    elseif ult:sub(1, 2) == "Hi" then resto = ult:sub(3)
    elseif ult:sub(1, 3) == "Hí" then resto = ult:sub(4) end
    if resto and not clave(resto):match("^[aeiou]") then conj = "e" end
    local ls = {}
    for k = 1, #items - 1 do ls[#ls + 1] = items[k].latex end
    -- la «y» va con el nombre que sigue (no al final del renglón)
    return table.concat(ls, ", ") .. " " .. conj .. "~" .. items[#items].latex
  end

  local function texto_obras(g)
    local comps, vistos_c, sin_comp, n = {}, {}, {}, 0
    for _, o in ipairs(g.obras) do
      n = n + #o.titulos
      local generico = clave(o.nombre):find("tradicional") or clave(o.nombre):find("anonimo")
        or clave(o.nombre):find("popular")
      if generico and #o.titulos > 0 then
        -- «Canciones tradicionales»: va aparte, en minúsculas
        local t = o.compositor:gsub("^(\\%a+{)(%u)", function(a, b) return a .. b:lower() end)
        t = t:gsub("^(%u)", function(b) return b:lower() end)
        sin_comp[#sin_comp + 1] = { latex = t, texto = "" }
      elseif o.compositor ~= "" then
        if not vistos_c[o.nombre] and #o.titulos > 0 then
          vistos_c[o.nombre] = true
          comps[#comps + 1] = { latex = o.compositor, texto = o.nombre }
        end
      else
        for _, t in ipairs(o.titulos) do sin_comp[#sin_comp + 1] = { latex = t.texto, texto = "" } end
      end
    end
    local partes = {}
    if #comps > 0 then
      partes[#partes + 1] = ((n - #sin_comp) <= 1 and "Obra de " or "Obras de ") .. unir(comps)
    end
    if #sin_comp > 0 then partes[#partes + 1] = unir(sin_comp) end
    if #partes == 0 then return "" end
    return table.concat(partes, "; ") .. "."
  end

  -- intérpretes del grupo y solistas de obras concretas
  local function texto_interpretes(g)
    local t, texto = condensar_interpretes(g.interpretes)
    local plano = clave(texto)
    for _, o in ipairs(g.obras) do
      for _, ti in ipairs(o.titulos) do
        for _, sol in ipairs(ti.solistas or {}) do
          local nombre = clave(trim(sol.texto:match("^([^,]+)") or sol.texto))
          if not plano:find(nombre, 1, true) then
            t = (t ~= "" and t .. "; " or "") .. sol.latex
            plano = plano .. " " .. nombre
          end
        end
      end
    end
    return t
  end

  local function contar_estrenos(e, total, vistas)
    local mundiales, mexico = 0, 0
    for _, g in ipairs(e.grupos) do
      for _, o in ipairs(g.obras) do
        for _, t in ipairs(o.titulos) do
          local llave = clave(o.nombre .. "|" .. t.texto)
          if t.marcas == "*" then mundiales = mundiales + 1
          elseif t.marcas == "**" then mexico = mexico + 1 end
          if t.marcas ~= "" and not vistas[llave] then
            vistas[llave] = true
            total[#t.marcas] = total[#t.marcas] + 1
          end
        end
      end
    end
    return mundiales, mexico
  end

  local function frase_estrenos(mundiales, mexico)
    local partes = {}
    if mundiales > 0 then
      partes[#partes + 1] = mundiales .. (mundiales == 1 and " estreno mundial" or " estrenos mundiales")
    end
    if mexico > 0 then
      partes[#partes + 1] = mexico .. (mexico == 1 and " estreno" or " estrenos") .. " en México"
    end
    return table.concat(partes, " y ")
  end

  local function fecha_larga(e)
    local fs = {}
    for _, f in ipairs(e.fechas) do fs[#fs + 1] = escape(etiqueta_dia(f)) .. " · " .. hora_texto(f.hora) end
    return table.concat(fs, " / ")
  end

  local function lugares(e)
    local ls = {}
    for _, l in ipairs(e.lugares) do
      if ls[#ls] ~= l then ls[#ls + 1] = l end
    end
    for k, l in ipairs(ls) do ls[k] = escape(l) end
    return table.concat(ls, " / ")
  end

  -- primero se recorren para contar los estrenos del Foro (sin repetir)
  local total, vistas_estreno = { 0, 0 }, {}
  for _, e in ipairs(eventos) do
    if e.tipo == "concierto" then
      -- un programa que se repite se da completo (no se menciona que se
      -- repite); sus estrenos cuentan una sola vez en el total
      e.mundiales, e.mexico = contar_estrenos(e, total, vistas_estreno)
    end
  end

  emit("\\begin{programas}{" .. frase_estrenos(total[1], total[2]) .. "}")
  local parte_previa
  for _, e in ipairs(eventos) do
    if e.tipo == "concierto" then
      if e.parte ~= parte_previa then
        local nombre = ({ ["conciertos en ciudad de mexico"] = "Ciudad de México",
          ["conciertos en los estados"] = "En los estados",
          ["ecos del foro"] = "Ecos del Foro" })[clave(e.parte or "")] or escape(e.parte or "")
        emit("\\programaparte{" .. nombre .. "}")
        parte_previa = e.parte
      end
      local letras = {}
      for k = 1, #e.fechas do
        local l = letra_de(e, k)
        if l ~= "" and letras[#letras] ~= l then letras[#letras + 1] = l end
      end
      local ls = {}
      for _, l in ipairs(letras) do ls[#ls + 1] = "\\letra{" .. l .. "}" end
      emit(string.format("\\concierto{%s}{%s}{%s}{%s}", fecha_larga(e), table.concat(ls, ""),
        e.titulo_tex, lugares(e)))
      for _, g in ipairs(e.grupos) do
        local it = texto_interpretes(g)
        local ob = texto_obras(g)
        if it ~= "" or ob ~= "" then
          emit(string.format("\\grupo{%s}{%s}", it, ob))
        end
      end
      local fe = frase_estrenos(e.mundiales, e.mexico)
      if fe ~= "" then emit("\\estrenos{" .. fe .. "}") end
      emit("\\finconcierto")
    end
  end
  -- Actividades académicas y Coloquio
  local hay = false
  for _, e in ipairs(eventos) do
    if e.tipo ~= "concierto" then
      if not hay then
        emit("\\programaparte{Actividades académicas y Coloquio Enríquez 100}")
        hay = true
      end
      emit(string.format("\\actividad{%s}{%s}{%s}{%s}", fecha_larga(e),
        "\\letra{" .. letra_de(e, 1) .. "}", e.titulo_tex, table.concat(e.extra, "; ")))
    end
  end
  emit("\\end{programas}")

  local logos = logos_de(doc)
  if #logos > 0 then
    emit("\\paginalogos{" .. table.concat(logos, "\\logosep ") .. "}")
  else
    emit("\\cierre")
  end

  -- Créditos: los del 48º FIMNME («## Créditos») y el directorio de la
  -- Coordinación Nacional de Música y Ópera («## Directorio»)
  local cred, tomar = {}, false
  local function quiero(titulo)
    local c = clave(titulo)
    return c:find("foro internacional de musica nueva", 1, true) ~= nil
        or c == "coordinacion nacional de musica y opera"
  end
  for _, b in ipairs(doc.blocks) do
    if b.t == "Header" and b.level <= 3 then
      tomar = b.level == 3 and quiero(stringify(b.content))
      if tomar then cred[#cred + 1] = "\\grupodirectorio{" .. latex(b.content) .. "}" end
    elseif tomar and (b.t == "Para" or b.t == "Plain") then
      cred[#cred + 1] = latex(b.content) .. "\\par"
    end
  end
  if #cred > 0 then emit("\\creditos{" .. table.concat(cred, "\n") .. "}") end

  -- Última página: directorio de la Secretaría de Cultura y del INBAL (el
  -- bloque «::: contraportada») con la pleca institucional
  local dir = {}
  doc.blocks:walk({ Div = function(div)
    if not div.classes:includes("contraportada") then return nil end
    for _, c in ipairs(div.content) do
      if c.t == "Header" then dir[#dir + 1] = "\\grupodirectorio{" .. latex(c.content) .. "}"
      elseif c.t == "Para" or c.t == "Plain" then dir[#dir + 1] = latex(c.content) .. "\\par" end
    end
  end })
  if #dir > 0 then emit("\\contraportada{" .. table.concat(dir, "\n") .. "}") end

  local bl = {}
  for _, s in ipairs(out) do bl[#bl + 1] = raw(s) end
  return pandoc.Pandoc(bl, doc.meta)
end
