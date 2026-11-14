#!/bin/bash
# 量化「锚定路线 vs 参考生视频路线」的首帧保真度与随时间的衰减
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
TMP=$LAB/frames-fid
mkdir -p "$TMP"

# $1=src $2=width $3=height $4=dst
prep_ref () {
  $FF -y -i "$1" -vf "scale=$2:$3:force_original_aspect_ratio=increase,crop=$2:$3" "$4" >/dev/null 2>&1
}

# $1=video $2=ref $3=label $4=描述
measure () {
  local vid="$1" ref="$2" label="$3"
  local ssim_file="$TMP/$(basename "$vid" .mp4).ssim"
  $FF -i "$vid" -i "$ref" -lavfi "[0:v][1:v]ssim=stats_file=$ssim_file" -f null - >/dev/null 2>&1
  local vals
  vals=$(awk -F'All:' '/All:/{split($2,a," ");print a[1]}' "$ssim_file")
  [ -z "$vals" ] && { echo "| $label | (尺寸不匹配,跳过) | | |"; return; }
  echo "$vals" | awk -v L="$label" '
    {v[NR]=$1; s+=$1}
    END{
      printf "| %s | %d 帧 | %.4f | %.4f | %.4f | %.4f |\n", L, NR, s/NR, v[1], v[int(NR/2)], v[NR]
    }'
}

echo "| 视频 | 帧数 | 全片平均 SSIM | 首帧 | 中帧 | 末帧 |"
echo "|---|---|---|---|---|---|"

# 832x480 组
prep_ref "$WS/refs/minimax-h3-reference-subject.jpg" 832 480 "$TMP/ref-cat-832.png"
prep_ref "$WS/refs/klein-multi-ref-panda.jpg"        832 480 "$TMP/ref-panda-832.png"
measure "$WS/out/pika-i2va-shop.mp4"        "$TMP/ref-cat-832.png"   "**i2va 首帧锚定**（猫+牛仔外套）"
measure "$WS/out/pika-ref2va-panda.mp4"     "$TMP/ref-panda-832.png" "Pika Ref2VA 参考生视频（熊猫参考）"
measure "$WS/out/pika-ref2va-ablation.mp4"  "$TMP/ref-cat-832.png"   "Pika Ref2VA 参考生视频（猫参考）"
measure "$WS/out/pika-ref2va-noref.mp4"     "$TMP/ref-cat-832.png"   "Pika Ref2VA 无参考对照（猫参考）"

# 960x544 组
prep_ref "$WS/refs/minimax-h3-reference-subject.jpg" 960 544 "$TMP/ref-cat-960.png"
measure "$WS/out/h3-first-last.mp4"                 "$TMP/ref-cat-960.png" "**FL2VA 首尾帧锚定**（猫+牛仔外套）"
measure "$WS/out/fl2va-ref2va-like-ablation.mp4"    "$TMP/ref-cat-960.png" "FL2VA + VDN 仿 Ref2VA（猫参考）"
