#!/usr/bin/env python3
"""Postales de los eventos del 48.º FIMNME (1080 × 1350 px: PNG, JPG, PDF e IDML editable).

Siguen las postales del diseñador (lineamientos y tamaños de logotipos
aprobados). Lee postales/postales.yaml (antetítulo, intérpretes, fotos…) y,
de cada evento, lo que ya está en el Markdown: fecha, hora, sede, dirección,
obras y logotipos (de sitio/_conciertos/<evento>.html, que genera
sitio/genera.sh). Prepara las fotos (con sus rostros, para encuadrarlas sin
cortarlos), los logotipos en blanco y los datos para postales/postal.tex, y lo
compila con LuaLaTeX.

    python3 postales/genera.py                 todas las postales
    python3 postales/genera.py <evento>…       solo esas

Salida: postales/png/, jpg/, pdf/ e idml/fimnme2026-postal-<evento>.* (el IDML,
editable en InDesign con los textos en Noto Sans, lo arma
postales/idml_editable.py).
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
from PIL import Image, ImageFilter, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "automatizacion"))
sys.path.insert(0, str(RAIZ / "postales"))
import idml_editable  # noqa: E402
try:   # detección de rostros del Programa general (OpenCV es opcional)
    from preparar_imagenes import detectar_rostros
except Exception:   # noqa: BLE001
    def detectar_rostros(_img):
        return []

BUILD = RAIZ / "build/postales"
SALIDA = RAIZ / "postales"
LADO_MAX_FOTO = 1800          # px; la franja de fotos mide a lo más 96 × 46 mm
MAX_FOTOS = 4
# Logotipos (tamaños aprobados en las postales del diseñador): la CNMO
# horizontal a 15,2 mm de ancho; los demás, de área parecida (como el del
# Centro Cultural del Bosque, 8 × 4,2 mm), a lo más 4,2 mm de alto y 14 de ancho
ANCHO_CNMO_MM = 15.2
ALTO_MAX_LOGO, ANCHO_MAX_LOGO, AREA_LOGO = 4.2, 14.0, 34.0
SEPARACION_LOGOS_MM = 4.2
ANCHO_MAX_FILA = 90.0         # mm (la postal mide 108)
ENTRADA_LIBRE = "Entrada libre | Cupo limitado"


def tex(texto, juntos=()):
    """Texto → LaTeX. En las postales no hay cursivas: los *asteriscos* de
    Markdown se quitan. Los nombres de «juntos» no se parten entre renglones."""
    if not texto:
        return ""
    t = str(texto)
    for nombre in sorted(juntos, key=len, reverse=True):
        t = t.replace(nombre, nombre.replace(" ", "\u00a0"))
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")):
        t = t.replace(a, b)
    t = t.replace("\u00a0", "~").replace("\n", r"\\")   # «\n»: cambio de renglón
    return re.sub(r"\*([^*]+)\*", r"\1", t)


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
    # «de», «la», «y»… no quedan al final de un renglón
    k = 0
    while k < len(salida) - 1:
        if salida[k] in CONECTORES:
            salida[k:k + 2] = [salida[k] + "\u00a0" + salida[k + 1]]
        else:
            k += 1
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


def analizar(img, foco):
    """Rostros de una foto → (punto de interés, número de rostros, zonas). El
    punto es el indicado o el centro de los rostros (en una foto de grupo, de
    todos; se descartan los muy chicos, que suelen ser falsos). Las zonas, en
    fracciones de la foto: «rostros», lo que no debe cortarse (los rostros, de
    la frente al mentón); «nucleo», lo que conviene mostrar entero (los rostros
    con el pelo y aire arriba), y «abajo», hasta dónde conviene mostrar
    (hombros y algo del torso)."""
    caras = detectar_rostros(img)
    if caras:
        mayor = max(c[2] * c[3] for c in caras)
        caras = [c for c in caras if c[2] * c[3] >= 0.15 * mayor]
    zonas = None
    if caras:
        alto = sum(c[3] for c in caras) / len(caras)
        ancho = sum(c[2] for c in caras) / len(caras)
        x0 = min(c[0] for c in caras) - 0.45 * ancho
        x1 = max(c[0] + c[2] for c in caras) + 0.45 * ancho
        y0 = min(c[1] for c in caras) - 0.55 * alto
        y1 = max(c[1] + c[3] for c in caras) + 0.35 * alto
        abajo = max(c[1] + c[3] for c in caras) + 1.6 * alto
        w, h = img.width, img.height
        rostros = (min(c[0] for c in caras) - 0.12 * ancho, min(c[1] for c in caras) - 0.2 * alto,
                   max(c[0] + c[2] for c in caras) + 0.12 * ancho, max(c[1] + c[3] for c in caras) + 0.12 * alto)
        zonas = {"nucleo": (max(0, x0 / w), max(0, y0 / h), min(1, x1 / w), min(1, y1 / h)),
                 "rostros": (max(0, rostros[0] / w), max(0, rostros[1] / h),
                             min(1, rostros[2] / w), min(1, rostros[3] / h)),
                 "abajo": min(1, abajo / h)}
    if foco:   # el punto indicado manda: se encuadra en él, sin las zonas
        return (foco[0], foco[1]), len(caras), None
    if zonas:
        x0, y0, x1, y1 = zonas["nucleo"]
        return ((x0 + x1) / 2, (y0 + y1) / 2), len(caras), zonas
    return (0.5, 0.5), 0, None


def proporcion_marco(a, caras):
    """Proporción (ancho/alto) del marco de una foto en la franja: un retrato
    (un rostro) va en un marco angosto; una foto de grupo, en uno apaisado."""
    if caras == 1:
        return min(max(a, 0.72), 1.0)
    if caras > 1:
        return min(max(a, 1.15), 1.9)
    return min(max(a, 0.72), 1.9)


def logo_blanco(archivo, destino):
    """Logotipo de build/logos (un solo color con transparencia) en blanco. Si
    el logotipo trae un recuadro de fondo (el borde parejo y entintado, como
    el de la Fundación Harp Helú), el recuadro se quita: en blanco sería un
    cuadro gris."""
    alfa = Image.open(RAIZ / "build/logos" / archivo).convert("RGBA").getchannel("A")
    w, h = alfa.size
    borde = sorted([alfa.getpixel((x, y)) for x in range(w) for y in (0, h - 1)] +
                   [alfa.getpixel((x, y)) for y in range(h) for x in (0, w - 1)])
    fondo = borde[len(borde) // 2]
    parejo = sum(abs(v - fondo) <= 12 for v in borde) >= 0.9 * len(borde)
    if fondo > 40 and parejo:
        m = fondo + 12
        alfa = alfa.point(lambda v: 0 if v <= m else round((v - m) * 255 / (255 - m)))
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


def obras_y_etiqueta(texto):
    """«Obras de A, B y C» → («Obras de», «A, B y C»). Un texto propio
    («Improvisación libre») va con la etiqueta «Programa»."""
    m = re.match(r"(Obras? de) (.+)", texto, re.S)
    return (m.group(1), m.group(2)) if m else ("Programa", texto)


def obras_texto(fm, postal):
    """«Obras de…» del Markdown, con los nombres como están ahí (o el de
    postales.yaml). Si todos los compositores están entre los intérpretes (una
    instalación de su autor), no hace falta."""
    if "obras" in postal:
        return postal["obras"] or ""
    interpretes = {i if isinstance(i, str) else i[0] for i in postal.get("interpretes", [])}
    if fm.get("compositores") and set(fm["compositores"]) <= interpretes:
        return ""
    return fm.get("obras", "")


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
    ancho = ANCHO_CNMO_MM
    for k, l in enumerate(elegidos):
        destino = carpeta / f"logo-{k + 1}.png"
        w, h = logo_blanco(l["archivo"], destino)
        r = w / h
        alto = min((AREA_LOGO / r) ** 0.5, ALTO_MAX_LOGO, ANCHO_MAX_LOGO / r)
        ancho += alto * r
        lista.append(rf"\includegraphics[width={alto * r:.2f}mm, height={alto:.2f}mm]{{{destino.relative_to(RAIZ)}}}")
    # con muchos logotipos, la separación se reduce para que la fila no pase
    # de ANCHO_MAX_FILA (los tamaños de los logotipos no cambian)
    separacion = SEPARACION_LOGOS_MM
    if len(lista) > 1:
        separacion = max(2.0, min(separacion, (ANCHO_MAX_FILA - ancho) / (len(lista) - 1)))
    return rf"\hspace{{{separacion:.2f}mm}}".join(r"\raisebox{-0.5\height}{" + l + "}" for l in lista)


FOCOS = {}   # «focos» de postales.yaml: para todas las postales
ANCHO_FRANJA_MM, SEPARACION_FOTOS_MM = 96.0, 2.0   # los de postal.lua


def extender(img, izquierda=0, arriba=0, derecha=0, abajo=0):
    """La foto con más fondo alrededor (fracciones de su ancho y su alto): se
    estira la orilla y, hacia afuera, se funde con el color del fondo. Sirve
    para fotos de estudio con fondo liso, cuando el grupo no cabe en el marco
    sin cortar cabezas."""
    w, h = img.size
    i, a, d, b = (round(izquierda * w), round(arriba * h), round(derecha * w), round(abajo * h))
    lienzo = Image.new("RGB", (w + i + d, h + a + b))

    def lado(columna, ancho, hacia_afuera_izquierda):
        estirada = columna.resize((ancho, h)).filter(ImageFilter.GaussianBlur(6))
        pixeles = sorted((columna.getpixel((0, y)) for y in range(h)), key=sum)
        liso = Image.new("RGB", (ancho, h), pixeles[len(pixeles) // 2])   # el color del fondo
        rampa = Image.linear_gradient("L").rotate(-90 if hacia_afuera_izquierda else 90).resize((ancho, h))
        return Image.composite(liso, estirada, rampa)

    if i:
        lienzo.paste(lado(img.crop((0, 0, 1, h)), i, True), (0, a))
    if d:
        lienzo.paste(lado(img.crop((w - 1, 0, w, h)), d, False), (i + w, a))
    lienzo.paste(img, (i, a))
    if a:
        lienzo.paste(lienzo.crop((0, a, lienzo.width, a + 1)).resize((lienzo.width, a)), (0, 0))
    if b:
        lienzo.paste(lienzo.crop((0, a + h - 1, lienzo.width, a + h)).resize((lienzo.width, b)), (0, a + h))
    return lienzo


def foto_de(entrada):
    """Una foto de postales.yaml: la ruta o {archivo, recorte, extender, peso}."""
    if isinstance(entrada, str):
        return {"archivo": entrada}
    return entrada


def fotos(postal, carpeta):
    """Las fotos para la franja (postal.lua): cada una reducida (y, si se
    indica, recortada), con la proporción de su marco, su punto de interés y
    sus zonas. Devuelve también los altos de franja que les convienen:
    el necesario para que ningún rostro se corte, el preferido (con hombros) y
    el máximo (para que no se corten por los lados)."""
    entradas = [foto_de(f) for f in (postal.get("fotos") or [])[:MAX_FOTOS]]
    focos = {**FOCOS, **(postal.get("foco") or {})}
    datos = []
    for k, f in enumerate(entradas):
        img = abrir(f["archivo"])
        if f.get("recorte"):   # [x0, y0, x1, y1] en fracciones: una parte de la foto
            x0, y0, x1, y1 = f["recorte"]
            img = img.crop((round(x0 * img.width), round(y0 * img.height),
                            round(x1 * img.width), round(y1 * img.height)))
        if f.get("extender"):   # [izquierda, arriba, derecha, abajo]: más fondo
            img = extender(img, *f["extender"])
        foco, caras, zonas = analizar(img, focos.get(f["archivo"]))
        img.thumbnail((LADO_MAX_FOTO, LADO_MAX_FOTO), Image.LANCZOS)
        destino = carpeta / f"foto-{k + 1}.jpg"
        img.save(destino, quality=90)
        a = img.width / img.height
        p = (ANCHO_FRANJA_MM if len(entradas) == 1 else proporcion_marco(a, caras)) * f.get("peso", 1)
        datos.append({"archivo": destino.relative_to(RAIZ), "a": a, "p": p, "foco": foco, "zonas": zonas})
    if not datos:
        return "", (0, 0, 0)
    util = ANCHO_FRANJA_MM - SEPARACION_FOTOS_MM * (len(datos) - 1)
    suma = sum(d["p"] for d in datos)
    necesaria, preferida, maxima = 0.0, 0.0, 999.0
    for d in datos:
        w = util if len(datos) == 1 else util * d["p"] / suma
        if d["zonas"]:
            # en unidades del alto de la foto: la foto mide «a» de ancho y 1 de alto
            x0, y0, x1, y1 = d["zonas"]["rostros"]
            necesaria = max(necesaria, w * (y1 - y0) / d["a"])
            maxima = min(maxima, w / max((x1 - x0) * d["a"], 1e-3))
            y0 = d["zonas"]["nucleo"][1]
            preferida = max(preferida, w * (d["zonas"]["abajo"] - y0) / d["a"])
        else:
            preferida = max(preferida, w / d["a"])   # sin rostros: la foto entera
    if len(datos) > 1:
        # el alto en que los marcos tienen su proporción (hasta 44 mm): en la
        # franja, los retratos no quedan apaisados ni los rostros chicos
        preferida = max(preferida, min(util / suma, 44.0))
    lua = []
    for d in datos:
        z = d["zonas"]
        nucleo = "{%.4f,%.4f,%.4f,%.4f}" % z["nucleo"] if z else "nil"
        rostros = "{%.4f,%.4f,%.4f,%.4f}" % z["rostros"] if z else "nil"
        abajo = "%.4f" % z["abajo"] if z else "nil"
        lua.append(f'{{archivo="{d["archivo"]}", a={d["a"]:.4f}, p={d["p"]:.4f}, '
                   f'fx={d["foco"][0]:.4f}, fy={d["foco"][1]:.4f}, nucleo={nucleo}, rostros={rostros}, '
                   f'abajo={abajo}}}')
    return ",".join(lua), (necesaria, preferida, maxima)


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
    etiqueta_obras, obras = obras_y_etiqueta(obras_texto(fm, postal))
    fotoslua, altos = fotos(postal, carpeta)
    if fotoslua and postal.get("franja"):   # alto mínimo pedido (mm)
        altos = (max(altos[0], postal["franja"]), max(altos[1], postal["franja"]), max(altos[2], postal["franja"]))
    datos = {
        "antetitulo": tex(postal.get("antetitulo", "Concierto")),
        "titulo": tex(juntar_nombres(postal.get("titulo", "")), nombres),
        "subtitulo": tex(juntar_nombres(postal.get("subtitulo", "")), nombres),
        "fecha": tex(postal.get("fecha", fecha_texto(fm, funcion))),
        "interpretes": "".join(interpretes),
        "etiquetaobras": tex(etiqueta_obras),
        "obras": tex(obras.replace(" y ", " y\u00a0"), nombres),
        "nota": tex("\n".join(juntar_nombres(r) for r in postal.get("nota", "").split("\n")), nombres),
        "sede": tex(juntar_nombres(postal.get("sede", sede))),
        "direccion": tex(juntar_nombres(postal.get("direccion", direccion))),
        "entrada": tex(postal.get("entrada", ENTRADA_LIBRE)),
        "fotoslua": fotoslua,
        "franjanecesaria": f"{altos[0]:.2f}mm",
        "franjapreferida": f"{altos[1]:.2f}mm",
        "franjamaxima": f"{min(altos[2], 99):.2f}mm",
        "pistas": str((carpeta / "fotos.json").relative_to(RAIZ)),
        "logos": logos(fm, carpeta, postal.get("sin_logos", [])),
    }
    if fm.get("tipo") in ("actividad", "coloquio"):   # fondo verde azulado
        datos["fondoactividad"] = ""
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
    """El fondo de las postales (verde o verde azulado, partitura y degradado), igual en
    todas las de su color: la plantilla compilada con \\solofondo, para el IDML."""
    azul = "fondoactividad" in datos.read_text(encoding="utf-8")
    return lualatex("fondo-azul" if azul else "fondo-verde", BUILD,
                    rf"\def\solofondo{{}}\def\datos{{{datos.relative_to(RAIZ)}}}"
                    r"\input{postales/postal.tex}", "el fondo")


def compilar(etiqueta, datos, pdf_fondo):
    carpeta = BUILD / etiqueta
    nombre = f"fimnme2026-postal-{etiqueta}"
    hecho = lualatex(nombre, carpeta, rf"\def\datos{{{datos.relative_to(RAIZ)}}}\input{{postales/postal.tex}}",
                     etiqueta)
    for formato in ("png", "jpg", "pdf", "idml"):
        (SALIDA / formato).mkdir(exist_ok=True)
    pdf = SALIDA / "pdf" / f"{nombre}.pdf"
    shutil.copyfile(hecho, pdf)
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1080", "-scale-to-y", "1350", "-singlefile",
                    str(pdf), str(SALIDA / "png" / nombre)], check=True)
    # JPG: pesa mucho menos que el PNG (es el que usa el sitio)
    Image.open(SALIDA / "png" / f"{nombre}.png").convert("RGB").save(
        SALIDA / "jpg" / f"{nombre}.jpg", quality=90, optimize=True, progressive=True)
    # IDML editable: fondo, recuadro, logotipos, fotos y textos por separado
    idml_editable.convertir(str(pdf), str(pdf_fondo), str(RAIZ / "postales/postal.tex"),
                            str(SALIDA / "idml" / f"{nombre}.idml"), f"48.º FIMNME · Postal: {etiqueta}",
                            pistas_fotos=carpeta / "fotos.json")
    print(f"✓ {nombre}: postales/png, jpg, pdf e idml")


def main():
    datos_yaml = yaml.safe_load((SALIDA / "postales.yaml").read_text(encoding="utf-8"))
    lista = datos_yaml["postales"]
    FOCOS.update(datos_yaml.get("focos") or {})
    pedidas = set(sys.argv[1:])
    fondos = {}   # un fondo por color
    for postal in lista:
        if pedidas and not pedidas & {postal["evento"], nombre_salida(postal)}:
            continue
        etiqueta, datos = preparar(postal)
        azul = "fondoactividad" in datos.read_text(encoding="utf-8")
        if azul not in fondos:
            fondos[azul] = fondo(datos)
        compilar(etiqueta, datos, fondos[azul])


if __name__ == "__main__":
    main()
