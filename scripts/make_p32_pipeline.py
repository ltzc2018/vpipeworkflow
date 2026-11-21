#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P32 —— RelayVSR 2× 真值对照（在 P22 的 320×192 源上补 2× 臂）

目的：P29 在 dance-woman 上确认了 RelayVSR 2× 跑通 + 确定性，但**无真值**可判
「编造量」。P22 判决 FlashVSR 4× 是「细节生成器非保真放大器」（纹理量 = 真值 1.76×）。
本轮在**同一份 320×192 源**上补 RelayVSR 2× 臂（→ 640×384，与 768p 真值降采样同口径
可比——P22 真值链是 768p → lanczos 降到 1280×768；本轮真值链是 768p → lanczos 降到
640×384），量化 2× 档的「编造量」。

流水线：以官方模板 relayvsr-upscale-x2.vpipeline 为基底，只改必要项。
自检断言（写文件前先验）：
  ① relayvsr-upscale 接 video-to-rgb 单路
  ② output_width/height 都写了（不写 = 按 4K 规划 → 必炸）
  ③ autotune:false 显式写（逐位复现判据）
  ④ save-video 两路 + output_url 绝对路径
  ⑤ 权重目录按 ComfyUI 布局摆放（diffusion_models/ + vae/）
"""
import json
import os
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
TEMPLATE = os.path.join(LAB, "repo/vpipe/docs/pipelines/relayvsr-upscale-x2.vpipeline")
OUT = "/Users/minichen/AI-Models/vpipe-workspace/pipelines/p32-relayvsr-x2-640x384.vpipeline"
MODEL_DIR = "/Users/minichen/AI-Models/vpipe-workspace/models/Comfy-Org/RelayVSR-x2"

SRC = "/Users/minichen/AI-Models/vpipe-workspace/p22-src-320x192.mp4"   # 复用 P22 素材
DST = "/Users/minichen/AI-Models/vpipe-workspace/out/p32/p32-relayvsr-x2-640x384.mp4"
W, H = 640, 384    # 320×192 的 2×（与 P22 的 4× 输出 1280×768 互补，真值同链）


def fail(msg):
    print("!! 自检失败：%s" % msg)
    sys.exit(1)


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        pipe = json.load(f)

    stages = {s["id"]: s for s in pipe["stages"]}

    # ---- 1. 模型：绝对路径（本地 ComfyUI 布局目录）
    stages["relayvsr-upscale"]["config"]["hf_dir"] = MODEL_DIR

    # ---- 2. 输入：P22 同源 320×192
    stages["load-video"]["config"]["input_url"] = SRC
    stages["load-audio"]["config"]["input_url"] = SRC

    # ---- 3. 输出尺寸：320×192 → 640×384（必写！不写按 4K 规划）
    stages["relayvsr-upscale"]["config"]["output_width"] = W
    stages["relayvsr-upscale"]["config"]["output_height"] = H

    # ---- 4. 关内核竞速（逐位复现判据，P29 K103 已证 RelayVSR autotune 真生效）
    stages["relayvsr-upscale"]["config"]["autotune"] = False

    # ---- 5. 输出
    stages["save-video"]["config"]["output_url"] = DST

    # ================= 自检断言（写文件之前） =================
    rs = stages["relayvsr-upscale"]
    assert len(rs["iports"]) == 1 and rs["iports"][0]["src"] == "video-to-rgb", \
        "relayvsr-upscale 应接 video-to-rgb 单路"
    assert rs["config"].get("output_width") == W and rs["config"].get("output_height") == H, \
        "output_width/height 必须显式写"
    assert rs["config"].get("autotune") is False, "autotune:false 必须显式写"
    assert rs["config"].get("seed") is not None, "seed 必须固定"

    sv = stages["save-video"]
    assert len(sv["iports"]) == 2, "save-video 必须接两路"
    assert sv["iports"][0]["src"] == "rgb-to-video" and sv["iports"][1]["src"] == "audio-to-pcm", \
        "save-video 两路接错"
    assert sv["config"]["output_url"].startswith("/"), "output_url 必须绝对路径（K89）"

    # 内存账：640×384 输出（2×，P29 实测 1664×960 才 7153 MB → 本轮远小于此）
    assert W * H < 1664 * 960, "输出面积应小于 P29 的 1664×960"

    if not os.path.isdir(MODEL_DIR):
        fail("模型目录不存在：%s" % MODEL_DIR)
    for sub, ext in (("diffusion_models", ".safetensors"), ("vae", ".safetensors")):
        p = os.path.join(MODEL_DIR, sub)
        if not (os.path.isdir(p) and any(f.endswith(ext) for f in os.listdir(p))):
            fail("缺 %s/%s" % (sub, ext))

    # ================= 写盘 =================
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pipe, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("OK 写出 %s" % OUT)
    print("   模型  = %s" % MODEL_DIR)
    print("   输入  = %s (320×192, P22 同源)" % SRC)
    print("   输出  = %s (%d×%d)" % (DST, W, H))
    print("   自检  = 全部通过")


if __name__ == "__main__":
    main()
