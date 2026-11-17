#!/bin/bash
# P3.4 续接的 LFM3-VL-2B 第三方复核（独立于生成链路）
#
# Q1 跨段一致性 —— 四段是不是同一只猫、同一个窗户、同一条光线？有没有换猫/换景？
# Q2 画面健康 —— 有没有花屏/噪点/条纹/撕裂/纯黑块？（P4 刚踩过花屏，必须独立复核）
# Q3 接缝跳变 —— 把每段的首帧与上一段的末帧放在一起看，接缝处有没有可见突变？
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1

ask () { # $1=tag  $2=question  $3..=images
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

F=$LAB/frames-p3-ext
Q1="这几张图是同一段连续视频在四个不同位置抽出的关键帧。请回答：1) 是否始终是同一只猫？毛色、脸型、脖子上的牛仔外套款式是否一致？2) 背景（窗户、木质窗台、窗外的房子和树）在四张里是否一致？3) 光线方向和色温是否一致？4) 猫的姿态变化是否自然连贯（不是突然换成另一只猫）？用中文回答。"
Q2="这些是生成视频的关键帧。请逐项回答有/没有：彩色噪点、马赛克方块、水平或竖直条纹、撕裂错位、大片纯黑或纯白区域、色彩突变块、四肢或脸部结构畸变。用中文回答。"
Q3="这是四段连续视频的拼接结果，每段的末帧紧接下一段的首帧。请按顺序描述这八张图之间画面是怎么变化的，特别指出：接缝处（每两帧之间）有没有突然的构图跳变、主体变形、光线突变或色彩跳变？接缝是平滑过渡还是明显断裂？用中文回答。"

if [ -d "$F" ]; then
  ask "p3-ext-consistency" "$Q1" "$F/p1_f000.png" "$F/p2_f000.png" "$F/p3_f000.png" "$F/p4_f000.png"
  ask "p3-ext-health" "$Q2" "$F/p1_f040.png" "$F/p2_f040.png" "$F/p3_f040.png" "$F/p4_f040.png"
  ask "p3-ext-seam" "$Q3" \
      "$F/p1_f_last.png" "$F/p2_f000.png" "$F/p2_f_last.png" "$F/p3_f000.png" \
      "$F/p3_f_last.png" "$F/p4_f000.png" "$F/p4_f_last.png" "$F/p1_f000.png"
fi
