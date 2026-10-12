#!/usr/bin/env bash
# Genera el sitio web del 48º FIMNME a partir del mismo Markdown que el
# Programa general (fimnme2026-programa.md) y lo compila con Jekyll.
#
#   sitio/genera.sh              contenido, recursos y compilación (sitio/_site)
#   sitio/genera.sh --servir     además lo sirve en http://localhost:4000/2026/
#   sitio/genera.sh --contenido  solo regenera el contenido (sin Jekyll)
#   sitio/genera.sh --compilar   solo compila (el contenido ya está generado)
#
# Requisitos: pandoc (≥ 3.1), Python 3 con Pillow, NumPy, PyMuPDF y PyYAML;
# para compilar, Ruby con Jekyll 4 y la gema rqrcode_core de los códigos QR
# (cd sitio && bundle install).
#
# Lo generado (sitio/_conciertos, sitio/_data, sitio/_includes/generado,
# sitio/assets/fotos, logos y postales, sitio/descargas, sitio/postales) se
# guarda en el repositorio: así el sitio se puede compilar solo con Jekyll,
# sin pandoc ni LaTeX. Los QR de la página de descargas los genera Jekyll al
# compilar (_plugins/qr.rb), con la dirección de _config.yml.
#
# Las direcciones llevan el año de la edición (baseurl de _config.yml, p. ej.
# «/2026»): el sitio se compila en sitio/_site/2026/ y en sitio/_site/ quedan
# una página que redirige a esa edición y el robots.txt.

set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" != "--compilar" ]]; then
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
fi

[[ "${1:-}" == "--contenido" ]] && exit 0

cd sitio
# Jekyll del Gemfile (bundle install) o, si no, el que esté instalado
if command -v bundle > /dev/null && bundle exec jekyll --version > /dev/null 2>&1; then
  JEKYLL=(bundle exec jekyll)
elif command -v jekyll > /dev/null; then
  JEKYLL=(jekyll)
elif [[ -n "${1:-}" ]]; then   # --compilar o --servir: sin Jekyll no se puede
  echo "✗ No se encontró Jekyll (se instala con «cd sitio && bundle install»; ver DESPLIEGUE.md)."
  exit 1
else
  echo "⚠ No se encontró Jekyll (se instala con «cd sitio && bundle install»)."
  echo "  El contenido del sitio ya está al día; falta compilarlo con «sitio/genera.sh --compilar»."
  exit 0
fi

BASEURL=$(sed -nE 's/^baseurl: *"?([^"]*)"?.*/\1/p' _config.yml)

if [[ "${1:-}" == "--servir" ]]; then
  "${JEKYLL[@]}" serve --livereload
  exit 0
fi

rm -rf _site
JEKYLL_ENV=production "${JEKYLL[@]}" build --quiet -d "_site${BASEURL}"
if [[ -n "$BASEURL" ]]; then
  # en la raíz del dominio: redirección a esta edición y robots.txt
  cp "_site${BASEURL}/robots.txt" _site/robots.txt
  cat > _site/index.html <<HTML
<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<title>Foro Internacional de Música Nueva Manuel Enríquez</title>
<meta http-equiv="refresh" content="0; url=${BASEURL}/">
<link rel="canonical" href="${BASEURL}/">
</head>
<body><p><a href="${BASEURL}/">48º Foro Internacional de Música Nueva Manuel Enríquez</a></p></body>
</html>
HTML
fi
paginas=$(find _site -name '*.html' | wc -l)
echo "✓ Listo: sitio/_site${BASEURL} ($paginas páginas HTML)"
