#!/bin/bash
# P1 汇总印相：把各组关键帧叠成一张带标签的对照图
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
T=$(mktemp -d)
W=416; H=240
i=0
ROWS=()

add_row () { # $1=帧目录 $2=标签
  local D="$1" LABEL="$2"
  [ -d "$D" ] || return
  local i=0
  local files=()
  for N in 000 040 080 123; do
    local f="$D/f$N.png"
    [ -f "$f" ] || continue
    files+=(-i "$f")
    i=$((i+1))
  done
  [ $i -eq 0 ] && return
  local out="$T/row$RANDOM.png"
  $FF -y -v error "${files[@]}" -filter_complex \
    "[0:v]scale=$W:$H[a];[1:v]scale=$W:$H[b];[2:v]scale=$W:$H[c];[3:v]scale=$W:$H[d];[a][b][c][d]hstack=inputs=4[out];\
     [out]drawbox=x=0:y=0:w=520:h=34:color=black@0.75:t=fill,drawtext=fontfile='$FONT':text='$LABEL':x=10:y=7:fontsize=20:fontcolor=white" \
    -frames:v 1 "$out" 2>/dev/null
  ROWS+=("$out")
}

add_row "$LAB/frames-p1/motion" "动作参考视频（横移摇摄）"
add_row "$LAB/frames-p1/ga"   "A 组 · 仅主体图（橘猫）"
add_row "$LAB/frames-p1/gb"   "B 组 · + 风格图（水彩熊猫）"
add_row "$LAB/frames-p1/gc"   "C 组 · + 动作视频 + 音轨"
add_row "$LAB/frames-p1/gd"   "D 组 · + 第 3 张图（熊猫特写）"

if [ ${#ROWS[@]} -eq 0 ]; then echo "没有可用的帧"; exit 1; fi
INPUTS=(); FILT=""
for idx in "${!ROWS[@]}"; do
  INPUTS+=(-i "${ROWS[$idx]}")
  FILT="$FILT[$idx:v]"
  if [ $idx -lt $(( ${#ROWS[@]} - 1 )) ]; then FILT="$FILT"; fi
done
FILT=$(printf '%s' "$FILT" | sed 's/\]/]/g')
# 逐个 vstack
if [ ${#ROWS[@]} -eq 1 ]; then
  cp "${ROWS[0]}" "$DL/images/p1-montage.png"
else
  VF=""
  for idx in "${!ROWS[@]}"; do VF="$VF[$idx:v]"; done
  STACK=""; for idx in "${!ROWS[@]}"; do STACK="$STACK[$idx:v]"; done
  $FF -y -v error "${INPUTS[@]}" -filter_complex "${STACK}vstack=inputs=${#ROWS[@]}" \
    -frames:v 1 "$DL/images/p1-montage.png" 2>/dev/null
fi
rm -rf "$T"
echo "$DL/images/p1-montage.png"
