#!/bin/bash
# vpipe 工作区磁盘占用报告 + 可回收项识别
set -euo pipefail
WS="${1:-/Users/minichen/AI-Models/vpipe-workspace}"
echo "=== 磁盘 ==="; df -h / | tail -1
echo; echo "=== 各模型占用 ==="; du -sh "$WS"/models/*/ 2>/dev/null | sort -rh
echo; echo "=== 量化产物（local/）==="; du -sh "$WS"/models/local/*/ 2>/dev/null | sort -rh
echo; echo "=== 硬链接检查（links=1 表示独立文件，删除安全）==="
find "$WS"/models/local -type f -name "*.safetensors" -exec stat -f "links=%l  %N" {} \; 2>/dev/null | sort | head -20
