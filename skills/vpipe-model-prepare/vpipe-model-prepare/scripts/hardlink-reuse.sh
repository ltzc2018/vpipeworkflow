#!/bin/bash
# 用硬链接复用 FL2VA-8bit 的编码器与双 VAE 到 Ref2VA-8bit，省约 27 GB
# 用法: hardlink-reuse.sh <FL2VA_8BIT_DIR> <REF2VA_8BIT_DIR>
set -euo pipefail
SRC="${1:?FL2VA 8bit 目录}"; DST="${2:?Ref2VA 8bit 目录}"
mkdir -p "$DST"
linked=0
while IFS= read -r f; do
  rel="${f#$SRC/}"
  case "$rel" in
    diffusion_models/*) continue ;;   # DiT 必须独立
  esac
  [ -f "$f" ] || continue
  target="$DST/$rel"; mkdir -p "$(dirname "$target")"
  if [ ! -e "$target" ]; then
    ln -f "$f" "$target"; linked=$((linked+1))
  fi
done < <(find "$SRC" -type f)
echo "已硬链接 $linked 个文件"
echo "--- 校验（links 应 > 1）---"
find "$DST" -type f -exec stat -f "%i %N links=%l" {} \; | head -10
echo "--- 磁盘占用对比 ---"
du -sh "$SRC" "$DST"
