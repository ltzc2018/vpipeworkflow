#!/bin/bash
# P1 成果同步到 GitHub（ltzc2018/vpipeworkflow，走 SSH）
# 规则：路径相对化；真人照片一律不上传（.gitignore 已挡 refs-real/ 等）
set -eu
REPO=${1:-/tmp/vpipeworkflow}
WS=/Users/minichen/AI-Models/vpipe-workspace
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
SKILL=$HOME/.workbuddy/skills/vpipe-reference-to-video

cd "$REPO"

echo "== 1. 流水线 =="
mkdir -p pipelines
for g in a b c d; do
  [ -f "$WS/pipelines/p1-$g-multi-ref.vpipeline" ] && cp "$WS/pipelines/p1-$g-multi-ref.vpipeline" pipelines/
done

echo "== 2. 素材（参考图 / 动作参考视频）=="
mkdir -p refs
for f in motion-pan-right-124f.mp4 motion-beach-124f.mp4 klein-multi-ref-panda-crop.jpg; do
  [ -f "$WS/refs/$f" ] && cp "$WS/refs/$f" refs/
done

echo "== 3. 成片 =="
mkdir -p videos
for g in a b c d; do
  [ -f "$WS/out/p1-$g-multi-ref.mp4" ] && cp "$WS/out/p1-$g-multi-ref.mp4" videos/
done
[ -f "$WS/out/p1-c-probe.mp4" ] && cp "$WS/out/p1-c-probe.mp4" videos/
cp "$WS/refs/motion-pan-right-124f.mp4" videos/p1-motion-ref.mp4

echo "== 4. 印相 / 图 =="
mkdir -p images
for g in a b c d; do
  [ -f "$LAB/deliverables/images/p1-$g-contact.png" ] && cp "$LAB/deliverables/images/p1-$g-contact.png" images/
done
[ -f "$LAB/deliverables/images/p1-motion-ref-contact.png" ] && cp "$LAB/deliverables/images/p1-motion-ref-contact.png" images/
[ -f "$LAB/deliverables/images/p1-montage.png" ] && cp "$LAB/deliverables/images/p1-montage.png" images/

echo "== 5. 日志 =="
mkdir -p logs
for f in "$LAB/logs"/p1-*.log "$LAB/logs"/p1-*.seconds; do
  [ -f "$f" ] && cp "$f" logs/
done
[ -f "$LAB/logs/p1-motion.json" ] && cp "$LAB/logs/p1-motion.json" logs/
[ -f "$LAB/logs/p1-audio.json" ] && cp "$LAB/logs/p1-audio.json" logs/

echo "== 6. 脚本 =="
mkdir -p scripts
for f in "$LAB/scripts"/p1_*.py "$LAB/scripts"/p1_*.sh; do
  [ -f "$f" ] && cp "$f" scripts/
done

echo "== 7. 文档 =="
mkdir -p docs
cp "$LAB/report/vpipe-H3-部署与测试报告.md" docs/
cp "$LAB/report/vpipe-后续计划任务.md" docs/

echo "== 8. 技能包 =="
mkdir -p skills/vpipe-reference-to-video/references
cp "$SKILL/SKILL.md" skills/vpipe-reference-to-video/
cp "$SKILL/references/multi-ref.md" skills/vpipe-reference-to-video/references/
for f in "$SKILL"/references/*.md; do
  [ -f "$f" ] && cp "$f" skills/vpipe-reference-to-video/references/
done

echo
git status --short | head -60
