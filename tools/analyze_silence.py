"""Measure leading and trailing silence of every audio file in the library.

Usage:
    python tools/analyze_silence.py [threshold_db]

Prints, for each song and the voice lines in total, how many seconds of silence
there are at the start and at the end (below threshold_db, default -60 dB).
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys

LIBRARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library")


def edges(path, threshold, duration):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                          f"silencedetect=noise={threshold}dB:d=0.05", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    lead = ends[0] if starts and starts[0] <= 0.01 and ends else 0.0
    # a trailing silence has a start but no end (or ends at the very end of the file)
    tail = 0.0
    if starts and (len(ends) < len(starts) or ends[-1] >= duration - 0.05):
        tail = duration - starts[-1]
    return lead, tail


def main():
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else -60
    with open(os.path.join(LIBRARY, "library.json"), encoding="utf-8") as f:
        durations = json.load(f)["durations"]
    names = sorted(durations)
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        res = dict(zip(names, pool.map(lambda n: edges(os.path.join(LIBRARY, n), threshold, durations[n]), names)))

    print(f"Silencio al inicio / al final (umbral {threshold} dB)\n")
    for n in names:
        if n.startswith("sound\\songs\\"):
            lead, tail = res[n]
            print(f"{lead:5.2f} s  {tail:5.2f} s  {n.rsplit(chr(92), 1)[1]}")
    voices = [res[n] for n in names if n.startswith("sound\\voice\\")]
    if voices:
        print(f"\nLocuciones ({len(voices)}): inicio medio {sum(v[0] for v in voices) / len(voices):.2f} s, "
              f"final medio {sum(v[1] for v in voices) / len(voices):.2f} s, "
              f"máximo {max(max(v) for v in voices):.2f} s")


if __name__ == "__main__":
    main()
