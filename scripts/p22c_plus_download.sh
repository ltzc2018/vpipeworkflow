#!/bin/bash
# P22c FlashVSR+ Turbo 权重下载 (hf-mirror.com)
DEST=/Users/minichen/AI-Models/vpipe-workspace/models/ruchangyao/FlashVSR_plus
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p22c-plus-download.log
mkdir -p "$(dirname "$LOG")" "$DEST/turbo"

echo "=== P22c FlashVSR+ Turbo 下载 (hf-mirror.com) $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"

FILES="TCDecoder.ckpt Wan2.1_VAE.pth config.json"
for f in $FILES; do
  out="$DEST/$f"
  if [ -f "$out.done" ]; then echo "SKIP $f" >> "$LOG"; continue; fi
  echo "GET $f" >> "$LOG"
  /usr/bin/curl -sL --max-time 1800 --retry 3 -o "$out" "https://hf-mirror.com/ruchangyao/FlashVSR_plus/resolve/main/$f"
  if [ $? -eq 0 ] && [ $(wc -c < "$out") -gt 100 ]; then touch "$out.done"; else echo "FAIL $f" >> "$LOG"; exit 1; fi
done

TFILES="turbo/dit.safetensors turbo/lq_proj_in.safetensors"
for f in $TFILES; do
  out="$DEST/$f"
  if [ -f "$out.done" ]; then echo "SKIP $f" >> "$LOG"; continue; fi
  echo "GET $f" >> "$LOG"
  /usr/bin/curl -sL --max-time 3600 --retry 3 -o "$out" "https://hf-mirror.com/ruchangyao/FlashVSR_plus/resolve/main/$f"
  if [ $? -eq 0 ] && [ $(wc -c < "$out") -gt 1000 ]; then touch "$out.done"; else echo "FAIL $f" >> "$LOG"; exit 1; fi
done

echo "ALLDONE $(date '+%H:%M:%S')" >> "$LOG"
