-- Disposición de las fotos de una postal (la usa postal.tex con \directlua).
--
-- Las fotos van en una franja: todas del mismo alto y cada una con un ancho
-- según su proporción (las de grupo, apaisadas, más anchas que los retratos),
-- hasta llenar el ancho. Cada foto se encuadra en su marco sin dejar huecos:
-- si se conocen sus rostros (genera.py), la ventana los contiene enteros, con
-- el pelo y aire arriba y, si cabe, hombros y algo del torso, y se acerca un
-- poco para que no se vean chicos (si la franja es muy baja, se corta primero
-- el pelo y no los ojos ni la boca); si no, la foto cubre el marco centrada en
-- su punto de interés.

local M = {}

local SEPARACION = 2.0        -- mm entre fotos
local HOLGURA = 1.08          -- margen alrededor de lo que no debe cortarse
local ACERCAMIENTO = 0.35     -- 0: lo más cerca posible; 1: la foto entera

local function mm(sp) return sp / 65536 / 72.27 * 25.4 end

local function entre(v, a, b) return math.max(a, math.min(b, v)) end

-- Ventana de la foto que se muestra en un marco de proporción r (ancho/alto),
-- en unidades del alto de la imagen (la imagen mide a × 1): x, y, ancho, alto
local function ventana(f, r)
  local a = f.a
  -- la mayor ventana posible (la foto cubre el marco)
  local cw, ch
  if r >= a then cw, ch = a, a / r else cw, ch = r, 1 end
  if not f.nucleo then
    return entre(f.fx * a - cw / 2, 0, a - cw), entre(f.fy - ch / 2, 0, 1 - ch), cw, ch
  end
  local x0, y0, x1, y1 = f.nucleo[1] * a, f.nucleo[2], f.nucleo[3] * a, f.nucleo[4]
  local abajo = math.max(f.abajo or y1, y1)
  -- la menor ventana que muestra los rostros con hombros; entre ella y la mayor
  local minimo = math.max(x1 - x0, (abajo - y0) * r) * HOLGURA
  local ww = cw
  if minimo < cw then ww = minimo + ACERCAMIENTO * (cw - minimo) end
  local wh = ww / r
  local r0, r1 = (f.rostros or f.nucleo)[2], (f.rostros or f.nucleo)[4]
  local wy
  if wh >= abajo - y0 then          -- caben los rostros y los hombros
    wy = y0 - 0.25 * (wh - (abajo - y0))
  elseif wh >= y1 - y0 then         -- caben los rostros con el pelo
    wy = y0 - 0.25 * (wh - (y1 - y0))
  elseif wh >= r1 - r0 then         -- caben los rostros: se corta el pelo
    wy = r1 - wh
  else                              -- no caben: centrados en los rostros
    wy = (r0 + r1) / 2 - wh / 2
  end
  return entre((x0 + x1) / 2 - ww / 2, 0, a - ww), entre(wy, 0, 1 - wh), ww, wh
end

-- fotos: { {archivo=, a=ancho/alto de la imagen, p=ancho/alto de su marco,
-- fx=, fy= (punto de interés), nucleo={x0,y0,x1,y1}, rostros={…}, abajo=
-- (zonas de los rostros, en fracciones de la imagen; pueden faltar)}, ... }
-- (lo calcula genera.py);
-- x0, y0: esquina de la franja (mm desde arriba a la izquierda); ancho, alto:
-- de la franja (mm)
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
    local wx, wy, ww = ventana(f, w / alto)
    local escala = w / ww          -- mm por unidad de la imagen
    marcos[k] = {archivo = f.archivo, x = x, y = y0, w = w, h = alto,
                 ix = x - wx * escala, iy = y0 - wy * escala, iw = f.a * escala, ih = escala}
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
