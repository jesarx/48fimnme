#!/usr/bin/env python3
"""Video promocional del 48º FIMNME (muestra), vertical 9:16 para redes.

Lee video/guion.yaml (escenas, duraciones, textos y, en las escenas «clip»,
el video o la foto de marcador) y compone cada cuadro con Pillow sobre el
fondo de las postales: el verde con la partitura de «1x4» de Manuel Enríquez
(que se desplaza despacio), el logotipo del Foro en dorado y Noto Sans. Los
cuadros pasan directo a ffmpeg (H.264, 30 cuadros por segundo, sin audio).

    python3 video/genera.py                 el video completo
    python3 video/genera.py --muestras      solo una hoja con un cuadro por escena

Salida: la de «salida» en el guion (video/fimnme2026-promo-muestra.mp4) y
video/fimnme2026-promo-muestras.jpg (un cuadro de cada escena).

Requisitos: Python 3 con Pillow, PyYAML y PyMuPDF; ffmpeg; LuaLaTeX (para
los logotipos vectoriales del Foro y de la CNMO).
"""

import math
import subprocess
import sys
from pathlib import Path

import pymupdf
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / "build/video"
FUENTES = RAIZ / "automatizacion/fuentes"
ANCHO, ALTO, FPS = 1080, 1920, 30

# Colores de las postales
FONDO = (0x61, 0x76, 0x55)
OSCURO = (0x52, 0x64, 0x48)
LOGO = (0xE6, 0xAE, 0x78)
ACENTO = (0xF0, 0xC7, 0x9B)
CASIBLANCO = (0xE8, 0xEF, 0xE5)
SUAVE = (0xDC, 0xE6, 0xD8)
BLANCO = (255, 255, 255)

# Estilos de texto: fuente, tamaño (px), color, mayúsculas, espaciado entre
# letras (px) y espacio antes (px)
ESTILOS = {
    "antetitulo":     ("SemiBold", 40, ACENTO, True, 7, 0),
    "numero":         ("ExtraBold", 300, BLANCO, False, 0, 0),
    "etiqueta":       ("SemiBold", 64, ACENTO, True, 5, 22),
    "detalle":        ("Regular", 48, CASIBLANCO, False, 0, 26),
    "detalle_acento": ("SemiBold", 46, ACENTO, False, 0, 54),
    "grande":         ("Bold", 90, BLANCO, False, 0, 6),
    "grande_acento":  ("Bold", 90, ACENTO, False, 0, 6),
    "media":          ("Bold", 74, BLANCO, False, 0, 10),
    "media_acento":   ("Bold", 74, ACENTO, False, 0, 10),
    "linea":          ("SemiBold", 70, BLANCO, False, 0, 46),
    "sublinea":       ("Regular", 44, SUAVE, False, 0, 10),
    "sitio":          ("SemiBold", 50, BLANCO, False, 0, 22),
}
ANCHO_TEXTO = 920          # px: los textos más largos pasan al renglón siguiente
ZONA_SEGURA = (230, 1560)  # px: arriba y abajo quedan los botones de las redes


# ------------------------------------------------------------------ apoyo --
def fuente(peso, tamano):
    return ImageFont.truetype(str(FUENTES / f"NotoSans-{peso}.ttf"), tamano)


def suave(x):
    """0 → 1 con salida suave (ease-out cubic)."""
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def con_alfa(im, k):
    if k >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point([int(v * k) for v in range(256)]))
    return im


def renglones(texto, f, espaciado):
    """Parte un texto en renglones que quepan en ANCHO_TEXTO."""
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = f"{actual} {p}".strip()
        if actual and medir(prueba, f, espaciado) > ANCHO_TEXTO:
            lineas.append(actual)
            actual = p
        else:
            actual = prueba
    return lineas + [actual]


def medir(texto, f, espaciado):
    return f.getlength(texto) + espaciado * max(len(texto) - 1, 0)


def capa_texto(texto, estilo):
    """El texto (centrado, en uno o más renglones) en una imagen RGBA justa."""
    peso, tamano, color, mayus, espaciado, _ = ESTILOS[estilo]
    f = fuente(peso, tamano)
    texto = texto.upper() if mayus else texto
    lineas = renglones(texto, f, espaciado)
    asc, desc = f.getmetrics()
    alto_linea = int((asc + desc) * (0.92 if tamano > 200 else 1.08))
    ancho = int(max(medir(l, f, espaciado) for l in lineas)) + 8
    im = Image.new("RGBA", (ancho, alto_linea * len(lineas) + desc // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lineas):
        x = (ancho - medir(l, f, espaciado)) / 2
        y = i * alto_linea
        if espaciado:
            for ch in l:
                d.text((x, y), ch, font=f, fill=color)
                x += f.getlength(ch) + espaciado
        else:
            d.text((x, y), l, font=f, fill=color)
    # recorte vertical a la tinta (los números grandes traen mucho aire)
    caja = im.getchannel("A").getbbox()
    if caja:
        im = im.crop((0, max(caja[1] - 6, 0), im.width, min(caja[3] + 6, im.height)))
    return im


class Bloque:
    """Textos apilados y centrados que entran uno tras otro (aparecen y suben)."""

    def __init__(self, textos, centro_y, retardo=0.12):
        self.piezas = []
        y = 0
        for i, t in enumerate(textos):
            capa = capa_texto(t["texto"], t["estilo"])
            y += ESTILOS[t["estilo"]][5] if i else 0
            self.piezas.append((capa, y, 0.15 + i * retardo))
            y += capa.height
        self.y0 = int(centro_y - y / 2)

    def pintar(self, cuadro, t, dur, salida=0.35):
        fin = 1 - suave((t - (dur - salida)) / salida) if t > dur - salida else 1
        for capa, y, entra in self.piezas:
            k = suave((t - entra) / 0.55)
            if k <= 0:
                continue
            dy = int((1 - k) * 46)
            cuadro.alpha_composite(con_alfa(capa, k * fin),
                                   ((ANCHO - capa.width) // 2, self.y0 + y + dy))


# --------------------------------------------------------------- recursos --
def logotipos():
    """El logotipo del Foro (dorado) y el de la CNMO (blanco), de sus TikZ."""
    BUILD.mkdir(parents=True, exist_ok=True)
    tex = BUILD / "logos.tex"
    tex.write_text(r"""\documentclass[tikz,border=0pt]{standalone}
\usepackage{xcolor}
\definecolor{colorlogo}{HTML}{E6AE78}
\input{automatizacion/plantilla/logo-48.tex}
\input{automatizacion/plantilla/logo-cnmo-horizontal.tex}
\begin{document}
\logofimnme{60mm}{colorlogo}
\logocnmohorizontal{60mm}{white}
\end{document}
""", encoding="utf-8")
    pdf = BUILD / "logos.pdf"
    if not pdf.exists() or pdf.stat().st_mtime < tex.stat().st_mtime:
        subprocess.run(["lualatex", "--interaction=nonstopmode", "--halt-on-error",
                        f"--output-directory={BUILD.relative_to(RAIZ)}", str(tex.relative_to(RAIZ))],
                       cwd=RAIZ, check=True, capture_output=True)
    doc = pymupdf.open(pdf)
    salida = []
    for pagina in doc:
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(8, 8), alpha=True)
        salida.append(Image.frombytes("RGBA", (pix.width, pix.height), pix.samples))
    return salida[0], salida[1]


def a_ancho(im, ancho):
    return im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)


def partitura():
    """La partitura de «1x4» de Enríquez, en blanco translúcido, más alta que el cuadro."""
    doc = pymupdf.open(RAIZ / "automatizacion/plantilla/partitura-1x4.pdf")
    pagina = doc[0]
    escala = 1500 / pagina.rect.width
    pix = pagina.get_pixmap(matrix=pymupdf.Matrix(escala, escala), alpha=True)
    hoja = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    blanca = Image.new("RGBA", hoja.size, (255, 255, 255, 0))
    blanca.putalpha(hoja.getchannel("A").point([int(v * 0.12) for v in range(256)]))
    # dos hojas, una sobre otra, para que alcance mientras se desplaza
    tira = Image.new("RGBA", (blanca.width, blanca.height * 2), (0, 0, 0, 0))
    tira.alpha_composite(blanca, (0, 0))
    tira.alpha_composite(blanca, (0, blanca.height))
    return tira


def degradado(alto, arriba, abajo, color):
    """Franja de ANCHO × alto que pasa de la opacidad «arriba» a «abajo» (0 a 1)."""
    g = Image.new("L", (1, alto))
    for y in range(alto):
        g.putpixel((0, y), int(255 * (arriba + (abajo - arriba) * y / max(alto - 1, 1))))
    capa = Image.new("RGBA", (ANCHO, alto), color + (0,))
    capa.putalpha(g.resize((ANCHO, alto)))
    return capa


class Fondo:
    """El verde de las postales con la partitura, que sube despacio durante el video."""

    def __init__(self, total):
        self.tira = partitura()
        self.total = total
        self.base = Image.new("RGBA", (ANCHO, ALTO), FONDO + (255,))
        self.base.alpha_composite(degradado(ALTO // 2, 0, 0.35, OSCURO), (0, ALTO // 2))

    def cuadro(self, t):
        im = self.base.copy()
        y = int(260 + 300 * t / self.total)
        im.alpha_composite(self.tira.crop((self.tira.width - ANCHO - 120, y,
                                           self.tira.width - 120, y + ALTO)))
        return im


class Medio:
    """Lo que ocupa la pantalla en una escena «clip»: el video o, mientras no lo
    haya, la foto de marcador con un acercamiento lento."""

    def __init__(self, escena, dur):
        self.dur = dur
        self.video = escena.get("video")
        self.inicio = escena.get("inicio", 0)
        self.lector, self.leido, self.ultimo = None, -1, None
        if not self.video:
            foto = ImageOps.exif_transpose(Image.open(RAIZ / escena["foto"])).convert("RGB")
            k = max(ANCHO * 1.12 / foto.width, ALTO * 1.12 / foto.height)
            self.foto = foto.resize((round(foto.width * k), round(foto.height * k)), Image.LANCZOS)
        # velo para que los textos se lean sobre cualquier imagen
        self.velo = Image.new("RGBA", (ANCHO, ALTO), (12, 20, 14, 70))
        self.velo.alpha_composite(degradado(460, 0.62, 0, (12, 20, 14)), (0, 0))   # la marca, arriba
        self.velo.alpha_composite(degradado(ALTO - 760, 0, 0.78, (12, 20, 14)), (0, 760))
        self.etiqueta = None if self.video else etiqueta_espacio(escena.get("espacio", ""))

    def cuadro_video(self, i):
        """El cuadro i del video, leído de ffmpeg en orden (sin guardar todo en memoria)."""
        if self.lector is None or i < self.leido:
            if self.lector:
                self.lector.kill()
            filtro = (f"scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
                      f"crop={ANCHO}:{ALTO},fps={FPS}")
            self.lector = subprocess.Popen(
                ["ffmpeg", "-v", "error", "-ss", str(self.inicio), "-t", str(self.dur + 0.5),
                 "-i", str(RAIZ / self.video), "-vf", filtro, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.leido = -1
        tam = ANCHO * ALTO * 3
        while self.leido < i:
            datos = self.lector.stdout.read(tam)
            if len(datos) < tam:      # el video es más corto: se queda el último cuadro
                break
            self.ultimo, self.leido = datos, self.leido + 1
        return Image.frombytes("RGB", (ANCHO, ALTO), self.ultimo)

    def cuadro(self, t):
        if self.video:
            im = self.cuadro_video(int(t * FPS)).convert("RGBA")
        else:
            z = 1 + 0.10 * (1 - t / self.dur)          # de 1.10 a 1.00 (se aleja)
            w, h = ANCHO * z * self.foto.width / (ANCHO * 1.12), ALTO * z * self.foto.height / (ALTO * 1.12)
            w, h = min(w, self.foto.width), min(h, self.foto.height)
            x0, y0 = (self.foto.width - w) / 2, (self.foto.height - h) * 0.4
            im = self.foto.resize((ANCHO, ALTO), Image.BILINEAR,
                                  box=(x0, y0, x0 + w, y0 + h)).convert("RGBA")
        im.alpha_composite(self.velo)
        if self.etiqueta:
            im.alpha_composite(self.etiqueta, (ANCHO - self.etiqueta.width - 60, ZONA_SEGURA[0] + 10))
        return im


def etiqueta_espacio(quien):
    """«ESPACIO PARA VIDEO · <ensamble>»: marca la muestra mientras no hay video."""
    f1, f2 = fuente("Bold", 26), fuente("Regular", 26)
    a, b = "ESPACIO PARA VIDEO", f"  {quien}" if quien else ""
    ancho = int(f1.getlength(a) + f2.getlength(b)) + 44
    im = Image.new("RGBA", (ancho, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, ancho - 1, 55), radius=28, fill=(230, 174, 120, 235))
    d.text((22, 12), a, font=f1, fill=(23, 43, 32))
    d.text((22 + f1.getlength(a), 12), b, font=f2, fill=(23, 43, 32))
    return im


def nombre_foro(alto_linea=46, tamano=40):
    """FORO INTERNACIONAL / DE MÚSICA NUEVA / MANUEL ENRÍQUEZ, en dorado."""
    f, fs = fuente("Regular", tamano), fuente("SemiBold", tamano)
    lineas = [("FORO INTERNACIONAL", f), ("DE MÚSICA NUEVA", f), ("MANUEL ENRÍQUEZ", fs)]
    ancho = int(max(ff.getlength(t) for t, ff in lineas)) + 4
    im = Image.new("RGBA", (ancho, alto_linea * 3 + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (t, ff) in enumerate(lineas):
        d.text((0, i * alto_linea), t, font=ff, fill=LOGO)
    return im


# ---------------------------------------------------------------- escenas --
class Apertura:
    def __init__(self, escena, dur, logo, _cnmo):
        self.dur = dur
        self.logo = a_ancho(logo, 430)
        self.nombre = nombre_foro(62, 54)
        self.fechas = capa_texto("6 al 21 de noviembre · 2026", "detalle")
        self.ed = capa_texto("48ª edición", "antetitulo")

    def pintar(self, im, t):
        fin = 1 - suave((t - (self.dur - 0.35)) / 0.35) if t > self.dur - 0.35 else 1
        k = suave(t / 0.8)
        logo = self.logo
        if k < 1:
            esc = 0.85 + 0.15 * k
            logo = self.logo.resize((max(1, int(self.logo.width * esc)), max(1, int(self.logo.height * esc))),
                                    Image.LANCZOS)
        im.alpha_composite(con_alfa(logo, k * fin), ((ANCHO - logo.width) // 2, 560 + (self.logo.height - logo.height) // 2))
        y = 560 + self.logo.height + 70
        for capa, entra, dy in ((self.nombre, 0.45, 0), (self.fechas, 0.85, self.nombre.height + 48),
                                (self.ed, 1.15, self.nombre.height + 48 + self.fechas.height + 34)):
            k2 = suave((t - entra) / 0.55)
            if k2 > 0:
                im.alpha_composite(con_alfa(capa, k2 * fin), ((ANCHO - capa.width) // 2, y + dy + int((1 - k2) * 40)))


class Cifra:
    def __init__(self, escena, dur, *_):
        self.dur = dur
        self.bloque = Bloque(escena["textos"], 900)

    def pintar(self, im, t):
        self.bloque.pintar(im, t, self.dur)


class Clip:
    def __init__(self, escena, dur, *_):
        self.dur = dur
        self.medio = Medio(escena, dur)
        self.bloque = Bloque(escena["textos"], 1180)

    def pintar(self, im, t):
        k = suave(t / 0.35) * (1 - suave((t - (self.dur - 0.3)) / 0.3) if t > self.dur - 0.3 else 1)
        if k > 0:
            im.alpha_composite(con_alfa(self.medio.cuadro(t), k))
        self.bloque.pintar(im, t, self.dur)


class Cierre:
    def __init__(self, escena, dur, logo, cnmo):
        self.dur = dur
        self.logo = a_ancho(logo, 300)
        self.nombre = nombre_foro(56, 48)
        self.bloque = Bloque(escena["textos"], 1130)
        self.cnmo = a_ancho(cnmo, 260)
        pleca = Image.open(RAIZ / "postales/recursos/pleca-cultura-inbal80.png").convert("RGBA")
        self.pleca = a_ancho(pleca, 640)
        self.velo = degradado(700, 0, 0.88, (8, 12, 9))

    def pintar(self, im, t):
        k = suave(t / 0.6)
        im.alpha_composite(con_alfa(self.velo, k), (0, ALTO - 700))
        im.alpha_composite(con_alfa(self.logo, k), ((ANCHO - self.logo.width) // 2, 470 + int((1 - k) * 40)))
        k2 = suave((t - 0.25) / 0.55)
        if k2 > 0:
            im.alpha_composite(con_alfa(self.nombre, k2),
                               ((ANCHO - self.nombre.width) // 2, 470 + self.logo.height + 50 + int((1 - k2) * 40)))
        self.bloque.pintar(im, t - 0.5, self.dur + 10)      # se queda hasta el final
        k3 = suave((t - 1.1) / 0.6)
        if k3 > 0:
            im.alpha_composite(con_alfa(self.cnmo, k3), ((ANCHO - self.cnmo.width) // 2, 1440))
            im.alpha_composite(con_alfa(self.pleca, k3), ((ANCHO - self.pleca.width) // 2, 1600))


TIPOS = {"apertura": Apertura, "cifra": Cifra, "clip": Clip, "cierre": Cierre}


class Marca:
    """Logotipo y nombre del Foro, chicos, arriba a la izquierda (como en las postales)."""

    def __init__(self, logo):
        self.logo = a_ancho(logo, 104)
        self.nombre = nombre_foro(30, 26)

    def pintar(self, im, k):
        if k > 0:
            im.alpha_composite(con_alfa(self.logo, k), (64, ZONA_SEGURA[0] - 110))
            im.alpha_composite(con_alfa(self.nombre, k), (64 + self.logo.width + 22, ZONA_SEGURA[0] - 108))


# ------------------------------------------------------------------ video --
def preparar():
    guion = yaml.safe_load((RAIZ / "video/guion.yaml").read_text(encoding="utf-8"))
    logo, cnmo = logotipos()
    escenas, t0 = [], 0.0
    for e in guion["escenas"]:
        dur = float(e["duracion"])
        escenas.append((t0, dur, e["tipo"], TIPOS[e["tipo"]](e, dur, logo, cnmo)))
        t0 += dur
    return guion, escenas, t0, Fondo(t0), Marca(logo)


def cuadro(t, escenas, fondo, marca):
    im = fondo.cuadro(t)
    for inicio, dur, tipo, escena in escenas:
        if inicio <= t < inicio + dur:
            local = t - inicio
            escena.pintar(im, local)
            if tipo not in ("apertura", "cierre"):
                # la marca aparece después de la apertura y se va antes del cierre
                k = 1.0
                if escenas.index((inicio, dur, tipo, escena)) == 1:
                    k = suave(local / 0.5)
                marca.pintar(im, k)
            break
    return im.convert("RGB")


def muestras(escenas, fondo, marca):
    """Hoja con un cuadro de cada escena (a 1.6 s de empezar, o a la mitad)."""
    lado = (270, 480)
    hoja = Image.new("RGB", (lado[0] * 5 + 6 * 12, lado[1] * 2 + 3 * 12), (23, 43, 32))
    for i, (inicio, dur, _, _) in enumerate(escenas):
        t = inicio + min(1.6, dur * 0.6)
        im = cuadro(t, escenas, fondo, marca).resize(lado, Image.LANCZOS)
        hoja.paste(im, (12 + (i % 5) * (lado[0] + 12), 12 + (i // 5) * (lado[1] + 12)))
    destino = RAIZ / "video/fimnme2026-promo-muestras.jpg"
    hoja.save(destino, quality=88)
    print(f"✓ {destino.relative_to(RAIZ)}")


def main():
    guion, escenas, total, fondo, marca = preparar()
    muestras(escenas, fondo, marca)
    if "--muestras" in sys.argv:
        return
    salida = RAIZ / guion["salida"]
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{ANCHO}x{ALTO}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
    n = math.ceil(total * FPS)
    for i in range(n):
        ff.stdin.write(cuadro(i / FPS, escenas, fondo, marca).tobytes())
        if i % (FPS * 5) == 0:
            print(f"  {i / FPS:4.1f} s de {total:.1f} s", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("✗ ffmpeg no pudo escribir el video")
    mb = salida.stat().st_size / 1e6
    print(f"✓ {salida.relative_to(RAIZ)} ({total:.1f} s, {ANCHO}×{ALTO}, {mb:.1f} MB, sin audio)")


if __name__ == "__main__":
    main()
