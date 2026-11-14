#!/bin/bash
# 校验相位相关 dx 的符号约定：造一条「已知方向」的横移片，看脚本报正还是负
set -eu
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
T=$(mktemp -d)
# 裁切窗口从右往左扫 -> 画面内容相对画框向右移动
$FF -y -v error -i "$WS/refs/motion-beach-124f.mp4" \
  -vf "crop=480:276:(123-n)*3.902:134,scale=832:480:flags=lanczos" \
  -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -c:a copy "$T/pan-left.mp4"
echo "造好：内容向【右】移动的片子 -> 脚本报告："
python3 /Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/scripts/p1_motion.py "$T/pan-left.mp4" | grep -E "net="
rm -rf "$T"
