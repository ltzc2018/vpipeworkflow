#!/bin/bash
# P13 · 印相（contact sheet）：把三臂静态场景输出 + 静态参考地板的抽帧拼成一张图
#
# 抽帧位：第 0 / 7 / 14 / 21 帧（22 帧片的 0 / 32% / 64% / 96%）
# 布局：4 行 × 4 列 —— 行 = [静态参考地板, shift6, shift12, er-sde]
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
OUT=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D"

A="$LAB/p13/static-768p-22f.mp4"
B="$OUT/out/p13-static-shift6.mp4"
C="$OUT/out/p13-static-shift12.mp4"
E="$OUT/out/p13-static-shifter-sde.mp4"

for f in "$A" "$B" "$C" "$E"; do
  [ -f "$f" ] || { echo "缺少产物: $f"; exit 1; }
done

"$FF" -v error -y \
  -i "$A" -i "$B" -i "$C" -i "$E" \
  -filter_complex "\
[0:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r0];\
[1:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r1];\
[2:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r2];\
[3:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r3];\
[r0][r1][r2][r3]vstack=4" \
  -frames:v 1 "$D/p13-contact-sheet.png"

echo "已生成 $D/p13-contact-sheet.png"

# 再单独出一张「首帧三臂并排」用于看 shift 是否换了场景
"$FF" -v error -y -i "$B" -i "$C" -i "$E" \
  -filter_complex "\
[0:v]select='eq(n\,0)',scale=448:256[a];\
[1:v]select='eq(n\,0)',scale=448:256[b];\
[2:v]select='eq(n\,0)',scale=448:256[c];\
[a][b][c]hstack=3" \
  -frames:v 1 "$D/p13-first-frame-3arms.png"
echo "已生成 $D/p13-first-frame-3arms.png"

# 把成片复制进交付目录
for n in p13-static-shift6 p13-static-shift12 p13-static-shifter-sde; do
  [ -f "$OUT/out/$n.mp4" ] && cp -f "$OUT/out/$n.mp4" "$LAB/deliverables/videos/$n.mp4" && echo "已复制 $n.mp4"
done
cp -f "$LAB/p13/static-768p-22f.mp4" "$LAB/deliverables/videos/p13-static-floor-22f.mp4" && echo "已复制 p13-static-floor-22f.mp4"
