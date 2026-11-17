#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P13 · 生成「静态场景」Ref2VA 768p 流水线（纹理沸腾复现用）

设计依据上游 issue #55 的夹具方法学：
  「The reference is a 22-frame clip made from one still image, so it is mathematically
    static. Measured on the reference itself: HF jitter 0.0000 ... Every bit of jitter
    in the output is therefore model-generated.」

因此本实验的要点：
  1. 用同一张静图作参考（参考本身 HF jitter ≈ 0）
  2. 提示词强制「完全静止 / 锁定机位 / 无运动」→ 场景里的高频时序变化只能来自模型重绘
  3. 帧数取 22 = 17×1+5，与 #55 夹具完全一致 → 数值可与上游直接对表
  4. shift 6.0 与 12.0 两支：参考图、提示词、seed、步数、画布全部相同，
     **只有 video_shift 不同** —— 这同时给出一个「场景受控」的 shift 对照
     （P9 的 shift 对照因为换场景而存在混淆项，见报告 18.3.3）
"""
import json
import os

WS = "/Users/minichen/AI-Models/vpipe-workspace"
OUT = os.path.join(WS, "pipelines")

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


def build(pid, shift, out_name, sigmas=None):
    cfg = {"video_shift": shift, "audio_shift": 3.0, "audio_seconds": 0.0,
           "lora": "lightx2v/Minimax-h3-Turbo-ref2va-8step-768p",
           "lora_scale": 1.0}
    if sigmas:
        # 上游 minimax-h3-model-config 的 `sigmas` 字段：直接给「实际跑的 sigma 网格」，
        # 取代 steps+shift 生成的网格。例串正是 ComfyUI er_sde 的 sigma 表
        # （与上游 issue #55 里贴的 ComfyUI 那一行逐位相同）。
        cfg["sigmas"] = sigmas
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
             "config": {"frames": FRAMES, "reference_image_short_edge": 1024,
                        "unload_when_idle": "auto"}},
            {"id": "generate-video", "type": "generate-video",
             # iport 列表必须与 P9-A 模板逐项一致（10 项）：多一个空槽就会把
             # model-config 挤到 iport10，报 payload type mismatch。
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
             "config": {"height": H, "width": W, "frames": FRAMES, "fps": 24,
                        "steps": STEPS, "seed": SEED, "i8_gemm": True,
                        "unload_when_idle": "always"}},
            {"id": "vae-decode", "type": "vae-decode",
             "iports": [{"src": "generate-video", "oport": 0},
                        {"src": "model-select", "oport": 0}], "config": {}},
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
    made = []
    # ComfyUI er_sde 的 sigma 表（上游 issue #55 正文给出，与上游文档 MINIMAX-H3.md 的
    # `sigmas` 示例逐位相同）：9 个 sigma → 8 次前向。
    ER_SDE = "1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"
    arms = (
        ("6", 6.0, None),            # 上游文档指定的 Ref2VA 768p shift
        ("12", 12.0, None),           # 同一适配器但换网格（对照）
        ("er-sde", 6.0, ER_SDE),     # 用 ComfyUI er_sde 的 sigma 网格
    )
    for tag, shift, sig in arms:
        pid = "p13-static-shift%s" % tag
        name = "%s.mp4" % pid
        p = os.path.join(OUT, pid + ".vpipeline")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(build(pid, shift, name, sig), f, ensure_ascii=False, indent=2)
        made.append((p, name))
        print("已生成 %s  (video_shift=%.1f, sigmas=%s, frames=%d, %dx%d, steps=%d, seed=%d)"
              % (p, shift, (sig or "默认网格"), FRAMES, W, H, STEPS, SEED))
    return made


if __name__ == "__main__":
    main()
