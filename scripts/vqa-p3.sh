#!/bin/bash
# P3 语义复核：LFM3-VL-2B（独立于生成链路）
# 三个问题对应 P3 的三条判据：
#   Q1 细节解析度 —— 毛发/牛仔布纹理在 768p 下是否真的被解出来？
#   Q2 画面健康   —— 有没有花屏/噪点/条纹/伪影？（这一轮刚修完预览流花屏，必须独立复核）
#   Q3 跨组一致性 —— shift6 / shift12 / 544p / 4step 四组是不是同一个场景与主体？
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

Q1="这些是同一提示词生成的视频关键帧。请回答：1) 画面主体是什么动物？穿着什么衣服？2) 毛发一根根是否清晰可辨？牛仔布的织纹能否看出经纬结构？3) 背景窗户玻璃和窗框的边缘是否锐利清晰？用中文简明回答，不要回避细节。"
Q2="这些是生成视频的关键帧。请逐项回答有/没有：画面里存在以下任何一种编码或生成异常吗——彩色噪点、马赛克方块、水平/竖直条纹、撕裂错位、大片纯黑或纯白区域、色彩突变块？用中文回答。"
Q3="这几张分别是同一条提示词在不同设置下生成的关键帧（依次是：768p正确设置、768p错误设置、544p、4步版本）。请回答：它们是不是同一个场景、同一个主体（同一只猫、同样的窗户和光线）？四组在构图和细节清晰度上有什么可见差别？用中文回答。"

for G in shift6 shift12 544p 4step long241; do
  F="$LAB/frames-p3/$G"
  [ -d "$F" ] || continue
  ask "p3-$G-detail" "$Q1" "$F/f000.png" "$F/f040.png" "$F/f080.png" "$F/f_last.png"
  ask "p3-$G-health" "$Q2" "$F/f000.png" "$F/f040.png" "$F/f080.png" "$F/f_last.png"
done

# 跨组对照（一次喂 4 组各一帧）
if [ -d "$LAB/frames-p3/shift6" ] && [ -d "$LAB/frames-p3/shift12" ] \
   && [ -d "$LAB/frames-p3/544p" ] && [ -d "$LAB/frames-p3/4step" ]; then
  ask "p3-cross-group" "$Q3" \
      "$LAB/frames-p3/shift6/f040.png" "$LAB/frames-p3/shift12/f040.png" \
      "$LAB/frames-p3/544p/f040.png" "$LAB/frames-p3/4step/f040.png"
fi
