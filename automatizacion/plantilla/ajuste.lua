-- Ajuste fino de páginas en dos pasadas (se carga desde fimnme.latex).
--
-- Cada concierto empieza en página nueva, así que pueden quedar finales
-- desafortunados: un programa que se desborda dos o tres líneas, o una
-- biografía cuyo final deja una página con un par de renglones. Para evitarlo
-- se registran en el .aux algunas posiciones (inicio del concierto, fin del
-- programa, fin del concierto) y en la pasada siguiente se decide:
--
--   * programa desbordado (≤ 8 líneas): se compone ese programa con un
--     interlineado algo más compacto;
--   * final suelto (≤ 4 líneas en la última página): las biografías y notas
--     del concierto se componen con interlineado algo más compacto; si aun
--     así queda suelto, con uno algo más holgado, de modo que la última página
--     tenga suficientes líneas.
--
-- Las decisiones se guardan en el .aux y son estables (no oscilan); los
-- márgenes no se tocan.

fimnme = { pos = {}, previo = {} }

function fimnme.guardapos(k, p, y) fimnme.pos[k] = { page = p, y = y } end
function fimnme.guardaajuste(k, modo) fimnme.previo[k] = modo end

local function medidas()
  -- borde superior de la caja de texto (medido desde abajo) y altura de línea
  return tex.dimen.paperheight - tex.sp("14mm"), tex.baselineskip.width
end

local function escribe_aux(clave, modo)
  tex.sprint(string.format("\\immediate\\write\\fimnmeaux{\\string\\fimnmeajuste{%s}{%d}}",
    clave, modo))
end

-- Devuelve el modo del programa (0 normal, 1 compacto)
local function modo_programa(n)
  local arriba, linea = medidas()
  local ini, fp = fimnme.pos["ini:" .. n], fimnme.pos["finprog:" .. n]
  local prev = fimnme.previo["prog:" .. n] or 0
  if prev == 1 then return 1 end
  if ini and fp and fp.page == ini.page + 1 and arriba - fp.y <= 8 * linea then
    return 1
  end
  return 0
end

-- Devuelve el modo de las biografías (0 normal, 1 compacto, 2 holgado)
local function modo_biografias(n)
  local arriba, linea = medidas()
  local ini, fin = fimnme.pos["ini:" .. n], fimnme.pos["fin:" .. n]
  local prev = fimnme.previo["fin:" .. n] or 0
  local suelto = ini and fin and fin.page > ini.page and arriba - fin.y <= 4.5 * linea
  if prev == 2 then return 2 end
  if prev == 1 then return suelto and 2 or 1 end
  return suelto and 1 or 0
end

function fimnme.iniconcierto(n)
  local mp, mb = modo_programa(n), modo_biografias(n)
  escribe_aux("prog:" .. n, mp)
  escribe_aux("fin:" .. n, mb)
  tex.sprint(string.format("\\def\\modoprograma{%d}\\def\\modobiografias{%d}", mp, mb))
end
