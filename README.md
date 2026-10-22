# 48º Foro Internacional de Música Nueva Manuel Enríquez

Materiales del **48º FIMNME** (6 al 21 de noviembre de 2026), de la
Coordinación Nacional de Música y Ópera del INBAL: el programa de mano, el
programa resumido, el sitio web, las postales para redes y el boletín por
correo.

Todo sale de un solo archivo, [`fimnme2026-programa.md`](fimnme2026-programa.md):
ahí está el contenido del Foro (conciertos, obras, semblanzas, notas al
programa, actividades académicas, Coloquio, sedes y créditos). Un cambio en el
Markdown se propaga a todos los materiales al volver a compilar.

| Material | Dónde queda | Detalles |
|---|---|---|
| Programa general (PDF, para imprimir y descargar) | [`fimnme2026-programa.pdf`](fimnme2026-programa.pdf) | este documento |
| Programa resumido (PDF) | [`resumen/fimnme2026-resumen.pdf`](resumen/fimnme2026-resumen.pdf) | [`resumen/README.md`](resumen/README.md) |
| Sitio web (Jekyll) | [`sitio/`](sitio/) → `sitio/_site/` | [`sitio/README.md`](sitio/README.md), [`sitio/DESPLIEGUE.md`](sitio/DESPLIEGUE.md) |
| Postales para redes, 1080 × 1350 px (PNG, JPG, PDF e IDML para InDesign) | [`postales/`](postales/) | [`postales/README.md`](postales/README.md) |
| Boletín por correo (HTML y versiones para Outlook) | [`newsletter/`](newsletter/) | [`newsletter/README.md`](newsletter/README.md) |
| Numeralia para la conferencia de prensa (Markdown y PDF, dos páginas) | [`conf_prensa/numeralia.pdf`](conf_prensa/numeralia.pdf) | [`conf_prensa/numeralia.md`](conf_prensa/numeralia.md) |
| Video promocional para redes, 9:16 (muestra, sin música) | [`video/fimnme2026-promo-muestra.mp4`](video/fimnme2026-promo-muestra.mp4) | [`video/README.md`](video/README.md) |

## Índice

- [Cómo funciona](#cómo-funciona)
- [Instalación](#instalación)
- [Compilar](#compilar)
- [Colaborar](#colaborar)
- [Sitio web: compilarlo y entregarlo a Informática](#sitio-web-compilarlo-y-entregarlo-a-informática)
- [Cómo está organizado](#cómo-está-organizado)
- [Tipografía automática](#tipografía-automática)
- [Convenciones del Markdown](#convenciones-del-markdown)
- [Derechos](#derechos)

## Cómo funciona

```
fimnme2026-programa.md ──┬─► pandoc + automatizacion/fimnme.lua + plantilla LaTeX ─► Programa general (PDF)
(+ fotos comp/ e int/,   ├─► pandoc + resumen/resumen.lua + resumen.latex ────────► Programa resumido (PDF)
 logotipos logos/)       └─► pandoc + sitio/sitio.lua ─► páginas y datos del sitio ─► Jekyll ─► Sitio web
                                                          │
                                                          ├─► postales/genera.py (LaTeX) ─► Postales
                                                          └─► newsletter/genera.py ───────► Boletín
```

No se usa una plantilla de pandoc convencional. El filtro
`automatizacion/fimnme.lua` reconoce las convenciones del Markdown (ver
[Convenciones del Markdown](#convenciones-del-markdown)) y escribe
directamente las macros del diseño: conciertos, fichas, actividades,
logotipos. La plantilla `automatizacion/plantilla/fimnme.latex` define esas
macros, es decir, el aspecto del programa. El resumido funciona igual
(`resumen/resumen.lua` y `resumen/resumen.latex`). El sitio también:
`sitio/sitio.lua` escribe las páginas y los datos de Jekyll. De esos datos
salen las postales (una por evento, compuestas en LaTeX) y el boletín.

Las fotos se recortan solas (centradas en el rostro, si está OpenCV) y los
logotipos se pasan a un solo color y a un tamaño visual parejo; las fuentes
Noto Sans van incluidas en `automatizacion/fuentes/`.

Para otra edición hacen falta tres cosas:

- un Markdown que siga las mismas convenciones;
- cambiar el diseño en las plantillas y en `sitio/assets/`;
- poner el año en `baseurl` de `sitio/_config.yml`.

## Instalación

Hace falta:

- pandoc ≥ 3.1;
- TeX Live ≥ 2023 con LuaLaTeX;
- poppler (`pdftoppm`, `pdfinfo`);
- Python 3 con los paquetes de [`requirements.txt`](requirements.txt): Pillow, NumPy, PyYAML,
  PyMuPDF y, opcional, OpenCV (sin OpenCV las fotos se recortan al centro, no
  en el rostro);
- para compilar el sitio web, Ruby 3 con bundler: Jekyll se instala dentro de
  `sitio/vendor/` (ver [Sitio web](#sitio-web-compilarlo-y-entregarlo-a-informática)).

**Debian o Ubuntu:**

```bash
sudo apt install pandoc poppler-utils python3-pip python3-venv \
  texlive-luatex texlive-latex-recommended texlive-latex-extra \
  texlive-pictures texlive-lang-spanish
python3 -m venv .venv && . .venv/bin/activate   # opcional: un entorno solo para el proyecto
pip install -r requirements.txt
```

**macOS** (con [Homebrew](https://brew.sh/)):

```bash
brew install pandoc poppler
brew install --cask mactex-no-gui
pip3 install -r requirements.txt
```

**Paquetes de TeX Live.** Con TeX Live completo ya está todo. En Debian o
Ubuntu bastan los de arriba. Los dos paquetes de LaTeX menos comunes son
estos:

- `truncate` (de `texlive-latex-extra`) recorta el encabezado de página
  cuando el título del concierto no cabe. Hoy lo hace en dos: la mesa
  redonda del 10 de noviembre y «Tres acercamientos a *Oltracuidansa* de
  Scodanibbio».
- `luacolor` (viene con `texlive-luatex`) se encarga del color en LuaLaTeX.

Ninguno pide instalar algo más: `texlive-latex-extra` ya hace falta para
`tcolorbox`, `enumitem` y `xurl`, y `texlive-luatex` para LuaLaTeX.

## Compilar

Desde la raíz del repositorio:

```bash
./compila.sh                 # todo: programa, resumido, sitio, postales y boletín (~25 min)
./compila.sh --rapido        # solo el programa general, en una pasada (para revisar cambios)
resumen/compila.sh           # solo el programa resumido
sitio/genera.sh              # solo el sitio web (ver sitio/README.md)
python3 postales/genera.py   # solo las postales de los eventos
postales/abono/compila.sh    # solo la postal del abono
python3 newsletter/genera.py # solo el boletín por correo
conf_prensa/genera.sh        # solo el PDF de la numeralia (las cifras se editan en conf_prensa/numeralia.md)
python3 video/genera.py      # solo el video promocional (ver video/README.md)
```

La compilación completa sigue este orden, porque cada paso usa lo anterior:

1. programa general (de 3 a 10 pasadas de LuaLaTeX, hasta que las
   referencias de página se estabilizan);
2. programa resumido;
3. contenido del sitio;
4. postal del abono y postales de los eventos (toman sus datos del contenido
   del sitio);
5. recursos y compilación del sitio (el sitio muestra las postales);
6. boletín.

Los archivos intermedios quedan en `build/`, que no se guarda en el
repositorio.

## Colaborar

**La regla principal: todo se corrige en el Markdown y se vuelve a compilar.**
Los archivos generados no se editan a mano, porque la siguiente compilación
los reescribe:

- los PDF;
- `sitio/_conciertos/`, `sitio/_data/`, `sitio/assets/fotos/` y
  `sitio/assets/logos/`;
- `postales/png/`, `jpg/`, `pdf/` e `idml/`;
- los HTML y el `.eml` de `newsletter/`.

**Dónde va cada cosa:**

| Para cambiar… | Se edita… |
|---|---|
| Programas, obras, semblanzas, notas, sedes, horarios, créditos | `fimnme2026-programa.md` (ver [Convenciones](#convenciones-del-markdown)) |
| Fotos de compositoras, compositores e intérpretes | `comp/` e `int/` (con el nombre de la persona: `comp/Federico Núñez.jpg`, que en el Markdown se escribe `comp/Federico%20Núñez.jpg`). El círculo de la ficha se recorta solo, centrado en el rostro; si la persona sale lejos y la cara queda chica, se acerca en `ACERCAR` de `automatizacion/preparar_imagenes.py` (un TIFF u otro formato conviene pasarlo antes a JPG). |
| Logotipos de un concierto | `logos/` y el bloque `::: logos` del concierto |
| Antetítulo, intérpretes y fotos de una postal | `postales/postales.yaml` |
| Textos y precios del abono | `postales/abono/abono.tex` |
| Diseño del programa general | `automatizacion/plantilla/fimnme.latex` |
| Diseño del sitio | `sitio/_layouts/`, `sitio/_includes/`, `sitio/assets/css/sitio.css` |
| Textos del boletín | `newsletter/genera.py` |

**Flujo de trabajo:**

1. `git pull` para partir de lo último.
2. Una rama para el cambio: `git switch -c nombre-del-cambio`.
3. Editar y compilar: `./compila.sh`, o solo lo que cambió (ver
   [Compilar](#compilar)).
4. Revisar el resultado:
   - las páginas que cambian en el PDF;
   - el sitio en el navegador (`sitio/genera.sh --servir`);
   - las postales afectadas.
5. Hacer commit. Los materiales generados también se guardan en el
   repositorio, así quien no compila puede descargar los PDF y las
   postales, e Informática puede compilar el sitio solo con Jekyll.
   - Conviene separar el cambio de fuente (Markdown, plantillas, código) de
     los archivos regenerados, en dos commits.
   - Los mensajes van en español y dicen qué cambia y dónde (por ejemplo:
     «Morelia, Julio I. Cervantes: obra de Federico Núñez»).
6. `git push` y abrir un pull request contra `main`.

## Sitio web: compilarlo y entregarlo a Informática

El contenido del sitio ya está generado en el repositorio (cada compilación
completa lo actualiza), así que para entregarlo **basta Jekyll**: no hacen
falta pandoc, LaTeX ni Python.

**Una sola vez** (instalar Jekyll y la gema de los códigos QR, dentro de
`sitio/vendor/`):

```bash
# Ruby 3 o posterior con bundler:
#   macOS:          brew install ruby          (y abrir una terminal nueva)
#   Debian/Ubuntu:  sudo apt install ruby-full build-essential zlib1g-dev
#   Windows:        RubyInstaller con DevKit (rubyinstaller.org) y Git Bash
gem install bundler
cd sitio
bundle config set --local path vendor/bundle
bundle install
cd ..
```

**Cada vez:**

```bash
git pull                        # trae lo último
sitio/genera.sh --compilar      # compila en sitio/_site/
```

Para revisarlo antes en el navegador: `sitio/genera.sh --servir` y abrir
<http://localhost:4000/2026/>.

**Para Informática**, se comprime el **contenido** de `sitio/_site/` (no la
carpeta `sitio/`):

```bash
cd sitio/_site && zip -r ../../fimnme2026-sitio.zip . && cd ../..
```

(En macOS o Windows también se puede seleccionar todo lo que hay dentro de
`sitio/_site/` y elegir «Comprimir».) El zip lleva la carpeta `2026/` (el
sitio: páginas HTML, CSS, JavaScript, imágenes y PDF), un `index.html` que
redirige de la raíz del dominio a `/2026/` y el `robots.txt`. Son archivos
estáticos: se copian tal cual a la raíz del servidor web, sin base de datos
ni PHP.

**La dirección del sitio, la venta del abono y la suscripción al boletín** están en `sitio/_config.yml`:

- `url`: el dominio donde se publica, `https://forodemusicanueva.inba.gob.mx`
  (el de prueba era `https://fimnme.qumran.cc`). Se usa en los enlaces para
  compartir, en los códigos QR de la página de descargas y en los enlaces
  del boletín.
- `abono_boletos`: la página de venta del abono (Ticketmaster), a la que
  llevan los botones «Comprar el abono» del sitio y del boletín.
- `boletin_suscripcion`: el formulario de Brevo para suscribirse al boletín de
  noticias del FIMNME (franja de la portada, pie de todas las páginas y
  boletín por correo).
- `indexar: true`, para que los buscadores lo encuentren (en `false` les
  pide que no lo indexen: es lo que se usa en un sitio de prueba).
- `baseurl` se queda en `"/2026"` si el sitio va en `…/2026/` del dominio.

Si alguno cambia, hay que volver a compilar (`sitio/genera.sh --compilar`,
y `python3 newsletter/genera.py` para el boletín) y hacer el zip. Más detalles en [`sitio/README.md`](sitio/README.md) y
[`sitio/DESPLIEGUE.md`](sitio/DESPLIEGUE.md).

## Cómo está organizado

| Archivo | Para qué sirve |
|---|---|
| `fimnme2026-programa.md`, `fimnme2026-programa.yaml` | Contenido y metadatos del programa. |
| `compila.sh` | Compilación completa (ver [Compilar](#compilar)). |
| `comp/`, `int/` | Fotos originales de compositores e intérpretes (las que usa el Markdown). |
| `logos/` | Logotipos originales de sedes, instituciones y patrocinadores, con sus variantes (también el de la CNMO en versión horizontal, de donde sale `automatizacion/plantilla/logo-cnmo-horizontal.tex`). |
| `resumen/` | Programa resumido (agenda, programas condensados, logotipos y directorio; ver `resumen/README.md`). |
| `sitio/` | Sitio web en Jekyll con toda la programación (agenda con filtros y búsqueda, una página por concierto con programa, semblanzas, notas y su postal, sedes, Coloquio, descargas con QR), generado del mismo Markdown; ver `sitio/README.md` (y `sitio/DESPLIEGUE.md` para montarlo en un VPS). |
| `postales/` | Postales para redes de todos los eventos (conciertos en verde; actividades académicas y Coloquio en verde azulado), 1080 × 1350 px, en carpetas por formato: `png/`, `jpg/`, `pdf/` e `idml/` (InDesign, 1080 × 1350 px, con sus imágenes vinculadas y la fuente: la carpeta se comprime y se envía tal cual). Cada archivo lleva al final del nombre la fecha en que se compiló (p. ej. `fimnme2026-postal-jue-nov-19-ocba_20oct.png`). Datos del Markdown y, en `postales.yaml`, antetítulo, título, intérpretes y fotos; ver `postales/README.md`. |
| `postales/abono/` | Postal para la venta del abono (concierto inaugural y de clausura; los precios son por ambos conciertos); sale, como las demás, en `postales/png`, `jpg`, `pdf` e `idml`. Sus textos están en `postales/abono/abono.tex`: si cambian esos conciertos en el Markdown, hay que cambiarlos ahí (el sitio web toma de ahí los precios del abono). |
| `newsletter/` | Boletín por correo para participantes y amistades (invitación, cifras, inauguración y clausura con el abono, Coloquio y programación día por día, con la CNMO y la pleca de Cultura e INBAL al pie): HTML, versión para pegar en Outlook en la web y `.eml` para Outlook de escritorio, generados de los datos del sitio. Cómo enviarlo: `newsletter/README.md`. |
| `conf_prensa/` | Numeralia para la conferencia de prensa: cifras del Foro, personas compositoras (por género y nacionalidad), obras y estrenos, intérpretes, convocatorias y tabulador de pagos. La fuente es `numeralia.md` (cifras escritas a mano, contadas del Markdown y de las bases de las convocatorias, que no están en el repositorio); `genera.sh` hace el PDF con `numeralia.latex`. |
| `video/` | Video promocional para redes (9:16, unos 30 s, sin música): `guion.yaml` (escenas, textos y los videos de los ensambles), `genera.py` (Pillow y ffmpeg) y, en `clips/`, los videos de los ensambles. Mientras no hay videos, cada espacio muestra una foto y la etiqueta «ESPACIO PARA VIDEO». |
| `automatizacion/plantilla/fimnme.latex` | Diseño: página, tipografía, colores, portada, divisorias, encabezados, fichas, índices. |
| `automatizacion/fimnme.lua` | Convierte la estructura del Markdown en las macros del diseño. |
| `automatizacion/tipografia.lua` | Reglas de [tipografía automática](#tipografía-automática) (siglas, nombres sin cortar, últimos renglones). |
| `automatizacion/preparar_imagenes.py` | Recorta y ajusta las fotos de `comp/` e `int/` (en `build/fotos/`). |
| `automatizacion/preparar_logos.py` | Pasa a un solo color, recorta y separa los logotipos que usa el Markdown (en `build/logos/`). |
| `automatizacion/plantilla/ajuste.lua` | Ajuste fino de páginas (evita programas desbordados y finales de sección con pocas líneas). |
| `automatizacion/indice-onomastico.yaml` | Excepciones de apellidos para el índice onomástico (del programa y del sitio). |
| `automatizacion/fuentes/` | Noto Sans (licencia OFL), la fuente de todos los materiales. |
| `automatizacion/plantilla/logo-*.tex`, `partitura-1x4.pdf` | Logotipos y partitura de la portada, en vectorial. |
| `automatizacion/plantilla/pleca-cultura-inbal.pdf` | Pleca de la Secretaría de Cultura y el INBAL (pie de la contraportada), en vectorial, tomada de la plantilla institucional. |
| `requirements.txt` | Paquetes de Python. |

## Tipografía automática

En el texto corrido (semblanzas, notas, intérpretes, descripciones) el filtro
aplica tres reglas (`automatizacion/tipografia.lua`; el resumido usa las dos
últimas en la agenda):

- Las siglas van en versalitas (UNAM, OSN, INBAL…), para que no destaquen.
- Los nombres de personas y lugares procuran no cortarse entre renglones.
- El último renglón de un párrafo no queda con una sola palabra, ni con una
  sílaba suelta tras un guion.

Las uniones no son rígidas: si un renglón no tiene otra salida, TeX corta, así
que nada se sale del margen.

## Convenciones del Markdown

- `\part{TÍTULO}` abre una parte (página verde). Si le sigue un párrafo, se usa
  como subtítulo de la parte.
- `## VIE | NOV 6, 20 h - Título` abre un concierto (siempre en página nueva).
  Dos fechas: `## VIE | NOV 13, 19 h / DOM | NOV 15, 12 h - Título`. Las horas
  van sin «:00» (`12 h`), salvo si no son en punto (`13:30 h`); así salen en
  el programa general, el resumen y el sitio.
  El primer párrafo después del encabezado es la sede: primero el recinto y
  luego la sala («Palacio de Bellas Artes, Sala Principal»).
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
  el de un grupo que queda solo en su página. Si un programa no cabe en una
  página ni con el interlineado compacto y tiene intermedio, la segunda
  parte empieza en la página siguiente.
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
- Logotipos de un concierto: un bloque al final del concierto, una imagen
  por renglón (con `<…>` si la ruta tiene espacios):

  ```markdown
  ::: logos
  ![](<logos/logos OSN/OSN-1.png>)
  ![](<logos/logos OJUEM/02.CintilloLogos_OJUEM.ai>){recorte="0.12 0.38 0.28 0.6"}
  :::
  ```

  Van en una franja al pie de la última página del concierto (si ahí no
  caben, al pie del programa), todos en el verde oscuro del diseño y con un
  tamaño visual parejo. Ningún logotipo es mayor que los de Cultura e INBAL
  de la pleca de la contraportada (Cultura mide 29 × 7,5 mm): como máximo,
  6,5 mm de alto y 20 mm de ancho (`medida_logo` en
  `automatizacion/fimnme.lua`; el resumen usa la misma medida). Se aceptan
  PNG, JPG, PDF, AI y SVG. Atributos
  opcionales: `pagina=3` (página de un PDF/AI), `recorte="x0 y0 x1 y1"`
  (parte de la página, en fracciones), `partir=si` (separa un cintillo en
  logotipos sueltos) y `realce=0.3` (oscurece un logotipo muy pálido).
  Detalles en `automatizacion/preparar_logos.py`.
- Cada sección de un concierto (Programa, Personas compositoras,
  Intérpretes…) empieza en página nueva. Una sección que solo tenga
  referencias «Ver pág.» sigue en la página (salvo justo después del
  programa), y la sección siguiente puede seguir tras ella.
- Para remitir a la página de otro concierto: `` `\pageref{conc:mie-nov-18-electroacustica-i}`{=latex} ``.
  La etiqueta se forma sola con la fecha y el título del encabezado, en
  minúsculas, sin acentos y con guiones.
- Cada actividad académica va en un bloque que no se parte entre páginas.
  En el título de la actividad va lo que es (*Conferencia: …*, *Taller de
  trompeta*) y debajo solo quiénes participan, sin repetir datos. Lo que
  describe la actividad (de qué trata, a quién va dirigida, módulos con su
  hora) va en un bloque `::: descripcion`: sale en el programa general (un
  punto menor, tras un filete) y en el sitio web, no en el resumen. Cada
  actividad lleva su bloque `::: logos` al final (el sitio web los muestra en
  la página de cada una); en el programa general se juntan, sin repetir, en
  una sola franja al pie de la última página de actividades.
- `::: contraportada` (al final del Markdown): directorio de la Secretaría
  de Cultura y del INBAL. Va en la última página, con la pleca institucional
  al pie; el programa resumido también la lleva.
- No hace falta poner `\clearpage` ni `\vfill`: la paginación la decide la
  plantilla (se ignoran si aparecen).
- El índice general y el índice onomástico se generan automáticamente. El
  onomástico lista a las personas compositoras de los programas, cada una
  con un botoncito por concierto (la fecha, día/mes) que en el PDF lleva al
  concierto. Si una persona tiene dos conciertos el mismo día, la fecha lleva
  además la hora (o la ciudad, si la hora también coincide). Los apellidos
  compuestos y las partículas van en `automatizacion/indice-onomastico.yaml`.
  El sitio web tiene el mismo índice, en `/2026/indice/`.

## Derechos

Los textos (semblanzas y notas al programa), las fotografías y los logotipos
pertenecen a sus autoras, autores e instituciones, y están aquí para producir
los materiales del Foro. Las fuentes Noto Sans tienen licencia SIL Open Font
License (`automatizacion/fuentes/LICENCIA-OFL.txt`).
