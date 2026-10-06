#!/bin/bash

pandoc fimnme2026-programa.yaml \
fimnme2026-programa.md \
  --pdf-engine=xelatex \
  --lua-filter=automatizacion/circular_margin.lua \
  -o fimnme2026-programa.pdf

pdftk ../disegno/cnmo-fimnme2026-fondo_imagen_oficial-16_9.pdf \
  fimnme2026-programa.pdf \
  ../disegno/cnmo-fimnme2026-fondo_imagen_oficial-16_9_cuarta.pdf \
  cat output temp.pdf

gs -sDEVICE=pdfwrite \
  -dCompatibilityLevel=1.4 \
  -dPDFSETTINGS=/ebook \
  -dNOPAUSE -dQUIET -dBATCH \
  -dFastWebView \
  -dDetectDuplicateImages \
  -sOutputFile=fimnme2026-programa.pdf \
  temp.pdf

  rm temp.pdf 
