#!/usr/bin/env bash
# Compila la postal para la venta de boletos del 48.º FIMNME (inauguración y
# clausura) y la exporta en PNG de 1080 × 1350 px.
#
#   postal/compila.sh
#
# Requisitos: LuaLaTeX, Python 3 con Pillow y pdftoppm (poppler). Usa los
# logotipos que prepara automatizacion/preparar_logos.py.

set -euo pipefail
cd "$(dirname "$0")/.."

NOMBRE=fimnme2026-postal-boletos
mkdir -p build/postal

[ -f build/logos/manifiesto.tsv ] || python3 automatizacion/preparar_logos.py
python3 postal/logos_blancos.py

for pasada in 1 2; do   # dos pasadas: las posiciones de TikZ (remember picture)
  lualatex --interaction=nonstopmode --halt-on-error --jobname="$NOMBRE" \
    --output-directory=build/postal postal/postal.tex > build/postal/salida.log 2>&1 || {
      echo "✗ Error de LuaLaTeX; últimas líneas de build/postal/$NOMBRE.log:"
      tail -n 30 "build/postal/$NOMBRE.log"
      exit 1
    }
done

cp "build/postal/$NOMBRE.pdf" "postal/$NOMBRE.pdf"
# 108 × 135 mm a 254 ppp = 1080 × 1350 px
pdftoppm -png -scale-to-x 1080 -scale-to-y 1350 -singlefile "postal/$NOMBRE.pdf" "postal/$NOMBRE"
tamano=$(python3 -c "from PIL import Image; print('×'.join(map(str, Image.open('postal/$NOMBRE.png').size)))")
echo "✓ Listo: postal/$NOMBRE.png ($tamano px) y postal/$NOMBRE.pdf"
