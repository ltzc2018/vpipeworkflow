#!/bin/bash
# P3 + P4 修正成果同步到 GitHub（ltzc2018/vpipeworkflow，走 SSH）
# 规则：路径相对化；真人照片一律不上传（.gitignore 已挡 refs-real/ 等）
set -eu
REPO=${1:-/tmp/vpipeworkflow}
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
SKILL_REF=$HOME/.workbuddy/skills/vpipe-reference-to-video
SKILL_PRE=$HOME/.workbuddy/skills/vpipe-live-preview
SKILL_PREP=$HOME/.workbuddy/skills/vpipe-model-prepare

cd "$REPO"

echo "== 1. 流水线（P3 768p 系列 + 续接系列）=="
mkdir -p pipelines
for f in "$WS/pipelines"/p3-*.vpipeline; do
  [ -f "$f" ] && cp "$f" pipelines/
done

echo "== 2. 成片 =="
mkdir -p videos
for f in p3-768p-shift6.mp4 p3-768p-shift12.mp4 p3-544p-ref.mp4 p3-768p-4step.mp4 \
         p3-768p-shift6-241f.mp4; do
  [ -f "$WS/out/$f" ] && cp "$WS/out/$f" videos/
done
# 四段式续接：只推拼接成片（h264，约 1–2 MB）；
# 分段本体是 ffv1 无损，每个 35 MB，不进仓库（本地 deliverables/videos/ 保留）
for f in p3-ext-full.mp4 p3-ext-full2.mp4; do
  [ -f "$WS/out/$f" ] && cp "$WS/out/$f" videos/
done

echo "== 3. 印相 / 图 =="
mkdir -p images
for f in "$LAB/deliverables/images"/p3-*.png; do
  [ -f "$f" ] && cp "$f" images/
done

echo "== 4. P4 修复后的预览流交付物 =="
for f in "$LAB/deliverables/videos"/p4-preview-stream-*.mp4; do
  [ -f "$f" ] && cp "$f" videos/
done

echo "== 5. 日志 =="
mkdir -p logs
for f in "$LAB/logs"/p3-*.log "$LAB/logs"/p3-*.seconds "$LAB/logs"/p3-*.mem; do
  [ -f "$f" ] && cp "$f" logs/
done
for f in p3-analysis.json p3-ext-analysis.json; do
  [ -f "$LAB/logs/$f" ] && cp "$LAB/logs/$f" logs/
done

echo "== 6. 脚本 =="
mkdir -p scripts
for f in "$LAB/scripts"/p3_*.py "$LAB/scripts"/p3_*.sh "$LAB/scripts"/detach_run.py; do
  [ -f "$f" ] && cp "$f" scripts/
done
# P4 修复脚本（注意：脚本开头已 cd $REPO，源路径必须用绝对路径）
for f in p4_fix_preview.py p4_mp4box.py ws_capture.py; do
  [ -f "$LAB/scripts/$f" ] && cp "$LAB/scripts/$f" scripts/
done

echo "== 7. 文档 =="
mkdir -p docs
cp "$LAB/report/vpipe-H3-部署与测试报告.md" docs/
cp "$LAB/report/vpipe-后续计划任务.md" docs/

echo "== 8. 技能包 =="
mkdir -p skills/vpipe-reference-to-video/references skills/vpipe-live-preview/references \
         skills/vpipe-live-preview/scripts skills/vpipe-model-prepare/references \
         skills/vpipe-model-prepare/assets
cp "$SKILL_REF/SKILL.md" skills/vpipe-reference-to-video/
for f in "$SKILL_REF"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-reference-to-video/references/
done
cp "$SKILL_PRE/SKILL.md" skills/vpipe-live-preview/
for f in "$SKILL_PRE"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-live-preview/references/
done
for f in p4_fix_preview.py p4_mp4box.py ws_capture.py p4_run.py p4_beats.py p4_anchor_emergence.py split_preview.py; do
  [ -f "$SKILL_PRE/scripts/$f" ] && cp "$SKILL_PRE/scripts/$f" skills/vpipe-live-preview/scripts/
done
cp "$SKILL_PREP/SKILL.md" skills/vpipe-model-prepare/
for f in "$SKILL_PREP"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-model-prepare/references/
done
for f in "$SKILL_PREP"/assets/*; do
  [ -f "$f" ] && cp "$f" skills/vpipe-model-prepare/assets/
done

echo "== 9. 隐私自检 =="
if git ls-files | grep -iE "refs-real|real-photo|boogu-real"; then
  echo "!! 仓库里有真人素材，中止"; exit 1
else
  echo "✅ 无真人素材"
fi

echo
git status --short | head -60
