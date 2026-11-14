#!/bin/bash
# P1 素材准备：把熊猫参考图裁一个特写，用作 D 组的第 3 张图参考
set -eu
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
$FF -y -v error -i "$WS/refs/klein-multi-ref-panda.jpg" \
  -vf "crop=512:512:256:256,scale=1024:1024:flags=lanczos" \
  -pix_fmt yuvj420p "$WS/refs/klein-multi-ref-panda-crop.jpg"
ls -la "$WS/refs/klein-multi-ref-panda-crop.jpg"
