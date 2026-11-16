#!/bin/bash
# P9 归档：把产物、印相、流水线、日志拷进 deliverables
set -u
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$DL/videos" "$DL/images" "$DL/pipelines" "$DL/logs" "$DL/scripts" "$DL/docs"

# 成片
for F in p9-ref2va-768p-a.mp4 p9-ref2va-768p-b-shift12.mp4 p9-ref2va-768p-c-multiref.mp4 \
         p9-ref2va-768p-d-shift8.mp4; do
  [ -f "$WS/out/$F" ] && cp "$WS/out/$F" "$DL/videos/$F" && echo "视频 -> $F"
done

# 印相
for N in a b c d; do
  [ -f "$DL/images/p9-$N-contact.png" ] && echo "印相 -> p9-$N-contact.png"
done
[ -f "$DL/images/p9-montage.png" ] && echo "印相 -> p9-montage.png"
[ -f "$DL/images/p9-crop-compare.png" ] && echo "印相 -> p9-crop-compare.png"

# 流水线
cp "$WS/pipelines"/p9-ref2va-768p-*.vpipeline "$DL/pipelines/" 2>/dev/null && echo "流水线 -> p9-ref2va-768p-*"

# 日志 / 度量
for F in p9-a-768p.log p9-b-768p-shift12.log p9-c-768p-multiref.log p9-d-768p-shift8.log \
         p9-a-768p.seconds p9-b-768p-shift12.seconds p9-c-768p-multiref.seconds p9-d-768p-shift8.seconds \
         p9-analysis.json p9-motion.json p9-audio.json p9-sharpness.json p9-sharpness-crop.json \
         p9-tables.md; do
  [ -f "$LAB/logs/$F" ] && cp "$LAB/logs/$F" "$DL/logs/$F"
done
for F in "$LAB/logs"/vqa-p9-*.log; do
  [ -f "$F" ] && cp "$F" "$DL/logs/"
done
echo "日志 -> P9 全组 + 量化 + VQA"

# 脚本
for F in "$LAB/scripts"/p9_*.py "$LAB/scripts"/p9_*.sh "$LAB/scripts"/make_p9_pipelines.py "$LAB/scripts"/vqa-p9.sh; do
  [ -f "$F" ] && cp "$F" "$DL/scripts/"
done
echo "脚本 -> P9 全套"

# 文档
cp "$LAB/report/vpipe-H3-部署与测试报告.md" "$LAB/report/vpipe-后续计划任务.md" "$DL/docs/"
echo "文档 -> 报告 + 计划清单"

echo "=== 交付物统计 ==="
du -sh "$DL"/* | sort -k2
