#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P15 · 可复现性基线（bit-for-bit）—— 流水线生成器

## 要回答的问题

第 3 轮实测：**同一个流水线、同一个 seed、连跑两次 → 0/22 帧逐位相同，整段 SSIM 仅 0.750072**。
当时归因为「已装 App (9db5dd7, 2026-11-01) 早于上游 bit-for-bit 修复 e6972ac (2026-11-06)」。

本轮读到上游 e6972ac 的**完整 commit 正文**后发现上一轮的归因**不完整**：

> "`autotune` false asks for a repeatable generation. A kernel tuner chooses between candidates
>  that agree to rounding but not to the bit, and it chooses by racing them, so two identical
>  runs could differ. With the key off each tuner times nothing, reads no answer the session
>  kept, and takes the route believed fastest on that GPU. ...
>  `ane_rows` is read as a fraction now, so a share below one no longer falls to nothing;
>  **pin it too and a generation repeats exactly.**"

即：**bit-for-bit 不是「升级到 e6972ac 之后自动生效」，而是一个需要显式打开的开关**：
  * `autotune: false` → 关闭内核竞速（计时器不再选内核，改走该 GPU 上「被认为最快」的固定路径）
  * `ane_rows` 显式钉死 → 防止 ANE/GPU 的负载分配按「实测速率」自动平衡（那也是计时行为）

而本机 P13 日志实测：`gemm autotune 4608` ms（首帧前向 4678 ms 中的 4608 ms = 98.5%）
→ **竞速确实是本机的主要开销来源**，关掉它还可能**更快**。

## 本实验设计（4 次生成，全部同一台机器、同一个 build、同一个 seed）

| 臂 | build | autotune | 说明 |
|---|---|---|---|
| A1 | 本地 33cda00 | 开（默认 true） | 对照组：本地 build 是否也有漂移 |
| A2 | 本地 33cda00 | 开（默认 true） | 与 A1 完全同配置，仅进程重启 |
| B1 | 本地 33cda00 | **关（false）** | generate-video + vae-decode + video-ref-encoder 三处 |
| B2 | 本地 33cda00 | **关（false）** | 与 B1 完全同配置，仅进程重启 |

其余**全部冻结**（与 P13 shift6 静态夹具逐项一致）：
参考图 / 提示词 / 帧数 22 / 1344×768 / 8 步 / seed 42 / 适配器 / shift 6.0 / i8_gemm。

这样 A1-A2 与 P13 的 App 两次运行构成「App vs 本地 build」的同条件对照，
B1-B2 则是「显式关闭竞速后是否逐位复现」的判决性实验。

## 判据

* **B1 vs B2**：`framemd5` 完全相同 **且** 音频轨 md5 完全相同 → bit-for-bit 复现成立；
  否则说明还有别的非确定性源。
* **A1 vs A2**：量化本地 build 的漂移基线（与第 3 轮 App 的 8.7%/18.4%/22.4% 对照）。
* 耗时对照：竞速开关是**加速**还是**减速**。
"""
import json
import os

WS = "/Users/minichen/AI-Models/vpipe-workspace"
OUT = os.path.join(WS, "pipelines")

# 与 P13 的静态夹具逐字一致（同一张参考图、同一段提示词、同一画布/帧数/步数/seed）
STATIC_PROMPT = (
    "References: @Image1 is the subject sheet. Make a new video of the subject from "
    "@Image1. The subject is completely motionless, sitting still on a wooden windowsill "
    "in warm late-afternoon sunlight, looking directly at the camera. The camera is "
    "locked off, absolutely static. The background is perfectly still. No blinking, no "
    "breathing, no movement of any kind, no camera movement, no zoom, no pan, no slow "
    "motion. Audio: silence. Normal real-time speed. No text, no captions, no logos."
)

REF_IMAGE = "refs/minimax-h3-reference-subject.jpg"
FRAMES = 22
W, H = 1344, 768
STEPS = 8
SEED = 42
SHIFT = 6.0


def build(pid, out_name, autotune_off):
    """autotune_off=True → 在 generate-video / vae-decode / video-ref-encoder 三处写 autotune=false。

    三个 stage 的选择依据（本地源码 grep）：
      stages/generate-video-stage.cc:119  声明 "autotune"
      stages/vae-decode-stage.cc:175       声明 "autotune"（并透传 accel flag）
      stages/video-ref-encoder-stage.cc:96 声明 "autotune"（ecfg.lm.autotune + vcfg.autotune）
    -> video-ref-encoder 一处同时管住文本编码器(LM)与视频条件器，缺它则文本侧仍可能竞速。
    """
    cfg = {"video_shift": SHIFT, "audio_shift": 3.0, "audio_seconds": 0.0,
           "lora": "lightx2v/Minimax-h3-Turbo-ref2va-8step-768p",
           "lora_scale": 1.0}

    ref_enc_cfg = {"frames": FRAMES, "reference_image_short_edge": 1024,
                   "unload_when_idle": "auto"}
    gen_cfg = {"height": H, "width": W, "frames": FRAMES, "fps": 24,
               "steps": STEPS, "seed": SEED, "i8_gemm": True,
               "unload_when_idle": "always"}
    vae_cfg = {}

    if autotune_off:
        gen_cfg["autotune"] = False
        vae_cfg["autotune"] = False
        ref_enc_cfg["autotune"] = False

    return {
        "id": pid,
        "stages": [
            {"id": "model-select", "type": "model-select", "iports": [],
             "config": {"hf_dir": "local/MiniMax-H3-Ref2VA-8bit"}},
            {"id": "text-prompt", "type": "text-prompt", "iports": [],
             "config": {"text": STATIC_PROMPT}},
            {"id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
             "config": cfg},
            {"id": "load-subject", "type": "load-image", "iports": [],
             "config": {"url": REF_IMAGE}},
            {"id": "size-subject", "type": "image-resample",
             "iports": [{"src": "load-subject", "oport": 0}],
             "config": {"width": 1024, "height": 1024, "fit": "stretch", "algorithm": "lanczos"}},
            {"id": "video-ref-encoder", "type": "video-ref-encoder",
             "iports": [{"src": "text-prompt", "oport": 0},
                        {"src": "model-select", "oport": 0},
                        {"src": "size-subject", "oport": 0}],
             "config": ref_enc_cfg},
            {"id": "generate-video", "type": "generate-video",
             # iport 列表必须与 P9-A 模板逐项一致（10 项），多一个空槽会挤走 model-config。
             "iports": [{"src": "video-ref-encoder", "oport": 0},
                        {"src": "", "oport": 0},
                        {"src": "model-select", "oport": 0},
                        {"src": "", "oport": 0},
                        {"src": "", "oport": 0},
                        {"src": "", "oport": 0},
                        {"src": "", "oport": 0},
                        {"src": "video-ref-encoder", "oport": 1},
                        {"src": "video-ref-encoder", "oport": 2},
                        {"src": "minimax-h3-model-config", "oport": 0}],
             "config": gen_cfg},
            {"id": "vae-decode", "type": "vae-decode",
             "iports": [{"src": "generate-video", "oport": 0},
                        {"src": "model-select", "oport": 0}], "config": vae_cfg},
            {"id": "audio-vae-decode", "type": "audio-vae-decode",
             "iports": [{"src": "generate-video", "oport": 1},
                        {"src": "model-select", "oport": 0}], "config": {}},
            {"id": "rgb-to-video", "type": "rgb-to-video",
             "iports": [{"src": "vae-decode", "oport": 0}],
             "config": {"fps": 24}},
            {"id": "save-video", "type": "save-video",
             "iports": [{"src": "rgb-to-video", "oport": 0},
                        {"src": "audio-vae-decode", "oport": 0}],
             "config": {"output_url": "out/" + out_name, "enable_video": True,
                        "enable_audio": True}},
        ],
        "subpipelines": [],
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    arms = (
        ("at1", False),   # A1：autotune 开（默认）
        ("at2", False),   # A2：与 A1 同配置，第二次进程
        ("af1", True),    # B1：autotune 关
        ("af2", True),    # B2：与 B1 同配置，第二次进程
    )
    for tag, off in arms:
        pid = "p15-repro-%s" % tag
        name = "%s.mp4" % pid
        p = os.path.join(OUT, pid + ".vpipeline")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(build(pid, name, off), f, ensure_ascii=False, indent=2)
        print("已生成 %s  (autotune=%s, frames=%d, %dx%d, steps=%d, seed=%d, shift=%.1f)"
              % (p, "OFF" if off else "ON(default)", FRAMES, W, H, STEPS, SEED, SHIFT))


if __name__ == "__main__":
    main()
