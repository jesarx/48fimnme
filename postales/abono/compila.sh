#!/usr/bin/env bash
# Compila la postal para la venta del abono del 48º FIMNME (inauguración y
# clausura) y la exporta en PNG y JPG de 1080 × 1350 px, en PDF y en IDML
# editable.
#
#   postales/abono/compila.sh
#
# Salida: postales/png, jpg, pdf e idml/fimnme2026-postal-abono_<fecha>.*, con
# la fecha de compilación al final del nombre (p. ej. «_20oct»; ver postales/fecha.py).
#
# Requisitos: LuaLaTeX, Python 3 con Pillow y PyMuPDF, y pdftoppm (poppler). Usa los
# logotipos que prepara automatizacion/preparar_logos.py.

set -euo pipefail
cd "$(dirname "$0")/../.."

NOMBRE=fimnme2026-postal-abono
SALIDA="${NOMBRE}_$(python3 postales/fecha.py)"   # con la fecha de compilación
mkdir -p build/postal

[ -f build/logos/manifiesto.tsv ] || python3 automatizacion/preparar_logos.py
python3 postales/abono/logos_blancos.py

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
compila "$NOMBRE" postales/abono/abono.tex
# el fondo solo (verde, partitura y franja), para el IDML
compila fondo '\def\solofondo{}\input{postales/abono/abono.tex}'

mkdir -p postales/png postales/jpg postales/pdf postales/idml
cp "build/postal/$NOMBRE.pdf" "postales/pdf/$SALIDA.pdf"
# 108 × 135 mm a 254 ppp = 1080 × 1350 px
pdftoppm -png -scale-to-x 1080 -scale-to-y 1350 -singlefile "postales/pdf/$SALIDA.pdf" "postales/png/$SALIDA"
# JPG (pesa mucho menos; el que usa el sitio)
python3 -c "from PIL import Image; Image.open('postales/png/$SALIDA.png').convert('RGB').save('postales/jpg/$SALIDA.jpg', quality=90, optimize=True, progressive=True)"
# IDML editable (InDesign): fondo, recuadros, logotipos y textos en Noto Sans
python3 postales/idml_editable.py "postales/pdf/$SALIDA.pdf" build/postal/fondo.pdf postales/abono/abono.tex \
  "postales/idml/$SALIDA.idml" "48º FIMNME · Postal del abono"
python3 postales/fecha.py limpiar "$NOMBRE"   # sin las versiones de compilaciones anteriores
python3 -c "import sys; sys.path.insert(0, 'postales'); import idml_editable; idml_editable.preparar_paquete('postales/idml')"
tamano=$(python3 -c "from PIL import Image; print('×'.join(map(str, Image.open('postales/png/$SALIDA.png').size)))")
echo "✓ Listo: postales/png/$SALIDA.png ($tamano px), y en postales/jpg, pdf e idml"
