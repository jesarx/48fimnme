-- =============================================================================
--  sitio.lua — Contenido del sitio web del 48.º FIMNME (Jekyll)
--
--  Lee el mismo fimnme2026-programa.md que el Programa general y escribe el
--  contenido del sitio (sitio/genera.sh lo ejecuta):
--
--    sitio/_conciertos/<etiqueta>.html   una página por concierto, actividad
--                                        académica o sesión del Coloquio: datos
--                                        en el encabezado YAML y el programa,
--                                        las fichas y las notas en HTML
--    sitio/_data/agenda.json             los días, con sus eventos
--    sitio/_data/sedes.json              sedes, direcciones y eventos de cada una
--    sitio/_data/foro.json               cifras del Foro (conciertos, estrenos…)
--    sitio/_data/secciones.json          partes del programa (Ciudad de México…)
--    sitio/_data/logos.json              todos los logotipos, sin repetir
--    sitio/_includes/generado/*.html     Coloquio (presentación), créditos y
--                                        directorio
--    build/sitio/recursos.tsv            fotos y logotipos que usa (los copia,
--                                        reducidos, sitio/recursos.py)
--
--  Las etiquetas de las páginas son las mismas que usa el Programa general para
--  sus referencias (vie-nov-6-inauguracion-osn-carrasco-hofele…), y las
--  remisiones «\pageref{conc:…}» del Markdown se vuelven enlaces.
--  Uso: pandoc fimnme2026-programa.md --metadata-file=fimnme2026-programa.yaml \
--         --lua-filter=sitio/sitio.lua -t plain -o /dev/null
-- =============================================================================

local stringify = pandoc.utils.stringify
local DESTINO = "sitio"

local function trim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

local ACENTOS = { ["á"] = "a", ["é"] = "e", ["í"] = "i", ["ó"] = "o", ["ú"] = "u",
  ["ü"] = "u", ["ñ"] = "n", ["Á"] = "a", ["É"] = "e", ["Í"] = "i", ["Ó"] = "o",
  ["Ú"] = "u", ["Ü"] = "u", ["Ñ"] = "n", ["à"] = "a", ["è"] = "e", ["ö"] = "o",
  ["ä"] = "a", ["ç"] = "c", ["ã"] = "a", ["ô"] = "o", ["ê"] = "e", ["å"] = "a",
  ["ø"] = "o", ["ł"] = "l", ["ń"] = "n", ["š"] = "s", ["č"] = "c", ["ž"] = "z",
  ["é"] = "e", ["\u{a0}"] = " " }

-- minúsculas sin acentos
local function clave(s)
  s = s:lower()
  for a, b in pairs(ACENTOS) do s = s:gsub(a, b) end
  return s
end

local function etiqueta(s)
  return (clave(s):gsub("[^%w]+", "-"):gsub("^-+", ""):gsub("-+$", ""))
end

local function urldecode(s)
  return (s:gsub("%%(%x%x)", function(h) return string.char(tonumber(h, 16)) end))
end

local function esc(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function escribir(ruta, texto)
  local f = assert(io.open(ruta, "w"))
  f:write(texto)
  f:close()
end

local function json(valor) return pandoc.json.encode(valor) end

-- -----------------------------------------------------------------------------
-- Manifiestos de fotos y logotipos (los preparan los scripts del programa)
-- -----------------------------------------------------------------------------
local FOTOS, LOGOS, RECURSOS = {}, {}, {}

local function cargar_manifiestos()
  local f = io.open("build/fotos/manifiesto.tsv", "r")
  if f then
    for linea in f:lines() do
      local orig, dest, tipo = linea:match("^([^\t]+)\t([^\t]+)\t?([^\t]*)$")
      if orig then FOTOS[orig] = { ruta = dest, tipo = tipo ~= "" and tipo or "circulo" } end
    end
    f:close()
  else
    io.stderr:write("Aviso: falta build/fotos/manifiesto.tsv\n")
  end
  f = io.open("build/logos/manifiesto.tsv", "r")
  if f then
    for linea in f:lines() do
      local k, ruta, w, h = linea:match("^(.-)\t(.-)\t(%d+)\t(%d+)$")
      if k then
        LOGOS[k] = LOGOS[k] or {}
        table.insert(LOGOS[k], { ruta = ruta, w = tonumber(w), h = tonumber(h) })
      end
    end
    f:close()
  else
    io.stderr:write("Aviso: falta build/logos/manifiesto.tsv\n")
  end
end

-- nombre del archivo en el sitio para un recurso de build/
local function recurso(tipo, ruta)
  local nombre = ruta:match("([^/]+)$")
  RECURSOS[tipo .. "\t" .. ruta] = nombre
  return nombre
end

local function foto(src)
  local m = FOTOS[urldecode(src)]
  if not m then
    io.stderr:write("Aviso (sitio): foto sin preparar: " .. src .. "\n")
    return nil
  end
  return { archivo = recurso("foto", m.ruta), tipo = m.tipo }
end

-- Bloque «::: logos» → lista de logotipos (archivo y proporción)
local function logos_de(div)
  local lista = {}
  div:walk({ Image = function(img)
    local partes = {}
    for _, k in ipairs({ "pagina", "partir", "realce", "recorte" }) do
      if img.attributes[k] then partes[#partes + 1] = k .. "=" .. img.attributes[k] end
    end
    for _, p in ipairs(LOGOS[img.src .. "|" .. table.concat(partes, ";")] or {}) do
      -- el mismo tamaño relativo que en el Programa general: ninguno mayor que
      -- los de Cultura e INBAL (máx. 6,5 mm de alto y 20 de ancho; aquí 1 mm = 6,4 px)
      local r = p.w / p.h
      local alto = math.max(3.2, math.min(6.5 * r ^ -0.45, 6.5))
      local ancho = alto * r
      if ancho > 20 then ancho, alto = 20, 20 / r end
      lista[#lista + 1] = { archivo = recurso("logo", p.ruta), proporcion = r,
                            alto = math.floor(alto * 6.4 + 0.5), ancho = math.floor(ancho * 6.4 + 0.5) }
    end
  end })
  return lista
end

-- -----------------------------------------------------------------------------
-- Fechas: «VIE | NOV 6, 20:00 h - Título»
-- -----------------------------------------------------------------------------
local MESES = { OCT = 10, NOV = 11, DIC = 12 }
local NOMBRE_MES = { [10] = "octubre", [11] = "noviembre", [12] = "diciembre" }
local NOMBRE_DIA = { LUN = "Lunes", MAR = "Martes", ["MIÉ"] = "Miércoles", JUE = "Jueves",
  VIE = "Viernes", ["SÁB"] = "Sábado", DOM = "Domingo" }

-- Horas: «12 h» y, si no son en punto, «13:30 h» (también se acepta «12:00 h»).
-- Dentro: «hora» = «12:00» (para ordenar y para el calendario) y «hora_txt» =
-- «12» o «13:30» (lo que se muestra, seguido de « h»).
local function partir_encabezado(texto)
  local izq, titulo = texto:match("^(.-%d h) %- (.*)$")
  if not izq then return nil end
  local fechas = {}
  for dia, mes, num, h in izq:gmatch("(%S+) | (%u+) (%d+), (%d[%d:]*) h") do
    local m = MESES[mes] or 11
    local hh, mm = h:match("^(%d+):?(%d*)$")
    local hora = string.format("%02d:%02d", tonumber(hh), tonumber(mm ~= "" and mm or "0"))
    fechas[#fechas + 1] = {
      dia = dia, mes = mes, num = tonumber(num), hora = hora,
      hora_txt = tonumber(hh) .. ((mm ~= "" and mm ~= "00") and (":" .. mm) or ""),
      iso = string.format("2026-%02d-%02d", m, tonumber(num)),
      texto_dia = (NOMBRE_DIA[dia] or dia) .. " " .. num .. " de " .. NOMBRE_MES[m],
      semana = NOMBRE_DIA[dia] or dia, nombre_mes = NOMBRE_MES[m],
      corto = dia .. " " .. num .. " " .. mes,
    }
  end
  if #fechas == 0 then return nil end
  return fechas, titulo
end

-- Las inlines del título (lo que sigue a « - »), con su formato
local function titulo_inlines(inlines)
  for k = 2, #inlines - 1 do
    local el = inlines[k]
    if el.t == "Str" and el.text == "-" and inlines[k - 1].t == "Space" and inlines[k + 1].t == "Space" then
      local resto = pandoc.List()
      for j = k + 2, #inlines do resto:insert(inlines[j]) end
      return resto
    end
  end
  return inlines
end

-- -----------------------------------------------------------------------------
-- Sedes: palabra clave que aparece en la sede del concierto y en «## Sedes»
-- (la misma lista que resumen/resumen.lua)
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
-- HTML
-- -----------------------------------------------------------------------------
local TITULOS = {}   -- etiqueta de cada evento → su título

local function destino_ref(ref)
  local conc, seccion = ref:match("^conc:([^:]+):?(.*)$")
  if not conc then return nil end
  return conc, "../" .. conc .. "/" .. (seccion ~= "" and ("#" .. seccion) or "")
end

-- Limpia el LaTeX que trae el Markdown: «la pág. \pageref{conc:…}» → «la
-- página de «Título»» con enlace; lo demás se quita
local function limpiar(bloques)
  bloques = pandoc.Blocks(bloques):walk({ Inlines = function(inls)
    local out, i = pandoc.Inlines({}), 1
    while i <= #inls do
      local a, b, c = inls[i], inls[i + 1], inls[i + 2]
      local ref = c and c.t == "RawInline" and c.text:match("^\\pageref{(.-)}$")
      local conc, destino = destino_ref(ref or "")
      if a.t == "Str" and a.text == "pág." and b and b.t == "Space" and conc then
        out:insert(pandoc.Str("página de"))
        out:insert(pandoc.Space())
        out:insert(pandoc.Link({ pandoc.Str("«" .. (TITULOS[conc] or "ese concierto") .. "»") }, destino))
        i = i + 3
      else
        out:insert(a)
        i = i + 1
      end
    end
    return out
  end })
  return bloques:walk({
    RawInline = function(r)
      if r.format == "tex" or r.format == "latex" then
        local ref = r.text:match("^\\pageref{(.-)}$")
        local conc, destino = destino_ref(ref or "")
        if conc then return pandoc.Link({ pandoc.Str("«" .. (TITULOS[conc] or "ver") .. "»") }, destino) end
        return {}
      end
    end,
    RawBlock = function(r)
      if r.format == "tex" or r.format == "latex" then return {} end
    end,
    -- marcas de estreno: «(2025)*» o «*Título*\*» → <span class="estreno">*</span>
    Str = function(s)
      local base, marcas = s.text:match("^(.-)(%*+)$")
      if base and (base == "" or base:match("%)$")) then
        return { pandoc.Str(base), pandoc.Span({ pandoc.Str(marcas) }, { class = "estreno" }) }
      end
    end,
  })
end

local function html(bloques)
  return trim(pandoc.write(pandoc.Pandoc(limpiar(bloques)), "html5", { wrap_text = "none" }))
end

local function html_inl(inlines)
  if not inlines or #inlines == 0 then return "" end
  return html({ pandoc.Plain(inlines) })
end

local function texto_plano(bloques)
  return trim(stringify(bloques)):gsub("%s+", " ")
end

-- ¿Párrafo que empieza con \hfill? (firma de una nota)
local function es_firma(b)
  return (b.t == "Para" or b.t == "Plain") and b.content[1] and b.content[1].t == "RawInline"
    and b.content[1].text:match("^\\hfill")
end

-- Bloques de texto (semblanzas, notas): firmas a la derecha
local function html_texto(bloques)
  local partes = {}
  for _, b in ipairs(bloques) do
    if es_firma(b) then
      local resto = pandoc.List()
      for k = 2, #b.content do resto:insert(b.content[k]) end
      partes[#partes + 1] = '<p class="firma">' .. html_inl(resto) .. "</p>"
    else
      partes[#partes + 1] = html({ b })
    end
  end
  return table.concat(partes, "\n")
end

-- -----------------------------------------------------------------------------
-- Programa
-- -----------------------------------------------------------------------------
local function solo_negrita(b)
  return (b.t == "Para" or b.t == "Plain") and #b.content == 1 and b.content[1].t == "Strong"
end

local function es_intermedio(b)
  return (b.t == "Para" or b.t == "Plain") and clave(texto_plano({ b })):match("^intermedio") ~= nil
end

local function solo_cursiva(b)
  return (b.t == "Para" or b.t == "Plain") and #b.content == 1 and b.content[1].t == "Emph"
end

local function es_solista(b)
  return (b.t == "Para" or b.t == "Plain") and b.content[1] and b.content[1].t == "Span"
    and b.content[1].classes:includes("solista")
end

local function tiene_anio(s) return s:find("%(%d%d%d%d") ~= nil or s:find("%d%d%d%d%)") ~= nil end

-- Una obra: «*Título* (2025)* \hfill 9' crédito» → título, duración, crédito
local function obra_html(item, previa)
  local primero = item[1]
  local inl = (primero and (primero.t == "Plain" or primero.t == "Para")) and primero.content or pandoc.List()
  local titulo, despues, partido = pandoc.List(), pandoc.List(), false
  for _, el in ipairs(inl) do
    if el.t == "RawInline" and el.text:match("^\\hfill") then
      partido = true
      -- «\hfill 9'» llega como RawInline «\hfill 9» + Str «’»
      local resto = trim(el.text:gsub("^\\hfill", ""))
      if resto ~= "" then despues:insert(pandoc.Str(resto)) end
    elseif partido then
      despues:insert(el)
    else
      titulo:insert(el)
    end
  end
  local dur, credito = "", pandoc.List()
  while despues[2] and despues[1].t == "Str" and despues[2].t == "Str" do
    despues[1] = pandoc.Str(despues[1].text .. despues[2].text)
    despues:remove(2)
  end
  if #despues > 0 then
    local primero_d = despues[1]
    if primero_d.t == "Str" and primero_d.text:match("^%d+[’']") then
      dur = primero_d.text
      for k = 2, #despues do credito:insert(despues[k]) end
    else
      credito = despues
    end
  end
  local txt = stringify(titulo)
  local movimiento = not partido and not tiene_anio(txt) and previa
  local clase = movimiento and "movimiento" or "obra"
  local h = '<li class="' .. clase .. '"><span class="obra-titulo">' .. html_inl(titulo) .. "</span>"
  if dur ~= "" then h = h .. '<span class="obra-duracion">' .. esc(dur:gsub("'", "’")) .. "</span>" end
  if #credito > 0 then
    while credito[1] and (credito[1].t == "Space" or credito[1].t == "SoftBreak") do credito:remove(1) end
    if #credito > 0 then h = h .. '<span class="obra-credito">' .. html_inl(credito) .. "</span>" end
  end
  -- movimientos (lista anidada)
  for k = 2, #item do
    if item[k].t == "BulletList" then
      local movs = {}
      for _, sub in ipairs(item[k].content) do
        movs[#movs + 1] = "<li>" .. html({ table.unpack(sub) }):gsub("^<p>(.*)</p>$", "%1") .. "</li>"
      end
      h = h .. '<ul class="movimientos">' .. table.concat(movs) .. "</ul>"
    end
  end
  return h .. "</li>", not movimiento
end

-- Intérpretes para las tarjetas de la agenda: nombres de conjuntos y personas
-- (sin instrumentos); de un conjunto, el nombre y quien lo dirige, no la lista
-- de integrantes (como en el Programa resumido)
local function renglones(inlines)
  local rs, actual = {}, pandoc.List()
  for _, el in ipairs(inlines) do
    if el.t == "LineBreak" then
      rs[#rs + 1] = actual
      actual = pandoc.List()
    elseif not (#actual == 0 and (el.t == "Space" or el.t == "SoftBreak")) then
      actual:insert(el)
    end
  end
  rs[#rs + 1] = actual
  return rs
end

local function resumir_interpretes(b, ev, estado)
  local rs = renglones(b.content)
  local function negrita(r) return r[1] and r[1].t == "Strong" end
  local tras_nombre = estado.nombre_solo and not negrita(rs[1])
  local conjunto = negrita(rs[1]) and #rs > 1
  local miembros = 0
  for k, r in ipairs(rs) do
    if not negrita(r) and (tras_nombre or (conjunto and k > 1)) then miembros = miembros + 1 end
  end
  for k, r in ipairs(rs) do
    local rt = trim(stringify(r))
    local dirige = clave(rt):find("direc") ~= nil
    if rt == "" or rt:find(" | ", 1, true) then
      -- renglón vacío o lista de integrantes «Nombre, instrumento | …»
    elseif negrita(r) then
      ev.interpretes[#ev.interpretes + 1] = trim(stringify(r[1].content))
    elseif miembros > 3 and (tras_nombre or (conjunto and k > 1)) and not dirige then
      -- integrante de un conjunto ya nombrado
    else
      local nombre = rt:match("^([^,]+),")
      if nombre then
        ev.interpretes[#ev.interpretes + 1] = trim(nombre)
      elseif not dirige then   -- «Director invitado» (sin nombre) no se lista
        ev.interpretes[#ev.interpretes + 1] = rt
      end
    end
  end
  estado.nombre_solo = #rs == 1 and #b.content == 1 and b.content[1].t == "Strong"
end

-- Texto del título de una obra (lo que va antes de «\hfill»), con sus marcas de estreno
local function titulo_obra(item)
  local primero = item[1]
  local partes = pandoc.List()
  if primero and (primero.t == "Plain" or primero.t == "Para") then
    for _, el in ipairs(primero.content) do
      if el.t == "RawInline" and el.text:match("^\\hfill") then break end
      partes:insert(el)
    end
  end
  return trim(stringify(partes))
end

-- Sección «Programa» → HTML; también reúne compositores, intérpretes y estrenos
local ESTRENOS_VISTOS, ESTRENOS_TOTAL = {}, { 0, 0 }

local function programa(bloques, ev)
  local partes, interpretes, estado = {}, {}, {}
  local compositor = ""
  local mundiales, mexico = 0, 0
  local function cerrar_interpretes()
    if #interpretes > 0 then
      partes[#partes + 1] = '<div class="interpretes">' .. table.concat(interpretes, "\n") .. "</div>"
      interpretes = {}
    end
  end
  for i, b in ipairs(bloques) do
    local sig = bloques[i + 1]
    if b.t == "HorizontalRule" then
      cerrar_interpretes()
      partes[#partes + 1] = '<hr class="separador-grupo">'
    elseif solo_negrita(b) and sig and sig.t == "BulletList" then
      cerrar_interpretes()
      local nombre = trim(stringify(b.content))
      partes[#partes + 1] = '<h4 class="compositor">' .. html_inl(b.content[1].content) .. "</h4>"
      compositor = nombre
      if not clave(nombre):find("tradicional") then ev.compositores[#ev.compositores + 1] = nombre end
    elseif b.t == "BulletList" then
      local items, previa = {}, false
      for _, item in ipairs(b.content) do
        local txt = titulo_obra(item)
        ev.titulos_obras[#ev.titulos_obras + 1] = txt
        local marcas = #(txt:match("(%*+)$") or "")
        if marcas == 2 then mexico = mexico + 1 elseif marcas == 1 then mundiales = mundiales + 1 end
        -- total del Foro: cada estreno una vez (como el Programa resumido)
        local llave = clave(compositor .. "|" .. txt)
        if marcas > 0 and not ESTRENOS_VISTOS[llave] then
          ESTRENOS_VISTOS[llave] = true
          ESTRENOS_TOTAL[marcas] = ESTRENOS_TOTAL[marcas] + 1
        end
        local h, es_obra = obra_html(item, previa)
        items[#items + 1] = h
        previa = previa or es_obra
      end
      partes[#partes + 1] = '<ul class="obras">' .. table.concat(items) .. "</ul>"
    elseif es_solista(b) then
      partes[#partes + 1] = '<p class="solista">' .. html_inl(b.content[1].content) .. "</p>"
    elseif es_intermedio(b) then
      cerrar_interpretes()
      partes[#partes + 1] = '<div class="intermedio"><span>Intermedio</span></div>'
    elseif solo_cursiva(b) then
      cerrar_interpretes()
      partes[#partes + 1] = '<p class="nota-breve">' .. html_inl(b.content[1].content) .. "</p>"
    elseif (b.t == "Para" or b.t == "Plain") and trim(stringify(b.content)) ~= "" then
      interpretes[#interpretes + 1] = html({ b })
      resumir_interpretes(b, ev, estado)
    elseif b.t ~= "Para" and b.t ~= "Plain" then
      cerrar_interpretes()
      partes[#partes + 1] = html({ b })
    end
  end
  cerrar_interpretes()
  -- solistas de obras concretas, también para el resumen
  for _, b in ipairs(bloques) do
    if es_solista(b) then
      for _, el in ipairs(b.content[1].content) do
        if el.t == "Strong" then ev.interpretes[#ev.interpretes + 1] = trim(stringify(el.content)) end
      end
    end
  end
  if mundiales + mexico > 0 then
    local ley = {}
    if mundiales > 0 then ley[#ley + 1] = '<span class="estreno">*</span> Estreno mundial' end
    if mexico > 0 then ley[#ley + 1] = '<span class="estreno">**</span> Estreno en México' end
    partes[#partes + 1] = '<p class="leyenda-estrenos">' .. table.concat(ley, " · ") .. "</p>"
  end
  ev.mundiales, ev.mexico = mundiales, mexico
  return table.concat(partes, "\n")
end

-- -----------------------------------------------------------------------------
-- Fichas (compositores, intérpretes) y notas
-- -----------------------------------------------------------------------------
local VISTAS = { bio = {}, nota = {} }   -- primera aparición: semblanza, foto y nota

local function partir_ficha(inlines)
  local n = #inlines
  if n > 0 and inlines[n].t == "Str" and inlines[n].text:match("%)$") then
    for i = n, 1, -1 do
      local el = inlines[i]
      if el.t == "Str" and el.text:match("^%(") then
        local nombre, detalle = pandoc.List(), pandoc.List()
        for j = 1, i - 1 do nombre:insert(inlines[j]) end
        for j = i, n do detalle:insert(inlines[j]) end
        while #nombre > 0 and nombre[#nombre].t == "Space" do nombre:remove(#nombre) end
        local d = stringify(detalle):gsub("^%(", ""):gsub("%)$", "")
        return nombre, d
      end
    end
  end
  return inlines, ""
end

local function imagen_sola(b)
  if b and b.t == "Para" and #b.content == 1 and b.content[1].t == "Image" then return b.content[1] end
  return nil
end

local function ficha_html(f, ev)
  local nombre_txt = trim(stringify(f.nombre))
  local id = "ficha-" .. etiqueta(nombre_txt)
  local clave_bio = clave(nombre_txt)
  -- En el sitio cada evento muestra completas las semblanzas y notas (en los
  -- PDF, las repetidas remiten a su página): si el Markdown no las repite, se
  -- toman de su primera aparición.
  local previa = VISTAS.bio[clave_bio]
  local foto_f = f.foto or (previa and previa.foto)
  local h = {}
  h[#h + 1] = '<article class="ficha" id="' .. id .. '">'
  h[#h + 1] = '<div class="ficha-cabeza">'
  if foto_f then
    h[#h + 1] = '<img class="ficha-foto' .. (foto_f.tipo ~= "circulo" and " ficha-foto-completa" or "") ..
      '" src="../../assets/fotos/' .. foto_f.archivo .. '" alt="' .. esc(nombre_txt) ..
      '" loading="lazy" width="120" height="120">'
  end
  h[#h + 1] = '<div><h3 class="ficha-nombre">' .. html_inl(f.nombre) .. "</h3>"
  if f.detalle ~= "" then h[#h + 1] = '<p class="ficha-detalle">' .. esc(f.detalle) .. "</p>" end
  h[#h + 1] = "</div></div>"
  local bio_html = #f.bio > 0 and html_texto(f.bio) or (previa and previa.html)
  if bio_html then
    h[#h + 1] = '<div class="ficha-texto">' .. bio_html .. "</div>"
    if not previa then VISTAS.bio[clave_bio] = { html = bio_html, foto = f.foto } end
  end
  for _, n in ipairs(f.notas) do
    local titulo_txt = trim(stringify(n.titulo))
    local nid = "nota-" .. etiqueta(titulo_txt)
    local clave_nota = clave(titulo_txt)
    local nprevia = VISTAS.nota[clave_nota]
    local nota_html = #n.bloques > 0 and html_texto(n.bloques) or (nprevia and nprevia.html)
    if nota_html then
      h[#h + 1] = '<details class="nota" id="' .. nid .. '"><summary><span class="nota-etiqueta">Nota al programa</span> ' ..
        html_inl(n.titulo) .. "</summary>" .. '<div class="nota-texto">' .. nota_html .. "</div></details>"
      if not nprevia then VISTAS.nota[clave_nota] = { html = nota_html } end
    end
  end
  h[#h + 1] = "</article>"
  return table.concat(h, "\n")
end

-- Sección de fichas → HTML
local function fichas(bloques, tipo, ev)
  local lista, actual, nota = {}, nil, nil
  local sueltos = {}
  local i = 1
  while i <= #bloques do
    local b = bloques[i]
    if b.t == "Header" and b.level == 4 then
      local nombre, detalle = partir_ficha(b.content)
      actual = { nombre = nombre, detalle = detalle, bio = {}, notas = {}, tipo = tipo }
      nota = nil
      local img = imagen_sola(bloques[i + 1])
      if img then actual.foto = foto(img.src); i = i + 1 end
      lista[#lista + 1] = actual
    elseif solo_negrita(b) and imagen_sola(bloques[i + 1]) then
      actual = { nombre = b.content[1].content, detalle = "", bio = {}, notas = {}, tipo = tipo,
                 foto = foto(imagen_sola(bloques[i + 1]).src) }
      nota = nil
      i = i + 1
      lista[#lista + 1] = actual
    elseif b.t == "Header" and b.level == 5 then
      nota = { titulo = b.content, bloques = {} }
      if actual then actual.notas[#actual.notas + 1] = nota else sueltos[#sueltos + 1] = nota end
    elseif b.t ~= "HorizontalRule" then
      if nota then nota.bloques[#nota.bloques + 1] = b
      elseif actual then actual.bio[#actual.bio + 1] = b
      else sueltos[#sueltos + 1] = { texto = b } end
    end
    i = i + 1
  end
  local h = {}
  for _, s in ipairs(sueltos) do
    if s.texto then h[#h + 1] = html_texto({ s.texto }) end
  end
  for _, f in ipairs(lista) do h[#h + 1] = ficha_html(f, ev) end
  return '<div class="fichas">' .. table.concat(h, "\n") .. "</div>"
end

local TIPO_SECCION = {
  ["personas compositoras"] = "comp", ["interpretes"] = "int", ["direccion y solistas"] = "int",
  ["solistas"] = "int", ["direccion"] = "int",
}

-- -----------------------------------------------------------------------------
-- Lectura del documento
-- -----------------------------------------------------------------------------
local SECCION_PARTE = {
  ["conciertos en ciudad de mexico"] = { id = "cdmx", nombre = "Ciudad de México" },
  ["conciertos en los estados"] = { id = "estados", nombre = "En los estados" },
  ["actividades academicas"] = { id = "actividades", nombre = "Actividades académicas" },
  ["ecos del foro"] = { id = "ecos", nombre = "Ecos del Foro" },
  ["enriquez | 100"] = { id = "coloquio", nombre = "Coloquio Manuel Enríquez 100" },
}

function Pandoc(doc)
  cargar_manifiestos()
  local bloques = doc.blocks
  local eventos = {}
  local sedes, region = {}, nil
  local parte, mayor = nil, nil
  local textos = { coloquio = {}, coloquio_intro = {}, creditos = {}, contraportada = {}, intros = {} }
  local coloquio_sub, en_colofon = nil, false

  -- 1. Partir el documento en eventos (bloques de cada uno) y secciones mayores
  local ev = nil
  local i, n = 1, #bloques
  while i <= n do
    local b = bloques[i]
    -- el colofón habla del libro impreso: no va en el sitio
    if b.t == "RawBlock" and b.text:match("^\\begin{colofon}") then en_colofon = true end
    if en_colofon then
      if b.t == "RawBlock" and b.text:match("\\end{colofon}") then en_colofon = false end
    elseif b.t == "RawBlock" and b.text:match("^\\part") then
      parte = clave(b.text:match("^\\part%*?{(.-)}") or "")
      mayor, ev = nil, nil
    elseif b.t == "Header" and (b.level == 2 or (b.level == 4 and mayor == "coloquio" and coloquio_sub == "programa")) then
      local texto = stringify(b.content)
      local fechas, titulo = partir_encabezado(texto)
      if fechas then
        local sec = SECCION_PARTE[parte or ""] or { id = "otros", nombre = "" }
        local tipo = "concierto"
        if sec.id == "actividades" then tipo = "actividad" elseif mayor == "coloquio" then tipo = "coloquio" end
        -- misma etiqueta que el Programa general: «vie nov 6 título»
        local slug = etiqueta(fechas[1].dia .. " " .. fechas[1].mes .. " " .. fechas[1].num .. " " .. titulo)
        ev = { slug = slug, url = "/conciertos/" .. slug .. "/", fechas = fechas, titulo_txt = titulo,
               titulo = html_inl(titulo_inlines(b.content)), tipo = tipo, seccion = sec,
               bloques = {}, compositores = {}, interpretes = {}, titulos_obras = {}, logos = {},
               orden = #eventos + 1 }
        eventos[#eventos + 1] = ev
        TITULOS[slug] = titulo
      else
        ev = nil
        if b.level == 2 then
          local c = clave(texto)
          mayor = c:find("coloquio") and "coloquio" or c
          coloquio_sub = nil
        end
      end
    elseif b.t == "Header" and b.level == 3 and mayor == "coloquio" then
      ev = nil
      coloquio_sub = clave(stringify(b.content)):find("programa") and "programa" or "presentacion"
    elseif b.t == "Header" and b.level <= 3 and ev and ev.tipo == "coloquio" then
      ev = nil
    elseif ev then
      if b.t == "Div" and b.classes:includes("logos") then
        for _, l in ipairs(logos_de(b)) do ev.logos[#ev.logos + 1] = l end
      else
        ev.bloques[#ev.bloques + 1] = b
      end
    elseif not mayor and parte and (b.t == "Para" or b.t == "Plain") then
      -- texto que abre una parte («Conciertos fuera de las fechas del FIMNME 2026.»)
      local sec = (SECCION_PARTE[parte] or {}).id
      if sec then
        textos.intros[sec] = textos.intros[sec] or {}
        table.insert(textos.intros[sec], b)
      end
    elseif mayor == "coloquio" then
      if coloquio_sub == "programa" then textos.coloquio_intro[#textos.coloquio_intro + 1] = b
      else textos.coloquio[#textos.coloquio + 1] = b end
    elseif mayor == "sedes" then
      if b.t == "Header" and b.level == 3 then
        region = stringify(b.content)
      elseif (b.t == "Para" or b.t == "Plain") and b.content[1] and b.content[1].t == "Strong" then
        local lineas, actual = {}, pandoc.List()
        for _, el in ipairs(b.content) do
          if el.t == "LineBreak" then lineas[#lineas + 1] = trim(stringify(actual)); actual = pandoc.List()
          else actual:insert(el) end
        end
        if #actual > 0 then lineas[#lineas + 1] = trim(stringify(actual)) end
        sedes[#sedes + 1] = { id = etiqueta(lineas[1]), nombre = lineas[1], direccion = lineas[2] or "",
                              region = region or "", palabra = palabra_sede(lineas[1]), eventos = {} }
      end
    elseif mayor == "creditos" or mayor == "directorio" then
      if b.t == "Div" and b.classes:includes("contraportada") then
        for _, c in ipairs(b.content) do textos.contraportada[#textos.contraportada + 1] = c end
      elseif not (b.t == "RawBlock") then
        if b.t == "Header" and b.level == 3 then
          textos.creditos[#textos.creditos + 1] = pandoc.Header(3, b.content)
        else
          textos.creditos[#textos.creditos + 1] = b
        end
      end
    end
    if b.t == "Header" and b.level == 2 and not partir_encabezado(stringify(b.content)) then
      local c = clave(stringify(b.content))
      if c == "creditos" or c == "directorio" then
        textos.creditos[#textos.creditos + 1] = pandoc.Header(2, b.content)
      end
    end
    -- la contraportada va al final del documento, tras el colofón
    if b.t == "Div" and b.classes:includes("contraportada") and mayor ~= "creditos" and mayor ~= "directorio" then
      for _, c in ipairs(b.content) do textos.contraportada[#textos.contraportada + 1] = c end
    end
    i = i + 1
  end

  -- 2. Cada evento: sede, secciones y HTML
  for _, e in ipairs(eventos) do
    local bl = e.bloques
    local k = 1
    -- sede(s): párrafos que siguen al encabezado
    e.lugares = {}
    while bl[k] and (bl[k].t == "Para" or bl[k].t == "Plain") and palabra_sede(stringify(bl[k].content))
          and #e.lugares < #e.fechas do
      local lineas, actual = {}, pandoc.List()
      for _, el in ipairs(bl[k].content) do
        if el.t == "LineBreak" then lineas[#lineas + 1] = trim(stringify(actual)); actual = pandoc.List()
        else actual:insert(el) end
      end
      if #actual > 0 then lineas[#lineas + 1] = trim(stringify(actual)) end
      -- con varias fechas, cada sede va precedida de la suya: «Viernes 13 de noviembre, 19:00 h»
      if #lineas > 1 and lineas[1]:match("%d h$") then table.remove(lineas, 1) end
      e.lugares[#e.lugares + 1] = lineas
      k = k + 1
    end
    if #e.lugares == 0 then io.stderr:write("Aviso (sitio): sin sede: " .. e.titulo_txt .. "\n") end
    -- lo que va antes de la primera sección: subtítulos, notas breves o el texto de la actividad
    local previo, secciones, actual = {}, {}, nil
    for j = k, #bl do
      local b = bl[j]
      if b.t == "Header" and b.level == 3 then
        actual = { titulo = stringify(b.content), clave = clave(stringify(b.content)), bloques = {} }
        secciones[#secciones + 1] = actual
      elseif actual then
        actual.bloques[#actual.bloques + 1] = b
      elseif b.t ~= "HorizontalRule" then
        previo[#previo + 1] = b
      end
    end
    -- subtítulo («Concierto inaugural», «Monográfico Saariaho»…; va en la
    -- cabecera de la página) y, en actividades y Coloquio, quienes participan
    local subtitulos, participantes, resto = {}, {}, {}
    for _, b in ipairs(previo) do
      local t = texto_plano({ b })
      if t ~= "" then
        if e.tipo == "concierto" or solo_cursiva(b) then subtitulos[#subtitulos + 1] = t
        else
          participantes[#participantes + 1] = t
          resto[#resto + 1] = b
        end
      end
    end
    e.previo = #resto > 0 and html_texto(resto) or ""
    e.subtitulo = table.concat(subtitulos, " · ")
    e.participantes = table.concat(participantes, " · ")
    e.secciones = {}
    for _, s in ipairs(secciones) do
      local id = etiqueta(s.titulo)
      local cuerpo
      if s.clave == "programa" then
        cuerpo = programa(s.bloques, e)
      elseif TIPO_SECCION[s.clave] then
        local titulo = s.titulo
        local nf = 0
        for _, b in ipairs(s.bloques) do if b.t == "Header" and b.level == 4 then nf = nf + 1 end end
        if s.clave == "interpretes" and nf == 1 then titulo = "Intérprete" end
        s.titulo = titulo
        cuerpo = fichas(s.bloques, TIPO_SECCION[s.clave], e)
      else
        cuerpo = '<div class="texto-nota">' .. html_texto(s.bloques) .. "</div>"
      end
      e.secciones[#e.secciones + 1] = { id = id, titulo = s.titulo, html = cuerpo }
    end
    -- sede de cada fecha en «## Sedes»
    e.sedes = {}
    for f = 1, #e.fechas do
      local pal = palabra_sede(table.concat(e.lugares[f] or e.lugares[1] or { "" }, " "))
      for _, s in ipairs(sedes) do
        if pal and s.palabra == pal then
          e.sedes[f] = s
          s.eventos[#s.eventos + 1] = { evento = e, fecha = e.fechas[f] }
          break
        end
      end
      if not e.sedes[f] then io.stderr:write("Aviso (sitio): sede sin dirección: " .. e.titulo_txt .. "\n") end
    end
    e.sede = e.sedes[1]
  end

  -- 3. Escribir las páginas
  local dir = DESTINO .. "/_conciertos"
  pandoc.system.make_directory(dir, true)
  for _, archivo in ipairs(pandoc.system.list_directory(dir)) do
    if archivo:match("%.html$") then os.remove(dir .. "/" .. archivo) end
  end

  local function lista_texto(xs)
    local vistos, ys = {}, {}
    for _, x in ipairs(xs) do
      if x ~= "" and not vistos[x] then vistos[x] = true; ys[#ys + 1] = x end
    end
    if #ys <= 1 then return ys[1] or "" end
    return table.concat(ys, ", ", 1, #ys - 1) .. " y " .. ys[#ys]
  end

  local por_dia = {}
  for _, e in ipairs(eventos) do
    e.resumen_interpretes = e.tipo == "concierto" and lista_texto(e.interpretes) or e.participantes
    local comps = lista_texto(e.compositores)
    e.resumen_obras = comps ~= "" and ((#e.compositores == 1 and "Obra" or "Obras") .. " de " .. comps) or ""
    if #e.compositores > 1 then e.resumen_obras = "Obras de " .. comps end
    local estrenos = {}
    if (e.mundiales or 0) > 0 then
      estrenos[#estrenos + 1] = e.mundiales .. (e.mundiales == 1 and " estreno mundial" or " estrenos mundiales")
    end
    if (e.mexico or 0) > 0 then
      estrenos[#estrenos + 1] = e.mexico .. (e.mexico == 1 and " estreno en México" or " estrenos en México")
    end
    e.estrenos = table.concat(estrenos, " y ")
    local lugares = {}
    for _, l in ipairs(e.lugares) do lugares[#lugares + 1] = table.concat(l, ", ") end
    local fm = {
      title = e.titulo_txt, titulo_html = e.titulo, slug = e.slug, orden = e.orden,
      tipo = e.tipo, seccion = e.seccion.id, seccion_nombre = e.seccion.nombre,
      fechas = {}, lugares = lugares, sede = e.sede and e.sede.id or "",
      sede_nombre = e.sede and e.sede.nombre or "", direccion = e.sede and e.sede.direccion or "",
      interpretes = e.resumen_interpretes, obras = e.resumen_obras, estrenos = e.estrenos,
      subtitulo = e.subtitulo,
      secciones = {}, logos = {}, render_with_liquid = false,
      description = (e.resumen_interpretes ~= "" and e.resumen_interpretes .. ". " or "") .. e.resumen_obras,
    }
    for k, f in ipairs(e.fechas) do
      local s = e.sedes[k] or {}
      fm.fechas[#fm.fechas + 1] = { iso = f.iso, hora = f.hora_txt, dia = f.texto_dia, corto = f.corto,
        semana = f.semana, numero = f.num, mes = f.nombre_mes,
        -- para «Agregar al calendario» (duración supuesta: dos horas)
        inicio = f.iso:gsub("-", "") .. "T" .. string.format("%04d", tonumber((f.hora:gsub(":", "")))) .. "00",
        fin = f.iso:gsub("-", "") .. "T" .. string.format("%04d", math.min(tonumber((f.hora:gsub(":", ""))) + 200, 2359)) .. "00",
        lugar = lugares[k] or lugares[1] or "", sede = s.id or "", sede_nombre = s.nombre or "",
        direccion = s.direccion or "" }
    end
    for _, s in ipairs(e.secciones) do fm.secciones[#fm.secciones + 1] = { id = s.id, titulo = s.titulo } end
    for _, l in ipairs(e.logos) do fm.logos[#fm.logos + 1] = l end
    local cuerpo = {}
    if e.previo ~= "" then cuerpo[#cuerpo + 1] = '<div class="evento-previo">' .. e.previo .. "</div>" end
    for _, s in ipairs(e.secciones) do
      cuerpo[#cuerpo + 1] = '<section class="seccion seccion-' .. s.id .. '" id="' .. s.id .. '">' ..
        '<h2 class="seccion-titulo">' .. esc(s.titulo) .. "</h2>\n" .. s.html .. "</section>"
    end
    escribir(dir .. "/" .. e.slug .. ".html", "---\n" .. json(fm) .. "\n---\n" .. table.concat(cuerpo, "\n") .. "\n")
    -- agenda
    for k, f in ipairs(e.fechas) do
      local dia = por_dia[f.iso]
      if not dia then
        dia = { fecha = f.iso, dia = f.texto_dia, corto = f.corto, semana = f.semana,
                numero = f.num, mes = f.nombre_mes, eventos = {} }
        por_dia[f.iso] = dia
      end
      local lugar = e.lugares[k] or e.lugares[1] or {}
      dia.eventos[#dia.eventos + 1] = {
        hora = f.hora_txt, momento = f.iso .. "T" .. f.hora, titulo = e.titulo_txt,
        titulo_html = e.titulo, url = e.url, tipo = e.tipo,
        seccion = e.seccion.id, seccion_nombre = e.seccion.nombre, lugar = table.concat(lugar, ", "),
        sede = e.sedes[k] and e.sedes[k].id or "", interpretes = e.resumen_interpretes, obras = e.resumen_obras,
        estrenos = e.estrenos, orden = e.orden, subtitulo = e.subtitulo,
        buscar = clave(table.concat({ e.titulo_txt, e.subtitulo, table.concat(lugar, " "),
                                      e.resumen_interpretes, e.resumen_obras,
                                      table.concat(e.titulos_obras, " ") }, " ")):gsub("[*]", ""),
      }
    end
  end

  -- 4. Datos: agenda, sedes, cifras
  local dias = {}
  for _, d in pairs(por_dia) do dias[#dias + 1] = d end
  table.sort(dias, function(a, b) return a.fecha < b.fecha end)
  for _, d in ipairs(dias) do
    table.sort(d.eventos, function(a, b)
      if a.momento ~= b.momento then return a.momento < b.momento end
      return a.orden < b.orden
    end)
  end
  pandoc.system.make_directory(DESTINO .. "/_data", true)
  escribir(DESTINO .. "/_data/agenda.json", json(dias) .. "\n")

  local datos_sedes = {}
  for _, s in ipairs(sedes) do
    if #s.eventos > 0 then
      local evs = {}
      table.sort(s.eventos, function(a, b)
        if a.fecha.iso ~= b.fecha.iso then return a.fecha.iso < b.fecha.iso end
        return a.evento.orden < b.evento.orden
      end)
      for _, x in ipairs(s.eventos) do
        evs[#evs + 1] = { titulo = x.evento.titulo_txt, titulo_html = x.evento.titulo, url = x.evento.url,
                          fecha = x.fecha.corto, hora = x.fecha.hora_txt, tipo = x.evento.tipo }
      end
      datos_sedes[#datos_sedes + 1] = { id = s.id, nombre = s.nombre, direccion = s.direccion,
                                        region = s.region, eventos = evs }
    end
  end
  escribir(DESTINO .. "/_data/sedes.json", json(datos_sedes) .. "\n")

  local cifras = { conciertos = 0, actividades = 0, coloquio = 0, sedes = #datos_sedes,
                   mundiales = ESTRENOS_TOTAL[1], mexico = ESTRENOS_TOTAL[2], dias = #dias }
  for _, e in ipairs(eventos) do
    if e.tipo == "concierto" and clave(e.titulo_txt):match("^instalacion") then
      cifras.instalaciones = (cifras.instalaciones or 0) + 1
    elseif e.tipo == "concierto" then cifras.conciertos = cifras.conciertos + 1
    elseif e.tipo == "actividad" then cifras.actividades = cifras.actividades + 1
    else cifras.coloquio = cifras.coloquio + 1 end
  end
  -- de fimnme2026-programa.yaml (genera.sh lo pasa con --metadata-file)
  cifras.estados = {}
  cifras.estados_nombres = {}   -- «CIUDAD DE MÉXICO» → «Ciudad de México»
  for _, e in ipairs(doc.meta["estados-portada"] or {}) do
    cifras.estados[#cifras.estados + 1] = stringify(e)
    local nombre = pandoc.text.lower(stringify(e)):gsub("(%S+)", function(p)
      if p == "de" or p == "del" or p == "la" or p == "y" then return p end
      return p:sub(1, 1):upper() .. p:sub(2)
    end)
    cifras.estados_nombres[#cifras.estados_nombres + 1] = nombre
  end
  cifras.titulo = doc.meta.title and stringify(doc.meta.title) or ""
  cifras.fechas = doc.meta.date and stringify(doc.meta.date) or ""
  escribir(DESTINO .. "/_data/foro.json", json(cifras) .. "\n")

  -- todos los logotipos, sin repetir y en orden de aparición (como la página
  -- final del Programa general)
  local logos, vistos_logo = {}, {}
  for _, e in ipairs(eventos) do
    for _, l in ipairs(e.logos) do
      if not vistos_logo[l.archivo] then
        vistos_logo[l.archivo] = true
        logos[#logos + 1] = l
      end
    end
  end
  escribir(DESTINO .. "/_data/logos.json", json(logos) .. "\n")

  -- secciones del programa (en orden), con el texto que las abre
  local secciones, vistas = {}, {}
  for _, e in ipairs(eventos) do
    local s = e.seccion
    if not vistas[s.id] then
      vistas[s.id] = true
      secciones[#secciones + 1] = { id = s.id, nombre = s.nombre,
        intro = textos.intros[s.id] and html_texto(textos.intros[s.id]) or "" }
    end
  end
  escribir(DESTINO .. "/_data/secciones.json", json(secciones) .. "\n")

  -- 5. Textos generales
  pandoc.system.make_directory(DESTINO .. "/_includes/generado", true)
  escribir(DESTINO .. "/_includes/generado/coloquio-presentacion.html", html_texto(textos.coloquio) .. "\n")
  escribir(DESTINO .. "/_includes/generado/coloquio-programa.html", html_texto(textos.coloquio_intro) .. "\n")
  escribir(DESTINO .. "/_includes/generado/creditos.html", html_texto(textos.creditos) .. "\n")
  escribir(DESTINO .. "/_includes/generado/directorio.html", html_texto(textos.contraportada) .. "\n")

  -- 6. Recursos (fotos y logotipos) para sitio/recursos.py
  pandoc.system.make_directory("build/sitio", true)
  local lineas = {}
  for k, nombre in pairs(RECURSOS) do lineas[#lineas + 1] = k .. "\t" .. nombre end
  table.sort(lineas)
  escribir("build/sitio/recursos.tsv", table.concat(lineas, "\n") .. "\n")

  io.stderr:write(string.format("Sitio: %d páginas de eventos, %d días, %d sedes\n",
    #eventos, #dias, #datos_sedes))
  return pandoc.Pandoc({}, doc.meta)
end
