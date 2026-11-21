#!/bin/bash
# P29 复跑臂（确定性验证）：与主臂同 config，输出 r2
WS=/Users/minichen/AI-Models/vpipe-workspace
BIN=/tmp/vp28/Helpers/vpipe
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p29-r2.log
cd "$WS" || exit 1
sed 's#p29-relayvsr-x2.mp4#p29-relayvsr-x2-r2.mp4#' "$WS/pipelines/p29-relayvsr-x2.vpipeline" > "$WS/pipelines/p29-relayvsr-x2-r2.vpipeline"
echo "=== P29 r2 $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
"$BIN" --launch "$WS/pipelines/p29-relayvsr-x2-r2.vpipeline" >> "$LOG" 2>&1
echo "EXIT=$? $(date '+%H:%M:%S')" >> "$LOG"
