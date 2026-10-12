# Programa resumido · 48.º FIMNME

`fimnme2026-resumen.pdf` es la versión concentrada del Programa General:
mismo formato (108 × 192 mm) y paleta, sin fotos, semblanzas ni notas, con
letra de lectura (Noto Sans de 8 pt en los programas).

- **Páginas 1–2 · Agenda.** Todos los conciertos, actividades académicas y
  sesiones del Coloquio, día por día, con hora, título y la letra de su sede,
  más la clave de sedes con su dirección (primero el recinto y luego la sala).
  Los nombres no se cortan entre renglones y ningún título termina con una
  palabra sola en su último renglón (`automatizacion/tipografia.lua`).
- **Programas.** Un concierto por bloque (no se parte entre páginas): fecha,
  título y sede; sus intérpretes y las personas compositoras («Obras de A, B
  y C»), sin los títulos de las obras; y cuántos estrenos mundiales y en
  México tiene. Al principio, el total de estrenos del Foro (cada obra una
  sola vez). Se omiten las listas de integrantes de los conjuntos (se dan
  su nombre y su dirección). El papel de cada intérprete (el instrumento,
  «director»…) va en un peso más ligero que su nombre; los nombres de
  intérpretes y compositores no se cortan entre renglones, y la «y» final de
  una lista va con el nombre que sigue.
- **Actividades académicas y Coloquio**, con sus participantes (su papel,
  «ponente», «moderadora»…, también más ligero).
- **Logotipos.** Todos los logotipos del Programa general (los bloques
  `::: logos` de cada concierto), sin repetir, en copias ligeras para que el
  PDF siga pesando poco.
- **Créditos** del 48.º FIMNME («## Créditos») y directorio de la
  Coordinación Nacional de Música y Ópera («## Directorio»), como en el
  Programa general.
- **Última página · Directorio** de la Secretaría de Cultura y del INBAL (el
  bloque `::: contraportada` del Markdown), con la pleca institucional al pie.

En total, 16 páginas (múltiplo de 4, para imprimirlo).

No se edita a mano: se genera a partir del mismo `fimnme2026-programa.md`,
así que cualquier corrección al programa general llega también aquí.

```bash
resumen/compila.sh      # unos segundos; ./compila.sh también lo regenera
```

| Archivo | Para qué sirve |
|---|---|
| `resumen.lua` | Lee el Markdown y arma la agenda y los programas condensados. |
| `resumen.latex` | Diseño: página, tipografía (Noto Sans, sin versiones condensadas), colores, agenda, programas. |
| `reducir_logos.py` | Copias ligeras (300 ppp, 16 niveles) de los logotipos que prepara `automatizacion/preparar_logos.py`. |
| `compila.sh` | Compila el PDF (en `build/resumen/`) y lo copia aquí. |

Las sedes y sus direcciones salen de la sección `## Sedes` del Markdown; la
correspondencia entre la sede de cada concierto y esa lista se hace por
palabras clave (`CLAVES_SEDE`, al principio de `resumen.lua`). Si se añade
una sede nueva, hay que agregar ahí su palabra clave; el filtro avisa si
alguna sede no se encuentra. `RESUMEN_DEPURAR=1 resumen/compila.sh` lista
cuántas obras se tomaron de cada concierto, para cotejarlas.
