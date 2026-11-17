#!/bin/bash
# P15 · 印相（contact sheet）：四臂可复现性对照
#
# 抽帧位：第 0 / 7 / 14 / 21 帧（22 帧片的 0 / 32% / 64% / 96%）
# 布局：5 行 × 4 列 —— 行 = [静态参考地板, at1, at2, af1, af2]
#        at1/at2 = autotune 开（默认）；af1/af2 = autotune 关
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D"

A="$LAB/p13/static-768p-22f.mp4"
B="$WS/out/p15-repro-at1.mp4"
C="$WS/out/p15-repro-at2.mp4"
D1="$WS/out/p15-repro-af1.mp4"
E="$WS/out/p15-repro-af2.mp4"

for f in "$A" "$B" "$C" "$D1" "$E"; do
  [ -f "$f" ] || { echo "缺少产物: $f"; exit 1; }
done

"$FF" -v error -y \
  -i "$A" -i "$B" -i "$C" -i "$D1" -i "$E" \
  -filter_complex "\
[0:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r0];\
[1:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r1];\
[2:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r2];\
[3:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r3];\
[4:v]select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192,tile=4x1[r4];\
[r0][r1][r2][r3][r4]vstack=5" \
  -frames:v 1 "$D/p15-contact-sheet.png"
echo "已生成 $D/p15-contact-sheet.png"

# 首帧四臂并排：看 autotune 开关是否改变了画面
"$FF" -v error -y -i "$B" -i "$C" -i "$D1" -i "$E" \
  -filter_complex "\
[0:v]select='eq(n\,0)',scale=448:256[a];\
[1:v]select='eq(n\,0)',scale=448:256[b];\
[2:v]select='eq(n\,0)',scale=448:256[c];\
[3:v]select='eq(n\,0)',scale=448:256[d];\
[a][b][c][d]hstack=4" \
  -frames:v 1 "$D/p15-first-frame-4arms.png"
echo "已生成 $D/p15-first-frame-4arms.png"

# af1 与 af2 若逐位相同，两段叠在一起应当完全无差 —— 直接算像素差做可视化
"$FF" -v error -y -i "$D1" -i "$E" \
  -filter_complex "\
[0:v]format=gray[a];[1:v]format=gray[b];\
[a][b]blend=all_mode=difference,scale=336:192,format=gray,\
 lut=y='if(gt(val\,0)\,255\,0)'" \
  -frames:v 1 "$D/p15-af1-af2-diff.png"
echo "已生成 $D/p15-af1-af2-diff.png（纯黑 = 逐帧完全一致）"

# 把成片复制进交付目录
for n in p15-repro-at1 p15-repro-at2 p15-repro-af1 p15-repro-af2; do
  [ -f "$WS/out/$n.mp4" ] && cp -f "$WS/out/$n.mp4" "$LAB/deliverables/videos/$n.mp4" && echo "已复制 $n.mp4"
done
