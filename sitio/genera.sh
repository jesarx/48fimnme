#!/usr/bin/env bash
# Genera el sitio web del 48.º FIMNME a partir del mismo Markdown que el
# Programa general (fimnme2026-programa.md) y lo compila con Jekyll.
#
#   sitio/genera.sh              contenido, recursos y compilación (sitio/_site)
#   sitio/genera.sh --servir     además lo sirve en http://localhost:4000
#   sitio/genera.sh --contenido  solo regenera el contenido (sin Jekyll)
#
# Requisitos: pandoc (≥ 3.1), Python 3 con Pillow, NumPy y PyMuPDF; para
# compilar, Ruby con Jekyll 4 (cd sitio && bundle install).
#
# Lo generado (sitio/_conciertos, sitio/_data, sitio/_includes/generado,
# sitio/assets/fotos y logos, sitio/descargas) se guarda en el repositorio:
# así el sitio se puede compilar solo con Jekyll, sin pandoc ni LaTeX.

set -euo pipefail
cd "$(dirname "$0")/.."

# fotos y logotipos: los mismos que prepara el Programa general
[ -f build/fotos/manifiesto.tsv ] || python3 automatizacion/preparar_imagenes.py
[ -f build/logos/manifiesto.tsv ] || python3 automatizacion/preparar_logos.py

echo "▸ Sitio: contenido desde fimnme2026-programa.md…"
pandoc fimnme2026-programa.md \
  --from markdown \
  --metadata-file=fimnme2026-programa.yaml \
  --lua-filter=sitio/sitio.lua \
  -t plain -o /dev/null

echo "▸ Sitio: fotos, logotipos y descargas…"
python3 sitio/recursos.py

[[ "${1:-}" == "--contenido" ]] && exit 0

cd sitio
# Jekyll del Gemfile (bundle install) o, si no, el que esté instalado
if command -v bundle > /dev/null && bundle exec jekyll --version > /dev/null 2>&1; then
  JEKYLL=(bundle exec jekyll)
elif command -v jekyll > /dev/null; then
  JEKYLL=(jekyll)
else
  echo "⚠ No se encontró Jekyll (se instala con «cd sitio && bundle install»)."
  echo "  El contenido del sitio ya está al día; falta compilarlo con «jekyll build» en sitio/."
  exit 0
fi

if [[ "${1:-}" == "--servir" ]]; then
  "${JEKYLL[@]}" serve --livereload
else
  "${JEKYLL[@]}" build --quiet
  paginas=$(find _site -name '*.html' | wc -l)
  echo "✓ Listo: sitio/_site ($paginas páginas HTML)"
fi
