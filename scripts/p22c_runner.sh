#!/bin/bash
# P22c 调度器 —— FlashVSR+ Turbo 原生 Metal 视频超分 (1920x1152)
#
# 沿用 P13b/P18/P22 runner 的四条加固。
# ★ 必须用本地 build (33cda00)。
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="${VPIPE_BIN:-/tmp/vp13/Helpers/vpipe}"
TAG=p22c-plus-1920
OUT_REL=out/p22/p22c-armC-plus-1920x1152.mp4
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD" "$WS/out/p22"

echo "[runner] vpipe = $VPIPE"
"$VPIPE" --version 2>&1 | head -1

mem_free () {
  memory_pressure 2>/dev/null \
    | awk '/System-wide memory free percentage/{gsub("%","",$NF); print $NF}' | head -1
}
wait_mem () {
  local need="$1" f
  for _ in $(seq 1 90); do
    f=$(mem_free)
    if [ -n "$f" ] && [ "$f" -ge "$need" ] 2>/dev/null; then
      [ "$f" -lt 100 ] && echo "  内存就绪：可用 ${f}%"
      return 0
    fi
    echo "  等待内存：可用 ${f:-?}% < ${need}% ($(date '+%H:%M:%S'))"
    sleep 10
  done
}
alive () { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

cd "$WS" || exit 1
DONE=$LOGD/$TAG.done
PIDF=$LOGD/$TAG.pid
LOG=$LOGD/$TAG.log
MEM=$LOGD/$TAG.mem
SEC=$LOGD/$TAG.seconds
PIPE=$WS/pipelines/p22c-plus-upscale-1920.vpipeline

# ---- 重新生成流水线
python3 "$LAB/scripts/make_p22c_pipeline.py" || exit 1

if [ -f "$DONE" ] && [ -f "$WS/$OUT_REL" ]; then
  echo "[SKIP] $TAG 已完成"; exit 0
fi

echo "[START] $TAG  $(date '+%H:%M:%S')  产物=$OUT_REL"
wait_mem 20

: > "$MEM"
( while true; do echo "ts=$(date +%s) free_pct=$(mem_free)" >> "$MEM"; sleep 5; done ) &
SPID=$!

T0=$(date +%s)
DETACH_PID_FILE="$PIDF" python3 "$LAB/scripts/detach_run.py" \
    "$VPIPE" --launch "$PIPE" > "$LOG" 2>&1
RC=$?
kill $SPID 2>/dev/null
T1=$(date +%s)
echo "$((T1-T0))" > "$SEC"

if [ $RC -eq 0 ] && [ -f "$WS/$OUT_REL" ]; then
  touch "$DONE"
  echo "[DONE] $TAG rc=0 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
else
  echo "[FAIL] $TAG rc=$RC 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
  echo "---- 日志尾部 ----"; tail -40 "$LOG"
fi
