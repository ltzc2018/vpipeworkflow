#!/usr/bin/env python3
"""P3 · 768p / 长规格 —— 流水线生成器

生成一组 FL2VA 文生视频流水线，全部走 lightx2v 的 768p 适配器：
  p3-768p-shift6.vpipeline    1344x768 shift 6.0   ← 正确网格
  p3-768p-shift12.vpipeline   1344x768 shift 12.0  ← 错误网格（对照）
  p3-544p-ref.vpipeline        960x544  shift 12.0  ← 分辨率对照（544p 适配器）
  p3-768p-4step.vpipeline     1344x768 shift 6.0   ← 4 步 v1.2 对照

用法: python3 make_p3_pipelines.py [输出目录]
"""
import json
import os
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"

# 所有实验共用同一个提示词与 seed，唯一的变量是被测参数
PROMPT = (
    "Cinematic close-up of a tabby cat in a denim jacket sitting on a wooden windowsill "
    "in warm late-afternoon sunlight, slowly blinking and licking its paw, individual fur "
    "strands and the denim weave clearly resolved, shallow depth of field, camera very "
    "slowly pushes in. Audio: soft rhythmic purring, a faint breeze through the open "
    "window, distant birdsong outside. Normal real-time speed, no slow motion. "
    "No text, no captions, no logos."
)

SEED = 42
FPS = 24

# name -> (宽度, 高度, video_shift, adapter, 帧数, 输出文件)
VARIANTS = {
    "shift6":  (1344, 768, 6.0,  "lightx2v/Minimax-h3-Turbo-8step-768p-split", 124, "out/p3-768p-shift6.mp4"),
    "shift12": (1344, 768, 12.0, "lightx2v/Minimax-h3-Turbo-8step-768p-split", 124, "out/p3-768p-shift12.mp4"),
    "544p":    (960,  544, 12.0, "lightx2v/Minimax-h3-Turbo-8step",            124, "out/p3-544p-ref.mp4"),
    "4step":   (1344, 768, 6.0,  "lightx2v/Minimax-h3-Turbo-4step-768p-v1.2",  124, "out/p3-768p-4step.mp4"),
}


def build(name, w, h, shift, lora, frames, out_path):
    stages = [
        {"id": "model-select", "type": "model-select", "iports": [],
         "config": {"hf_dir": "local/MiniMax-H3-FL2VA-8bit"}},
        {"id": "text-prompt", "type": "text-prompt", "iports": [],
         "config": {"text": PROMPT}},
        {"id": "diffusion-conditioner", "type": "diffusion-conditioner",
         "iports": [{"src": "text-prompt", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "model-select", "oport": 0}],
         "config": {"unload_when_idle": "always"}},
        {"id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
         "config": {"video_shift": shift, "audio_shift": 3.0, "condition_timestep": 1.0,
                    "audio_seconds": 0.0, "lora": lora, "lora_scale": 1.0}},
        {"id": "generate-video", "type": "generate-video",
         # 端口布局照抄官方 FL2VA 流水线：空端口的位置不能动
         "iports": [{"src": "diffusion-conditioner", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "model-select", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "", "oport": 0},
                    {"src": "minimax-h3-model-config", "oport": 0}],
         "config": {"height": h, "width": w, "frames": frames, "fps": FPS,
                    "steps": 8, "seed": SEED, "i8_gemm": True, "unload_when_idle": "always"}},
        {"id": "vae-decode", "type": "vae-decode",
         "iports": [{"src": "generate-video", "oport": 0}, {"src": "model-select", "oport": 0}],
         "config": {}},
        {"id": "audio-vae-decode", "type": "audio-vae-decode",
         "iports": [{"src": "generate-video", "oport": 1}, {"src": "model-select", "oport": 0}],
         "config": {}},
        {"id": "rgb-to-video", "type": "rgb-to-video",
         "iports": [{"src": "vae-decode", "oport": 0}], "config": {"fps": FPS}},
        {"id": "save-video", "type": "save-video",
         "iports": [{"src": "rgb-to-video", "oport": 0}, {"src": "audio-vae-decode", "oport": 0}],
         "config": {"output_url": out_path, "enable_video": True, "enable_audio": True}},
    ]
    pipeline = {"id": f"p3-768p-{name}", "stages": stages, "subpipelines": []}
    return pipeline


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WS, "pipelines")
    os.makedirs(outdir, exist_ok=True)
    for name, (w, h, shift, lora, frames, out) in VARIANTS.items():
        p = build(name, w, h, shift, lora, frames, out)
        path = os.path.join(outdir, f"p3-768p-{name}.vpipeline")
        with open(path, "w") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)
        print(f"写出 {path}  {w}x{h} shift={shift} frames={frames} lora={lora}")


if __name__ == "__main__":
    main()
