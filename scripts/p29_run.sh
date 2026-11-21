#!/bin/bash
# P29 RelayVSR 2× 主臂
WS=/Users/minichen/AI-Models/vpipe-workspace
BIN=/tmp/vp28/Helpers/vpipe
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p29-main.log
cd "$WS" || exit 1
echo "=== P29 main $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
"$BIN" --launch "$WS/pipelines/p29-relayvsr-x2.vpipeline" >> "$LOG" 2>&1
echo "EXIT=$? $(date '+%H:%M:%S')" >> "$LOG"
