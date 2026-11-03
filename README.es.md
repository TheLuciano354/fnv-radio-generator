# Generador de radio de Fallout: New Vegas

[Read in English](README.md)

Genera emisiones infinitas y reproducibles de las radios de **Fallout: New Vegas** a partir de tu propia copia del juego. No mezcla canciones al azar: ejecuta la misma lógica de diálogo que usa el motor del juego (saludos, noticias, segmentos, presentaciones, reglas anti-repetición), así que cada emisión suena como la radio del juego.

Emisoras disponibles:

- **Radio New Vegas**: Mr. New Vegas, noticias que dependen de la partida, presentaciones de canciones, 19 canciones.
- **Black Mountain Radio**: los segmentos de Tabitha, Rhonda y Raúl y 15 canciones country.
- **Mojave Music Radio**: 15 canciones country.

> **No incluye archivos del juego.** El programa los lee de tu instalación de Fallout: New Vegas. Sin relación con Bethesda Softworks ni con Obsidian Entertainment.

## Características

- Interfaz gráfica para Windows: eliges la carpeta del juego, extraes una vez y generas todas las emisiones que quieras.
- **Semillas**: la misma semilla con las mismas opciones produce siempre la misma emisión.
- Salida en **WAV**, **MP3 256 kbps VBR** u **Opus 128 kbps VBR**, con escaleta con tiempos (`.txt`).
- Conserva los **niveles originales del juego** (las canciones suenan mucho más bajas que el locutor, como en el Pip-Boy) o lo normaliza todo a −16 LUFS.
- Opciones: frases del perk *Yermo salvaje*, corrección del bug original de *Big Iron* / *Stars of the Midnight Range* y no repetir locuciones dentro de un bloque.

## Requisitos

- Windows
- Fallout: New Vegas (Steam, GOG…); los DLC son opcionales
- [ffmpeg](https://ffmpeg.org/download.html) con `ffprobe`, en el `PATH` o junto al `.exe`

## Uso

1. Descarga `FNV Radio Generator.exe` desde [Releases](../../releases) y ponlo en una carpeta propia (guarda sus datos a su lado).
2. Ábrelo, comprueba la carpeta de Fallout: New Vegas (en Steam se detecta sola) y pulsa **Extraer archivos del juego**. Copia unos 275 MB a `library/`, una sola vez.
3. Elige emisora, semilla (o **Nueva semilla**), duración, opciones y formato.
4. **Vista previa** muestra la escaleta; **Generar radio** guarda el audio en la carpeta de salida.

Notas:

- La duración es mínima: la emisión termina al acabar un bloque o tras la primera canción que la alcanza.
- Los textos de la escaleta salen en el idioma de tu juego.
- Las noticias usan el estado inicial de la partida (noticias del principio del juego).

## Ejecutar desde el código

Necesita Python 3.10+ (solo biblioteca estándar, tkinter incluido).

```bash
python -m fnv_radio
```

Para compilar el `.exe` ejecuta `build.bat`: crea un entorno virtual con PyInstaller y deja `FNV Radio Generator.exe` en la carpeta del proyecto. Al subir una etiqueta `v*`, GitHub Actions lo compila y lo adjunta a una release.

`tests/check_rules.py` simula 5000 bloques de Radio New Vegas y comprueba las reglas del juego (necesita `library/` extraída).

## Cómo funciona

- [Cómo funciona Radio New Vegas por dentro](docs/es/como-funciona-radio-new-vegas.md): el grafo de diálogo obtenido por ingeniería inversa, las variables de control, los formatos de archivo y la lista de canciones.
- [Emisoras del juego](docs/es/emisoras.md): todas las emisoras del juego base y los DLC, y cuáles se podrían añadir.

| Carpeta | Contenido |
|---|---|
| `fnv_radio/` | La app: lectores ESM/BSA, extracción, motor de radio, render, interfaz |
| `docs/` | Documentación en inglés y español |
| `tests/` | Comprobación de reglas |
| `tools/` | Análisis de sonoridad y silencios del audio generado |

## Licencia

Código bajo [licencia MIT](LICENSE). Fallout: New Vegas y todos sus audios y textos pertenecen a Bethesda Softworks / ZeniMax Media; este proyecto no los incluye ni los redistribuye.
