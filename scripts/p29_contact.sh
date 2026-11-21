#!/bin/bash
# P29 · 印相：A 臂 lanczos 插值 / B 臂 RelayVSR 2×（源片 dance-woman 832×480→1664×960）
# 抽帧位：第 0 / 40 / 80 / 123 帧（124 帧片的 0 / 33% / 65% / 99%）
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D" "$LAB/deliverables/videos"

A="$WS/out/p29/p29-armA-lanczos-1664x960.mp4"
B="$WS/out/p29-relayvsr-x2.mp4"
for f in "$A" "$B"; do [ -f "$f" ] || { echo "缺少产物: $f"; exit 1; }; done

SEL="select='eq(n\,0)+eq(n\,40)+eq(n\,80)+eq(n\,123)',scale=416:240"

"$FF" -v error -y -i "$A" -i "$B" \
  -filter_complex "\
[0:v]${SEL},tile=4x1[r0];\
[1:v]${SEL},tile=4x1[r1];\
[r0][r1]vstack=2" \
  -frames:v 1 "$D/p29-contact-sheet.png"
echo "OK $D/p29-contact-sheet.png"

# ---- 1:1 原尺寸同区域裁切并排（第 40 帧，人物躯干区）----
"$FF" -v error -y -i "$A" -i "$B" \
  -filter_complex "\
[0:v]select='eq(n\,40)',crop=480:360:592:300[a];\
[1:v]select='eq(n\,40)',crop=480:360:592:300[b];\
[a][b]hstack=2" \
  -frames:v 1 "$D/p29-1to1-crop.png"
echo "OK $D/p29-1to1-crop.png"

# ---- 首帧并排 ----
"$FF" -v error -y -i "$A" -i "$B" \
  -filter_complex "\
[0:v]select='eq(n\,0)',scale=560:323[a];\
[1:v]select='eq(n\,0)',scale=560:323[b];\
[a][b]hstack=2" \
  -frames:v 1 "$D/p29-first-frame.png"
echo "OK $D/p29-first-frame.png"

# ---- 成片进交付目录 ----
for n in p29-armA-lanczos-1664x960 p29-relayvsr-x2 p29-relayvsr-x2-r2; do
  if [ -f "$WS/out/p29/$n.mp4" ]; then cp -f "$WS/out/p29/$n.mp4" "$LAB/deliverables/videos/$n.mp4"
  elif [ -f "$WS/out/$n.mp4" ]; then cp -f "$WS/out/$n.mp4" "$LAB/deliverables/videos/$n.mp4"; fi
done
ls -la "$LAB/deliverables/videos/" | grep p29
