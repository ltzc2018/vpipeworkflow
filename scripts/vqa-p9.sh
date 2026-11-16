#!/bin/bash
# P9 语义复核：LFM3-VL-2B（独立于生成链路，不参与任何生成决策）
# 三个问题对应 P9 的三条判据：
#   Q1 身份 + 画质 —— 主体是谁？画面是清晰还是发糊？（判 shift 网格用错）
#   Q2 串味       —— 动作参考视频的内容有没有被带进来？（判多参考的分工）
#   Q3 运镜       —— 镜头怎么动？整体往左还是往右？（判 768p 下运镜锁是否还在）
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1

ask () { # $1=tag  $2=question  $3=images...
  local tag="$1"; shift
  local q="$1"; shift
  local line="$q"
  for f in "$@"; do
    line="$line<|__vpipe_fs_im_start__|>$f<|__vpipe_fs_im_end__|>"
  done
  echo "$line" | "$VP" --launch ./pipelines/lfm3-vl-vqa.vpipeline \
      --stage-cfg "save::path=out/vqa-$tag.txt" > "$LAB/logs/vqa-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-$tag.txt" 2>/dev/null
  echo
}

Q1="第一张是参考图，其余是同一提示词生成的视频关键帧。请回答：1) 视频里的主体是什么动物？毛色花纹？身上穿着什么？2) 画面是清晰锐利还是发糊、边缘发软？毛发的细节看得清吗？3) 整体是暖色还是偏灰？用中文简明回答。"
Q2="这些是生成视频的关键帧。请逐项回答有/没有：画面里出现了以下任何一样东西吗——海边、沙滩、奔跑的人、女性、竹子、熊猫？另外背景场景是什么？用中文回答。"
Q3="这是同一段视频的关键帧（按时间顺序）。请回答：镜头是怎么运动的？是静止不动、缓慢推近、拉远、左右平移、还是剧烈晃动？画面整体是在向左移动还是向右移动（以背景景物为参照）？用中文回答。"

for G in a b c d; do
  F="$LAB/frames-p9/$G"
  [ -d "$F" ] || continue
  ask "p9-$G-idsharp" "$Q1" "$WS/refs/minimax-h3-reference-subject.jpg" "$F/f000.png" "$F/f040.png" "$F/f080.png" "$F/f_last.png"
  ask "p9-$G-scene"    "$Q2" "$F/f000.png" "$F/f040.png" "$F/f080.png" "$F/f_last.png"
  ask "p9-$G-cam"      "$Q3" "$F/f000.png" "$F/f040.png" "$F/f080.png" "$F/f_last.png"
done

# 动作参考视频自身：作为「运镜基准」
M="$LAB/frames-p1/motion"
if [ -d "$M" ]; then
  ask "p9-ref-motion" "$Q3" "$M/f000.png" "$M/f040.png" "$M/f080.png" "$M/f123.png"
fi
