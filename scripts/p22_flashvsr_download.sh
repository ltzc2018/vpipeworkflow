#!/bin/bash
# P22 FlashVSR 权重下载（ModelScope kuohao/FlashVSR-v1.1）
# 幂等：每个文件用 <file>.done 标记；已存在则跳过
DEST=/Users/minichen/AI-Models/vpipe-workspace/models/kuohao/FlashVSR-v1.1
REPO=kuohao/FlashVSR-v1.1
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p22-flashvsr-download.log
mkdir -p "$(dirname "$LOG")" "$DEST"
echo "=== P22 FlashVSR 权重下载 $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
FILES="posi_prompt.pth TCDecoder.ckpt Wan2.1_VAE.pth LQ_proj_in.ckpt diffusion_pytorch_model_streaming_dmd.safetensors"
for f in $FILES; do
  out="$DEST/$f"
  if [ -f "$out.done" ]; then echo "SKIP $f (已有 .done)" >> "$LOG"; continue; fi
  echo "GET $f $(date '+%H:%M:%S')" >> "$LOG"
  code=$(curl -sL --max-time 2400 --retry 3 --retry-delay 5 -o "$out" -w "%{http_code}" \
    "https://modelscope.cn/api/v1/models/$REPO/repo?Revision=master&FilePath=$f")
  sz=$(wc -c < "$out" 2>/dev/null || echo 0)
  echo "  -> http=$code bytes=$sz $(date '+%H:%M:%S')" >> "$LOG"
  if [ "$code" != "200" ] || [ "$sz" -lt 1000 ]; then echo "FAIL $f" >> "$LOG"; exit 1; fi
  touch "$out.done"
done
echo "ALLDONE $(date '+%H:%M:%S')" >> "$LOG"
ls -la "$DEST" >> "$LOG"
