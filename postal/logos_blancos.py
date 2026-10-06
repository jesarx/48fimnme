#!/usr/bin/env python3
"""Logotipos en blanco para la postal (van sobre el fondo verde).

Toma los logotipos ya preparados por automatizacion/preparar_logos.py
(build/logos/*.png, un solo color con transparencia) y deja copias en blanco
en build/postal/. Cuáles: los de LOGOS, por su ruta en el Markdown (la
misma clave que en build/logos/manifiesto.tsv).
"""

from pathlib import Path

from PIL import Image

MANIFIESTO = Path("build/logos/manifiesto.tsv")
DESTINO = Path("build/postal")
LOGOS = {
    "osn": "logos/logos%20OSN/OSN-1.png|",
    "patronato": "logos/logos%20OSN/Logo-Patronato%20Industria%20Alemana%20Cultura.PNG|",
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for linea in MANIFIESTO.read_text().splitlines():
        partes = linea.split("\t")
        if len(partes) == 4:
            rutas[partes[0]] = partes[1]
    for nombre, clave in LOGOS.items():
        alfa = Image.open(rutas[clave]).convert("RGBA").getchannel("A")
        blanco = Image.new("RGBA", alfa.size, (255, 255, 255, 0))
        blanco.putalpha(alfa)
        blanco.save(DESTINO / f"{nombre}-blanco.png", optimize=True)


if __name__ == "__main__":
    main()
