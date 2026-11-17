#!/bin/bash
# P11 第三方复核：LFM3-VL-2B（独立于生成链路，不参与任何生成决策）
# 复核目标：4:2:0（h264/yuv420p/limited/bt601）与 4:4:4（ffv1/yuv444p/full/bt709）
#           两种落盘格式的画面，肉眼是否可分辨差异。
# 预期：LFM3-VL 判不出差异（与 SSIM 差 0.005 的量化结果一致）——
#       即「4:2:0 丢的色度远小于人眼/模型的分辨阈」，0.03 的口径差纯属测量域问题。
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1
mkdir -p "$LAB/logs"

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

S="$LAB/p11-sheets"

# Q1：4:2:0 与 4:4:4 并排，能否看出画质/色彩差异
if [ -f "$S/p11-variants-frame0.png" ]; then
  ask "p11-variants" \
    "这张图是同一段视频的 8 个版本并排（从左到右依次是不同像素格式与色彩空间编码的落盘结果，内容完全相同）。请回答：1) 这些画面看起来有差别吗？特别是颜色饱和度、边缘锐度、是否有色块/条纹伪影。2) 哪几个看起来明显发糊或有色彩偏差。3) 整体判断：这 8 格在肉眼分辨下是否基本等价？用中文简明回答。" \
    "$S/p11-variants-frame0.png"
fi

# Q2：4:2:0 的印相 vs 4:4:4 的印相（0/40/80/末帧），逐帧看是否一致
if [ -f "$S/p11-V420-def-contact-sheet.png" ] && [ -f "$S/p11-V444-contact-sheet.png" ]; then
  ask "p11-420-vs-444" \
    "第一张是 4:2:0 编码版本的 4 个关键帧，第二张是 4:4:4 无损编码版本的同样 4 个关键帧。请回答：1) 两组画面的内容一样吗？2) 4:2:0 那组有没有肉眼可见的色彩偏差、边缘锯齿、色块或模糊？3) 能否从这两组里挑出画面质量明显更差的一组？如果挑不出来就说挑不出来。用中文回答。" \
    "$S/p11-V420-def-contact-sheet.png" "$S/p11-V444-contact-sheet.png"
fi

# Q3：真值无损 vs 4:2:0 —— 4:2:0 到底丢了什么
if [ -f "$S/p11-T444-contact-sheet.png" ] && [ -f "$S/p11-T420h-contact-sheet.png" ]; then
  ask "p11-truth-vs-420h" \
    "第一张是 4:4:4 无损基准的关键帧，第二张是 4:2:0 + limited + bt601 + h264 全默认链的关键帧。请回答：1) 两组内容一致吗？2) 第二组的颜色更灰/更饱和/偏黄偏蓝吗？3) 第二组的纹理、边缘、渐变有没有明显劣化？用中文回答。" \
    "$S/p11-T444-contact-sheet.png" "$S/p11-T420h-contact-sheet.png"
fi
