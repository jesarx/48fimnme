-- =============================================================================
--  tipografia.lua — Ajustes de composición del texto (Programa general y
--  resumido). Lo usan automatizacion/fimnme.lua y resumen/resumen.lua:
--
--    nombres(inlines, límite)   marca los nombres propios («Pedro Antonio»,
--                               «Nuño de Buen», «Bellas Artes»; los muy
--                               largos, en dos partes) y los títulos breves en
--                               cursiva («No me basta») para no cortarlos.
--    atar_final(inlines, n)     une las n últimas palabras: el último renglón
--                               de un párrafo no queda con una sola palabra.
--    siglas(inlines)            las siglas van en versalitas (\siglas{UNAM})
--                               para que no destaquen dentro del texto.
--    componer(inlines)          pasa a LaTeX lo anterior.
--
--  Las uniones no son rígidas: entre las palabras de un nombre va una
--  penalización alta (TeX evita cortar ahí, pero puede hacerlo si no hay otra
--  salida, así que nunca se sale un renglón del margen), y las palabras
--  breves del nombre van sin división con guion.
-- =============================================================================

local T = pandoc.text
local M = {}

local CONECTORES = {
  de = true, del = true, la = true, las = true, los = true, da = true, das = true,
  di = true, dos = true, du = true, van = true, von = true, der = true, le = true,
}
local ANTES = { "(", "[", "«", "“", "‘", "¿", "¡", '"', "'" }
local DESPUES = { ")", "]", "»", "”", "’", ".", ",", ";", ":", "?", "!", "…", '"', "'" }
local CONTENEDORES = {
  Emph = true, Strong = true, Span = true, Quoted = true, SmallCaps = true,
  Underline = true, Strikeout = true, Link = true,
}

-- «(Pedro» → «(», «Pedro», «»;  «Antonio,» → «», «Antonio», «,»
local function partir(texto)
  local pre, suf = "", ""
  local otra = true
  while otra do
    otra = false
    for _, p in ipairs(ANTES) do
      if #texto > #p and texto:sub(1, #p) == p then
        pre, texto, otra = pre .. p, texto:sub(#p + 1), true
      end
    end
  end
  otra = true
  while otra do
    otra = false
    for _, p in ipairs(DESPUES) do
      if #texto > #p and texto:sub(-#p) == p then
        suf, texto, otra = p .. suf, texto:sub(1, -#p - 1), true
      end
    end
  end
  return pre, texto, suf
end

-- Palabra con mayúscula inicial y el resto en minúsculas (o compuesta con
-- guion: «Jean-Claude»)
local function capitalizada(nucleo)
  if nucleo == "" or nucleo:find("%d") or nucleo:gsub("[-']", ""):find("%p") then return false end
  for parte in nucleo:gmatch("[^-]+") do
    local primera, resto = T.sub(parte, 1, 1), T.sub(parte, 2)
    if primera == T.lower(primera) or resto == "" or resto ~= T.lower(resto) then return false end
  end
  return true
end

local function es_espacio(el)
  return el ~= nil and (el.t == "Space" or el.t == "SoftBreak")
end

-- Palabra de un nombre: «nombre» (con mayúscula o inicial: «M.») o
-- «conector» (de, del, la…); fin = lleva puntuación y cierra el nombre
local function palabra(el, primera)
  if el == nil or el.t ~= "Str" then return nil end
  local pre, nucleo, suf = partir(el.text)
  if pre ~= "" and not primera then return nil end
  if CONECTORES[nucleo] and pre == "" and suf == "" and not primera then return { tipo = "conector" } end
  if T.len(nucleo) == 1 and nucleo ~= T.lower(nucleo) and suf:sub(1, 1) == "." then
    return { tipo = "nombre", fin = suf ~= "." }
  end
  if capitalizada(nucleo) then return { tipo = "nombre", fin = suf ~= "" } end
  return nil
end

local function largo(xs, a, b)
  local n = 0
  for k = a, b do n = n + (xs[k].t == "Str" and T.len(xs[k].text) or 1) end
  return n
end

-- Cursiva breve (hasta tres palabras y 20 caracteres): un título que no se corta
local function cursiva_breve(el)
  if el.t ~= "Emph" then return false end
  local palabras = 0
  for _, c in ipairs(el.content) do
    if c.t == "Str" then palabras = palabras + 1
    elseif not es_espacio(c) then return false end
  end
  return palabras >= 2 and palabras <= 3 and largo(el.content, 1, #el.content) <= 20
end

function M.nombres(xs, limite)
  limite = limite or 26
  for _, el in ipairs(xs) do
    if CONTENEDORES[el.t] then el.content = M.nombres(el.content, limite) end
  end
  local rangos = {}
  local i = 1
  while i <= #xs do
    local w = palabra(xs[i], true)
    if w and w.tipo == "nombre" then
      local idx, tipos, j, fin = { i }, { "nombre" }, i, w.fin
      while not fin and es_espacio(xs[j + 1]) do
        local w2 = palabra(xs[j + 2], false)
        if not w2 then break end
        idx[#idx + 1], tipos[#tipos + 1] = j + 2, w2.tipo
        j, fin = j + 2, w2.fin
      end
      while #idx > 1 and tipos[#tipos] == "conector" do
        table.remove(idx); table.remove(tipos)
      end
      local function nombres_en(p, q)
        local c = 0
        for t = p, q do if tipos[t] == "nombre" then c = c + 1 end end
        return c
      end
      if nombres_en(1, #idx) >= 2 then
        local a, b = idx[1], idx[#idx]
        if largo(xs, a, b) <= limite then
          rangos[#rangos + 1] = { a, b }
        else
          -- muy largo: en dos partes, lo más parejas posible
          local mejor
          for k = 2, #idx do
            if tipos[k - 1] == "nombre" then
              local l1, l2 = largo(xs, a, idx[k - 1]), largo(xs, idx[k], b)
              if l1 <= limite and l2 <= limite and (not mejor or math.abs(l1 - l2) < mejor.d) then
                mejor = { k = k, d = math.abs(l1 - l2) }
              end
            end
          end
          if mejor then
            local k = mejor.k
            if nombres_en(1, k - 1) >= 2 then rangos[#rangos + 1] = { a, idx[k - 1] } end
            if #idx - k >= 1 and nombres_en(k, #idx) >= 1 then rangos[#rangos + 1] = { idx[k], b } end
          end
        end
      end
      i = j + 1
    else
      if cursiva_breve(xs[i]) then rangos[#rangos + 1] = { i, i } end
      i = i + 1
    end
  end
  if #rangos == 0 then return xs end
  local inicio = {}
  for _, r in ipairs(rangos) do inicio[r[1]] = r[2] end
  local out, k = pandoc.Inlines({}), 1
  while k <= #xs do
    if inicio[k] then
      local grupo = pandoc.Inlines({})
      for m = k, inicio[k] do grupo:insert(xs[m]) end
      out:insert(pandoc.Span(grupo, { class = "nombre" }))
      k = inicio[k] + 1
    else
      out:insert(xs[k])
      k = k + 1
    end
  end
  return out
end

-- Caracteres visibles de un elemento
local function largo_de(el)
  if el.t == "Str" then return T.len(el.text) end
  if es_espacio(el) then return 1 end
  if CONTENEDORES[el.t] then
    local n = 0
    for _, c in ipairs(el.content) do n = n + largo_de(c) end
    return n
  end
  return 0
end

local function tiene_espacio(el)
  if es_espacio(el) then return true end
  if CONTENEDORES[el.t] then
    for _, c in ipairs(el.content) do if tiene_espacio(c) then return true end end
  end
  return false
end

local function es_nombre(el)
  return el ~= nil and el.t == "Span" and el.classes:includes("nombre")
end

-- Largo de la última palabra de un elemento (o del nombre entero) y si dentro
-- de él empieza esa palabra
local function cola(el)
  if es_nombre(el) then return largo_de(el), true end
  if el.t == "Str" then return T.len(el.text), false end
  if CONTENEDORES[el.t] then
    local n = 0
    for m = #el.content, 1, -1 do
      local c = el.content[m]
      if es_espacio(c) then return n, true end
      local l, empieza = cola(c)
      n = n + l
      if empieza then return n, true end
    end
    return n, false
  end
  return 0, false
end

-- Largo de lo que queda pegado antes de xs[k]: la palabra o el nombre entero
local function antes_de(xs, k)
  local n = 0
  for j = k - 1, 1, -1 do
    local el = xs[j]
    if es_espacio(el) or el.t == "LineBreak" then break end
    local l, empieza = cola(el)
    n = n + l
    if empieza then break end
  end
  return n
end

local UNION_FINAL = "\\penalty7000\\ "   -- entre las dos últimas palabras
local UNION_NOMBRE = "\\penalty5000\\ "  -- entre las palabras de un nombre

-- Une las n últimas palabras, sin cruzar un salto de renglón ni formar un
-- bloque de más de «limite» caracteres (que no cabría en el renglón)
local function atar(xs, n, despues, limite)
  local k = #xs
  while k >= 1 and n > 0 do
    local el = xs[k]
    if es_espacio(el) then
      if antes_de(xs, k) + 1 + despues > limite then return 0, despues end
      xs[k] = pandoc.RawInline("latex", UNION_FINAL)
      n, despues = n - 1, despues + 1
    elseif el.t == "LineBreak" then
      return 0, despues
    elseif es_nombre(el) then
      -- un nombre o un título ya unido: se salta entero, y si es de varias
      -- palabras cuenta como una unión hecha
      despues = despues + largo_de(el)
      if tiene_espacio(el) then n = n - 1 end
    elseif CONTENEDORES[el.t] then
      local contenido = el.content
      n, despues = atar(contenido, n, despues, limite)
      el.content = contenido
    else
      despues = despues + largo_de(el)
    end
    k = k - 1
  end
  return n, despues
end

function M.atar_final(xs, n, limite)
  local espacios = 0
  pandoc.Inlines(xs):walk({ Space = function() espacios = espacios + 1 end,
                            SoftBreak = function() espacios = espacios + 1 end })
  if espacios >= 2 then atar(xs, n or 1, 0, limite or 26) end
  return xs
end

-- Números romanos (XX, XXI, III): no son siglas
local VALOR = { I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000 }
local function romano(s)
  if not s:match("^[IVXLCDM]+$") then return false end
  local total = 0
  for k = 1, #s do
    local v, sig = VALOR[s:sub(k, k)], VALOR[s:sub(k + 1, k + 1)] or 0
    total = total + (v < sig and -v or v)
  end
  local r, n = "", total
  for _, par in ipairs({ { 1000, "M" }, { 900, "CM" }, { 500, "D" }, { 400, "CD" }, { 100, "C" },
                         { 90, "XC" }, { 50, "L" }, { 40, "XL" }, { 10, "X" }, { 9, "IX" },
                         { 5, "V" }, { 4, "IV" }, { 1, "I" } }) do
    while n >= par[1] do r, n = r .. par[2], n - par[1] end
  end
  return r == s
end

function M.siglas(xs)
  local out = pandoc.Inlines({})
  for _, el in ipairs(xs) do
    if el.t == "Str" then
      local pre, nucleo, suf = partir(el.text)
      if T.len(nucleo) >= 2 and nucleo == T.upper(nucleo) and nucleo ~= T.lower(nucleo)
         and not nucleo:find("[%d%p]") and not romano(nucleo) then
        if pre ~= "" then out:insert(pandoc.Str(pre)) end
        out:insert(pandoc.RawInline("latex", "\\siglas{" .. nucleo .. "}"))
        if suf ~= "" then out:insert(pandoc.Str(suf)) end
      else
        out:insert(el)
      end
    else
      if CONTENEDORES[el.t] then el.content = M.siglas(el.content) end
      out:insert(el)
    end
  end
  return out
end

-- Pasa a LaTeX las marcas: en un nombre, entre las palabras la penalización, y
-- las palabras de hasta 9 letras sin división con guion (las más largas sí se
-- pueden dividir: en los renglones angostos junto a las fotos no cabrían)
local function componer_nombre(xs)
  local out = pandoc.Inlines({})
  for _, el in ipairs(xs) do
    if el.t == "Str" and T.len(el.text) <= 9 then
      out:insert(pandoc.RawInline("latex", "\\mbox{"))
      out:insert(el)
      out:insert(pandoc.RawInline("latex", "}"))
    elseif es_espacio(el) then
      out:insert(pandoc.RawInline("latex", UNION_NOMBRE))
    elseif CONTENEDORES[el.t] then
      el.content = componer_nombre(el.content)
      out:insert(el)
    else
      out:insert(el)
    end
  end
  return out
end

function M.componer(xs)
  local out = pandoc.Inlines({})
  for _, el in ipairs(xs) do
    if es_nombre(el) then
      out:extend(componer_nombre(el.content))
    else
      if CONTENEDORES[el.t] then el.content = M.componer(el.content) end
      out:insert(el)
    end
  end
  return out
end

-- Párrafo de texto corrido: todo lo anterior (primero los nombres, para que
-- la última palabra se una al nombre entero)
function M.parrafo(xs, limite)
  return M.componer(M.siglas(M.atar_final(M.nombres(xs, limite), 1, limite)))
end

return M
