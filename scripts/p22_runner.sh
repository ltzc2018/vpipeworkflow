#!/bin/bash
# P22 调度器 —— FlashVSR 原生 Metal 视频超分（单臂）
#
# 沿用 P13b/P18 runner 的四条加固（后台任务被回收会 SIGHUP 杀掉重任务）：
#   1. setsid 脱离进程组（macOS 无 setsid → 用 detach_run.py，内含 os.setsid()）
#   2. 幂等续跑（.done 标记）
#   3. PID 续接
#   4. 内存门限（FlashVSR 1280×768 预估 ~8.9 GB）
#
# ★ 第 3 轮坑 10.6：不要在跑的过程中编辑本脚本（bash 按文件偏移增量读取）。
# ★ 必须用**本地 build**（33cda00）—— FlashVSR 是 2026-11-09 之后才进上游的，
#   已装 App（9db5dd7, 2026-11-01）没有这个 stage。
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="${VPIPE_BIN:-/tmp/vp13/Helpers/vpipe}"
TAG=p22-flashvsr
OUT_REL=out/p22/p22-armB-flashvsr-1280x768.mp4
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD" "$WS/out/p22"

echo "[runner] vpipe = $VPIPE"
"$VPIPE" --version 2>&1 | head -1
"$VPIPE" --help 2>&1 | grep -qi flashvsr && echo "[runner] 该 build 含 flashvsr stage" \
  || echo "[runner] 提示：--help 里没有 flashvsr 字样（正常，stage 名在注册表里）"

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
PIPE=$WS/pipelines/p22-flashvsr-upscale.vpipeline

# ---- 重新生成流水线（幂等：每次跑都从官方模板重生成，杜绝手改漂移）
python3 "$LAB/scripts/make_p22_pipeline.py" || exit 1

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
echo "########## P22 调度器结束 $(date '+%H:%M:%S') ##########"
