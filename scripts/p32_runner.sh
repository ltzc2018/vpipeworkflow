#!/bin/bash
# P32 调度器 —— RelayVSR 2× 真值对照（P22 源 320×192 → 640×384）
#
# 沿用 P22/P29 runner 四条加固：setsid 脱离 / .done 幂等 / PID 续接 / 内存门限。
# ★ 用本地 build d72c22f（/tmp/vp28 软链农场）—— RelayVSR 2× 是 d72c22f 才进的。
# ★ 不要在跑的过程中编辑本脚本。
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="${VPIPE_BIN:-/tmp/vp28/Helpers/vpipe}"
TAG=p32-relayvsr-x2
OUT_REL=out/p32/p32-relayvsr-x2-640x384.mp4
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD" "$WS/out/p32"

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
  echo "  !! 内存门限等待超时，仍然开跑"
}
alive () { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

cd "$WS" || exit 1
DONE=$LOGD/$TAG.done
PIDF=$LOGD/$TAG.pid
LOG=$LOGD/$TAG.log
MEM=$LOGD/$TAG.mem
SEC=$LOGD/$TAG.seconds
PIPE=$WS/pipelines/p32-relayvsr-x2-640x384.vpipeline

# ---- 重新生成流水线（幂等：每次从官方模板重生成）
python3 "$LAB/scripts/make_p32_pipeline.py" || exit 1

if [ -f "$DONE" ] && [ -f "$WS/$OUT_REL" ]; then
  echo "[SKIP] $TAG 已完成"; exit 0
fi
if [ -f "$PIDF" ]; then
  oldpid=$(cat "$PIDF" 2>/dev/null)
  if alive "$oldpid"; then
    echo "[WAIT] $TAG 已有存活进程 pid=$oldpid，等待其完成"
    while alive "$oldpid"; do sleep 15; done
    if [ -f "$WS/$OUT_REL" ]; then touch "$DONE"; echo "[DONE] $TAG 由在跑的进程完成"; exit 0; fi
    echo "[FAIL] $TAG 在跑的进程结束但无产物"; exit 1
  fi
fi

echo "[START] $TAG  $(date '+%H:%M:%S')  产物=$OUT_REL"
wait_mem 25

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
  exit 1
fi
echo "########## P32 调度器结束 $(date '+%H:%M:%S') ##########"
