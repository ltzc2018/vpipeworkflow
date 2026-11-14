#!/bin/bash
# P1 成果归档到 deliverables/
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
DL=$LAB/deliverables
mkdir -p "$DL/pipelines" "$DL/scripts" "$DL/refs" "$DL/videos" "$DL/images" "$DL/logs" "$DL/docs"

for g in a b c d; do
  [ -f "$WS/pipelines/p1-$g-multi-ref.vpipeline" ] && cp "$WS/pipelines/p1-$g-multi-ref.vpipeline" "$DL/pipelines/"
  [ -f "$WS/out/p1-$g-multi-ref.mp4" ] && cp "$WS/out/p1-$g-multi-ref.mp4" "$DL/videos/"
done
for f in motion-pan-right-124f.mp4 motion-beach-124f.mp4 klein-multi-ref-panda-crop.jpg; do
  [ -f "$WS/refs/$f" ] && cp "$WS/refs/$f" "$DL/refs/"
done
for f in "$LAB/scripts"/p1_*.py "$LAB/scripts"/p1_*.sh; do
  [ -f "$f" ] && cp "$f" "$DL/scripts/"
done
cp "$LAB/scripts/vqa-p1.sh" "$DL/scripts/" 2>/dev/null
cp "$LAB/logs/p1-motion.json" "$LAB/logs/p1-audio.json" "$DL/logs/" 2>/dev/null
for f in "$LAB/logs"/p1-*.log "$LAB/logs"/p1-*.seconds; do
  [ -f "$f" ] && cp "$f" "$DL/logs/"
done
cp "$LAB/report/p1-tables.md" "$DL/docs/" 2>/dev/null
echo "归档完成："
du -sh "$DL"
ls "$DL/videos" | grep p1
