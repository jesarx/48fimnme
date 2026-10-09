-- Disposición de las fotos de una postal (la usa postal.tex con \directlua).
--
-- Las fotos van en una franja: todas del mismo alto y cada una con un ancho
-- según su proporción (las de grupo, apaisadas, más anchas que los retratos),
-- hasta llenar el ancho. Cada foto se recorta para cubrir su marco, centrada
-- en su punto de interés (los rostros), sin dejar huecos.

local M = {}

local SEPARACION = 2.0        -- mm entre fotos

local function mm(sp) return sp / 65536 / 72.27 * 25.4 end

-- fotos: { {archivo=, a=ancho/alto de la imagen, p=ancho/alto de su marco,
-- fx=, fy=}, ... } (p lo calcula genera.py); x0, y0: esquina de la
-- franja (mm desde arriba a la izquierda); ancho, alto: de la franja (mm)
function M.disponer(fotos, x0, y0, ancho, alto)
  local n = #fotos
  if n == 0 then return {} end
  local suma = 0
  local props = {}
  for k, f in ipairs(fotos) do
    local p = f.p
    if n == 1 then p = ancho / alto end
    props[k] = p
    suma = suma + p
  end
  local util = ancho - SEPARACION * (n - 1)
  local marcos, x = {}, x0
  for k, f in ipairs(fotos) do
    local w = util * props[k] / suma
    -- la imagen cubre el marco
    local iw, ih
    if f.a >= w / alto then ih = alto; iw = alto * f.a else iw = w; ih = w / f.a end
    local ix = x + w / 2 - f.fx * iw
    ix = math.min(x, math.max(x + w - iw, ix))
    local iy = y0 + alto / 2 - f.fy * ih
    iy = math.min(y0, math.max(y0 + alto - ih, iy))
    marcos[k] = {archivo = f.archivo, x = x, y = y0, w = w, h = alto, ix = ix, iy = iy, iw = iw, ih = ih}
    x = x + w + SEPARACION
  end
  return marcos
end

-- TikZ de las fotos (coordenadas desde la esquina de arriba a la izquierda)
function M.tikz(marcos, radio)
  local salida = {}
  for _, m in ipairs(marcos) do
    salida[#salida + 1] = string.format(
      "\\begin{scope}\\clip[rounded corners=%.2fmm] ($(current page.north west)+(%.3fmm,%.3fmm)$) rectangle ++(%.3fmm,%.3fmm);"
      .. "\\node[anchor=north west, inner sep=0pt] at ($(current page.north west)+(%.3fmm,%.3fmm)$)"
      .. "{\\includegraphics[width=%.3fmm, height=%.3fmm]{%s}};\\end{scope}",
      radio, m.x, -m.y, m.w, -m.h, m.ix, -m.iy, m.iw, m.ih, m.archivo)
  end
  tex.sprint(table.concat(salida, "\n"))
end

-- Marcos e imágenes en puntos PostScript, para el IDML (postal/idml_editable.py)
function M.pistas(marcos, ruta, radio)
  local bp = 72 / 25.4
  local f = io.open(ruta, "w")
  f:write("[")
  for k, m in ipairs(marcos) do
    f:write(string.format('%s{"marco": [%.3f, %.3f, %.3f, %.3f], "imagen": [%.3f, %.3f, %.3f, %.3f], "radio": %.3f}',
      k > 1 and ", " or "", m.x * bp, m.y * bp, (m.x + m.w) * bp, (m.y + m.h) * bp,
      m.ix * bp, m.iy * bp, (m.ix + m.iw) * bp, (m.iy + m.ih) * bp, radio * bp))
  end
  f:write("]\n")
  f:close()
end

M.mm = mm
return M
