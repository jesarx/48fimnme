# Boletín por correo · 48º FIMNME

Un boletín para enviar por correo a las personas participantes y a sus
amistades:
- la invitación;
- el Foro en cifras;
- la inauguración y la clausura, con el abono y el botón para comprarlo;
- el Coloquio Manuel Enríquez 100;
- la programación día por día, con un enlace a cada evento en el sitio;
- al pie, la Coordinación Nacional de Música y Ópera y la pleca de Cultura e
  INBAL, como en las postales.

| Archivo | Para qué sirve |
|---|---|
| `fimnme2026-newsletter-outlook.html` | **Para enviarlo desde Outlook en la web.** Lleva las imágenes dentro: se abre en el navegador, se copia y se pega en un mensaje nuevo. |
| `fimnme2026-newsletter.eml` | **Para enviarlo desde Outlook de escritorio** (Windows). Es un mensaje sin enviar, con el asunto y las imágenes: se abre con doble clic. |
| `fimnme2026-newsletter.html` | El mismo boletín, con las imágenes de `img/`, para verlo y revisarlo. |
| `img/` | Encabezado, pie con los logotipos y las postales de la inauguración y la clausura. |
| `genera.py`, `imagenes.tex` | Generan todo lo anterior (ver «Cambiar algo» al final). |

## Enviarlo desde Outlook en la web

1. **Abrir el boletín en el navegador.** Hacer doble clic en
   `fimnme2026-newsletter-outlook.html`, o arrastrarlo a una ventana de
   Chrome, Edge o Firefox.
   - Si no tienes el repositorio en tu computadora, ábrelo en GitHub y usa el
     botón «Download raw file» (descargar).
2. **Copiarlo.** Hacer clic en cualquier parte de la página y luego:
   - `Ctrl+A` (seleccionar todo) y `Ctrl+C` (copiar);
   - en Mac, `Cmd+A` y `Cmd+C`.
3. **Pegarlo en un mensaje nuevo.** En Outlook en la web (outlook.office.com),
   hacer clic en **Correo nuevo**, luego en el cuerpo del mensaje, y pegar con
   `Ctrl+V` (`Cmd+V` en Mac).
   - Si tienes firma automática, bórrala antes de pegar: el boletín ya cierra
     con los logotipos.
   - Si Outlook pregunta cómo pegar, elige **Mantener formato de origen**.
   - Debe aparecer el boletín completo, con sus imágenes.
4. **Asunto.** Sugerido:
   `48º Foro Internacional de Música Nueva Manuel Enríquez · 6 al 21 de noviembre`
5. **Mandar una prueba.** Pon solo tu dirección en «Para» y envía.
   - Si puedes, envíalo también a una cuenta de Gmail y ábrelo en el celular.
   - Revisa que se vean las imágenes y que los enlaces abran el sitio.
6. **Enviarlo a todas las personas.** Repite los pasos 3 y 4 en un mensaje
   nuevo:
   - en **Para**, tu propia dirección;
   - en **CCO** (copia oculta), todas las demás. Si no ves el campo, haz clic
     en «CCO» a la derecha de «Para».

   Así nadie ve las direcciones de las demás personas (son datos personales) y
   nadie responde «a todos» por error.
   - Las direcciones se pegan separadas por punto y coma (`;`).
   - Si están en una columna de Excel, esta fórmula las une así:
     `=UNIRCADENAS(";";VERDADERO;A2:A300)` (en Excel en inglés, `TEXTJOIN`).
7. **Muchas direcciones: en grupos.** Las cuentas institucionales tienen un
   límite de destinatarios por mensaje y por día (en Microsoft 365 suele ser
   de 500 por mensaje).
   - Lo prudente es enviar grupos de 100 a 200 direcciones, cada grupo en un
     mensaje nuevo (pasos 3, 4 y 6).
   - Si Outlook rechaza un envío, divide el grupo.

## Enviarlo desde Outlook de escritorio

- **Outlook clásico para Windows:** doble clic en `fimnme2026-newsletter.eml`.
  1. Se abre como mensaje nuevo, con el asunto y el boletín listos.
  2. Agrega los destinatarios (en CCO, como arriba) y envía.
- **Nuevo Outlook para Windows o Outlook para Mac:** quizá abran el `.eml`
  solo para leerlo. En ese caso, usa el método de copiar y pegar de arriba:
  funciona igual que en la web.

## Si algo no se ve bien

- **Al pegar no aparecen las imágenes:** envíalo desde Outlook de escritorio
  con el `.eml`, que lleva las imágenes adjuntas en línea.
- **En la prueba que llega a Gmail no se ven las imágenes:** usa también el
  `.eml` desde Outlook de escritorio.
- **La letra:** el boletín usa Noto Sans si el equipo la tiene y, si no, Segoe
  UI o Arial. Es normal que cambie un poco de un programa a otro.
- **Modo oscuro:** algunos programas de correo cambian los colores. Es normal.

## Cambiar algo

El boletín sale de los mismos datos que el sitio, y estos del Markdown:
`sitio/_data/agenda.json`, `foro.json` y `abono.json`. Si cambia algún
evento, se regeneran con la compilación completa (`./compila.sh`), que al
final también rehace el boletín. Para rehacer solo el boletín:

```bash
sitio/genera.sh --contenido   # si cambió el Markdown: actualiza los datos del sitio
python3 newsletter/genera.py  # rehace el boletín (unos segundos)
```

- **Textos** (invitación, asunto, títulos de las secciones): en `genera.py`.
  - Asunto, título, abono y entrada: al principio del archivo.
  - Los demás textos: en `armar_html` (y en `armar_texto`, la versión sin
    formato del `.eml`).
- **Encabezado y pie:** en `imagenes.tex`.
  - El pie usa la CNMO y la pleca de Cultura e INBAL de las postales, con sus
    proporciones.
- **Compra del abono:** el botón lleva a `abono_boletos` de
  `sitio/_config.yml` (la misma dirección que usa el sitio).
- **Suscripción:** el enlace «Suscríbete al boletín de noticias del Foro» (para
  quien lo reciba reenviado) lleva a `boletin_suscripcion` de
  `sitio/_config.yml`, el formulario de Brevo.
- **Enlaces:** apuntan al sitio, a la dirección de `url` y `baseurl` en
  `sitio/_config.yml`: `https://forodemusicanueva.inba.gob.mx/2026`.
  - Si el sitio se publica en otra dirección, cámbiala ahí y rehaz el boletín
    antes de enviarlo.
