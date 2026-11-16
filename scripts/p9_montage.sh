#!/bin/bash
# P9 汇总印相：把各组关键帧叠成一张带标签的对照图
# 行序：第 8 轮 FL2VA 768p 基线（跨轮参照）→ P9 A → P9 B → P9 C
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
T=$(mktemp -d)
W=416; H=240
ROWS=()

add_row () { # $1=帧目录 $2=标签 [$3=文件名前缀]
  local D="$1" LABEL="$2" PRE="${3:-f}"
  [ -d "$D" ] || return
  local files=()
  local n=0
  for N in 000 040 080 _last; do
    local f="$D/${PRE}${N}.png"
    [ -f "$f" ] || continue
    # ffmpeg 需要 -i 与路径是**两个** argv；图像数量单独用 n 记，
    # 否则 ${#files[@]} 是图数的两倍，filter 索引会错位（第 8 轮坑）
    files+=(-i "$f")
    n=$(( n + 1 ))
  done
  [ "$n" -eq 0 ] && return
  local out="$T/row$(date +%s%N).png"
  local F=""
  local ST=""
  for ((i=0;i<n;i++)); do F="$F[$i:v]scale=$W:$H[s$i];"; ST="$ST[s$i]"; done
  $FF -y -v error "${files[@]}" -filter_complex \
    "$F${ST}hstack=inputs=$n[row];[row]drawbox=x=0:y=0:w=760:h=34:color=black@0.78:t=fill,drawtext=fontfile='$FONT':text='$LABEL':x=10:y=7:fontsize=20:fontcolor=white" \
    -frames:v 1 "$out" 2>/dev/null
  [ -f "$out" ] && ROWS+=("$out")
}

add_row "$LAB/frames-p3/shift6" "参照 · 第8轮 FL2VA 768p shift 6.0 · 1344x768"
add_row "$LAB/frames-p9/a" "P9-A · Ref2VA 768p · 1 图参考 · shift 6.0 · 8 步"
add_row "$LAB/frames-p9/d" "P9-D · Ref2VA 768p · 1 图参考 · shift 8.0（中间档）"
add_row "$LAB/frames-p9/b" "P9-B · Ref2VA 768p · 1 图参考 · shift 12.0（错误网格）"
add_row "$LAB/frames-p9/c" "P9-C · Ref2VA 768p · 1 图 + 动作视频 + 音轨 · shift 6.0"

if [ ${#ROWS[@]} -eq 0 ]; then echo "没有可用的帧"; exit 1; fi
INPUTS=(); STACK=""
for idx in "${!ROWS[@]}"; do INPUTS+=(-i "${ROWS[$idx]}"); STACK="$STACK[$idx:v]"; done
$FF -y -v error "${INPUTS[@]}" -filter_complex "${STACK}vstack=inputs=${#ROWS[@]}" \
  -frames:v 1 "$DL/images/p9-montage.png" 2>&1 | head -3
rm -rf "$T" 2>/dev/null
if [ -f "$DL/images/p9-montage.png" ]; then
  echo "$DL/images/p9-montage.png  （${#ROWS[@]} 行）"
else
  echo "汇总失败"; exit 1
fi
