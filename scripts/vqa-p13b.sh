#!/bin/bash
# P13b · LFM3-VL-2B 第三方复核（er_sde σ 网格 vs 默认网格）
#
# 只问「粗粒度、可观察」的问题 —— 已知 LFM3-VL-2B 的四个缺陷：
#   ① 否定式问题会编答案；② 分不清细微锐度差；③ 运镜方向判断不可靠；
#   ④ 「是否同一场景」只能靠首帧 SSIM / 相位相关裁决，不能靠 LFM3-VL。
# 本轮问三件它能可靠回答的事：
#   Q1「场景是不是静的」→ 验证静态夹具成立
#   Q2「哪一行纹理更花」→ 纹理沸腾粗判（判定仍以量化为准）
#   Q3「两臂是否同一场景」→ 只作粗判，像素级裁决以首帧 SSIM 为准
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
      --stage-cfg "save::path=out/vqa-p13b-$tag.txt" > "$LAB/logs/vqa-p13b-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-p13b-$tag.txt" 2>/dev/null
  echo
}

# Q1：每行是一段视频的第 0/7/14/21 帧（第 1 行静态参考地板，第 2 行 A 臂，第 3 行 B 臂）
Q1="这张图是 3 行 × 4 列的抽帧图，每一行是一段视频的第 0、7、14、21 帧。第 1 行是没有任何运动的静态参考图，第 2 行和第 3 行是模型生成的视频。请用中文回答：第 2 行和第 3 行各自这一行内部，画面里的主体和背景有没有发生位置移动或姿态变化？把每一行分别描述一下。"
ask "static" "$Q1" "$LAB/deliverables/images/p13b-contact-sheet.png"

# Q2：纹理粗判 —— 哪一行的高频噪点更明显（量化以 HF jitter 为准，这里只作粗判）
Q2="这张图是 3 行 × 4 列的抽帧图，同一行内是同一段视频的第 0、7、14、21 帧。请用中文回答：只比较第 2 行和第 3 行，哪一行在平坦区域（比如背景墙面、桌面）上看起来噪点更细碎、更像'沙沙的颗粒感'？请分别描述两行的表面质感。"
ask "texture" "$Q2" "$LAB/deliverables/images/p13b-contact-sheet.png"

# Q3：两臂首帧 —— 是否同一场景（★ 只能粗判，像素级裁决以首帧 SSIM 为准）
Q3="这张图是两次不同生成结果的第一帧并排（左边一张、右边一张）。请用中文回答：这两张图的场景是否完全相同？分别描述每张图里的主体姿态、背景内容和主体在画面中的位置。"
ask "firstframe" "$Q3" "$LAB/deliverables/images/p13b-first-frame-2arms.png"

# Q4：首帧 vs 末帧 —— 纹理是否随时间累积（两臂各看首末）
Q4="这张图是 4 格：左上、右上是第一段视频的首帧和末帧，左下、右下是第二段视频的首帧和末帧。请用中文回答：每一段从首帧到末帧，画面表面的纹理（噪点/颗粒感）有没有变多、变花？请分别描述两段的变化。"
ask "firstlast" "$Q4" "$LAB/deliverables/images/p13b-first-last-2arms.png"
