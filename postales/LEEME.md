# Postales de los conciertos · 48.º FIMNME

Una postal por concierto para redes (1080 × 1350 px, PNG) y en PDF. Siguen
la estructura de las postales del INBAL: fotos de los intérpretes, título,
intérpretes con su papel, obras, fecha, sede y dirección, logotipos y, al
pie, la pleca de la Secretaría de Cultura y del INBAL. El diseño es el del
Programa general (fondo verde con la partitura de *1 x 4*, logotipo del
Foro en dorado, Noto Sans).

De arriba abajo:

1. el encabezado (logotipo y nombre del Foro) sobre el verde, sin encimarse
   a las fotos;
2. las fotos;
3. el contenido, sin espacio entre las obras y la fecha y sede;
4. la franja negra con los logotipos y la pleca.

El contenido va pegado a la franja y las fotos ocupan el alto que queda
(`genera.py` lo mide en una primera pasada y recorta las fotos a esa medida).
Si el contenido de una postal es largo, sus fotos quedan más bajas; con menos
de 24 mm, `genera.py` avisa.

Criterios de las revisiones (`comentarios/postales 48 fimnme.pdf`):

- Sin cursivas, salvo los títulos de las obras.
- Ningún logotipo más grande que los de Cultura e INBAL: a lo más 4,5 mm de
  alto y 13 mm de ancho. La CNMO va en su versión horizontal
  (`automatizacion/plantilla/logo-cnmo-horizontal.tex`, de
  `comentarios/CNMO horizontal.ai`).
- Los nombres de compositores e intérpretes no se parten entre renglones.

```bash
python3 postales/genera.py                          # todas
python3 postales/genera.py mar-nov-10-alberto-rosado-piano   # solo esa
```

`./compila.sh` (compilación completa) también las regenera.

## Cómo se arma cada postal

- **Del Markdown** (a través de `sitio/_conciertos/<concierto>.html`, que
  genera `sitio/genera.sh`):
  - la fecha y la hora;
  - la sede y su dirección (sin «Ciudad de México»);
  - «Obras de…» y los estrenos;
  - los logotipos del concierto, que se ponen en blanco junto al de la CNMO.

  Si cambia algo de esto en el Markdown, basta regenerar.
- **De `postales.yaml`**:
  - lo editorial: antetítulo, título, subtítulo e intérpretes con su papel;
  - lo opcional: nota de colaboración, precio, otra dirección u otras obras;
  - las fotos y su encuadre.

  Para agregar una postal, se copia un bloque y se cambia la etiqueta del
  concierto (la misma del Programa general y del sitio).
- **Fotos**: las de `int/`.
  - `fotos`: una o varias, lado a lado, a todo lo ancho de la parte de arriba;
    cada una se recorta centrada en el rostro.
  - `retratos`: opcionales, en círculo, como en las fichas del programa (abajo a
    la derecha de las fotos).
  - `foco`: corrige el encuadre si hace falta.
- **Pleca de Cultura e INBAL** (`recursos/pleca-cultura-inbal80.png`): la de
  las postales del INBAL (con el logotipo de los 80 años), con la misma
  posición y el mismo tamaño. Es una imagen tomada de esas postales; si se
  consigue en vectorial, conviene reemplazarla.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `postales.yaml` | Lista de postales y sus datos editoriales. |
| `genera.py` | Prepara fotos, logotipos y datos, y compila cada postal. |
| `postal.tex` | Diseño (LuaLaTeX/TikZ), común a todas. |
| `recursos/` | Pleca de Cultura e INBAL. |
| `fimnme2026-postal-<concierto>.png`, `.pdf` | Las postales (generadas). |

Requisitos: LuaLaTeX, Python 3 con PyYAML y Pillow (OpenCV es opcional:
centra las fotos en los rostros) y `pdftoppm`. Los archivos intermedios van
en `build/postales/`.
