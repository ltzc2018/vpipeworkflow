#!/bin/bash
# P3.4 续接抽帧：每段抽 0/40/80/末帧 + 拼印相
# 帧名带段号前缀（p1_f000 / p2_f000 ...），供 vqa-p3-ext.sh 跨段引用
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$LAB/frames-p3-ext" "$DL/images" "$DL/videos"

frame_count () {
  $FF -v error -i "$1" -map 0:v:0 -f rawvideo -pix_fmt gray -s 16x16 - 2>/dev/null \
    | wc -c | awk '{print int($1/256)}'
}

for N in 1 2 3 4; do
  V="$WS/out/p3-ext-part$N.mp4"
  [ -f "$V" ] || { echo "跳过 part${N}（无产物）"; continue; }
  D="$LAB/frames-p3-ext"
  rm -f "$D/p${N}_"*.png
  CNT=$(frame_count "$V")
  LAST=$(( CNT - 1 ))
  for PAIR in "0:0:p${N}_f000" "1:40:p${N}_f040" "2:80:p${N}_f080" "3:$LAST:p${N}_f_last"; do
    IDXN=$(echo "$PAIR" | cut -d: -f2)
    NAME=$(echo "$PAIR" | cut -d: -f3)
    $FF -y -v error -i "$V" -vf "select=eq(n\,${IDXN}),scale=512:-1" -fps_mode passthrough \
        -frames:v 1 "$D/$NAME.png" 2>/dev/null
  done
  python3 "$LAB/scripts/p3_contact.py" "$V" "$DL/images/p3-ext-part${N}-contact.png" \
      0 40 80 last
  cp "$V" "$DL/videos/p3-ext-part${N}.mp4"
  echo "part${N} 抽帧完成 (总帧数 ${CNT})"
done

# 拼接片
for F in p3-ext-full.mp4 p3-ext-full2.mp4; do
  V="$WS/out/$F"
  [ -f "$V" ] || continue
  TAG="${F%.mp4}"
  python3 "$LAB/scripts/p3_contact.py" "$V" "$DL/images/$TAG-contact.png" 0 40 80 last
  cp "$V" "$DL/videos/$F"
  echo "$F 抽帧完成"
done
