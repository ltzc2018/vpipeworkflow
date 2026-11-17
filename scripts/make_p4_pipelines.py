#!/usr/bin/env python3
"""P4 —— 为 i2va（首帧锚定）链路生成接入 TAE-H3 实时预览的流水线。

三支：
  A  pika-i2va-preview-fast  首帧锚定 + TAE 预览   512x288 / 39 帧 / 6 步 / seed 42
  D  pika-t2v-preview-fast  纯文生  + TAE 预览     512x288 / 39 帧 / 6 步 / seed 42（对照：非锚定路径）
  C  pika-i2va-preview-prod 首帧锚定 + TAE 预览   832x480 / 124 帧 / 6 步 / seed 42（生产规格，
                                                         与已有的 out/pika-i2va-shop.mp4 同参同 seed）
"""
import json
import os

WS = "/Users/minichen/AI-Models/vpipe-workspace"
OUT = os.path.join(WS, "pipelines")

TAE = "/Users/minichen/AI-Models/vpipe-workspace/models/madebyollin/taehv/taeh3.safetensors"
REF = "/Users/minichen/AI-Models/vpipe-workspace/refs/minimax-h3-reference-subject.jpg"

PROMPT_ANCHORED = (
    "Starting on the first frame: the subject stays seated on the wooden "
    "windowsill, slowly turns its head toward the camera and blinks, its fur "
    "rippling gently in the warm breeze; the camera pushes in very slowly. "
    "Natural motion at real-time speed. Sound: soft rhythmic purring, a faint "
    "breeze through the open window, distant birdsong. No text, no captions, "
    "no logos."
)
PROMPT_PLAIN = (
    "A cat stays seated on the wooden windowsill, slowly turns its head toward "
    "the camera and blinks, its fur rippling gently in the warm breeze; the "
    "camera pushes in very slowly. Natural motion at real-time speed. Sound: "
    "soft rhythmic purring, a faint breeze through the open window, distant "
    "birdsong. No text, no captions, no logos."
)


def base(pipeline_id, out_name, width, height, frames, steps, seed,
         anchored, preview_every, preview_frames):
    stages = []

    stages.append({
        "id": "model-select",
        "type": "model-select",
        "iports": [],
        "config": {"hf_dir": "local/MiniMax-H3-FL2VA-8bit"},
    })

    if anchored:
        stages.append({
            "id": "load-image",
            "type": "load-image",
            "iports": [],
            "config": {"url": [REF]},
        })
        stages.append({
            "id": "first-frame",
            "type": "image-resample",
            "iports": [{"src": "load-image", "oport": 0}],
            "config": {"width": width, "height": height,
                       "fit": "crop", "algorithm": "lanczos"},
        })
        stages.append({
            "id": "vae-encode-first",
            "type": "vae-encode",
            "iports": [{"src": "first-frame", "oport": 0},
                       {"src": "model-select", "oport": 0}],
            "config": {"unload_when_idle": "always"},
        })

    stages.append({
        "id": "text-prompt",
        "type": "text-prompt",
        "iports": [],
        "config": {"text": PROMPT_ANCHORED if anchored else PROMPT_PLAIN},
    })

    cond_iports = [{"src": "text-prompt", "oport": 0},
                   {"src": "", "oport": 0},
                   {"src": "model-select", "oport": 0}]
    if anchored:
        cond_iports.append({"src": "first-frame", "oport": 0})
    stages.append({
        "id": "diffusion-conditioner",
        "type": "diffusion-conditioner",
        "iports": cond_iports,
        "config": {"unload_when_idle": "always"},
    })

    stages.append({
        "id": "minimax-h3-model-config",
        "type": "minimax-h3-model-config",
        "iports": [],
        "config": {
            "video_shift": 12.0,
            "audio_shift": 3.0,
            "audio_seconds": 0.0,
            "lora": "Pika-Labs/Pika-H3-Flex-fl2va",
            "lora_scale": 1.0,
            # --- 实时预览三件套（挂在 model-config 上，generate-video 从它的 beat 里读）---
            "preview_vae": TAE,
            "preview_every": preview_every,
            "preview_max_edge": 512,
            "preview_frames": preview_frames,
        },
    })

    gen_iports = [{"src": "diffusion-conditioner", "oport": 0},
                  {"src": "", "oport": 0},
                  {"src": "model-select", "oport": 0},
                  {"src": "", "oport": 0},
                  {"src": "", "oport": 0}]
    gen_iports.append({"src": "vae-encode-first", "oport": 0} if anchored
                      else {"src": "", "oport": 0})
    gen_iports += [{"src": "", "oport": 0}] * 3
    gen_iports.append({"src": "minimax-h3-model-config", "oport": 0})
    stages.append({
        "id": "generate-video",
        "type": "generate-video",
        "iports": gen_iports,
        "config": {
            "height": height, "width": width, "frames": frames, "fps": 24,
            "steps": steps, "seed": seed, "i8_gemm": True,
            "unload_when_idle": "always",
        },
    })

    # 实时预览：generate-video 的 preview oport（index 2）→ preview stage
    stages.append({
        "id": "preview",
        "type": "preview",
        "iports": [{"src": "generate-video", "oport": 2}],
        "config": {"title": "MiniMax-H3 i2va denoise preview"},
    })

    stages.append({
        "id": "vae-decode",
        "type": "vae-decode",
        "iports": [{"src": "generate-video", "oport": 0},
                   {"src": "model-select", "oport": 0}],
        "config": {},
    })
    stages.append({
        "id": "audio-vae-decode",
        "type": "audio-vae-decode",
        "iports": [{"src": "generate-video", "oport": 1},
                   {"src": "model-select", "oport": 0}],
        "config": {},
    })
    stages.append({
        "id": "rgb-to-video",
        "type": "rgb-to-video",
        "iports": [{"src": "vae-decode", "oport": 0}],
        "config": {"fps": 24},
    })
    stages.append({
        "id": "save-video",
        "type": "save-video",
        "iports": [{"src": "rgb-to-video", "oport": 0},
                   {"src": "audio-vae-decode", "oport": 0}],
        "config": {
            "output_url": os.path.join(WS, "out", out_name),
            "enable_video": True,
            "enable_audio": True,
        },
    })

    return {"id": pipeline_id, "stages": stages, "subpipelines": []}


SPECS = [
    ("pika-i2va-preview-fast", "p4-i2va-preview-fast.mp4", 512, 288, 39, 6, 42,
     True, 1, 39),
    ("pika-t2v-preview-fast", "p4-t2v-preview-fast.mp4", 512, 288, 39, 6, 42,
     False, 1, 39),
    ("pika-i2va-preview-prod", "p4-i2va-preview-prod.mp4", 832, 480, 124, 6, 42,
     True, 1, 124),
]

if __name__ == "__main__":
    for spec in SPECS:
        pid = spec[0]
        doc = base(*spec)
        path = os.path.join(OUT, pid + ".vpipeline")
        with open(path, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        print("wrote", path)
