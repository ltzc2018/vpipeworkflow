#!/bin/bash
# P22c · 印相（contact sheet）：1920×1152 真值 vs FlashVSR+ Turbo 超分
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D"

REF="$WS/out/p22/p22-src-1920x1152-ref.mp4"
C="$WS/out/p22/p22c-armC-plus-1920x1152.mp4"

# 抽帧位：第 0 / 16 / 32 / 48 帧 (49 帧片)
SEL="select='eq(n\,0)+eq(n\,16)+eq(n\,32)+eq(n\,48)',scale=480:288"

if [ -f "$REF" ] && [ -f "$C" ]; then
    "$FF" -v error -y -i "$REF" -i "$C" \
      -filter_complex "[0:v]${SEL},tile=4x1[r0]; [1:v]${SEL},tile=4x1[r1]; [r0][r1]vstack=2" \
      -frames:v 1 "$D/p22c-contact-sheet.png"
    echo "已生成 $D/p22c-contact-sheet.png"

    # 1:1 裁切对比
    "$FF" -v error -y -i "$REF" -i "$C" \
      -filter_complex "[0:v]select='eq(n\,16)',crop=640:384:640:384[r]; [1:v]select='eq(n\,16)',crop=640:384:640:384[c]; [r][c]hstack=2" \
      -frames:v 1 "$D/p22c-1to1-crop.png"
    echo "已生成 $D/p22c-1to1-crop.png"
fi
