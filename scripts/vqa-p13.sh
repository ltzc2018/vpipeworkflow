#!/bin/bash
# P13 · LFM3-VL-2B 第三方复核（静态场景纹理沸腾实验）
#
# 只问「粗粒度、可观察」的问题 —— 已知 LFM3-VL-2B 的三个缺陷：
#   ① 否定式问题会编答案；② 分不清细微锐度差；③ 运镜方向判断不可靠。
# 所以本脚本只问两件它能可靠回答的事：
#   Q1「场景是不是静的」→ 验证静态场景假设成立（否则 HF jitter 会被运动污染）
#   Q2「三次生成是不是同一个场景」→ 验证「换 shift = 换场景」这个混淆项
set -u

VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope

ask () { # $1=tag  $2=question  $3...=images
  local tag="$1"; shift
  local q="$1"; shift
  local line="$q"
  for f in "$@"; do
    line="$line<|__vpipe_fs_im_start__|>$f<|__vpipe_fs_im_end__|>"
  done
  echo "$line" | "$VP" --launch ./pipelines/lfm3-vl-vqa.vpipeline \
      --stage-cfg "save::path=out/vqa-$tag.txt" > "$LAB/logs/vqa-p13-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-$tag.txt" 2>/dev/null
  echo
}

# Q1：每行是一段视频的第 0/7/14/21 帧（第 1 行是静态参考地板，其余是模型生成）
Q1="这张图是 4 行 × 4 列的抽帧图，每一行是一段视频的第 0、7、14、21 帧。第 1 行是没有任何运动的静态参考图，第 2、3、4 行是模型生成的视频。请用中文回答：第 2、3、4 行各自这一行内部，画面里的主体（猫）和背景有没有发生位置移动或姿态变化？把每一行分别描述一下。"
ask "p13-static" "$Q1" "$LAB/deliverables/images/p13-contact-sheet.png"

# Q2：三臂首帧并排 —— 是否同一个场景
Q2="这张图是三次不同生成结果的第 0 帧并排（从左到右）。请用中文回答：这三张图的场景是否完全相同？分别描述每张图里的主体姿态、背景内容和构图位置。"
ask "p13-firstframe" "$Q2" "$LAB/deliverables/images/p13-first-frame-3arms.png"

# Q3：三臂各抽首帧 —— 静态性交叉验证
Q3="这几张图是三段视频各自的第一帧。请用中文回答：每张图里的猫的姿态、窗户和背景的细节是否几乎完全一样？如果有明显不同，请指出不同在哪里。"
ask "p13-arms" "$Q3" \
  "$LAB/deliverables/images/p13-first-frame-3arms.png"
