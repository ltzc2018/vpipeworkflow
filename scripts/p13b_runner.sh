#!/bin/bash
# P13b 调度器（幂等可续跑）—— `sigmas`（ComfyUI er_sde σ 表）网格对照
#
# 沿用 P18 runner 的四条加固（后台任务被回收会 SIGHUP 杀掉重任务）：
#   1. setsid 脱离进程组（macOS 无 setsid → 用 detach_run.py，内含 os.setsid()）
#   2. 幂等续跑（.done 标记）
#   3. PID 续接
#   4. 内存门限（768p 会打满 wired pool）
#
# ★ 第 3 轮坑 10.6：**不要在跑的过程中编辑本脚本**（bash 按文件偏移增量读取）。
#   要改先停掉实例。
#
# 默认用**本地 build**（/tmp/vp13/Helpers/vpipe -> repo/vpipe/build/libvpipe.0.1.dylib = 33cda00），
# 与第 4 轮 p18-euler.mp4 同源 → B1 臂应与 p18-euler.mp4 **逐位相同**（跨轮次锚点）。
#
# 用法: p13b_runner.sh {all|ersde|default}
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

# 每次跑之前生成一个只改 output_url 的流水线副本 → 产物名唯一
make_pipe () {  # $1=基臂  $2=运行序号
  local arm="$1" n="$2"
  local src="$WS/pipelines/p13b-${arm}.vpipeline"
  local dst="$WS/pipelines/p13b-${arm}-r${n}.vpipeline"
  python3 - "$src" "$dst" "out/p13b-${arm}-r${n}.mp4" <<'PY'
import json, sys
src, dst, out = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src, encoding="utf-8") as f:
    pipe = json.load(f)
for st in pipe["stages"]:
    if st["type"] == "save-video":
        st["config"]["output_url"] = out
    if st["type"] == "minimax-h3-model-config":
        assert st["config"].get("video_shift") == 6.0
with open(dst, "w", encoding="utf-8") as f:
    json.dump(pipe, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY
  echo "$dst"
}

run_one () {  # $1=基臂  $2=运行序号
  local arm="$1" n="$2"
  local tag="p13b-${arm}-r${n}"
  local out="p13b-${arm}-r${n}.mp4"
  local pipe; pipe=$(make_pipe "$arm" "$n")
  local done="$LOGD/$tag.done"
  local pidf="$LOGD/$tag.pid"
  local log="$LOGD/$tag.log"
  local mem="$LOGD/$tag.mem"
  local sec="$LOGD/$tag.seconds"

  if [ -f "$done" ] && [ -f "$WS/out/$out" ]; then
    echo "[SKIP] $tag 已完成"; return 0
  fi

  if [ -f "$pidf" ]; then
    local oldpid; oldpid=$(cat "$pidf" 2>/dev/null)
    if alive "$oldpid"; then
      echo "[WAIT] $tag 已有存活进程 pid=$oldpid，等待其完成"
      while alive "$oldpid"; do sleep 15; done
      if [ -f "$WS/out/$out" ]; then
        touch "$done"; echo "[DONE] $tag 由在跑的进程完成"; return 0
      fi
      echo "[FAIL] $tag 在跑的进程结束但无产物"
    fi
  fi

  echo "[START] $tag  $(date '+%H:%M:%S')  产物=out/$out"
  wait_mem 30

  : > "$mem"
  ( while true; do
      echo "ts=$(date +%s) free_pct=$(mem_free)" >> "$mem"
      sleep 5
    done ) &
  local SPID=$!

  local T0=$(date +%s)
  DETACH_PID_FILE="$pidf" python3 "$LAB/scripts/detach_run.py" \
      "$VPIPE" --launch "$pipe" > "$log" 2>&1
  local RC=$?
  kill $SPID 2>/dev/null
  local T1=$(date +%s)

  echo "$((T1-T0))" > "$sec"
  if [ $RC -eq 0 ] && [ -f "$WS/out/$out" ]; then
    touch "$done"
    echo "[DONE] $tag rc=0 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
  else
    echo "[FAIL] $tag rc=$RC 用时 $(( (T1-T0)/60 )) 分 $(( (T1-T0)%60 )) 秒"
    tail -20 "$log"
  fi
  sleep 8
}

cd "$WS" || exit 1

case "${1:-all}" in
  ersde)
    run_one ersde 1; run_one ersde 2; run_one ersde 3
    ;;
  default)
    run_one default 1; run_one default 2
    ;;
  all)
    # 串行（实测并行会互相杀死进程）
    run_one ersde 1; run_one ersde 2; run_one ersde 3
    run_one default 1; run_one default 2
    ;;
  *) echo "用法: $0 {all|ersde|default}"; exit 2 ;;
esac

echo "########## P13b 调度器结束 $(date '+%H:%M:%S') ##########"
