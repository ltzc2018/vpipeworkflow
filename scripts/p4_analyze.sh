#!/bin/bash
# P4 分析：预览流逐步印相 + 预览/成片/锚定图三方 SSIM/PSNR
#
# 用法： p4_analyze.sh <tag> <preview-stream.mp4> <final.mp4> <anchor.jpg>
#   <beat_frames> = 预览流里每个 beat（=每步一帧 clip）的帧数，默认 39
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab

TAG="$1"; STREAM="$2"; FINAL="$3"; ANCHOR="$4"; BEAT="${5:-39}"
OUT="$LAB/deliverables/p4-preview/$TAG"
WORK="$LAB/frames-p4/$TAG"
rm -rf "$WORK"; mkdir -p "$WORK" "$OUT"

echo "=== [$TAG] 预览流基本信息 ==="
$FF -hide_banner -i "$STREAM" 2>&1 | grep -E "Duration|Stream #" | head -5

# 预览流的帧总数 → 用它算 beat 数（本机没有 ffprobe，用 ffmpeg 空转数帧）
TOTAL=$($FF -hide_banner -i "$STREAM" -map 0:v:0 -f null - 2>&1 \
        | grep -oE "frame= *[0-9]+" | tail -1 | grep -oE "[0-9]+")
TOTAL="${TOTAL:-0}"
echo "总帧数=$TOTAL  每 beat=$BEAT 帧 → 推算 beat 数=$(( (TOTAL + BEAT - 1) / BEAT ))"

# ---- 1) 逐步印相：每个 beat 的最后一帧（该步的干净估计）----
LASTS=""
FIRSTS=""
i=0
f=0
while [ $f -lt $TOTAL ]; do
  last=$(( f + BEAT - 1 ))
  [ $last -ge $TOTAL ] && last=$(( TOTAL - 1 ))
  $FF -y -i "$STREAM" -vf "select=eq(n\,$last)" -vframes 1 \
      "$WORK/beat${i}_last.png" >/dev/null 2>&1
  $FF -y -i "$STREAM" -vf "select=eq(n\,$f)" -vframes 1 \
      "$WORK/beat${i}_first.png" >/dev/null 2>&1
  FIRSTS="$FIRSTS $WORK/beat${i}_first.png"
  LASTS="$LASTS $WORK/beat${i}_last.png"
  echo "  beat $i: 帧 $f..$last"
  f=$(( f + BEAT ))
  i=$(( i + 1 ))
done

# 拼印相（带 step 标签）
mk_sheet () {
  local list="$1" out="$2" label="$3"
  [ -z "$list" ] && return
  local inputs=""
  for p in $list; do
    [ -f "$p" ] || continue
    local n=$(basename "$p" .png | sed 's/[^0-9]//g')
    inputs="$inputs -i $p"
  done
  [ -z "$inputs" ] && return
  local n=$(echo $inputs | wc -w | tr -d ' ')
  local filt=""
  local k=0
  for p in $list; do
    [ -f "$p" ] || continue
    local nn=$(basename "$p" .png | sed 's/[^0-9]//g')
    filt="$filt[$k:v]scale=384:216,drawtext=text='$label $nn':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6[vt$k];"
    k=$(( k + 1 ))
  done
  local stack=""
  for i in $(seq 0 $(( k - 1 ))); do stack="$stack[vt$i]"; done
  $FF -y $inputs -filter_complex "${filt}${stack}hstack=inputs=$k[v]" \
      -map "[v]" -frames:v 1 "$out" >/dev/null 2>&1
  echo "  印相 -> $out ($k 格)"
}
mk_sheet "$LASTS" "$OUT/contact-sheet-beat-last.png" "step"
mk_sheet "$FIRSTS" "$OUT/contact-sheet-beat-first.png" "step"

# ---- 2) SSIM / PSNR 三方对照 ----
echo
echo "=== [$TAG] SSIM / PSNR ==="
echo "| 对照 | 帧数 | SSIM 均值 | SSIM 首 | SSIM 末 | PSNR 均值(dB) | PSNR 首 | PSNR 末 |"
echo "|---|---|---|---|---|---|---|---|"

# 锚定图裁成预览分辨率
$FF -y -i "$ANCHOR" -vf "scale=512:288:force_original_aspect_ratio=increase,crop=512:288" \
    "$WORK/anchor-512.png" >/dev/null 2>&1

measure () { # $1=video  $2=ref  $3=label
  local vid="$1" ref="$2" label="$3"
  local tag=$(basename "$vid" | tr '.' '_')
  local ss="$WORK/$tag.ssim" ps="$WORK/$tag.psnr"
  $FF -i "$vid" -i "$ref" -lavfi "[0:v][1:v]ssim=stats_file=$ss" -f null - >/dev/null 2>&1
  $FF -i "$vid" -i "$ref" -lavfi "[0:v][1:v]psnr=stats_file=$ps" -f null - >/dev/null 2>&1
  if [ ! -s "$ss" ]; then echo "| $label | 尺寸不匹配，跳过 | | | | | | |"; return; fi
  # ssim stats: "n:1 Y:.. U:.. V:.. All:0.99 (..)"   psnr stats: "n:1 mse_avg:.. psnr_avg:45.3 .."
  local n=$(wc -l < "$ss" | tr -d ' ')
  local s_mean=$(awk -F'All:' '/All:/{split($2,a," ");s+=a[1];k++} END{if(k)printf "%.4f", s/k}' "$ss")
  local s_first=$(awk -F'All:' '/All:/{split($2,a," ");print a[1]; exit}' "$ss")
  local s_last=$(awk -F'All:' '/All:/{split($2,a," ");v=a[1]} END{print v}' "$ss")
  local p_mean=$(awk 'BEGIN{FS="psnr_avg:"} /psnr_avg:/{split($2,a," ");s+=a[1];k++} END{if(k)printf "%.2f", s/k}' "$ps")
  local p_first=$(awk 'BEGIN{FS="psnr_avg:"} /psnr_avg:/{split($2,a," ");print a[1]; exit}' "$ps")
  local p_last=$(awk 'BEGIN{FS="psnr_avg:"} /psnr_avg:/{split($2,a," ");v=a[1]} END{print v}' "$ps")
  echo "| $label | $n | $s_mean | $s_first | $s_last | $p_mean | $p_first | $p_last |"
}

# a) 成片 vs 锚定图（首帧锚定是否成立）
measure "$FINAL" "$WORK/anchor-512.png" "成片 vs 锚定图（512x288）"
# b) 预览流 vs 成片（预览与正片是否一致）
measure "$STREAM" "$FINAL" "预览流 vs 成片"
# c) i2va 特有：预览的首帧是否就是锚定图
$FF -y -i "$STREAM" -vf "select=eq(n\,0)" -vframes 1 "$WORK/preview-first.png" >/dev/null 2>&1
measure "$WORK/preview-first.png" "$WORK/anchor-512.png" "预览首帧 vs 锚定图"
# d) 预览末帧 vs 成片末帧（最后一版干净估计与正片的差距）
$FF -y -i "$STREAM" -vf "select=eq(n\,$((TOTAL-1)))" -vframes 1 "$WORK/preview-last.png" >/dev/null 2>&1
$FF -y -i "$FINAL" -vf "select=eq(n\,$((TOTAL-1)))" -vframes 1 "$WORK/final-last.png" >/dev/null 2>&1
measure "$WORK/preview-last.png" "$WORK/final-last.png" "预览末帧 vs 成片末帧"

echo
echo "=== [$TAG] 产物 ==="
ls -la "$OUT"
