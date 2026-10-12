# Postales de los eventos · 48º FIMNME

Una postal por evento para redes: todos los conciertos (Ciudad de México,
estados y Ecos del Foro), las actividades académicas y las sesiones del
Coloquio Manuel Enríquez 100. Las de los conciertos van en el verde de las
postales del diseñador; las de las actividades académicas y el Coloquio, en
verde azulado (#53797C). Las del Coloquio son solo de texto, sin fotos (como
las de Electroacústica). Un concierto con dos funciones lleva una postal por
función (el Coro de Madrigalistas: Jardín Escénico y Palacio de Bellas Artes).
Cada postal sale en cuatro formatos, cada uno en su carpeta:

- `png/`: PNG de 1080 × 1350 px, para redes;
- `jpg/`: JPG de 1080 × 1350 px (calidad 90): se ve igual y pesa menos de la
  mitad; es el que usa el sitio web;
- `pdf/`: PDF;
- `idml/`: IDML para InDesign (ver «El IDML», abajo).

En las mismas carpetas está la postal del abono (`fimnme2026-postal-abono`), que
se genera aparte (`abono/`, abajo). El sitio web muestra la postal de cada
evento en su página y todas juntas en la de descargas.

Siguen las postales del diseñador, que ya cumplen los lineamientos del INBAL.
Los tamaños y posiciones de los logotipos están aprobados.

```bash
python3 postales/genera.py                                  # todas
python3 postales/genera.py sab-nov-7-gonzalo-gutierrez-piano  # solo esa
postales/abono/compila.sh                                   # la del abono
```

`./compila.sh` (la compilación completa) también las regenera.

## Cómo es cada postal

Parte de las postales del diseñador, pero prioriza la legibilidad. Lo que
sigue las reglas de los logotipos no cambia: el logotipo y el nombre del Foro
arriba a la izquierda y, al pie, sobre el degradado oscuro, la fila de
logotipos y la pleca de Cultura e INBAL, con sus tamaños y posiciones.

De arriba abajo:

1. Logotipo y nombre del Foro, en el color del logotipo (#E6AE78).
2. La franja de fotos (hasta cuatro), con esquinas redondeadas: todas del
   mismo alto; los grupos en marcos apaisados y los retratos en marcos
   angostos. Cada foto se encuadra con sus rostros enteros (todos, en una foto
   de grupo), con aire arriba y, si cabe, los hombros, y un poco de cerca
   para que no se vean chicos.
3. Antetítulo («Concierto», «Instalación sonora», «Ecos del Foro»,
   «Conferencia», «Coloquio Manuel Enríquez 100»…), en dorado claro; el
   título del concierto, si lo tiene (y su segunda parte, más chica); la
   fecha y la hora.
4. Intérpretes (o ponentes, participantes y moderadores), uno por renglón,
   con su papel. Si un nombre no cabe en un
   renglón, lo que pasa al siguiente va con sangría, para que no parezca otro
   intérprete. El papel no se parte: va junto al nombre o, si no cabe,
   completo en el renglón siguiente.
5. «OBRAS DE» y los compositores, sin recuadro; si se indica, una nota (una
   colaboración, a quién va dirigida una actividad). Si todos los compositores
   son intérpretes (una instalación de su autor), no va.
6. Sede, dirección y «Entrada libre | Cupo limitado».

No hay cursivas. El fondo (verde o verde azulado) lleva la partitura de *1 x 4* de
Enríquez; detrás del contenido se oscurece un poco para que los textos se lean
bien (todos pasan de 4:1 de contraste, en los dos colores).

El contenido va de los 21 a los 108 mm. La franja de fotos toma el alto que
les conviene a sus fotos (`genera.py` lo calcula con los rostros): el
preferido, que muestra los rostros con los hombros (hasta 50 mm), sin bajar
del necesario para no cortar ningún rostro ni pasar del máximo que no los
corta por los lados. Si el texto no cabe, primero la franja baja hasta el
alto necesario, luego el texto se compone un poco más chico (hasta el 82 %),
la franja baja hasta 17 mm (aquí ya puede cortarse algún rostro) y solo
entonces el texto se achica más. Si sobra lugar, la franja
crece (hasta 46 mm) y el conjunto se centra. La disposición y el encuadre de
las fotos están en `postal.lua`.

Para afinar una foto, en `postales.yaml` se le puede dar un **recorte** (la
parte que se usa: así una foto que son dos retratos juntos, como la del Dúo
Gasparini-Monnet, o una del escenario con los músicos lejos, como la del
Ensamble Sonus, va en dos marcos, uno por persona), un **peso** (su marco,
más ancho que los otros: el Trío LaMN y el Trío Siqueiros, que comparten
concierto, van más grandes) o **extender** su fondo (en una foto de estudio con
fondo liso: el del Cuarteto de Bellas Artes se extiende a la izquierda para
que los cuatro quepan completos, con los hombros, en la franja). A una postal
se le puede pedir un alto mínimo de **franja** (en mm) cuando el que se calcula
con los rostros no basta: el Ensamble Sonus pide 32 mm para que los retratos
lleven los hombros.

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
  - el antetítulo, el título y los intérpretes;
  - las fotos, con su recorte, su peso o su fondo extendido si los tienen
    (y, en «focos», el punto de interés de las fotos en las que no se detecta
    bien el rostro), y el alto mínimo de la franja si se pide;
  - lo opcional: la función (en un concierto con varias), otras obras, una
    nota, la entrada o el precio, otra sede o dirección, y los logotipos del evento que no van en esa postal
    (la función del Coro de Madrigalistas en el Palacio de Bellas Artes no
    lleva los del Jardín Escénico).

  Para agregar una postal, se copia un bloque y se cambia la etiqueta del
  evento (la misma del Programa general y del sitio).

## Criterios

- **Logotipos**: la CNMO en su versión horizontal, de 15,2 mm de ancho
  (`automatizacion/plantilla/logo-cnmo-horizontal.tex`, de
  `comentarios/CNMO horizontal.ai`). Los demás, en blanco y de área parecida
  (como el del Centro Cultural del Bosque en la postal del diseñador): a lo
  más 4,2 mm de alto y 14 mm de ancho. En el Jardín Escénico van los del
  Centro Cultural del Bosque y del Jardín Escénico (`logos/*.ai`), como en
  la postal del diseñador. En el Palacio de Bellas Artes solo va la CNMO,
  como en las postales del INBAL. Si una fila de logotipos pasa de 90 mm (siete
  en Guadalajara), se reduce la separación entre ellos, no su tamaño. Si un
  logotipo trae un recuadro de fondo (el de la Fundación Harp Helú), en la
  versión en blanco se quita el recuadro.
- **Pleca de Cultura e INBAL** (`recursos/pleca-cultura-inbal80.png`): la de
  los 80 años, con fondo transparente, en la posición y el tamaño de esas
  postales.
- **«Obras de…»** y **dirección**: como en el Markdown, con los nombres
  completos (sin pasar los nombres de pila a iniciales). Si la lista es larga,
  el contenido se compone un poco más chico (ver arriba).
- **Entrada**: «Entrada libre | Cupo limitado», salvo que se indique otra cosa.
  La inauguración y la clausura llevan el precio del abono de ambos conciertos
  (el de la postal del abono).
- **Cursivas**: ninguna. Los nombres de personas y lugares no se parten entre
  renglones, y «de», «la», «y»… no quedan al final de un renglón.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `postales.yaml` | Lista de postales y sus datos editoriales. |
| `genera.py` | Prepara fotos (con sus rostros), logotipos y datos; compila cada postal y la exporta a PNG, JPG e IDML. |
| `postal.tex` | Diseño (LuaLaTeX/TikZ), común a todas. |
| `postal.lua` | Disposición y recorte de las fotos en la franja (y sus marcos para el IDML). |
| `idml_editable.py` | Arma el IDML de cada postal (y el del abono) a partir de su PDF. |
| `recursos/` | Pleca de Cultura e INBAL. |
| `png/`, `jpg/`, `pdf/`, `idml/` | Las postales (generadas): `fimnme2026-postal-<evento>.png`, `.jpg`, `.pdf` e `.idml`. La de cada función de un concierto que se repite empieza con su fecha. |
| `abono/` | La postal del abono (inauguración y clausura): `abono.tex` (diseño y textos), `compila.sh` y `logos_blancos.py`. |

## El IDML

Lo arma `postales/idml_editable.py` (el mismo que hace el de la postal del
abono) a partir del PDF de cada postal y del fondo, que se compila aparte
(la plantilla con `\solofondo`, en `build/postales/fondo-verde.pdf` y
`fondo-azul.pdf`, el verde azulado). Es un
documento de InDesign de una página, del tamaño de la postal, con todo
incrustado (no depende de otros archivos). De atrás hacia adelante:

- **Fondo**: verde, partitura, velo y degradado, como imagen (300 ppp),
  bloqueado.
- **Logotipos y pleca**: cada uno como imagen aparte. Los vectoriales (el del
  Foro y el de la CNMO) van a 1200 ppp.
- **Fotos**: cada una en su marco de esquinas redondeadas, con la imagen
  recortada como en el PDF; se cambian fácilmente (Archivo › Colocar sobre
  el marco).
- **Textos**, editables en Noto Sans: un marco por bloque (antetítulo,
  título, fecha, intérpretes, obras, sede, dirección, entrada), con los
  mismos cortes de renglón, tamaños, colores, interlineado y espaciado entre
  letras que el PDF. Cada bloque tiene su estilo de párrafo y los colores
  están en las muestras con sus nombres (`acento`, `casiblanco`, `suave`…).

Para editarlo hay que tener instalada la familia Noto Sans
(`automatizacion/fuentes/`). Se revisó con el importador de IDML de Scribus:
posiciones, imágenes, colores, fuentes y cortes de renglón coinciden con el
PDF. No se ha abierto todavía en InDesign.

Requisitos: LuaLaTeX, Python 3 con PyYAML, Pillow y PyMuPDF (OpenCV es
opcional: centra las fotos en los rostros) y `pdftoppm`. Los archivos
intermedios van en `build/postales/`.
