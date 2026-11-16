#!/usr/bin/env python3
"""P9 · Ref2VA @ 768p 多参考组合 —— 生成三条 768p Ref2VA 流水线

背景（第 9 轮）：
  P1 证明了「多参考组合」在 480p / Pika 适配器上成立（端口路线 ≡ 文件列表路线，位级一致）；
  P3 证明了「768p」在 FL2VA 上可行，且 shift 6.0 必需但完全静默。
  但 768p 适配器家族里**唯一没有跑过的那个**是 Ref2VA 专用适配器：
      lightx2v/Minimax-h3-Turbo-ref2va-8step-768p
  （权重早在第 8 轮就已下载并注册进 LMDB 注册表，但从未被任何流水线引用过。）

本轮三组共用同一套采样参数，唯一变量逐组递进：

  A 组 p9-ref2va-768p-a          : 1 张图                 , video_shift 6.0
  B 组 p9-ref2va-768p-b-shift12  : 1 张图（同 A 提示词）  , video_shift 12.0   ← 成对检验 shift 规则
  C 组 p9-ref2va-768p-c-multiref : 1 张图 + 1 段动作视频 + 其音轨, video_shift 6.0 ← 多参考是否仍然成立

  A vs B → 只差一个 shift 数字，检验「Ref2VA 768p 的 shift 规则」是否与 FL2VA 一样（6.0）
  A vs C → 只多一条视频参考，检验「多参考在 768p 下是否仍然成立、运镜锁是否还有效」

端口路线（官方 minimax-h3-reference-to-video.vpipeline 的写法）：
  图   : load-image -> image-resample -> video-ref-encoder.iport2+
  视频 : load-video -> video-to-rgb -> image-resample(1344x768) -> temporal-stack -> iport
  音频 : load-video(oport1) -> audio-to-pcm(32000, stereo) -> temporal-stack -> iport

attach_audio 填的是「音频那条参考自己的 slot 号」（1 起算，P1 第 6 坑）：
  C 组喂进去 3 条（img=1, video=2, audio=3）→ attach_audio: [3]
"""
import json
import os

WS = "/Users/minichen/AI-Models/vpipe-workspace"

CAT = "refs/minimax-h3-reference-subject.jpg"   # 写实橘猫（穿牛仔外套）→ 主体身份参考
MOTION = "refs/motion-pan-right-124f.mp4"       # 可测量的水平摇摄动作参考（含音轨）

BASE_ACTION = ("The subject sits on a wooden windowsill in warm late-afternoon sunlight, "
               "looks directly at the camera, blinks slowly and gently licks its paw")
AUDIO_LINE = ("Audio: soft rhythmic purring, a faint breeze through the open window, "
              "distant birdsong outside. Normal real-time speed, no slow motion. "
              "No text, no captions, no logos.")

PROMPTS = {
    "A": ("References: @Image1 is the subject sheet. Make a new video of the subject from @Image1. "
          f"{BASE_ACTION}; the camera pushes in very slowly. {AUDIO_LINE}"),
    "C": ("References: @Image1 is the subject sheet, @Video1 is the motion reference. "
          "Make a new video of the subject from @Image1, with the camera movement and motion "
          f"timing of @Video1. {BASE_ACTION}. {AUDIO_LINE}"),
}

FRAMES = 124
WIDTH, HEIGHT = 1344, 768
SEED = 42
STEPS = 8
LORA = "lightx2v/Minimax-h3-Turbo-ref2va-8step-768p"


def model_select():
    return {"id": "model-select", "type": "model-select", "iports": [],
            "config": {"hf_dir": "local/MiniMax-H3-Ref2VA-8bit"}}


def text_prompt(text):
    return {"id": "text-prompt", "type": "text-prompt", "iports": [], "config": {"text": text}}


def model_config(shift):
    return {"id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
            "config": {"video_shift": shift, "audio_shift": 3.0, "audio_seconds": 0.0,
                       "lora": LORA, "lora_scale": 1.0}}


def load_image(stage_id, url):
    return {"id": stage_id, "type": "load-image", "iports": [], "config": {"url": url}}


def resample(stage_id, src, w, h):
    return {"id": stage_id, "type": "image-resample", "iports": [{"src": src, "oport": 0}],
            "config": {"width": w, "height": h, "fit": "stretch", "algorithm": "lanczos"}}


def ref_encoder(img_ports, video_port=None, audio_port=None, attach_audio=None):
    """编码器 iport 分配：0=提示词，1=model-select，2..7=参考 1..6。
    没用的参考端口干脆不要接 —— 一个「空」端口会重编号后面的所有参考（P1 第 2 坑）。"""
    iports = [{"src": "text-prompt", "oport": 0}, {"src": "model-select", "oport": 0}]
    iports += [{"src": p, "oport": 0} for p in img_ports]
    if video_port:
        iports.append({"src": video_port, "oport": 0})
    if audio_port:
        iports.append({"src": audio_port, "oport": 0})
    cfg = {"frames": FRAMES, "reference_image_short_edge": 1024, "unload_when_idle": "auto"}
    if attach_audio:
        cfg["attach_audio"] = attach_audio
    return {"id": "video-ref-encoder", "type": "video-ref-encoder", "iports": iports, "config": cfg}


def tail(out_name):
    return [
        {"id": "generate-video", "type": "generate-video",
         "iports": [{"src": "video-ref-encoder", "oport": 0}, {"src": "", "oport": 0},
                    {"src": "model-select", "oport": 0}, {"src": "", "oport": 0},
                    {"src": "", "oport": 0}, {"src": "", "oport": 0}, {"src": "", "oport": 0},
                    {"src": "video-ref-encoder", "oport": 1}, {"src": "video-ref-encoder", "oport": 2},
                    {"src": "minimax-h3-model-config", "oport": 0}],
         "config": {"height": HEIGHT, "width": WIDTH, "frames": FRAMES, "fps": 24, "steps": STEPS,
                    "seed": SEED, "i8_gemm": True, "unload_when_idle": "always"}},
        {"id": "vae-decode", "type": "vae-decode",
         "iports": [{"src": "generate-video", "oport": 0}, {"src": "model-select", "oport": 0}],
         "config": {}},
        {"id": "audio-vae-decode", "type": "audio-vae-decode",
         "iports": [{"src": "generate-video", "oport": 1}, {"src": "model-select", "oport": 0}],
         "config": {}},
        {"id": "rgb-to-video", "type": "rgb-to-video",
         "iports": [{"src": "vae-decode", "oport": 0}], "config": {"fps": 24}},
        {"id": "save-video", "type": "save-video",
         "iports": [{"src": "rgb-to-video", "oport": 0}, {"src": "audio-vae-decode", "oport": 0}],
         "config": {"output_url": out_name, "enable_video": True, "enable_audio": True}},
    ]


def build_a():
    """A 组：1 张图参考，shift 6.0（基线）"""
    stages = [
        model_select(),
        text_prompt(PROMPTS["A"]),
        model_config(6.0),
        load_image("load-subject", CAT),
        resample("size-subject", "load-subject", 1024, 1024),
        ref_encoder(img_ports=["size-subject"]),
    ] + tail("out/p9-ref2va-768p-a.mp4")
    return {"id": "p9-ref2va-768p-a", "stages": stages, "subpipelines": []}


def build_b():
    """B 组：与 A 组逐字相同，只把 video_shift 从 6.0 改成 12.0"""
    d = build_a()
    d["id"] = "p9-ref2va-768p-b-shift12"
    for s in d["stages"]:
        if s["id"] == "minimax-h3-model-config":
            s["config"]["video_shift"] = 12.0
        if s["id"] == "save-video":
            s["config"]["output_url"] = "out/p9-ref2va-768p-b-shift12.mp4"
    return d


def build_c():
    """C 组：1 张图 + 1 段动作参考视频 + 该视频的音轨，shift 6.0"""
    stages = [
        model_select(),
        text_prompt(PROMPTS["C"]),
        model_config(6.0),
        load_image("load-subject", CAT),
        resample("size-subject", "load-subject", 1024, 1024),
        {"id": "load-motion", "type": "load-video", "iports": [],
         "config": {"input_url": MOTION}},
        {"id": "motion-frames", "type": "video-to-rgb",
         "iports": [{"src": "load-motion", "oport": 0}], "config": {"output_dtype": "u8"}},
        resample("size-motion", "motion-frames", WIDTH, HEIGHT),
        {"id": "stack-motion", "type": "temporal-stack",
         "iports": [{"src": "size-motion", "oport": 0}],
         "config": {"mode": "video", "group_size": 0, "max_mb": 384}},
        {"id": "motion-pcm", "type": "audio-to-pcm",
         "iports": [{"src": "load-motion", "oport": 1}],
         "config": {"output_sample_rate": 32000, "channels": 2,
                    "chunk_duration_s": 30.0, "max_chunk_duration_s": 60.0}},
        {"id": "stack-pcm", "type": "temporal-stack",
         "iports": [{"src": "motion-pcm", "oport": 0}],
         "config": {"mode": "audio", "group_size": 0}},
        # 喂进去 3 条：img(slot1) / video(slot2) / audio(slot3) → attach_audio 填音频自己的 slot 号 3
        ref_encoder(img_ports=["size-subject"], video_port="stack-motion",
                    audio_port="stack-pcm", attach_audio=[3]),
    ] + tail("out/p9-ref2va-768p-c-multiref.mp4")
    return {"id": "p9-ref2va-768p-c-multiref", "stages": stages, "subpipelines": []}


def build_d():
    """D 组：与 A 组逐字相同，video_shift = 8.0 —— 用来把 shift 做成**三点梯度**（6.0 / 8.0 / 12.0）

    为什么需要这一组：
      A(6.0) 与 B(12.0) 的量化结论是「Ref2VA 768p 上 shift 12.0 的纹理反而更锐」，
      与第 8 轮 FL2VA 的结论方向相反。单个两点对比无法区分
      「12.0 真的更好」与「6.0 这档采样网格在 Ref2VA 上恰好不对」。
      加一档中间值 8.0，若细节能量随 shift 单调变化 → 说明 shift 在 Ref2VA 768p 上
      是**连续生效的**，官方文档写的 6.0 对 Ref2VA 可能不是最优。
    """
    d = build_a()
    d["id"] = "p9-ref2va-768p-d-shift8"
    for s in d["stages"]:
        if s["id"] == "minimax-h3-model-config":
            s["config"]["video_shift"] = 8.0
        if s["id"] == "save-video":
            s["config"]["output_url"] = "out/p9-ref2va-768p-d-shift8.mp4"
    return d


def main():
    outdir = os.path.join(WS, "pipelines")
    os.makedirs(outdir, exist_ok=True)
    for d in (build_a(), build_b(), build_c(), build_d()):
        p = os.path.join(outdir, d["id"] + ".vpipeline")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("wrote", p)


if __name__ == "__main__":
    main()
