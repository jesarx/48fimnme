# Programa General · 48.º FIMNME

El PDF `fimnme2026-programa.pdf` se genera a partir de `fimnme2026-programa.md`
(contenido) y `fimnme2026-programa.yaml` (metadatos).

```bash
./compila.sh            # compilación completa (3–5 pasadas, ~2 min)
./compila.sh --rapido   # una sola pasada, para revisar cambios
```

Requisitos: pandoc ≥ 3.1, TeX Live ≥ 2023 con LuaLaTeX (koma-script, tcolorbox,
tikz, microtype…), makeindex y Python 3 con Pillow. Con `opencv-python-headless`
las fotos se recortan centradas en el rostro (si no está, el recorte es centrado).
Las fuentes Noto Sans van incluidas en `automatizacion/fuentes/`.

## Cómo está organizado

| Archivo | Para qué sirve |
|---|---|
| `automatizacion/plantilla/fimnme.latex` | Diseño: página, tipografía, colores, portada, divisorias, encabezados, fichas, índices. |
| `automatizacion/fimnme.lua` | Convierte la estructura del Markdown en las macros del diseño. |
| `automatizacion/preparar_imagenes.py` | Recorta y ajusta las fotos de `comp/` e `int/` (en `build/fotos/`). |
| `automatizacion/plantilla/ajuste.lua` | Ajuste fino de páginas (evita programas desbordados y finales sueltos). |
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
- La leyenda «\* Estreno mundial / \*\* Estreno en México» se genera sola con
  las marcas que aparezcan en cada programa; no hay que escribirla.
- `#### Nombre (País, año)` seguido de `![](comp/Foto.jpg)` crea la ficha con
  foto. Las fotos de grupos se muestran apaisadas.
- `##### *Obra*`: título de nota al programa.
- No hace falta poner `\clearpage` ni `\vfill`: la paginación la decide la
  plantilla (se ignoran si aparecen).
- El índice general y el índice onomástico se generan automáticamente.
