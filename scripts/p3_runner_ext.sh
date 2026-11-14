#!/bin/bash
# P3.4 四段式续接调度器（必须在 p3_runner.sh 之后串行执行）
#
# 链路：part1(FL2VA t2v) → part2 → part3 → part4 → concat
# 每段都是「上一段的末 90 帧 + 末 3.75 秒音轨」作为参考续接。
# 沿用 p3_runner.sh 的四条加固：setsid 脱离进程组 / 幂等续跑 / PID 续接 / 内存门限。
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

alive () { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

disk_avail_gb () { df -g "$WS" | awk 'NR==2{print $4}'; }

wait_disk () {  # $1 = 最低剩余 GiB
  local need="$1" g
  for _ in $(seq 1 30); do
    g=$(disk_avail_gb)
    if [ -n "$g" ] && [ "$g" -ge "$need" ] 2>/dev/null; then
      echo "  磁盘就绪：剩余 ${g} GiB"; return 0
    fi
    echo "  磁盘不足：剩余 ${g:-?} GiB < ${need} GiB"
    sleep 20
  done
  echo "  !! 磁盘低于门限，仍然开跑"
}

run_one () {  # $1=pipeline  $2=日志名  $3=产物文件名
  local pipe="$1" logname="$2" out="$3"
  local done="$LOGD/$logname.done" pidf="$LOGD/$logname.pid"
  local log="$LOGD/$logname.log" mem="$LOGD/$logname.mem"

  if [ -f "$done" ] && [ -f "$WS/out/$out" ]; then echo "[SKIP] $logname"; return 0; fi
  if [ -f "$pidf" ]; then
    local oldpid; oldpid=$(cat "$pidf" 2>/dev/null)
    if alive "$oldpid"; then
      echo "[WAIT] $logname 已有存活进程 pid=$oldpid"
      while alive "$oldpid"; do sleep 15; done
      if [ -f "$WS/out/$out" ]; then touch "$done"; echo "[DONE] $logname（续接完成）"; return 0; fi
      echo "[FAIL] $logname 在跑的进程结束但无产物"; return 1
    fi
  fi

  echo "[START] $pipe  $(date '+%H:%M:%S')  产物=out/$out"
  wait_disk 15
  wait_mem 30
  : > "$mem"
  ( while true; do echo "ts=$(date +%s) free_pct=$(mem_free)" >> "$mem"; sleep 5; done ) &
  local SPID=$!
  local T0=$(date +%s)
  DETACH_PID_FILE="$pidf" python3 "$LAB/scripts/detach_run.py" \
      "$VPIPE" --launch "./pipelines/$pipe" > "$log" 2>&1
  local RC=$?
  kill $SPID 2>/dev/null
  local T1=$(date +%s)
  echo "$((T1-T0))" > "$LOGD/$logname.seconds"
  if [ $RC -eq 0 ] && [ -f "$WS/out/$out" ]; then
    touch "$done"
    echo "[DONE] $logname rc=0 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
  else
    echo "[FAIL] $logname rc=$RC 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
    tail -8 "$log"
  fi
  sleep 10
}

cd "$WS" || exit 1

run_one p3-ext-part1.vpipeline p3-ext-part1 p3-ext-part1.mp4 || exit 1
run_one p3-ext-part2.vpipeline p3-ext-part2 p3-ext-part2.mp4 || exit 1
# 先落袋一个两段拼接（证明续接机制可行），再继续 3/4 段
run_one p3-ext-concat2.vpipeline p3-ext-concat2 p3-ext-full2.mp4
run_one p3-ext-part3.vpipeline p3-ext-part3 p3-ext-part3.mp4 || exit 1
run_one p3-ext-part4.vpipeline p3-ext-part4 p3-ext-part4.mp4 || exit 1
run_one p3-ext-concat.vpipeline p3-ext-concat p3-ext-full.mp4

echo "########## P3.4 续接调度器结束 $(date '+%H:%M:%S') ##########"
