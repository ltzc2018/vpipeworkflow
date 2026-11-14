#!/bin/bash
# P3 稳健调度器（幂等可续跑）
#
# 解决的问题：上一轮后台任务在会话压缩时被回收，SIGHUP 带走正在跑的重任务，
# 30 分钟的 denoise 全部作废（shift12 只跑到 0%）。
#
# 四条加固：
#   1. setsid 脱离进程组 —— 调度脚本被杀，正在跑的那一支仍能跑完
#   2. 幂等续跑 —— 每组有 .done 标记，已完成的直接跳过
#   3. PID 续接 —— 重启调度器时发现该组还有活着的 PID，就等它而不是重跑
#   4. 内存门限 —— 每组开跑前等可用内存回升到阈值以上（768p 会打满 wired pool）
set -u

LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD"

mem_free () {
  memory_pressure 2>/dev/null \
    | awk '/System-wide memory free percentage/{gsub("%","",$NF); print $NF}' | head -1
}

wait_mem () {   # $1 = 最低可用内存百分比
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

alive () {  # $1 = pid
  [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null
}

run_one () {  # $1=pipeline  $2=log名  $3=产物文件名  $4..=额外 --stage-cfg
  local pipe="$1" logname="$2" out="$3"; shift 3
  local done="$LOGD/$logname.done"
  local pidf="$LOGD/$logname.pid"
  local log="$LOGD/$logname.log"
  local mem="$LOGD/$logname.mem"
  local sec="$LOGD/$logname.seconds"

  if [ -f "$done" ] && [ -f "$WS/out/$out" ]; then
    echo "[SKIP] $logname 已完成"; return 0
  fi

  # 续接：上一轮调度器被杀但生成仍在跑 → 等它，不重跑
  if [ -f "$pidf" ]; then
    local oldpid; oldpid=$(cat "$pidf" 2>/dev/null)
    if alive "$oldpid"; then
      echo "[WAIT] $logname 已有存活进程 pid=$oldpid，等待其完成"
      while alive "$oldpid"; do sleep 15; done
      if [ -f "$WS/out/$out" ]; then
        touch "$done"
        echo "[DONE] $logname 由在跑的进程完成"; return 0
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
      "$VPIPE" --launch "./pipelines/$pipe" "$@" > "$log" 2>&1
  local RC=$?
  kill $SPID 2>/dev/null
  local T1=$(date +%s)

  echo "$((T1-T0))" > "$sec"
  if [ $RC -eq 0 ] && [ -f "$WS/out/$out" ]; then
    touch "$done"
    echo "[DONE] $logname rc=0 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
  else
    echo "[FAIL] $logname rc=$RC 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
    tail -5 "$log"
  fi
  sleep 15   # 让上一组的内存回收干净
}

cd "$WS" || exit 1

case "${1:-all}" in
  shift6)
    run_one p3-768p-shift6.vpipeline p3-shift6-124f p3-768p-shift6.mp4 ;;
  shift12)
    run_one p3-768p-shift12.vpipeline p3-shift12-124f p3-768p-shift12.mp4 ;;
  long241)
    run_one p3-768p-shift6.vpipeline p3-shift6-241f p3-768p-shift6-241f.mp4 \
      --stage-cfg generate-video::frames=241 \
      --stage-cfg 'save-video::output_url="out/p3-768p-shift6-241f.mp4"' ;;
  544p)
    run_one p3-768p-544p.vpipeline p3-544p-124f p3-544p-ref.mp4 ;;
  4step)
    run_one p3-768p-4step.vpipeline p3-4step-124f p3-768p-4step.mp4 ;;
  all)
    run_one p3-768p-shift6.vpipeline  p3-shift6-124f p3-768p-shift6.mp4
    run_one p3-768p-shift12.vpipeline p3-shift12-124f p3-768p-shift12.mp4
    run_one p3-768p-shift6.vpipeline  p3-shift6-241f p3-768p-shift6-241f.mp4 \
      --stage-cfg generate-video::frames=241 \
      --stage-cfg 'save-video::output_url="out/p3-768p-shift6-241f.mp4"'
    run_one p3-768p-544p.vpipeline    p3-544p-124f p3-544p-ref.mp4
    run_one p3-768p-4step.vpipeline   p3-4step-124f p3-768p-4step.mp4
    ;;
  *)
    echo "用法: $0 {all|shift6|shift12|long241|544p|4step}"; exit 2 ;;
esac

echo "########## 调度器结束 $(date '+%H:%M:%S') ##########"
