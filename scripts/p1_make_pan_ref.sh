#!/bin/bash
# 造一条「可测量的水平摇摄」动作参考视频：
# 在已有的跟踪镜头素材上开一个 480x276 的窗口匀速横扫，得到明确的全局横移。
set -eu
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
SRC="$WS/refs/motion-beach-124f.mp4"
DST="$WS/refs/motion-pan-right-124f.mp4"

$FF -y -v error -i "$SRC" \
  -vf "crop=480:276:n*3.902:134,scale=832:480:flags=lanczos" \
  -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -c:a copy "$DST"

ls -la "$DST"
