#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P22 —— FlashVSR 原生 Metal 视频超分：流水线生成器（含自检断言）

以**上游官方模板** `docs/pipelines/flashvsr-upscale-1920x1088.vpipeline` 为基底，
只改必要项，不重画接线（SOP 10.7：generate-video 的 iport 数量必须与模板逐项一致）。

★ 第 5 轮坑 13.7：生成器必须带自检断言（写文件前先验），断言失败要早、要响。

自检项：
  ① generate-video 的 iports 总数 = 3，且 src 依次为 flashvsr-src-encoder / "" / model-select
  ② generate-video 的 width/height 都是 128 的倍数（FlashVSR 几何契约）
  ③ frames 满足 8k+1（FlashVSR-v1.1 的分块契约）
  ④ temporal-stack 的 group_size == frames（一组放完，避免残留）
  ⑤ autotune:false 出现 2 处（generate-video + vae-decode）
  ⑥ 模型目录存在，且恰好 1 个 .safetensors + 4 个 companion 文件齐全
  ⑦ save-video 接两路（rgb-to-video + audio-to-pcm）
"""
import json
import os
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
TEMPLATE = os.path.join(LAB, "repo/vpipe/docs/pipelines/flashvsr-upscale-1920x1088.vpipeline")
OUT = "/Users/minichen/AI-Models/vpipe-workspace/pipelines/p22-flashvsr-upscale.vpipeline"
MODEL_DIR = "/Users/minichen/AI-Models/vpipe-workspace/models/kuohao/FlashVSR-v1.1"

SRC = "p22-src-320x192.mp4"          # 低清输入（320×192 = 输出 1280×768 的 1/4）
DST = "out/p22/p22-armB-flashvsr-1280x768.mp4"
W, H = 1280, 768                     # 输出分辨率（128 的倍数）
FRAMES = 25                          # 8k+1（k=3），且是 FlashVSR-v1.1 的最小 clip（≥25）
SRC_DURATION_S = 25 / 24.0


def fail(msg):
    print("!! 自检失败：%s" % msg)
    sys.exit(1)


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        pipe = json.load(f)

    stages = {s["id"]: s for s in pipe["stages"]}

    # ---- 1. 模型：绝对路径（registry 里没有 FlashVSR 条目，resolve_model 对未注册 ref 直接当路径用）
    stages["model-select"]["config"]["hf_dir"] = MODEL_DIR

    # ---- 2. 输入
    stages["load-video"]["config"]["input_url"] = SRC
    stages["load-audio"]["config"]["input_url"] = SRC
    stages["load-audio"]["config"]["duration_s"] = round(SRC_DURATION_S, 4)

    # ---- 3. 目标分辨率：1280×768（上游源码给出的内存账：~20 GB @1920×1152，
    #        本机 24 GB 跑 1920 级别太紧 → 按面积比降到 44% ≈ 8.9 GB）
    stages["upscale-in"]["config"]["width"] = W
    stages["upscale-in"]["config"]["height"] = H
    stages["squeeze-out"]["config"]["width"] = W
    stages["squeeze-out"]["config"]["height"] = H

    # ---- 4. 分组与帧数
    stages["temporal-stack"]["config"]["group_size"] = FRAMES
    stages["generate-video"]["config"]["width"] = W
    stages["generate-video"]["config"]["height"] = H
    stages["generate-video"]["config"]["frames"] = FRAMES

    # ---- 5. 关内核竞速（SOP 12.6：新 stage 第一次跑先显式写 autotune:false）
    stages["generate-video"]["config"]["autotune"] = False
    stages["vae-decode"]["config"]["autotune"] = False

    # ---- 6. 输出
    stages["save-video"]["config"]["output_url"] = DST

    # ================= 自检断言（写文件之前） =================
    gv = stages["generate-video"]
    assert len(gv["iports"]) == 3, "generate-video 的 iports 总数应与模板一致(3)"
    assert gv["iports"][0]["src"] == "flashvsr-src-encoder", "iports[0] 应接源编码器"
    assert gv["iports"][1]["src"] == "", "iports[1] 应为空（FlashVSR 不读提示词）"
    assert gv["iports"][2]["src"] == "model-select", "iports[2] 应接模型"
    assert gv["config"]["width"] % 128 == 0 and gv["config"]["height"] % 128 == 0, \
        "输出宽高必须是 128 的倍数"
    assert gv["config"]["frames"] % 8 == 1, "帧数必须满足 8k+1"
    assert stages["temporal-stack"]["config"]["group_size"] == gv["config"]["frames"], \
        "group_size 应与 frames 一致（单组放完）"

    n_autotune = sum(
        1 for s in pipe["stages"]
        for k, v in s.get("config", {}).items()
        if k == "autotune" and v is False
    )
    assert n_autotune == 2, "autotune:false 应出现 2 处，实为 %d" % n_autotune

    sv = stages["save-video"]
    assert len(sv["iports"]) == 2, "save-video 必须接两路（视频 + 音频）"
    assert sv["iports"][0]["src"] == "rgb-to-video" and sv["iports"][1]["src"] == "audio-to-pcm", \
        "save-video 两路接错"

    if not os.path.isdir(MODEL_DIR):
        fail("模型目录不存在：%s" % MODEL_DIR)
    files = os.listdir(MODEL_DIR)
    saf = [x for x in files if x.endswith(".safetensors")]
    if len(saf) != 1:
        fail("模型目录应有且仅有 1 个 .safetensors，实为 %d：%s" % (len(saf), saf))
    for need in ("LQ_proj_in.ckpt", "posi_prompt.pth", "Wan2.1_VAE.pth", "TCDecoder.ckpt"):
        if need not in files:
            fail("缺少 companion 文件：%s" % need)

    # ================= 写盘 =================
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pipe, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("OK 写出 %s" % OUT)
    print("   模型      = %s" % MODEL_DIR)
    print("   输入      = %s (320×192)" % SRC)
    print("   输出      = %s (%d×%d, %d 帧)" % (DST, W, H, FRAMES))
    print("   自检      = 7 组全部通过")


if __name__ == "__main__":
    main()
