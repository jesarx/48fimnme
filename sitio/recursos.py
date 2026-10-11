#!/usr/bin/env python3
"""Recursos del sitio web del 48.º FIMNME (sitio/genera.sh lo ejecuta).

Prepara, a partir de lo que ya usan el Programa general y la postal:

* sitio/assets/fotos/   fotos de las fichas: en comp/ e int/ (como en el
                        Markdown), el recorte en círculo del programa (los de
                        build/fotos, ligeros), y en completas/ cada foto del
                        Markdown entera (sin recortar), para verla en grande
* sitio/assets/logos/   logotipos de los conciertos (los de build/logos, ligeros)
* sitio/assets/img/     logo «48» y de la CNMO en SVG (de los trazos de la
                        plantilla; copia en _includes/generado), textura de la
                        partitura de Enríquez, ícono e imagen para compartir
* sitio/_data/abono.json      precios y sede del abono (los de postales/abono/abono.tex)
* sitio/_data/descargas.json  PDF del Programa general y del resumido
* sitio/descargas/            copias de esos archivos (los QR para descargarlos
                              los genera Jekyll al compilar: _plugins/qr.rb)
* sitio/postales/             la postal de cada evento en PNG (para descargar)
* sitio/assets/postales/      su vista previa, ligera (JPG de 540 × 675 px)
* sitio/_data/postales.json   las postales de cada evento (por su etiqueta)

Las fotos y logotipos que hacen falta los lista sitio/sitio.lua en
build/sitio/recursos.tsv.
"""

import json
import re
import shutil
import sys
from pathlib import Path

import yaml

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
SITIO = RAIZ / "sitio"
ASSETS = SITIO / "assets"
PLANTILLA = RAIZ / "automatizacion/plantilla"
FUENTES = RAIZ / "automatizacion/fuentes"

# colores de la portada (automatizacion/plantilla/fimnme.latex)
PORTADABASE = (0x4E, 0x5F, 0x44)
PORTADALUZ = (0x76, 0x8F, 0x68)
PORTADATEXTO = (0xE2, 0xE6, 0xDF)
PORTADALOGO = (0xC7, 0xD2, 0xC3)
PORTADACAJA = (0xA5, 0xB9, 0xA8)
VERDEOSCURO = (0x17, 0x2B, 0x20)


def limpiar_directorio(d, conservar):
    """Borra de d (y sus subcarpetas) lo que no esté en conservar (rutas relativas)."""
    d.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.rglob("*"), reverse=True):
        if f.is_file() and str(f.relative_to(d)) not in conservar:
            f.unlink()
        elif f.is_dir() and not any(f.iterdir()):
            f.rmdir()


def al_dia(destino, origen):
    return destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime


def foto_web(origen, destino, lado, calidad):
    """Imagen → JPEG de como máximo lado × lado px (transparencia sobre blanco)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    im = ImageOps.exif_transpose(Image.open(origen))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGB", im.size, (255, 255, 255))
        fondo.paste(im, mask=im.getchannel("A"))
        im = fondo
    im = im.convert("RGB")
    im.thumbnail((lado, lado), Image.LANCZOS)
    im.save(destino, "JPEG", quality=calidad, optimize=True, progressive=True)


def fotos_y_logos():
    lista = RAIZ / "build/sitio/recursos.tsv"
    fotos, completas, logos = {}, {}, {}
    for linea in lista.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        tipo, origen, nombre = linea.split("\t")
        {"foto": fotos, "completa": completas}.get(tipo, logos)[nombre] = RAIZ / origen
    limpiar_directorio(ASSETS / "fotos", set(fotos) | {f"completas/{n}" for n in completas})
    limpiar_directorio(ASSETS / "logos", logos)
    for nombre, origen in fotos.items():          # recortes: se muestran a 96-120 px
        destino = ASSETS / "fotos" / nombre
        if not al_dia(destino, origen):
            foto_web(origen, destino, 240, 82)
    for nombre, origen in completas.items():      # completas: para verlas en grande
        destino = ASSETS / "fotos/completas" / nombre
        if not al_dia(destino, origen):
            foto_web(origen, destino, 1000, 80)
    for nombre, origen in logos.items():
        destino = ASSETS / "logos" / nombre
        if al_dia(destino, origen):
            continue
        im = Image.open(origen).convert("RGBA")
        im.thumbnail((300, 84), Image.LANCZOS)    # se muestran a 28-42 px de alto
        im.save(destino, "PNG", optimize=True)
    print(f"  {len(fotos)} fotos (y sus versiones completas) y {len(logos)} logotipos")


# -----------------------------------------------------------------------------
# Logotipos vectoriales: los trazos PGF de la plantilla → SVG (color del texto)
# -----------------------------------------------------------------------------
PUNTO = r"\\pgfqpoint\{([-\d.]+)pt\}\{([-\d.]+)pt\}"


def svg_de_pgf(tex, destino, titulo):
    texto = tex.read_text(encoding="utf-8")
    ordenes = re.findall(r"\\pgfpath(moveto|lineto|curveto|close)((?:\{" + PUNTO + r"\})*)", texto)
    puntos = [(float(x), float(y)) for x, y in re.findall(PUNTO, texto)]
    xmin, xmax = min(p[0] for p in puntos), max(p[0] for p in puntos)
    ymin, ymax = min(p[1] for p in puntos), max(p[1] for p in puntos)
    letra = {"moveto": "M", "lineto": "L", "curveto": "C", "close": "Z"}
    d = []
    for orden, argumentos, *_ in ordenes:
        pts = re.findall(PUNTO, argumentos)
        coords = " ".join(f"{float(x) - xmin:.2f} {ymax - float(y):.2f}" for x, y in pts)
        d.append(letra[orden] + coords)
    ancho, alto = xmax - xmin, ymax - ymin
    destino.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho:.2f} {alto:.2f}" '
        f'width="{ancho:.1f}" height="{alto:.1f}" fill="currentColor" role="img">'
        f"<title>{titulo}</title><path d=\"{''.join(d)}\"/></svg>\n", encoding="utf-8")
    return ancho / alto


def logotipos_vectoriales():
    img = ASSETS / "img"
    img.mkdir(parents=True, exist_ok=True)
    svg_de_pgf(PLANTILLA / "logo-48.tex", img / "logo-48.svg", "48.º FIMNME")
    svg_de_pgf(PLANTILLA / "logo-cnmo.tex", img / "logo-cnmo.svg",
               "Coordinación Nacional de Música y Ópera")
    # también para insertarlos en la página (toman el color del texto)
    incluir = SITIO / "_includes/generado"
    incluir.mkdir(parents=True, exist_ok=True)
    for nombre in ("logo-48.svg", "logo-cnmo.svg"):
        shutil.copyfile(img / nombre, incluir / nombre)
    # ícono: el «48» sobre el verde de la portada
    logo = (img / "logo-48.svg").read_text(encoding="utf-8")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', logo).group(1).split()]
    lado = max(vb[2], vb[3]) * 1.3
    dx, dy = (lado - vb[2]) / 2, (lado - vb[3]) / 2
    trazo = re.search(r'<path d="([^"]+)"', logo).group(1)
    icono = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado:.2f} {lado:.2f}">'
             f'<rect width="{lado:.2f}" height="{lado:.2f}" rx="{lado * 0.16:.2f}" fill="#4E5F44"/>'
             f'<path transform="translate({dx:.2f} {dy:.2f})" fill="#E6AE78" d="{trazo}"/></svg>\n')
    (img / "icono.svg").write_text(icono, encoding="utf-8")
    pix = pymupdf.open(stream=icono.encode(), filetype="svg")[0].get_pixmap(
        matrix=pymupdf.Matrix(180 / lado, 180 / lado))
    pix.save(img / "icono-180.png")


def partitura():
    """La partitura de «1 x 4» de Enríquez (fondo de la portada), en trazos
    blancos sobre transparente."""
    pagina = pymupdf.open(PLANTILLA / "partitura-1x4.pdf")[0]
    z = 1400 / pagina.rect.width
    pix = pagina.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=True)
    im = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    im.save(ASSETS / "img/partitura.webp", "WEBP", quality=60, method=6)
    return im


def imagen_redes(textura):
    """Imagen para compartir (1200 × 630): como la portada del programa."""
    w, h = 1200, 630
    im = Image.new("RGB", (w, h), PORTADABASE)
    # luz radial desde la esquina superior derecha
    yy, xx = np.mgrid[0:h, 0:w]
    distancia = np.hypot(xx - (w - 40), yy - 30)
    mascara = Image.fromarray((np.clip(1 - distancia / 1050, 0, 1) * 255).astype("uint8"), "L")
    im.paste(Image.new("RGB", (w, h), PORTADALUZ), (0, 0), mascara)
    # partitura
    t = textura.resize((int(textura.width * h * 1.25 / textura.height), int(h * 1.25)))
    alfa = t.getchannel("A").point(lambda v: v * 0.12)
    t.putalpha(alfa)
    base = im.convert("RGBA")
    base.alpha_composite(t, (w - t.width + 180, -40))
    im = base.convert("RGB")
    # logotipo «48»
    logo_svg = (ASSETS / "img/logo-48.svg").read_text(encoding="utf-8").replace(
        'fill="currentColor"', 'fill="#E6AE78"')   # el logotipo, en su color
    doc = pymupdf.open(stream=logo_svg.encode(), filetype="svg")[0]
    alto_logo = 230
    pix = doc.get_pixmap(matrix=pymupdf.Matrix(alto_logo / doc.rect.height,
                                               alto_logo / doc.rect.height), alpha=True)
    logo = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    im.paste(logo, (80, 110), logo)
    d = ImageDraw.Draw(im)
    ligera = ImageFont.truetype(str(FUENTES / "NotoSans-Light.ttf"), 50)
    semi = ImageFont.truetype(str(FUENTES / "NotoSans-SemiBold.ttf"), 50)
    negra = ImageFont.truetype(str(FUENTES / "NotoSans-Bold.ttf"), 30)
    x = 80 + logo.width + 34
    d.text((x, 104), "FORO INTERNACIONAL", font=ligera, fill=PORTADATEXTO)
    d.text((x, 160), "DE MÚSICA NUEVA", font=ligera, fill=PORTADATEXTO)
    d.text((x, 216), "MANUEL ENRÍQUEZ", font=semi, fill=PORTADATEXTO)
    d.text((x, 292), "NOVIEMBRE 6 AL 21, 2026", font=negra, fill=PORTADATEXTO)
    caja = ImageFont.truetype(str(FUENTES / "NotoSans-Bold.ttf"), 26)
    texto = "CONCIERTOS · ACTIVIDADES ACADÉMICAS · COLOQUIO ENRÍQUEZ | 100"
    tw = d.textlength(texto, font=caja)
    d.rectangle((80, 450, 80 + tw + 48, 506), fill=PORTADACAJA)
    d.text((80 + 24, 459), texto, font=caja, fill=VERDEOSCURO)
    im.save(ASSETS / "img/compartir.jpg", "JPEG", quality=86, optimize=True, progressive=True)


# -----------------------------------------------------------------------------
# Abono y descargas
# -----------------------------------------------------------------------------
def abono():
    """Precios, sede y dirección del abono: los mismos de la postal."""
    tex = (RAIZ / "postales/abono/abono.tex").read_text(encoding="utf-8")

    def comando(nombre):
        m = re.search(r"\\newcommand\{\\" + nombre + r"\}\{(.*)\}\s*$", tex, flags=re.M)
        return m.group(1) if m else ""

    precios = [p.replace("\\$", "$").strip()
               for p in re.split(r"\\enspace·\\enspace", comando("precios")) if p.strip()]
    datos = {"precios": precios, "sede": comando("sede"), "direccion": comando("direccion")}
    (SITIO / "_data/abono.json").write_text(json.dumps(datos, ensure_ascii=False) + "\n",
                                           encoding="utf-8")


DESCARGAS = [
    ("programa", RAIZ / "fimnme2026-programa.pdf", "Programa general",
     "Programa completo: obras, semblanzas y notas al programa"),
    ("resumen", RAIZ / "resumen/fimnme2026-resumen.pdf", "Programa resumido",
     "Todas las fechas en pocas páginas, para imprimir o consultar rápido"),
]


def descargas():
    destino = SITIO / "descargas"
    destino.mkdir(exist_ok=True)
    lista = []
    for clave, origen, titulo, descripcion in DESCARGAS:
        if not origen.exists():
            print(f"  Aviso: falta {origen.relative_to(RAIZ)}")
            continue
        copia = destino / origen.name
        if not copia.exists() or copia.read_bytes() != origen.read_bytes():
            shutil.copyfile(origen, copia)
        kb = origen.stat().st_size / 1024
        peso = f"{kb / 1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        detalle = peso
        if origen.suffix == ".pdf":
            detalle = f"PDF · {len(pymupdf.open(origen))} páginas · {peso}"
        else:
            with Image.open(origen) as im:
                detalle = f"{origen.suffix[1:].upper()} · {im.width} × {im.height} px · {peso}"
        lista.append({"id": clave, "archivo": origen.name, "titulo": titulo,
                      "descripcion": descripcion, "detalle": detalle})
    limpiar_directorio(destino, {d["archivo"] for d in lista})
    (SITIO / "_data/descargas.json").write_text(json.dumps(lista, ensure_ascii=False) + "\n",
                                               encoding="utf-8")


# -----------------------------------------------------------------------------
# Postales de los eventos (las que genera postales/genera.py)
# -----------------------------------------------------------------------------
LADO_PREVIA = (540, 675)


def postales():
    """La postal de cada evento: el JPG para descargarla (1080 × 1350 px; pesa
    mucho menos que el PNG) y una vista previa ligera. En postales.json, por la
    etiqueta del evento, la lista de sus postales (dos en un concierto con dos
    funciones, cada una con su fecha)."""
    sys.path.insert(0, str(RAIZ / "postales"))
    import genera   # noqa: E402  (nombre de cada postal, el mismo que al generarlas)
    lista = yaml.safe_load((RAIZ / "postales/postales.yaml").read_text(encoding="utf-8"))["postales"]
    destino, previas = SITIO / "postales", ASSETS / "postales"
    destino.mkdir(exist_ok=True)
    previas.mkdir(exist_ok=True)
    datos, archivos, jpgs = {}, set(), set()
    for postal in lista:
        nombre = genera.nombre_salida(postal)
        jpg = RAIZ / "postales/jpg" / f"fimnme2026-postal-{nombre}.jpg"
        if not jpg.exists():
            print(f"  Aviso: falta {jpg.relative_to(RAIZ)} (python3 postales/genera.py)")
            continue
        copia = destino / jpg.name
        if not copia.exists() or copia.read_bytes() != jpg.read_bytes():
            shutil.copyfile(jpg, copia)
        previa = previas / f"{nombre}.jpg"
        if not al_dia(previa, jpg):
            with Image.open(jpg) as im:
                im.convert("RGB").resize(LADO_PREVIA, Image.LANCZOS).save(
                    previa, "JPEG", quality=84, optimize=True, progressive=True)
        fecha = ""
        if "funcion" in postal:
            f = genera.datos_evento(postal["evento"])["fechas"][postal["funcion"] - 1]
            fecha = f"{f['corto']} · {f['hora']} h"
        datos.setdefault(postal["evento"], []).append(
            {"archivo": jpg.name, "previa": previa.name, "fecha": fecha,
             "kb": round(jpg.stat().st_size / 1024)})
        archivos.add(jpg.name)
        jpgs.add(previa.name)
    limpiar_directorio(destino, archivos)
    limpiar_directorio(previas, jpgs)
    (SITIO / "_data/postales.json").write_text(json.dumps(datos, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
    print(f"  {len(archivos)} postales")


def main():
    fotos_y_logos()
    logotipos_vectoriales()
    textura = partitura()
    imagen_redes(textura)
    abono()
    descargas()
    postales()


if __name__ == "__main__":
    main()
