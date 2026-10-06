#!/usr/bin/env python3
"""Prepara los logotipos de los conciertos para el Programa General.

Los logotipos se declaran en el Markdown, al final de cada concierto:

    ::: logos
    ![](<logos/logos OSN/OSN-1.png>)
    ![](<logos/logos OJUEM/02.CintilloLogos_OJUEM.ai>){partir=si}
    :::

Atributos opcionales de cada imagen:

* ``pagina=3``: página de un PDF/AI con varias versiones del logotipo;
* ``recorte="x0 y0 x1 y1"``: parte de la página o imagen que se usa, en
  fracciones de su ancho y alto (0 a 1);
* ``partir=si``: la imagen es un cintillo con varios logotipos; se separa en
  logotipos individuales (por los espacios en blanco entre ellos) para que
  cada uno se componga del mismo tamaño que los demás. Un número en lugar
  de «si» (p. ej. ``partir=0.1``) fija el hueco mínimo, en fracción de la
  altura (0.22 por omisión). Si el resultado no convence, es más seguro dar
  un ``recorte`` para cada logotipo del cintillo;
* ``realce=0.4``: oscurece los tonos claros de un logotipo que, en un solo
  color, queda demasiado pálido (p. ej. uno dorado); 0.75 por omisión.

Para cada logotipo:

* abre PNG/JPG/TIFF y también PDF, AI, PS (si son PDF por dentro) y SVG;
* lo convierte a un solo color, el verde oscuro del diseño, conservando los
  matices como transparencia (funciona igual con logotipos negros, de color,
  blancos sobre transparente o claros sobre un fondo oscuro);
* recorta los márgenes vacíos y lo guarda en ``build/logos/`` como PNG con
  transparencia, a resolución suficiente para que no se pixele.

Genera ``build/logos/manifiesto.tsv`` (clave, archivo, ancho, alto) que lee
el filtro Lua para componer los logotipos con un tamaño visual parejo.

Requisitos: Pillow y pandoc. Para PDF/AI/PS/SVG, PyMuPDF
(``pip install pymupdf``); sin él, los PDF se abren con ``pdftoppm``
(poppler) y los SVG con ``rsvg-convert``.

Uso:  python3 automatizacion/preparar_logos.py
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

from PIL import Image, ImageChops, ImageOps, ImageStat

try:
    import pymupdf
except Exception:  # PyMuPDF es opcional
    try:
        import fitz as pymupdf
    except Exception:
        pymupdf = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKDOWN = os.path.join(RAIZ, "fimnme2026-programa.md")
SALIDA = os.path.join(RAIZ, "build", "logos")
COLOR = (0x17, 0x2B, 0x20)   # verdeoscuro de la plantilla
ALTO_MAX = 320               # px; un logotipo mide ~4–9 mm de alto: >900 ppp
ANCHO_MAX = 2000
ATRIBUTOS = ("pagina", "partir", "realce", "recorte")


# ---------------------------------------------------------------- Markdown --
def logos_del_markdown():
    """Imágenes dentro de los bloques «::: logos», en orden."""
    salida = subprocess.run(["pandoc", MARKDOWN, "-f", "markdown", "-t", "json"],
                            capture_output=True, check=True).stdout
    doc = json.loads(salida)
    encontrados = []

    def recorrer(nodo, en_logos):
        if isinstance(nodo, dict):
            t = nodo.get("t")
            if t == "Div":
                (ident, clases, kvs), bloques = nodo["c"]
                for b in bloques:
                    recorrer(b, en_logos or "logos" in clases)
                return
            if t == "Image" and en_logos:
                (ident, clases, kvs), _alt, (src, _titulo) = nodo["c"]
                encontrados.append((src, dict(kvs)))
                return
            for v in nodo.values():
                recorrer(v, en_logos)
        elif isinstance(nodo, list):
            for v in nodo:
                recorrer(v, en_logos)

    recorrer(doc["blocks"], False)
    return encontrados


def clave(src, atributos):
    """Misma clave que construye el filtro Lua."""
    partes = [f"{k}={atributos[k]}" for k in sorted(atributos) if k in ATRIBUTOS]
    return src + "|" + ";".join(partes)


# ------------------------------------------------------------------ Lectura --
def es_pdf(ruta):
    with open(ruta, "rb") as f:
        return f.read(5) == b"%PDF-"


def renderizar_vectorial(ruta, pagina, recorte, svg):
    """Página de un PDF/AI/PS-PDF o un SVG → imagen RGBA."""
    x0, y0, x1, y1 = recorte
    if pymupdf is not None:
        with open(ruta, "rb") as f:
            datos = f.read()
        doc = pymupdf.open(stream=datos, filetype="svg" if svg else "pdf")
        pag = doc[pagina - 1]
        r = pag.rect
        clip = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height,
                            r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        # resolución tal que la parte usada mida ~2400 px por su lado mayor
        zoom = 2400 / max(clip.width, clip.height)
        pix = pag.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=True)
        modo = "RGBA" if pix.alpha else "RGB"
        return Image.frombytes(modo, (pix.width, pix.height), pix.samples).convert("RGBA"), False
    # Sin PyMuPDF: herramientas externas (la imagen sale completa y se recorta luego)
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "pagina.png")
        if svg:
            if not shutil.which("rsvg-convert"):
                sys.exit("Para logotipos SVG hace falta PyMuPDF o rsvg-convert.")
            subprocess.run(["rsvg-convert", "-w", "2400", "-o", destino, ruta], check=True)
        else:
            if not shutil.which("pdftoppm"):
                sys.exit("Para logotipos PDF/AI hace falta PyMuPDF o pdftoppm (poppler).")
            subprocess.run(["pdftoppm", "-png", "-r", "400", "-f", str(pagina), "-l", str(pagina),
                            "-singlefile", ruta, destino[:-4]], check=True)
        return Image.open(destino).convert("RGBA"), True


def cargar(ruta, atributos):
    pagina = int(atributos.get("pagina", "1"))
    recorte = [float(v) for v in atributos.get("recorte", "0 0 1 1").split()]
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".svg" or es_pdf(ruta):
        img, falta_recorte = renderizar_vectorial(ruta, pagina, recorte, ext == ".svg")
    else:
        img = ImageOps.exif_transpose(Image.open(ruta))
        if img.mode == "CMYK":
            img = img.convert("RGB")
        img = img.convert("RGBA")
        falta_recorte = True
    if falta_recorte and recorte != [0, 0, 1, 1]:
        w, h = img.size
        img = img.crop((round(recorte[0] * w), round(recorte[1] * h),
                        round(recorte[2] * w), round(recorte[3] * h)))
    return img


# ------------------------------------------------------------ Un solo color --
def tabla(fn):
    return [max(0, min(255, round(fn(v)))) for v in range(256)]


def tinta(img, realce=0.75):
    """Imagen RGBA → canal de «tinta» (0 = vacío, 255 = color pleno).

    Los tonos intermedios se oscurecen un poco (gamma 0.75) para que las
    partes de color claro de un logotipo (dorado, amarillo...) sigan viéndose.
    """
    ink = tinta_lineal(img)
    return ink.point(tabla(lambda v: 255 * (v / 255) ** realce))


def tinta_lineal(img):
    alfa = img.getchannel("A")
    blanco = Image.new("RGBA", img.size, (255, 255, 255, 255))
    lum = Image.alpha_composite(blanco, img).convert("L")
    w, h = img.size
    transparente = ImageStat.Stat(alfa.point(lambda v: 255 if v < 128 else 0)).mean[0] / 255

    if transparente > 0.15:
        # Logotipo sobre fondo transparente
        opaco = alfa.point(lambda v: 255 if v >= 128 else 0)
        claro = ImageStat.Stat(lum, mask=opaco).mean[0] if opaco.getbbox() else 0
        if claro > 170:
            return alfa                      # logotipo blanco o muy claro
        oscuridad = lum.point(tabla(lambda v: (255 - v) * 1.35))
        return ImageChops.multiply(alfa, oscuridad)

    # Imagen opaca: el fondo es el tono que predomina en el borde
    borde = Image.new("L", (w, h), 0)
    m = max(2, min(w, h) // 40)
    for caja in ((0, 0, w, m), (0, h - m, w, h), (0, 0, m, h), (w - m, 0, w, h)):
        borde.paste(255, caja)
    fondo = ImageStat.Stat(lum, mask=borde).median[0]
    hist = lum.histogram()
    total = sum(hist)

    def percentil(p):
        acum = 0
        for v, n in enumerate(hist):
            acum += n
            if acum >= p * total:
                return v
        return 255

    if fondo >= 128:                         # fondo claro, logotipo oscuro
        tope = min(percentil(0.01), fondo - 40)
        ink = lum.point(tabla(lambda v: (fondo - 8 - v) / max(1, fondo - 8 - tope) * 255))
    else:                                    # fondo oscuro, logotipo claro
        tope = max(percentil(0.99), fondo + 40)
        ink = lum.point(tabla(lambda v: (v - fondo - 8) / max(1, tope - fondo - 8) * 255))
    return ImageChops.multiply(ink, alfa)


def recortar(ink, umbral=24):
    caja = ink.point(lambda v: 255 if v > umbral else 0).getbbox()
    return ink.crop(caja) if caja else None


def partir(ink, separacion=0.22):
    """Separa un cintillo en logotipos por las columnas vacías."""
    w, h = ink.size
    columnas = ink.point(lambda v: 255 if v > 24 else 0).resize((w, 1), Image.BOX)
    llenas = [v > 0 for v in columnas.tobytes()]
    hueco = max(4, int(separacion * h))
    piezas, inicio, vacias = [], None, 0
    for x, llena in enumerate(llenas + [False] * (hueco + 1)):
        if llena:
            if inicio is None:
                inicio = x
            vacias = 0
            fin = x
        elif inicio is not None:
            vacias += 1
            if vacias >= hueco:
                piezas.append((inicio, fin + 1))
                inicio, vacias = None, 0
    salida = []
    for a, b in piezas:
        pieza = recortar(ink.crop((a, 0, b, h)))
        # se descartan filetes separadores y motas
        if pieza and pieza.size[0] >= 0.12 * h and pieza.size[1] >= 0.2 * h:
            salida.append(pieza)
    return salida


def guardar(ink, ruta):
    w, h = ink.size
    escala = min(1.0, ALTO_MAX / h, ANCHO_MAX / w)
    if escala < 1:
        ink = ink.resize((max(1, round(w * escala)), max(1, round(h * escala))), Image.LANCZOS)
    img = Image.new("RGBA", ink.size, COLOR + (0,))
    img.putalpha(ink)
    img.save(ruta, optimize=True)
    return ink.size


# --------------------------------------------------------------------- Main --
def main():
    os.makedirs(SALIDA, exist_ok=True)
    lineas, vistos = [], set()
    for src, atributos in logos_del_markdown():
        k = clave(src, atributos)
        if k in vistos:
            continue
        vistos.add(k)
        ruta = os.path.join(RAIZ, src)
        if not os.path.exists(ruta):
            ruta = os.path.join(RAIZ, urllib.parse.unquote(src))
        if not os.path.exists(ruta):
            print(f"Logotipo no encontrado: {src}", file=sys.stderr)
            continue
        ink = recortar(tinta(cargar(ruta, atributos), float(atributos.get("realce", "0.75"))))
        if ink is None:
            print(f"Logotipo vacío: {src}", file=sys.stderr)
            continue
        modo = atributos.get("partir", "no")
        if modo in ("si", "sí"):
            piezas = partir(ink)
        elif modo.replace(".", "", 1).isdigit():
            piezas = partir(ink, float(modo))
        else:
            piezas = [ink]
        base = hashlib.md5(k.encode("utf-8")).hexdigest()[:10]
        for n, pieza in enumerate(piezas, 1):
            destino = os.path.join(SALIDA, f"{base}-{n}.png")
            w, h = guardar(pieza, destino)
            lineas.append(f"{k}\t{os.path.relpath(destino, RAIZ)}\t{w}\t{h}")
    with open(os.path.join(SALIDA, "manifiesto.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + ("\n" if lineas else ""))
    print(f"{len(lineas)} logotipos listos en build/logos/")


if __name__ == "__main__":
    main()
