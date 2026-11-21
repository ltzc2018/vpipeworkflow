#!/bin/bash
# P28 调度器端口验证 runner —— 本地 build d72c22f，2 臂串行，幂等
set -u
LAB=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab
WS=/Users/minichen/AI-Models/vpipe-workspace
VPIPE="${VPIPE_BIN:-/tmp/vp28/Helpers/vpipe}"
LOGD=$LAB/logs
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
mkdir -p "$LOGD"

alive () { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

run_one () {
  local pipe="$1" logname="$2" out="$3"
  local done="$LOGD/$logname.done" pidf="$LOGD/$logname.pid" log="$LOGD/$logname.log"
  if [ -f "$done" ] && [ -f "$WS/out/$out" ]; then echo "[SKIP] $logname"; return 0; fi
  if [ -f "$pidf" ]; then
    local oldpid; oldpid=$(cat "$pidf" 2>/dev/null)
    if alive "$oldpid"; then echo "[WAIT] $logname alive pid=$oldpid"; return 1; fi
  fi
  echo "[RUN] $pipe -> $out  $(date '+%H:%M:%S')"
  echo $$ > "$pidf"
  "$VPIPE" --launch "$WS/pipelines/$pipe.vpipeline" > "$log" 2>&1
  local rc=$?
  rm -f "$pidf"
  if [ $rc -eq 0 ] && [ -f "$WS/out/$out" ]; then
    echo "[OK] $logname rc=0"; date '+%s' > "$done"
  else
    echo "[FAIL] $logname rc=$rc"; tail -5 "$log"
  fi
  return 0
}

cd "$WS" || exit 1

run_one p28-anchor p28-anchor p28-anchor.mp4
run_one p28-sgm    p28-sgm    p28-sgm.mp4
echo "[ALL-DONE] $(date '+%H:%M:%S')"
