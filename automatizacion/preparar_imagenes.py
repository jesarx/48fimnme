#!/usr/bin/env python3
"""Prepara las fotografías del programa para su uso en LaTeX.

Para cada imagen de ``comp/`` e ``int/``:

* aplica la orientación EXIF (LaTeX la ignora y las fotos de teléfono
  aparecerían giradas);
* convierte a RGB (CMYK, escala de grises, PNG con transparencia, TIFF...);
* recorta un cuadrado centrado en el rostro (o rostros, en fotos de grupo)
  usando la detección de caras de OpenCV, si está disponible;
* reescala con Lanczos a ``LADO`` píxeles y guarda un JPEG de buena calidad.

Así las fotos llegan al PDF nítidas y ligeras, sin necesidad de pasar el PDF
final por Ghostscript (que era lo que las pixelaba).

Las fotos de conjunto (tres o más rostros, apaisadas) se recortan en formato
2:1 para mostrarse a lo ancho, en lugar de en un círculo diminuto.

Genera ``build/fotos/manifiesto.tsv`` con la correspondencia
``ruta original -> ruta procesada -> tipo`` que lee el filtro Lua.

Uso:  python3 automatizacion/preparar_imagenes.py [--hoja-contactos]
"""

import argparse
import os
import sys
import unicodedata

from PIL import Image, ImageOps

try:
    import cv2
    import numpy as np
except Exception:  # OpenCV es opcional
    cv2 = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETAS = ["comp", "int"]
SALIDA = os.path.join(RAIZ, "build", "fotos")
LADO = 300  # px; el círculo mide 19 mm, así que esto equivale a ~400 ppp
BANDA = (1000, 500)  # px; fotos de grupo a lo ancho de la caja (88 mm ≈ 290 ppp)
MODELO = os.path.join(RAIZ, "automatizacion", "modelos",
                      "face_detection_yunet_2023mar.onnx")
EXTENSIONES = {".jpg", ".jpeg", ".jfif", ".png", ".tif", ".tiff", ".webp"}


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    out = []
    for c in texto:
        out.append(c if c.isalnum() else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def abrir_rgb(ruta):
    img = Image.open(ruta)
    img.seek(0)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        fondo = Image.new("RGB", img.size, (244, 241, 234))
        fondo.paste(img, mask=img.split()[-1])
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return img


_detector = None


def _crear_detector():
    """YuNet (preciso) si está el modelo; si no, la cascada Haar clásica."""
    global _detector
    if _detector is None:
        if hasattr(cv2, "FaceDetectorYN") and os.path.exists(MODELO):
            _detector = ("yunet", cv2.FaceDetectorYN.create(
                MODELO, "", (320, 320), 0.7, 0.3, 5000))
        else:
            _detector = ("haar", cv2.CascadeClassifier(os.path.join(
                cv2.data.haarcascades, "haarcascade_frontalface_alt2.xml")))
    return _detector


def detectar_rostros(img):
    """Devuelve una lista de rectángulos (x, y, w, h) en coordenadas de img."""
    if cv2 is None:
        return []
    tipo, det = _crear_detector()
    w, h = img.size
    escala = min(1.0, 900.0 / max(w, h))
    peq = img.resize((max(1, int(w * escala)), max(1, int(h * escala))))
    if tipo == "yunet":
        arr = cv2.cvtColor(np.array(peq), cv2.COLOR_RGB2BGR)
        det.setInputSize((arr.shape[1], arr.shape[0]))
        _, caras = det.detect(arr)
        caras = [] if caras is None else [c[:4] for c in caras]
    else:
        gris = cv2.equalizeHist(cv2.cvtColor(np.array(peq), cv2.COLOR_RGB2GRAY))
        lado_min = int(min(peq.size) * 0.07)
        caras = det.detectMultiScale(gris, 1.08, 6, minSize=(lado_min, lado_min))
    return [tuple(int(v / escala) for v in c) for c in caras]


def es_grupo(caras):
    """Tres o más caras de tamaño comparable: foto de conjunto."""
    if len(caras) < 3:
        return False
    areas = sorted((c[2] * c[3] for c in caras), reverse=True)
    return areas[2] > 0.3 * areas[0]


def caja_banda(img, caras):
    """Rectángulo 2:1 que contiene a todo el grupo."""
    w, h = img.size
    proporcion = BANDA[0] / BANDA[1]
    if w / h >= proporcion:
        bh, bw = h, h * proporcion
    else:
        bw, bh = w, w / proporcion
    x0 = min(c[0] for c in caras)
    y0 = min(c[1] for c in caras)
    x1 = max(c[0] + c[2] for c in caras)
    y1 = max(c[1] + c[3] for c in caras)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    izq = max(0, min(cx - bw / 2, w - bw))
    arriba = max(0, min(cy - bh * 0.42, h - bh))
    return (int(izq), int(arriba), int(izq + bw), int(arriba + bh))


def caja_recorte(img, caras):
    """Calcula el cuadrado (izq, arriba, lado) a recortar."""
    w, h = img.size
    m = min(w, h)
    if caras:
        caras = sorted(caras, key=lambda c: c[2] * c[3], reverse=True)
        principal = caras[0]
        # Si hay una cara claramente dominante, se usa sola; si no, se
        # consideran todas (foto de grupo).
        if len(caras) > 1 and caras[1][2] * caras[1][3] > 0.35 * principal[2] * principal[3]:
            x0 = min(c[0] for c in caras)
            y0 = min(c[1] for c in caras)
            x1 = max(c[0] + c[2] for c in caras)
            y1 = max(c[1] + c[3] for c in caras)
            lado = max((x1 - x0) * 1.35, (y1 - y0) * 2.4, 0.55 * m)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            cy_rel = 0.45
        else:
            x, y, cw, ch = principal
            lado = max(ch * 2.7, 0.45 * m)
            cx, cy = x + cw / 2, y + ch / 2
            cy_rel = 0.42  # la cara queda un poco por encima del centro
        lado = min(lado, m)
        izq = cx - lado / 2
        arriba = cy - lado * cy_rel
    else:
        lado = m
        izq = (w - lado) / 2
        # Retratos verticales: la cabeza suele estar en el tercio superior.
        arriba = (h - lado) * (0.22 if h > w else 0.5)
    izq = max(0, min(izq, w - lado))
    arriba = max(0, min(arriba, h - lado))
    return int(round(izq)), int(round(arriba)), int(round(lado))


def procesar(ruta_rel, forzar=False):
    """Devuelve (ruta procesada, tipo) con tipo 'circulo' o 'banda'."""
    origen = os.path.join(RAIZ, ruta_rel)
    carpeta, nombre = os.path.split(ruta_rel)
    base = os.path.join("build", "fotos", carpeta, slug(nombre))
    for tipo in ("circulo", "banda"):
        destino_rel = f"{base}.{tipo}.jpg"
        destino = os.path.join(RAIZ, destino_rel)
        if (
            not forzar
            and os.path.exists(destino)
            and os.path.getmtime(destino) >= os.path.getmtime(origen)
            and os.path.getmtime(destino) >= os.path.getmtime(__file__)
        ):
            return destino_rel, tipo
    img = abrir_rgb(origen)
    caras = detectar_rostros(img)
    if es_grupo(caras) and img.size[0] > img.size[1]:
        tipo = "banda"
        img = img.crop(caja_banda(img, caras)).resize(BANDA, Image.LANCZOS)
    else:
        tipo = "circulo"
        izq, arriba, lado = caja_recorte(img, caras)
        img = img.crop((izq, arriba, izq + lado, arriba + lado))
        img = img.resize((LADO, LADO), Image.LANCZOS)
    destino_rel = f"{base}.{tipo}.jpg"
    destino = os.path.join(RAIZ, destino_rel)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=82, optimize=True, progressive=True)
    return destino_rel, tipo


def hoja_contactos(rutas, archivo):
    t = 120
    cols = 12
    filas = (len(rutas) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * t, filas * t), "white")
    for i, r in enumerate(rutas):
        im = Image.open(os.path.join(RAIZ, r))
        im.thumbnail((t - 4, t - 4))
        hoja.paste(im, ((i % cols) * t + 2, (i // cols) * t + 2))
    hoja.save(archivo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--hoja-contactos", metavar="PNG")
    args = ap.parse_args()

    if cv2 is None:
        print("Aviso: OpenCV no está instalado; los recortes serán centrados.",
              file=sys.stderr)

    lineas = []
    procesadas = []
    for carpeta in CARPETAS:
        base = os.path.join(RAIZ, carpeta)
        for nombre in sorted(os.listdir(base)):
            if os.path.splitext(nombre)[1].lower() not in EXTENSIONES:
                continue
            ruta_rel = carpeta + "/" + nombre
            try:
                dest, tipo = procesar(ruta_rel, args.forzar)
            except Exception as e:  # imagen corrupta o formato raro
                print(f"Error con {ruta_rel}: {e}", file=sys.stderr)
                continue
            lineas.append(f"{ruta_rel}\t{dest}\t{tipo}")
            procesadas.append(dest)

    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, "manifiesto.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"{len(lineas)} imágenes listas en build/fotos/")

    if args.hoja_contactos:
        hoja_contactos(procesadas, args.hoja_contactos)


if __name__ == "__main__":
    main()
