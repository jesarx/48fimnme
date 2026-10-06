#!/usr/bin/env bash
# Compila el Programa resumido del 48.º FIMNME a partir del mismo Markdown
# que el Programa general (no usa fotos: pesa poco y compila en segundos).
#
#   resumen/compila.sh
#
# Requisitos: pandoc (≥ 3.1) y LuaLaTeX (TeX Live ≥ 2023).

set -euo pipefail
cd "$(dirname "$0")/.."

NOMBRE=fimnme2026-resumen
mkdir -p build/resumen

pandoc fimnme2026-programa.md \
  --from markdown \
  --template=resumen/resumen.latex \
  --lua-filter=resumen/resumen.lua \
  --wrap=none \
  -o "build/resumen/$NOMBRE.tex"

for pasada in 1 2; do
  lualatex --interaction=nonstopmode --halt-on-error \
    --output-directory=build/resumen "build/resumen/$NOMBRE.tex" \
    > "build/resumen/$NOMBRE.salida" 2>&1 || {
      echo "✗ Error de LuaLaTeX; últimas líneas de build/resumen/$NOMBRE.log:"
      tail -n 30 "build/resumen/$NOMBRE.log"
      exit 1
    }
done

cp "build/resumen/$NOMBRE.pdf" "resumen/$NOMBRE.pdf"
paginas=$(pdfinfo "resumen/$NOMBRE.pdf" 2>/dev/null | awk '/^Pages/{print $2}')
peso=$(du -k "resumen/$NOMBRE.pdf" | cut -f1)
echo "✓ Listo: resumen/$NOMBRE.pdf ($paginas páginas, $peso KB)"
