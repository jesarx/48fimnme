#!/usr/bin/env python3
"""Copias ligeras de los logotipos para la página final del Programa resumido.

Toma los logotipos ya preparados por automatizacion/preparar_logos.py
(build/logos/*.png, un solo color con transparencia) y los guarda en
build/resumen/logos/ a la resolución justa para su tamaño en la página
(unos 300 ppp) y con una paleta de 16 niveles de transparencia del mismo
verde. Así la página de logotipos apenas aumenta el peso del PDF.
"""

from pathlib import Path

from PIL import Image

ORIGEN = Path("build/logos")
DESTINO = Path("build/resumen/logos")
COLOR = (0x17, 0x2B, 0x20)   # verdeoscuro de la plantilla
ALTO_MAX, ANCHO_MAX = 110, 310   # px: ~9 × 26 mm (el máximo en la página) a 300 ppp
NIVELES = 16


def reducir(origen: Path, destino: Path) -> None:
    alfa = Image.open(origen).convert("RGBA").getchannel("A")
    escala = min(1.0, ALTO_MAX / alfa.height, ANCHO_MAX / alfa.width)
    if escala < 1:
        alfa = alfa.resize((max(1, round(alfa.width * escala)),
                            max(1, round(alfa.height * escala))), Image.LANCZOS)
    # índice de paleta = nivel de transparencia; todos los colores, el verde
    paso = 255 / (NIVELES - 1)
    indices = alfa.point(lambda v: round(v / paso))
    img = Image.frombytes("P", alfa.size, indices.tobytes())
    img.putpalette(list(COLOR) * NIVELES)
    transparencia = bytes(round(k * paso) for k in range(NIVELES))
    img.save(destino, optimize=True, transparency=transparencia)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for origen in sorted(ORIGEN.glob("*.png")):
        destino = DESTINO / origen.name
        if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
            continue
        reducir(origen, destino)


if __name__ == "__main__":
    main()
