#!/usr/bin/env python3
"""P1 印相：抽第 0/40/80/末帧拼成一张 4 联联系表

用法: p1_contact.py <video.mp4> <out.png> [帧索引...]
"""
import os
import subprocess
import sys

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"


def frame_count(path):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0", "-f", "rawvideo",
         "-pix_fmt", "gray", "-s", "16x16", "-"],
        capture_output=True, check=True).stdout
    return len(raw) // (16 * 16)


def grab(path, n, out):
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", path, "-vf", f"select=eq(n\\,{n}),scale=480:-1",
         "-fps_mode", "passthrough", "-frames:v", "1", out],
        check=True)


def main():
    vid, out = sys.argv[1], sys.argv[2]
    idx = sys.argv[3:] or ["0", "40", "80", "last"]
    n = frame_count(vid)
    picks = []
    for i in idx:
        picks.append(n - 1 if i == "last" else int(i))
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    files = []
    for p in picks:
        f = os.path.join(tmp, f"f_{p:04d}.png")
        grab(vid, p, f)
        files.append(f)
    subprocess.run(
        [FF, "-y", "-v", "error", "-pattern_type", "glob", "-i", os.path.join(tmp, "f_*.png"),
         "-filter_complex", "tile=4x1:padding=6:color=0x1a1a1a", "-frames:v", "1", out],
        check=True)
    for f in files:
        os.remove(f)
    os.rmdir(tmp)
    print(f"{out}  总帧数={n}  取帧={picks}")


if __name__ == "__main__":
    main()
