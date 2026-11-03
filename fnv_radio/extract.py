"""Build the local library: station data (JSON) and audio files taken from the game.

Library layout (paths mirror the game's Data folder):
    library/library.json            what was extracted, durations of every file
    library/stations/<id>.json      dialogue graph of each station
    library/sound/songs/...         every song of the game (mp3)
    library/sound/voice/...         voice lines used by the supported stations
"""
import collections
import concurrent.futures
import glob
import json
import os
import re
import struct
import subprocess
import time

from .bsa import BSA
from .esm import iter_records, read_masters
from .stations import STATIONS

RECORD_TYPES = {"QUST", "DIAL", "INFO", "SOUN", "SCPT", "GLOB", "PERK"}
OPS = ["==", "!=", ">", ">=", "<", "<="]
FUNCS = {
    46: "GetDead", 56: "GetQuestRunning", 58: "GetStage", 59: "GetStageDone", 72: "GetIsID",
    74: "GetGlobalValue", 79: "GetQuestVariable", 420: "GetObjectiveCompleted", 449: "HasPerk",
    546: "GetQuestCompleted",
}
INFO_FLAGS = {0x01: "Goodbye", 0x02: "Random", 0x04: "SayOnce", 0x08: "RunImmediately",
              0x20: "RandomEnd"}
VOICE_RE = re.compile(r"_([0-9a-f]{8})_(\d+)\.ogg$")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def u32(b, o=0):
    return struct.unpack_from("<I", b, o)[0]


class GameFiles:
    """Every file of the game's sound folders: loose files override BSA archives."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.bsa_files = {}
        for path in sorted(glob.glob(os.path.join(data_dir, "*.bsa"))):
            archive = BSA(path)
            for name in archive.files:
                if name.startswith("sound\\"):
                    self.bsa_files[name] = archive

    def names(self):
        loose = set()
        for path in glob.glob(os.path.join(self.data_dir, "Sound", "**", "*"), recursive=True):
            if os.path.isfile(path):
                loose.add(os.path.relpath(path, self.data_dir).lower())
        return set(self.bsa_files) | loose

    def read(self, name):
        loose = os.path.join(self.data_dir, name)
        if os.path.isfile(loose):
            with open(loose, "rb") as f:
                return f.read()
        return self.bsa_files[name].read(name)


class LoadOrder:
    """Records of a plugin and its masters, addressed as (owner plugin, local FormID)."""

    def __init__(self, data_dir, plugin):
        self.data_dir = data_dir
        self.masters = {}
        self.records = {}
        for name in self._masters(plugin) + [plugin]:
            for r in iter_records(os.path.join(data_dir, name), RECORD_TYPES):
                key = self.key(name, r.formid)
                r.parent_dial = self.key(name, r.parent_dial) if r.parent_dial else None
                self.records[key] = (name, r)

    def _masters(self, plugin):
        if plugin not in self.masters:
            self.masters[plugin] = read_masters(os.path.join(self.data_dir, plugin))
        return self.masters[plugin]

    def key(self, plugin, formid):
        names = self._masters(plugin) + [plugin]
        owner = names[min(formid >> 24, len(names) - 1)]
        return owner.lower(), formid & 0xFFFFFF

    def get(self, plugin, formid):
        return self.records.get(self.key(plugin, formid), (None, None))[1]

    def name(self, plugin, formid):
        r = self.get(plugin, formid)
        return (r.edid if r else None) or f"{formid:08X}"


def export_station(station, load, voices):
    """Turn the station's quest into a JSON-friendly dialogue graph."""
    plugin = station.plugin
    quest_key, quest = next((k, r) for k, (src, r) in load.records.items()
                            if r.type == "QUST" and r.edid == station.quest and src == plugin)

    qvars = {}
    script = load.get(plugin, u32(quest.get("SCRI"))) if quest.get("SCRI") else None
    for k, v in (script.subs if script else []):
        if k == "SLSD":
            idx = u32(v)
        elif k == "SCVR":
            qvars[idx] = v.split(b"\0")[0].decode("cp1252")

    def cond(v):
        t = v[0]
        fn = struct.unpack_from("<H", v, 8)[0]
        p1, p2 = u32(v, 12), u32(v, 16)
        fname = FUNCS.get(fn, f"Function{fn}")
        if fn == 79:
            own = load.key(plugin, p1) == quest_key
            arg = f"{load.name(plugin, p1)}.{qvars.get(p2, p2) if own else p2}"
        elif fn == 420:
            arg = f"{load.name(plugin, p1)}, {p2}"
        elif fn == 46 and p1 == 0:
            arg = "<ref>"
        else:
            arg = load.name(plugin, p1)
        value = load.name(plugin, u32(v, 4)) if t & 0x04 else round(struct.unpack_from("<f", v, 4)[0], 3)
        return {"function": fname, "args": arg, "op": OPS[t >> 5], "value": value, "or": bool(t & 1)}

    topics = collections.defaultdict(list)
    for key, (src, r) in load.records.items():
        if r.type != "INFO" or not r.get("QSTI") or load.key(src, u32(r.get("QSTI"))) != quest_key:
            continue
        dial = load.records.get(r.parent_dial, (None, None))[1]
        texts = [v.split(b"\0")[0].decode("cp1252", "replace") for k, v in r.subs if k == "NAM1"]
        sounds = [u32(v, 16) for k, v in r.subs if k == "TRDT" and u32(v, 16)]
        sctx = r.get("SCTX")
        fid = f"{r.formid:08X}"
        line = {
            "formid": fid,
            "text": " ".join(texts),
            "flags": [n for b, n in INFO_FLAGS.items() if r.get("DATA")[2] & b],
            "conditions": [cond(v) for v in r.all("CTDA")],
            "choices": [load.name(src, u32(v)) for v in r.all("TCLT")],
            "script": sctx.decode("cp1252", "replace").replace("\r\n", "\n").strip() if sctx else "",
        }
        if sounds:
            snd = load.get(src, sounds[0])
            line["song"] = "sound\\" + snd.zstr("FNAM").lower()
            if fid in station.sound_fixes:
                line["song_fixed"] = station.sound_fixes[fid]
        else:
            line["voice"] = [path for _, path in sorted(voices.get(key, {}).items())]
        topics[dial.edid].append(line)

    return {"id": station.id, "name": station.name, "quest": station.quest,
            "quest_variables": {str(k): v for k, v in sorted(qvars.items())},
            "topics": dict(topics)}


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    return float(out.stdout.strip() or 0)


def build_library(game_dir, library_dir, progress=lambda msg, frac: None):
    """Extract every song plus the voices of the supported stations. Returns a summary."""
    data_dir = os.path.join(game_dir, "Data")
    if not os.path.isfile(os.path.join(data_dir, "FalloutNV.esm")):
        raise FileNotFoundError(f"No se encuentra FalloutNV.esm en {data_dir}")

    progress("Leyendo archivos BSA…", 0.02)
    game = GameFiles(data_dir)
    all_names = game.names()
    voices = collections.defaultdict(dict)  # (plugin, local formid) -> {response: game path}
    for name in all_names:
        parts = name.split("\\")
        m = VOICE_RE.search(name)
        if m and len(parts) == 5 and parts[1] == "voice":
            voices[(parts[2], int(m.group(1), 16) & 0xFFFFFF)][int(m.group(2))] = name

    os.makedirs(os.path.join(library_dir, "stations"), exist_ok=True)
    wanted = {n for n in all_names if n.startswith("sound\\songs\\") and n.endswith(".mp3")}
    exported = []
    for i, station in enumerate(STATIONS.values()):
        progress(f"Leyendo {station.plugin} ({station.name})…", 0.05 + 0.25 * i / len(STATIONS))
        data = export_station(station, LoadOrder(data_dir, station.plugin), voices)
        for lines in data["topics"].values():
            for line in lines:
                wanted.update(line.get("voice", []))
                wanted.update(p for p in (line.get("song"), line.get("song_fixed")) if p)
        with open(os.path.join(library_dir, "stations", f"{station.id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        exported.append(station.id)

    wanted = sorted(n for n in wanted if n in all_names)
    for i, name in enumerate(wanted):
        if i % 10 == 0:
            progress(f"Extrayendo audio {i + 1}/{len(wanted)}…", 0.3 + 0.5 * i / len(wanted))
        dest = os.path.join(library_dir, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(game.read(name))

    progress("Midiendo duraciones…", 0.8)
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        durations = dict(zip(wanted, pool.map(lambda n: probe_duration(os.path.join(library_dir, n)), wanted)))

    summary = {
        "game_dir": game_dir,
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "stations": exported,
        "songs": sum(1 for n in wanted if n.startswith("sound\\songs\\")),
        "voices": sum(1 for n in wanted if n.startswith("sound\\voice\\")),
        "durations": durations,
    }
    with open(os.path.join(library_dir, "library.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    progress("Biblioteca lista.", 1.0)
    return summary


def load_library(library_dir):
    path = os.path.join(library_dir, "library.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_station(library_dir, station_id):
    with open(os.path.join(library_dir, "stations", f"{station_id}.json"), encoding="utf-8") as f:
        return json.load(f)
