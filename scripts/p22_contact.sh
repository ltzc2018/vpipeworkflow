#!/bin/bash
# P22 · 印相（contact sheet）：真值 / A 臂 lanczos 插值 / B 臂 FlashVSR 4× 超分
#
# 抽帧位：第 0 / 8 / 16 / 24 帧（25 帧片的 0 / 33% / 67% / 96%）
# 布局：3 行 × 4 列 —— 行 = [真值 ref(768p→1280×768), A(lanczos 插值), B(FlashVSR)]
# 另出一张 **1:1 不缩放** 的同区域裁切并排 —— 缩略图会藏掉纹理差异，必须给原尺寸
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
FF=$HOME/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
D=$LAB/deliverables/images
mkdir -p "$D" "$LAB/deliverables/videos"

REF="$WS/out/p22/p22-ref-1280x768.mkv"                  # 真值（原始 768p lanczos 到 1280×768）
A="$WS/out/p22/p22-armA-lanczos-1280x768.mp4"            # A 臂：纯 lanczos 插值
B="$WS/out/p22/p22-armB-flashvsr-1280x768.mp4"           # B 臂：FlashVSR 原生 Metal 4× 超分

for f in "$REF" "$A" "$B"; do
  [ -f "$f" ] || { echo "缺少产物: $f"; exit 1; }
done

SEL="select='eq(n\,0)+eq(n\,8)+eq(n\,16)+eq(n\,24)',scale=320:192"

"$FF" -v error -y \
  -i "$REF" -i "$A" -i "$B" \
  -filter_complex "\
[0:v]${SEL},tile=4x1[r0];\
[1:v]${SEL},tile=4x1[r1];\
[2:v]${SEL},tile=4x1[r2];\
[r0][r1][r2]vstack=3" \
  -frames:v 1 "$D/p22-contact-sheet.png"
echo "已生成 $D/p22-contact-sheet.png"

# ---- 1:1 原尺寸裁切并排（同一区域，三臂）—— 看真实纹理差异的唯一有效视图 ----
"$FF" -v error -y -i "$REF" -i "$A" -i "$B" \
  -filter_complex "\
[0:v]select='eq(n\,8)',crop=480:288:400:240[r];\
[1:v]select='eq(n\,8)',crop=480:288:400:240[a];\
[2:v]select='eq(n\,8)',crop=480:288:400:240[b];\
[r][a][b]hstack=3" \
  -frames:v 1 "$D/p22-1to1-crop-3arms.png"
echo "已生成 $D/p22-1to1-crop-3arms.png"

# ---- 同一区域再放大 2×（更便于 LFM3-VL 粗判纹理） ----
"$FF" -v error -y -i "$REF" -i "$A" -i "$B" \
  -filter_complex "\
[0:v]select='eq(n\,8)',crop=320:192:480:288[r];\
[1:v]select='eq(n\,8)',crop=320:192:480:288[a];\
[2:v]select='eq(n\,8)',crop=320:192:480:288[b];\
[r]scale=640:384[r2];[a]scale=640:384[a2];[b]scale=640:384[b2];\
[r2][a2][b2]hstack=3" \
  -frames:v 1 "$D/p22-zoom2x-3arms.png"
echo "已生成 $D/p22-zoom2x-3arms.png"

# ---- 首帧两臂并排（真值 vs FlashVSR） ----
"$FF" -v error -y -i "$REF" -i "$B" \
  -filter_complex "\
[0:v]select='eq(n\,0)',scale=560:320[a];\
[1:v]select='eq(n\,0)',scale=560:320[b];\
[a][b]hstack=2" \
  -frames:v 1 "$D/p22-first-frame-truth-vs-flashvsr.png"
echo "已生成 $D/p22-first-frame-truth-vs-flashvsr.png"

# ---- 成片进交付目录 ----
for n in p22-armA-lanczos-1280x768 p22-armB-flashvsr-1280x768 p22-armB-flashvsr-r2-1280x768; do
  [ -f "$WS/out/p22/$n.mp4" ] && cp -f "$WS/out/p22/$n.mp4" "$LAB/deliverables/videos/$n.mp4" && echo "已复制 $n.mp4"
done
[ -f "$WS/out/p22/p22-ref-1280x768.mkv" ] && cp -f "$WS/out/p22/p22-ref-1280x768.mkv" "$LAB/deliverables/videos/p22-ref-1280x768.mkv" && echo "已复制 ref"
