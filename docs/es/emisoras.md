# Emisoras del juego (base + DLC)

[English version](../en/stations.md)

Inventario sacado de `FalloutNV.esm`, `DeadMoney.esm`, `HonestHearts.esm`, `OldWorldBlues.esm`, `LonesomeRoad.esm`, `GunRunnersArsenal.esm` y los 4 packs. Una emisora es un *Talking Activator* con el flag *Radio Station* (0x00020000) cuyo contenido vive en una quest. "Oculta" = no aparece en el Pip-Boy (flag 0x10000000): suena en altavoces del mundo (casinos, tiendas).

- **Lonesome Road, Gun Runners' Arsenal y los packs (Caravan, Classic, Mercenary, Tribal) no tienen ninguna emisora.**
- `FalloutNV.esm` conserva ~20 emisores heredados de Fallout 3 (Galaxy News Radio, Enclave Radio, Agatha, Radio 101…) sin quest ni audio: no sirven.

## A. Emisoras completas

| Emisora | Quest | Contenido | En el programa |
|---|---|---|---|
| **Radio New Vegas** | `RadioNewVegas` | Mr. New Vegas: 196 locuciones + 19 canciones | ✅ ([cómo funciona](como-funciona-radio-new-vegas.md)) |
| **Black Mountain Radio** | `RadioBlackMountain` | Tabitha, Rhonda y Raúl: 156 locuciones (149 con audio) + 15 canciones country | ✅ |
| **Mojave Music Radio** | `vCountryRadioQuest` | 15 canciones country, sin locutor | ✅ |

### Black Mountain Radio

- `RadioHello` son las propias canciones (sin repetir las 3 últimas). Tras cada canción se elige uno de 12 **segmentos** (`RadioBMSegment01`–`13`): "Mundo Mutante", "CNU, el Canal de Noticias de Utobitha", anuncios de reclutamiento, entrevistas con Raúl…
- Cada segmento es una secuencia de 5–19 frases en orden, controlada por `SegmentVar`. No se repite ninguno de los 3 últimos segmentos.
- La conversación solo termina en el segmento 13, así que puede encadenar media hora: el programa corta tras la primera canción que alcanza la duración pedida.
- 7 frases no tienen audio en el juego ("[Silencio.]", "[Pista de aplausos.]"…) y se omiten.
- Parte del contenido cambia según la misión de Black Mountain y si Raúl sigue allí. El programa usa el estado inicial.

### Mojave Music Radio

Solo canciones: una al azar, sin repetir las 3 últimas. Aquí *Stars of the Midnight Range* suena con su archivo correcto.

## B. Hilo musical (solo música, emisoras ocultas)

Misma regla: canción aleatoria sin repetir las 3 últimas.

| Emisora | Quest | Canciones |
|---|---|---|
| Ultra-Luxe (clásica) | `vUltraLuxeRadioQuest` | 7 entradas / 6 archivos (Vivaldi, Bach, Mozart, *Lakmé*…). Bug: *Spring Song* apunta al concierto de Mozart |
| Gomorrah, música del salón | `vGomorrahRadioQuest` | 6 jazz/blues |
| Tops | `TopsRadioQuest` | 8 |
| Old World Blues, "Emisión misteriosa" | `NVDLC03RadioBroadcast` | 10 jazz, incluido el tema de Vera |
| Dead Money, música ambiente del Sierra Madre | `NVDLC01RadioAMBMusic` | 3 |

## C. Señales habladas cortas (mensajes en bucle)

| Señal | Quest | Líneas | Notas |
|---|---|---|---|
| Radio de emergencia de la RNC | `vNCREmergencyRadio` | 32 | Boletines que dependen de la partida y de un temporizador de script |
| Radio del campamento Guardian | `vCampGuardianRadio` | 8 | Petición de auxilio del soldado Halford |
| Retransmisión del Sierra Madre (DM) | `NVDLC01RadioCasino` | 25 | Mensaje de Vera en 3 versiones según el avance del DLC |
| Frecuencias ULF de los collarines (DM) | `NVDLC01RadioElijah/Dean/Christine/Dog` | 75 / 59 / 27 / 116 | Cambian con cada acto del DLC |
| Happy Trails (HH) | `NVDLC02RadioMessage` | 6 | Anuncio de Jed Masterson |
| Hanlon, nietos de Lily | `VCampGolfHanlon`, `vDialogueLily` | 8 / 7 | Grabaciones de misión, ocultas |

## Añadir una emisora

El motor interpreta cualquier quest de radio, así que añadir las de B es darlas de alta en [`fnv_radio/stations.py`](../../fnv_radio/stations.py) (plugin + EditorID de la quest), volver a extraer y comprobar que se comportan como en el juego. Las de C necesitarían un "perfil de partida" para elegir qué versión del mensaje suena.
