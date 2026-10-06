#!/usr/bin/env bash
# Compila el Programa General del 48.º FIMNME.
#
#   ./compila.sh            compilación completa
#   ./compila.sh --rapido   una sola pasada de LuaLaTeX (para revisar cambios)
#
# Requisitos: pandoc (≥ 3.1), LuaLaTeX (TeX Live ≥ 2023 con koma-script,
# tcolorbox, tikz, microtype...), makeindex y Python 3 con Pillow.
# OpenCV (opencv-python-headless) es opcional: mejora el recorte de las fotos
# centrándolas en el rostro.
#
# El PDF ya no se pasa por Ghostscript: las fotos se preparan a la resolución
# adecuada antes de compilar, así que nada sale pixeleado y el texto conserva
# su capa Unicode (búsqueda y copiado correctos).

set -euo pipefail
cd "$(dirname "$0")"

NOMBRE=fimnme2026-programa
mkdir -p build

echo "▸ Preparando fotografías…"
python3 automatizacion/preparar_imagenes.py
echo "▸ Preparando logotipos…"
python3 automatizacion/preparar_logos.py

echo "▸ Pandoc → LaTeX…"
pandoc "$NOMBRE.yaml" "$NOMBRE.md" \
  --from markdown \
  --metadata-file=automatizacion/indice-onomastico.yaml \
  --template=automatizacion/plantilla/fimnme.latex \
  --lua-filter=automatizacion/fimnme.lua \
  --wrap=none \
  -o "build/$NOMBRE.tex"

lualatex_pasada() {
  lualatex --interaction=nonstopmode --halt-on-error \
    --output-directory=build "build/$NOMBRE.tex" > "build/$NOMBRE.salida" 2>&1 || {
      echo "✗ Error de LuaLaTeX; últimas líneas de build/$NOMBRE.log:"
      tail -n 40 "build/$NOMBRE.log"
      exit 1
    }
}

firma_aux() {
  # Decisiones del ajuste fino y números de página de las etiquetas
  grep -h -E '^\\(fimnmeajuste|newlabel)' "build/$NOMBRE.aux" 2>/dev/null | md5sum
}

# Una compilación completa parte de cero: el ajuste fino solo escala dentro
# de una misma compilación, así que no debe heredar decisiones de otra.
if [[ "${1:-}" != "--rapido" ]]; then rm -f "build/$NOMBRE.aux"; fi

echo "▸ LuaLaTeX (pasada 1)…"
lualatex_pasada
if [[ "${1:-}" != "--rapido" ]]; then
  # Se repite hasta que el índice, las referencias y el ajuste fino de
  # páginas se estabilizan (mínimo 3 pasadas, máximo 10).
  anterior=""
  for pasada in 2 3 4 5 6 7 8 9 10; do
    makeindex -q -s automatizacion/plantilla/indice.ist "build/$NOMBRE.idx"
    echo "▸ LuaLaTeX (pasada $pasada)…"
    lualatex_pasada
    actual="$(firma_aux)"
    if [[ $pasada -ge 3 && "$actual" == "$anterior" ]] && \
       ! grep -q "Rerun to get" "build/$NOMBRE.log"; then
      break
    fi
    anterior="$actual"
  done
fi

cp "build/$NOMBRE.pdf" "$NOMBRE.pdf"
echo "✓ Listo: $NOMBRE.pdf ($(pdfinfo "$NOMBRE.pdf" 2>/dev/null | awk '/^Pages/{print $2}') páginas)"
grep -E "^(Overfull|Underfull) \\\\hbox" "build/$NOMBRE.log" | sort | uniq -c | sort -rn | head -5 || true

# El programa resumido sale del mismo Markdown
if [[ "${1:-}" != "--rapido" ]]; then
  echo "▸ Programa resumido…"
  resumen/compila.sh
fi
