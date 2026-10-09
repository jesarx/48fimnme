#!/usr/bin/env python3
"""Postales de los eventos del 48.º FIMNME (1080 × 1350 px: PNG, PDF e IDML editable).

Siguen las postales del diseñador (lineamientos y tamaños de logotipos
aprobados). Lee postales/postales.yaml (antetítulo, intérpretes, fotos…) y,
de cada evento, lo que ya está en el Markdown: fecha, hora, sede, dirección,
obras y logotipos (de sitio/_conciertos/<evento>.html, que genera
sitio/genera.sh). Prepara las fotos en círculo (centradas en los rostros), los
logotipos en blanco y los datos para postales/postal.tex, y lo compila con
LuaLaTeX.

    python3 postales/genera.py                 todas las postales
    python3 postales/genera.py <evento>…       solo esas

Salida: postales/fimnme2026-postal-<evento>.png, .pdf e .idml (editable en
InDesign, con los textos en Noto Sans; lo arma postal/idml_editable.py).
"""

import json
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.parse
from pathlib import Path

import yaml
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "automatizacion"))
sys.path.insert(0, str(RAIZ / "postal"))
import idml_editable  # noqa: E402
try:   # detección de rostros del Programa general (OpenCV es opcional)
    from preparar_imagenes import detectar_rostros
except Exception:   # noqa: BLE001
    def detectar_rostros(_img):
        return []

BUILD = RAIZ / "build/postales"
SALIDA = RAIZ / "postales"
PX_MM = 20                    # fotos a 2× de la salida (10 px/mm)
DIAMETRO_FOTO_MM = 17.2       # círculos de las postales del diseñador
PASO_FOTOS_MM = 20.2          # de centro a centro
MAX_FOTOS = 4
# Logotipos (tamaños aprobados en las postales del diseñador): la CNMO
# horizontal a 15,2 mm de ancho; los demás, de área parecida (como el del
# Centro Cultural del Bosque, 8 × 4,2 mm), a lo más 4,2 mm de alto y 14 de ancho
ANCHO_CNMO_MM = 15.2
ALTO_MAX_LOGO, ANCHO_MAX_LOGO, AREA_LOGO = 4.2, 14.0, 34.0
SEPARACION_LOGOS_MM = 4.2
# Con más letras que esto, en «Obras de…» los nombres de pila van en inicial
# («J. Torres Sáenz»), como en las postales del diseñador
LARGO_MAX_OBRAS = 150
ENTRADA_LIBRE = "Entrada libre | Cupo limitado"


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
    t = t.replace("\u00a0", "~").replace("\n", r"\\")   # «\n»: cambio de renglón
    return re.sub(r"\*([^*]+)\*", r"\\emph{\1}", t)


CONECTORES = {"de", "del", "la", "las", "los", "y"}


def juntar_nombres(texto, limite=26):
    """Los nombres propios (de lugares y personas) no se parten entre renglones:
    «Bosque de Chapultepec», «Paseo de la Reforma» (con espacios fijos)."""
    palabras = texto.split(" ")
    def mayuscula(w):
        return w[:1].isupper() and not w[:1].isdigit()
    k, salida = 0, []
    while k < len(palabras):
        j = k
        if mayuscula(palabras[k]) and not palabras[k].endswith((",", ".", ";", ":")):
            # una cadena: mayúscula (conector)* mayúscula …
            while j + 1 < len(palabras):
                m = j + 1
                while m < len(palabras) and palabras[m] in CONECTORES:
                    m += 1
                if m < len(palabras) and mayuscula(palabras[m]) and not palabras[j].endswith((",", ".", ";", ":")):
                    j = m
                    if palabras[m].endswith((",", ".", ";", ":")):
                        break
                else:
                    break
        cadena = " ".join(palabras[k:j + 1])
        if j > k and len(cadena) <= limite:
            salida.append(cadena.replace(" ", "\u00a0"))
        else:
            # muy larga: se puede partir, pero no después de «de», «la»…
            for w in palabras[k:j + 1]:
                if salida and salida[-1].split("\u00a0")[-1] in CONECTORES:
                    salida[-1] += "\u00a0" + w
                else:
                    salida.append(w)
        k = j + 1
    # y el último renglón, con dos palabras al menos (si no las tiene ya:
    # «…Cárdenas s/n, | Centro Histórico»)
    if len(salida) > 2 and "\u00a0" not in salida[-1] and len(salida[-2]) + len(salida[-1]) < limite:
        salida[-2:] = [salida[-2] + "\u00a0" + salida[-1]]
    return " ".join(salida)


def datos_evento(etiqueta):
    """Encabezado de la página del evento y los nombres de sus compositores."""
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


def recortar(img, lado, foco):
    """Recorte cuadrado de img alrededor de foco, escalado a lado × lado."""
    fx, fy = foco
    l = min(img.width, img.height)
    x0 = min(max(0, int(fx * img.width - l / 2)), img.width - l)
    y0 = min(max(0, int(fy * img.height - l * 0.45)), img.height - l)
    return img.crop((x0, y0, x0 + l, y0 + l)).resize((lado, lado), Image.LANCZOS)


def logo_blanco(archivo, destino):
    """Logotipo de build/logos (un solo color con transparencia) en blanco."""
    alfa = Image.open(RAIZ / "build/logos" / archivo).convert("RGBA").getchannel("A")
    blanco = Image.new("RGBA", alfa.size, (255, 255, 255, 0))
    blanco.putalpha(alfa)
    blanco.save(destino, optimize=True)
    return alfa.size


def sede_y_direccion(fm, funcion=0):
    """«Centro Cultural Tlaqná, Sala Principal, Xalapa, Veracruz» y su dirección →
    («Centro Cultural Tlaqná, Sala Principal», «Av. …, Xalapa, Veracruz»).
    En la Ciudad de México la dirección va sin «Ciudad de México»."""
    lugar = fm["fechas"][funcion]["lugar"] or fm["lugares"][0]
    direccion = fm["fechas"][funcion]["direccion"] or fm.get("direccion", "")
    partes = lugar.split(", ")
    for k in range(1, len(partes)):
        if direccion.endswith(", ".join(partes[k:])):
            lugar = ", ".join(partes[:k])
            break
    return lugar, re.sub(r",\s*Ciudad de México$", "", direccion)


def fecha_texto(fm, funcion=0):
    f = fm["fechas"][funcion]
    return f"{f['dia']} de 2026, {f['hora']} h"


def nombre_salida(postal):
    """Etiqueta del evento; si tiene varias funciones, cada postal empieza con
    la fecha de la suya: «dom-nov-15-coro-de-madrigalistas-…»."""
    if "funcion" not in postal:
        return postal["evento"]
    f = datos_evento(postal["evento"])["fechas"][postal["funcion"] - 1]
    semana, dia, mes = unicodedata.normalize("NFKD", f["corto"]).encode("ascii", "ignore").decode().lower().split()
    return re.sub(r"^[a-z]{3}-[a-z]{3}-\d+-", f"{semana}-{mes}-{dia}-", postal["evento"])


def apellidos():
    """Excepciones del índice onomástico: «Nombre Apellidos» → «Apellidos, Nombre»."""
    datos = yaml.safe_load((RAIZ / "automatizacion/indice-onomastico.yaml").read_text(encoding="utf-8"))
    return {k: v for k, v in (datos.get("indice-onomastico") or {}).items() if v != "-"}


def con_iniciales(nombre, excepciones):
    """«Jorge Torres Sáenz» → «J. Torres Sáenz»; «Liliana Z. del Río» → «L.Z. del Río»."""
    if nombre in excepciones and ", " in excepciones[nombre]:
        apellido, pila = excepciones[nombre].split(", ", 1)
        # el índice pone en mayúscula la partícula («De Mattos»); aquí va como
        # en el nombre («F.L. de Mattos»)
        if nombre.lower().endswith(apellido.lower()):
            apellido = nombre[len(nombre) - len(apellido):]
    else:
        palabras = nombre.split()
        k = len(palabras) - 1
        while k > 1 and palabras[k - 1][:1].islower():   # partículas: «del Río»
            k -= 1
        apellido, pila = " ".join(palabras[k:]), " ".join(palabras[:k])
    iniciales = "".join(p[0] + "." for p in pila.split() if p[:1].isupper())
    return (f"{iniciales} {apellido}" if iniciales else apellido).replace(" ", "\u00a0")   # no se parte


def obras_texto(fm, postal):
    """«Obras de…» del Markdown (o el de postales.yaml); si es muy largo, con
    los nombres de pila en inicial."""
    if postal.get("obras"):
        return postal["obras"]
    obras = fm.get("obras", "")
    if len(obras) > LARGO_MAX_OBRAS:
        excepciones = apellidos()
        for c in sorted(fm.get("compositores", []), key=len, reverse=True):
            obras = obras.replace(c, con_iniciales(c, excepciones))
    return obras


def origen_logos():
    """build/logos/<archivo> → ruta del logotipo en el Markdown (de manifiesto.tsv)."""
    origen = {}
    for fila in (RAIZ / "build/logos/manifiesto.tsv").read_text(encoding="utf-8").splitlines():
        partes = fila.split("\t")
        if len(partes) >= 2:
            origen[Path(partes[1]).name] = urllib.parse.unquote(partes[0].split("|")[0])
    return origen


def logos(fm, carpeta, sin_logos=()):
    """La CNMO (horizontal) y los logotipos del evento, en blanco; sin los de
    «sin_logos» (partes de su ruta: p. ej. los de una sede en la que no es
    esta función)."""
    lista = [rf"\logocnmohorizontal{{{ANCHO_CNMO_MM}mm}}{{white}}"]
    origen = origen_logos() if sin_logos else {}
    elegidos = [l for l in fm.get("logos", [])
                if not any(s in origen.get(l["archivo"], "") for s in sin_logos)]
    for k, l in enumerate(elegidos):
        destino = carpeta / f"logo-{k + 1}.png"
        w, h = logo_blanco(l["archivo"], destino)
        r = w / h
        alto = min((AREA_LOGO / r) ** 0.5, ALTO_MAX_LOGO, ANCHO_MAX_LOGO / r)
        lista.append(rf"\includegraphics[width={alto * r:.2f}mm, height={alto:.2f}mm]{{{destino.relative_to(RAIZ)}}}")
    return rf"\hspace{{{SEPARACION_LOGOS_MM}mm}}".join(r"\raisebox{-0.5\height}{" + l + "}" for l in lista)


def fotos(postal, carpeta):
    """Fotos en círculo, una debajo de otra, centradas en (centrofotos)."""
    rutas = (postal.get("fotos") or [])[:MAX_FOTOS]
    focos = postal.get("foco", {}) or {}
    r = DIAMETRO_FOTO_MM / 2
    tikz = []
    for k, ruta in enumerate(rutas):
        img = abrir(ruta)
        destino = carpeta / f"foto-{k + 1}.jpg"
        recortar(img, round(DIAMETRO_FOTO_MM * PX_MM), foco_de(img, focos.get(ruta))).save(destino, quality=90)
        dy = ((len(rutas) - 1) / 2 - k) * PASO_FOTOS_MM
        centro = f"($(centrofotos)+(0,{dy:.2f}mm)$)"
        tikz.append(
            rf"\begin{{scope}}\clip {centro} circle ({r:.2f}mm);"
            rf"\node[inner sep=0pt] at {centro} {{\includegraphics[width={DIAMETRO_FOTO_MM}mm]{{{destino.relative_to(RAIZ)}}}}};\end{{scope}}"
            rf"\draw[bordefoto, line width=1.4pt] {centro} circle ({r:.2f}mm);")
    return "\n".join(tikz)


def media_columna(postal):
    """Media altura de la columna de fotos (para que no baje hasta los logotipos)."""
    n = len((postal.get("fotos") or [])[:MAX_FOTOS])
    return f"{((n - 1) * PASO_FOTOS_MM + DIAMETRO_FOTO_MM) / 2 if n else 0:.2f}mm"


def preparar(postal):
    etiqueta = postal["evento"]
    fm = datos_evento(etiqueta)
    funcion = postal.get("funcion", 1) - 1
    nombre = nombre_salida(postal)
    carpeta = BUILD / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    nombres = fm.get("compositores", []) + [i if isinstance(i, str) else i[0] for i in postal.get("interpretes", [])]

    interpretes = []
    for i in postal.get("interpretes", []):
        persona, papel = (i, "") if isinstance(i, str) else (i[0], i[1] if len(i) > 1 else "")
        # el papel no se parte: va en el renglón del nombre o en el siguiente
        interpretes.append(rf"\interprete{{{tex(juntar_nombres(persona))}}}{{{tex(papel.replace(' ', chr(0xa0)))}}}")
    sede, direccion = sede_y_direccion(fm, funcion)
    datos = {
        "antetitulo": tex(postal.get("antetitulo", "Concierto")),
        "fecha": tex(postal.get("fecha", fecha_texto(fm, funcion))),
        "interpretes": "".join(interpretes),
        "obras": tex(obras_texto(fm, postal).replace(" y ", " y\u00a0"), nombres),
        "nota": tex("\n".join(juntar_nombres(r) for r in postal.get("nota", "").split("\n")), nombres),
        "sede": tex(juntar_nombres(postal.get("sede", sede))),
        "direccion": tex(juntar_nombres(postal.get("direccion", direccion))),
        "entrada": tex(postal.get("entrada", ENTRADA_LIBRE)),
        "fotos": fotos(postal, carpeta),
        "mediofotos": media_columna(postal),
        "logos": logos(fm, carpeta, postal.get("sin_logos", [])),
    }
    archivo = carpeta / "datos.tex"
    archivo.write_text("".join(rf"\def\{k}{{{v}}}" + "\n" for k, v in datos.items()), encoding="utf-8")
    return nombre, archivo


def lualatex(nombre, carpeta, entrada, etiqueta):
    for _ in range(2):   # dos pasadas: posiciones de TikZ (remember picture)
        r = subprocess.run(
            ["lualatex", "--interaction=nonstopmode", "--halt-on-error", f"--jobname={nombre}",
             f"--output-directory={carpeta.relative_to(RAIZ)}", entrada],
            cwd=RAIZ, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ Error de LuaLaTeX en {etiqueta}; últimas líneas del registro:")
            print("\n".join((carpeta / f"{nombre}.log").read_text(errors="replace").splitlines()[-25:]))
            sys.exit(1)
    return carpeta / f"{nombre}.pdf"


def fondo(datos):
    """El fondo de las postales (verde, partitura y degradado), igual en todas:
    la plantilla compilada con \\solofondo, para el IDML."""
    return lualatex("fondo", BUILD, rf"\def\solofondo{{}}\def\datos{{{datos.relative_to(RAIZ)}}}"
                    r"\input{postales/postal.tex}", "el fondo")


def compilar(etiqueta, datos, pdf_fondo):
    carpeta = BUILD / etiqueta
    nombre = f"fimnme2026-postal-{etiqueta}"
    hecho = lualatex(nombre, carpeta, rf"\def\datos{{{datos.relative_to(RAIZ)}}}\input{{postales/postal.tex}}",
                     etiqueta)
    pdf = SALIDA / f"{nombre}.pdf"
    shutil.copyfile(hecho, pdf)
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1080", "-scale-to-y", "1350", "-singlefile",
                    str(pdf), str(SALIDA / nombre)], check=True)
    # IDML editable: fondo, recuadro, logotipos, fotos y textos por separado
    idml_editable.convertir(str(pdf), str(pdf_fondo), str(RAIZ / "postales/postal.tex"),
                            str(SALIDA / f"{nombre}.idml"), f"48.º FIMNME · Postal: {etiqueta}")
    print(f"✓ {SALIDA.relative_to(RAIZ)}/{nombre}.png, .pdf e .idml")


def main():
    lista = yaml.safe_load((SALIDA / "postales.yaml").read_text(encoding="utf-8"))["postales"]
    pedidas = set(sys.argv[1:])
    pdf_fondo = None
    for postal in lista:
        if pedidas and not pedidas & {postal["evento"], nombre_salida(postal)}:
            continue
        etiqueta, datos = preparar(postal)
        pdf_fondo = pdf_fondo or fondo(datos)
        compilar(etiqueta, datos, pdf_fondo)


if __name__ == "__main__":
    main()
