# Programa General · 48.º FIMNME

El PDF `fimnme2026-programa.pdf` se genera a partir de `fimnme2026-programa.md`
(contenido) y `fimnme2026-programa.yaml` (metadatos).

```bash
./compila.sh            # compilación completa (3–5 pasadas, ~2 min)
./compila.sh --rapido   # una sola pasada, para revisar cambios
resumen/compila.sh      # solo el programa resumido (la compilación completa también lo genera)
```

Requisitos: pandoc ≥ 3.1, TeX Live ≥ 2023 con LuaLaTeX (koma-script, tcolorbox,
tikz, microtype…), makeindex y Python 3 con Pillow. Con `opencv-python-headless`
las fotos se recortan centradas en el rostro (si no está, el recorte es centrado).
Las fuentes Noto Sans van incluidas en `automatizacion/fuentes/`.

## Cómo está organizado

| Archivo | Para qué sirve |
|---|---|
| `fimnme2026-programa.md`, `fimnme2026-programa.yaml` | Contenido y metadatos del programa. |
| `comp/`, `int/` | Fotos originales de compositores e intérpretes (las que usa el Markdown). |
| `48 FIMNME programas/` | Programas de mano individuales (docx), referencia para cotejar. |
| `revision/` | Listas de correcciones para revisar (p. ej. el cotejo con los programas de mano). |
| `resumen/` | Programa resumido (agenda en una página y programas condensados; ver `resumen/LEEME.md`). |
| `automatizacion/plantilla/fimnme.latex` | Diseño: página, tipografía, colores, portada, divisorias, encabezados, fichas, índices. |
| `automatizacion/fimnme.lua` | Convierte la estructura del Markdown en las macros del diseño. |
| `automatizacion/preparar_imagenes.py` | Recorta y ajusta las fotos de `comp/` e `int/` (en `build/fotos/`). |
| `automatizacion/plantilla/ajuste.lua` | Ajuste fino de páginas (evita programas desbordados y finales de sección con pocas líneas). |
| `automatizacion/indice-onomastico.yaml` | Excepciones de apellidos para el índice onomástico. |
| `automatizacion/plantilla/logo-*.tex`, `partitura-1x4.pdf` | Logotipos y partitura de la portada, en vectorial. |

## Convenciones del Markdown

- `\part{TÍTULO}` abre una parte (página verde). Si le sigue un párrafo, se usa
  como subtítulo de la parte.
- `## VIE | NOV 6, 20:00 h - Título` abre un concierto (siempre en página nueva).
  Dos fechas: `## VIE | NOV 13, 19:00 h / DOM | NOV 15, 12:00 h - Título`.
  El primer párrafo después del encabezado es la sede.
- En «Conciertos en Ciudad de México» la página divisoria de cada día se genera
  sola; no hace falta escribirla. El orden de los conciertos es el del archivo.
- `### Programa`, `### Personas compositoras`, `### Intérpretes`,
  `### Dirección y solistas`: secciones del concierto.
- En el programa: `**Compositor**` seguido de la lista de obras
  `- *Obra* (2025)\* \hfill 9'`. Lo que va después de la duración (p. ej.
  «Video de…») sale como crédito en línea aparte. Las viñetas sin duración ni
  año se componen como movimientos.
- Después de un grupo de obras, los párrafos que no van en negrita inicial
  ni en cursivas son sus intérpretes: se componen en un bloque con filete
  verde. Si el programa tiene varios grupos de obras con distintos
  intérpretes, cada grupo va separado del siguiente y no se parte entre
  páginas; un `---` entre grupos también los separa. Si todo el programa lo
  tocan los mismos intérpretes, su bloque va al pie de la página; también
  el de un grupo que queda solo en su página.
- Solista de una obra concreta (dentro de un grupo que tocan otros):
  `[**Nombre**, instrumento]{.solista}` justo después de la obra; sale como
  crédito bajo la obra.
- Un párrafo entero en cursivas dentro del programa (`*Duración: 50 minutos*`,
  patrocinios…) es una nota breve, en gris.
- La leyenda «\* Estreno mundial / \*\* Estreno en México» se genera sola con
  las marcas que aparezcan en cada programa y va debajo de la última obra
  (o al final del programa, si tiene varios grupos), alineada al margen; no
  hay que escribirla.
- `#### Nombre (País, año)` seguido de `![](comp/Foto.jpg)` crea la ficha con
  foto circular (también para conjuntos: si los rostros no caben, la foto se
  muestra completa sobre un fondo difuminado). Las semblanzas se componen un
  punto menos que las notas. Foto y semblanza van solo la primera vez: en las
  siguientes sale el nombre con «Ver pág. N» (enlace a la primera semblanza).
  A los compositores les basta el nombre; a los intérpretes, el nombre y la
  misma semblanza (si el texto es otro, p. ej. una semblanza como director,
  se compone completa).
- `##### *Obra*`: título de nota al programa. El texto de la nota va en un
  recuadro con fondo verde claro, al tamaño normal; si la nota incluye una
  cita (`> «…»`) junto con otros párrafos, la cita va sangrada dentro del
  recuadro. Si la misma nota de la misma obra ya apareció, sale su título con
  «Ver pág. N».
- Cada sección de un concierto (Programa, Personas compositoras,
  Intérpretes…) empieza en página nueva. Una sección que solo tenga
  referencias «Ver pág.» sigue en la página (salvo justo después del
  programa), y la sección siguiente puede seguir tras ella.
- Para remitir a la página de otro concierto: `` `\pageref{conc:mie-nov-18-electroacustica-i}`{=latex} ``.
  La etiqueta se forma sola con la fecha y el título del encabezado, en
  minúsculas, sin acentos y con guiones.
- No hace falta poner `\clearpage` ni `\vfill`: la paginación la decide la
  plantilla (se ignoran si aparecen).
- El índice general y el índice onomástico se generan automáticamente.
