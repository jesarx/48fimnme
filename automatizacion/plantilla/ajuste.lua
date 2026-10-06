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
--   * final suelto (unas 6 líneas o menos en la última página de una sección
--     de semblanzas, o la franja de logotipos sola en su página): esa sección
--     se compone con interlineado algo más compacto; si aun así queda suelto,
--     con uno algo más holgado, de modo que la última página tenga suficientes
--     líneas;
--   * programa que ni compactado cabe en una página (modo 3): si tiene
--     intermedio, la segunda parte empieza en la página siguiente.
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

-- Devuelve el modo del programa (0 normal, 1 compacto, 2 más compacto,
-- 3 normal porque ni el más compacto cabe).
-- «pre» marca el final de las obras, antes del bloque de intérpretes que va al
-- pie de la página. Los modos solo escalan, así que no oscilan.
local function modo_programa(n)
  local arriba, linea = medidas()
  local ini, fp, pre = fimnme.pos["ini:" .. n], fimnme.pos["finprog:" .. n], fimnme.pos["pre:" .. n]
  local prev = fimnme.previo["prog:" .. n] or 0
  local desbordado = false
  if ini and fp and fp.page == ini.page + 1 then
    if pre and pre.page == ini.page then
      desbordado = true                                   -- solo pasaron los intérpretes
    else
      local ref = pre or fp
      desbordado = ref.page == ini.page + 1 and arriba - ref.y <= 8 * linea
    end
  end
  if desbordado then
    -- si ni el modo más compacto basta, compactar no sirve: modo 3, que se
    -- compone como el normal (y ya no cambia)
    if prev >= 2 then return 3 end
    return prev + 1
  end
  return prev
end

-- Devuelve el modo de una sección de semblanzas según cómo terminó en la
-- pasada anterior: 0 normal; 1 y 2, cada vez más compactos (para que el final
-- quepa en la página anterior); si no basta, 3 y 4, cada vez más holgados
-- (para que la última página tenga más renglones). Los modos solo escalan.
local function modo_seccion(sid)
  local arriba, linea = medidas()
  local ini, fin = fimnme.pos["ini:" .. sid], fimnme.pos["fin:" .. sid]
  local prev = fimnme.previo["sec:" .. sid] or 0
  local suelto = ini and fin and fin.page > ini.page and arriba - fin.y <= 8 * linea
  -- Con franja de logotipos: también es suelto que la franja quede sola en
  -- una página.
  local logos = fimnme.pos["logos:" .. sid]
  if logos and fin and logos.page > fin.page then suelto = true end
  if not suelto then return prev end
  return math.min(prev + 1, 4)
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

-- Grupo de obras de un programa con varios grupos de intérpretes: si quedó
-- solo en su página (el grupo anterior terminó en otra página y el siguiente
-- empieza en otra), sus intérpretes van al pie. No altera la paginación.
function fimnme.grupofondo(n, g, ultimo)
  local k = n .. "-" .. g
  local fin = fimnme.pos["gf:" .. k]
  local modo = 0
  if fin then
    local ant = fimnme.pos["gf:" .. n .. "-" .. (g - 1)]
    local sig = fimnme.pos["gi:" .. n .. "-" .. (g + 1)]
    local arriba = g == 1 or (ant ~= nil and ant.page < fin.page)
    local abajo = ultimo == 1 or (sig ~= nil and sig.page > fin.page)
    if arriba and abajo then modo = 1 end
  end
  escribe_aux("grp:" .. k, modo)
  tex.sprint(string.format("\\def\\fondogrupo{%d}", modo))
end

-- Franja de logotipos de un concierto. Va al final de su última sección; si
-- ahí queda sola en una página aun con el ajuste más amplio de la sección
-- (modo 4), en las pasadas siguientes va al pie de la página del programa.
-- La decisión no se revierte.
function fimnme.logosfin(sid)
  local n = sid:match("^(%d+)%-")
  local antes = fimnme.previo["lp:" .. n] or 0
  local decision = antes
  if antes == 0 then
    local lg, fin = fimnme.pos["logos:" .. sid], fimnme.pos["fin:" .. sid]
    if lg and fin and lg.page > fin.page and (fimnme.previo["sec:" .. sid] or 0) >= 4 then
      decision = 1
    end
  end
  escribe_aux("lp:" .. n, decision)
  tex.sprint(string.format("\\def\\logosaqui{%d}", antes == 1 and 0 or 1))
end

function fimnme.logosprograma(n)
  tex.sprint(string.format("\\def\\logosaqui{%d}", fimnme.previo["lp:" .. n] or 0))
end
