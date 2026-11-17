#!/bin/bash
# 拼接 Z-Image-Turbo vs Krea-2-Turbo 的同提示词文生图对照图
# 2 行 × 2 列：上排 = 猫场景提示词，下排 = 带货商品图提示词
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
W=/Users/minichen/AI-Models/vpipe-workspace/out
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
OUT=$LAB/t2i-compare.png

norm () { # $1=src $2=dst
  $FF -y -i "$1" -vf "scale=640:640:force_original_aspect_ratio=increase,crop=640:640" "$2" >/dev/null 2>&1
}

norm "$W/t2i-zimage-cat.jpeg"     "$LAB/t2i-z-image-cat.png"
norm "$W/t2i-krea-cat.jpeg"      "$LAB/t2i-krea-cat.png"
norm "$W/t2i-zimage-product.jpeg" "$LAB/t2i-z-image-product.png"
norm "$W/t2i-krea-product.jpeg"  "$LAB/t2i-krea-product.png"

$FF -y -i "$LAB/t2i-z-image-cat.png" -i "$LAB/t2i-krea-cat.png" \
     -i "$LAB/t2i-z-image-product.png" -i "$LAB/t2i-krea-product.png" \
     -filter_complex "[0:v][1:v]hstack=inputs=2[a];[2:v][3:v]hstack=inputs=2[b];[a][b]vstack=inputs=2" \
     -frames:v 1 "$OUT" 2>&1 | tail -2
ls -la "$OUT"
