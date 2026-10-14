#!/usr/bin/env python3
"""Boletín por correo del 48º FIMNME (newsletter/).

Lo arma con los datos del sitio, que salen del Markdown
(sitio/_data/agenda.json, foro.json y abono.json: sitio/genera.sh
--contenido y sitio/recursos.py), las postales (postales/jpg) y la dirección
del sitio (url y baseurl de sitio/_config.yml), a la que enlazan los eventos.

Deja en newsletter/:

* img/                                  encabezado y pie (de imagenes.tex, con
                                        el logotipo del Foro, la CNMO y la pleca
                                        de Cultura e INBAL de las postales) y
                                        las postales de la inauguración y la
                                        clausura
* fimnme2026-newsletter.html            el boletín, con las imágenes de img/
                                        (para verlo y revisarlo)
* fimnme2026-newsletter-outlook.html    el mismo, con las imágenes dentro del
                                        archivo: se abre en el navegador, se
                                        copia y se pega en un mensaje nuevo de
                                        Outlook (en la web)
* fimnme2026-newsletter.eml             el mismo, como mensaje sin enviar (con
                                        las imágenes adjuntas en línea y una
                                        versión en texto): Outlook de escritorio
                                        lo abre listo para enviar

Uso: python3 newsletter/genera.py   (desde cualquier carpeta)
"""

import base64
import hashlib
import json
import re
import subprocess
import sys
from email.message import EmailMessage
from email.policy import SMTP
from html import escape
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
AQUI = RAIZ / "newsletter"
IMG = AQUI / "img"
BUILD = RAIZ / "build/newsletter"
DATOS = RAIZ / "sitio/_data"
NOMBRE = "fimnme2026-newsletter"

ASUNTO = "48º Foro Internacional de Música Nueva Manuel Enríquez · 6 al 21 de noviembre"
TITULO = "48º Foro Internacional de Música Nueva Manuel Enríquez"
ABONO = "Abono para la inauguración y la clausura"   # como en las postales
ENTRADA = "Entrada libre con cupo limitado"

# Colores: los del sitio (sitio/assets/css/sitio.css) y los de las postales
VERDEOSCURO = "#172B20"   # texto
ACENTO = "#2F7F59"        # antetítulos, cifras y enlaces
VERDEGRIS = "#546B5C"     # texto secundario
FILETE = "#B9CDBF"
BEIGE = "#F4F1EA"         # fondo de las cifras
EXTERIOR = "#E6E9E3"      # alrededor del boletín
PORTADABASE = "#4E5F44"   # recuadro del abono
VERDEPIE = "#526448"      # banda final: el verde de las postales con su velo (el pie empieza así)
CASIBLANCO = "#E8EFE5"
SUAVE = "#DCE6D8"
DORADO = "#F0C79B"        # «acento» de las postales: abono y botón
TEAL = "#3F6467"          # Coloquio: el verde azulado de sus postales (#53797C), más oscuro para el texto
TEALCLARO = "#E3ECEC"
LETRA = "'Noto Sans', 'Segoe UI', Helvetica, Arial, sans-serif"

MESES_CORTOS = {"octubre": "OCT", "noviembre": "NOV", "diciembre": "DIC"}


# -----------------------------------------------------------------------------
# Datos
# -----------------------------------------------------------------------------
def leer_json(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def config(clave):
    """Un valor de sitio/_config.yml (la dirección del sitio, la venta del abono)."""
    texto = (RAIZ / "sitio/_config.yml").read_text(encoding="utf-8")
    m = re.search(rf'^{clave}:\s*"?([^"\n#]*)"?', texto, flags=re.M)
    return m.group(1).strip() if m else ""


def sitio_url():
    return config("url").rstrip("/") + config("baseurl").rstrip("/")


def hora(e):
    return f"{e['hora']} h"


def unir(lista):
    return lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " y " + lista[-1]


def slug(e):
    return e["url"].strip("/").split("/")[-1]


# -----------------------------------------------------------------------------
# Imágenes
# -----------------------------------------------------------------------------
def lualatex(pieza):
    """Una pieza de imagenes.tex → PNG de 1200 px de ancho (en build/)."""
    BUILD.mkdir(parents=True, exist_ok=True)
    orden = ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={BUILD}", f"-jobname={pieza}",
             rf"\def\pieza{{{pieza}}}\input{{newsletter/imagenes.tex}}"]
    for _ in range(2):   # (remember picture: la segunda pasada coloca el fondo)
        r = subprocess.run(orden, cwd=RAIZ, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"Error al compilar {pieza}: ver {BUILD / pieza}.log")
    subprocess.run(["pdftoppm", "-png", "-r", "254", "-singlefile",
                    str(BUILD / f"{pieza}.pdf"), str(BUILD / pieza)], check=True)
    return Image.open(BUILD / f"{pieza}.png").convert("RGB")


def guardar_si_cambia(im, destino, **opciones):
    """Guarda la imagen solo si sus píxeles cambian (el archivo no se toca si
    no hace falta: así git no ve cambios de puros bytes)."""
    if destino.exists():
        with Image.open(destino) as previa:
            if previa.size == im.size and previa.convert("RGB").tobytes() == im.tobytes():
                return
    im.save(destino, **opciones)


def imagenes(destacados):
    IMG.mkdir(parents=True, exist_ok=True)
    guardar_si_cambia(lualatex("encabezado"), IMG / "encabezado.jpg",
                      format="JPEG", quality=88, optimize=True, progressive=True)
    # el pie va en PNG: su borde superior tiene que ser exactamente el verde de la banda
    guardar_si_cambia(lualatex("pie"), IMG / "pie.png", format="PNG", optimize=True)
    usadas = {"encabezado.jpg", "pie.png"}
    for clave, e in destacados.items():
        origen = RAIZ / "postales/jpg" / f"fimnme2026-postal-{slug(e)}.jpg"
        destino = IMG / f"postal-{clave}.jpg"
        if not destino.exists() or destino.stat().st_mtime < origen.stat().st_mtime:
            im = Image.open(origen).convert("RGB")
            im = im.resize((540, 675), Image.LANCZOS)
            im.save(destino, "JPEG", quality=84, optimize=True, progressive=True)
        usadas.add(destino.name)
    for f in IMG.iterdir():
        if f.name not in usadas:
            f.unlink()


# -----------------------------------------------------------------------------
# HTML (tablas y estilos en línea: lo que conservan Outlook y los demás
# programas de correo; sin hojas de estilo, que Outlook en la web descarta al
# pegar)
# -----------------------------------------------------------------------------
def p(texto, tam=16, color=VERDEOSCURO, alto=1.6, abajo=16, extra=""):
    return (f'<p style="margin:0 0 {abajo}px 0; font-family:{LETRA}; font-size:{tam}px; '
            f'line-height:{alto}; color:{color};{extra}">{texto}</p>')


def antetitulo(texto, color=ACENTO):
    return p(escape(texto.upper()), tam=12, color=color, alto=1.4, abajo=8,
             extra=" font-weight:700; letter-spacing:2px;")


def titulo2(texto, color=VERDEOSCURO):
    return (f'<h2 style="margin:0 0 14px 0; font-family:{LETRA}; font-size:23px; '
            f'line-height:1.25; font-weight:600; color:{color};">{texto}</h2>')


def enlace(url, texto, color=ACENTO, extra=""):
    return (f'<a href="{url}" style="color:{color}; text-decoration:none;{extra}">{texto}</a>')


def boton(url, texto, fondo, color, borde=None):
    borde = borde or fondo
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            f'style="display:inline-table; margin:0 8px 12px 0;"><tr>'
            f'<td bgcolor="{fondo}" style="background-color:{fondo}; border:1px solid {borde}; '
            f'border-radius:4px;">'
            f'<a href="{url}" style="display:inline-block; padding:12px 22px; font-family:{LETRA}; '
            f'font-size:15px; font-weight:700; line-height:1.2; color:{color}; '
            f'text-decoration:none;">{texto}</a></td></tr></table>')


def fila(contenido, fondo="#FFFFFF", relleno="36px 40px"):
    return (f'<tr><td bgcolor="{fondo}" style="background-color:{fondo}; padding:{relleno};">'
            f"{contenido}</td></tr>\n")


def imagen(src, ancho, alto, alt, url=None):
    img = (f'<img src="{src}" width="{ancho}" height="{alto}" alt="{escape(alt)}" '
           f'style="display:block; width:100%; max-width:{ancho}px; height:auto; border:0; '
           f'outline:none; text-decoration:none; font-family:{LETRA}; font-size:14px; '
           f'color:{VERDEOSCURO};">')
    return f'<a href="{url}" style="text-decoration:none;">{img}</a>' if url else img


def estados_y_ecos(agenda, foro):
    """Los estados con conciertos (sin la CDMX) y los ecos, con sus fechas."""
    estados, ecos = [], {}
    for d in agenda:
        for e in d["eventos"]:
            estado = next((n for n in foro["estados_nombres"] if e["lugar"].endswith(n)), None)
            if e["seccion"] == "estados" and estado and estado not in estados:
                estados.append(estado)
            elif e["seccion"] == "ecos" and estado:
                ecos.setdefault(estado, []).append(f"{d['numero']} de {d['mes']}")
    return sorted(estados), ecos


def armar_html(agenda, foro, abono, destacados, url, imgs):
    """imgs: nombre de la imagen → src (ruta relativa, data: o cid:)."""
    estados, ecos = estados_y_ecos(agenda, foro)
    filas = []

    # Encabezado
    filas.append(fila(imagen(imgs["encabezado.jpg"], 600, 280,
                             f"{TITULO} · Noviembre 6 al 21, 2026", url + "/"), relleno="0"))

    # Invitación
    texto_ecos = unir([f"{estado} ({unir(fechas)})" for estado, fechas in ecos.items()])
    filas.append(fila(
        antetitulo(f"Del {foro['fechas']}")
        + f'<h1 style="margin:0 0 20px 0; font-family:{LETRA}; font-size:27px; line-height:1.25; '
          f'font-weight:600; color:{VERDEOSCURO};">Les invitamos al {escape(TITULO)}</h1>'
        + p("Querida comunidad del Foro:")
        + p(f"Del 6 al 21 de noviembre, la música de nuestro tiempo suena en la Ciudad de "
            f"México y en {escape(unir(estados))}, con ecos en {escape(texto_ecos)}. Este año "
            f"celebramos además el centenario de Manuel Enríquez (1926-1994), el compositor "
            f"que da nombre al Foro, con un coloquio y conciertos dedicados a su obra.")
        + p("Gracias a quienes hacen posible esta edición: intérpretes, compositoras y "
            "compositores, ponentes, sedes y equipos de trabajo. Les invitamos a acompañarnos y "
            "a compartir esta invitación con sus amistades.", abajo=18)
        + p("Coordinación Nacional de Música y Ópera", tam=15, abajo=0,
            extra=" font-weight:600;"),
        relleno="36px 40px 34px"))

    # Cifras
    cifras = [(foro["conciertos"], "conciertos"), (foro["obras"], "obras interpretadas"),
              (foro["mundiales"], "estrenos mundiales"), (foro["mexico"], "estrenos en México"),
              (foro["actividades"] + foro["coloquio"], "actividades académicas"),
              (foro["sedes"], f"sedes en {len(foro['estados'])} entidades")]
    celdas = [f'<td width="33%" align="center" valign="top" style="padding:12px 6px;">'
              f'<div style="font-family:{LETRA}; font-size:32px; line-height:1.1; font-weight:700; '
              f'color:{ACENTO};">{n}</div>'
              f'<div style="font-family:{LETRA}; font-size:13px; line-height:1.35; color:{VERDEGRIS}; '
              f'padding-top:4px;">{escape(t)}</div></td>' for n, t in cifras]
    filas.append(fila(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>{"".join(celdas[:3])}</tr><tr>{"".join(celdas[3:])}</tr></table>',
        fondo=BEIGE, relleno="22px 28px"))

    # Inauguración y clausura
    columnas = []
    for k, (clave, e) in enumerate(destacados.items()):
        d = e["_dia"]
        relleno = "0 12px 0 0" if k == 0 else "0 0 0 12px"
        columnas.append(
            f'<td width="50%" valign="top" style="padding:{relleno};">'
            + imagen(imgs[f"postal-{clave}.jpg"], 248, 310,
                     f"Postal: {e['subtitulo']}, {d['dia']}, {hora(e)}", url + e["url"])
            + '<div style="height:14px; line-height:14px; font-size:14px;">&nbsp;</div>'
            + p(escape(f"{d['dia']} · {hora(e)}"), tam=13, color=ACENTO, alto=1.4, abajo=4,
                extra=" font-weight:700;")
            + p(enlace(url + e["url"], escape(e["subtitulo"]), color=VERDEOSCURO), tam=18,
                alto=1.3, abajo=6, extra=" font-weight:600;")
            + p(escape(e["interpretes"]), tam=14, alto=1.45, abajo=6)
            + p(escape(e["obras"]), tam=13, color=VERDEGRIS, alto=1.45, abajo=4)
            + (p(escape(e["estrenos"].capitalize() if e["estrenos"][0].islower() else e["estrenos"]),
                 tam=13, color=VERDEGRIS, alto=1.45, abajo=0) if e["estrenos"] else "")
            + "</td>")
    precios = " · ".join(abono["precios"])
    filas.append(fila(
        antetitulo(abono["sede"])
        + titulo2("Inauguración y clausura")
        + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
          f'<tr>{"".join(columnas)}</tr></table>',
        relleno="36px 40px 24px"))
    filas.append(fila(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td bgcolor="{PORTADABASE}" style="background-color:{PORTADABASE}; padding:20px 24px; '
        f'border-radius:4px;">'
        + p(escape(ABONO), tam=15, color=DORADO, alto=1.3, abajo=4, extra=" font-weight:700;")
        + p(escape(precios), tam=24, color=DORADO, alto=1.25, abajo=8, extra=" font-weight:700;")
        + p(escape(f"{abono['sede']} · {abono['direccion']}"), tam=13, color=SUAVE, alto=1.45,
            abajo=16 if abono.get("boletos") else 0)
        + (boton(escape(abono["boletos"]), "Comprar el abono", DORADO, VERDEOSCURO)
           if abono.get("boletos") else "")
        + "</td></tr></table>",
        relleno="0 40px 36px"))

    # Coloquio Manuel Enríquez 100
    sesiones, conciertos_enriquez = [], []
    for d in agenda:
        del_dia = [e for e in d["eventos"] if e["seccion"] == "coloquio"]
        if del_dia:
            sesiones.append((d, del_dia))
        conciertos_enriquez += [(d, e) for e in d["eventos"]
                                if e["tipo"] == "concierto" and "Enríquez 100" in e["titulo"].replace("\xa0", " ")]
    bloque = ""
    for d, eventos in sesiones:
        sedes = unir(sorted({e["lugar"] for e in eventos}))
        bloque += p(escape(f"{d['dia']} · {sedes}"), tam=14, color=TEAL, alto=1.4, abajo=6,
                    extra=" font-weight:700;")
        bloque += ('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                   'border="0" style="margin:0 0 16px 0;">')
        for e in eventos:
            bloque += (f'<tr><td width="58" valign="top" style="padding:3px 0; font-family:{LETRA}; '
                       f'font-size:14px; line-height:1.45; color:{VERDEOSCURO}; white-space:nowrap;">'
                       f'{escape(hora(e))}</td><td valign="top" style="padding:3px 0; '
                       f'font-family:{LETRA}; font-size:14px; line-height:1.45;">'
                       f'{enlace(url + e["url"], e["titulo_html"], color=VERDEOSCURO)}</td></tr>')
        bloque += "</table>"
    en_concierto = unir([
        f'{enlace(url + e["url"], e["titulo_html"], color=TEAL, extra=" font-weight:600;")} '
        f'({escape(d["semana"].lower())} {d["numero"]}, {escape(hora(e))}, '
        f'{escape(e["lugar"])})' for d, e in conciertos_enriquez])
    filas.append(fila(
        antetitulo(f"{sesiones[0][0]['numero']} y {sesiones[-1][0]['numero']} de "
                   f"{sesiones[-1][0]['mes']}", color=TEAL)
        + titulo2("Coloquio Manuel Enríquez 100")
        + p("Dos jornadas de conferencias y mesas para pensar la obra y la figura de Manuel "
            "Enríquez a cien años de su nacimiento.", abajo=20)
        + bloque
        + p(f"Y en concierto: {en_concierto}.", tam=14, alto=1.55, abajo=20)
        + boton(url + "/coloquio/", "Programa del Coloquio", TEAL, "#FFFFFF"),
        fondo=TEALCLARO, relleno="36px 40px 26px"))

    # Programación día por día
    dias = ""
    for d in agenda:
        dias += (f'<tr><td colspan="2" style="padding:22px 0 6px 0; border-bottom:1px solid {FILETE}; '
                 f'font-family:{LETRA}; font-size:12px; line-height:1.4; font-weight:700; '
                 f'letter-spacing:2px; color:{ACENTO};">{escape(d["dia"].upper())}</td></tr>')
        for e in d["eventos"]:
            seccion = {"coloquio": "Coloquio Manuel Enríquez 100 · ",
                       "actividades": "Actividad académica · ",
                       "ecos": "Ecos del Foro · "}.get(e["seccion"], "")
            dias += (f'<tr><td width="64" valign="top" style="padding:10px 0 0 0; font-family:{LETRA}; '
                     f'font-size:14px; line-height:1.4; font-weight:700; color:{VERDEOSCURO}; '
                     f'white-space:nowrap;">{escape(hora(e))}</td>'
                     f'<td valign="top" style="padding:10px 0 0 0;">'
                     + p(enlace(url + e["url"], e["titulo_html"], extra=" font-weight:600;"),
                         tam=15, alto=1.35, abajo=2)
                     + p(escape(seccion + e["lugar"]), tam=13, color=VERDEGRIS, alto=1.4, abajo=0)
                     + "</td></tr>")
    primero, ultimo = agenda[0], agenda[-1]
    filas.append(fila(
        antetitulo(f"Del {primero['numero']} de {primero['mes']} al {ultimo['numero']} de "
                   f"{ultimo['mes']}")
        + titulo2("Programación día por día")
        + p(f"{ENTRADA}, salvo la inauguración y la clausura (abono). Cada título lleva a su "
            "página en el sitio del Foro, con el programa, las semblanzas y las notas.",
            tam=14, color=VERDEGRIS, alto=1.55, abajo=4)
        + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        + dias + "</table>",
        relleno="36px 40px 40px"))

    # Cierre: banda verde y pie
    filas.append(fila(
        titulo2("Comparte el Foro", color=CASIBLANCO)
        + p("Cada evento tiene su postal para redes sociales, que se puede descargar en su "
            "página del sitio o en Descargas, junto con el programa de mano y el programa "
            "resumido.", color=SUAVE, abajo=22)
        + boton(url + "/programacion/", "Programación", DORADO, VERDEOSCURO)
        + boton(url + "/descargas/", "Descargas", VERDEPIE, CASIBLANCO, borde=SUAVE)
        + p(f"Recibes este correo porque participas en el {escape(TITULO)} o formas parte de su "
            "comunidad. Si prefieres no recibir más mensajes, basta con responder a este correo.",
            tam=12, color="#B9C7B3", alto=1.5, abajo=0, extra=" padding-top:14px;"),
        fondo=VERDEPIE, relleno="36px 40px 0"))
    filas.append(fila(imagen(imgs["pie.png"], 600, 185,
                             "Coordinación Nacional de Música y Ópera · Cultura, Secretaría de "
                             "Cultura · INBAL 80 aniversario"),
                      fondo=VERDEPIE, relleno="0"))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>{escape(TITULO)}</title>
</head>
<body style="margin:0; padding:0; background-color:{EXTERIOR};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{EXTERIOR}" style="background-color:{EXTERIOR};">
<tr><td align="center" style="padding:24px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%; max-width:600px; background-color:#FFFFFF;">
{"".join(filas)}</table>
</td></tr>
</table>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Texto (la versión sin formato del .eml)
# -----------------------------------------------------------------------------
def armar_texto(agenda, foro, abono, destacados, url):
    estados, ecos = estados_y_ecos(agenda, foro)
    texto_ecos = unir([f"{estado} ({unir(fechas)})" for estado, fechas in ecos.items()])
    t = [TITULO.upper(), f"Del {foro['fechas']}", "",
         "Querida comunidad del Foro:", "",
         f"Del 6 al 21 de noviembre, la música de nuestro tiempo suena en la Ciudad de México y en "
         f"{unir(estados)}, con ecos en {texto_ecos}. Este año celebramos además el centenario de "
         f"Manuel Enríquez (1926-1994), el compositor que da nombre al Foro, con un coloquio y "
         f"conciertos dedicados a su obra.", "",
         "Gracias a quienes hacen posible esta edición: intérpretes, compositoras y compositores, "
         "ponentes, sedes y equipos de trabajo. Les invitamos a acompañarnos y a compartir esta "
         "invitación con sus amistades.", "",
         "Coordinación Nacional de Música y Ópera", "",
         f"{foro['conciertos']} conciertos · {foro['obras']} obras interpretadas · "
         f"{foro['mundiales']} estrenos mundiales · {foro['mexico']} estrenos en México · "
         f"{foro['actividades'] + foro['coloquio']} actividades académicas · {foro['sedes']} sedes "
         f"en {len(foro['estados'])} entidades", "",
         "INAUGURACIÓN Y CLAUSURA", ""]
    for e in destacados.values():
        t += [f"{e['_dia']['dia']} · {hora(e)} · {e['subtitulo']}", e["interpretes"], e["obras"],
              url + e["url"], ""]
    t += [f"{ABONO}: {' · '.join(abono['precios'])}",
          f"{abono['sede']} · {abono['direccion']}"]
    if abono.get("boletos"):
        t.append(f"Compra del abono: {abono['boletos']}")
    t += ["",
          "PROGRAMACIÓN DÍA POR DÍA", f"{ENTRADA}, salvo la inauguración y la clausura (abono).", ""]
    for d in agenda:
        t.append(d["dia"].upper())
        for e in d["eventos"]:
            titulo = re.sub(r"</?em>", "", e["titulo_html"]).replace("&amp;", "&")
            t.append(f"  {hora(e)}  {titulo} · {e['lugar']}")
        t.append("")
    t += [f"Programación: {url}/programacion/", f"Coloquio Manuel Enríquez 100: {url}/coloquio/",
          f"Descargas (programa de mano, programa resumido y postales): {url}/descargas/", "",
          f"Recibes este correo porque participas en el {TITULO} o formas parte de su comunidad. "
          "Si prefieres no recibir más mensajes, basta con responder a este correo."]
    return "\n".join(t) + "\n"


# -----------------------------------------------------------------------------
def tipo_de(nombre):
    return ("image", "png") if nombre.endswith(".png") else ("image", "jpeg")


def escribir_si_cambia(destino, contenido):
    datos = contenido.encode("utf-8") if isinstance(contenido, str) else contenido
    if not destino.exists() or destino.read_bytes() != datos:
        destino.write_bytes(datos)


def main():
    agenda = leer_json("agenda.json")
    foro = leer_json("foro.json")
    abono = leer_json("abono.json")
    abono["boletos"] = config("abono_boletos")
    url = sitio_url()
    destacados = {}
    for d in agenda:
        for e in d["eventos"]:
            for clave, inicio in (("inauguracion", "INAUGURACIÓN"), ("clausura", "CLAUSURA")):
                if e["titulo"].startswith(inicio):
                    destacados[clave] = dict(e, _dia=d)
    imagenes(destacados)
    nombres = sorted(f.name for f in IMG.iterdir())

    # con las imágenes de img/
    html = armar_html(agenda, foro, abono, destacados, url, {n: f"img/{n}" for n in nombres})
    escribir_si_cambia(AQUI / f"{NOMBRE}.html", html)

    # con las imágenes dentro (para copiar y pegar en Outlook en la web)
    datos = {n: "data:{}/{};base64,{}".format(*tipo_de(n),
                                               base64.b64encode((IMG / n).read_bytes()).decode())
             for n in nombres}
    escribir_si_cambia(AQUI / f"{NOMBRE}-outlook.html",
                       armar_html(agenda, foro, abono, destacados, url, datos))

    # mensaje sin enviar (.eml): imágenes en línea (cid:) y versión en texto
    cids = {n: f"{Path(n).stem}@fimnme2026" for n in nombres}
    msg = EmailMessage(policy=SMTP)
    msg["Subject"] = ASUNTO
    msg["X-Unsent"] = "1"   # Outlook de escritorio lo abre como mensaje nuevo, listo para enviar
    msg.set_content(armar_texto(agenda, foro, abono, destacados, url))
    msg.add_alternative(armar_html(agenda, foro, abono, destacados, url,
                                   {n: f"cid:{c}" for n, c in cids.items()}), subtype="html")
    parte_html = msg.get_payload()[1]
    for n in nombres:
        principal, sub = tipo_de(n)
        parte_html.add_related((IMG / n).read_bytes(), maintype=principal, subtype=sub,
                               cid=f"<{cids[n]}>", filename=n, disposition="inline")
    # separadores fijos (derivados del contenido): si nada cambia, el .eml tampoco
    firma = hashlib.sha1(html.encode("utf-8")).hexdigest()[:16]
    for k, parte in enumerate(p for p in msg.walk() if p.is_multipart()):
        parte.set_boundary(f"==fimnme2026-{k}-{firma}==")
    escribir_si_cambia(AQUI / f"{NOMBRE}.eml", msg.as_bytes())

    peso = (AQUI / f"{NOMBRE}-outlook.html").stat().st_size / 1024
    print(f"  Boletín: {sum(len(d['eventos']) for d in agenda)} eventos; versión para Outlook "
          f"de {peso:.0f} KB; enlaces a {url}")


if __name__ == "__main__":
    main()
