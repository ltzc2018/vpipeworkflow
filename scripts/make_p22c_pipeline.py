#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P22c —— FlashVSR+ Turbo 原生 Metal 视频超分：流水线生成器 (修正版)"""
import json
import os
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
TEMPLATE = os.path.join(LAB, "repo/vpipe/docs/pipelines/flashvsr-plus-upscale-1920x1088.vpipeline")
OUT = "/Users/minichen/AI-Models/vpipe-workspace/pipelines/p22c-plus-upscale-1920.vpipeline"
MODEL_ROOT = "/Users/minichen/AI-Models/vpipe-workspace/models/ruchangyao/FlashVSR_plus"

# 4x 契约输入：480x288 -> 1920x1152
SRC_1920 = "p22-src-480x288.mp4"
DST = "out/p22/p22c-armC-plus-1920x1152.mp4"
W, H = 1920, 1152
FRAMES = 49                          # 16k+1

def main():
    if not os.path.exists(TEMPLATE):
        print("!! 模板不存在: %s" % TEMPLATE)
        return

    with open(TEMPLATE, encoding="utf-8") as f:
        pipe = json.load(f)

    stages = {s["id"]: s for s in pipe["stages"]}

    # ---- 1. 模型
    stages["model-select"]["config"]["hf_dir"] = MODEL_ROOT

    # ---- 2. 输入
    stages["load-video"]["config"]["input_url"] = SRC_1920
    stages["load-audio"]["config"]["input_url"] = SRC_1920

    # ---- 3. 分辨率 (修正 ID)
    stages["upscale-in"]["config"]["width"] = W
    stages["upscale-in"]["config"]["height"] = H
    stages["generate-video"]["config"]["width"] = W
    stages["generate-video"]["config"]["height"] = H
    stages["generate-video"]["config"]["frames"] = FRAMES
    stages["squeeze-out"]["config"]["width"] = W
    stages["squeeze-out"]["config"]["height"] = H

    # ---- 4. 分组
    stages["temporal-stack"]["config"]["group_size"] = FRAMES

    # ---- 5. 关竞速
    stages["generate-video"]["config"]["autotune"] = False
    stages["vae-decode"]["config"]["autotune"] = False

    # ---- 6. 输出
    stages["save-video"]["config"]["output_url"] = DST

    # ================= 写盘 =================
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pipe, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("OK 写出 %s" % OUT)

if __name__ == "__main__":
    main()
