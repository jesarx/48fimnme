# Postales de los eventos · 48.º FIMNME

Una postal por concierto para redes: todos los de la Ciudad de México y, de los
estados, la de Xalapa. Un concierto con dos funciones lleva una postal por
función (el Coro de Madrigalistas: Jardín Escénico y Palacio de Bellas Artes).
Cada postal sale en tres formatos:

- PNG de 1080 × 1350 px;
- PDF;
- SVG editable en Inkscape o Illustrator, con los textos como texto en Noto
  Sans y el fondo, las fotos y los logotipos en otra capa.

Siguen las postales del diseñador, que ya cumplen los lineamientos del INBAL.
Los tamaños y posiciones de los logotipos están aprobados.

```bash
python3 postales/genera.py                                  # todas
python3 postales/genera.py sab-nov-7-gonzalo-gutierrez-piano  # solo esa
```

`./compila.sh` (la compilación completa) también las regenera.

## Cómo es cada postal

De arriba abajo:

1. Logotipo y nombre del Foro, en el color del logotipo (#E6AE78).
2. Antetítulo («Concierto», «Instalación sonora»…), fecha y hora.
3. Intérpretes, uno por renglón, con su papel en letra ligera si se indica.
   Si un nombre no cabe en un renglón, lo que pasa al siguiente va con
   sangría, para que no parezca otro intérprete. El papel no se parte: va
   junto al nombre o, si no cabe, completo en el renglón siguiente.
4. Recuadro de obras y, si se indica, una nota en cursivas (el nombre del
   programa, una colaboración), como en la postal del abono del diseñador.
5. Sede, dirección y «Entrada libre | Cupo limitado».
6. Al pie, sobre el degradado oscuro: los logotipos y la pleca de Cultura e
   INBAL.

Las fotos van en círculo a la derecha, una debajo de otra (hasta cuatro).
El fondo es verde, con la partitura de *1 x 4* de Enríquez.

Medidas y colores se calibraron sobre la postal del maratón de guitarras del
diseñador: los textos y el recuadro coinciden con ella a un par de píxeles. El
contenido arranca a los 27,6 mm. Si es más corto que el de esa postal, se
centra en el espacio disponible. Si es más largo (muchos intérpretes u obras),
sube hasta los 24 mm y, si aun así no cabe, se compone un poco más chico. Las
fotos nunca bajan hasta los logotipos.

## De dónde sale cada dato

- **Del Markdown** (a través de `sitio/_conciertos/<evento>.html`, que genera
  `sitio/genera.sh`):
  - la fecha y la hora;
  - la sede (primero el recinto, luego la sala) y su dirección (sin «Ciudad
    de México»);
  - «Obras de…»;
  - los logotipos del evento, que van en blanco junto al de la CNMO.

  Si cambia algo de esto en el Markdown, basta regenerar.
- **De `postales.yaml`**:
  - el antetítulo y los intérpretes;
  - las fotos;
  - lo opcional: la función (en un concierto con varias), otras obras (p. ej.
    el título de una instalación), una nota, la entrada o el precio, otra
    sede o dirección.

  Para agregar una postal, se copia un bloque y se cambia la etiqueta del
  evento (la misma del Programa general y del sitio).

## Criterios

- **Logotipos**: la CNMO en su versión horizontal, de 15,2 mm de ancho
  (`automatizacion/plantilla/logo-cnmo-horizontal.tex`, de
  `comentarios/CNMO horizontal.ai`). Los demás, en blanco y de área parecida
  (como el del Centro Cultural del Bosque en la postal del diseñador): a lo
  más 4,2 mm de alto y 14 mm de ancho. En el Palacio de Bellas Artes solo va
  la CNMO, como en las postales del INBAL.
- **Pleca de Cultura e INBAL** (`recursos/pleca-cultura-inbal80.png`): la de
  los 80 años, con fondo transparente, en la posición y el tamaño de esas
  postales.
- **«Obras de…»**: con los nombres completos. Si la lista pasa de 150
  caracteres, los nombres de pila van en inicial («J. Torres Sáenz»), como hizo
  el diseñador. Para separar apellidos usa `automatizacion/indice-onomastico.yaml`.
- **Entrada**: «Entrada libre | Cupo limitado», salvo que se indique otra cosa.
  La inauguración y la clausura llevan el precio del abono de ambos conciertos
  (el de la postal del abono).
- **Cursivas**: solo en los títulos de las obras. Los nombres de personas y
  lugares no se parten entre renglones.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `postales.yaml` | Lista de postales y sus datos editoriales. |
| `genera.py` | Prepara fotos, logotipos y datos; compila cada postal y la exporta a PNG y SVG. |
| `postal.tex` | Diseño (LuaLaTeX/TikZ), común a todas. |
| `recursos/` | Pleca de Cultura e INBAL. |
| `fimnme2026-postal-<evento>.png`, `.pdf`, `.svg` | Las postales (generadas). La de cada función de un concierto que se repite empieza con su fecha. |
| `anteriores/` | Las primeras postales de prueba, con el diseño anterior (solo como referencia). |

El SVG lo arma `postal/svg_editable.py`, el mismo que hace el de la postal del
abono. No se genera un `.ai`: es un formato cerrado de Adobe. Illustrator
abre el SVG, con los textos editables, y también el PDF.

Requisitos: LuaLaTeX, Python 3 con PyYAML, Pillow y PyMuPDF (OpenCV es
opcional: centra las fotos en los rostros) y `pdftoppm`. Los archivos
intermedios van en `build/postales/`.
