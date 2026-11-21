#!/bin/bash
# P29 · LFM3-VL-2B 第三方复核（RelayVSR 2× vs lanczos 插值）
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
      --stage-cfg "save::path=out/vqa-p29-$tag.txt" > "$LAB/logs/vqa-p29-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-p29-$tag.txt" 2>/dev/null
  echo
}

Q1="这张图是两行×四列的抽帧图，每一行是同一段舞蹈视频的第0、40、80、123帧。第一行是普通插值放大后的画面，第二行是AI超分放大后的画面。请用中文回答：这两行描述的是同一个场景吗？每一行的主体在画面中的位置和姿态是否一致？"
ask "scene" "$Q1" "$LAB/deliverables/images/p29-contact-sheet.png"

Q2="这张图是两行×四列的抽帧图，上行是普通插值放大，下行是AI超分放大。请用中文回答：只比较两行，哪一行的画面看起来纹理更细碎、更锐利、更有颗粒感？请分别描述两行的表面质感。"
ask "texture" "$Q2" "$LAB/deliverables/images/p29-contact-sheet.png"

Q3="这张图是两张1:1原尺寸裁切并排的图片：左边是普通插值放大，右边是AI超分放大，内容是舞蹈视频同一帧的人物躯干。请用中文回答：右边的图和左边的图相比，细节是变多了还是变少了？右图有没有出现左图里没有的、看起来像编造出来的细小纹理或斑点？"
ask "1to1" "$Q3" "$LAB/deliverables/images/p29-1to1-crop.png"
