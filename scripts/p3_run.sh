#!/bin/bash
# P3 768p —— 运行一条流水线并留日志 + 记录内存峰值
# 用法: p3_run.sh <pipeline.vpipeline> <logname> [额外 --stage-cfg ...]
set -u
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab

PIPE="$1"; LOG="$2"; shift 2
mkdir -p "$LAB/logs"
cd "$WS" || exit 1

# 内存采样器（后台）：记录 vpipe 进程 RSS + 系统可用内存百分比
SAMPLER="$LAB/logs/$LOG.mem"
(
  while true; do
    RSS=$(ps -Ao rss=,comm= 2>/dev/null | grep -i "vpipe" | awk '{s+=$1} END{print s+0}')
    FREE=$(memory_pressure 2>/dev/null | awk '/System-wide memory free percentage/{print $NF}')
    echo "ts=$(date +%s) vpipe_rss_kb=$RSS free_pct=${FREE:-0}" >> "$SAMPLER"
    sleep 5
  done
) &
SAMPLER_PID=$!

START=$(date +%s)
"$VPIPE" --launch "./pipelines/$PIPE" "$@" > "$LAB/logs/$LOG.log" 2>&1
RC=$?
END=$(date +%s)
kill $SAMPLER_PID 2>/dev/null

echo "=== $PIPE rc=$RC  用时 $(( (END-START)/60 )) 分 $(( (END-START)%60 )) 秒 ==="
echo "$(( END-START ))" > "$LAB/logs/$LOG.seconds"
tail -25 "$LAB/logs/$LOG.log"
