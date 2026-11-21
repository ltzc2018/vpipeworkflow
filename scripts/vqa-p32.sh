#!/bin/bash
# P32 · LFM3-VL-2B 第三方复核（真值 vs lanczos 插值 vs RelayVSR 2×，P22 同源猫片）
#
# 已知 LFM3-VL-2B 四缺陷：①否定式编答案 ②细微锐度盲 ③运镜不可靠 ④场景只语义层。
# 只问「粗粒度、可观察」的问题；像素级裁决以 SSIM/PSNR 为准。
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope

ask () {
  local tag="$1"; shift
  local q="$1"; shift
  local line="$q"
  for f in "$@"; do
    line="$line<|__vpipe_fs_im_start__|>$f<|__vpipe_fs_im_end__|>"
  done
  echo "$line" | "$VP" --launch ./pipelines/lfm3-vl-vqa.vpipeline \
      --stage-cfg "save::path=out/vqa-p32-$tag.txt" > "$LAB/logs/vqa-p32-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-p32-$tag.txt" 2>/dev/null
  echo
}

Q1="这张图是 3 行 × 4 列的抽帧图，每一行是同一段视频的第 0、8、16、24 帧。第 1 行是原始画面，第 2 行是普通插值放大后的结果，第 3 行是 AI 超分放大后的结果。请用中文回答：这三行描述的是同一个场景吗？主体分别是什么？每一行的主体在画面中的位置和姿态是否一致？"
ask "scene" "$Q1" "$LAB/deliverables/images/p32-contact-sheet.png"

Q2="这张图是同一区域的三段 1:1 裁切并排（左、中、右三块）。左块来自原始高清画面，中块是普通插值放大的结果，右块是 AI 超分放大的结果。请用中文回答：只比较中块和右块，哪一块的毛发和胡须看起来更锐利、细节更丰富？右块有没有出现中块没有的噪点、颗粒或奇怪的纹理？"
ask "texture" "$Q2" "$LAB/deliverables/images/p32-1to1-crop-3arms.png"

Q3="这张图是同一帧画面的两个版本并排（左=原始高清，右=AI 超分放大后）。请用中文回答：两边的主体（动物）和背景内容是否一致？右边有没有左边没有的、看起来像 AI 编造出来的纹理或图案？"
ask "1to1" "$Q3" "$LAB/deliverables/images/p32-firstframe-ref-vs-relayvsr.png"
