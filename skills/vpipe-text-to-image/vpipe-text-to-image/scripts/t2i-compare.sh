#!/bin/bash
# Z-Image-Turbo vs Krea-2-Turbo：同提示词文生图对照
set -u
VP="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
cd "$WS" || exit 1
export VPIPE_DISABLE_TELEMETRY=1

# 提示词 1：与视频实验同题（猫 + 牛仔外套 + 窗台暖阳）
P1="A ginger tabby cat wearing a dark blue denim jacket with brass buttons, sitting on a wooden windowsill in warm late-afternoon sunlight, looking directly at the camera, photorealistic, shallow depth of field, warm golden light --no text, no watermark, no logo"

# 提示词 2：带货商品图
P2="E-commerce product photograph of a dark blue denim jacket hanging on a wooden hanger against a warm beige wall, soft directional window light from the left, crisp visible denim weave texture, contrast stitching and brass buttons clearly visible, clean minimal background, studio quality --no text, no watermark, no logo"

run () { # $1=model pipeline  $2=outname  $3=prompt
  local pl="$1" out="$2" p="$3"
  echo "── $out ─────────────────────────────"
  local t0=$(date +%s)
  "$VP" --launch "./pipelines/$pl" \
      --stage-cfg "text-prompt::text=\"$p\"" \
      --stage-cfg "save-image::path=\"out/$out.jpeg\"" \
      > "$LAB/t2i-$out.log" 2>&1
  local t1=$(date +%s)
  echo "耗时 $(( t1 - t0 )) 秒"
  grep -E "memory-plan|residency probe|peak|ResourcePlan" "$LAB/t2i-$out.log" | head -4
  ls -la "out/$out.jpeg" 2>/dev/null
  echo
}

run "z-image-turbo-t2i.vpipeline" "t2i-zimage-cat"     "$P1"
run "krea-2-turbo-t2i.vpipeline"  "t2i-krea-cat"      "$P1"
run "z-image-turbo-t2i.vpipeline" "t2i-zimage-product" "$P2"
run "krea-2-turbo-t2i.vpipeline"  "t2i-krea-product"  "$P2"
