"""Simulate many Radio New Vegas blocks and check they follow the rules found in the ESM.

Run from the project folder after extracting the library:
    python tests/check_rules.py
"""
import collections
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from fnv_radio.engine import GameProfile, RadioStation  # noqa: E402
from fnv_radio.extract import load_station  # noqa: E402

BLOCKS = 5000


def main():
    data = load_station(os.path.join(ROOT, "library"), "rnv")
    topic = {l["formid"]: t for t, lines in data["topics"].items() for l in lines}
    station = RadioStation(data, GameProfile(), seed=1)
    history, errors = [], []
    songs_per_block = collections.Counter()

    for b in range(BLOCKS):
        lines = list(station.conversation())
        topics = [topic[l["formid"]] for l in lines]
        songs = [l for l in lines if "song" in l]
        intro = next((t for t in topics if t.startswith("RNVMusicIntro")), None)
        if topics[0] != "RadioHello":
            errors.append(f"block {b}: starts with {topics[0]}")
        if topics.count("RNVNewsStory") != 2:
            errors.append(f"block {b}: {topics.count('RNVNewsStory')} news stories")
        if intro == "RNVMusicIntroGeneric" and len(songs) != 3:
            errors.append(f"block {b}: generic intro but {len(songs)} songs")
        if intro == "RNVMusicIntroSpecific" and len(songs) != 1:
            errors.append(f"block {b}: specific intro but {len(songs)} songs")
        if any(not l["voice"] for l in lines if "song" not in l):
            errors.append(f"block {b}: spoken line without audio")
        for s in songs:
            if s["formid"] in history[-3:]:
                errors.append(f"block {b}: {s['text']} repeated within 3 songs")
            history.append(s["formid"])
        songs_per_block[len(songs)] += 1

    print(f"{BLOCKS} blocks, {len(errors)} rule violations, songs per block: {dict(songs_per_block)}")
    for e in errors[:10]:
        print("  !", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
