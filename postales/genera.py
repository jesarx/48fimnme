#!/usr/bin/env python3
"""Postales de los conciertos del 48.º FIMNME (1080 × 1350 px, PNG y PDF).

Lee postales/postales.yaml (datos editoriales de cada postal) y, de cada
concierto, lo que ya está en el Markdown: fecha, hora, sede, dirección,
obras, estrenos y logotipos (de sitio/_conciertos/<concierto>.html, que
genera sitio/genera.sh). Prepara las fotos (recortadas al encuadre, centradas
en los rostros), los logotipos en blanco y los datos para postales/postal.tex,
y lo compila con LuaLaTeX.

    python3 postales/genera.py                 todas las postales
    python3 postales/genera.py <concierto>…    solo esas

Salida: postales/fimnme2026-postal-<concierto>.png y .pdf
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "automatizacion"))
try:   # detección de rostros del Programa general (OpenCV es opcional)
    from preparar_imagenes import detectar_rostros
except Exception:   # noqa: BLE001
    def detectar_rostros(_img):
        return []

BUILD = RAIZ / "build/postales"
SALIDA = RAIZ / "postales"
ANCHO_MM, ALTO_FOTOS_MM = 108, 42     # como en postal.tex (\altofotos)
PX_MM = 20                            # fotos a 2× de la salida (10 px/mm)
DIAMETRO_RETRATO_MM = 21


def tex(texto):
    """Texto (con *cursivas* de Markdown) → LaTeX."""
    if not texto:
        return ""
    t = str(texto)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")):
        t = t.replace(a, b)
    return re.sub(r"\*([^*]+)\*", r"\\emph{\1}", t)


def datos_concierto(etiqueta):
    archivo = RAIZ / "sitio/_conciertos" / f"{etiqueta}.html"
    if not archivo.exists():
        sys.exit(f"✗ No existe {archivo.relative_to(RAIZ)}: revise la etiqueta o ejecute sitio/genera.sh --contenido")
    cabecera = archivo.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    return json.loads(cabecera[4:])


def abrir(ruta):
    img = Image.open(RAIZ / ruta)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def foco_de(img, foco):
    """Punto de interés (x, y) en fracciones: el indicado o el de los rostros."""
    if foco:
        return foco
    caras = detectar_rostros(img)
    if caras:
        x, y, w, h = max(caras, key=lambda c: c[2] * c[3])
        return ((x + w / 2) / img.width, (y + h / 2) / img.height)
    return (0.5, 0.4)


def recortar(img, ancho, alto, foco):
    """Recorta img a la proporción ancho:alto alrededor de foco y la escala."""
    fx, fy = foco
    proporcion = ancho / alto
    if img.width / img.height > proporcion:     # sobra ancho
        w, h = int(img.height * proporcion), img.height
    else:                                       # sobra alto
        w, h = img.width, int(img.width / proporcion)
    # el rostro, a un tercio desde arriba (no al centro)
    x0 = min(max(0, int(fx * img.width - w / 2)), img.width - w)
    y0 = min(max(0, int(fy * img.height - h * 0.4)), img.height - h)
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((ancho, alto), Image.LANCZOS)


def logo_blanco(archivo, destino):
    """Logotipo de build/logos (un solo color con transparencia) en blanco."""
    alfa = Image.open(RAIZ / "build/logos" / archivo).convert("RGBA").getchannel("A")
    blanco = Image.new("RGBA", alfa.size, (255, 255, 255, 0))
    blanco.putalpha(alfa)
    blanco.save(destino, optimize=True)
    return alfa.size


def sede_texto(fm):
    """«Sala Principal, Palacio de Bellas Artes» → «Palacio de Bellas Artes, Sala Principal»."""
    lugar = fm["fechas"][0]["lugar"] or fm["lugares"][0]
    sede = fm["fechas"][0]["sede_nombre"]
    if sede and lugar.endswith(", " + sede):
        return sede + ", " + lugar[: -len(sede) - 2]
    return lugar


def direccion_texto(fm):
    return re.sub(r",\s*Ciudad de México$", "", fm["fechas"][0]["direccion"] or "")


def fecha_texto(fm):
    f = fm["fechas"][0]
    return f"{f['dia']} de 2026, {f['hora']} h"


def preparar(postal):
    etiqueta = postal["concierto"]
    fm = datos_concierto(etiqueta)
    carpeta = BUILD / etiqueta
    carpeta.mkdir(parents=True, exist_ok=True)
    focos = postal.get("foco", {}) or {}

    # Fotos a todo lo ancho (una o varias, lado a lado)
    fotos = postal.get("fotos", []) or []
    tikz = []
    n = len(fotos)
    for k, ruta in enumerate(fotos):
        ancho_mm = ANCHO_MM / n
        img = abrir(ruta)
        recorte = recortar(img, int(ancho_mm * PX_MM), ALTO_FOTOS_MM * PX_MM, foco_de(img, focos.get(ruta)))
        destino = carpeta / f"foto-{k + 1}.jpg"
        recorte.save(destino, quality=90)
        tikz.append(rf"\node[anchor=north west, inner sep=0pt] at ($(current page.north west)+({k * ancho_mm:.3f}mm,0)$)"
                    rf" {{\includegraphics[width={ancho_mm:.3f}mm, height={ALTO_FOTOS_MM}mm]{{{destino.relative_to(RAIZ)}}}}};")
        if k > 0:
            tikz.append(rf"\draw[portadabase, line width=1.2pt] ($(current page.north west)+({k * ancho_mm:.3f}mm,0)$)"
                        rf" -- ++(0,-{ALTO_FOTOS_MM}mm);")

    # Retratos en círculo, abajo a la derecha de las fotos
    retratos = []
    lista_retratos = postal.get("retratos", []) or []
    for k, ruta in enumerate(lista_retratos):
        img = abrir(ruta)
        lado = DIAMETRO_RETRATO_MM * PX_MM
        recorte = recortar(img, lado, lado, foco_de(img, focos.get(ruta)))
        destino = carpeta / f"retrato-{k + 1}.jpg"
        recorte.save(destino, quality=90)
        r = DIAMETRO_RETRATO_MM / 2
        # en el orden de la lista, de izquierda a derecha, pegados al margen derecho
        x = ANCHO_MM - 9 - r - (len(lista_retratos) - 1 - k) * (DIAMETRO_RETRATO_MM + 3)
        retratos.append(
            rf"\begin{{scope}}\clip ($(current page.north west)+({x:.2f}mm,-30mm)$) circle ({r}mm);"
            rf"\node[inner sep=0pt] at ($(current page.north west)+({x:.2f}mm,-30mm)$)"
            rf" {{\includegraphics[width={DIAMETRO_RETRATO_MM}mm]{{{destino.relative_to(RAIZ)}}}}};\end{{scope}}"
            rf"\draw[portadacaja, line width=1.1pt] ($(current page.north west)+({x:.2f}mm,-30mm)$) circle ({r}mm);")

    # Logotipos: la CNMO y los del concierto, en blanco
    logos = [r"\logocnmo{11mm}{white}"]
    for k, l in enumerate(fm.get("logos", [])):
        destino = carpeta / f"logo-{k + 1}.png"
        w, h = logo_blanco(l["archivo"], destino)
        alto = 5.6 if w / h < 3 else 4.2
        ancho = min(alto * w / h, 22)
        logos.append(rf"\includegraphics[width={ancho:.2f}mm, height={ancho * h / w:.2f}mm]{{{destino.relative_to(RAIZ)}}}")

    interpretes = "".join(rf"\interprete{{{tex(n)}}}{{{tex(p)}}}" for n, p in postal.get("interpretes", []))
    datos = {
        "fotos": "\n".join(tikz),
        "retratos": "\n".join(retratos),
        "antetitulo": tex(postal.get("antetitulo", "Concierto")),
        "titulo": tex(postal.get("titulo", fm["title"])),
        "subtitulo": tex(postal.get("subtitulo", "")),
        "interpretes": interpretes,
        "obras": tex(postal.get("obras") or fm.get("obras", "")),
        "estrenos": tex(postal.get("estrenos", fm.get("estrenos", ""))),
        "nota": tex(postal.get("nota", "")),
        "precio": tex(postal.get("precio", "")),
        "fecha": tex(postal.get("fecha", fecha_texto(fm))),
        "sede": tex(postal.get("sede", sede_texto(fm))),
        "direccion": tex(postal.get("direccion", direccion_texto(fm))),
        "logos": r"\hspace{6mm}".join(r"\raisebox{-0.5\height}{" + l + "}" for l in logos),
    }
    archivo = carpeta / "datos.tex"
    archivo.write_text("".join(rf"\def\{k}{{{v}}}" + "\n" for k, v in datos.items()), encoding="utf-8")
    return etiqueta, archivo


def compilar(etiqueta, datos):
    carpeta = BUILD / etiqueta
    nombre = f"fimnme2026-postal-{etiqueta}"
    for _ in range(2):   # dos pasadas: posiciones de TikZ (remember picture)
        r = subprocess.run(
            ["lualatex", "--interaction=nonstopmode", "--halt-on-error", f"--jobname={nombre}",
             f"--output-directory={carpeta.relative_to(RAIZ)}",
             rf"\def\datos{{{datos.relative_to(RAIZ)}}}\input{{postales/postal.tex}}"],
            cwd=RAIZ, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ Error de LuaLaTeX en {etiqueta}; últimas líneas del registro:")
            print("\n".join((carpeta / f"{nombre}.log").read_text(errors="replace").splitlines()[-25:]))
            sys.exit(1)
    pdf = SALIDA / f"{nombre}.pdf"
    shutil.copyfile(carpeta / f"{nombre}.pdf", pdf)
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1080", "-scale-to-y", "1350", "-singlefile",
                    str(pdf), str(SALIDA / nombre)], check=True)
    print(f"✓ {SALIDA.relative_to(RAIZ)}/{nombre}.png y .pdf")


def main():
    lista = yaml.safe_load((SALIDA / "postales.yaml").read_text(encoding="utf-8"))["postales"]
    pedidas = set(sys.argv[1:])
    for postal in lista:
        if pedidas and postal["concierto"] not in pedidas:
            continue
        compilar(*preparar(postal))


if __name__ == "__main__":
    main()
