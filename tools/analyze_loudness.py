"""Measure the loudness of every piece inside a generated broadcast.

Usage:
    python tools/analyze_loudness.py output/rnv_semilla7_60min.mp3

Reads the <name>.timeline.json written next to the audio by the generator, measures
each piece with the EBU R128 meter (and its source file in library/) and writes
<name>.loudness.txt.
"""
import json
import os
import re
import subprocess
import sys

LIBRARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library")


def ebur128(path, start=None, length=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}"]
    cmd += ["-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    log = subprocess.run(cmd, capture_output=True, text=True).stderr
    summary = log[log.rfind("Summary:"):]
    get = lambda key: float(re.search(rf"{key}:\s+(-?[\d.]+|-inf)", summary).group(1)
                            .replace("-inf", "-99"))
    return {"lufs": get("I"), "lra": get("LRA"), "peak": get("Peak")}


def main():
    audio = sys.argv[1]
    base = os.path.splitext(audio)[0]
    with open(base + ".timeline.json", encoding="utf-8") as f:
        items = json.load(f)

    rows = []
    for it in items:
        out = ebur128(audio, it["start"], it["duration"])
        src = ebur128(os.path.join(LIBRARY, it["file"]))
        rows.append((it, src, out))

    whole = ebur128(audio)
    lines = [f"Sonoridad de {audio} (cambio = generado - original)",
             f"Archivo completo: {whole['lufs']:.1f} LUFS, LRA {whole['lra']:.1f} LU, pico {whole['peak']:.1f} dBTP",
             "",
             f"{'inicio':>6}  {'tipo':<22} {'orig LUFS':>9} {'LUFS':>6} {'cambio':>6} {'LRA':>5} {'pico':>6}  pieza",
             "-" * 108]
    for it, src, out in rows:
        t = it["start"]
        label = "CANCIÓN" if it["kind"] == "song" else it["topic"]
        lines.append(f"{int(t // 60):02d}:{int(t % 60):02d}  {label:<22} {src['lufs']:9.1f} "
                     f"{out['lufs']:6.1f} {out['lufs'] - src['lufs']:+6.1f} {out['lra']:5.1f} {out['peak']:6.1f}  "
                     f"{it['text'][:45]}")

    def stats(kind, label):
        sel = [(s, o) for it, s, o in rows if it["kind"] == kind]
        if not sel:
            return
        vals = [o["lufs"] for _, o in sel]
        orig = [s["lufs"] for s, _ in sel]
        lines.append(f"{label:<10} n={len(sel):3}  generado: media {sum(vals) / len(vals):6.1f} LUFS, "
                     f"rango {min(vals):6.1f} … {max(vals):6.1f} | original: rango {min(orig):6.1f} … {max(orig):6.1f}")

    lines += ["", "Resumen"]
    stats("song", "Canciones")
    stats("voice", "Voces")

    report = "\n".join(lines)
    with open(base + ".loudness.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
