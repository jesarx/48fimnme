#!/usr/bin/env python3
"""SVG editable de la postal (para Inkscape o Illustrator).

Toma el PDF de la postal y arma un SVG con dos capas:

* «Fondo y logotipos»: los vectores e imágenes del PDF (fondo, partitura,
  recuadros, filetes y logotipos), tal cual.
* «Textos»: cada renglón como texto editable en Noto Sans, con su peso,
  tamaño, color y espaciado entre letras.

Uso: python3 postal/svg_editable.py ENTRADA.pdf SALIDA.svg

Para editarlo hay que tener instalada la familia Noto Sans (está en
automatizacion/fuentes/).
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf

FUENTES = Path("automatizacion/fuentes")
PESOS = {"Light": 300, "Regular": 400, "SemiBold": 600, "Bold": 700, "ExtraBold": 800}


def estilo(nombre):
    """«NotoSans-SemiBoldItalic» → (peso, cursiva, archivo de la fuente)."""
    variante = nombre.split("-", 1)[1] if "-" in nombre else "Regular"
    cursiva = variante.endswith("Italic")
    base = variante[:-6] if cursiva else variante
    peso = PESOS.get(base or "Regular", 400)
    archivo = FUENTES / f"NotoSans-{variante}.ttf"
    return peso, cursiva, archivo


def color(c):
    return "#%06x" % c


def capa_textos(pagina):
    """Un <text> por renglón. Los espacios y el espaciado entre letras se
    deducen de la posición de cada letra (el PDF no los trae como texto)."""
    fuentes = {}

    def fuente(archivo):
        if archivo not in fuentes:
            fuentes[archivo] = pymupdf.Font(fontfile=str(archivo))
        return fuentes[archivo]

    salida = []
    for bloque in pagina.get_text("rawdict")["blocks"]:
        for linea in bloque.get("lines", []):
            letras = []
            for s in linea["spans"]:
                peso, cursiva, archivo = estilo(s["font"])
                f = fuente(archivo)
                for ch in s["chars"]:
                    if ch["c"].isspace():
                        continue
                    letras.append({"c": ch["c"], "x": ch["origin"][0], "y": ch["origin"][1],
                                   "avance": f.text_length(ch["c"], fontsize=s["size"]),
                                   "espacio": f.text_length(" ", fontsize=s["size"]),
                                   "estilo": (peso, cursiva, round(s["size"], 2), s["color"])})
            if not letras:
                continue
            letras.sort(key=lambda l: l["x"])
            # huecos entre letras consecutivas; el espaciado de cada estilo es
            # la mediana de los huecos pequeños; un hueco mayor es un espacio
            for a, b in zip(letras, letras[1:]):
                a["hueco"] = b["x"] - (a["x"] + a["avance"])
            letras[-1]["hueco"] = 0.0
            corridas = []
            for l in letras:
                if corridas and corridas[-1]["estilo"] == l["estilo"]:
                    corridas[-1]["letras"].append(l)
                else:
                    corridas.append({"estilo": l["estilo"], "letras": [l]})
            partes = []
            for k, c in enumerate(corridas):
                ls = c["letras"]
                huecos = sorted(l["hueco"] for l in ls[:-1] if l["hueco"] < 0.6 * l["espacio"])
                espaciado = huecos[len(huecos) // 2] if huecos else 0.0
                texto = ""
                for n, l in enumerate(ls):
                    texto += l["c"]
                    ultima = n == len(ls) - 1
                    if l["hueco"] > espaciado + 0.45 * l["espacio"] and not (ultima and k == len(corridas) - 1):
                        # uno o más espacios, según el ancho del hueco
                        texto += " " * max(1, round((l["hueco"] - espaciado) / l["espacio"]))
                peso, cursiva, tam, col = c["estilo"]
                atributos = [f'font-weight="{peso}"', f'font-size="{tam:.2f}"', f'fill="{color(col)}"']
                if cursiva:
                    atributos.append('font-style="italic"')
                if abs(espaciado) > 0.05:
                    atributos.append(f'letter-spacing="{espaciado:.2f}"')
                partes.append(f'<tspan {" ".join(atributos)}>{escape(texto)}</tspan>')
            salida.append(f'<text x="{letras[0]["x"]:.2f}" y="{letras[0]["y"]:.2f}" '
                          f'font-family="Noto Sans" xml:space="preserve">{"".join(partes)}</text>')
    return salida


def main():
    entrada, destino = sys.argv[1], sys.argv[2]
    pagina = pymupdf.open(entrada)[0]
    svg = pagina.get_svg_image(text_as_path=False)
    # el fondo: todo menos los textos (que MuPDF escribe letra por letra)
    fondo = re.sub(r"<text\b.*?</text>", "", svg, flags=re.S)
    inicio = fondo.index(">", fondo.index("<svg")) + 1
    fin = fondo.rindex("</svg>")
    ancho, alto = pagina.rect.width, pagina.rect.height
    mm = 25.4 / 72
    textos = "\n".join(capa_textos(pagina))
    salida = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" '
        f'width="{ancho * mm:.1f}mm" height="{alto * mm:.1f}mm" viewBox="0 0 {ancho:.3f} {alto:.3f}">\n'
        '<title>48.º FIMNME · Postal del abono</title>\n'
        '<g id="fondo" inkscape:groupmode="layer" inkscape:label="Fondo y logotipos">\n'
        + fondo[inicio:fin] +
        '</g>\n<g id="textos" inkscape:groupmode="layer" inkscape:label="Textos">\n'
        + textos + '\n</g>\n</svg>\n')
    Path(destino).write_text(salida, encoding="utf-8")


if __name__ == "__main__":
    main()
