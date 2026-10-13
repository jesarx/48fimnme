#!/usr/bin/env python3
"""IDML editable de una postal (para InDesign).

Toma el PDF de la postal y el PDF de su fondo (la misma plantilla compilada
con \\solofondo: verde, partitura y degradado) y arma un IDML de una página,
del mismo tamaño, con estos elementos, de atrás hacia adelante:

* «Fondo»: el fondo como imagen (300 ppp), bloqueado;
* los recuadros de color (el de las obras, el del abono…) como rectángulos
  de InDesign, con su color en las muestras;
* los logotipos y la pleca de Cultura e INBAL, cada uno como imagen aparte
  (los vectoriales, como el del Foro o el de la CNMO, a 1200 ppp);
* las fotos, cada una en su marco circular con el filete, para cambiarlas
  fácilmente;
* los textos, editables, en Noto Sans: un marco por bloque (antetítulo,
  fecha, intérpretes, obras…), con un estilo de párrafo por bloque y los
  mismos cortes de renglón, tamaños, colores, interlineado y espaciado entre
  letras que el PDF.

El documento mide 1080 × 1350 px (reglas en píxeles): todo se escala de los
108 × 135 mm del PDF, también los tamaños de letra, así que al exportar a
JPG a 72 ppp sale de 1080 × 1350 px, como las postales.

Las imágenes van vinculadas, no incrustadas: se guardan en la carpeta Links/,
junto al IDML (cada una con un nombre según su contenido, así que las que se
repiten, como el fondo o los logotipos, se guardan una sola vez), y las
fuentes van en «Document fonts/» (InDesign las activa al abrir el
documento). Así la carpeta del IDML lleva todo lo necesario para editarlo:
basta comprimirla.

Uso: python3 postales/idml_editable.py POSTAL.pdf FONDO.pdf PLANTILLA.tex SALIDA.idml [TÍTULO]

De PLANTILLA.tex toma los nombres de los colores (\\definecolor) para las
muestras.
"""

import hashlib
import io
import json
import shutil
from collections import Counter
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import pymupdf
from PIL import Image

FUENTES = Path(__file__).resolve().parent.parent / "automatizacion/fuentes"
ANCHO_PX = 1080            # ancho de la página del IDML, en píxeles (= puntos a 72 ppp)
PPP_FONDO = 300
PPP_VECTORES = 1200
KAPPA = 0.5522847498   # curvas de Bézier de un círculo
ESTILOS = {   # variante del PDF → estilo de la fuente en InDesign
    "Regular": "Regular", "Italic": "Italic", "Light": "Light", "LightItalic": "Light Italic",
    "SemiBold": "SemiBold", "SemiBoldItalic": "SemiBold Italic", "Bold": "Bold",
    "BoldItalic": "Bold Italic", "ExtraBold": "ExtraBold", "ExtraBoldItalic": "ExtraBold Italic",
}
LIGADURAS = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl"}
NS = 'xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="8.0"'
CABECERA = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def num(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) >= 0.00005 else "0"


# ---------------------------------------------------------------- Colores ---
class Muestras:
    """Colores RGB usados, con el nombre que tienen en la plantilla."""

    def __init__(self, plantilla):
        self.nombres = {"ffffff": "blanco", "000000": "negro"}
        texto = Path(plantilla).read_text(encoding="utf-8") if plantilla else ""
        for nombre, hexa in re.findall(r"\\definecolor\{([^}]+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}", texto):
            self.nombres.setdefault(hexa.lower(), nombre)
        self.usados = {}

    def __call__(self, rgb):
        """(r, g, b) en 0–1 o entero sRGB → «Color/…»."""
        if isinstance(rgb, int):
            rgb = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
        else:
            rgb = tuple(round(c * 255) for c in rgb[:3])
        # el PDF redondea: se toma el color con nombre más cercano (±2)
        for hexa, nombre in self.nombres.items():
            ref = tuple(int(hexa[k:k + 2], 16) for k in (0, 2, 4))
            if max(abs(a - b) for a, b in zip(rgb, ref)) <= 2:
                rgb, etiqueta = ref, nombre
                break
        else:
            etiqueta = "RGB %d %d %d" % rgb
        clave = "Color/" + re.sub(r"[^A-Za-z0-9]+", "_", etiqueta)
        self.usados[clave] = (etiqueta, rgb)
        return clave

    def xml(self):
        filas = [
            '<Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" ColorOverride="Specialblack" '
            'AlternateSpace="NoAlternateColor" AlternateColorValue="" Name="Black" ColorEditable="false" ColorRemovable="false" '
            'Visible="true" SwatchCreatorID="7937"/>',
            '<Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" ColorOverride="Specialpaper" '
            'AlternateSpace="NoAlternateColor" AlternateColorValue="" Name="Paper" ColorEditable="true" ColorRemovable="false" '
            'Visible="true" SwatchCreatorID="7937"/>',
            '<Color Self="Color/Registration" Model="Registration" Space="CMYK" ColorValue="100 100 100 100" '
            'ColorOverride="Specialregistration" AlternateSpace="NoAlternateColor" AlternateColorValue="" Name="Registration" '
            'ColorEditable="false" ColorRemovable="false" Visible="true" SwatchCreatorID="7937"/>',
        ]
        for clave, (etiqueta, rgb) in sorted(self.usados.items()):
            filas.append(f'<Color Self="{clave}" Model="Process" Space="RGB" ColorValue="{rgb[0]} {rgb[1]} {rgb[2]}" '
                         f'ColorOverride="Normal" AlternateSpace="NoAlternateColor" AlternateColorValue="" '
                         f'Name={quoteattr(etiqueta)} ColorEditable="true" ColorRemovable="true" Visible="true" '
                         f'SwatchCreatorID="7937"/>')
        filas.append('<Swatch Self="Swatch/None" Name="None" ColorEditable="false" ColorRemovable="false" Visible="true" '
                     'SwatchCreatorID="7937"/>')
        filas.append('<StrokeStyle Self="StrokeStyle/$ID/Solid" Name="$ID/Solid"/>')
        return f'{CABECERA}<idPkg:Graphic {NS}>\n' + "\n".join(filas) + "\n</idPkg:Graphic>\n"


# ------------------------------------------------------------------ Textos --
def variante(fuente):
    """«ABCDEF+NotoSans-SemiBoldItalic» → «SemiBoldItalic»."""
    nombre = fuente.split("+", 1)[-1]
    return nombre.split("-", 1)[1] if "-" in nombre else "Regular"


def s_tam(letra):
    return letra["estilo"][1]


def renglones(pagina):
    """Renglones del PDF: cada uno con su origen (x, línea base) y sus
    corridas de texto [(texto, variante, tamaño, color, espaciado)]. Los
    espacios y el espaciado entre letras se deducen de la posición de cada
    letra (como en el PDF no vienen como texto)."""
    fuentes = {}

    def fuente(var):
        if var not in fuentes:
            fuentes[var] = pymupdf.Font(fontfile=str(FUENTES / f"NotoSans-{var}.ttf"))
        return fuentes[var]

    salida = []
    for bloque in pagina.get_text("rawdict")["blocks"]:
        for linea in bloque.get("lines", []):
            letras = []
            for s in linea["spans"]:
                if "NotoSans" not in s["font"]:
                    continue
                var = variante(s["font"])
                f = fuente(var)
                for ch in s["chars"]:
                    c = LIGADURAS.get(ch["c"], ch["c"])
                    if c.isspace():
                        continue
                    # el avance de cada letra es el ancho de su caja en el PDF
                    # (en una ligadura, «fi», la «f» trae todo el ancho y la
                    # «i», cero)
                    letras.append({"c": c, "x": ch["origin"][0], "y": ch["origin"][1],
                                   "avance": max(0.0, ch["bbox"][2] - ch["bbox"][0]),
                                   "espacio": f.text_length(" ", fontsize=s["size"]),
                                   "estilo": (var, round(s["size"], 2), s["color"])})
            if not letras:
                continue
            letras.sort(key=lambda l: l["x"])
            for a, b in zip(letras, letras[1:]):
                a["hueco"] = b["x"] - (a["x"] + a["avance"])
            letras[-1]["hueco"] = 0.0
            grupos = []
            for l in letras:
                if grupos and grupos[-1]["estilo"] == l["estilo"]:
                    grupos[-1]["letras"].append(l)
                else:
                    grupos.append({"estilo": l["estilo"], "letras": [l]})
            corridas = []
            for k, g in enumerate(grupos):
                ls = g["letras"]
                huecos = sorted(l["hueco"] for l in ls[:-1] if l["hueco"] < 0.6 * l["espacio"])
                espaciado = huecos[len(huecos) // 2] if huecos else 0.0
                texto = ""
                for n, l in enumerate(ls):
                    texto += l["c"]
                    ultima = n == len(ls) - 1
                    if l["hueco"] > espaciado + 0.45 * l["espacio"] and not (ultima and k == len(grupos) - 1):
                        # un espacio o, si el hueco es mayor, espacios de medio
                        # cuadratín (\enspace, \hskip0.5em)
                        n = round((l["hueco"] - espaciado) / l["espacio"])
                        texto += " " if n <= 1 else "\u2002" * max(1, round(l["hueco"] / (0.5 * s_tam(l))))
                var, tam, col = g["estilo"]
                corridas.append((texto, var, tam, col, espaciado if abs(espaciado) > 0.05 else 0.0))
            fin = letras[-1]["x"] + letras[-1]["avance"]
            salida.append({"x": letras[0]["x"], "y": letras[0]["y"], "ancho": fin - letras[0]["x"],
                           "tam": max(c[2] for c in corridas), "corridas": corridas})
    # microtype varía un poco el tamaño de algunos renglones: los tamaños que
    # difieren en menos de 1 % se unifican en el más frecuente
    cuenta = Counter(c[2] for r in salida for c in r["corridas"])
    grupos, actual = [], []
    for tam in sorted(cuenta):
        if actual and tam > actual[0] * 1.01:
            grupos.append(actual)
            actual = []
        actual.append(tam)
    if actual:
        grupos.append(actual)
    unificado = {tam: max(g, key=lambda v: (cuenta[v], v)) for g in grupos for tam in g}
    for r in salida:
        r["corridas"] = [(tx, var, unificado[tam], col, esp) for tx, var, tam, col, esp in r["corridas"]]
        r["tam"] = max(c[2] for c in r["corridas"])
    salida.sort(key=lambda r: (round(r["y"], 1), r["x"]))
    return salida


def bloques_de_texto(lineas, recuadros):
    """Agrupa los renglones en bloques (un marco cada uno): renglones seguidos,
    dentro del mismo recuadro (o fuera de todos), alineados a la izquierda (o
    con sangría, si continúan el anterior) y con el mismo tamaño y color al
    empezar."""
    def recuadro(r):
        return next((k for k, c in enumerate(recuadros) if c.contains(pymupdf.Point(r["x"] + 1, r["y"] - 1))), None)

    bloques = []
    for r in lineas:
        firma = r["corridas"][0][2:4]
        dentro = recuadro(r)
        elegido = None
        for b in reversed(bloques):
            ultimo = b["lineas"][-1]
            salto = r["y"] - ultimo["y"]
            if b["recuadro"] != dentro or not 0.5 < salto <= 1.75 * max(r["tam"], ultimo["tam"]):
                continue
            sangria = r["x"] - b["x"]
            if abs(sangria) <= 1.5 and firma == b["firma"]:
                elegido = b
                break
            if 3 <= sangria <= 20:
                elegido = b
                r["continua"] = True
                break
        if elegido is None:
            bloques.append({"x": r["x"], "firma": firma, "recuadro": dentro, "lineas": [r]})
        else:
            elegido["lineas"].append(r)
    return bloques


# ---------------------------------------------------------------- Gráficos --
def firma_trazo(d):
    return (d["type"], tuple(round(v, 1) for v in d["rect"]), tuple(round(v, 3) for v in (d.get("fill") or ())),
            tuple(round(v, 3) for v in (d.get("color") or ())))


def es_rectangulo(d):
    """¿Un rectángulo relleno sin filete (recuadro, franja)?"""
    if d["type"] != "f" or not d.get("fill"):
        return False
    items = d["items"]
    if all(i[0] == "re" for i in items) and len(items) == 1:
        return True
    if len(items) == 4 and all(i[0] == "l" for i in items):
        puntos = [i[1] for i in items] + [items[-1][2]]
        return all(abs(a.x - b.x) < 0.01 or abs(a.y - b.y) < 0.01 for a, b in zip(puntos, puntos[1:]))
    return False


def cerca(a, b, tolerancia):
    """¿Dos rectángulos casi iguales?"""
    return max(abs(a.x0 - b.x0), abs(a.y0 - b.y0), abs(a.x1 - b.x1), abs(a.y1 - b.y1)) <= tolerancia


def es_linea(d):
    """¿Un filete recto (una sola línea con trazo)?"""
    return d["type"] == "s" and len(d["items"]) == 1 and d["items"][0][0] == "l"


def es_circulo(d):
    return d["type"] == "s" and sum(1 for i in d["items"] if i[0] == "c") >= 4 and \
        abs(d["rect"].width - d["rect"].height) < 0.5


def agrupar(trazos, margen=2.0):
    """Trazos vectoriales cercanos → grupos (un logotipo cada uno)."""
    grupos = []
    for d in trazos:
        caja = pymupdf.Rect(d["rect"])
        juntos = [g for g in grupos if (g["caja"] + (-margen, -margen, margen, margen)).intersects(caja)]
        nuevo = {"caja": caja, "trazos": [d]}
        for g in juntos:
            nuevo["caja"] |= g["caja"]
            nuevo["trazos"] = g["trazos"] + nuevo["trazos"]
            grupos.remove(g)
        grupos.append(nuevo)
    return grupos


def rasterizar_vectores(grupo):
    """Redibuja los trazos de un grupo en una página aparte y la exporta como
    PNG con transparencia."""
    caja = grupo["caja"] + (-0.5, -0.5, 0.5, 0.5)
    doc = pymupdf.open()
    pag = doc.new_page(width=caja.width, height=caja.height)
    m = pymupdf.Matrix(1, 0, 0, 1, -caja.x0, -caja.y0)
    forma = pag.new_shape()
    for d in grupo["trazos"]:
        for it in d["items"]:
            if it[0] == "l":
                forma.draw_line(it[1] * m, it[2] * m)
            elif it[0] == "c":
                forma.draw_bezier(it[1] * m, it[2] * m, it[3] * m, it[4] * m)
            elif it[0] == "re":
                forma.draw_rect(pymupdf.Rect(it[1]) * m)
            elif it[0] == "qu":
                forma.draw_quad(pymupdf.Quad(it[1]) * m)
        forma.finish(fill=d.get("fill"), color=d.get("color"), width=d.get("width") or 0,
                     even_odd=d.get("even_odd", False), closePath=d.get("closePath", False),
                     fill_opacity=d.get("fill_opacity") or 1, stroke_opacity=d.get("stroke_opacity") or 1,
                     lineCap=max(d.get("lineCap") or (0,)), lineJoin=d.get("lineJoin") or 0)
    forma.commit()
    pix = pag.get_pixmap(dpi=PPP_VECTORES, alpha=True)
    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples), caja


def imagen_del_pdf(doc, xref):
    """Imagen incrustada en el PDF (con su transparencia, si la tiene)."""
    datos = doc.extract_image(xref)
    img = Image.open(io.BytesIO(datos["image"]))
    if datos.get("smask"):
        alfa = Image.open(io.BytesIO(doc.extract_image(datos["smask"])["image"])).convert("L")
        img = img.convert("RGB")
        img.putalpha(alfa.resize(img.size))
    return img


def codificar(img, formato):
    """Imagen → (bytes, tipo para InDesign, extensión). Se guarda a 72 ppp,
    así su tamaño en puntos es el de píxeles."""
    b = io.BytesIO()
    if formato == "JPEG":
        img.convert("RGB").save(b, "JPEG", quality=92, dpi=(72, 72))
        return b.getvalue(), "$ID/JPEG", ".jpg"
    img.save(b, "PNG", optimize=True, dpi=(72, 72))
    return b.getvalue(), "$ID/Portable Network Graphics (PNG)", ".png"


def enlaces_usados(carpeta):
    """Archivos de Links/ que vinculan los IDML de la carpeta."""
    usados = set()
    for idml in Path(carpeta).glob("*.idml"):
        with zipfile.ZipFile(idml) as z:
            for nombre in z.namelist():
                if nombre.startswith("Spreads/"):
                    usados |= set(re.findall(r'LinkResourceURI="file:Links/([^"]+)"', z.read(nombre).decode()))
    return usados


def preparar_paquete(carpeta):
    """La carpeta de los IDML lista para comprimir y enviar: las fuentes en
    «Document fonts/» (copias de automatizacion/fuentes), un LEEME y, en
    Links/, solo las imágenes que vinculan los IDML (se borran las que ya
    no usa ninguno)."""
    carpeta = Path(carpeta)
    fuentes = carpeta / "Document fonts"
    fuentes.mkdir(parents=True, exist_ok=True)
    for f in sorted(FUENTES.glob("NotoSans-*.ttf")) + [FUENTES / "LICENCIA-OFL.txt"]:
        destino = fuentes / f.name
        if not destino.exists() or destino.read_bytes() != f.read_bytes():
            shutil.copyfile(f, destino)
    leeme = Path(__file__).resolve().parent / "idml-LEEME.txt"
    if leeme.exists():
        shutil.copyfile(leeme, carpeta / "LEEME.txt")
    enlaces = carpeta / "Links"
    if enlaces.exists():
        usados = enlaces_usados(carpeta)
        for f in enlaces.iterdir():
            if f.is_file() and f.name not in usados:
                f.unlink()


# --------------------------------------------------------------------- IDML --
class Documento:
    def __init__(self, ancho, alto, muestras, enlaces):
        """ancho, alto: los del PDF (pt); en el IDML se escalan a ANCHO_PX
        de ancho (self.k); enlaces: la carpeta Links/ de las imágenes."""
        self.ancho, self.alto = ancho, alto
        self.k = ANCHO_PX / ancho
        self.enlaces = Path(enlaces)
        self.muestras = muestras
        self.n = 0
        self.objetos = []        # XML de los objetos del pliego, de atrás hacia adelante
        self.historias = {}      # id → XML
        self.estilos = {}        # firma → (Self, nombre)
        self.variantes = set()   # variantes de Noto Sans que se usan

    def nuevo(self):
        self.n += 1
        return f"u{self.n:x}"

    def p(self, x, y):
        """Coordenadas de la página (pt, desde arriba a la izquierda) →
        coordenadas del pliego. En un documento de páginas sueltas, InDesign
        centra la página en el origen del pliego."""
        return f"{num((x - self.ancho / 2) * self.k)} {num((y - self.alto / 2) * self.k)}"

    def m(self, v):
        """Una medida del PDF (pt) en el IDML (px)."""
        return num(v * self.k)

    def geometria(self, puntos):
        filas = []
        for ancla, izq, der in puntos:
            filas.append(f'<PathPointType Anchor="{self.p(*ancla)}" LeftDirection="{self.p(*izq)}" '
                         f'RightDirection="{self.p(*der)}"/>')
        return ('<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>'
                + "".join(filas) + '</PathPointArray></GeometryPathType></PathGeometry></Properties>')

    def rect_puntos(self, r):
        esquinas = [(r.x0, r.y0), (r.x0, r.y1), (r.x1, r.y1), (r.x1, r.y0)]
        return [(e, e, e) for e in esquinas]

    def circulo_puntos(self, cx, cy, radio):
        k = KAPPA * radio
        return [((cx, cy - radio), (cx - k, cy - radio), (cx + k, cy - radio)),
                ((cx + radio, cy), (cx + radio, cy - k), (cx + radio, cy + k)),
                ((cx, cy + radio), (cx + k, cy + radio), (cx - k, cy + radio)),
                ((cx - radio, cy), (cx - radio, cy + k), (cx - radio, cy - k))]

    def imagen_xml(self, img, formato, caja, nombre):
        """La imagen, vinculada: se guarda en Links/ con un nombre según su
        contenido (la misma imagen en varias postales es un solo archivo)."""
        datos, tipo, extension = codificar(img, formato)
        prefijo = re.sub(r"[^a-z]+", "-", nombre.lower().split(" ")[0]).strip("-") or "imagen"
        archivo = f"{prefijo}-{hashlib.sha1(datos).hexdigest()[:12]}{extension}"
        self.enlaces.mkdir(parents=True, exist_ok=True)
        ruta = self.enlaces / archivo
        if not ruta.exists():
            ruta.write_bytes(datos)
        w, h = img.size
        sx, sy = caja.width * self.k / w, caja.height * self.k / h
        ident, enlace = self.nuevo(), self.nuevo()
        return (f'<Image Self="{ident}" Space="$ID/RGB" ActualPpi="72 72" EffectivePpi="{round(72 / sx)} {round(72 / sy)}" '
                f'ImageRenderingIntent="UseColorSettings" LocalDisplaySetting="Default" ImageTypeName="{tipo}" '
                f'AppliedObjectStyle="ObjectStyle/$ID/[None]" Visible="true" Name="$ID/" '
                f'ItemTransform="{sx:.6f} 0 0 {sy:.6f} {self.p(caja.x0, caja.y0)}">'
                f'<Properties><GraphicBounds Left="0" Top="0" Right="{w}" Bottom="{h}"/></Properties>'
                f'<Link Self="{enlace}" AssetURL="$ID/" AssetID="$ID/" LinkResourceURI="file:Links/{archivo}" '
                f'LinkResourceFormat="{tipo}" StoredState="Normal" LinkClassID="35906" LinkClientID="257" '
                f'LinkResourceModified="false" LinkObjectModified="false" ShowInUI="true" CanEmbed="true" '
                f'CanUnembed="true" CanPackage="true" ImportPolicy="NoAutoImport" ExportPolicy="NoAutoExport"/>'
                f'</Image>')

    def marco_imagen(self, img, formato, caja, nombre, bloqueado=False):
        self.objetos.append(
            f'<Rectangle Self="{self.nuevo()}" ContentType="GraphicType" Name={quoteattr(nombre)} '
            f'ItemLayer="ucapa" Locked="{"true" if bloqueado else "false"}" Visible="true" '
            f'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
            f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            + self.geometria(self.rect_puntos(caja))
            + '<FrameFittingOption FittingOnEmptyFrame="None"/>'
            + self.imagen_xml(img, formato, caja, nombre) + '</Rectangle>')

    def foto(self, img, caja, filete, color, nombre):
        cx, cy, radio = (caja.x0 + caja.x1) / 2, (caja.y0 + caja.y1) / 2, caja.width / 2
        self.objetos.append(
            f'<Oval Self="{self.nuevo()}" ContentType="GraphicType" Name={quoteattr(nombre)} ItemLayer="ucapa" '
            f'Locked="false" Visible="true" FillColor="Swatch/None" StrokeColor="{color}" StrokeWeight="{self.m(filete)}" '
            f'StrokeAlignment="CenterAlignment" AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            + self.geometria(self.circulo_puntos(cx, cy, radio))
            + '<FrameFittingOption FittingOnEmptyFrame="FillProportionally"/>'
            + self.imagen_xml(img, "JPEG", caja, nombre) + '</Oval>')

    def foto_recortada(self, img, caja, marco, radio, nombre):
        """Foto en un marco de esquinas redondeadas; la imagen (más grande que
        el marco) queda recortada por él, como en el PDF."""
        esquinas = "".join(f' {e}CornerOption="RoundedCorner" {e}CornerRadius="{self.m(radio)}"'
                           for e in ("TopLeft", "TopRight", "BottomLeft", "BottomRight"))
        self.objetos.append(
            f'<Rectangle Self="{self.nuevo()}" ContentType="GraphicType" Name={quoteattr(nombre)} ItemLayer="ucapa" '
            f'Locked="false" Visible="true" FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0"'
            f'{esquinas} AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            + self.geometria(self.rect_puntos(marco))
            # lo que la imagen sobresale del marco (InDesign la ubica con su
            # ItemTransform; esto lo repite para otros programas, como Scribus)
            + f'<FrameFittingOption FittingOnEmptyFrame="FillProportionally" LeftCrop="{self.m(marco.x0 - caja.x0)}" '
              f'TopCrop="{self.m(marco.y0 - caja.y0)}" RightCrop="{self.m(caja.x1 - marco.x1)}" '
              f'BottomCrop="{self.m(caja.y1 - marco.y1)}"/>'
            + self.imagen_xml(img, "JPEG", caja, nombre) + '</Rectangle>')

    def rectangulo(self, caja, color, nombre):
        self.objetos.append(
            f'<Rectangle Self="{self.nuevo()}" ContentType="Unassigned" Name={quoteattr(nombre)} ItemLayer="ucapa" '
            f'Locked="false" Visible="true" FillColor="{color}" StrokeColor="Swatch/None" StrokeWeight="0" '
            f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            + self.geometria(self.rect_puntos(caja)) + '</Rectangle>')

    def linea(self, a, b, grueso, color, nombre):
        self.objetos.append(
            f'<GraphicLine Self="{self.nuevo()}" ContentType="Unassigned" Name={quoteattr(nombre)} ItemLayer="ucapa" '
            f'Locked="false" Visible="true" FillColor="Swatch/None" StrokeColor="{color}" StrokeWeight="{self.m(grueso)}" '
            f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            f'<Properties><PathGeometry><GeometryPathType PathOpen="true"><PathPointArray>'
            f'<PathPointType Anchor="{self.p(a.x, a.y)}" LeftDirection="{self.p(a.x, a.y)}" RightDirection="{self.p(a.x, a.y)}"/>'
            f'<PathPointType Anchor="{self.p(b.x, b.y)}" LeftDirection="{self.p(b.x, b.y)}" RightDirection="{self.p(b.x, b.y)}"/>'
            f'</PathPointArray></GeometryPathType></PathGeometry></Properties></GraphicLine>')

    def estilo(self, var, tam, color):
        """Estilo de párrafo para los bloques que empiezan con esta letra."""
        firma = (var, tam, color)
        if firma not in self.estilos:
            k = len(self.estilos) + 1
            nombre_color = self.muestras.usados[color][0]
            nombre = f"{k:02d} {ESTILOS.get(var, var)} {self.m(tam).replace('.', ',')} px · {nombre_color}"
            self.estilos[firma] = (f"ParagraphStyle/Postal{k:02d}", nombre)
        return self.estilos[firma][0]

    def texto(self, bloque):
        lineas = bloque["lineas"]
        x0 = bloque["x"]
        # interlineado de cada renglón: la distancia desde la línea base anterior
        for k, r in enumerate(lineas):
            r["interlineado"] = r["y"] - lineas[k - 1]["y"] if k else None
        # el del primero (que fija la distancia del borde de arriba del marco a
        # la primera línea base): el del bloque, si es parejo; si no, 1,2 veces
        # el tamaño de la letra
        tam0 = lineas[0]["tam"]
        primero = lineas[1]["interlineado"] if len(lineas) > 1 and lineas[1]["interlineado"] >= 0.9 * tam0 \
            else round(tam0 * 1.2, 2)
        lineas[0]["interlineado"] = primero
        sangrias = [r["x"] - x0 for r in lineas if r.get("continua")]
        sangria = sorted(sangrias)[len(sangrias) // 2] if sangrias else 0.0
        # párrafos: con sangría francesa si hay renglones que continúan el
        # anterior; si no, un solo párrafo con cortes de renglón
        parrafos = []
        for r in lineas:
            if not parrafos or (sangrias and not r.get("continua")):
                parrafos.append([r])
            else:
                parrafos[-1].append(r)
        var0, tam0, col0 = lineas[0]["corridas"][0][1:4]
        color0 = self.muestras(col0)
        estilo = self.estilo(var0, tam0, color0)
        xml = []
        for np_, par in enumerate(parrafos):
            atributos = f'AppliedParagraphStyle="{estilo}" Hyphenation="false" Justification="LeftAlign"'
            if sangria:
                atributos += f' LeftIndent="{self.m(sangria)}" FirstLineIndent="{self.m(-sangria)}"'
            corridas = []
            for nl, r in enumerate(par):
                for nc, (texto, var, tam, col, espaciado) in enumerate(r["corridas"]):
                    if nl and nc == 0:
                        texto = "\u2028" + texto    # corte de renglón
                    tracking = round(espaciado / tam * 1000) if espaciado else 0
                    corridas.append((texto, var, tam, self.muestras(col), tracking, r["interlineado"]))
            for k, (texto, var, tam, color, tracking, interlineado) in enumerate(corridas):
                br = "<Br/>" if k == len(corridas) - 1 and np_ < len(parrafos) - 1 else ""
                xml.append(
                    f'<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    f'FontStyle="{ESTILOS.get(var, var)}" PointSize="{self.m(tam)}" FillColor="{color}" Tracking="{tracking}">'
                    f'<Properties><AppliedFont type="string">Noto Sans</AppliedFont>'
                    f'<Leading type="unit">{self.m(interlineado)}</Leading></Properties>'
                    f'<Content>{escape(texto)}</Content>{br}</CharacterStyleRange>')
            xml[-len(corridas)] = f'<ParagraphStyleRange {atributos}>' + xml[-len(corridas)]
            xml[-1] += '</ParagraphStyleRange>'
        historia = self.nuevo()
        self.historias[historia] = (
            f'{CABECERA}<idPkg:Story {NS}>\n<Story Self="{historia}" AppliedTOCStyle="n" TrackChanges="false" '
            f'StoryTitle="$ID/" AppliedNamedGrid="n">'
            '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" '
            'StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection"/>'
            + "".join(xml) + '</Story>\n</idPkg:Story>\n')
        # el marco: la primera línea base queda a «interlineado» del borde de arriba
        arriba = lineas[0]["y"] - primero
        ancho = max(r["x"] - x0 + r["ancho"] for r in lineas)
        ancho = min(ancho * 1.05 + 6, self.ancho + 20 - x0)
        abajo = lineas[-1]["y"] + 0.8 * lineas[-1]["tam"] + 4
        caja = pymupdf.Rect(x0, arriba, x0 + ancho, abajo)
        primer_texto = "".join(c[0] for c in lineas[0]["corridas"])
        self.objetos.append(
            f'<TextFrame Self="{self.nuevo()}" ParentStory="{historia}" PreviousTextFrame="n" NextTextFrame="n" '
            f'ContentType="TextType" Name={quoteattr(primer_texto[:40])} ItemLayer="ucapa" Locked="false" Visible="true" '
            f'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
            f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
            + self.geometria(self.rect_puntos(caja))
            + '<TextFramePreference TextColumnCount="1" FirstBaselineOffset="LeadingOffset" AutoSizingType="Off" '
              'VerticalJustification="TopAlign" IgnoreWrap="true"><Properties><InsetSpacing type="list">'
              '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
              '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
              '</InsetSpacing></Properties></TextFramePreference></TextFrame>')

    # ------------------------------------------------------------ paquete --
    def fuentes_xml(self):
        variantes = sorted({ESTILOS.get(v, v) for (v, _, _) in self.estilos} | {"Regular"} |
                           {ESTILOS.get(variante_f, variante_f) for variante_f in self.variantes})
        filas = []
        for k, estilo in enumerate(variantes):
            ps = "NotoSans-" + estilo.replace(" ", "")
            filas.append(f'<Font Self="difuente{k}" FontFamily="Noto Sans" Name="Noto Sans {estilo}" '
                         f'PostScriptName="{ps}" Status="Installed" FontStyleName="{estilo}" FontType="OpenTypeTT" '
                         f'WritingScript="0" FullName="Noto Sans {estilo}" FullNameNative="Noto Sans {estilo}" '
                         f'FontStyleNameNative="{estilo}" PlatformName="$ID/" Version="Version 2.013"/>')
        return (f'{CABECERA}<idPkg:Fonts {NS}>\n<FontFamily Self="difamilia" Name="Noto Sans">'
                + "".join(filas) + '</FontFamily>\n</idPkg:Fonts>\n')

    def estilos_xml(self):
        parrafos = [
            '<ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" Name="$ID/[No paragraph style]" '
            'Imported="false" PointSize="12" FillColor="Color/Black" Hyphenation="false" Justification="LeftAlign">'
            '<Properties><AppliedFont type="string">Noto Sans</AppliedFont><Leading type="enumeration">Auto</Leading>'
            '</Properties></ParagraphStyle>',
            '<ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle" '
            'Imported="false" NextStyle="ParagraphStyle/$ID/NormalParagraphStyle">'
            '<Properties><BasedOn type="string">$ID/[No paragraph style]</BasedOn></Properties></ParagraphStyle>',
        ]
        for (var, tam, color), (ident, nombre) in self.estilos.items():
            parrafos.append(
                f'<ParagraphStyle Self="{ident}" Name={quoteattr(nombre)} Imported="false" NextStyle="{ident}" '
                f'FontStyle="{ESTILOS.get(var, var)}" PointSize="{self.m(tam)}" FillColor="{color}" '
                f'Hyphenation="false" Justification="LeftAlign"><Properties>'
                f'<BasedOn type="string">$ID/[No paragraph style]</BasedOn>'
                f'<AppliedFont type="string">Noto Sans</AppliedFont></Properties></ParagraphStyle>')
        return (f'{CABECERA}<idPkg:Styles {NS}>\n'
                '<RootCharacterStyleGroup Self="ugcar"><CharacterStyle Self="CharacterStyle/$ID/[No character style]" '
                'Imported="false" Name="$ID/[No character style]"/></RootCharacterStyleGroup>\n'
                '<RootParagraphStyleGroup Self="ugpar">' + "".join(parrafos) + '</RootParagraphStyleGroup>\n'
                '<TOCStyle Self="TOCStyle/$ID/DefaultTOCStyleName" Name="$ID/DefaultTOCStyleName" Title="Contents" '
                'TitleStyle="ParagraphStyle/$ID/[No paragraph style]"/>\n'
                '<RootCellStyleGroup Self="ugcel"><CellStyle Self="CellStyle/$ID/[None]" Name="$ID/[None]"/>'
                '</RootCellStyleGroup>\n'
                '<RootTableStyleGroup Self="ugtab"><TableStyle Self="TableStyle/$ID/[No table style]" '
                'Name="$ID/[No table style]"/></RootTableStyleGroup>\n'
                '<RootObjectStyleGroup Self="ugobj">'
                '<ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]" FillColor="Swatch/None" '
                'StrokeColor="Swatch/None" StrokeWeight="0"/>'
                '<ObjectStyle Self="ObjectStyle/$ID/[Normal Graphics Frame]" Name="$ID/[Normal Graphics Frame]">'
                '<Properties><BasedOn type="string">$ID/[None]</BasedOn></Properties></ObjectStyle>'
                '<ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" Name="$ID/[Normal Text Frame]">'
                '<Properties><BasedOn type="string">$ID/[None]</BasedOn></Properties></ObjectStyle>'
                '</RootObjectStyleGroup>\n</idPkg:Styles>\n')

    def guardar(self, destino, titulo):
        # en píxeles enteros (el PDF redondea el alto: 1349,998 → 1350)
        ancho_px, alto_px = round(self.ancho * self.k), round(self.alto * self.k)
        w, h = num(ancho_px), num(alto_px)
        traslado = f"{num(-ancho_px / 2)} {num(-alto_px / 2)}"
        margenes = (f'<MarginPreference ColumnCount="1" ColumnGutter="12" Top="0" Bottom="0" Left="0" Right="0" '
                    f'ColumnDirection="Horizontal" ColumnsPositions="0 {w}"/>')
        maestra = (f'{CABECERA}<idPkg:MasterSpread {NS}>\n<MasterSpread Self="umaestra" Name="A-Página maestra" '
                   f'NamePrefix="A" BaseName="Página maestra" ShowMasterItems="true" PageCount="1" '
                   f'OverriddenPageItemProps="" PrimaryTextFrame="n" ItemTransform="1 0 0 1 0 0">'
                   f'<Page Self="umaestrap" GeometricBounds="0 0 {h} {w}" ItemTransform="1 0 0 1 {traslado}" '
                   f'Name="A" AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
                   f'UseMasterGrid="true">{margenes}</Page></MasterSpread>\n</idPkg:MasterSpread>\n')
        pliego = (f'{CABECERA}<idPkg:Spread {NS}>\n<Spread Self="upliego" PageCount="1" BindingLocation="0" '
                  f'AllowPageShuffle="true" ItemTransform="1 0 0 1 0 0" ShowMasterItems="true" '
                  f'FlattenerOverride="Default">'
                  f'<Page Self="upagina" GeometricBounds="0 0 {h} {w}" ItemTransform="1 0 0 1 {traslado}" '
                  f'Name="1" AppliedMaster="umaestra" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
                  f'UseMasterGrid="true">{margenes}</Page>\n'
                  + "\n".join(self.objetos) + '\n</Spread>\n</idPkg:Spread>\n')
        preferencias = (
            f'{CABECERA}<idPkg:Preferences {NS}>\n'
            f'<DocumentPreference PageHeight="{h}" PageWidth="{w}" PagesPerDocument="1" FacingPages="false" '
            'DocumentBleedTopOffset="0" DocumentBleedBottomOffset="0" DocumentBleedInsideOrLeftOffset="0" '
            'DocumentBleedOutsideOrRightOffset="0" DocumentBleedUniformSize="true" SlugTopOffset="0" '
            'SlugBottomOffset="0" SlugInsideOrLeftOffset="0" SlugRightOrOutsideOffset="0" '
            'DocumentSlugUniformSize="false" PreserveLayoutWhenShuffling="true" AllowPageShuffle="true" '
            'OverprintBlack="true" PageBinding="LeftToRight" ColumnDirection="Horizontal" ColumnGuideLocked="true" '
            'MasterTextFrame="false" SnippetImportUsesOriginalLocation="false" Intent="WebIntent" '
            'StartPageNumber="1"/>\n'
            '<ViewPreference HorizontalMeasurementUnits="Pixels" VerticalMeasurementUnits="Pixels" '
            'LineMeasurementUnits="Points" TypographicMeasurementUnits="Points" TextSizeMeasurementUnits="Points" '
            'PrintDialogMeasurementUnits="Points" RulerOrigin="SpreadOrigin"/>\n'
            '<TransparencyPreference BlendingSpace="RGB" GlobalLightAngle="120" GlobalLightAltitude="30"/>\n'
            '</idPkg:Preferences>\n')
        historias = list(self.historias)
        designmap = (
            f'{CABECERA}<?aid style="50" type="document" readerVersion="6.0" featureSet="257" product="8.0(370)" ?>\n'
            f'<Document {NS} Self="d" StoryList="{" ".join(historias + ["uhistoriafondo"])}" '
            f'Name={quoteattr(titulo)} ZeroPoint="0 0" ActiveLayer="ucapa" '
            'CMYKProfile="Coated FOGRA39 (ISO 12647-2:2004)" RGBProfile="sRGB IEC61966-2.1" '
            'SolidColorIntent="UseColorSettings" AfterBlendingIntent="UseColorSettings" '
            'DefaultImageIntent="UseColorSettings" RGBPolicy="PreserveEmbeddedProfiles" '
            'CMYKPolicy="CombinationOfPreserveAndSafeCmyk" AccurateLABSpots="false">\n'
            '<idPkg:Graphic src="Resources/Graphic.xml"/>\n'
            '<idPkg:Fonts src="Resources/Fonts.xml"/>\n'
            '<idPkg:Styles src="Resources/Styles.xml"/>\n'
            '<idPkg:Preferences src="Resources/Preferences.xml"/>\n'
            '<idPkg:Tags src="XML/Tags.xml"/>\n'
            '<Layer Self="ucapa" Name="Postal" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true" '
            'LockGuides="false" UI="true" Expendable="true" Printable="true">'
            '<Properties><LayerColor type="enumeration">LightBlue</LayerColor></Properties></Layer>\n'
            '<idPkg:MasterSpread src="MasterSpreads/MasterSpread_umaestra.xml"/>\n'
            '<idPkg:Spread src="Spreads/Spread_upliego.xml"/>\n'
            '<Section Self="useccion" Length="1" Name="" ContinueNumbering="true" IncludeSectionPrefix="false" '
            'PageNumberStyle="Arabic" PageStart="upagina" SectionPrefix="" Marker=""/>\n'
            '<idPkg:BackingStory src="XML/BackingStory.xml"/>\n'
            + "".join(f'<idPkg:Story src="Stories/Story_{s}.xml"/>\n' for s in historias)
            + '</Document>\n')
        etiquetas = (f'{CABECERA}<idPkg:Tags {NS}>\n<XMLTag Self="XMLTag/Root" Name="Root"><Properties>'
                     '<TagColor type="enumeration">LightBlue</TagColor></Properties></XMLTag>\n</idPkg:Tags>\n')
        respaldo = (f'{CABECERA}<idPkg:BackingStory {NS}>\n<XmlStory Self="uhistoriafondo" AppliedTOCStyle="n" '
                    'TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">'
                    '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    '<XMLElement Self="diraiz" MarkupTag="XMLTag/Root"/></CharacterStyleRange>'
                    '</ParagraphStyleRange></XmlStory>\n</idPkg:BackingStory>\n')
        contenedor = (f'{CABECERA}<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                      '<rootfiles><rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles></container>\n')
        with zipfile.ZipFile(destino, "w") as z:
            z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.adobe.indesign-idml-package",
                       compress_type=zipfile.ZIP_STORED)
            partes = {"designmap.xml": designmap, "META-INF/container.xml": contenedor,
                      "Resources/Graphic.xml": self.muestras.xml(), "Resources/Fonts.xml": self.fuentes_xml(),
                      "Resources/Styles.xml": self.estilos_xml(), "Resources/Preferences.xml": preferencias,
                      "MasterSpreads/MasterSpread_umaestra.xml": maestra, "Spreads/Spread_upliego.xml": pliego,
                      "XML/Tags.xml": etiquetas, "XML/BackingStory.xml": respaldo}
            partes.update({f"Stories/Story_{s}.xml": x for s, x in self.historias.items()})
            for nombre, contenido in partes.items():
                z.writestr(nombre, contenido, compress_type=zipfile.ZIP_DEFLATED)


def convertir(pdf, pdf_fondo, plantilla, destino, titulo, pistas_fotos=None):
    """pistas_fotos: JSON (de postales/postal.lua) con el marco y la imagen de
    cada foto recortada en un rectángulo de esquinas redondeadas."""
    doc = pymupdf.open(pdf)
    pagina = doc[0]
    fondo = pymupdf.open(pdf_fondo)[0]
    muestras = Muestras(plantilla)
    idml = Documento(pagina.rect.width, pagina.rect.height, muestras, Path(destino).parent / "Links")

    # 1. Fondo (bloqueado)
    pix = fondo.get_pixmap(dpi=PPP_FONDO)
    idml.marco_imagen(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), "JPEG",
                      pagina.rect, "Fondo", bloqueado=True)

    # 2. Lo que no es fondo: recuadros, fotos (con su filete), logotipos
    del_fondo = {firma_trazo(d) for d in fondo.get_drawings()}
    trazos = [d for d in pagina.get_drawings() if firma_trazo(d) not in del_fondo]
    cajas_fondo = [pymupdf.Rect(i["bbox"]) for i in fondo.get_image_info()]
    imagenes = [i for i in pagina.get_image_info(xrefs=True)
                if i["xref"] and not any(cerca(pymupdf.Rect(i["bbox"]), c, 1) for c in cajas_fondo)]
    circulos = [d for d in trazos if es_circulo(d)]
    pistas = json.loads(Path(pistas_fotos).read_text()) if pistas_fotos and Path(pistas_fotos).exists() else []
    fotos, otras, recortadas = [], [], []
    for i in imagenes:
        caja = pymupdf.Rect(i["bbox"])
        pista = next((p for p in pistas if cerca(pymupdf.Rect(p["imagen"]), caja, 1)), None)
        filete = next((d for d in circulos if cerca(pymupdf.Rect(d["rect"]), caja, 3)), None)
        if pista:
            recortadas.append((i, caja, pista))
        else:
            (fotos if filete else otras).append((i, caja, filete))
    usados = [f[2]["seqno"] for f in fotos]
    rectangulos = [d for d in trazos if es_rectangulo(d)]
    lineas_rectas = [d for d in trazos if es_linea(d)]
    vectores = [d for d in trazos if not es_rectangulo(d) and not es_linea(d) and d["seqno"] not in usados]

    for k, d in enumerate(rectangulos):
        idml.rectangulo(pymupdf.Rect(d["rect"]), muestras(d["fill"]), f"Recuadro {k + 1}")
    for k, d in enumerate(lineas_rectas):
        _, a, b = d["items"][0]
        idml.linea(a, b, d.get("width") or 1, muestras(d["color"]), f"Filete {k + 1}")
    graficos = []
    for i, caja, _ in otras:
        graficos.append((caja, imagen_del_pdf(doc, i["xref"]), "PNG"))
    for g in agrupar(vectores):
        img, caja = rasterizar_vectores(g)
        graficos.append((caja, img, "PNG"))
    graficos.sort(key=lambda g: (round(g[0].y0 / 20), g[0].x0))
    for k, (caja, img, formato) in enumerate(graficos):
        idml.marco_imagen(img, formato, caja, f"Logotipo {k + 1}")
    for k, (i, caja, pista) in enumerate(sorted(recortadas, key=lambda f: f[1].x0)):
        # la caja de la imagen, la exacta de postal.lua (la del PDF se redondea)
        idml.foto_recortada(imagen_del_pdf(doc, i["xref"]), pymupdf.Rect(pista["imagen"]),
                            pymupdf.Rect(pista["marco"]), pista["radio"], f"Foto {k + 1}")
    for k, (i, caja, filete) in enumerate(sorted(fotos, key=lambda f: f[1].y0)):
        idml.foto(imagen_del_pdf(doc, i["xref"]), caja, filete.get("width") or 1,
                  muestras(filete["color"]), f"Foto {k + 1}")

    # 3. Textos
    lineas = renglones(pagina)
    idml.variantes = {c[1] for r in lineas for c in r["corridas"]}
    for b in bloques_de_texto(lineas, [pymupdf.Rect(d["rect"]) for d in rectangulos]):
        idml.texto(b)
    idml.guardar(destino, titulo)


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    pdf, fondo, plantilla, destino = sys.argv[1:5]
    titulo = sys.argv[5] if len(sys.argv) > 5 else Path(destino).stem
    convertir(pdf, fondo, plantilla, destino, titulo)


if __name__ == "__main__":
    main()
