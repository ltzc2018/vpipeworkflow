#!/bin/bash
# P15 · LFM3-VL-2B 第三方复核（可复现性基线实验）
#
# 只问它能可靠回答的粗粒度问题。
# 已知 LFM3-VL-2B 的 4 个缺陷（见报告 18.3.6 / SOP 10.8）：
#   ① 否定式问题会编答案；② 分不清细微锐度差；③ 运镜方向不可靠；
#   ④ 按语义层判断场景同一性，对像素级差异不敏感
# → **「两次生成是否逐位相同」不能问它**（那正是第 ④ 条缺陷覆盖的场景），
#   逐位判据由 framemd5 / SSIM 给出。
#   这里只问「输出是否崩坏」——固定内核路径可能带来的副作用是本实验的真风险。
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
      --stage-cfg "save::path=out/vqa-$tag.txt" > "$LAB/logs/vqa-p15-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-$tag.txt" 2>/dev/null
  echo
}

# Q1：四臂首帧并排 —— 问「有没有崩坏/伪影/空画面」，不问「是否相同」
Q1="这张图是四段视频各自的第一帧，从左到右排成一行。请用中文描述每张图里的内容：主体是什么、姿态如何、背景是什么、清晰度如何。特别指出：有没有哪一张是全黑、全白、空白、明显崩坏、或者有严重的块状/网格状伪影？请逐张说明。"
ask "p15-4arms" "$Q1" "$LAB/deliverables/images/p15-first-frame-4arms.png"

# Q2：五行抽帧图 —— 每一行内部是否静止（验证静态夹具仍然成立）
Q2="这张图是 5 行 × 4 列的抽帧图，每一行是一段视频的第 0、7、14、21 帧。第 1 行是完全静止的静态参考图，其余 4 行是模型生成的视频。请用中文回答：第 2 到第 5 行，每一行内部从左到右，主体和背景有没有发生位置移动或姿态变化？请逐行描述。"
ask "p15-static" "$Q2" "$LAB/deliverables/images/p15-contact-sheet.png"

# Q3：af1 与 af2 的差异图 —— 若逐位相同应纯黑
Q3="这是一张两张图的差异对比图。请用中文回答：这张图整体是全黑的，还是能看到明显的白色斑块或条纹？如果能看到白色内容，说明它们在哪里、大概占多大面积？"
ask "p15-diff" "$Q3" "$LAB/deliverables/images/p15-af1-af2-diff.png"
