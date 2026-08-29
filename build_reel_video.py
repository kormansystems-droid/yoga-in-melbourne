#!/usr/bin/env python3
"""
build_reel_video.py — turn a directory of 1080x1920 PNGs into a reel.

Two things are load-bearing and were both learned the hard way:

  * zoompan needs d=1 with an explicit -framerate on the input. d=n makes
    zoompan emit n frames PER INPUT FRAME, and a 25-second reel came out 191
    seconds. Always ffprobe the output; never trust the encoder's log.
  * hold times are per-frame, not global. The opener is a title card — it is
    read in a beat. A teacher's face is the reason to stop scrolling, so it
    gets three times as long.
"""
import argparse, subprocess, shlex, os, sys, json
from pathlib import Path

W, H, FPS = 1080, 1920, 30
XF = 0.40                      # crossfade seconds


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "json", str(p)],
                         capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def segment(img, secs, zoom_to, out, ffmpeg):
    n = max(1, int(round(secs * FPS)))
    # zoom drifts linearly across the segment; d=1, one output frame per input.
    vf = (f"scale={W*2}:{H*2},"
          f"zoompan=z='1+({zoom_to}-1)*on/{n}':d=1:x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{secs}",
           "-i", str(img), "-vf", vf, "-frames:v", str(n),
           "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--opener", type=float, default=1.3)
    ap.add_argument("--hold", type=float, default=3.4)
    # The last frame is the one the viewer acts on — it carries the route to the
    # site. It needs longer than a teacher hold, and it is the only frame with no
    # following crossfade to bleed into, so its full time is on screen. Defaults
    # to --hold so existing runs are unchanged.
    ap.add_argument("--final", type=float, default=None,
                    help="hold for the LAST frame (default: same as --hold)")
    a = ap.parse_args()

    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
    d = Path(a.dir)
    frames = sorted(f for f in d.glob("*.png"))
    if not frames:
        raise SystemExit(f"no PNGs in {d}")

    tmp = d / "_seg"
    tmp.mkdir(exist_ok=True)
    segs, holds = [], []
    for i, f in enumerate(frames):
        is_opener = "opener" in f.name
        is_final = (i == len(frames) - 1)
        if is_opener:
            secs = a.opener
        elif is_final and a.final is not None:
            secs = a.final
        else:
            secs = a.hold
        # A type-only card gets the gentler push. 1.13 on a page of set text
        # reads as drift rather than emphasis, and pulls the lower rows toward
        # the frame edge where the Ken Burns crop eats them.
        zoom = 1.06 if (is_opener or (is_final and a.final is not None)) else 1.13
        s = tmp / f"seg-{i:02d}.mp4"
        segment(f, secs, zoom, s, ffmpeg)
        segs.append(s); holds.append(secs)
        print(f"  {f.name}  {secs:.2f}s  -> {probe(s):.2f}s")

    # xfade chain. Each offset is where the NEXT clip starts fading in, measured
    # on the accumulated timeline, which shortens by XF at every join.
    ins, filt, prev, acc = [], [], "0:v", holds[0]
    for i in range(1, len(segs)):
        off = acc - XF
        lbl = f"x{i}"
        filt.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[{lbl}]")
        prev = lbl
        acc = off + holds[i]
    cmd = [ffmpeg, "-y"]
    for s in segs:
        cmd += ["-i", str(s)]
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{prev}]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
            str(a.out)]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"{a.out}  {probe(a.out):.2f}s   (expected {acc:.2f}s)")


if __name__ == "__main__":
    main()
