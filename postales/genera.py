#!/usr/bin/env python3
"""Postales de los conciertos del 48.º FIMNME (1080 × 1350 px, PNG y PDF).

Lee postales/postales.yaml (datos editoriales de cada postal) y, de cada
concierto, lo que ya está en el Markdown: fecha, hora, sede, dirección,
obras, estrenos y logotipos (de sitio/_conciertos/<concierto>.html, que
genera sitio/genera.sh). Prepara los logotipos en blanco y los datos para
postales/postal.tex y lo compila con LuaLaTeX en dos pasadas: la primera mide
cuánto alto queda para las fotos (el contenido va pegado a la franja de los
logotipos) y la segunda las pone, recortadas a esa medida y centradas en los
rostros.

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
ANCHO_MM = 108
PX_MM = 20                            # fotos a 2× de la salida (10 px/mm)
DIAMETRO_RETRATO_MM = 20
# Logotipos de la franja: ninguno más grande que los de Cultura e INBAL de la
# pleca (el escudo y «Cultura» ocupan unos 22 × 7 mm; el del INBAL, 13 mm de
# ancho): a lo más 4,5 mm de alto y 13 mm de ancho, con un área parecida
# entre sí. La CNMO, en su versión horizontal.
ALTO_MAX_LOGO, ANCHO_MAX_LOGO, AREA_LOGO = 4.5, 13.0, 42.0
ANCHO_CNMO = 15.5


def tex(texto, juntos=()):
    """Texto (con *cursivas* de Markdown) → LaTeX. Los nombres de «juntos» no
    se parten entre renglones."""
    if not texto:
        return ""
    t = str(texto)
    for nombre in sorted(juntos, key=len, reverse=True):
        t = t.replace(nombre, nombre.replace(" ", "\u00a0"))
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")):
        t = t.replace(a, b)
    t = t.replace("\u00a0", "~")
    return re.sub(r"\*([^*]+)\*", r"\\emph{\1}", t)


def datos_concierto(etiqueta):
    """Encabezado de la página del concierto y los nombres de sus compositores."""
    archivo = RAIZ / "sitio/_conciertos" / f"{etiqueta}.html"
    if not archivo.exists():
        sys.exit(f"✗ No existe {archivo.relative_to(RAIZ)}: revise la etiqueta o ejecute sitio/genera.sh --contenido")
    cabecera, cuerpo = archivo.read_text(encoding="utf-8").split("\n---\n", 1)
    fm = json.loads(cabecera[4:])
    fm["compositores"] = [re.sub(r"<[^>]+>", "", c).strip()
                          for c in re.findall(r'<h4 class="compositor">(.*?)</h4>', cuerpo)]
    return fm


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
    """Logotipos y datos de la postal; las fotos se recortan al compilar."""
    etiqueta = postal["concierto"]
    fm = datos_concierto(etiqueta)
    carpeta = BUILD / etiqueta
    carpeta.mkdir(parents=True, exist_ok=True)

    # Logotipos: la CNMO y los del concierto, en blanco
    logos = [rf"\logocnmohorizontal{{{ANCHO_CNMO}mm}}{{white}}"]
    for k, l in enumerate(fm.get("logos", [])):
        destino = carpeta / f"logo-{k + 1}.png"
        w, h = logo_blanco(l["archivo"], destino)
        r = w / h
        alto = min((AREA_LOGO / r) ** 0.5, ALTO_MAX_LOGO, ANCHO_MAX_LOGO / r)
        logos.append(rf"\includegraphics[width={alto * r:.2f}mm, height={alto:.2f}mm]{{{destino.relative_to(RAIZ)}}}")

    nombres = fm.get("compositores", []) + [n for n, _ in postal.get("interpretes", [])]
    interpretes = "".join(rf"\interprete{{{tex(n)}}}{{{tex(p)}}}" for n, p in postal.get("interpretes", []))
    datos = {
        "fotos": "",
        "retratos": "",
        "antetitulo": tex(postal.get("antetitulo", "Concierto")),
        "titulo": tex(postal.get("titulo", fm["title"])),
        "subtitulo": tex(postal.get("subtitulo", "")),
        "interpretes": interpretes,
        "obras": tex(postal.get("obras") or fm.get("obras", ""), nombres),
        "estrenos": tex(postal.get("estrenos", fm.get("estrenos", ""))),
        "nota": tex(postal.get("nota", "")),
        "precio": tex(postal.get("precio", "")),
        "fecha": tex(postal.get("fecha", fecha_texto(fm))),
        "sede": tex(postal.get("sede", sede_texto(fm))),
        "direccion": tex(postal.get("direccion", direccion_texto(fm))),
        "logos": r"\hspace{5mm}".join(r"\raisebox{-0.5\height}{" + l + "}" for l in logos),
    }
    return etiqueta, carpeta, datos


def escribir_datos(carpeta, datos):
    archivo = carpeta / "datos.tex"
    archivo.write_text("".join(rf"\def\{k}{{{v}}}" + "\n" for k, v in datos.items()), encoding="utf-8")
    return archivo


def fotos_y_retratos(postal, carpeta, alto_mm):
    """Fotos a todo lo ancho (lado a lado) y retratos en círculo, para el alto medido."""
    focos = postal.get("foco", {}) or {}
    fotos = postal.get("fotos", []) or []
    tikz = []
    n = len(fotos)
    for k, ruta in enumerate(fotos):
        ancho_mm = ANCHO_MM / n
        img = abrir(ruta)
        recorte = recortar(img, round(ancho_mm * PX_MM), round(alto_mm * PX_MM), foco_de(img, focos.get(ruta)))
        destino = carpeta / f"foto-{k + 1}.jpg"
        recorte.save(destino, quality=90)
        tikz.append(rf"\node[anchor=north west, inner sep=0pt] at ($(fotoNO)+({k * ancho_mm:.3f}mm,0)$)"
                    rf" {{\includegraphics[width={ancho_mm:.3f}mm, height=\altofotos]{{{destino.relative_to(RAIZ)}}}}};")
        if k > 0:
            tikz.append(rf"\draw[portadabase, line width=1.2pt] ($(fotoNO)+({k * ancho_mm:.3f}mm,0)$) -- ($(fotoSO)+({k * ancho_mm:.3f}mm,0)$);")

    # Retratos en círculo, abajo a la derecha de las fotos, de izquierda a
    # derecha en el orden de la lista
    retratos = []
    lista_retratos = postal.get("retratos", []) or []
    diametro = min(DIAMETRO_RETRATO_MM, alto_mm - 6)
    r = diametro / 2
    for k, ruta in enumerate(lista_retratos):
        img = abrir(ruta)
        lado = round(diametro * PX_MM)
        recorte = recortar(img, lado, lado, foco_de(img, focos.get(ruta)))
        destino = carpeta / f"retrato-{k + 1}.jpg"
        recorte.save(destino, quality=90)
        x = ANCHO_MM - 9 - r - (len(lista_retratos) - 1 - k) * (diametro + 3)
        centro = rf"($(fotoSO)+({x:.2f}mm,{r + 3:.2f}mm)$)"
        retratos.append(
            rf"\begin{{scope}}\clip {centro} circle ({r:.2f}mm);"
            rf"\node[inner sep=0pt] at {centro} {{\includegraphics[width={diametro:.2f}mm]{{{destino.relative_to(RAIZ)}}}}};\end{{scope}}"
            rf"\draw[portadacaja, line width=1.1pt] {centro} circle ({r:.2f}mm);")
    return "\n".join(tikz), "\n".join(retratos)


def lualatex(carpeta, nombre, datos, medir=False):
    previo = r"\def\medir{}" if medir else ""
    r = subprocess.run(
        ["lualatex", "--interaction=nonstopmode", "--halt-on-error", f"--jobname={nombre}",
         f"--output-directory={carpeta.relative_to(RAIZ)}",
         rf"{previo}\def\datos{{{datos.relative_to(RAIZ)}}}\input{{postales/postal.tex}}"],
        cwd=RAIZ, capture_output=True, text=True)
    registro = (carpeta / f"{nombre}.log").read_text(errors="replace")
    if r.returncode != 0:
        print(f"✗ Error de LuaLaTeX en {nombre}; últimas líneas del registro:")
        print("\n".join(registro.splitlines()[-25:]))
        sys.exit(1)
    return registro


def compilar(postal, etiqueta, carpeta, datos):
    nombre = f"fimnme2026-postal-{etiqueta}"
    # 1.ª pasada: sin fotos, para medir su alto (y las posiciones de TikZ)
    registro = lualatex(carpeta, nombre, escribir_datos(carpeta, datos), medir=True)
    alto_pt = float(re.search(r"POSTAL-ALTOFOTOS=([\d.]+)pt", registro).group(1))
    alto_mm = alto_pt * 25.4 / 72.27
    if alto_mm < 24:
        print(f"⚠ {etiqueta}: el contenido deja solo {alto_mm:.0f} mm para las fotos; conviene acortarlo")
    # 2.ª pasada: con las fotos recortadas a esa medida
    datos["fotos"], datos["retratos"] = fotos_y_retratos(postal, carpeta, alto_mm)
    lualatex(carpeta, nombre, escribir_datos(carpeta, datos))
    pdf = SALIDA / f"{nombre}.pdf"
    shutil.copyfile(carpeta / f"{nombre}.pdf", pdf)
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1080", "-scale-to-y", "1350", "-singlefile",
                    str(pdf), str(SALIDA / nombre)], check=True)
    print(f"✓ {SALIDA.relative_to(RAIZ)}/{nombre}.png y .pdf (fotos de {alto_mm:.0f} mm de alto)")


def main():
    lista = yaml.safe_load((SALIDA / "postales.yaml").read_text(encoding="utf-8"))["postales"]
    pedidas = set(sys.argv[1:])
    for postal in lista:
        if pedidas and postal["concierto"] not in pedidas:
            continue
        compilar(postal, *preparar(postal))


if __name__ == "__main__":
    main()
