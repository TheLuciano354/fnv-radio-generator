# Fallout: New Vegas Radio Generator

[Leer en español](README.es.md)

Generates endless, reproducible broadcasts of the **Fallout: New Vegas** radio stations from your own copy of the game. It doesn't shuffle songs: it runs the same dialogue logic the game engine uses (greetings, news, segments, song intros, no-repeat rules), so every broadcast sounds like the in-game radio.

Supported stations:

- **Radio New Vegas**: Mr. New Vegas, news that depends on the game state, song intros, 19 songs.
- **Black Mountain Radio**: Tabitha, Rhonda and Raul's segments and 15 country songs.
- **Mojave Music Radio**: 15 country songs.

> **No game files are included.** The program reads them from your Fallout: New Vegas installation. Not affiliated with Bethesda Softworks or Obsidian Entertainment.

## Features

- Windows GUI: pick the game folder, extract once, generate as many broadcasts as you want.
- **Seeds**: the same seed with the same options always produces the same broadcast.
- Output to **WAV**, **MP3 256 kbps VBR** or **Opus 128 kbps VBR**, plus a timestamped tracklist (`.txt`).
- Keeps the **original game levels** (songs are much quieter than the host, like on the Pip-Boy) or normalizes everything to −16 LUFS.
- Options: *Wild Wasteland* perk lines, fix for the vanilla *Big Iron* / *Stars of the Midnight Range* bug, no repeated lines within a block.

## Requirements

- Windows
- Fallout: New Vegas (Steam, GOG…); DLCs are optional
- [ffmpeg](https://ffmpeg.org/download.html) with `ffprobe`, either on the `PATH` or next to the `.exe`

## Usage

1. Download `FNV Radio Generator.exe` from [Releases](../../releases) and put it in its own folder (it stores its data next to itself).
2. Open it, check the Fallout: New Vegas folder (detected automatically for Steam) and click **Extract game files**. It copies about 275 MB to `library/`, only once.
3. Choose a station, a seed (or **New seed**), the length, the options and the format.
4. **Preview** shows the tracklist; **Generate radio** writes the audio to the output folder.

Notes:

- The length is a minimum: the broadcast ends when a block finishes or after the first song that reaches it.
- Subtitles in the tracklist come from your game's language.
- The news uses the game's starting state (early-game stories).

## Running from source

Needs Python 3.10+ (standard library only, tkinter included).

```bash
python -m fnv_radio
```

To build the `.exe` yourself run `build.bat`, which creates a virtual environment with PyInstaller and leaves `FNV Radio Generator.exe` in the project folder. Pushing a `v*` tag builds it on GitHub Actions and attaches it to a release.

`tests/check_rules.py` simulates 5000 Radio New Vegas blocks and checks the game's rules (needs an extracted `library/`).

## How it works

- [How Radio New Vegas works under the hood](docs/en/how-radio-new-vegas-works.md): the reverse-engineered dialogue graph, control variables, file formats and song list.
- [In-game radio stations](docs/en/stations.md): every station in the base game and DLCs, and which ones could be added.

| Folder | Contents |
|---|---|
| `fnv_radio/` | The app: ESM/BSA readers, extraction, radio engine, renderer, GUI |
| `docs/` | Documentation in English and Spanish |
| `tests/` | Rule checks |
| `tools/` | Loudness and silence analysis of generated audio |

## License

Code under the [MIT License](LICENSE). Fallout: New Vegas and all its audio and text belong to Bethesda Softworks / ZeniMax Media; this project neither includes nor redistributes them.
