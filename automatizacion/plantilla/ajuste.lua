-- Ajuste fino de páginas en dos pasadas (se carga desde fimnme.latex).
--
-- Cada concierto empieza en página nueva, así que pueden quedar finales
-- desafortunados: un programa que se desborda dos o tres líneas, o una
-- biografía cuyo final deja una página con un par de renglones. Para evitarlo
-- se registran en el .aux algunas posiciones (inicio del concierto, fin del
-- programa, inicio y fin de cada sección) y en la pasada siguiente se decide:
--
--   * programa desbordado (≤ 8 líneas): se compone ese programa con un
--     interlineado algo más compacto;
--   * final suelto (≤ 4 líneas en la última página de una sección de
--     semblanzas): esa sección se compone con interlineado algo más compacto;
--     si aun así queda suelto, con uno algo más holgado, de modo que la última
--     página tenga suficientes líneas.
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

-- Devuelve el modo del programa (0 normal, 1 compacto). «pre» marca el final
-- de las obras, antes del bloque de intérpretes que va al pie de la página.
local function modo_programa(n)
  local arriba, linea = medidas()
  local ini, fp, pre = fimnme.pos["ini:" .. n], fimnme.pos["finprog:" .. n], fimnme.pos["pre:" .. n]
  local prev = fimnme.previo["prog:" .. n] or 0
  if prev == 1 then return 1 end
  if ini and fp and fp.page == ini.page + 1 then
    if pre and pre.page == ini.page then return 1 end      -- solo pasaron los intérpretes
    local ref = pre or fp
    if ref.page == ini.page + 1 and arriba - ref.y <= 8 * linea then return 1 end
  end
  return 0
end

-- Devuelve el modo de una sección de semblanzas según cómo terminó en la
-- pasada anterior: 0 normal, 1 compacto (para que el final quepa en la página
-- anterior); si no basta, 2 y 3, cada vez más holgados (para que la última
-- página tenga más renglones). Los modos solo escalan, así que no oscilan.
local function modo_seccion(sid)
  local arriba, linea = medidas()
  local ini, fin = fimnme.pos["ini:" .. sid], fimnme.pos["fin:" .. sid]
  local prev = fimnme.previo["sec:" .. sid] or 0
  local suelto = ini and fin and fin.page > ini.page and arriba - fin.y <= 6 * linea
  if not suelto then return prev end
  return math.min(prev + 1, 3)
end

function fimnme.iniconcierto(n)
  local mp = modo_programa(n)
  escribe_aux("prog:" .. n, mp)
  tex.sprint(string.format("\\def\\modoprograma{%d}", mp))
end

function fimnme.iniseccion(sid)
  local mb = modo_seccion(sid)
  escribe_aux("sec:" .. sid, mb)
  tex.sprint(string.format("\\def\\modobiografias{%d}", mb))
end
