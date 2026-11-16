#!/bin/bash
# P9 抽帧：每组抽 **第 0 / 40 / 80 / 末帧** 四帧（与第 8 轮 P3 完全相同的口径，跨轮可按绝对帧号对齐）
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$LAB/frames-p9" "$DL/images" "$DL/videos"

video_path () {
  case "$1" in
    a)   echo "$WS/out/p9-ref2va-768p-a.mp4" ;;
    b)   echo "$WS/out/p9-ref2va-768p-b-shift12.mp4" ;;
    c)   echo "$WS/out/p9-ref2va-768p-c-multiref.mp4" ;;
    d)   echo "$WS/out/p9-ref2va-768p-d-shift8.mp4" ;;
    *)   echo "" ;;
  esac
}

frame_count () {
  $FF -v error -i "$1" -map 0:v:0 -f rawvideo -pix_fmt gray -s 16x16 - 2>/dev/null \
    | wc -c | awk '{print int($1/256)}'
}

for G in a b c d; do
  V="$(video_path "$G")"
  if [ -z "$V" ] || [ ! -f "$V" ]; then echo "跳过 ${G}（无产物）"; continue; fi
  D="$LAB/frames-p9/$G"
  mkdir -p "$D"
  /bin/rm -f "$D"/f*.png

  N=$(frame_count "$V")
  LAST=$(( N - 1 ))
  if [ "$N" -ge 81 ]; then
    IDX0=0; IDX1=40; IDX2=80
  else
    IDX0=0; IDX1=$(( N / 3 )); IDX2=$(( 2 * N / 3 ))
  fi
  IDX3=$LAST

  for PAIR in "0:$IDX0:f000" "1:$IDX1:f040" "2:$IDX2:f080" "3:$IDX3:f_last"; do
    POS="${PAIR%%:*}"; REST="${PAIR#*:}"
    IDXN="${REST%%:*}"; NAME="${REST#*:}"
    $FF -y -v error -i "$V" -vf "select=eq(n\,${IDXN}),scale=640:-1" -fps_mode passthrough \
        -frames:v 1 "$D/$NAME.png" 2>/dev/null
  done

  python3 "$LAB/scripts/p3_contact.py" "$V" "$DL/images/p9-$G-contact.png" \
      "$IDX0" "$IDX1" "$IDX2" last
  cp "$V" "$DL/videos/$(basename "$V")"
  echo "P9-$G 抽帧完成 (总帧数 ${N}, 取帧 ${IDX0}/${IDX1}/${IDX2}/${IDX3})"
done
