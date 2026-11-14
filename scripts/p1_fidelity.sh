#!/bin/bash
# P1 保真度量化：SSIM / PSNR
# 口径 A（主口径）：视频流直接与图片比 —— ffmpeg lavfi ssim/psnr
#   SSIM 取 **All:** 聚合值（Y/U/V 合并），与历史表格（anchor-fidelity.sh）同口径
#   直接比会把 YUV 4:2:0 色度往返损失计入，比「两张都先落盘 PNG 再比」低约 0.03
#   本脚本对所有被测对象使用同一口径，组间可比。
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
TMP=$LAB/frames-p1
mkdir -p "$TMP"

prep_ref () {  # $1=src $2=w $3=h $4=dst
  $FF -y -v error -i "$1" -vf "scale=$2:$3:force_original_aspect_ratio=increase,crop=$2:$3" -pix_fmt rgb24 "$4"
}

measure () {  # $1=video $2=ref_png $3=label
  local vid="$1" ref="$2" label="$3"
  local sf="$TMP/$(basename "$vid" .mp4).ssim"
  $FF -hide_banner -i "$vid" -i "$ref" -lavfi "[0:v][1:v]ssim=stats_file=$sf" -f null - 2>/dev/null
  local pv
  pv=$($FF -hide_banner -i "$vid" -i "$ref" -lavfi "[0:v][1:v]psnr" -f null - 2>&1 | grep -o "average:[a-z0-9.]*" | head -1 | cut -d: -f2)
  local line
  line=$(awk -F'All:' '/^n:/{split($2,a," ");print a[1]}' "$sf" | \
    awk '{v[NR]=$1;s+=$1} END{printf "%.4f|%.4f|%.4f|%.4f|%d", s/NR, v[1], v[int(NR/2)], v[NR], NR}')
  echo "$line" | awk -v L="$label" -v P="$pv" -F'|' \
    '{printf "| %s | %d | %s | %s | %s | %s | %s dB |\n", L, $5, $1, $2, $3, $4, P}'
}

echo "口径 A：视频流直接比（lavfi ssim/psnr，SSIM 取 All: 聚合值，YUV 4:2:0 往返）"
echo "| 对象 | 帧数 | 全片平均 SSIM | 首帧 SSIM | 中帧 SSIM | 末帧 SSIM | 全片平均 PSNR |"
echo "|---|---|---|---|---|---|---|"

prep_ref "$WS/refs/minimax-h3-reference-subject.jpg" 832 480 "$TMP/ref-cat.png"
prep_ref "$WS/refs/klein-multi-ref-panda.jpg"        832 480 "$TMP/ref-panda.png"

for G in a b c d; do
  V="$WS/out/p1-$G-multi-ref.mp4"
  [ -f "$V" ] || continue
  measure "$V" "$TMP/ref-cat.png" "P1-$G 组 vs 主体参考图（橘猫）"
done
