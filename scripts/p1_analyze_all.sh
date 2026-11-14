#!/bin/bash
# P1 全量分析（纯 CPU，不加载模型，可与生成任务并行）
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
cd "$LAB" || exit 1

echo "########## 1. 抽帧 + 印相 ##########"
bash scripts/p1_frames.sh

echo
echo "########## 2. 运动学（相位相关）##########"
VIDS=""
for g in a b c d; do [ -f "$WS/out/p1-$g-multi-ref.mp4" ] && VIDS="$VIDS $WS/out/p1-$g-multi-ref.mp4"; done
python3 scripts/p1_motion.py $VIDS "$WS/refs/motion-pan-right-124f.mp4" --json logs/p1-motion.json

echo
echo "########## 3. 音频通道 ##########"
AUD="$WS/refs/motion-pan-right-124f.mp4"
for g in a b c d; do [ -f "$WS/out/p1-$g-multi-ref.mp4" ] && AUD="$AUD $WS/out/p1-$g-multi-ref.mp4"; done
python3 scripts/p1_audio.py $AUD --json logs/p1-audio.json

echo
echo "########## 4. 保真度（SSIM/PSNR）##########"
bash scripts/p1_fidelity.sh

echo
echo "########## 5. 组间两两对比 ##########"
bash scripts/p1_pairwise.sh

echo
echo "########## 6. 汇总印相 ##########"
bash scripts/p1_montage.sh

echo
echo "########## 7. 报告表格 ##########"
python3 scripts/p1_report_tables.py --md report/p1-tables.md
