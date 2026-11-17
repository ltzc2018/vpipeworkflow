#!/bin/bash
# P18 调度器（幂等可续跑）—— `dmd` 采样器对纹理沸腾（issue #55）的作用
#
# 沿用 P15 runner 的四条加固（后台任务被回收会 SIGHUP 杀掉重任务）：
#   1. setsid 脱离进程组（macOS 无 setsid → 用 detach_run.py，内含 os.setsid()）
#   2. 幂等续跑（.done 标记）
#   3. PID 续接
#   4. 内存门限（768p 会打满 wired pool）
#
# 默认用**本地 build**（/tmp/vp13/Helpers/vpipe -> repo/vpipe/build/libvpipe.0.1.dylib = 33cda00），
# 与 P15 B1/B2 臂同源 → 可与 p15-repro-af1.mp4 做跨轮次逐位比对。
#
# 用法: p18_runner.sh {all|euler|dmd|dmd2}
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="${VPIPE_BIN:-/tmp/vp13/Helpers/vpipe}"
echo "[runner] vpipe = $VPIPE"
"$VPIPE" --version 2>&1 | head -1
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD"

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
    echo "  等待内存：可用 ${f:-?}% < ${need}%  ($(date '+%H:%M:%S'))"
    sleep 10
  done
  echo "  !! 内存门限等待超时，仍然开跑"
}

alive () {
  [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null
}

run_one () {  # $1=pipeline  $2=log名  $3=产物文件名
  local pipe="$1" logname="$2" out="$3"
  local done="$LOGD/$logname.done"
  local pidf="$LOGD/$logname.pid"
  local log="$LOGD/$logname.log"
  local mem="$LOGD/$logname.mem"
  local sec="$LOGD/$logname.seconds"

  if [ -f "$done" ] && [ -f "$WS/out/$out" ]; then
    echo "[SKIP] $logname 已完成"; return 0
  fi

  if [ -f "$pidf" ]; then
    local oldpid; oldpid=$(cat "$pidf" 2>/dev/null)
    if alive "$oldpid"; then
      echo "[WAIT] $logname 已有存活进程 pid=$oldpid，等待其完成"
      while alive "$oldpid"; do sleep 15; done
      if [ -f "$WS/out/$out" ]; then
        touch "$done"; echo "[DONE] $logname 由在跑的进程完成"; return 0
      fi
      echo "[FAIL] $logname 在跑的进程结束但无产物"
    fi
  fi

  echo "[START] $pipe  $(date '+%H:%M:%S')  产物=out/$out"
  wait_mem 30

  : > "$mem"
  ( while true; do
      echo "ts=$(date +%s) free_pct=$(mem_free)" >> "$mem"
      sleep 5
    done ) &
  local SPID=$!

  local T0=$(date +%s)
  DETACH_PID_FILE="$pidf" python3 "$LAB/scripts/detach_run.py" \
      "$VPIPE" --launch "./pipelines/$pipe" > "$log" 2>&1
  local RC=$?
  kill $SPID 2>/dev/null
  local T1=$(date +%s)

  echo "$((T1-T0))" > "$sec"
  if [ $RC -eq 0 ] && [ -f "$WS/out/$out" ]; then
    touch "$done"
    echo "[DONE] $logname rc=0 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
  else
    echo "[FAIL] $logname rc=$RC 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
    tail -20 "$log"
  fi
  sleep 8
}

cd "$WS" || exit 1

case "${1:-all}" in
  euler) run_one p18-euler.vpipeline p18-euler p18-euler.mp4 ;;
  dmd)   run_one p18-dmd.vpipeline   p18-dmd   p18-dmd.mp4 ;;
  dmd2)  run_one p18-dmd2.vpipeline  p18-dmd2  p18-dmd2.mp4 ;;
  all)
    run_one p18-euler.vpipeline p18-euler p18-euler.mp4
    run_one p18-dmd.vpipeline   p18-dmd   p18-dmd.mp4
    run_one p18-dmd2.vpipeline  p18-dmd2  p18-dmd2.mp4
    ;;
  *) echo "用法: $0 {all|euler|dmd|dmd2}"; exit 2 ;;
esac

echo "########## P18 调度器结束 $(date '+%H:%M:%S') ##########"
