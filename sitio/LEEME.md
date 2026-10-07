# Sitio web · 48.º FIMNME

Sitio en [Jekyll](https://jekyllrb.com/) con toda la programación del Foro. Su
contenido sale del mismo `fimnme2026-programa.md` que el Programa general y el
resumido: **no se edita a mano**, se corrige el Markdown y se regenera.

```bash
sitio/genera.sh              # contenido + recursos + compilación (sitio/_site)
sitio/genera.sh --servir     # además lo sirve en http://localhost:4000 para revisarlo
sitio/genera.sh --contenido  # solo regenera el contenido (sin Jekyll)
cd sitio && jekyll build     # solo compila (el contenido generado ya está en el repo)
```

`./compila.sh` (compilación completa) también regenera el sitio al final.

Requisitos: pandoc ≥ 3.1 y Python 3 con Pillow, NumPy y PyMuPDF para generar
el contenido; Ruby con Jekyll 4.4 para compilarlo (`cd sitio && bundle install`).
El contenido generado se guarda en el repositorio, así que para compilar el
sitio basta Jekyll.

Para publicarlo se copia el contenido de `sitio/_site/` al servidor (son
archivos estáticos): `sitio/publicar.sh CARPETA` lo compila y lo copia, en el
mismo servidor o por SSH. **Cómo montarlo en un VPS con su dominio y HTTPS:
[`DESPLIEGUE.md`](DESPLIEGUE.md).** En `_config.yml`, `url` es el dominio
(se usa en los enlaces para compartir en redes; ahora el de prueba,
`fimnme.qumran.cc`), `indexar: false` pide a los buscadores que no lo indexen
mientras es de prueba, y `baseurl` va solo si el sitio queda en una subcarpeta.

## Páginas

| Página | Qué muestra |
|---|---|
| Inicio | Portada (como la del programa), cifras del Foro, próximos eventos (según la fecha del día), calendario de noviembre, partes del programa, abono de inauguración y clausura, logotipos. |
| Programación | Agenda día por día con filtros por parte (Ciudad de México, En los estados, Actividades académicas, Ecos del Foro, Coloquio) y búsqueda por obra, compositor, intérprete o sede. El filtro queda en la dirección (`?seccion=estados`, `?q=saariaho`) para compartirla. |
| Cada evento (`/conciertos/…/`) | Fecha, sede con dirección y «Cómo llegar», «Agregar a mi calendario» (Google Calendar o archivo .ics), programa, semblanzas con foto, notas al programa (desplegables) y logotipos. La dirección es la misma etiqueta que usa el Programa general (`vie-nov-6-inauguracion-osn-carrasco-hofele`). |
| Sedes | Sedes con dirección, mapa y lo que se presenta en cada una. |
| Coloquio Enríquez &#124; 100 | Presentación y programa del Coloquio. |
| Programa de mano | Descargas: Programa general, Programa resumido y postal del abono. |
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
| `recursos.py` | Fotos y logotipos ligeros, logotipos «48» y CNMO en SVG, partitura, ícono, imagen para redes, precios del abono y descargas. |
| `genera.sh` | Ejecuta los dos anteriores y compila con Jekyll. |
| `publicar.sh`, `DESPLIEGUE.md` | Compila y copia el sitio al servidor; guía para montarlo en un VPS. |
| `_config.yml`, `Gemfile` | Configuración de Jekyll. |
| `_layouts/`, `_includes/` | Plantillas: `base` (encabezado y pie), `pagina` (bandas de título), `evento` (cada concierto), `tarjeta` (evento en la agenda). |
| `index.html`, `programacion.html`, `sedes.html`, `coloquio.html`, `creditos.html`, `descargas.html`, `404.html`, `robots.txt` | Páginas. |
| `assets/css/sitio.css`, `assets/js/sitio.js` | Estilos y comportamiento (sin dependencias; sin JavaScript el sitio muestra todo). |
| `assets/img/cultura.svg`, `inbal.svg` | Logotipos oficiales del pie (del sitio del Palacio de Bellas Artes). |

Generado (no editar: lo reescribe `genera.sh`):

| Archivo | Contenido |
|---|---|
| `_conciertos/*.html` | Una página por concierto, actividad académica o sesión del Coloquio. |
| `_data/agenda.json`, `sedes.json`, `secciones.json`, `foro.json`, `logos.json` | Agenda por día, sedes, partes, cifras (conciertos, estrenos, sedes) y logotipos. |
| `_data/abono.json` | Precios y sede del abono: los de `postal/postal.tex`. |
| `_data/descargas.json`, `descargas/` | Copias del Programa general, del resumido y de la postal. |
| `_includes/generado/` | Coloquio, créditos, directorio y logotipos en SVG. |
| `assets/fotos/`, `assets/logos/`, `assets/img/` (salvo `cultura.svg` e `inbal.svg`) | Fotos, logotipos e imágenes. |

## Notas

- Los logotipos de cada actividad académica son los de su bloque `::: logos`
  (en el programa general se juntan en una sola franja).
- Las cifras de estrenos cuentan cada estreno una vez (como el Programa
  resumido): una obra que se repite en otra sede no vuelve a contar.
- En las tarjetas de la agenda, de un conjunto se dan el nombre y quien lo
  dirige, no la lista de integrantes (está completa en la página del evento).
- La duración en «Agregar a mi calendario» es de dos horas (el programa no
  indica la hora de término).
- Las remisiones del Markdown a otra página (`\pageref{conc:…}`) se vuelven
  enlaces; las semblanzas y notas repetidas enlazan a su primera aparición.
