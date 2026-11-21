#!/bin/bash
# P29 RelayVSR-x2 int8 权重下载（ModelScope Comfy-Org/RelayVSR，子目录 diffusion_models/ + vae/）
# 幂等：每个文件用 <file>.done 标记
DEST=/Users/minichen/AI-Models/vpipe-workspace/models/Comfy-Org/RelayVSR-x2
REPO=Comfy-Org/RelayVSR
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p29-relayvsr-download.log
mkdir -p "$(dirname "$LOG")" "$DEST/diffusion_models" "$DEST/vae"
echo "=== P29 RelayVSR-x2 权重下载 $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"

dl() { # $1=repo path  $2=dest path
  local f="$1" out="$2"
  if [ -f "$out.done" ]; then echo "SKIP $f (已有 .done)" >> "$LOG"; return 0; fi
  echo "GET $f $(date '+%H:%M:%S')" >> "$LOG"
  local code sz
  code=$(curl -sL --max-time 3600 --retry 3 --retry-delay 5 -o "$out" -w "%{http_code}" \
    "https://modelscope.cn/api/v1/models/$REPO/repo?Revision=master&FilePath=$f")
  sz=$(wc -c < "$out" 2>/dev/null || echo 0)
  echo "  -> http=$code bytes=$sz $(date '+%H:%M:%S')" >> "$LOG"
  if [ "$code" != "200" ] || [ "$sz" -lt 100000 ]; then echo "FAIL $f" >> "$LOG"; return 1; fi
  touch "$out.done"
}

dl "diffusion_models/relayvsr_x2_lightx2v_int8_convrot.safetensors" "$DEST/diffusion_models/relayvsr_x2_lightx2v_int8_convrot.safetensors" || exit 1
dl "vae/relayvsr_flash_vae_x2_fp32.safetensors" "$DEST/vae/relayvsr_flash_vae_x2_fp32.safetensors" || exit 1
echo "ALLDONE $(date '+%H:%M:%S')" >> "$LOG"
ls -laR "$DEST" >> "$LOG"
