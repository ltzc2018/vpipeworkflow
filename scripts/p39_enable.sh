#!/bin/bash
# ============================================================================
# P39 一键启用脚本 —— 请在【本机真实终端】(Terminal.app/iTerm) 执行，不要在 AI 对话沙箱里跑
#
# 用法：
#   bash /Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/scripts/p39_enable.sh
#
# 做两件事：
#   1) 注册 launchd 定时任务 com.vpipe.nightly（00:30/02:30/04:30/06:30）
#   2) 立即触发一次无头闭环做验证（force 模式，忽略日期去重）
# ============================================================================
set -u
LAB="/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
PLIST="/Users/minichen/Library/LaunchAgents/com.vpipe.nightly.plist"
uid=$(id -u)

echo "=== P39 一键启用 ==="

# ---- 1. 注册 launchd ----
echo "[1/3] 注册 launchd 服务..."
launchctl bootout gui/$uid/com.vpipe.nightly 2>/dev/null || true
if launchctl bootstrap gui/$uid "$PLIST" 2>&1; then
  echo "  ✅ launchd 注册成功"
else
  echo "  ❌ launchd 注册失败（检查 plist: plutil -lint $PLIST）"
  exit 1
fi
launchctl print gui/$uid/com.vpipe.nightly >/dev/null 2>&1 && echo "  ✅ 服务已在 gui/$uid 域"

# ---- 2. 立即验证一次无头闭环（force，会真实跑一轮并推进轮次）----
echo "[2/3] 立即触发一次无头闭环验证（约 5-15 分钟，联网检索+固化+同步）..."
echo "  日志: $LAB/logs/p39-run-*.log（最新一份）"
bash "$LAB/scripts/p39_headless_runner.sh" 00:30 force
RC=$?
echo "  执行器退出码=$RC"

# ---- 3. 复核 ----
echo "[3/3] 复核状态..."
bash "$LAB/scripts/nightly_guard.sh" status
echo "  最近的 P39 运行日志:"
ls -t "$LAB"/logs/p39-run-*.log 2>/dev/null | head -1 | xargs -I{} sh -c 'echo "  {}"; tail -20 "{}"'

echo "=== 完成。以后每天 00:30/02:30/04:30/06:30 将由 launchd 独立触发，不经 WorkBuddy 会话层 ==="
