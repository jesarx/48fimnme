#!/usr/bin/env bash
# Compila la postal para la venta del abono del 48.º FIMNME (inauguración y
# clausura) y la exporta en PNG de 1080 × 1350 px, en PDF y en IDML editable.
#
#   postal/compila.sh
#
# Requisitos: LuaLaTeX, Python 3 con Pillow y PyMuPDF, y pdftoppm (poppler). Usa los
# logotipos que prepara automatizacion/preparar_logos.py.

set -euo pipefail
cd "$(dirname "$0")/.."

NOMBRE=fimnme2026-postal-abono
mkdir -p build/postal

[ -f build/logos/manifiesto.tsv ] || python3 automatizacion/preparar_logos.py
python3 postal/logos_blancos.py

# compila JOB ENTRADA (dos pasadas: las posiciones de TikZ, remember picture)
compila() {
  for pasada in 1 2; do
    lualatex --interaction=nonstopmode --halt-on-error --jobname="$1" \
      --output-directory=build/postal "$2" > build/postal/salida.log 2>&1 || {
        echo "✗ Error de LuaLaTeX; últimas líneas de build/postal/$1.log:"
        tail -n 30 "build/postal/$1.log"
        exit 1
      }
  done
}
compila "$NOMBRE" postal/postal.tex
# el fondo solo (verde, partitura y franja), para el IDML
compila fondo '\def\solofondo{}\input{postal/postal.tex}'

cp "build/postal/$NOMBRE.pdf" "postal/$NOMBRE.pdf"
# 108 × 135 mm a 254 ppp = 1080 × 1350 px
pdftoppm -png -scale-to-x 1080 -scale-to-y 1350 -singlefile "postal/$NOMBRE.pdf" "postal/$NOMBRE"
# IDML editable (InDesign): fondo, recuadros, logotipos y textos en Noto Sans
python3 postal/idml_editable.py "postal/$NOMBRE.pdf" build/postal/fondo.pdf postal/postal.tex \
  "postal/$NOMBRE.idml" "48.º FIMNME · Postal del abono"
tamano=$(python3 -c "from PIL import Image; print('×'.join(map(str, Image.open('postal/$NOMBRE.png').size)))")
echo "✓ Listo: postal/$NOMBRE.png ($tamano px), .pdf e .idml (editable)"
