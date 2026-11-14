#!/bin/bash
# P3 抽帧：每组抽 **第 0 / 40 / 80 / 末帧** 四帧（自动化约定口径，跨组可按绝对帧号对齐比较）
# 注意：macOS 自带 bash 3.2，不支持关联数组（declare -A），故用 case 分派
set -u
FF=/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
DL=$LAB/deliverables
mkdir -p "$LAB/frames-p3" "$DL/images" "$DL/videos"

video_path () {
  case "$1" in
    shift6)  echo "$WS/out/p3-768p-shift6.mp4" ;;
    shift12) echo "$WS/out/p3-768p-shift12.mp4" ;;
    544p)    echo "$WS/out/p3-544p-ref.mp4" ;;
    4step)   echo "$WS/out/p3-768p-4step.mp4" ;;
    long241) echo "$WS/out/p3-768p-shift6-241f.mp4" ;;
    *)       echo "" ;;
  esac
}

frame_count () {
  $FF -v error -i "$1" -map 0:v:0 -f rawvideo -pix_fmt gray -s 16x16 - 2>/dev/null \
    | wc -c | awk '{print int($1/256)}'
}

for G in shift6 shift12 544p 4step long241; do
  V="$(video_path "$G")"
  if [ -z "$V" ] || [ ! -f "$V" ]; then echo "跳过 ${G}（无产物）"; continue; fi
  D="$LAB/frames-p3/$G"
  mkdir -p "$D"
  rm -f "$D"/f*.png

  N=$(frame_count "$V")
  LAST=$(( N - 1 ))
  # 约定口径：0 / 40 / 80 / 末帧；不足 81 帧时退化为 0 / N/3 / 2N/3 / 末帧
  if [ "$N" -ge 81 ]; then
    IDX0=0; IDX1=40; IDX2=80
  else
    IDX0=0; IDX1=$(( N / 3 )); IDX2=$(( 2 * N / 3 ))
  fi
  IDX3=$LAST

  # 输出名固定 f000 / f040 / f080 / f_last，保证 vqa-p3.sh 跨组引用一致
  for PAIR in "0:$IDX0:f000" "1:$IDX1:f040" "2:$IDX2:f080" "3:$IDX3:f_last"; do
    POS="${PAIR%%:*}"; REST="${PAIR#*:}"
    IDXN="${REST%%:*}"; NAME="${REST#*:}"
    $FF -y -v error -i "$V" -vf "select=eq(n\,${IDXN}),scale=640:-1" -fps_mode passthrough \
        -frames:v 1 "$D/$NAME.png" 2>/dev/null
  done

  python3 "$LAB/scripts/p3_contact.py" "$V" "$DL/images/p3-$G-contact.png" \
      "$IDX0" "$IDX1" "$IDX2" last
  cp "$V" "$DL/videos/$(basename "$V")"
  echo "P3-$G 抽帧完成 (总帧数 ${N}, 取帧 ${IDX0}/${IDX1}/${IDX2}/${IDX3})"
done
