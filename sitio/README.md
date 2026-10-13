# Sitio web · 48º FIMNME

Sitio en [Jekyll](https://jekyllrb.com/) con toda la programación del Foro. Su
contenido sale del mismo `fimnme2026-programa.md` que el Programa general y el
resumido: **no se edita a mano**, se corrige el Markdown y se regenera.

```bash
sitio/genera.sh              # contenido + recursos + compilación (sitio/_site/2026)
sitio/genera.sh --servir     # además lo sirve en http://localhost:4000/2026/ para revisarlo
sitio/genera.sh --contenido  # solo regenera el contenido (sin Jekyll)
sitio/genera.sh --compilar   # solo compila (el contenido generado ya está en el repo)
```

`./compila.sh` (compilación completa) también regenera el sitio al final.

Requisitos: pandoc ≥ 3.1 y Python 3 con Pillow, NumPy y PyMuPDF para generar
el contenido; Ruby con Jekyll 4.4 para compilarlo (`cd sitio && bundle install`).
El contenido generado se guarda en el repositorio, así que para compilar el
sitio basta Jekyll.

Las direcciones llevan el año de la edición: `…/2026/`,
`…/2026/programacion/`, `…/2026/conciertos/…/`. Así las ediciones pueden
convivir en el mismo dominio. El sitio se compila en `sitio/_site/2026/`. En
`sitio/_site/` quedan además una página que redirige de la raíz del dominio a
`/2026/` y el `robots.txt`.

Para publicarlo se copia el contenido de `sitio/_site/` al servidor (son
archivos estáticos): `sitio/publicar.sh CARPETA` lo compila y lo copia, en el
mismo servidor o por SSH. Para entregarlo en un zip (git pull, compilar y
comprimir `sitio/_site/`), los pasos están en el `README.md` principal,
«Sitio web: compilarlo y entregarlo a Informática». **Cómo montarlo en un VPS con su dominio y HTTPS:
[`DESPLIEGUE.md`](DESPLIEGUE.md).**

En `_config.yml`:

- `url` es el dominio. Se usa en los enlaces para compartir en redes; ahora es
  el de prueba, `fimnme.qumran.cc`.
- `baseurl` es la carpeta de la edición (`"/2026"`).
- `indexar: false` pide a los buscadores que no lo indexen mientras es de
  prueba.

## Páginas

| Página | Qué muestra |
|---|---|
| Inicio | Portada (como la del programa), cifras del Foro, próximos eventos (según la fecha del día), calendario de noviembre, partes del programa, abono de inauguración y clausura, logotipos. |
| Programación | Agenda día por día con filtros por parte (Ciudad de México, En los estados, Actividades académicas, Ecos del Foro, Coloquio) y búsqueda por obra, compositor, intérprete o sede. El filtro queda en la dirección (`?seccion=estados`, `?q=saariaho`) para compartirla. |
| Cada evento (`/2026/conciertos/…/`) | Fecha, sede con dirección y «Cómo llegar», «Agregar a mi calendario» (Google Calendar o archivo .ics), su postal (con un clic, en grande; con un botón, para descargarla), programa, semblanzas con foto (con un clic, la foto completa), notas al programa (desplegables) y logotipos. La dirección es la misma etiqueta que usa el Programa general (`vie-nov-6-inauguracion-osn-carrasco-hofele`). |
| Sedes | Sedes con dirección, mapa y lo que se presenta en cada una. |
| Coloquio Enríquez &#124; 100 | Presentación y programa del Coloquio. |
| Programa de mano (`/2026/descargas/`) | El Programa general y el resumido, cada uno con su código QR; un QR de la propia página (para carteles e impresos) y la galería de las postales de todos los eventos, por parte del programa. |
| Créditos | Directorio de Cultura e INBAL, créditos y directorio de la CNMO y del Palacio. |

El encabezado y el pie siguen la estructura del sitio del Palacio de Bellas
Artes (barra oscura con logotipo y menú; pie con los logotipos oficiales de la
Secretaría de Cultura y del INBAL y franja final). El contenido usa el diseño
del programa de mano: Noto Sans, los mismos verdes y el fondo beige, la
partitura de *1 x 4* de Enríquez en las bandas de título, los filetes y las
versalitas espaciadas.

## Cómo está organizado

| Archivo | Para qué sirve |
|---|---|
| `sitio.lua` | Filtro de pandoc: lee el Markdown y escribe el contenido (abajo). |
| `recursos.py` | Fotos y logotipos ligeros, logotipos «48» y CNMO en SVG, partitura, ícono, imagen para redes, precios del abono, descargas y postales. |
| `genera.sh` | Ejecuta los dos anteriores y compila con Jekyll. |
| `publicar.sh`, `DESPLIEGUE.md` | Compila y copia el sitio al servidor; guía para montarlo en un VPS. |
| `_config.yml`, `Gemfile` | Configuración de Jekyll. |
| `_plugins/qr.rb` | Genera al compilar los códigos QR de la página de descargas (`descargas/qr-*.svg`), con la dirección de `_config.yml` (`url` y `baseurl`): si cambia el dominio, basta volver a compilar. Usa la gema `rqrcode_core` (en el `Gemfile`); sin ella el sitio se compila igual, sin QR. |
| `_layouts/`, `_includes/` | Plantillas: `base` (encabezado y pie), `pagina` (bandas de título), `evento` (cada concierto), `tarjeta` (evento en la agenda). |
| `index.html`, `programacion.html`, `sedes.html`, `coloquio.html`, `creditos.html`, `descargas.html`, `404.html`, `robots.txt` | Páginas. |
| `assets/css/sitio.css`, `assets/js/sitio.js` | Estilos y comportamiento (sin dependencias; sin JavaScript el sitio muestra todo). |
| `assets/img/cultura.svg`, `inbal.svg` | Logotipos oficiales del pie (del sitio del Palacio de Bellas Artes). |

Generado (no editar: lo reescribe `genera.sh`):

| Archivo | Contenido |
|---|---|
| `_conciertos/*.html` | Una página por concierto, actividad académica o sesión del Coloquio. |
| `_data/agenda.json`, `sedes.json`, `secciones.json`, `foro.json`, `logos.json` | Agenda por día, sedes, partes, cifras (conciertos, obras, estrenos, sedes) y logotipos. |
| `_data/abono.json` | Precios y sede del abono: los de `postales/abono/abono.tex`. |
| `_data/descargas.json`, `descargas/` | Copias del Programa general y del resumido. |
| `_data/postales.json`, `postales/`, `assets/postales/` | La postal de cada evento (de `postales/jpg/`): el JPG de 1080 × 1350 px para descargarla y una vista previa ligera (JPG de 540 × 675 px). |
| `_includes/generado/` | Coloquio, créditos, directorio y logotipos en SVG. |
| `assets/fotos/comp/`, `assets/fotos/int/` | Las fotos de las fichas: el recorte en círculo del Programa general (240 px). |
| `assets/fotos/completas/` | Cada foto del Markdown entera, sin recortar (hasta 1000 px), para verla en grande. |
| `assets/logos/`, `assets/img/` (salvo `cultura.svg` e `inbal.svg`) | Logotipos e imágenes. |

## Notas

- Los logotipos de cada actividad académica son los de su bloque `::: logos`
  (en el programa general se juntan en una sola franja).
- Las cifras del inicio: los conciertos cuentan cada función (el Coro de
  Madrigalistas, con dos, cuenta dos; las instalaciones sonoras no cuentan);
  las obras interpretadas, cada obra una vez aunque se toque en varios
  conciertos (la misma obra y el mismo compositor; si el año no coincide, son
  versiones distintas y cuentan aparte; las improvisaciones no cuentan); los
  estrenos, cada estreno una vez (como el Programa resumido): una obra que se
  repite en otra sede no vuelve a contar; las actividades académicas suman las
  del Coloquio.
- En las tarjetas de la agenda, de un conjunto se dan el nombre y quien lo
  dirige, no la lista de integrantes (está completa en la página del evento).
- La duración en «Agregar a mi calendario» es de dos horas (el programa no
  indica la hora de término).
- Las remisiones del Markdown a otra página (`\pageref{conc:…}`) se vuelven
  enlaces.
- En el programa de cada evento, cada compositor enlaza a su semblanza (más
  abajo, en la misma página) y cada obra a su nota al programa (que se abre)
  o, si no la tiene, a la semblanza de su compositor. Los compositores sin
  semblanza en el Markdown quedan sin enlace.
- Están todas las fotos del Markdown, cada una en dos versiones: el recorte en
  círculo centrado en el rostro (el del Programa general) y, con un clic sobre
  él, la foto completa. Conservan la carpeta del Markdown (`comp/` e `int/`),
  porque hay nombres que están en las dos con fotos distintas (Rodrigo Cadet
  e Iracema de Andrade, como compositores y como intérpretes).
- Cada evento muestra completas sus semblanzas (con foto) y notas al programa,
  aunque ya hayan salido en otro (en los PDF, las repetidas remiten a su
  página): si el Markdown no las repite, se toman de su primera aparición.
