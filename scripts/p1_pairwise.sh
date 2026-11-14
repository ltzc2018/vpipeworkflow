#!/bin/bash
# P1 组间对比：加一条参考分别带来多少画面变化
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace

pair () { # $1=视频A $2=视频B $3=标签
  [ -f "$1" ] && [ -f "$2" ] || return
  local s p
  s=$($FF -hide_banner -i "$1" -i "$2" -lavfi "[0:v][1:v]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*" | head -1)
  p=$($FF -hide_banner -i "$1" -i "$2" -lavfi "[0:v][1:v]psnr" -f null - 2>&1 | grep -o "average:[a-z0-9.]*" | head -1)
  echo "| $3 | SSIM ${s#All:} | PSNR ${p#average:} |"
}

echo "| 对比 | 指标 |"
echo "|---|---|"
pair "$WS/out/p1-a-multi-ref.mp4" "$WS/out/p1-b-multi-ref.mp4" "A(1 图) vs B(2 图)：加风格参考的画面变化"
pair "$WS/out/p1-a-multi-ref.mp4" "$WS/out/p1-c-multi-ref.mp4" "A(1 图) vs C(2 图+视频+音轨)"
pair "$WS/out/p1-b-multi-ref.mp4" "$WS/out/p1-c-multi-ref.mp4" "B(2 图) vs C(2 图+视频+音轨)：加动作参考的画面变化"
pair "$WS/out/p1-c-multi-ref.mp4" "$WS/out/p1-d-multi-ref.mp4" "C(4 参) vs D(5 参)：再加一张图的画面变化"
