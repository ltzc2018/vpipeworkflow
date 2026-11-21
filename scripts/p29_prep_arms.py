#!/usr/bin/env python3
"""P29 臂 A（lanczos 插值基线）生成：832x480 → 1664x960，与主臂 B 同源同规格"""
import subprocess, os

FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
SRC = "/Users/minichen/AI-Models/vpipe-workspace/out/dance-woman-5s.mp4"
OUT = "/Users/minichen/AI-Models/vpipe-workspace/out/p29/p29-armA-lanczos-1664x960.mp4"

cmd = [FF, "-y", "-v", "error", "-i", SRC,
       "-vf", "scale=1664:960:flags=lanczos",
       "-c:v", "libx264", "-preset", "slow", "-crf", "14",
       "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
       "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
print("OK", OUT, os.path.getsize(OUT))
