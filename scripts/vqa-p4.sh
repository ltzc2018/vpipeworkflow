#!/bin/bash
# P4 第三方模型复核（LFM3-VL-2B，独立于生成链路）
# 用法： vqa-p4.sh <tag>
set -u
VP="${VPIPE_BIN:-/Applications/Vpipe Manager.app/Contents/Helpers/vpipe}"
WS="${VPIPE_WS:-$HOME/AI-Models/vpipe-workspace}"
LAB="${VPIPE_LAB:-$HOME/WorkBuddy/vpipe-lab}"
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1

TAG="${1:-i2va-fast}"
OUT="$LAB/deliverables/p4-preview/$TAG"
FR="$LAB/frames-p4/$TAG"

ask () { # $1=tag  $2=question  $3=images...
  local tag="$1"; shift
  local q="$1"; shift
  local line="$q"
  for f in "$@"; do
    [ -f "$f" ] || { echo "缺少 $f"; continue; }
    line="$line<|__vpipe_fs_im_start__|>$f<|__vpipe_fs_im_end__|>"
  done
  echo "$line" | "$VP" --launch ./pipelines/lfm3-vl-vqa.vpipeline \
      --stage-cfg "save::path=out/vqa-$tag.txt" > "$LAB/vqa-$tag.log" 2>&1
  echo "── $tag ──────────────────────────────────────────"
  cat "$WS/out/vqa-$tag.txt" 2>/dev/null
  echo
}

# 1) 锚定涌现：逐步预览里主体是否全程在场、是否逐步收敛
Q1="这些图片是同一个视频生成任务中，实时预览在视频首帧位置上的逐拍输出（从左到右是第1步到第6步）。请回答：1) 每一张图里的主体分别是什么？主体在每一步都在场吗？2) 主体身上的服装（牛仔外套/蓝色衣服）在每一步都保留吗？3) 画面清晰度是不是从左到右逐步提升？用中文回答。"
ask "p4-emerge-$TAG" "$Q1" "$OUT/contact-sheet-anchor-emergence.png"

# 2) 锚定对照：参考图 / 预览首帧 / 成片首帧
Q2="第一张是首帧锚定用的参考图，第二张是实时预览的第1帧，第三张是最终成片的第1帧。请回答：1) 第二张预览首帧里是不是参考图里的同一只猫？服装、外观、姿态与参考图一致吗？2) 第二张和第三张是同一个画面吗？3) 第二张比第三张少了哪些细节？用中文回答。"
ask "p4-anchor-$TAG" "$Q2" \
  "$FR/anchor-512.png" "$FR/preview-first.png" "$FR/final-first.png"

# 3) 预览 vs 成片：低清预览能否代表正片
Q3="第一张是实时预览的逐拍对比图（低清 TAE 解码），第二张是最终成片的第1帧（高清 VAE 解码）。请回答：1) 两张是不是同一个场景、同一个主体、同一动作？2) 用预览画面来判断这个结果好不好、要不要重跑，信息够不够？3) 预览丢失了哪些正片才有的细节？用中文回答。"
ask "p4-prev-vs-final-$TAG" "$Q3" \
  "$OUT/contact-sheet-anchor-emergence.png" "$FR/final-first.png"
