#!/bin/bash
# vpipe 夜间自动任务 · GitHub 同步脚本
#
# 用法：nightly_sync.sh <轮次号> "<本轮时间 YYYY-MM-DD HH:MM>" ["<本轮摘要>"]
#
# 设计要点（2026-11-17 实测）：
#   * 仓库 212 MB，全量 clone 会被 SIGTERM 打死 → 用常驻副本 + 增量 pull
#   * --filter=blob:none 部分克隆不能做 checkout（每个 blob 单独回源）→ 不用
#   * 仓库路径必须相对化；真人素材一律不推（public 仓库）
#
set -uo pipefail

ROUND="${1:-0}"
STAMP="${2:-$(date '+%Y-%m-%d %H:%M')}"
SUMMARY="${3:-夜间知识同步}"

LAB="/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
# 常驻工作副本：text-only 稀疏克隆（排除 videos/ 与 images/，避免拉媒体 blob 被杀）
REPO="${VPIPE_SYNC_REPO:-/Users/minichen/WorkBuddy/2026-11-12-21-10-11/.vpipeworkflow-t}"
LOG_DIR="$LAB/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/nightly-sync-r${ROUND}.log"

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }
fail() { log "❌ $*"; exit 1; }

log "=== 第 ${ROUND} 轮同步 · ${STAMP} · ${SUMMARY} ==="

# ---------- 0. 前置检查 ----------
[ -d "$REPO/.git" ] || fail "常驻副本不存在：$REPO（请先跑一次完整 clone，后台执行）"

# ---------- 1. 拉取远端增量 ----------
log "git pull --ff-only ..."
if ! git -C "$REPO" pull --ff-only >>"$LOG" 2>&1; then
  log "⚠️  pull 失败，尝试中止残留 rebase/merge 后重试"
  git -C "$REPO" rebase --abort 2>/dev/null
  git -C "$REPO" merge --abort 2>/dev/null
  git -C "$REPO" pull --ff-only >>"$LOG" 2>&1 || fail "pull 仍失败，见 $LOG"
fi
log "当前 HEAD：$(git -C "$REPO" log -1 --format='%h %ad %s' --date=short)"

# ---------- 2. 复制本轮变更 ----------
log "复制技能包 / 脚本 / 流水线 / 报告 ..."

# 2.1 技能包（以实验室副本为准，实验室副本 = 安装版）
# ⚠️ 2026-11-18 第 3 轮修正：BSD 的 `cp -R src/ dst/` 是「把 src 的**内容**铺到 dst」，
#    而 src 带了尾斜杠 → 旧写法 `cp -R "$d" "$REPO/skills/"` 会把每个技能的内容
#    **平铺**到仓库的 skills/ 顶层（skills/SKILL.md、skills/references/、skills/assets/…），
#    正确定位的 skills/<name>/… 从此再也不被刷新（实测陈旧了两轮：21 603 B vs 源 36 163 B），
#    而且 skills/SKILL.md 会被最后一个技能覆盖（实测 = vpipe-text-to-image），在 public 仓库里误导。
#
# ★★★ 2026-11-18 第 6 轮再修正：**上面那条「正解」在本沙箱里是错的**。
#   本机的 `cp` 走 sandbox shim，**尾斜杠语义与 BSD 相反**（实测三个用例）：
#     cp -R src/  dst/   → dst/src/...     ← 仍然嵌套（源带斜杠被忽略）
#     cp -R src/. dst/   → dst/...         ← ★ 唯一正确的「铺内容」写法
#     cp -R src   dst/   → dst/src/...     ← 嵌套
#   ⇒ 第 6 轮用旧写法 `cp -R "$d" "$REPO/skills/$name/"` 重新制造了**嵌套副本**
#     `skills/<name>/<name>/…`（21 个条目入库），而正确定位 `skills/<name>/references/…`
#     仍是旧内容 → 「树里有这个文件」但内容陈旧。
#   ⇒ **正解：源写成 "$d."（带 /.），目标带斜杠**；并在复制后**逐文件比字节数**。
for d in "$LAB"/skills/*/; do
  name=$(basename "$d")
  [ -d "$d" ] || continue
  mkdir -p "$REPO/skills/$name"
  cp -R "$d." "$REPO/skills/$name/" 2>/dev/null || fail "复制技能包失败：$name"
done

# 2.1b 清理历史遗留的嵌套副本 `skills/<name>/<name>/…`（第 6 轮的旧写法造成）
NESTED=$(find "$REPO/skills" -mindepth 2 -type d -name '*' 2>/dev/null \
         | while read -r p; do
             [ "$(basename "$(dirname "$p")")" = "$(basename "$p")" ] && echo "$p"
         done)
if [ -n "$NESTED" ]; then
  log "清理嵌套副本 skills/<name>/<name>/ …"
  echo "$NESTED" | while read -r p; do
    log "  移除：${p#$REPO/}"
    rm -rf "$p"
  done
fi

# 2.1c ★ 复制后逐文件比字节数（不能只看「树里有这个文件」—— 第 3/6 轮各踩过一次）
SKILL_BAD=0
for d in "$LAB"/skills/*/; do
  name=$(basename "$d")
  [ -d "$d" ] || continue
  while IFS= read -r rel; do
    a=$(wc -c < "$d$rel" 2>/dev/null || echo -1)
    b=$(wc -c < "$REPO/skills/$name/$rel" 2>/dev/null || echo -1)
    if [ "$a" != "$b" ]; then
      log "❌ 字节不一致：skills/$name/$rel  源=$a 仓库=$b"
      SKILL_BAD=$((SKILL_BAD+1))
    fi
  done < <(cd "$d" && find . -type f)
done
if [ "$SKILL_BAD" -ne 0 ]; then
  fail "技能包有 $SKILL_BAD 个文件字节不一致（见上），已中止推送"
fi
log "✅ 技能包逐文件字节校验通过"

# 2.2 脚本与流水线
cp -R "$LAB"/scripts/. "$REPO/scripts/" 2>/dev/null
cp -R "$LAB"/pipelines/. "$REPO/pipelines/" 2>/dev/null

# 2.3 报告 → docs/reports/（含两份主报告 + SOP + 知识台账 + 轮次状态）
mkdir -p "$REPO/docs/reports"
for f in "vpipe-H3-部署与测试报告.md" "vpipe-后续计划任务.md" "vpipe-daily-knowledge.md" \
         "vpipe-夜间自动任务SOP.md" "vpipe-upstream-issues.md" "vpipe-能力与速度总表.md" \
         ".auto-round-state.json"; do
  [ -f "$LAB/report/$f" ] && cp "$LAB/report/$f" "$REPO/docs/reports/$f"
done
[ -d "$LAB/report/issues" ] && cp -R "$LAB/report/issues" "$REPO/docs/reports/" 2>/dev/null

# ---------- 3. 真人素材防火墙 ----------
log "检查真人素材 ..."
BAD=$(git -C "$REPO" ls-files | grep -Ei 'refs-real|real-photo|boogu-real|refs_real' || true)
if [ -n "$BAD" ]; then
  log "❌ 检测到应排除的真人文件："
  echo "$BAD" | tee -a "$LOG"
  git -C "$REPO" rm --cached --quiet $(echo "$BAD" | tr '\n' ' ') 2>/dev/null
  fail "已从索引移除，请人工确认后重跑"
fi
log "✅ 索引中无真人文件"

# ---------- 4. 提交与推送 ----------
cd "$REPO" || fail "进入仓库失败"
git add -A
if git diff --cached --quiet; then
  log "无变更，无需提交"
else
  git commit -q -m "docs: 第 ${ROUND} 轮夜间知识同步（${STAMP}）— ${SUMMARY}" || fail "commit 失败"
  log "已提交：$(git log -1 --format='%h %s')"
  git push origin main >>"$LOG" 2>&1 || fail "push 失败，见 $LOG"
  log "✅ 已推送到 origin/main"
fi

log "=== 同步完成 ==="
