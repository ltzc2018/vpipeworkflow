#!/bin/bash
# P18 · 印相（contact sheet）：静态参考地板 + euler 臂 + dmd 臂
#
# 抽帧位：第 0 / 7 / 14 / 21 帧（22 帧片的 0 / 32% / 64% / 96%）
# 布局：3 行 × 4 列 —— 行 = [静态参考地板, euler, dmd]
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D"

A="$LAB/p13/static-768p-22f.mp4"          # 静态参考地板（第 3 轮产物）
B="$WS/out/p18-euler.mp4"                   # A 臂：euler（接 sampler 端口）
C="$WS/out/p18-dmd.mp4"                     # B 臂：dmd（每步重注噪）

for f in "$A" "$B" "$C"; do
  [ -f "$f" ] || { echo "缺少产物: $f"; exit 1; }
done

SEL="select='eq(n\,0)+eq(n\,7)+eq(n\,14)+eq(n\,21)',scale=336:192"

"$FF" -v error -y \
  -i "$A" -i "$B" -i "$C" \
  -filter_complex "\
[0:v]${SEL},tile=4x1[r0];\
[1:v]${SEL},tile=4x1[r1];\
[2:v]${SEL},tile=4x1[r2];\
[r0][r1][r2]vstack=3" \
  -frames:v 1 "$D/p18-contact-sheet.png"
echo "已生成 $D/p18-contact-sheet.png"

# 首帧两臂并排 —— 用于「换采样器 = 换场景」的目视交叉验证
"$FF" -v error -y -i "$B" -i "$C" \
  -filter_complex "\
[0:v]select='eq(n\,0)',scale=560:320[a];\
[1:v]select='eq(n\,0)',scale=560:320[b];\
[a][b]hstack=2" \
  -frames:v 1 "$D/p18-first-frame-2arms.png"
echo "已生成 $D/p18-first-frame-2arms.png"

# 首帧 + 末帧并排（两臂各两帧）—— 看纹理是否随时间累积
"$FF" -v error -y -i "$B" -i "$C" \
  -filter_complex "\
[0:v]select='eq(n\,0)+eq(n\,21)',scale=560:320,tile=2x1[a];\
[1:v]select='eq(n\,0)+eq(n\,21)',scale=560:320,tile=2x1[b];\
[a][b]vstack=2" \
  -frames:v 1 "$D/p18-first-last-2arms.png"
echo "已生成 $D/p18-first-last-2arms.png"

# 成片进交付目录
mkdir -p "$LAB/deliverables/videos"
for n in p18-euler p18-dmd p18-dmd2; do
  [ -f "$WS/out/$n.mp4" ] && cp -f "$WS/out/$n.mp4" "$LAB/deliverables/videos/$n.mp4" && echo "已复制 $n.mp4"
done
