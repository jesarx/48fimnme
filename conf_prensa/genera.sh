#!/usr/bin/env bash
# Numeralia para la conferencia de prensa del 48º FIMNME: compila el PDF a
# partir de conf_prensa/numeralia.md (la fuente; las cifras se actualizan ahí).
#
#   conf_prensa/genera.sh
#
# Requisitos: pandoc (≥ 3.1) y LuaLaTeX (TeX Live ≥ 2023).

set -euo pipefail
cd "$(dirname "$0")/.."

NOMBRE=numeralia
mkdir -p build/conf_prensa

pandoc "conf_prensa/$NOMBRE.md" \
  --from markdown \
  --template=conf_prensa/numeralia.latex \
  --metadata pagetitle="48º FIMNME · Numeralia para la conferencia de prensa" \
  --wrap=none \
  -o "build/conf_prensa/$NOMBRE.tex"

lualatex --interaction=nonstopmode --halt-on-error \
  --output-directory=build/conf_prensa "build/conf_prensa/$NOMBRE.tex" \
  > "build/conf_prensa/$NOMBRE.salida" 2>&1 || {
    echo "✗ Error de LuaLaTeX; últimas líneas de build/conf_prensa/$NOMBRE.log:"
    tail -n 30 "build/conf_prensa/$NOMBRE.log"
    exit 1
  }

cp "build/conf_prensa/$NOMBRE.pdf" "conf_prensa/$NOMBRE.pdf"
paginas=$(pdfinfo "conf_prensa/$NOMBRE.pdf" 2>/dev/null | awk '/^Pages/{print $2}')
echo "✓ Listo: conf_prensa/$NOMBRE.pdf ($paginas páginas)"
