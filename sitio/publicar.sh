#!/usr/bin/env bash
# Compila el sitio web y lo copia a la carpeta que sirve el servidor web.
#
#   sitio/publicar.sh /var/www/fimnme.qumran.cc                     en el propio VPS
#   sitio/publicar.sh usuario@servidor:/var/www/fimnme.qumran.cc    desde otra computadora (por SSH)
#
# Copia con rsync --delete: el destino queda igual a sitio/_site (lo que ya no
# existe en el sitio se borra del servidor). Instrucciones completas en
# sitio/DESPLIEGUE.md.

set -euo pipefail
cd "$(dirname "$0")"

DESTINO="${1:-}"
if [[ -z "$DESTINO" ]]; then
  echo "Uso: sitio/publicar.sh CARPETA   (p. ej. /var/www/fimnme.qumran.cc o usuario@servidor:/var/www/fimnme.qumran.cc)"
  exit 1
fi

# Jekyll del Gemfile (bundle install) o, si no, el que esté instalado
if command -v bundle > /dev/null && bundle exec jekyll --version > /dev/null 2>&1; then
  JEKYLL=(bundle exec jekyll)
elif command -v jekyll > /dev/null; then
  JEKYLL=(jekyll)
else
  echo "✗ No se encontró Jekyll. Instálelo con «cd sitio && bundle install» (ver DESPLIEGUE.md)."
  exit 1
fi

echo "▸ Compilando el sitio…"
JEKYLL_ENV=production "${JEKYLL[@]}" build --quiet
echo "▸ Copiando a $DESTINO…"
rsync -rlt --delete --chmod=D755,F644 --human-readable --info=stats1 _site/ "$DESTINO/"
echo "✓ Publicado: $(grep -E '^url:' _config.yml | sed -E 's/url: *"?([^"]*)"?/\1/')"
