#!/bin/bash
# nightly_guard.sh — vpipe 夜间自动任务统一守卫
#
# 背景（2026-11-23 第 24 轮）：
#   原 4 槽的「今天已跑则跳过 / 并发保护」判断写在 prompt 文本里靠 agent 自觉遵守，
#   既不可自动化测试，也会让「立即运行」在 last_run=今天 时空转。
#   本脚本把判断标准化为唯一可执行入口，支持自动/立即/测试三模式。
#
# 模式：
#   check              自动模式（4 个定时槽用）：今天已跑或并发中→SKIP；否则建锁→RUN
#   force              立即运行（手动触发）：忽略日期，仅拒并发；建锁→RUN
#   status             显示当前状态（不修改任何文件）
#   release <R> [时间] 成功后推进 round 并删锁
#   test [HH:MM]       隔离测试某槽的四类判断（临时文件，不碰真实 state/lock）
#
# 退出码：0=RUN  10=今天已跑SKIP  11=并发中SKIP  2=用法错误
# 环境变量覆盖（测试用）：VPIPE_GUARD_STATE / VPIPE_GUARD_LOCK
set -uo pipefail

LAB="/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
STATE="${VPIPE_GUARD_STATE:-$LAB/report/.auto-round-state.json}"
LOCK="${VPIPE_GUARD_LOCK:-$LAB/report/.auto-round.lock}"
TODAY=$(date '+%Y-%m-%d')
NOW=$(date '+%Y-%m-%d %H:%M')
MODE="${1:-check}"
LOCK_TTL=5400   # 90 分钟（与 SOP 硬超时一致）

jget() { python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get(sys.argv[2]) or '')" "$1" "$2" 2>/dev/null; }
last_run_date() { jget "$1" last_run | cut -c1-10; }
round_now() { r=$(jget "$1" round); if [ -n "$r" ]; then echo "$r"; else echo 0; fi; }

decide() {
  local force="$1"
  # 1) 并发保护：锁存在且 mtime < TTL → 上一轮未结束
  if [ -f "$LOCK" ]; then
    local mt age
    mt=$(stat -f %m "$LOCK" 2>/dev/null || echo 0)
    age=$(( $(date +%s) - mt ))
    if [ "$age" -lt "$LOCK_TTL" ]; then
      echo "SKIP|LOCK|上一轮未结束(锁存活 ${age}s < ${LOCK_TTL}s)"
      return 11
    fi
  fi
  # 2) 日期去重（仅自动模式）：last_run 是今天 → 今天任一槽已成功
  if [ "$force" = "0" ]; then
    local lrd
    lrd=$(last_run_date "$STATE")
    if [ "$lrd" = "$TODAY" ]; then
      echo "SKIP|DATE|今天($TODAY)已成功跑过 last_run=$lrd"
      return 10
    fi
  fi
  # 3) 获得运行权：建锁，下一轮 R = round + 1
  local r=$(( $(round_now "$STATE") + 1 ))
  printf 'mode=%s slot_run=%s\n' "$MODE" "$NOW" > "$LOCK"
  echo "RUN||下一轮 R=${r}（锁已建立）"
  return 0
}

case "$MODE" in
  check)
    out=$(decide 0); rc=$?; echo "$out"; exit $rc ;;
  force)
    out=$(decide 1); rc=$?; echo "$out"; exit $rc ;;
  status)
    echo "TODAY=$TODAY  NOW=$NOW  MODE=status"
    echo "STATE=$STATE"
    cat "$STATE" 2>/dev/null || echo "(state 不存在)"
    echo "round=$(round_now "$STATE")  last_run_date=$(last_run_date "$STATE")"
    echo "LOCK=$LOCK"
    if [ -f "$LOCK" ]; then
      echo "锁内容: $(cat "$LOCK")  mtime=$(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$LOCK")"
    else
      echo "(无锁)"
    fi
    ;;
  release)
    R="${2:-}"; STAMP="${3:-$NOW}"
    if [ -z "$R" ]; then echo "用法: release <round> [\"stamp\"]" >&2; exit 2; fi
    mkdir -p "$(dirname "$STATE")"
    printf '{"round": %s, "last_run": "%s"}\n' "$R" "$STAMP" > "$STATE"
    rm -f "$LOCK"
    echo "RELEASED round=$R last_run=$STAMP (锁已删)"
    ;;
  test)
    SLOT="${2:-00:30}"
    TMP=$(mktemp -d /tmp/vpipe-guard-test.XXXXXX)
    YEST=$(date -v-1d '+%Y-%m-%d')
    printf '{"round": 23, "last_run": "%s 00:30"}\n' "$TODAY" > "$TMP/s_today"
    printf '{"round": 23, "last_run": "%s 06:30"}\n' "$YEST"  > "$TMP/s_yest"
    echo "===== 槽 $SLOT 守卫逻辑测试（隔离，不碰真实 state/lock） ====="
    # ★ 必须用子进程调用脚本自身：给 shell 函数前置 VAR=x 不会覆盖函数内已固定的全局 $LOCK
    run_case() {
      local desc="$1" st="$2" lk="$3" m="$4" out rc
      out=$(VPIPE_GUARD_STATE="$st" VPIPE_GUARD_LOCK="$lk" bash "$LAB/scripts/nightly_guard.sh" "$m" 2>&1); rc=$?
      printf '%-30s %s  exit=%s\n' "$desc" "$out" "$rc"
    }
    run_case "场景1 今天已跑→应SKIP(10)" "$TMP/s_today" "$TMP/l1" check
    run_case "场景2 今天未跑→应RUN(0)"  "$TMP/s_yest"  "$TMP/l2" check
    run_case "场景3 force立即→应RUN(0)" "$TMP/s_today" "$TMP/l3" force
    printf 'testfresh' > "$TMP/l4"
    run_case "场景4 并发锁新鲜→应SKIP(11)" "$TMP/s_yest" "$TMP/l4" check
    rm -rf "$TMP"
    ;;
  *)
    echo "用法: $0 {check|force|status|release|test} [参数]" >&2; exit 2 ;;
esac
