#!/bin/bash
# P3 归档：把产物、印相、报告拷进 deliverables
set -u
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$DL/videos" "$DL/images" "$DL/pipelines" "$DL/docs"

# 成片
for F in p3-768p-shift6.mp4 p3-768p-shift12.mp4 p3-544p-ref.mp4 p3-768p-4step.mp4 \
         p3-768p-shift6-241f.mp4 p3-ext-part1.mp4 p3-ext-part2.mp4 p3-ext-part3.mp4 \
         p3-ext-part4.mp4 p3-ext-full.mp4; do
  [ -f "$WS/out/$F" ] && cp "$WS/out/$F" "$DL/videos/$F" && echo "视频 -> $F"
done

# 印相
for N in shift6 shift12 544p 4step long241; do
  [ -f "$DL/images/p3-$N-contact.png" ] && echo "印相 -> p3-$N-contact.png"
done
for N in 1 2 3 4; do
  [ -f "$DL/images/p3-ext-part${N}-contact.png" ] && echo "印相 -> p3-ext-part${N}-contact.png"
done
[ -f "$DL/images/p3-ext-full-contact.png" ] && echo "印相 -> p3-ext-full-contact.png"
[ -f "$DL/images/p3-montage.png" ] && echo "印相 -> p3-montage.png"

# 流水线
cp "$WS/pipelines"/p3-768p-*.vpipeline "$DL/pipelines/" 2>/dev/null && echo "流水线 -> 768p 系列"
cp "$WS/pipelines"/p3-ext-*.vpipeline "$DL/pipelines/" 2>/dev/null && echo "流水线 -> 续接系列"

# 文档
cp "$LAB/report/vpipe-H3-部署与测试报告.md" "$LAB/report/vpipe-后续计划任务.md" "$DL/docs/"
echo "文档 -> 报告 + 计划清单"

echo "=== 交付物统计 ==="
du -sh "$DL"/* | sort -k2
