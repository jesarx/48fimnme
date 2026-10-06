# Cotejo con los programas de mano (carpeta «48 FIMNME programas»)

Correcciones aplicadas a `fimnme2026-programa.md` en el commit `1fc2c98`,
tras cotejar el contenido del programa general con los programas de mano
individuales (`48 FIMNME programas/*.docx`), tomados como la versión más
actualizada.

**Cómo revertir.** Todo el cotejo: `git revert 1fc2c98` (el diseño queda
intacto porque va en otro commit). Un cambio concreto: buscar en
`fimnme2026-programa.md` el texto de «Ahora» (las líneas del Markdown están
cortadas, conviene buscar un fragmento corto) y reponer el de «Antes».
Cada cambio lleva un número (C1, C2…) para poder referirse a él.

Al final están las diferencias que **no** se aplicaron: erratas de los
programas de mano, convenciones del programa general que se conservaron y
casos dudosos que conviene decidir a mano.

## 1. Estructura

- **C1** · El concierto **VIE | OCT 30 — San Luis Potosí: OSLP** pasa de «Conciertos en los estados» a «Ecos del Foro» (en la carpeta de programas de mano está con los Ecos del Foro). La parte cambia de subtítulo: «Conciertos en fechas posteriores al FIMNME 2026.» → «Conciertos fuera de las fechas del FIMNME 2026.» (el de San Luis Potosí es anterior al Festival).
- **C2** · Concierto nuevo en «Conciertos en los estados»: **MIÉ | NOV 18, 19:00 h — Morelia: Electroacústica I** (Centro Mexicano para la Música y las Artes Sonoras). Programa tomado del programa de mano (mismas obras que el MIÉ | NOV 18 en la Casa Rafael Galván); en lugar de repetir semblanzas y notas, lleva una línea que remite a la página de ese concierto.
- **C3** · Concierto nuevo en «Conciertos en los estados»: **JUE | NOV 19, 19:00 h — Morelia: Electroacústica II** (CMMAS), con el mismo criterio (remite al JUE | NOV 19 en la Casa Rafael Galván).

## 2. Cambios generales (varios conciertos)

- **C4** · «Cepromusic» en lugar de «CEPROMUSIC» en todo el programa (48 apariciones: títulos de concierto, semblanzas, integrantes y créditos), como en los programas de mano. Conciertos: SÁB | NOV 7, 19:00 h — Gonzalo Gutiérrez, piano; DOM | NOV 8, 16:30 h — Cuarteto Arcano; LUN | NOV 9, 19:00 h — Black Noise Ensamble; VIE | NOV 13, 17:00 h — Dirén Checa, violín; VIE | NOV 13, 19:00 h / DOM | NOV 15, 12:00 h — Madrigalistas: Cadet; SÁB | NOV 14, 12:00 h — Sesión de percusiones; SÁB | NOV 14, 13:00 h — Ensamble de Música Nueva (FaM-UNAM); SÁB | NOV 14, 17:00 h — Dúo Gasparini-Monnet; SÁB | NOV 14, 19:00 h — Cepromusic: Saariaho; DOM | NOV 15, 18:00 h — Dúo Arco y Teclas / Trío Siqueiros; DOM | NOV 15, 19:00 h — Ehecatl Flores, fagot contrabajo; MIÉ | NOV 18, 19:00 h — Electroacústica I; MIÉ | NOV 18, 19:00 h — Francisco García Torres: Enríquez 100; JUE | NOV 19, 20:00 h — Electroacústica II; VIE | NOV 20, 19:00 h — Cepromusic; SÁB | NOV 21, 17:00 h — Ensamble Sonus; MAR | NOV 10, 17:00 h — Monterrey: Q-SION, percusiones; MAR | NOV 10, 19:30 h — Guadalajara: Dúo Gasparini-Monnet; VIE | NOV 13, 19:00 h — Julio I. Cervantes, guitarra; VIE | NOV 13, 19:00 h — Eusebio Sánchez, percusiones; SÁB | NOV 14, 17:00 h — Acapulco: Fabián Rangel; SÁB | NOV 28, 20:00 h — Ocotlán: Dúo Gasparini-Monnet; MAR | DIC 1, 20:00 h — Oaxaca: Dúo Gasparini-Monnet; Créditos.
  - Antes: «CEPROMUSIC»
  - Ahora: «Cepromusic»
- **C5** · Semblanza de Kaija Saariaho: «tanto en su país natal como en el mundo entero» en lugar de «…como en todo el mundo», como en los programas de mano. Conciertos: MAR | NOV 10, 17:00 h — Monterrey: Q-SION, percusiones; JUE | NOV 12, 19:00 h — CMMAS: Compositoras en música electrónica; VIE | NOV 13, 19:00 h — Eusebio Sánchez, percusiones. (En el resto de las fichas ya decía «en el mundo entero»; en la primera ficha del concierto de Black Noise el programa de mano dice «en todo el mundo» y así se dejó.)
  - Antes: «tanto en su país natal como en todo el mundo»
  - Ahora: «tanto en su país natal como en el mundo entero»
- **C6** · Semblanza de Kurtág: «donde más tarde fue también profesor» (en Ocotlán el programa de mano dice «también fue profesor» y así se dejó). Conciertos: MAR | NOV 10, 19:30 h — Guadalajara: Dúo Gasparini-Monnet; MAR | DIC 1, 20:00 h — Oaxaca: Dúo Gasparini-Monnet.
  - Antes: «donde más tarde también fue profesor»
  - Ahora: «donde más tarde fue también profesor»
- **C7** · Nota de *Kafka Fragments*: «la más extensa que Kurtág haya compuesto hasta la fecha» (en lugar de «ha compuesto»). Conciertos: MAR | NOV 10, 19:30 h — Guadalajara: Dúo Gasparini-Monnet; SÁB | NOV 28, 20:00 h — Ocotlán: Dúo Gasparini-Monnet; MAR | DIC 1, 20:00 h — Oaxaca: Dúo Gasparini-Monnet.
  - Antes: «que Kurtág ha compuesto hasta la fecha»
  - Ahora: «que Kurtág haya compuesto hasta la fecha»
- **C8** · Nota de *Cliché*: «¿…esa especie de citas musicales escuchadas mil veces, se volvieran el material de base para la composición de una pieza?». Conciertos: MAR | NOV 10, 19:30 h — Guadalajara: Dúo Gasparini-Monnet; SÁB | NOV 28, 20:00 h — Ocotlán: Dúo Gasparini-Monnet; MAR | DIC 1, 20:00 h — Oaxaca: Dúo Gasparini-Monnet.
  - Antes: «permitiéramos que estos lugares comunes, especie de cita de músicas muchas veces escuchadas, se volvieran material inicial de base para la composición de una pieza musical?»
  - Ahora: «permitiéramos que estos lugares comunes, esa especie de citas musicales escuchadas mil veces, se volvieran el material de base para la composición de una pieza?»
- **C9** · Cargo de Juan Cáceres Avitia en la lista de integrantes de Cepromusic. Conciertos: SÁB | NOV 14, 19:00 h — Cepromusic: Saariaho; VIE | NOV 20, 19:00 h — Cepromusic.
  - Antes: «Juan Cáceres Avitia, **nuevas tecnologías**»
  - Ahora: «Juan Cáceres Avitia, **coordinador de nuevas tecnologías aplicadas a la creación musical**»

## 3. Por concierto


### Conciertos en Ciudad de México


#### VIE | NOV 6, 20:00 h — OSN: Carrasco / Höfele

- **C10** · Mayúsculas del título en inglés como en el programa de mano (6 apariciones en programa y notas)
  - Antes: «Nobody knows the trouble I see»
  - Ahora: «Nobody Knows the Trouble I See»

#### SÁB | NOV 7, 12:00 h — Tetraktys / Artificios / Ortiz / Ibarra

- **C11** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Gongan* (1997); *Ibia-Mom Jaci Ndipapahabi* (1999); *La llegada de Atheris* (2019); *Cinq illusions sonores* (2012); *Scintilla after Arvo Pärt* (2014-2015); De *Sonata de los misterios* (2011); *Kamajaya* (1998). (Para revertir: quitar `\*\*` tras el año de la obra.)

#### SÁB | NOV 7, 17:00 h — Instalación sonora: Nuño de Buen

- **C12** · Subtítulo como en el programa de mano («Instalación»; se quita «Instalación sonora / Inauguración»)
  - Antes: «**Instalación sonora** Inauguración»
  - Ahora: «**Instalación**»
- **C13** · Instalación de Nuño de Buen (SÁB | NOV 7 y DOM | NOV 8): la duración va en la línea de la obra (50') en lugar de la nota «Duración: 50 minutos», como en el programa de mano.
  - Antes: «- *Sobre las sensaciones de tono y otros fantasmas*\* *Duración: 50 minutos*»
  - Ahora: «- *Sobre las sensaciones de tono y otros fantasmas*\* … 50'»

#### SÁB | NOV 7, 19:00 h — Gonzalo Gutiérrez, piano

- **C14** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *O forse, l'ho già perduta poco a poco...* (2018); *Piezas con forma apropiada* (2024); *to an utterance -- a study* (2020). (Para revertir: quitar `\*\*` tras el año de la obra.)

#### DOM | NOV 8, 16:30 h — Cuarteto Arcano

- **C15** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Quello che resta* (2021); *Quimera etérea* (2018). (Para revertir: quitar `\*\*` tras el año de la obra.)

#### DOM | NOV 8, 18:00 h — OJUEM: Areán / Rosado

- **C16** · Alberto Rosado, piano, como solista de Ciudad sin sueño (Coll), como en el programa de mano
  - Antes: «- *Ciudad sin sueño*, fantasía para piano y orquesta … 20'»
  - Ahora: «- *Ciudad sin sueño*, fantasía para piano y orquesta … 20' [**Alberto Rosado**, piano]{.solista}»

#### LUN | NOV 9, 19:00 h — Black Noise Ensamble

- **C17** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Il pleut* (1986); *Changing Light* (2002); *Ogloudoglou* (1969). (Para revertir: quitar `\*\*` tras el año de la obra.)
- **C18** · Saariaho, Changing Light: la nota pasa a una segunda ficha de Saariaho, antes de Wilfrido Terrazas, como en el programa de mano. La nota se quita de la primera ficha y se pone en una ficha nueva del compositor/a en el lugar que le toca según el orden del programa; en el PDF esa ficha sale con el nombre y «Ver pág.» seguido de la nota.

#### MIÉ | NOV 11, 19:00 h — Trío LaMN

- **C19** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Dolce tormento* (2004); *Eón interior* (2023). (Para revertir: quitar `\*\*` tras el año de la obra.)

#### VIE | NOV 13, 17:00 h — Dirén Checa, violín

- **C20** · Saariaho, Frises: la nota pasa a una segunda ficha de Saariaho, después de Morton Feldman, como en el programa de mano. La nota se quita de la primera ficha y se pone en una ficha nueva del compositor/a en el lugar que le toca según el orden del programa; en el PDF esa ficha sale con el nombre y «Ver pág.» seguido de la nota.

#### VIE | NOV 13, 19:00 h / DOM | NOV 15, 12:00 h — Madrigalistas: Cadet

- **C21** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Light is Withheld*. (Para revertir: quitar `\*\*` tras el año de la obra.)
- **C22** · Semblanza de Rodrigo Cadet (como director) sustituida por la del programa de mano.
  - Antes: «Director huésped habitual para el Coro de Madrigalistas de Bellas Artes, el músico integró, a petición del comité organizador, un programa vocal que suma obras seleccionadas desde Convocatoria FIMNME 2026, obras de autoras y autores del canon contemporáneo, y…»
  - Ahora: «Originario de la Ciudad de México. Compositor y director egresado de la Escuela Superior de Música, ha escrito obras para orquesta, ensambles de cámara y coro. Ha hecho estudios de composición y orquestación con Hugo Rosales, Alejandro Romero, Georgina Derbez,…»

#### SÁB | NOV 14, 12:00 h — Sesión de percusiones

- **C23** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Dasselbe ist nicht dasselbe*. (Para revertir: quitar `\*\*` tras el año de la obra.)
- **C24** · Enríquez, Interecos: la nota pasa a una segunda ficha de Enríquez (con la semblanza del programa de mano), después de Nicolaus A. Huber. La nota se quita de la primera ficha y se pone en una ficha nueva del compositor/a en el lugar que le toca según el orden del programa; en el PDF esa ficha sale con el nombre y «Ver pág.» seguido de la nota.
- **C25** · Título de la nota: «Rebonds A y B», como en el programa de mano
  - Antes: «##### *Rebonds A* y *Rebonds B*»
  - Ahora: «##### *Rebonds A* y *B*»

#### SÁB | NOV 14, 19:00 h — Cepromusic: Saariaho

- **C26** · «Beneficiarios del Programa…» (sin «todos,»), como en el programa de mano
  - Antes: «Beneficiarios todos, del»
  - Ahora: «Beneficiarios del»

#### DOM | NOV 15, 19:00 h — Ehecatl Flores, fagot contrabajo

- **C27** · Semblanza de Aurés Moussong como en este programa de mano (en el PDF se muestra «Ver pág.»).
  - Antes: «Estudió Composición en la Escuela Superior de Música con Horacio Uribe, Georgina Derbez y José Luis Castillo. Obtuvo una Maestría en Composición por la Liszt Academy de Budapest y la UdK de Berlín, así como una especialización en el Conservatoire de Strasbourg…»
  - Ahora: «Estudió Composición en la Escuela Superior de Música de la Ciudad de México con Horacio Uribe, Georgina Derbez y José Luis Castillo. Obtuvo una Maestría en Composición por la Liszt Academy de Budapest y la UdK de Berlín, y una especialización en el Conservatoi…»

#### VIE | NOV 20, 17:00 h — Iracema de Andrade / ÓNIX

- **C28** · Enríquez, Díptico I: la nota pasa a una segunda ficha de Enríquez, después de Jimena Contreras, como en el programa de mano. La nota se quita de la primera ficha y se pone en una ficha nueva del compositor/a en el lugar que le toca según el orden del programa; en el PDF esa ficha sale con el nombre y «Ver pág.» seguido de la nota.

### Conciertos en los estados


#### VIE | NOV 6, 20:00 h — Xalapa: OSX

- **C29** · «Veracruz y Poza Rica, así como del país»
  - Antes: «Boca del Río, Veracruz, Poza Rica, y del país,»
  - Ahora: «Boca del Río, Veracruz y Poza Rica, así como del país,»
- **C30** · «Países Bajos» en lugar de «Holanda»
  - Antes: «Bélgica, Holanda, Luxemburgo»
  - Ahora: «Bélgica, Países Bajos, Luxemburgo»
- **C31** · «…República Checa, y en 2014…»
  - Antes: «República Checa, en 2014»
  - Ahora: «República Checa, y en 2014»
- **C32** · Puntuación: «Amor Ice, el cual»
  - Antes: «*Amor Ice* el cual»
  - Ahora: «*Amor Ice*, el cual»
- **C33** · Puntuación: «1959, que»
  - Antes: «Pablo Casals 1959 que»
  - Ahora: «Pablo Casals 1959, que»
- **C34** · Puntuación: «2010, en Guatemala»
  - Antes: «la de 2010 en Guatemala»
  - Ahora: «la de 2010, en Guatemala»
- **C35** · Puntuación: «En 2009, fue nombrado»
  - Antes: «En 2009 fue nombrado»
  - Ahora: «En 2009, fue nombrado»

#### LUN | NOV 9, 19:00 h — Morelia: Ensamble Danaus

- **C36** · Doderer: «se formó con Beat Furrer en Graz; posteriormente…»
  - Antes: «nació en Bregenz y estudió con Beat Furrer en Graz, y posteriormente»
  - Ahora: «nació en Bregenz y se formó con Beat Furrer en Graz; posteriormente»
- **C37** · Doderer: «ha escrito obras para orquesta»
  - Antes: «ha escrito varias obras para orquesta»
  - Ahora: «ha escrito obras para orquesta»
- **C38** · Nota de *Raunacht*: «doce noches» con letra (2 apariciones).
  - Antes: «Las Rauhnacht son 12 noches»
  - Ahora: «Las Rauhnacht son doce noches»
- **C39** · Raunacht: «se procesa el pasado y se conjura el futuro»
  - Antes: «y se puede procesar el pasado y conjurar el futuro»
  - Ahora: «y se procesa el pasado y se conjura el futuro»
- **C40** · «que se basa en un motivo»
  - Antes: «acompañamiento reiterado basado en un motivo»
  - Ahora: «acompañamiento reiterado que se basa en un motivo»
- **C41** · Puntuación: sin coma antes de «y Derek Bermel»
  - Antes: «Arturo Márquez, y Derek Bermel»
  - Ahora: «Arturo Márquez y Derek Bermel»
- **C42** · «Saint-John Perse» con guion
  - Antes: «Saint John Perse»
  - Ahora: «Saint-John Perse»
- **C43** · Puntuación: «dueto;»
  - Antes: «es decir un dueto, en la segunda vuelta»
  - Ahora: «es decir un dueto; en la segunda vuelta»
- **C44** · Puntuación: «y, finalmente,»
  - Antes: «un cuarteto y finalmente un quinteto»
  - Ahora: «un cuarteto y, finalmente, un quinteto»

#### MAR | NOV 10, 17:00 h — Monterrey: Q-SION, percusiones

- **C45** · Puntuación: «y, a partir de allí, explora»
  - Antes: «de una acción física y a partir de allí explora»
  - Ahora: «de una acción física y, a partir de allí, explora»
- **C46** · Ternasonantia: «sonancia, resultado sonoro del grupo, juntos forman el título y la descripción»
  - Antes: «y sonancia resultado sonoro del grupo, juntos forman tanto el título como la descripción»
  - Ahora: «y sonancia, resultado sonoro del grupo, juntos forman el título y la descripción»
- **C47** · «maneja con precisión»
  - Antes: «rigorosa y controlada, manejando con precisión»
  - Ahora: «rigorosa y controlada, maneja con precisión»
- **C48** · «dominio formal»
  - Antes: «estructura detallada y control formal,»
  - Ahora: «estructura detallada y dominio formal,»
- **C49** · Puntuación: «tradicional, sino»
  - Antes: «la melodía tradicional sino un diálogo»
  - Ahora: «la melodía tradicional, sino un diálogo»

#### JUE | NOV 12, 19:00 h — CMMAS: Compositoras en música electrónica

- **C50** · «indoestadounidense»
  - Antes: «Compositora indo estadounidense»
  - Ahora: «Compositora indoestadounidense»
- **C51** · Puntuación: «Musicología, tras lo cual»
  - Antes: «Musicología tras lo cual»
  - Ahora: «Musicología, tras lo cual»
- **C52** · Nota sobre Machaut (Asako Arai): «Desde la década de los años ochenta,» en lugar de «Desde la década de 1980,» (texto exacto del programa de mano)
  - Antes: «Desde la década de 1980,»
  - Ahora: «Desde la década de los años ochenta,»
- **C53** · Se quita «(Tonada de la luna llena I)» de la nota, como en el programa de mano
  - Antes: «este díptico (*Tonada de la luna llena I*) sin usar»
  - Ahora: «este díptico sin usar»
- **C54** · Puntuación: «inspiración, el resultado»
  - Antes: «fuente de inspiración el resultado»
  - Ahora: «fuente de inspiración, el resultado»

#### VIE | NOV 13, 19:00 h — Julio I. Cervantes, guitarra

- **C55** · Marca «\*\* Estreno en México» añadida, como en el programa de mano, a: *Y sueña que su sueño se repite* (2016); *Tres-Cuatro* (2025); *Capricho* (2006); *Preludio* (2015); *Slide* (2002). (Para revertir: quitar `\*\*` tras el año de la obra.)
- **C56** · Se retira del programa **Federico Núñez**, *Five Introspections* (2015)\* 9', que no figura en el programa de mano, junto con su semblanza y la nota de la obra.
  - Antes: «**Federico Núñez** - *Five Introspections* (2015)\* … 9'»
  - Ahora: «(se elimina)»

#### VIE | NOV 13, 19:00 h — Eusebio Sánchez, percusiones

- **C57** · «No ha sido estrenada públicamente; se presentó únicamente…»
  - Antes: «públicamente, presentándose únicamente»
  - Ahora: «públicamente; se presentó únicamente»

#### VIE | NOV 13, 19:30 h — Carmen Maldonado, percusión teatral

- **C58** · Título «Río» con tilde, como en el programa de mano
  - Antes: «*Rio* con la Universidad»
  - Ahora: «*Río* con la Universidad»
- **C59** · «WiroWero» como en el programa de mano
  - Antes: «música electrónica wirowero.»
  - Ahora: «música electrónica WiroWero.»
- **C60** · Puntuación: «aprendizaje, crítica»
  - Antes: «difusión y aprendizaje crítica»
  - Ahora: «difusión y aprendizaje, crítica»
- **C61** · Puntuación: «árbol, Ramón»
  - Antes: «místico árbol Ramón»
  - Ahora: «místico árbol, Ramón»
- **C62** · Puntuación: «2012, experimentando»
  - Antes: «Tuba en 2012 experimentando»
  - Ahora: «Tuba en 2012, experimentando»
- **C63** · Puntuación: «Artes, haciendo»
  - Antes: «Maestría en Artes haciendo»
  - Ahora: «Maestría en Artes, haciendo»
- **C64** · Puntuación: «En esta versión, la flauta»
  - Antes: «En esta versión la flauta»
  - Ahora: «En esta versión, la flauta»
- **C65** · «cincuenta años» con letra
  - Antes: «Lleva 50 años»
  - Ahora: «Lleva cincuenta años»
- **C66** · Puntuación: sin coma en «De 1993 a 2005 participó»
  - Antes: «De 1993 a 2005, participó»
  - Ahora: «De 1993 a 2005 participó»
- **C67** · Puntuación: «Dalí, en San Petersburgo»
  - Antes: «*Salvador Dalí* en San Petersburgo»
  - Ahora: «*Salvador Dalí*, en San Petersburgo»
- **C68** · Puntuación: «teatral, crea»
  - Antes: «percusión teatral crea»
  - Ahora: «percusión teatral, crea»
- **C69** · Puntuación: «Metamorfosis, música teatral para percusiones. Fundadora…»
  - Antes: «intérprete de Metamorfosis música teatral para percusiones, fundadora»
  - Ahora: «intérprete de *Metamorfosis*, música teatral para percusiones. Fundadora»
- **C70** · Puntuación: «entre arte y ciencia, forma parte»
  - Antes: «entre arte y ciencia y forma parte»
  - Ahora: «entre arte y ciencia, forma parte»

#### SÁB | NOV 14, 17:00 h — Acapulco: Fabián Rangel

- **C71** · Puntuación: «el tránsito; después»
  - Antes: «inicia el tránsito, después»
  - Ahora: «inicia el tránsito; después»
- **C72** · Puntuación: «y, por último,»
  - Antes: «suspensión y por último»
  - Ahora: «suspensión y, por último,»
- **C73** · Puntuación: «marcando, así, un ciclo» (como en el programa de mano)
  - Antes: «transformada, marcando así»
  - Ahora: «transformada, marcando, así,»
- **C74** · «elemento tierra» con minúscula
  - Antes: «elemento Tierra»
  - Ahora: «elemento tierra»
- **C75** · Puntuación: «veces, y»
  - Antes: «cualquier número de veces y»
  - Ahora: «cualquier número de veces, y»
- **C76** · Puntuación: «como se acomoden;»
  - Antes: «como se acomoden,»
  - Ahora: «como se acomoden;»
- **C77** · Puntuación: «Ruido 13, enfocándose»
  - Antes: «Ruido 13 enfocándose»
  - Ahora: «Ruido 13, enfocándose»
- **C78** · Puntuación: «grabaciones, además»
  - Antes: «realizado grabaciones además»
  - Ahora: «realizado grabaciones, además»
- **C79** · Puntuación: «interactiva, ya que»
  - Antes: «Es interactiva ya que»
  - Ahora: «Es interactiva, ya que»
- **C80** · Puntuación «el otro; se intenta» y errata «sobe» → «sobre» (la errata también está en el programa de mano)
  - Antes: «de un instrumento sobe el otro, se intenta»
  - Ahora: «de un instrumento sobre el otro; se intenta»
- **C81** · Puntuación: «2014, como»
  - Antes: «segunda en 2014 como»
  - Ahora: «segunda en 2014, como»
- **C82** · «…en 2024 y 2025, y la Orquesta de Cámara…»
  - Antes: «en 2024 y 2025 y por la»
  - Ahora: «en 2024 y 2025, y la»
- **C83** · «kintsugi» con minúscula
  - Antes: «llamada Kintsugi»
  - Ahora: «llamada kintsugi»
- **C84** · Se quita «(uno rápido, uno lento y cierra con uno rápido)», como en el programa de mano
  - Antes: «en tres movimientos (uno rápido, uno lento y cierra con uno rápido) sin»
  - Ahora: «en tres movimientos sin»
- **C85** · Puntuación: «Madrid, en 1967»
  - Antes: «grabada en Madrid en 1967»
  - Ahora: «grabada en Madrid, en 1967»
- **C86** · «Edgar Guzmán» sin tilde (2 apariciones), como en el programa de mano
  - Antes: «Édgar Guzmán»
  - Ahora: «Edgar Guzmán»

### Ecos del Foro


#### VIE | OCT 30, 20:00 h — San Luis Potosí: OSLP

- **C87** · «este tipo de noche»
  - Antes: «La obra entiende esta noche»
  - Ahora: «La obra entiende este tipo de noche»
- **C88** · Puntuación: sin coma antes de «y el corazón»
  - Antes: «dejan de ser suficientes, y el corazón»
  - Ahora: «dejan de ser suficientes y el corazón»
- **C89** · Nombre completo de la orquesta en la ficha
  - Antes: «#### Orquesta Sinfónica Universitaria de la UASLP (OSU)»
  - Ahora: «#### Orquesta Sinfónica Universitaria de la Universidad Autónoma de San Luis Potosí (OSU)»
- **C90** · Puntuación: «1971, con»
  - Antes: «se remonta a 1971 con»
  - Ahora: «se remonta a 1971, con»
- **C91** · «situarse» en lugar de «posicionarse»
  - Antes: «ha logrado posicionarse como»
  - Ahora: «ha logrado situarse como»
- **C92** · Orden: «y, durante una década, la Sinfónica de Michoacán»
  - Antes: «de la Universidad de Zacatecas y la Sinfónica de Michoacán, durante una década.»
  - Ahora: «de la Universidad de Zacatecas y, durante una década, la Sinfónica de Michoacán.»

## 4. Diferencias que no se aplicaron

### 4.1. Para decidir a mano

Aquí el programa de mano dice otra cosa que el programa general y no es
obviamente una errata. Se conservó lo que ya estaba en el programa general.

- **SÁB | NOV 14, 12:00 h — Sesión de percusiones.** Gene Koshinski: el
  programa de mano dice «(Estados Unidos, 1935)»; se dejó **1980**, su año
  de nacimiento real.
- **SÁB | NOV 14, 17:00 h — Dúo Gasparini-Monnet.** Berio, *Sequenza III*:
  el programa de mano dice «para violín solo»; se dejó **«para voz femenina
  solista»**, que es lo correcto (la de violín es la *Sequenza VIII*, que va
  después en el mismo programa).
- **SÁB | NOV 14, 17:00 h — Dúo Gasparini-Monnet.** Nota de *Sequenza VIII*:
  se dejó «los sonidos La y Si»; el programa de mano dice «A y B».
- **Guadalajara, Ocotlán y Oaxaca (Dúo Gasparini-Monnet).** En el programa
  de mano: Leoncavallo, «Ridono Lassú» (se dejó *Qual fiamma avea nel
  guardo!… Stridono lassù*); «Johannes Strauss» (se dejó Richard Strauss,
  autor de *Morgen!*); Ravel, «Habanera» (se dejó *Pièce en forme de
  habanera*); y la forma de citar las *Siete canciones populares*.
- **LUN | NOV 9 — Morelia: Ensamble Danaus.** «Un discurso disconexo» en el
  programa de mano; se dejó «disjunto».
- **VIE | NOV 13 — Julio I. Cervantes.** Nota de *Slide*: el programa de mano
  repite el apellido antes de la atribución («(composición) Kandinsky,
  Wassily Kandinsky (1912)»); se dejó «(composición). Wassily Kandinsky
  (1912)».
- **SÁB | NOV 14 — Acapulco.** El programa de mano repite «Alemania, Costa
  Rica» en la lista de países de una semblanza; no se añadió.
- **MAR | NOV 10 — Monterrey.** El programa de mano dice «y a partir, de
  allí, explora»; se puso «y, a partir de allí, explora» (C45).
- **VIE | NOV 6 — OSN.** El programa de mano pone «(Alemania, 1918-1970)»
  junto a Zimmermann en el programa; se dejó sin fechas, como pidió la
  revisión anterior (las fechas están en su ficha). Tampoco se cambió «In
  memoriam» por «In Memoriam».
- **Subtítulos de concierto.** Los programas de mano traen «Concierto
  electroacústico» (Casa Rafael Galván), «Compositoras en música
  electrónica» (CMMAS) y «Electroacústica I/II»; no se añadieron como
  subtítulo porque la revisión anterior los había quitado (ya forman parte
  del título).
- **DOM | NOV 8, 12:00 h — Instalación.** Se dejó el subtítulo
  «Instalación - Concierto» de ese día (el del SÁB | NOV 7 sí se cambió, C12).
- **Dúo Arco y Teclas.** Su semblanza aparece en el programa de mano de
  Gonzalo Gutiérrez (SÁB | NOV 7, 19:00 h), donde no tocan; no se añadió
  ahí. En el del DOM | NOV 15 no viene, pero se conservó en el programa
  general porque es el concierto en que tocan.
- **SÁB | NOV 28 — Ocotlán.** El programa de mano trae una variante de la
  semblanza de Noemi Gasparini (con una oración en otro lugar); los otros
  tres programas de mano del dúo coinciden con el programa general, así
  que se dejó igual.
- **Dúo Gasparini-Monnet.** Se conservó el título de nota «*Kafka
  Fragments*, Op. 24».
- **JUE | NOV 12 — CMMAS.** El programa de mano de Asako Arai se tomó como
  el del concierto «Compositoras en música electrónica».
- **DOM | NOV 15 — Ehecatl Flores.** La semblanza de Aurés Moussong se
  actualizó (C27), pero en el PDF no se ve porque ahí sale «Ver pág.»; la
  que se ve es la del DOM | NOV 8 (OJUEM), que coincide con el programa de
  mano de ese concierto.

### 4.2. Erratas de los programas de mano (el programa general ya estaba bien)

Musikhochule, Thèâtre, Palais Des, caracterizo, «un algún», 19534,
RéSilience, «op,», Sings, Kuntachi, Ensmable, «del Enríquez», Guagauncó,
coofundador, Baukholt (Bauckholt), Depp, Shaeffer, imbólico, Visones,
Panoyotis, Migue, Villlanueva, Jeijetsu, Loweinstein, Bryan Fernyhough
(Brian Ferneyhough), Rhim (Rihm), Reina Marie Jose, Francois, Velázquez-Ensemble,
Düseldorff, Kélemen, generarn, motlo, MAX/SP, Jamaisensis, fueestrenada,
Awardfor, Talqná (Tlaqná).

### 4.3. Convenciones del programa general que se conservaron

Los programas de mano no son uniformes entre sí; en estos casos se mantuvo
el criterio único del programa general:

- «solo» y los demostrativos (este, esta, aquel…) sin tilde; «Rumanía».
- Comillas latinas «», rayas y guiones con su espaciado, asterisco de estreno
  pegado al año.
- «trío» en minúscula en el texto, «Trío LaMN» como nombre.
- Grafías ya revisadas: Areán, Ortiz, Gurría, Q-SION, Zárate Marfil,
  Liliana Z. del Río, Tobías Álvarez, CalArts.
- Nombres de sede unificados: «Antigua Sede del Senado. Casona de
  Xicoténcatl», «Sala Principal, Centro Cultural Tlaqná», «Fundación
  Cultural Rodolfo Morales, Ocotlán de Morelos», «Museo de Arte Carrillo
  Gil».
- Formato de la lista de integrantes de la OSN; «violín I / violín II».
- Títulos: «In memoriam», *Scintilla after Arvo Pärt*, *Erbarme dich*,
  y las mayúsculas de los movimientos de *Six Japanese Gardens*.

