---
name: vpipe-first-frame-to-video
description: 使用 vpipe 的 MiniMax-H3 FL2VA 首帧锚定模式，把一张静态图片变成一段带声音的短视频，首帧与原图像素级一致。适用于"商品图转短视频"、"照片动起来"、"保持画面构图不变的运镜"等场景。本技能应在本机需要以图片为起点生成视频、或需要保证首帧与原图严格一致时使用。
agent_created: true
---

# vpipe 首帧图生视频（i2va）

给定一张图，让它动起来。**首帧与原图高度一致**（实测 SSIM 0.9505 / PSNR 31.11 dB），构图、光线、姿态全部保留，模型只负责让它"活"起来。

## 何时使用

- 电商：一张商品图 → 带运镜的短视频
- 摄影：一张照片 → 有轻微呼吸感的动态画面
- 需要**严格保留原图构图**做二次创作
- 首尾帧都提供 → 走 `vpipe-first-last-to-video`

**不适用**：想换主体外观（那是 `vpipe-reference-to-video`）；想让商品在整段片子里都在（首帧锚定做不到，见下方「关键限制」）。

## 工作原理

```
load-image → image-resample(832×480) → vae-encode → generate-video 端口 5
                                                       ↑
                                        diffusion-conditioner → 端口 3（首帧条件）
```

关键在 `vae-encode`：它把图编码成 **keyframe latent**，由 `generate-video` 的 **5 号端口**接收并"钉"在第 0 帧。

日志会明确确认：
```
GenerateVideoStage('generate-video'): 1 keyframe anchor (first frame) rounded to bf16
(the adapter's conditioning policy), noised to t 0.999
```

## 关键限制（实测得出，容易踩）

> **只有首帧锚定时，DiT 会按提示词重构画面。**

实测证据：一张穿深蓝牛仔外套的猫图做首帧锚定，
- 第 0 帧：外套在，SSIM 0.9505
- 第 20 帧：外套还在
- 第 40 帧：**外套消失**，背景/光线/姿态整体重构，SSIM 断崖到 0.42

也就是说**锚定只保第 0 帧**，不是"保全程"。

| 需求 | 正确路线 |
|---|---|
| 商品/主体只需在**开头**出现 | 首帧锚定 ✅ |
| 商品/主体要**全程都在** | **首尾帧锚定**（`vpipe-first-last-to-video`）|
| 主体外观要换、场景要换 | 参考生视频（`vpipe-reference-to-video`）|

## 快速开始

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

# 1) 准备 FL2VA-8bit + Pika H3 Flex fl2va adapter
$VPIPE --launch ./pipelines/prepare-minimax-h3-8bit.vpipeline
$VPIPE --launch ./pipelines/prepare-pika-h3-flex.vpipeline

# 2) 出片
$VPIPE --launch ./pipelines/pika-i2va-shop.vpipeline
```

## 完整流水线

```json
{
  "id": "my-i2va",
  "stages": [
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "local/MiniMax-H3-FL2VA-8bit" } },
    { "id": "load-image", "type": "load-image", "iports": [],
      "config": { "url": ["/abs/path/to/product.jpg"] } },
    { "id": "image-resample", "type": "image-resample",
      "iports": [ {"src":"load-image","oport":0} ],
      "config": { "width": 832, "height": 480, "fit": "crop", "algorithm": "lanczos" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "The camera slowly pushes in. Audio: soft room tone." } },
    { "id": "diffusion-conditioner", "type": "diffusion-conditioner",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": { "unload_when_idle": "always" } },
    { "id": "vae-encode", "type": "vae-encode",
      "iports": [ {"src":"image-resample","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
      "config": { "video_shift": 12.0, "audio_shift": 3.0, "audio_seconds": 5.18,
                  "lora": "Pika-Labs/Pika-H3-Flex-fl2va", "lora_scale": 1.0 } },
    { "id": "generate-video", "type": "generate-video",
      "iports": [
        {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
        {"src":"model-select","oport":0},
        {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
        {"src":"vae-encode","oport":0},
        {"src":"","oport":0}, {"src":"","oport":0}, {"src":"","oport":0},
        {"src":"minimax-h3-model-config","oport":0} ],
      "config": { "width": 832, "height": 480, "frames": 124, "fps": 24,
                  "steps": 6, "seed": 42, "i8_gemm": true, "unload_when_idle": "always" } },
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

## 三个容易搞错的接线点

**1. `generate-video` 的端口 3 和端口 5 都要接**
- 端口 3 = 文本条件（`diffusion-conditioner` 输出）
- 端口 5 = **keyframe latent**（`vae-encode` 输出）
- 端口 6 = 末帧 keyframe（首尾帧模式才用）

漏接端口 5 = 退化成文生视频，图完全没进去。

**2. `save-video` 需要两个输入边**
```
rgb-to-video (oport 0)  → save-video iport 0
audio-vae-decode (oport 0) → save-video iport 1
```
只接一路会报 `expected 2 input edge(s) (enable_video=true, enable_audio=true) but got 1`，整个 stage 被跳过，流水线**秒退且不报错**——这是最容易浪费时间的一种失败。

**3. `save-video` 的键是 `output_url`，不是 `path`**

## 尺寸处理

`image-resample` 的 `fit: "crop"` 会**居中裁切**到目标比例。原图与目标比例不一致时会裁掉边缘。

- 竖图（如 484×864）→ 832×480 会裁掉上下大量内容，主体可能整块被切掉
- 建议：先用 `image-resample` 配 `fit: "letterbox"` 或先裁好原图

**参考图比例建议与输出一致**（832×480 ≈ 1.73:1），否则构图会被强行改变。

## 提示词写法

首帧锚定模式下，提示词的作用是**描述运动**，不是描述画面（画面已经由图决定）。

```
The camera slowly pushes in. The subject blinks and breathes naturally.
Audio: soft room tone, distant city ambience.
Normal real-time speed, no slow motion. No text, no captions, no logos.
```

**运动幅度要克制**。首帧锚定的自由度本就很小，提示词要求越离谱（"人物转身跳跃"），DiT 重构画面的压力就越大 —— 那正是商品消失的原因。

## 实测数据（本机 M5 Pro 24GB）

| 项 | 值 |
|---|---|
| 耗时 | **5 分 59 秒** |
| 规格 | 832×480 / 124 帧 / 5.18 s + AAC |
| 首帧 SSIM | **0.9505** |
| 首帧 PSNR | **31.11 dB** |
| 全片平均 SSIM | 0.5774 |
| 去噪行数 | 15,712 rows |

差分图验证：4× 放大后，输出首帧与参考图 crop 的残差**只有低阶强度偏差**（VAE 重建 + H.264 量化），**没有可辨识的结构形状** → 几何完全对齐。

## 验证保真度

```bash
# 抽首帧
ffmpeg -i out.mp4 -vf "select=eq(n\,0)" -vframes 1 f000.png
# 生成参考图 crop
ffmpeg -i ref.jpg -vf "scale=832:480:force_original_aspect_ratio=increase,crop=832:480" ref-crop.png
# 算相似度
ffmpeg -i f000.png -i ref-crop.png -lavfi "[0:v][1:v]ssim;[0:v][1:v]psnr" -f null -
```

`scripts/anchor-fidelity.sh` 把这个流程批量化，同时输出逐帧 SSIM 衰减曲线。

## 参考资料

- `references/anchor-vs-reference.md` —— 锚定与参考的量化对比
- `references/troubleshooting.md` —— 故障排查表
- `assets/pika-i2va.vpipeline` —— 可直接改用的出片流水线
