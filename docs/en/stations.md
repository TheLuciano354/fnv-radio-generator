# In-game radio stations (base game + DLC)

[Versión en español](../es/emisoras.md)

Inventory taken from `FalloutNV.esm`, `DeadMoney.esm`, `HonestHearts.esm`, `OldWorldBlues.esm`, `LonesomeRoad.esm`, `GunRunnersArsenal.esm` and the 4 packs. A station is a *Talking Activator* with the *Radio Station* flag (0x00020000) whose content lives in a quest. "Hidden" = not listed on the Pip-Boy (flag 0x10000000): it plays through in-world speakers (casinos, shops).

- **Lonesome Road, Gun Runners' Arsenal and the packs (Caravan, Classic, Mercenary, Tribal) have no stations.**
- `FalloutNV.esm` still contains ~20 broadcasters left over from Fallout 3 (Galaxy News Radio, Enclave Radio, Agatha, Radio 101…) with no quest or audio: unusable.

## A. Full stations

| Station | Quest | Content | In the program |
|---|---|---|---|
| **Radio New Vegas** | `RadioNewVegas` | Mr. New Vegas: 196 spoken lines + 19 songs | ✅ ([how it works](how-radio-new-vegas-works.md)) |
| **Black Mountain Radio** | `RadioBlackMountain` | Tabitha, Rhonda and Raul: 156 spoken lines (149 with audio) + 15 country songs | ✅ |
| **Mojave Music Radio** | `vCountryRadioQuest` | 15 country songs, no host | ✅ |

### Black Mountain Radio

- `RadioHello` is made of the songs themselves (never one of the last 3). After each song one of 12 **segments** (`RadioBMSegment01`–`13`) is picked: talk shows about the different mutants, Utobitha news bulletins, recruitment ads, interviews with Raul…
- Each segment is a sequence of 5–19 lines played in order, driven by `SegmentVar`. None of the last 3 segments repeats.
- The conversation only ends at segment 13, so it can run for half an hour: the program stops after the first song that reaches the requested length.
- 7 lines have no audio in the game (stage directions such as a silence or an applause track) and are skipped.
- Part of the content changes with the Black Mountain quest and whether Raul is still there. The program uses the starting state.

### Mojave Music Radio

Songs only: one at random, never one of the last 3. Here *Stars of the Midnight Range* plays with its correct file.

## B. Background music (music only, hidden stations)

Same rule: random song, never one of the last 3.

| Station | Quest | Songs |
|---|---|---|
| Ultra-Luxe (classical) | `vUltraLuxeRadioQuest` | 7 entries / 6 files (Vivaldi, Bach, Mozart, *Lakmé*…). Bug: *Spring Song* points to the Mozart concerto |
| Gomorrah lounge music | `vGomorrahRadioQuest` | 6 jazz/blues |
| Tops | `TopsRadioQuest` | 8 |
| Old World Blues, "Mysterious Broadcast" | `NVDLC03RadioBroadcast` | 10 jazz, including Vera's theme |
| Dead Money, Sierra Madre ambient music | `NVDLC01RadioAMBMusic` | 3 |

## C. Short spoken signals (looping messages)

| Signal | Quest | Lines | Notes |
|---|---|---|---|
| NCR Emergency Radio | `vNCREmergencyRadio` | 32 | Bulletins that depend on the game state and a script timer |
| Camp Guardian radio | `vCampGuardianRadio` | 8 | Private Halford calling for help |
| Sierra Madre broadcast (DM) | `NVDLC01RadioCasino` | 25 | Vera's message in 3 versions depending on DLC progress |
| Collar ULF frequencies (DM) | `NVDLC01RadioElijah/Dean/Christine/Dog` | 75 / 59 / 27 / 116 | Change with each act of the DLC |
| Happy Trails (HH) | `NVDLC02RadioMessage` | 6 | Jed Masterson's announcement |
| Hanlon, Lily's grandkids | `VCampGolfHanlon`, `vDialogueLily` | 8 / 7 | Hidden quest recordings |

## Adding a station

The engine runs any radio quest, so adding the B stations means registering them in [`fnv_radio/stations.py`](../../fnv_radio/stations.py) (plugin + quest EditorID), extracting again and checking they behave like in the game. The C signals would need a "game profile" to choose which version of the message plays.
