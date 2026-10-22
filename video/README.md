# Video promocional · 48º FIMNME (muestra)

Video corto para redes, vertical 9:16 (1080 × 1920 px, 30 cuadros por
segundo, H.264): Reels, TikTok, historias y Shorts. Dura unos 30 segundos y
por ahora va **sin música** (no lleva pista de audio).

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
| 2 | **Video** (OSN) | La música de hoy / suena en vivo |
| 3 | Cifra | 47 conciertos en 10 ciudades del país |
| 4 | **Video** (Tambuco) | 109 estrenos: 51 mundiales · 58 en México |
| 5 | Cifra | 194 compositoras y compositores de 31 países |
| 6 | **Video** (Cuarteto de Bellas Artes) | 1926 · 2026 · Manuel Enríquez · Centenario · Conciertos y coloquio |
| 7 | Palacio de Bellas Artes | Inauguración: Orquesta Sinfónica Nacional · 6 nov / Clausura: Tambuco · 21 nov / Abono en Ticketmaster |
| 8 | **Video** (Black Noise) | Conciertos · Actividades académicas · Coloquio Enríquez \| 100 |
| 9 | Cierre | Programación completa: forodemusicanueva.inba.gob.mx/2026 · CNMO · Cultura e INBAL |

Los textos, las duraciones y el orden se cambian en `guion.yaml`.

## Los videos de los ensambles

Las escenas de **video** muestran por ahora una foto del ensamble (con un
acercamiento lento) y la etiqueta «ESPACIO PARA VIDEO». Para poner los
videos:

1. Subir los videos a `video/clips/` (MP4 o MOV). Se usan unos 3 segundos de
   cada uno; mejor si están grabados en vertical. Los horizontales se recortan
   al centro, así que conviene que lo importante quede en medio. El audio de
   los videos no se usa.
2. En `guion.yaml`, en la escena correspondiente, poner la ruta en `video:`
   (p. ej. `video: video/clips/tambuco.mp4`) y, si el mejor momento no está al
   principio, el segundo en que empieza: `inicio: 12.5`. Con un video, la foto
   y la etiqueta dejan de usarse.
3. Volver a generar el video:

```bash
python3 video/genera.py              # el video y la hoja de cuadros (~1 min)
python3 video/genera.py --muestras   # solo la hoja de cuadros (segundos)
```

Requisitos: Python 3 con Pillow, PyYAML y PyMuPDF; ffmpeg; LuaLaTeX (para los
logotipos vectoriales del Foro y de la CNMO).
