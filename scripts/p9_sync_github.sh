#!/bin/bash
# P9 成果同步到 GitHub（ltzc2018/vpipeworkflow，走 SSH）
# 规则：路径相对化（相对 vpipe 工作目录）；真人照片一律不上传（.gitignore 已挡 refs-real/ 等）
set -eu
REPO=${1:-/tmp/vpipeworkflow}
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
SKILL=$HOME/.workbuddy/skills/vpipe-model-prepare
SKILL2=$HOME/.workbuddy/skills/vpipe-reference-to-video

cd "$REPO"

echo "== 1. 流水线 =="
mkdir -p pipelines
for f in p9-ref2va-768p-a p9-ref2va-768p-b-shift12 p9-ref2va-768p-c-multiref p9-ref2va-768p-d-shift8; do
  [ -f "$WS/pipelines/$f.vpipeline" ] && cp "$WS/pipelines/$f.vpipeline" pipelines/
done

echo "== 2. 素材 =="
mkdir -p refs
for f in motion-pan-right-124f.mp4 minimax-h3-reference-subject.jpg; do
  [ -f "$WS/refs/$f" ] && cp "$WS/refs/$f" refs/
done

echo "== 3. 成片 =="
mkdir -p videos
for f in p9-ref2va-768p-a.mp4 p9-ref2va-768p-b-shift12.mp4 p9-ref2va-768p-c-multiref.mp4 \
         p9-ref2va-768p-d-shift8.mp4; do
  [ -f "$WS/out/$f" ] && cp "$WS/out/$f" videos/
done

echo "== 4. 印相 / 图 =="
mkdir -p images
for f in p9-a-contact.png p9-b-contact.png p9-c-contact.png p9-d-contact.png \
         p9-montage.png p9-crop-compare.png; do
  [ -f "$LAB/deliverables/images/$f" ] && cp "$LAB/deliverables/images/$f" images/
done

echo "== 5. 日志 =="
mkdir -p logs
for f in "$LAB/logs"/p9-*.log "$LAB/logs"/p9-*.seconds "$LAB/logs"/p9-*.json "$LAB/logs"/vqa-p9-*.log; do
  [ -f "$f" ] && cp "$f" logs/
done

echo "== 6. 脚本 =="
mkdir -p scripts
for f in "$LAB/scripts"/p9_*.py "$LAB/scripts"/p9_*.sh "$LAB/scripts"/make_p9_pipelines.py "$LAB/scripts"/vqa-p9.sh; do
  [ -f "$f" ] && cp "$f" scripts/
done

echo "== 7. 文档 =="
mkdir -p docs
cp "$LAB/report/vpipe-H3-部署与测试报告.md" docs/
cp "$LAB/report/vpipe-后续计划任务.md" docs/

echo "== 8. 技能包 =="
mkdir -p skills/vpipe-model-prepare/references skills/vpipe-model-prepare/assets
cp "$SKILL/SKILL.md" skills/vpipe-model-prepare/
for f in "$SKILL"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-model-prepare/references/
done
for f in "$SKILL"/assets/*.vpipeline; do
  [ -f "$f" ] && cp "$f" skills/vpipe-model-prepare/assets/
done
mkdir -p skills/vpipe-reference-to-video/references
cp "$SKILL2/SKILL.md" skills/vpipe-reference-to-video/
for f in "$SKILL2"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-reference-to-video/references/
done

echo "== 9. 隐私自检 =="
if git ls-files | grep -iE "refs-real|real-photo|boogu-real"; then
  echo "!! 仓库里有真人素材，中止"; exit 1
else
  echo "✅ 无真人素材"
fi

echo
git status --short | head -60
