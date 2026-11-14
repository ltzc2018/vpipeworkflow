#!/bin/bash
# P3 · 768p 长规格 —— 串行跑 5 组（重任务必须串行）
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$LAB" || exit 1

run () {  # $1=pipeline  $2=logname  $3..=额外参数
  local pipe="$1" log="$2"; shift 2
  echo "########## $pipe ($(date '+%H:%M:%S')) ##########"
  bash "$LAB/scripts/p3_run.sh" "$pipe" "$log" "$@" 2>&1 | grep -E "^===|ran for|ERROR|Error" | head -6
}

# R1 768p 正确网格（shift 6.0）
run p3-768p-shift6.vpipeline  p3-shift6-124f
# R2 768p 错误网格（shift 12.0）—— 验证 shift 是不是真的必需
run p3-768p-shift12.vpipeline p3-shift12-124f
# R5 768p 10 秒单段（241 帧）—— P3 的长规格主线，放前面保证拿到
run p3-768p-shift6.vpipeline  p3-shift6-241f --stage-cfg generate-video::frames=241 --stage-cfg 'save-video::output_url="out/p3-768p-shift6-241f.mp4"'
# R3 544p 分辨率对照（960x544，544p 适配器，shift 12）
run p3-768p-544p.vpipeline    p3-544p-124f
# R4 768p 4 步 v1.2 适配器对照
run p3-768p-4step.vpipeline   p3-4step-124f

echo "########## P3 全部完成 ($(date '+%H:%M:%S')) ##########"
