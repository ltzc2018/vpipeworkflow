#!/bin/bash
# P1 抽帧：每组抽 0/40/80/123 帧 + 拼印相
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$LAB/frames-p1" "$DL/images" "$DL/videos"

for G in a b c d; do
  V="$WS/out/p1-$G-multi-ref.mp4"
  [ -f "$V" ] || { echo "跳过 P1-${G}（无产物）"; continue; }
  D="$LAB/frames-p1/g$G"; mkdir -p "$D"
  for N in 000 040 080 123; do
    $FF -y -v error -i "$V" -vf "select=eq(n\,$((10#$N))),scale=832:480" -fps_mode passthrough \
        -frames:v 1 "$D/f$N.png" 2>/dev/null
  done
  python3 "$LAB/scripts/p1_contact.py" "$V" "$DL/images/p1-$G-contact.png" 0 40 80 last
  cp "$V" "$DL/videos/p1-$G-multi-ref.mp4"
  echo "P1-${G} 抽帧完成"
done

# 动作参考视频的印相（作为运镜基准）
python3 "$LAB/scripts/p1_contact.py" "$WS/refs/motion-pan-right-124f.mp4" \
        "$DL/images/p1-motion-ref-contact.png" 0 40 80 last
cp "$WS/refs/motion-pan-right-124f.mp4" "$DL/videos/p1-motion-ref.mp4"

MD="$LAB/frames-p1/motion"; mkdir -p "$MD"
for N in 000 040 080 123; do
  $FF -y -v error -i "$WS/refs/motion-pan-right-124f.mp4" -vf "select=eq(n\,$((10#$N))),scale=832:480" \
      -fps_mode passthrough -frames:v 1 "$MD/f$N.png" 2>/dev/null
done
