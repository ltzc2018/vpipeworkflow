#!/bin/bash
# P1 三组串行运行（重任务串行，绝不并行）
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
for G in a b c; do
  echo "########## 组 $G ##########"
  bash "$LAB/scripts/p1_run.sh" "p1-$G-multi-ref.vpipeline" "p1-$G" 2>&1 | tail -6
  echo
done
echo "########## 全部完成 ##########"
