#!/bin/bash
# ============================================================================
# P39 根治方案：launchd 独立调度执行器（绕开 WorkBuddy 会话层空壳问题）
#
# 背景：WorkBuddy automation 会话被主对话抢占 → 空壳（K139/K144）。
# 方案：launchd 到点直接拉起本脚本 → 调用 codebuddy -p 无头 CLI（独立进程，
#       不经过 WorkBuddy 会话层）→ 按 SOP 执行 vpipe 夜间知识同步闭环。
#
# 用法：
#   bash p39_headless_runner.sh <槽位> [check|force]
#     槽位: 00:30 / 02:30 / 04:30 / 06:30
#     check: 守卫判定（并发锁保护）；force: 手动立即运行（忽略日期，仅拒并发）
#   由 launchd 调用时固定传 check；用户手动"立即运行"传 force。
#
# 退出码：0=成功闭环 / 11=并发中跳过 / 其它=失败（锁已清理，不推进轮次）
# ============================================================================
set -u

LAB="/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
CB="/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy"
NODE_BIN="/Users/minichen/.workbuddy/binaries/node/versions/22.22.2-6/bin"
MODEL="custom-local:deepseek-v4.1-flash"   # K146: -1017 别名上游无渠道(503)；去掉后缀才是 deeprouter 真实 ID（2026-11-24 实测可用）
PROMPT_FILE="$LAB/scripts/p39_sop_prompt.md"
LOG_DIR="$LAB/logs"

ARG1="${1:-00:30}"
ARG2="${2:-check}"

# launchd 4 时段共用同一条命令，用 --launchd-- 占位；此处按当前小时推断槽位
if [ "$ARG1" = "--launchd--" ]; then
  HOUR=$(date '+%H')
  case "$HOUR" in
    00) SLOT="00:30" ;;
    02) SLOT="02:30" ;;
    04) SLOT="04:30" ;;
    06) SLOT="06:30" ;;
    *)  SLOT="${HOUR}:30" ;;  # 手动 kickstart 等非整点触发，仍记录实际小时
  esac
  MODE="check"
else
  SLOT="$ARG1"
  MODE="$ARG2"
fi
TS="$(date '+%Y%m%d-%H%M%S')"
RUN_LOG="$LOG_DIR/p39-run-${SLOT//:/}-${TS}.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RUN_LOG"; }

# 环境：codebuddy 是 node 脚本，需显式注入 node 路径（launchd 环境 PATH 极简）
export PATH="$NODE_BIN:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
# ★ 关键（K145）：本机 WorkBuddy 定制版 cli/dist 下只打包了 codebuddy-lite-wb.mjs，
#   没有 codebuddy-headless / codebuddy 两个 CJS bundle。-p 会触发 headless 分支，
#   逐级回退到缺失的 dist/codebuddy → MODULE_NOT_FOUND（实测 2026-11-24 00:50）。
#   必须显式强制 lite-wb bundle（其支持 -p/--model/--permission-mode/--session-id/--add-dir）。
export CODEBUDDY_FORCE_LITE_WB_BUNDLE=1

log "===== P39 无头执行启动 slot=$SLOT mode=$MODE ====="

cd "$LAB" || { log "FATAL: 无法进入 $LAB"; exit 1; }

# ---- 第 0 步：守卫判定（复用已测试的 nightly_guard.sh）----
log "守卫判定: bash scripts/nightly_guard.sh $MODE"
bash scripts/nightly_guard.sh "$MODE"
GUARD_EXIT=$?
log "守卫退出码=$GUARD_EXIT"
if [ "$GUARD_EXIT" -eq 11 ]; then
  log "并发锁未释放，本槽跳过（另一轮真在跑）"
  exit 11
fi
if [ "$GUARD_EXIT" -ne 0 ]; then
  log "守卫返回异常码 $GUARD_EXIT，放弃执行并清理"
  bash scripts/nightly_guard.sh release "$(python3 -c "import json;print(json.load(open('report/.auto-round-state.json'))['round'])")" "$(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1
  exit "$GUARD_EXIT"
fi

# 读取守卫已算好的本轮 R
ROUND=$(python3 -c "import json;print(json.load(open('report/.auto-round-state.json'))['round']+1)")
SESSION_ID="p39-${SLOT//:/}-${TS}"
log "获得运行权，本轮 R=$ROUND session=$SESSION_ID"

# ---- 第 1 步：无头 CLI 执行 SOP（stdin 传 prompt，规避 lite 版参数解析 quirk）----
log "启动无头 CLI: codebuddy -p model=$MODEL session=$SESSION_ID"
SED_SCRIPT="s/__ROUND__/${ROUND}/g; s/__SLOT__/${SLOT}/g; s/__TS__/$(date '+%Y-%m-%d %H:%M')/g"

# ★ K147 看门狗：agent 在 trace 里 trace_end（成功或失败）后，CLI 进程有时不自行退出
#   （实测 2026-11-24 01:24 agent 已 error，但 CLI 挂 ESTABLISHED 连接僵死到 01:38+，
#    占锁阻塞后续槽）。这里起后台守护：每 20s 查本 session 的 trace 是否出现 trace_end，
#    出现即 kill CLI 进程组，让 runner 立刻进入校验/兜底，不再傻等 timeout。
#   trace 与 session 可靠关联：trace 文件内含 8 处 session-id 字符串。
WATCHDOG_PID=""
(
  for i in $(seq 1 270); do   # 270*20s = 90min，与硬超时对齐
    sleep 20
    # 找含本 session-id 且已 trace_end 的 trace 文件
    DONE_TRACE=$(grep -rl -- "$SESSION_ID" "$HOME/.workbuddy/traces/" 2>/dev/null \
      | while read -r tf; do grep -q '"type":"trace_end"' "$tf" 2>/dev/null && echo "$tf"; done \
      | head -1)
    if [ -n "$DONE_TRACE" ]; then
      # agent 已结束：温和 kill CLI（含 timeout 包装进程），让主线程继续
      echo "[watchdog $(date '+%H:%M:%S')] 检测到 agent trace_end，终止 CLI 进程" >> "$RUN_LOG"
      pkill -f "codebuddy -p.*$SESSION_ID" 2>/dev/null
      exit 0
    fi
  done
) &
WATCHDOG_PID=$!

sed "$SED_SCRIPT" "$PROMPT_FILE" | \
  /usr/bin/timeout 5400 "$CB" -p \
    --model "$MODEL" \
    --permission-mode bypassPermissions \
    --session-id "$SESSION_ID" \
    --add-dir "$LAB" >> "$RUN_LOG" 2>&1
CB_EXIT=$?
# 收尾看门狗
if [ -n "$WATCHDOG_PID" ]; then kill "$WATCHDOG_PID" 2>/dev/null; wait "$WATCHDOG_PID" 2>/dev/null; fi
log "无头 CLI 退出码=$CB_EXIT"

# ---- 第 2 步：校验闭环产物（成功 = round 已推进 且 有本轮同步日志）----
NEW_ROUND=$(python3 -c "import json;print(json.load(open('report/.auto-round-state.json'))['round'])")
SYNC_LOG="$LOG_DIR/nightly-sync-r${ROUND}.log"
if [ "$CB_EXIT" -eq 0 ] && [ "$NEW_ROUND" -ge "$ROUND" ] && [ -f "$SYNC_LOG" ]; then
  log "✅ 闭环成功: round $ROUND 已推进, 同步日志存在"
  exit 0
fi

# ---- 失败兜底：删锁但不推进轮次，供下个槽/下次重试 ----
log "⚠️ 闭环未完整: cb_exit=$CB_EXIT round=${NEW_ROUND}(期望$ROUND) sync_log=$([ -f "$SYNC_LOG" ] && echo 有 || echo 无)"
OLD_ROUND=$(python3 -c "import json;print(json.load(open('report/.auto-round-state.json'))['round'])")
bash scripts/nightly_guard.sh release "$OLD_ROUND" "$(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1
log "已清理并发锁（未推进轮次），详细输出见 $RUN_LOG"
exit 1
