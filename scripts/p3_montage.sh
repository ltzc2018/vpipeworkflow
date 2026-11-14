#!/bin/bash
# P3 汇总印相：把各组关键帧叠成一张带标签的对照图
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
    # ffmpeg 需要 -i 与路径是**两个** argv，所以这里追加两个元素；
    # 图像数量单独用 n 记，否则 ${#files[@]} 是图数的两倍，filter 索引会错位
    files+=(-i "$f")
    n=$(( n + 1 ))
  done
  [ "$n" -eq 0 ] && return
  local out="$T/row$(date +%s%N).png"
  local F=""
  local ST=""
  for ((i=0;i<n;i++)); do F="$F[$i:v]scale=$W:$H[s$i];"; ST="$ST[s$i]"; done
  $FF -y -v error "${files[@]}" -filter_complex \
    "$F${ST}hstack=inputs=$n[row];[row]drawbox=x=0:y=0:w=560:h=34:color=black@0.78:t=fill,drawtext=fontfile='$FONT':text='$LABEL':x=10:y=7:fontsize=20:fontcolor=white" \
    -frames:v 1 "$out" 2>/dev/null
  [ -f "$out" ] && ROWS+=("$out")
}

add_row "$LAB/frames-p3/544p"    "544p 对照 · 960x544 · shift 12 · 8 步"
add_row "$LAB/frames-p3/shift6"  "768p 正确 · 1344x768 · shift 6.0 · 8 步"
add_row "$LAB/frames-p3/shift12" "768p 错误网格 · shift 12.0（应换 6.0）"
add_row "$LAB/frames-p3/4step"   "768p · 4 步 v1.2 适配器"
add_row "$LAB/frames-p3/long241" "768p 长规格 · 241 帧 / 10.04 秒"

# 四段式续接（每段一行，文件名形如 p1_f000.png）
for N in 1 2 3 4; do
  add_row "$LAB/frames-p3-ext" "续接 第 ${N} 段 · 832x480 · Ref2VA" "p${N}_f"
done

if [ ${#ROWS[@]} -eq 0 ]; then echo "没有可用的帧"; exit 1; fi
INPUTS=(); STACK=""
for idx in "${!ROWS[@]}"; do INPUTS+=(-i "${ROWS[$idx]}"); STACK="$STACK[$idx:v]"; done
$FF -y -v error "${INPUTS[@]}" -filter_complex "${STACK}vstack=inputs=${#ROWS[@]}" \
  -frames:v 1 "$DL/images/p3-montage.png" 2>&1 | head -3
rm -rf "$T" 2>/dev/null
if [ -f "$DL/images/p3-montage.png" ]; then
  echo "$DL/images/p3-montage.png  （${#ROWS[@]} 行）"
else
  echo "汇总失败"; exit 1
fi
