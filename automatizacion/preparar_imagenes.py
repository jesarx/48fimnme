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

Todas las fotos se muestran en círculo; en las de conjunto el recorte abarca
lo más posible del grupo.

Genera ``build/fotos/manifiesto.tsv`` con la correspondencia
``ruta original -> ruta procesada`` que lee el filtro Lua.

Uso:  python3 automatizacion/preparar_imagenes.py [--hoja-contactos]
"""

import argparse
import os
import sys
import unicodedata

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import cv2
    import numpy as np
except Exception:  # OpenCV es opcional
    cv2 = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETAS = ["comp", "int"]
SALIDA = os.path.join(RAIZ, "build", "fotos")
LADO = 300  # px; el círculo mide 19 mm, así que esto equivale a ~400 ppp
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


def caja_recorte(img, caras):
    """Decide el recorte cuadrado.

    Devuelve (caja, lado) con caja = (izq, arriba, der, abajo). Si los rostros
    de una foto de grupo no caben en ningún cuadrado de la imagen, la caja es
    más estrecha que el cuadrado (``der - izq`` o ``abajo - arriba`` < lado):
    entonces la foto se coloca entera y se rellena con un fondo difuminado.
    """
    w, h = img.size
    m = min(w, h)
    if caras:
        caras = sorted(caras, key=lambda c: c[2] * c[3], reverse=True)
        principal = caras[0]
        # Si hay una cara claramente dominante, se usa sola; si no, se
        # consideran todas las de tamaño comparable (foto de grupo).
        grupo = [c for c in caras if c[2] * c[3] > 0.12 * principal[2] * principal[3]]
        if len(grupo) > 1:
            x0 = min(c[0] for c in grupo)
            y0 = min(c[1] for c in grupo)
            x1 = max(c[0] + c[2] for c in grupo)
            y1 = max(c[1] + c[3] for c in grupo)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            necesario = max((x1 - x0) * 1.3, (y1 - y0) * 2.2)
            if necesario > m:
                lado = min(necesario, max(w, h))
                if w >= h:
                    izq = max(0, min(cx - lado / 2, w - lado))
                    return (int(izq), 0, int(izq + lado), h), int(lado)
                arriba = max(0, min(cy - lado / 2, h - lado))
                return (0, int(arriba), w, int(arriba + lado)), int(lado)
            lado = m
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
    izq = int(round(max(0, min(izq, w - lado))))
    arriba = int(round(max(0, min(arriba, h - lado))))
    lado = int(round(lado))
    return (izq, arriba, izq + lado, arriba + lado), lado


def componer_cuadrado(img, caja, lado):
    """Recorta; si la caja no es cuadrada, rellena con la foto difuminada."""
    recorte = img.crop(caja)
    rw, rh = recorte.size
    if rw == rh:
        return recorte
    escala = lado / min(rw, rh)
    fondo = recorte.resize((max(lado, int(rw * escala)), max(lado, int(rh * escala))), Image.LANCZOS)
    fx, fy = (fondo.width - lado) // 2, (fondo.height - lado) // 2
    fondo = fondo.crop((fx, fy, fx + lado, fy + lado))
    fondo = fondo.filter(ImageFilter.GaussianBlur(lado / 25))
    fondo = ImageEnhance.Brightness(fondo).enhance(0.8)
    fondo.paste(recorte, ((lado - rw) // 2, (lado - rh) // 2))
    return fondo


def procesar(ruta_rel, forzar=False):
    """Recorta la foto en cuadrado (para el círculo) y devuelve la ruta procesada."""
    origen = os.path.join(RAIZ, ruta_rel)
    carpeta, nombre = os.path.split(ruta_rel)
    destino_rel = os.path.join("build", "fotos", carpeta, slug(nombre) + ".jpg")
    destino = os.path.join(RAIZ, destino_rel)
    if (
        not forzar
        and os.path.exists(destino)
        and os.path.getmtime(destino) >= os.path.getmtime(origen)
        and os.path.getmtime(destino) >= os.path.getmtime(__file__)
    ):
        return destino_rel
    img = abrir_rgb(origen)
    caja, lado = caja_recorte(img, detectar_rostros(img))
    img = componer_cuadrado(img, caja, lado)
    img = img.resize((LADO, LADO), Image.LANCZOS)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=82, optimize=True, progressive=True)
    return destino_rel


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
                dest = procesar(ruta_rel, args.forzar)
            except Exception as e:  # imagen corrupta o formato raro
                print(f"Error con {ruta_rel}: {e}", file=sys.stderr)
                continue
            lineas.append(f"{ruta_rel}\t{dest}")
            procesadas.append(dest)

    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, "manifiesto.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"{len(lineas)} imágenes listas en build/fotos/")

    if args.hoja_contactos:
        hoja_contactos(procesadas, args.hoja_contactos)


if __name__ == "__main__":
    main()
