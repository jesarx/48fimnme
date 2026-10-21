#!/usr/bin/env python3
"""Fecha de compilación en el nombre de las postales.

Cada postal lleva al final del nombre el día en que se compiló, corto y en
español: fimnme2026-postal-jue-nov-19-ocba_20oct.png. Así, quien descarga
las postales del repositorio ve de qué compilación es cada archivo. Al
compilar una postal se borran sus versiones anteriores (las de otras fechas).

La fecha es la de la Ciudad de México. compila.sh la fija una sola vez
(variable FECHA_POSTALES) para que todas las postales de una compilación
lleven la misma, aunque pase la medianoche.

    python3 postales/fecha.py                  imprime la fecha (p. ej. «20oct»)
    python3 postales/fecha.py limpiar <base>   borra las versiones de otras fechas
"""

import datetime
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

SALIDA = Path(__file__).resolve().parent          # postales/
FORMATOS = ("png", "jpg", "pdf", "idml")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def fecha():
    """«20oct»: la de FECHA_POSTALES o, si no está, la de hoy en la Ciudad de México."""
    if os.environ.get("FECHA_POSTALES"):
        return os.environ["FECHA_POSTALES"]
    hoy = datetime.datetime.now(ZoneInfo("America/Mexico_City"))
    return f"{hoy.day}{MESES[hoy.month - 1]}"


def nombre(base):
    """fimnme2026-postal-<evento> → fimnme2026-postal-<evento>_20oct"""
    return f"{base}_{fecha()}"


def _versiones(carpeta, base, ext):
    """Los archivos de una postal en una carpeta: con fecha o sin ella (los de antes)."""
    patron = re.compile(re.escape(base) + r"(_\d{1,2}[a-z]{3})?\." + ext + "$")
    return [f for f in Path(carpeta).glob(f"{base}*.{ext}") if patron.match(f.name)]


def buscar(carpeta, base, ext):
    """El archivo vigente de una postal (el más reciente, si quedara más de uno)."""
    versiones = _versiones(carpeta, base, ext)
    return max(versiones, key=lambda f: f.stat().st_mtime) if versiones else None


def limpiar(base):
    """Borra las versiones de una postal que no son de la fecha de esta compilación."""
    vigente = nombre(base)
    for ext in FORMATOS:
        for f in _versiones(SALIDA / ext, base, ext):
            if f.stem != vigente:
                f.unlink()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "limpiar":
        limpiar(sys.argv[2])
    else:
        print(fecha())
