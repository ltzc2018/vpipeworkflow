---
name: vpipe-reference-to-video
description: 使用 vpipe 的 MiniMax-H3 Ref2VA 模式，以参考图（可叠加参考视频/参考音频）为条件生成带声音的短视频。适用于"保持主体身份换场景换动作"、"商品图生视频"、"角色一致性"、"多参考组合"等场景。本技能应在本机需要用参考图生成视频、或需要判断参考图是否真正生效时使用。
agent_created: true
---

# vpipe 参考生视频（Ref2VA）

用参考图作为条件，让 MiniMax-H3 生成一段**带环境音/音效/配乐**的视频，主体身份、服饰、风格从参考图继承。

## 何时使用

- 手里有一张主体照片，想让它动起来（换动作、换场景、保持同一张脸）
- 电商「一物多场景」：同一件商品出现在多个环境里
- 需要参考**动作/镜头**：再喂一段参考视频（`<Video 1>`）
- 需要参考**音色/配乐**：再喂一条参考音频（`<Audio 1>`）
- 多参考组合：商品图 + 场景图 + 动作参考视频，一次最多 **9 图 + 3 视频 + 3 音频 = 12 项**

**不适用**：需要把某张图**钉死**为第 0 帧时——那是 `vpipe-first-frame-to-video` 的活。官方明确说明**参考与关键帧互斥**（见下方「硬约束」）。

## 核心概念

| 概念 | 说明 |
|---|---|
| **FL2VA** | 文生视频 / 首帧 / 首尾帧锚定。用 `local/MiniMax-H3-FL2VA-8bit` |
| **Ref2VA** | 参考图/视频/音频条件。用 `local/MiniMax-H3-Ref2VA-8bit` |
| `video-ref-encoder` | 把参考打包成条件行的 stage。输出接到 `generate-video` 的 **0**（条件）/ **7**（参考视频行）/ **8**（参考音频行） |
| `references` | 文件列表写法。一次最多 9 图 + 3 视频 + 3 音频 = 12 项，且音频不能是唯一种类 |

两种 partition 共用同一个 Qwen3-VL-32B 编码器和同一对双 VAE，**只有 DiT 权重不同**。

## 硬约束（官方设计，实测确认）

> **参考不是关键帧，Ref2VA 无法钉住某一帧。**

Ref2VA 的序列是 `[text | reference blocks | target audio | target video]`，FL2VA 是 `[text | keyframe conditions | target audio | target video]`。序列里**没有任何槽位**能把参考绑到输出第 0 帧。

因此：
- 在提示词里写 *"use image 1 as the opening frame"* **完全无效**——没有机制让它生效
- 在 Ref2VA 图上接关键帧，`generate-video` 会**告警**，不会静默丢弃
- 一次运行里服装和面容都迁移过来了，首帧却没有 —— 这是正常行为，不是 bug

## 实测数据（本机 M5 Pro 24GB）

| 路线 | 权重 | 参考 | 耗时 | 规格 |
|---|---|---|---|---|
| 参考生视频 | Ref2VA-8bit + Pika H3 Flex ref2va | ✅ | 6 分 49 秒 | 832×480 / 124 帧 / 5.18 s + AAC |
| 参考生视频（官方已发布配对） | FL2VA-8bit + VDN 线性分支 | ✅ | 8 分 20 秒 | 960×544 / 124 帧 / 5.18 s + AAC |
| 参考生视频（无参考对照） | Ref2VA-8bit | ❌ 空列表 | 5 分 50 秒 | 960×544 / 124 帧 |

**参考生视频的像素保真度很低**：首帧 SSIM 约 **0.49–0.52**。参考图做的是**语义条件**，不是像素重建。

## 快速开始

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

# 1) 准备 Ref2VA-8bit（见 vpipe-model-prepare 技能）
$VPIPE --launch ./pipelines/prepare-minimax-h3-ref2va-8bit.vpipeline

# 2) 准备 Pika H3 Flex ref2va adapter
$VPIPE --launch ./pipelines/prepare-pika-h3-flex.vpipeline

# 3) 出片
$VPIPE --launch ./pipelines/pika-ref2va-ablation.vpipeline
```

改参考图：编辑 `video-ref-encoder` 的 `references` 数组（绝对路径），或用 `--stage-cfg` 覆盖。

## 完整可运行流水线（照抄即可）

```json
{
  "id": "my-ref2va",
  "stages": [
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "local/MiniMax-H3-Ref2VA-8bit" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "References: @Image1 is the subject sheet. ..." } },
    { "id": "video-ref-encoder", "type": "video-ref-encoder",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"model-select","oport":0} ],
      "config": {
        "references": ["/abs/path/to/ref.jpg"],
        "frames": 124,
        "reference_image_short_edge": 1024,
        "reference_video_short_edge": 480,
        "reference_video_max_pixels": 399360,
        "unload_when_idle": "auto"
      } },
    { "id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
      "config": { "video_shift": 12.0, "audio_shift": 3.0, "audio_seconds": 5.18,
                  "lora": "Pika-Labs/Pika-H3-Flex-ref2va", "lora_scale": 1.0 } },
    { "id": "generate-video", "type": "generate-video",
      "iports": [
        {"src":"video-ref-encoder","oport":0}, {"src":"","oport":0},
        {"src":"model-select","oport":0}, {"src":"","oport":0},
        {"src":"","oport":0}, {"src":"","oport":0},
        {"src":"video-ref-encoder","oport":1}, {"src":"video-ref-encoder","oport":2},
        {"src":"","oport":0}, {"src":"minimax-h3-model-config","oport":0} ],
      "config": { "width": 832, "height": 480, "frames": 124, "fps": 24,
                  "steps": 6, "seed": 42, "i8_gemm": true, "unload_when_idle": "always" } },
    { "id": "save-video", "type": "save-video",
      "iports": [ {"src":"generate-video","oport":0} ],
      "config": { "output_url": "/abs/path/to/out.mp4",
                  "enable_video": true, "enable_audio": true } }
  ],
  "subpipelines": []
}
```

**四个必须写对的地方**（写错会静默失败）：

1. `save-video` 的键是 **`output_url`**，不是 `path`。写成 `path` 会得到 `config.output_url is required; skipping initialize/process` —— 整个 stage 被跳过，流水线秒退还不报错。
2. `video-ref-encoder` 的 `frames` **必须等于** `generate-video` 的 `frames`。不一致时日志是 `the layout reserves N reference video rows but the encoder packed 0 and 0 ... skipping`。
3. `reference_video_short_edge` + `reference_video_max_pixels` 必须写。缺了会报 `last-frame keyframe latent does not match [24, n, 30, 52]`。
4. `generate-video` 的 `i8_gemm: true` 能明显提速。

## 提示词写法

**消融实验的关键**：提示词里**不要写主体的外观描述**。写死了外观，就无法证明参考图生效。

```
References: @Image1 is the subject sheet. Make a new video of the subject from @Image1.
The subject sits on a wooden windowsill in warm late-afternoon sunlight, looks directly at
the camera, blinks slowly; the camera pushes in very slowly.
Audio: soft rhythmic purring, a faint breeze through the open window, distant birdsong.
Normal real-time speed, no slow motion. No text, no captions, no logos.
```

要点：
- `References: @Image1 is the subject sheet` —— 声明参考图的**角色**，这是 Pika adapter 的契约
- 只描述**动作、场景、镜头、音频**，不描述外观
- `Audio:` 段写环境音/音效/配乐，H3 的音画是同一次去噪里产生的
- 结尾的 `Normal real-time speed, no slow motion. No text, no captions, no logos.` 能有效抑制水印和字幕

官方 Pika 提示词范式还要求写 *"Keep the character exactly as designed in @Image1 — same face, proportions, **outfit**, colours"*。服装丢失是已知问题，官方给的解法就是点名要求保留。

## 关键配置

`video-ref-encoder`：

| 键 | 默认 | 说明 |
|---|---|---|
| `references` | — | 文件列表。`[]` 表示**显式无参考**（走 prompt-only Ref2VA） |
| `reference_image_short_edge` | 2048 | **静帧按自己短边编码，没有总像素上限**。2048 下单张就是 121 个 VAE 图块，9 张会爆显存。务必降到 **1024** |
| `reference_video_short_edge` | 768 | 参考视频画布。**不写会导致 frames 不匹配** |
| `reference_video_max_pixels` | 1032192 | 参考视频像素上限 |
| `frames` | — | **必须与 `generate-video` 的 `frames` 一致**，两者互相校验 |
| `attach_audio` | — | `[N]` 表示 N 号参考的音频折叠到它前面那个参考上（按位置，不是端口号） |

`generate-video`：

| 键 | 值 |
|---|---|
| `width` / `height` | 832×480（Pika 路线）/ 960×544（FL2VA 路线） |
| `frames` | 124（5.18 s @ 24fps） |
| `steps` | 6（Pika）/ 4–6（Turbo LoRA） |
| `seed` | 固定值便于对照 |

## 常见坑

**1. `references: []` 与省略 `references` 键是两回事**
- `[]` = 显式无参考，合法，走 prompt-only Ref2VA
- 省略键且不接任何 `ref` 端口 = 编码器什么都没拿到，**会告警并跳过请求**，不会花掉一次 33B 去噪

**2. `references` 里的静帧要自己降 `reference_image_short_edge`**
官方默认值 2048 是给"少量大图"设计的。多参考时必须降到 1024，否则显存爆炸。

**3. 参考视频的帧率必须活下来**
MiniMax-H3 会把每个参考重采样到 24 fps。输入途中丢了帧率 = 以错误速度做条件，**而且没有任何东西会抱怨**。走端口路线时必须在 `video-ref-encoder` 上声明 `fps`。

**4. 音频采样率必须是 32000 Hz**
一段未被统一的 44.1 kHz 音轨会被当成 32 kHz 编码 —— 快 1.38 倍、音高升高四度，**所有形状依然合法**。用 `audio-to-pcm` 的 `output_sample_rate: 32000`。

**5. 参考图被上采样会导致画面比例走样**
`reference_image_short_edge` 作用于**短边**。一张 484×864 的竖图，短边 484 → 1024 会变成 1024×1824（447% 像素），日志会警告 `UPSCALED ... (447% of the pixels)`。竖图建议单独准备正方形或匹配输出比例的版本。

**6. 服装/配饰经常丢失**
参考图负责"主体长什么样"，但服装、配饰往往不自动保留。需要保真见 `vpipe-first-last-to-video`。

## 验证参考图是否真的生效

**这是本技能最该被认真执行的部分。** 直接看片子里"像不像"是自说自话。

三层验证：

1. **消融对照**：跑两组，只差 `references` 一项。但必须先问"对照组能不能产生不同结果"——猫参考图 vs 场景先验也能出猫，就是不可证伪。**换一个模型先验不可能产出的参考主体**（如水彩熊猫）才有效。
2. **第三方模型复核**：用 LFM3-VL-2B / Qwen3.5-4B 对输出抽帧提问。如果两个独立模型都答对，而提示词里根本没有那个词，结论就被独立验证了。
3. **像素级量化**：`scripts/anchor-fidelity.sh` 逐帧算 SSIM/PSNR。参考生视频约 0.49–0.52。

**反直觉但重要**：参考生视频"有参考"(0.5120) 的 SSIM **低于**"无参考对照"(0.5718)。这说明参考图不是把输出往参考图拉，而是**改写主体本身**。

## 多参考组合（进阶）

官方 `minimax-h3-reference-to-video.vpipeline` 用**端口路线**而非文件列表：

```
load-image → image-resample(1024×1024)                              → ref1
load-video ┬→ video-to-rgb → image-resample(1344×768) → temporal-stack → ref2
           └→ audio-to-pcm(32000, stereo) → temporal-stack             → ref3
```

关键细节：
- `attach_audio: [3]` 让 ref3 的音频成为 ref2 的音轨，保持 `<Video 1>` + `<Audio 1>` 配对
- `channels: 2` 承载真正的立体声
- 视频堆叠器 `max_mb: 384` 是有意设的（124 帧 @ 1344×768 = 366 MiB，超过默认 256 MiB 会被截到 86 帧）
- `reference_video_short_edge: 0` 让参考视频保持在输出画布尺寸上，行数不翻倍

端口路线的**优势**：可以自己决定每个参考的几何尺寸。文件列表路线则由模型自己定尺寸。

## 参考资料

- `references/ref2va-ports.md` —— 端口与序列布局详解
- `references/prompt-guide.md` —— 提示词写法与消融方法论
- `references/troubleshooting.md` —— 故障排查表
- `assets/pika-ref2va.vpipeline` —— 可直接改用的出片流水线
- `assets/prepare-ref2va-8bit.vpipeline` —— Ref2VA 8-bit 准备流水线
