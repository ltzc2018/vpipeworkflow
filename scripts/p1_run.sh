#!/bin/bash
# P1 多参考组合 —— 运行一条流水线并留日志
# 用法: p1_run.sh <pipeline.vpipeline> <logname> [额外 --stage-cfg ...]
set -u
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab

PIPE="$1"; LOG="$2"; shift 2
mkdir -p "$LAB/logs"
cd "$WS" || exit 1
START=$(date +%s)
"$VPIPE" --launch "./pipelines/$PIPE" "$@" > "$LAB/logs/$LOG.log" 2>&1
RC=$?
END=$(date +%s)
echo "=== $PIPE rc=$RC  用时 $(( (END-START)/60 )) 分 $(( (END-START)%60 )) 秒 ==="
echo "$(( END-START ))" > "$LAB/logs/$LOG.seconds"
tail -25 "$LAB/logs/$LOG.log"
