#!/usr/bin/env python3
"""P3 印相：抽首/中/末等若干帧拼成联系表（帧数可变，支持 124 帧与 362 帧两种规格）

用法: p3_contact.py <video.mp4> <out.png> [帧索引...]
      不给帧索引时自动取 0 / 1/3 / 2/3 / 末帧
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


def grab(path, n, out, width=480):
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", path, "-vf", f"select=eq(n\\,{n}),scale={width}:-1",
         "-fps_mode", "passthrough", "-frames:v", "1", out],
        check=True)


def main():
    vid, out = sys.argv[1], sys.argv[2]
    n = frame_count(vid)
    idx = sys.argv[3:]
    if not idx:
        idx = ["0", str(n // 3), str(2 * n // 3), "last"]
    picks = []
    for i in idx:
        p = n - 1 if i == "last" else int(i)
        picks.append(max(0, min(p, n - 1)))
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    files = []
    for p in picks:
        f = os.path.join(tmp, f"f_{p:04d}.png")
        grab(vid, p, f)
        files.append(f)
    cols = 4 if len(files) > 4 else len(files)
    rows = (len(files) + cols - 1) // cols
    subprocess.run(
        [FF, "-y", "-v", "error", "-pattern_type", "glob", "-i", os.path.join(tmp, "f_*.png"),
         "-filter_complex", f"tile={cols}x{rows}:padding=6:color=0x1a1a1a",
         "-frames:v", "1", out],
        check=True)
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass  # 沙箱环境下目录删除可能被拒，不影响产物
    print(f"{out}  总帧数={n}  取帧={picks}")


if __name__ == "__main__":
    main()
