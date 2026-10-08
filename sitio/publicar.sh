#!/usr/bin/env bash
# Compila el sitio web y lo copia a la carpeta que sirve el servidor web (la
# raíz del dominio).
#
#   sitio/publicar.sh /var/www/fimnme.qumran.cc                     en el propio VPS
#   sitio/publicar.sh usuario@servidor:/var/www/fimnme.qumran.cc    desde otra computadora (por SSH)
#
# La edición va en su carpeta (/2026/, según baseurl de _config.yml) y se
# copia con rsync --delete: queda igual a sitio/_site/2026 (lo que ya no
# existe en el sitio se borra del servidor). Otras carpetas del dominio (otras
# ediciones) no se tocan; en la raíz se actualizan la redirección a esta
# edición y el robots.txt. Instrucciones completas en sitio/DESPLIEGUE.md.

set -euo pipefail
cd "$(dirname "$0")"

DESTINO="${1:-}"
if [[ -z "$DESTINO" ]]; then
  echo "Uso: sitio/publicar.sh CARPETA   (p. ej. /var/www/fimnme.qumran.cc o usuario@servidor:/var/www/fimnme.qumran.cc)"
  exit 1
fi

./genera.sh --compilar
BASEURL=$(sed -nE 's/^baseurl: *"?([^"]*)"?.*/\1/p' _config.yml)

echo "▸ Copiando a $DESTINO${BASEURL}/…"
rsync -rlt --delete --chmod=D755,F644 --human-readable --info=stats1 "_site${BASEURL}/" "$DESTINO${BASEURL}/"
if [[ -n "$BASEURL" ]]; then
  rsync -lt --chmod=F644 _site/index.html _site/robots.txt "$DESTINO/"
fi
echo "✓ Publicado: $(sed -nE 's/^url: *"?([^"]*)"?.*/\1/p' _config.yml)${BASEURL}/"
