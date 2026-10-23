# Video promocional · 48º FIMNME (muestra)

Video corto para redes, vertical 9:16 (1080 × 1920 px, 30 cuadros por
segundo, H.264): Reels, TikTok, historias y Shorts. Dura 33 segundos y por
ahora va **sin música** (no lleva pista de audio).

- `fimnme2026-promo-muestra.mp4`: el video.
- `fimnme2026-promo-muestras.jpg`: un cuadro de cada escena, para revisarlo
  de un vistazo.

Sigue el diseño de las postales: el verde con la partitura de *1x4* de
Manuel Enríquez (que sube despacio durante todo el video), el logotipo del
Foro en dorado, Noto Sans y, al cierre, la CNMO y la pleca de Cultura e
INBAL.

## Guion

| | Escena | Texto |
|---|---|---|
| 1 | Apertura | Logotipo · Foro Internacional de Música Nueva Manuel Enríquez · 6 al 21 de noviembre · 2026 · 48ª edición |
| 2 | **Video** (orquesta) | La música de hoy / suena en vivo |
| 3 | Cifra | 47 conciertos en 10 ciudades del país |
| 4 | **Video** (orquesta, alientos) | 107 estrenos: 49 mundiales · 58 en México |
| 5 | Cifra | 192 compositoras y compositores de 31 países |
| 6 | **Video** (orquesta, violinista) | 1926 · 2026 · Manuel Enríquez · Centenario · Conciertos y coloquio |
| 7 | **Video** (instalación) | Instalación sonora · Andrés Nuño de Buen · *Sobre las sensaciones de tono y otros fantasmas* · 7 y 8 nov · Casa Rafael Galván, UAM |
| 8 | Palacio de Bellas Artes | Inauguración: Orquesta Sinfónica Nacional · 6 nov / Clausura: Tambuco · 21 nov / Abono en Ticketmaster |
| 9 | **Video** (instalación) | Conciertos · Actividades académicas · Coloquio Enríquez \| 100 |
| 10 | Cierre | Programación completa: forodemusicanueva.inba.gob.mx/2026 · CNMO · Cultura e INBAL |

Los textos, las duraciones y el orden se cambian en `guion.yaml`.

## Los videos

Están en `video/clips/`, **recortados, verticales y sin audio**, para que el
repositorio no crezca: de cada video original se guardan solo los fragmentos
que se usan (unos 30 segundos, 2 a 4 MB).

- `orquesta-travelling.mp4`: el travelling de la orquesta (plano general,
  alientos de cerca y una violinista).
- `instalacion-nuno-de-buen.mp4`: la instalación de Andrés Nuño de Buen
  (tocándola, la torre de botellas y de cerca).

Por ahora esos dos se repiten en todas las escenas de video (en `guion.yaml`
están marcadas como «provisional»). Cada escena dice qué video usa (`video:`)
y desde qué segundo (`inicio:`); en el encabezado de `guion.yaml` está qué hay
en cada tramo de los dos videos.

Para agregar un video nuevo: subir el original (MP4 o MOV) y, antes de usarlo,
recortarlo a lo que sirve y pasarlo a vertical, sin audio, con ffmpeg (los
originales no se guardan en el repositorio). Por ejemplo, de un video
horizontal de 1920 × 1080, del segundo 12 al 20, tomando el centro:

```bash
ffmpeg -ss 12 -to 20 -i original.mp4 -vf "crop=608:1080:656:0" -an \
  -c:v libx264 -crf 23 -preset slow -pix_fmt yuv420p video/clips/nombre.mp4
```

Si una escena no tiene `video:`, muestra la `foto` con un acercamiento lento y
la etiqueta «ESPACIO PARA VIDEO».

Para volver a generar el video:

```bash
python3 video/genera.py              # el video y la hoja de cuadros (~1 min)
python3 video/genera.py --muestras   # solo la hoja de cuadros (segundos)
```

Requisitos: Python 3 con Pillow, PyYAML y PyMuPDF; ffmpeg; LuaLaTeX (para los
logotipos vectoriales del Foro y de la CNMO).
