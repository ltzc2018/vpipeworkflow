---
name: vpipe-first-last-to-video
description: 使用 vpipe 的 MiniMax-H3 FL2VA 首尾帧锚定模式，给定首帧和末帧两张图，生成一段中间的插值视频，首帧与末帧都被严格锚定。适用于"商品必须全程在画面里"、"镜头从A构图推到B构图"、"两帧之间的平滑过渡"等场景。本技能应在本机需要端点保真、或实测发现仅首帧锚定会导致主体中途消失时使用。
agent_created: true
---

# vpipe 首尾帧插值（FL2VA）

给两张图（首帧 + 末帧），模型生成中间的过程。**两个端点都被钉住**，中间的镜头运动、姿态变化由模型补全。

## 何时使用

- **商品必须在整段片子里都在**（仅首帧锚定做不到——见下方「为什么必须是首尾帧」）
- 镜头从构图 A 推到构图 B（如全身中景 → 面部特写）
- 两张关键帧之间的平滑过渡
- 广告片：产品从全景推到细节特写

**不适用**：只有一张图 → 用 `vpipe-first-frame-to-video`；需要换主体外观 → 用 `vpipe-reference-to-video`。

## 为什么必须是首尾帧

本技能存在的唯一理由是实测得出的一条硬结论：

| 路线 | 首帧 | 末帧 | 中途（第40帧） |
|---|---|---|---|
| **仅首帧锚定** | 外套在，SSIM 0.9505 | — | **外套消失**，画面整体重构，SSIM 0.42 |
| **首尾帧锚定** | 外套在，SSIM 0.9500 | 外套在 | **外套与铜扣每一帧都在** |

**仅首帧锚定时，DiT 会按提示词重构画面** —— 实测一只穿深蓝牛仔外套的猫，外套在第 20–40 帧之间（约 1 秒）彻底消失，背景、光线、姿态全变。

**首尾帧锚定把两端都钉住**，中间的插值过程因此被约束在两个已知构图之间，主体不会中途跑掉。

> 实操结论：**商品要在整段片子里都在，必须给到末帧锚定。** 只给首帧是不够的。

## 工作原理

```
load-image-1 → image-resample ─┐
                                ├→ vae-encode-1 ─→ generate-video 端口 5（首帧 keyframe）
load-image-2 → image-resample ─┴→ vae-encode-2 ─→ generate-video 端口 6（末帧 keyframe）
```

日志确认：
```
GenerateVideoStage('generate-video'): 2 keyframe anchors (first + last frame), noised to t 1
```

首尾帧都被 `noised to t 1`（完全加噪再让模型去噪重建），这样两个端点都是"强条件"。

## 快速开始

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

$VPIPE --launch ./pipelines/h3-first-last.vpipeline
```

改图：编辑 `h3-first-last.vpipeline` 里两个 `load-image` 的 `url` 数组。

## 完整流水线

```json
{
  "id": "my-first-last",
  "stages": [
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "local/MiniMax-H3-FL2VA-8bit" } },
    { "id": "load-image-1", "type": "load-image", "iports": [],
      "config": { "url": ["/abs/path/to/first.jpg"] } },
    { "id": "load-image-2", "type": "load-image", "iports": [],
      "config": { "url": ["/abs/path/to/last.jpg"] } },
    { "id": "resample-1", "type": "image-resample",
      "iports": [ {"src":"load-image-1","oport":0} ],
      "config": { "width": 960, "height": 544, "fit": "crop", "algorithm": "lanczos" } },
    { "id": "resample-2", "type": "image-resample",
      "iports": [ {"src":"load-image-2","oport":0} ],
      "config": { "width": 960, "height": 544, "fit": "crop", "algorithm": "lanczos" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "The camera pushes in slowly to a close-up of the face. Audio: ..." } },
    { "id": "diffusion-conditioner", "type": "diffusion-conditioner",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": { "unload_when_idle": "always" } },
    { "id": "vae-encode-1", "type": "vae-encode",
      "iports": [ {"src":"resample-1","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "vae-encode-2", "type": "vae-encode",
      "iports": [ {"src":"resample-2","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
      "config": { "video_shift": 12.0, "audio_shift": 3.0, "audio_seconds": 5.18,
                  "lora": "larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema", "lora_scale": 1.0 } },
    { "id": "generate-video", "type": "generate-video",
      "iports": [
        {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
        {"src":"model-select","oport":0},
        {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
        {"src":"vae-encode-1","oport":0},
        {"src":"vae-encode-2","oport":0},
        {"src":"","oport":0}, {"src":"","oport":0},
        {"src":"minimax-h3-model-config","oport":0} ],
      "config": { "width": 960, "height": 544, "frames": 124, "fps": 24,
                  "steps": 5, "seed": 42, "i8_gemm": true, "unload_when_idle": "always" } },
    { "id": "vae-decode", "type": "vae-decode",
      "iports": [ {"src":"generate-video","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "audio-vae-decode", "type": "audio-vae-decode",
      "iports": [ {"src":"generate-video","oport":1}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "rgb-to-video", "type": "rgb-to-video",
      "iports": [ {"src":"vae-decode","oport":0} ], "config": {} },
    { "id": "save-video", "type": "save-video",
      "iports": [ {"src":"rgb-to-video","oport":0}, {"src":"audio-vae-decode","oport":0} ],
      "config": { "output_url": "/abs/path/to/out.mp4",
                  "enable_video": true, "enable_audio": true } }
  ],
  "subpipelines": []
}
```

## 端口对照表

| `generate-video` 端口 | 用途 | 本模式接什么 |
|---|---|---|
| 0 | 条件 | `diffusion-conditioner` |
| 1 | — | 空 |
| 2 | 模型 | `model-select` |
| 3 | 文本/多模态条件 | `diffusion-conditioner` |
| 4 | — | 空 |
| **5** | **首帧 keyframe** | `vae-encode-1` |
| **6** | **末帧 keyframe** | `vae-encode-2` |
| 7/8/9 | 参考视频/音频行 | 空（Ref2VA 才用） |
| 10 | 模型配置 | `minimax-h3-model-config` |

**端口 5 和 6 都要接**，漏一个就退化成单锚定。

## 首尾帧的准备要点

**1. 两张图必须同尺寸同比例**
两个 `image-resample` 用完全相同的 `width`/`height`/`fit`/`algorithm`。不一致会导致 latent 形状不匹配。

**2. 两张图要有连贯性**
模型要插的是"同一场景的两个时刻"。如果两张图的主体/服装/背景完全不同，模型会硬凑出一段诡异的过渡。

**3. 构图差异越大，插值越剧烈**
实测：全身中景 → 面部极特写，跨度很大，模型给出了平滑的镜头推进，牛仔外套全程保留。这个跨度是可行的。

**4. 提示词描述中间过程，不是描述画面**
```
The camera slowly pushes in to a close-up of the face. The subject's expression softens.
Audio: quiet room tone, a faint breath.
Normal real-time speed, no slow motion.
```

## 实测数据（本机 M5 Pro 24GB）

| 项 | 值 |
|---|---|
| 耗时 | **8 分 41 秒** |
| 规格 | 960×544 / 124 帧 / 5.18 s + AAC |
| 锚定数 | `2 keyframe anchors (first + last frame), noised to t 1` |
| 首帧 SSIM | **0.9500** |
| 全片平均 SSIM | **0.6657**（四类视频里最高） |
| 模型 | FL2VA-8bit + `larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema` |

目检结果：镜头从正面全身中景**平滑推进**到面部极特写，深蓝牛仔外套（含铜扣）**全程保留**。

## 常见坑

**1. 只接了端口 5，忘了端口 6**
退化成单锚定，主体中途会消失。

**2. `save-video` 只接了一路**
`expected 2 input edge(s) (enable_video=true, enable_audio=true) but got 1` —— stage 被跳过，流水线秒退。

**3. `save-video` 用了 `path` 而不是 `output_url`**
`config.output_url is required; skipping initialize/process`。

**4. 两张图尺寸不一致**
两个 `vae-encode` 产出的 latent 形状不同，`generate-video` 会告警 `last-frame keyframe latent does not match [24, n, 30, 52]` 并**丢掉末帧**。

**5. 并行跑重任务时进程被杀**
实测在并行下载 66GB 模型时，同期跑的这条流水线被杀（日志一切正常后无错消失）。下载结束后重跑即通过。**重任务之间要串行。**

## 参考资料

- `references/anchor-fidelity.md` —— 四类路线保真度对比与结论
- `references/troubleshooting.md` —— 故障排查表
- `assets/h3-first-last.vpipeline` —— 可直接改用的出片流水线
