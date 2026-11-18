#!/bin/bash
# P22 · LFM3-VL-2B 第三方复核（FlashVSR 4× 超分 vs lanczos 插值 vs 真值）
#
# 只问「粗粒度、可观察」的问题 —— 已知 LFM3-VL-2B 的四个缺陷：
#   ① 否定式问题会编答案；② 分不清细微锐度差；③ 运镜方向判断不可靠；
#   ④ 「是否同一场景」只能靠首帧 SSIM / 相位相关裁决，不能靠 LFM3-VL。
# 本轮问四件它能相对可靠回答的事：
#   Q1 三行是不是同一个场景（只作粗判，像素级裁决以 SSIM 为准）
#   Q2 哪一行的表面纹理更细碎/更锐（粗判，判定以纹理量为准）
#   Q3 有没有运动、主体有没有跑出画面
#   Q4 真值那一行与另外两行，画面内容是否一致（粗判）
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
      --stage-cfg "save::path=out/vqa-p22-$tag.txt" > "$LAB/logs/vqa-p22-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-p22-$tag.txt" 2>/dev/null
  echo
}

# Q1：三行场景一致性（★ 只能粗判；像素级裁决以 SSIM 为准：真值 vs FlashVSR = 0.895679）
Q1="这张图是 3 行 × 4 列的抽帧图，每一行是同一段视频的第 0、8、16、24 帧。第 1 行是原始画面，第 2 行是普通插值放大后的结果，第 3 行是 AI 超分放大后的结果。请用中文回答：这三行描述的是同一个场景吗？主体分别是什么？每一行的主体在画面中的位置和姿态是否一致？"
ask "scene" "$Q1" "$LAB/deliverables/images/p22-contact-sheet.png"

# Q2：纹理粗判 —— 哪一行表面更锐/更细碎（量化以 3×3 中值滤波纹理量为准）
Q2="这张图是 3 行 × 4 列的抽帧图，同一行内是同一段视频的第 0、8、16、24 帧。请用中文回答：只比较第 2 行和第 3 行，哪一行在平坦区域（比如墙面、地面、天空）上看起来纹理更细碎、更锐利、更有'颗粒感'？请分别描述第 2 行和第 3 行的表面质感。"
ask "texture" "$Q2" "$LAB/deliverables/images/p22-contact-sheet.png"

# Q3：1:1 裁切并排（真值 / 插值 / AI 超分）—— 问它能不能看出第三张的纹理更碎
Q3="这张图是三张 1:1 原尺寸裁切并排的图片：左边是原始画面，中间是普通插值放大，右边是 AI 超分放大。请用中文回答：右边的图和左边的图相比，细节是变多了还是变少了？右边的图有没有出现原图里没有的、看起来像'编造出来的'细小纹理或斑点？请描述右图相对左图多出来的细节是什么样的。"
ask "1to1" "$Q3" "$LAB/deliverables/images/p22-1to1-crop-3arms.png"

# Q4：有没有运动 + 主体是否跑出画面
Q4="这张图是 3 行 × 4 列的抽帧图，每一行是同一段视频的第 0、8、16、24 帧。请用中文回答：画面里有没有发生运动或镜头移动？主体有没有跑出画面或者位置发生明显变化？"
ask "motion" "$Q4" "$LAB/deliverables/images/p22-contact-sheet.png"
