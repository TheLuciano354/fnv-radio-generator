"""Build a broadcast timeline from a seed and render it to WAV, MP3 or Opus."""
import json
import os
import re
import shutil
import subprocess
import tempfile

from .engine import GameProfile, RadioStation

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

FORMATS = {
    "wav": {"label": "WAV (PCM 16 bits)", "ext": ".wav", "rate": 44100,
            "args": ["-c:a", "pcm_s16le", "-rf64", "auto"]},
    "mp3": {"label": "MP3 256 kbps VBR", "ext": ".mp3", "rate": 44100,
            "args": ["-c:a", "libmp3lame", "-abr", "1", "-b:a", "256k"]},
    "opus": {"label": "Opus 128 kbps VBR", "ext": ".opus", "rate": 48000,
             "args": ["-c:a", "libopus", "-b:a", "128k", "-vbr", "on"]},
}
TAG_RE = re.compile(r"\{[^}]*\}|<[^>]*>")
# Leading "{Rhonda}", "[Raúl]", "{Primm Slim:}" or "{Tabitha, gruñendo}": who is speaking.
NAME = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ]*"
SPEAKER_RE = re.compile(rf"^\s*[\[{{]\s*({NAME}(?: {NAME})?)\s*:?\s*(?:,[^\]}}]*)?[\]}}]\s*")


def ffmpeg_available():
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def clean_text(text):
    """Drop the voice-actor directions ({Pausa}, {Eslogan}, <Risas>…), keep who speaks."""
    speaker = ""
    m = SPEAKER_RE.match(text)
    if m:
        speaker, text = m.group(1) + ": ", text[m.end():]
    return speaker + re.sub(r"\s+", " ", TAG_RE.sub(" ", text)).strip()


def song_title(text, path):
    """Title from the line text ("{Song 1 Goin Under}", '"BIG IRON"'), else from the file name."""
    title = re.sub(r'[{}"]', "", text).strip()
    title = re.sub(r"^Song\s*\d+\s*-?\s*", "", title, flags=re.I).strip()
    if not title:
        title = re.sub(r"^mus_", "", os.path.splitext(os.path.basename(path))[0])
        title = title.replace("_", " ").strip().title()
    return title


def build_timeline(station_data, library, library_dir, seed, minutes, wild_wasteland=False,
                   fix_bugs=True, avoid_repeated_lines=True, gap=0.35):
    """Return the list of pieces (songs and voice lines) that fill `minutes` of radio.

    The broadcast ends at the end of a conversation or after the first song that
    reaches the target (some stations, like Black Mountain, chain for half an hour).
    """
    perks = {"WildWasteland"} if wild_wasteland else set()
    station = RadioStation(station_data, GameProfile(perks=perks), seed=seed, fix_bugs=fix_bugs,
                           avoid_repeated_lines=avoid_repeated_lines)
    durations = library["durations"]
    topic_of = {l["formid"]: t for t, lines in station_data["topics"].items() for l in lines}
    target = minutes * 60

    items, total, block = [], 0.0, 0
    while total < target:
        block += 1
        empty = True
        for line in station.conversation():
            empty = False
            if "song" in line:
                files = [station.song_file(line)]
                kind, text = "song", song_title(line["text"], files[0])
            else:
                files = line["voice"]
                kind, text = "voice", clean_text(line["text"])
            for path in files:
                if path not in durations:
                    continue
                items.append({"block": block, "kind": kind, "topic": topic_of[line["formid"]],
                              "text": text, "file": path, "start": total,
                              "duration": durations[path]})
                total += durations[path] + gap
            if kind == "song" and total >= target:
                return items
        if empty:
            raise RuntimeError("La emisora no tiene ninguna línea válida para empezar.")
    return items


def stamp(seconds):
    h, rest = divmod(int(seconds), 3600)
    return f"{h}:{rest // 60:02d}:{rest % 60:02d}" if h else f"{rest // 60:02d}:{rest % 60:02d}"


def tracklist_text(items, header):
    out, last = [header, ""], 0
    for it in items:
        if it["block"] != last:
            out.append(f"=== Bloque {it['block']} ===")
            last = it["block"]
        label = "♪ CANCIÓN" if it["kind"] == "song" else it["topic"]
        out.append(f"[{stamp(it['start'])}] {label:<22} {it['text']}")
    return "\n".join(out) + "\n"


def _ffmpeg(*args):
    # stdin and output are redirected explicitly: a windowed .exe has no console handles.
    proc = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, creationflags=NO_WINDOW)
    if proc.returncode:
        raise RuntimeError(f"ffmpeg falló: {proc.stderr.strip()[-500:]}")


def render(items, library_dir, out_path, fmt="mp3", loudness="original", gap=0.35, header="",
           progress=lambda msg, frac: None, cancelled=lambda: False):
    """Decode every piece to a common PCM format, concatenate and encode once.

    Next to the audio it writes <name>.txt (tracklist) and <name>.timeline.json.
    """
    spec = FORMATS[fmt]
    rate = str(spec["rate"])
    level = ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"] if loudness == "normalized" else []
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fnvradio_") as tmp:
        silence = os.path.join(tmp, "gap.wav")
        _ffmpeg("-f", "lavfi", "-i", f"anullsrc=r={rate}:cl=stereo", "-t", str(gap), "-c:a", "pcm_s16le",
                silence)
        decoded = {}
        unique = list(dict.fromkeys(it["file"] for it in items))
        for i, name in enumerate(unique):
            if cancelled():
                raise InterruptedError
            progress(f"Preparando pieza {i + 1}/{len(unique)}", 0.85 * i / len(unique))
            wav = os.path.join(tmp, f"{i:05d}.wav")
            _ffmpeg("-i", os.path.join(library_dir, name), *level, "-ar", rate, "-ac", "2",
                    "-c:a", "pcm_s16le", wav)
            decoded[name] = wav

        listing = os.path.join(tmp, "list.txt")
        with open(listing, "w", encoding="utf-8") as f:
            for it in items:
                f.write(f"file '{decoded[it['file']]}'\nfile '{silence}'\n")
        progress("Codificando…", 0.87)
        _ffmpeg("-f", "concat", "-safe", "0", "-i", listing, "-ar", rate, *spec["args"], out_path)

    base = os.path.splitext(out_path)[0]
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write(tracklist_text(items, header))
    with open(base + ".timeline.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    progress("Terminado.", 1.0)
