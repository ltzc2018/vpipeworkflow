#!/bin/bash
# 等 P3 主调度器（p3_runner.sh all）跑完 5 组后，自动接续 P3.4 四段式续接调度
# 判据：5 个 .done 标记全部出现；主调度器进程退出也视为结束
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
LOGD=$LAB/logs
MARKERS="p3-shift6-124f p3-shift12-124f p3-shift6-241f p3-544p-124f p3-4step-124f"

for _ in $(seq 1 720); do
  ALLDONE=1
  for m in $MARKERS; do
    [ -f "$LOGD/$m.done" ] || ALLDONE=0
  done
  [ "$ALLDONE" = "1" ] && break
  sleep 20
done

echo "[chain] 主调度器已结束（$(date '+%H:%M:%S')），接续 P3.4 续接调度"
for m in $MARKERS; do
  [ -f "$LOGD/$m.done" ] || echo "[chain] !! 缺标记 $m"
done
bash "$LAB/scripts/p3_runner_ext.sh"
