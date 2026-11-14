#!/bin/bash
# LFM3-VL 语义验证：对多条 H3 产出视频做同一提问，独立于生成链路
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1

ask () { # $1=tag  $2=question  $3=frames...
  local tag="$1"; shift
  local q="$1"; shift
  local line="$q"
  for f in "$@"; do
    line="$line<|__vpipe_fs_im_start__|>$f<|__vpipe_fs_im_end__|>"
  done
  echo "$line" | "$VP" --launch ./pipelines/lfm3-vl-vqa.vpipeline \
      --stage-cfg "save::path=out/vqa-$tag.txt" > "$LAB/vqa-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-$tag.txt" 2>/dev/null
  echo
}

Q1="这些画面里的动物是什么？请描述它的毛色、姿态和所处环境。用中文回答。"
Q2="第一张画面里的动物身上穿着什么衣服？衣服是什么颜色和款式？后面几张画面里这件衣服还在吗？用中文回答。"

ask "A-cat-ref"  "$Q1" "$LAB/vqa-frames/pika-ref2va-ablation-f0.png" "$LAB/vqa-frames/pika-ref2va-ablation-f60.png" "$LAB/vqa-frames/pika-ref2va-ablation-f120.png"
ask "B-no-ref"   "$Q1" "$LAB/vqa-frames/pika-ref2va-noref-f0.png"   "$LAB/vqa-frames/pika-ref2va-noref-f60.png"   "$LAB/vqa-frames/pika-ref2va-noref-f120.png"
ask "i2va-anchor" "$Q2" "$LAB/vqa-frames/pika-i2va-shop-f0.png"   "$LAB/vqa-frames/pika-i2va-shop-f60.png"   "$LAB/vqa-frames/pika-i2va-shop-f120.png"
