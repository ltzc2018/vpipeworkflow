#!/bin/bash
DEST=/Users/minichen/AI-Models/vpipe-workspace/models/ruchangyao/FlashVSR_plus
LOG=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/logs/p22c-plus-download.log
mkdir -p "$DEST/turbo"

log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

download_file() {
    local f=$1
    local out="$DEST/$f"
    local url="https://hf-mirror.com/ruchangyao/FlashVSR_plus/resolve/main/$f"
    if [ -f "$out.done" ]; then log "SKIP $f"; return 0; fi
    
    for i in {1..5}; do
        log "GET $f (try $i)..."
        /usr/bin/curl -L -C - --max-time 1800 -o "$out" "$url"
        if [ $? -eq 0 ] && [ $(wc -c < "$out") -gt 100 ]; then
            touch "$out.done"
            log "SUCCESS $f"
            return 0
        fi
        log "RETRY $f in 10s..."
        sleep 10
    done
    log "CRITICAL FAIL $f"
    return 1
}

log "=== P22c FlashVSR+ Turbo 下载 V2 启动 ==="
FILES="TCDecoder.ckpt Wan2.1_VAE.pth config.json turbo/dit.safetensors turbo/lq_proj_in.safetensors"
for f in $FILES; do
    download_file "$f" || exit 1
done
log "ALLDONE"
