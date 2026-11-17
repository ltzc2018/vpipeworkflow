#!/usr/bin/env python3
"""P1 多参考组合 —— 生成三条「端口路线」Ref2VA 流水线

三组共用同一套采样参数（832x480 / 124 帧 / seed 42 / Pika H3 Flex ref2va / 6 步），
唯一的变量是「喂了几条参考、分别是什么角色」：

  A 组 p1-a-img-only        : 1 张图（橘猫写实照）           -> 编码器 slot 1
  B 组 p1-b-img-style       : 2 张图（橘猫 + 熊猫水彩）       -> slot 1,2
  C 组 p1-c-img-style-motion: 2 张图 + 1 段动作视频 + 其音轨 -> slot 1,2,3,4

端口路线（官方 minimax-h3-reference-to-video.vpipeline 的写法）：
  图   : load-image -> image-resample -> video-ref-encoder.iport2+
  视频 : load-video -> video-to-rgb -> image-resample -> temporal-stack -> iport
  音频 : load-video(oport1) -> audio-to-pcm(32000, stereo) -> temporal-stack -> iport

attach_audio 填的是「音频那条参考自己的 slot 号」：音频必须排在它要归属的片段后面。
"""
import json
import os
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"

CAT = "refs/minimax-h3-reference-subject.jpg"        # 写实橘猫（穿牛仔外套）
PANDA = "refs/klein-multi-ref-panda.jpg"             # 水彩手绘熊猫（风格参考）
PANDA_CROP = "refs/klein-multi-ref-panda-crop.jpg"   # 同一只熊猫的特写裁剪（第 3 张图）
MOTION = "refs/motion-pan-right-124f.mp4"            # 可测量的水平摇摄动作参考

BASE_ACTION = ("The subject sits on a wooden windowsill in warm late-afternoon sunlight, "
               "looks directly at the camera, blinks slowly and gently licks its paw")
AUDIO_LINE = ("Audio: soft rhythmic purring, a faint breeze through the open window, "
              "distant birdsong outside. Normal real-time speed, no slow motion. "
              "No text, no captions, no logos.")

PROMPTS = {
    "A": ("References: @Image1 is the subject sheet. Make a new video of the subject from @Image1. "
          f"{BASE_ACTION}; the camera pushes in very slowly. {AUDIO_LINE}"),
    "B": ("References: @Image1 is the subject sheet, @Image2 is the style reference. "
          "Make a new video of the subject from @Image1, rendered in the artistic style of @Image2. "
          f"{BASE_ACTION}; the camera pushes in very slowly. {AUDIO_LINE}"),
    "C": ("References: @Image1 is the subject sheet, @Image2 is the style reference, "
          "@Video1 is the motion reference. Make a new video of the subject from @Image1, "
          "rendered in the artistic style of @Image2, with the camera movement and motion "
          f"timing of @Video1. {BASE_ACTION}. {AUDIO_LINE}"),
    "D": ("References: @Image1 is the subject sheet, @Image2 and @Image3 are style references "
          "showing the same artwork, @Video1 is the motion reference. Make a new video of the "
          "subject from @Image1, rendered in the artistic style of @Image2 and @Image3, with the "
          f"camera movement and motion timing of @Video1. {BASE_ACTION}. {AUDIO_LINE}"),
}

FRAMES = 124
WIDTH, HEIGHT = 832, 480
SEED = 42


def model_select():
    return {"id": "model-select", "type": "model-select", "iports": [],
            "config": {"hf_dir": "local/MiniMax-H3-Ref2VA-8bit"}}


def text_prompt(text):
    return {"id": "text-prompt", "type": "text-prompt", "iports": [], "config": {"text": text}}


def model_config():
    return {"id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
            "config": {"video_shift": 12.0, "audio_shift": 3.0, "audio_seconds": 0.0,
                       "lora": "Pika-Labs/Pika-H3-Flex-ref2va", "lora_scale": 1.0}}


def load_image(stage_id, url):
    return {"id": stage_id, "type": "load-image", "iports": [], "config": {"url": url}}


def resample(stage_id, src, w, h, fit="stretch"):
    return {"id": stage_id, "type": "image-resample",
            "iports": [{"src": src, "oport": 0}],
            "config": {"width": w, "height": h, "fit": fit, "algorithm": "lanczos"}}


def build(group, out_path):
    stem = os.path.basename(out_path).replace(".vpipeline", "")
    stages = [model_select(), text_prompt(PROMPTS[group]), model_config()]
    ref_slots = []          # 编码器 iport 列表：2,3,4,5...
    encoder_cfg = {
        "frames": FRAMES,
        "reference_image_short_edge": 1024,
        "unload_when_idle": "auto",
    }

    # --- 参考 1：主体图（写实橘猫）---
    stages.append(load_image("load-subject", CAT))
    stages.append(resample("size-subject", "load-subject", 1024, 1024))
    ref_slots.append("size-subject")

    # --- 参考 2：风格图（水彩熊猫），B/C/D 组有 ---
    if group in ("B", "C", "D"):
        stages.append(load_image("load-style", PANDA))
        stages.append(resample("size-style", "load-style", 1024, 1024))
        ref_slots.append("size-style")

    # --- 参考 3：同一张风格图的特写裁剪，只有 D 组有 ---
    if group == "D":
        stages.append(load_image("load-style2", PANDA_CROP))
        stages.append(resample("size-style2", "load-style2", 1024, 1024))
        ref_slots.append("size-style2")

    # --- 参考 3(+4)：动作视频 + 其音轨，C/D 组有 ---
    if group in ("C", "D"):
        stages.append({"id": "load-motion", "type": "load-video", "iports": [],
                       "config": {"input_url": MOTION}})
        stages.append({"id": "motion-frames", "type": "video-to-rgb",
                       "iports": [{"src": "load-motion", "oport": 0}],
                       "config": {"output_dtype": "u8"}})
        # 参考视频保持在输出画布尺寸上（= reference_video_short_edge: 0 的语义），
        # 参考行数不会翻倍
        stages.append(resample("size-motion", "motion-frames", WIDTH, HEIGHT))
        stages.append({"id": "stack-motion", "type": "temporal-stack",
                       "iports": [{"src": "size-motion", "oport": 0}],
                       "config": {"mode": "video", "group_size": 0, "max_mb": 384}})
        stages.append({"id": "motion-pcm", "type": "audio-to-pcm",
                       "iports": [{"src": "load-motion", "oport": 1}],
                       "config": {"output_sample_rate": 32000, "channels": 2,
                                  "chunk_duration_s": 30.0, "max_chunk_duration_s": 60.0}})
        stages.append({"id": "stack-pcm", "type": "temporal-stack",
                       "iports": [{"src": "motion-pcm", "oport": 0}],
                       "config": {"mode": "audio", "group_size": 0}})
        ref_slots.append("stack-motion")
        ref_slots.append("stack-pcm")
        # attach_audio 填「音频那条参考自己的 slot 号」（1 起算）= 4
        encoder_cfg["attach_audio"] = [len(ref_slots)]

    # --- video-ref-encoder ---
    enc_iports = [{"src": "text-prompt", "oport": 0}, {"src": "model-select", "oport": 0}]
    for i, slot in enumerate(ref_slots):
        enc_iports.append({"src": slot, "oport": 0})
    stages.append({"id": "video-ref-encoder", "type": "video-ref-encoder",
                   "iports": enc_iports, "config": encoder_cfg})

    # --- generate-video ---
    stages.append({
        "id": "generate-video", "type": "generate-video",
        "iports": [{"src": "video-ref-encoder", "oport": 0}, {"src": "", "oport": 0},
                   {"src": "model-select", "oport": 0}, {"src": "", "oport": 0},
                   {"src": "", "oport": 0}, {"src": "", "oport": 0}, {"src": "", "oport": 0},
                   {"src": "video-ref-encoder", "oport": 1},
                   {"src": "video-ref-encoder", "oport": 2},
                   {"src": "minimax-h3-model-config", "oport": 0}],
        "config": {"height": HEIGHT, "width": WIDTH, "frames": FRAMES, "fps": 24,
                   "steps": 6, "seed": SEED, "i8_gemm": True, "unload_when_idle": "always"}})

    stages.append({"id": "vae-decode", "type": "vae-decode",
                   "iports": [{"src": "generate-video", "oport": 0},
                              {"src": "model-select", "oport": 0}], "config": {}})
    stages.append({"id": "audio-vae-decode", "type": "audio-vae-decode",
                   "iports": [{"src": "generate-video", "oport": 1},
                              {"src": "model-select", "oport": 0}], "config": {}})
    stages.append({"id": "rgb-to-video", "type": "rgb-to-video",
                   "iports": [{"src": "vae-decode", "oport": 0}], "config": {"fps": 24}})
    out_name = f"out/{stem}.mp4"
    stages.append({"id": "save-video", "type": "save-video",
                   "iports": [{"src": "rgb-to-video", "oport": 0},
                              {"src": "audio-vae-decode", "oport": 0}],
                   "config": {"output_url": out_name, "enable_video": True, "enable_audio": True}})

    pipeline = {"id": stem, "stages": stages, "subpipelines": []}
    with open(out_path, "w") as f:
        json.dump(pipeline, f, indent=2, ensure_ascii=False)
    print(f"写出 {out_path}  (参考 slot: {ref_slots}, attach_audio={encoder_cfg.get('attach_audio')})")


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WS, "pipelines")
    os.makedirs(outdir, exist_ok=True)
    for group in ("A", "B", "C", "D"):
        name = f"p1-{group.lower()}-multi-ref"
        build(group, os.path.join(outdir, f"{name}.vpipeline"))


if __name__ == "__main__":
    main()
