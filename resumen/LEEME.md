# Programa resumido · 48.º FIMNME

`fimnme2026-resumen.pdf` es la versión concentrada del Programa General:
mismo formato (108 × 192 mm) y paleta, sin fotos, semblanzas ni notas.

- **Página 1 · Agenda.** Todos los conciertos, actividades académicas y
  sesiones del Coloquio con día, hora, título y la letra de su sede, más la
  clave de sedes con su dirección. Es lo necesario para llegar a cada
  concierto.
- **Páginas 2–5 · Programas.** Por concierto: compositores y obras (con las
  marcas de estreno), intérpretes y solistas, en texto corrido y a dos
  columnas. Se omiten años, duraciones, movimientos y las listas de
  integrantes de los conjuntos (se dan su nombre y su dirección). Cuando un
  concierto repite el programa de otro, se indica «Mismo programa que…».
- **Página 6 · Logotipos.** Todos los logotipos del Programa general (los
  bloques `::: logos` de cada concierto), sin repetir, en copias ligeras
  para que el PDF siga pesando poco.

No se edita a mano: se genera a partir del mismo `fimnme2026-programa.md`,
así que cualquier corrección al programa general llega también aquí.

```bash
resumen/compila.sh      # unos segundos; ./compila.sh también lo regenera
```

| Archivo | Para qué sirve |
|---|---|
| `resumen.lua` | Lee el Markdown y arma la agenda y los programas condensados. |
| `resumen.latex` | Diseño: página, tipografía (Noto Sans SemiCondensed), colores, agenda, programas. |
| `reducir_logos.py` | Copias ligeras (300 ppp, 16 niveles) de los logotipos que prepara `automatizacion/preparar_logos.py`. |
| `compila.sh` | Compila el PDF (en `build/resumen/`) y lo copia aquí. |

Las sedes y sus direcciones salen de la sección `## Sedes` del Markdown; la
correspondencia entre la sede de cada concierto y esa lista se hace por
palabras clave (`CLAVES_SEDE`, al principio de `resumen.lua`). Si se añade
una sede nueva, hay que agregar ahí su palabra clave; el filtro avisa si
alguna sede no se encuentra. `RESUMEN_DEPURAR=1 resumen/compila.sh` lista
cuántas obras se tomaron de cada concierto, para cotejarlas.
