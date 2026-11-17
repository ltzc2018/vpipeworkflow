#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P18 · `dmd` 采样器对纹理沸腾（上游 issue #55）的作用 —— 流水线生成器

## 要回答的问题

第 3 轮续作已经确立了两条硬知识：

1. `autotune: false`（generate-video + vae-decode + video-ref-encoder 三处）→ **bit-for-bit 可复现**
   （SSIM 1.000000 / PSNR inf），且**快 2.2%**。
   ⇒ 本实验的漂移噪声被压到 0，**任何组间差异都可直接归因**。
2. 上游 issue #55 的机制在 H3 里有**内置版**：`diffusion-sampler-select` 的 `dmd` 方法
   （`stages/diffusion-sampler-select-stage.h:26` 的枚举；`generate-video` 的 **iport 3 = sampler**）。

   上游 `stages/generate-video-stage.cc:587-596` 的 iport 文档原文：
   > "minimax-h3 carries its own sampler and maps the spec's method onto it:
   >  **euler** (its default), **dmd (x0 at each sigma, then fresh noise to the next)**
   >  and res_multistep, one forward a step each; any other method is warned about
   >  and its default runs."

   即 `dmd` = **每步重注噪**：`x0 = x + σ·v` → `(1−σ')·x0 + σ'·n`，
   噪声取自 clip 自己的 seed（`generate-video-stage.cc:5279-5281`：`req.seed = _h3_sampler.seed != 0 ? _h3_sampler.seed : _seed;`）
   → **仍然确定性**（本实验的 B2 臂专门验证这一点）。

**零下载**：`dmd` 是 vpipe 内置的采样器选择，不需要任何新模型、不需要新适配器。

## 假设

纹理沸腾 = 逐帧重新渲染的高频纹理噪声（#55 的 HF jitter 指标）。
`dmd` 每步重注噪 → 它**既可能**加剧沸腾（每步都往里加随机扰动），
**也可能**抑制沸腾（重注噪让模型每步都从新的 x0 出发，避免在一个噪声球里打转）。

## 实验设计（3 臂，全部同一台机器、同一个 build、同一个 seed、竞速关闭）

| 臂 | sampler 端口 | method | 作用 |
|---|---|---|---|
| **A** | **接上** `diffusion-sampler-select` | `euler` | ★ **接线对照**：证明「接上 sampler 端口且 method=euler」与「不接端口」逐位相同 ⇒ 端口本身是透明的，B 臂的差异只能来自 `dmd` 本身 |
| **B** | 接上 | `dmd` | 处理组：每步重注噪 |
| **B2** | 接上 | `dmd` | **确定性验证**：`dmd` 的重注噪路径是否也 bit-for-bit 复现（第 3 轮只证过 euler 路径） |

A 臂可与第 3 轮续作的 `p15-repro-af1.mp4`（**不接** sampler 端口、method 缺省 = euler）
做**跨轮次**逐位比对 —— 一举两得：既验证接线透明性，又验证跨轮次可复现。

其余**全部冻结**（与 P13 静态夹具 / P15 B1 臂逐字一致）：
参考图 `refs/minimax-h3-reference-subject.jpg` / 同一段静止提示词 / 帧数 22 / 1344×768 /
8 步 / seed 42 / `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` / shift 6.0-3.0 /
`i8_gemm: true` / `reference_image_short_edge: 1024` / `autotune: false`（三处）。

## 判据（全部量化，口径写明）

* `framemd5`（**仅视频流**，必须 `-map 0:v`）+ 音频轨 md5 → 逐位判据
* SSIM / PSNR（`p13_hf_jitter.py` 的 pairwise 首帧 + 整段口径）
* #55 三指标：HF jitter / frame diff / sharpness（384 宽灰度解码域）
* 本实验室补充指标：`static_hf_jitter`（只在时序静止像素上统计）
"""
import json
import os

WS = "/Users/minichen/AI-Models/vpipe-workspace"
OUT = os.path.join(WS, "pipelines")

# 与 P13 静态夹具 / P15 B1 臂逐字一致
STATIC_PROMPT = (
    "References: @Image1 is the subject sheet. Make a new video of the subject from "
    "@Image1. The subject is completely motionless, sitting still on a wooden windowsill "
    "in warm late-afternoon sunlight, looking directly at the camera. The camera is "
    "locked off, absolutely static. The background is perfectly still. No blinking, no "
    "breathing, no movement of any kind, no camera movement, no zoom, no pan, no slow "
    "motion. Audio: silence. Normal real-time speed. No text, no captions, no logos."
)

REF_IMAGE = "refs/minimax-h3-reference-subject.jpg"
MODEL_DIR = "local/MiniMax-H3-Ref2VA-8bit"
ADAPTER = "lightx2v/Minimax-h3-Turbo-ref2va-8step-768p"


def stage(sid, stype, iports, config):
    return {"id": sid, "type": stype, "iports": iports, "config": config}


def edge(src, oport):
    return {"src": src, "oport": oport}


def build(pipeline_id, out_name, method):
    """method=None 表示**不接** sampler 端口（基线）；否则接上并写 method。"""
    stages = [
        stage("model-select", "model-select", [], {"hf_dir": MODEL_DIR}),
        stage("text-prompt", "text-prompt", [], {"text": STATIC_PROMPT}),
        stage(
            "minimax-h3-model-config",
            "minimax-h3-model-config",
            [],
            {
                "video_shift": 6.0,
                "audio_shift": 3.0,
                "audio_seconds": 0.0,
                "lora": ADAPTER,
                "lora_scale": 1.0,
            },
        ),
        stage("load-subject", "load-image", [], {"url": REF_IMAGE}),
        stage(
            "size-subject",
            "image-resample",
            [edge("load-subject", 0)],
            {"width": 1024, "height": 1024, "fit": "stretch", "algorithm": "lanczos"},
        ),
        stage(
            "video-ref-encoder",
            "video-ref-encoder",
            [
                edge("text-prompt", 0),
                edge("model-select", 0),
                edge("size-subject", 0),
            ],
            {
                "frames": 22,
                "reference_image_short_edge": 1024,
                "unload_when_idle": "auto",
                "autotune": False,
            },
        ),
    ]

    if method is not None:
        # ★ iport 3 = sampler（上游 kIports 顺序：0 conditioning / 1 neg_conditioning /
        #   2 model / **3 sampler** / 4 scheduler / 5 ref_latent0 / 6 ref_latent1 /
        #   7 ref_video_rows / 8 ref_audio_rows / 9 model_config）
        stages.append(
            stage(
                "sampler-select",
                "diffusion-sampler-select",
                [],
                {"method": method},
            )
        )

    # generate-video 的 iports 列表照抄 P13/P15 模板（只可能改第 3 位）
    gv_iports = [
        edge("video-ref-encoder", 0),   # 0 conditioning
        edge("", 0),                    # 1 neg_conditioning
        edge("model-select", 0),        # 2 model
        edge("sampler-select", 0) if method is not None else edge("", 0),  # 3 sampler
        edge("", 0),                    # 4 scheduler
        edge("", 0),                    # 5 ref_latent0
        edge("", 0),                    # 6 ref_latent1
        edge("video-ref-encoder", 1),   # 7 ref_video_rows
        edge("video-ref-encoder", 2),   # 8 ref_audio_rows
        edge("minimax-h3-model-config", 0),  # 9 model_config
    ]

    stages += [
        stage(
            "generate-video",
            "generate-video",
            gv_iports,
            {
                "height": 768,
                "width": 1344,
                "frames": 22,
                "fps": 24,
                "steps": 8,
                "seed": 42,
                "i8_gemm": True,
                "unload_when_idle": "always",
                "autotune": False,
            },
        ),
        stage(
            "vae-decode",
            "vae-decode",
            [edge("generate-video", 0), edge("model-select", 0)],
            {"autotune": False},
        ),
        stage(
            "audio-vae-decode",
            "audio-vae-decode",
            [edge("generate-video", 1), edge("model-select", 0)],
            {},
        ),
        stage("rgb-to-video", "rgb-to-video", [edge("vae-decode", 0)], {"fps": 24}),
        stage(
            "save-video",
            "save-video",
            [edge("rgb-to-video", 0), edge("audio-vae-decode", 0)],
            {
                "output_url": "out/%s" % out_name,
                "enable_video": True,
                "enable_audio": True,
            },
        ),
    ]

    return {"id": pipeline_id, "stages": stages, "subpipelines": []}


ARMS = [
    # (pipeline_id, 输出文件名, method, 说明)
    ("p18-euler", "p18-euler.mp4", "euler", "接线对照：接上 sampler 端口 + method=euler"),
    ("p18-dmd", "p18-dmd.mp4", "dmd", "处理组：dmd（每步重注噪）"),
    ("p18-dmd2", "p18-dmd2.mp4", "dmd", "确定性验证：dmd 再跑一次"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for pid, out_name, method, desc in ARMS:
        doc = build(pid, out_name, method)
        path = os.path.join(OUT, pid + ".vpipeline")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        print("[OK] %-28s -> %s   (%s)" % (pid + ".vpipeline", path, desc))

    # 自检：A 臂与 B 臂的 generate-video iport 数量必须一致（上游坑：多一个空 iport 会挤走 model_config）
    for pid, _, _, _ in ARMS:
        doc = json.load(open(os.path.join(OUT, pid + ".vpipeline"), encoding="utf-8"))
        gv = [s for s in doc["stages"] if s["id"] == "generate-video"][0]
        assert len(gv["iports"]) == 10, "%s iport 数不是 10" % pid
        assert gv["iports"][9]["src"] == "minimax-h3-model-config", "%s model_config 位置错" % pid
        if pid == "p18-euler":
            assert gv["iports"][3]["src"] == "sampler-select", "A 臂 sampler 接线错"
    print("[自检] 3 臂的 generate-video iport 均为 10 个，model_config 仍在第 9 位。")


if __name__ == "__main__":
    main()
