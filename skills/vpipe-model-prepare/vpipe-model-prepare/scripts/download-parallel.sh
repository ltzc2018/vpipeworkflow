#!/bin/bash
# 大文件并行 Range 下载 + 拼接 + sha256 校验
# 用法: download-parallel.sh <URL> <OUT_PATH> <SIZE> <SHA256> [并行段数]
set -euo pipefail
URL="$1"; OUT="$2"; SIZE="$3"; SHA="$4"; N="${5:-8}"
PARTS="$(dirname "$OUT")/.parts-$(basename "$OUT")"
CHUNK=$(( (SIZE + N - 1) / N ))
mkdir -p "$PARTS" "$(dirname "$OUT")"

for i in $(seq 0 $((N-1))); do
  START=$(( i * CHUNK )); END=$(( START + CHUNK - 1 ))
  [ $END -ge $SIZE ] && END=$(( SIZE - 1 ))
  P="$PARTS/p$i"; WANT=$(( END - START + 1 ))
  (
    for a in $(seq 1 6); do
      HAVE=$(stat -f%z "$P" 2>/dev/null || echo 0)
      [ "$HAVE" = "$WANT" ] && break
      FROM=$(( START + HAVE ))
      curl -sL -C - --retry 8 --retry-delay 3 --max-time 5400 \
           -H "Range: bytes=${FROM}-${END}" "$URL" >> "$P" 2>/dev/null
    done
    echo "part$i done: $(stat -f%z "$P" 2>/dev/null || echo 0) / $WANT"
  ) &
done
wait

TOT=0; for i in $(seq 0 $((N-1))); do TOT=$(( TOT + $(stat -f%z "$PARTS/p$i") )); done
echo "sum parts: $TOT / $SIZE"
[ "$TOT" != "$SIZE" ] && { echo "SIZE_MISMATCH"; exit 1; }
cat "$PARTS"/p* > "$OUT"
ACT=$(shasum -a 256 "$OUT" | awk '{print $1}')
echo "actual  : $ACT"; echo "expected: $SHA"
[ "$ACT" = "$SHA" ] && echo "SHA256_OK" || { echo "SHA256_MISMATCH"; exit 1; }
