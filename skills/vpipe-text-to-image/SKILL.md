---
name: vpipe-text-to-image
description: 使用 vpipe 在本机做文生图（text-to-image）。已验证两个模型：Z-Image-Turbo（6B 蒸馏，8 步，约 42 秒）与 Krea-2-Turbo（8 步，约 50 秒），均可在 24GB 统一内存的 Mac 上跑动 25–30GB bf16 权重。适用于生成电商主图、场景图、素材底图，以及为视频生成链路预先生成参考图。本技能应在本机需要生成图片、或需要横评多个图像模型时使用。
agent_created: true
---

# vpipe 文生图（T2I）

在本机用纯文本生成高质量图片。vpipe 内置 catalog 有 152 个模型条目，image 类里本技能实测通过两个：**Z-Image-Turbo** 与 **Krea-2-Turbo**。

## 何时使用

- 生成电商主图、详情页配图、场景素材
- 给视频链路预先生成参考图（避免用网上素材带来的版权问题）
- 横评不同图像模型的速度与质量

**不适用**：需要基于已有图片修改 → 走 `vpipe-image-edit`。

## 两个已验证模型对照

| | **Z-Image-Turbo** | **Krea-2-Turbo** |
|---|---|---|
| 仓库 | `Tongyi-MAI/Z-Image-Turbo` | `krea/Krea-2-Turbo` |
| 参数量 | 6B（transformer 24.6 GB / 12.3B 参数 / 3 分片） | 12B（~28 GB） |
| 步数 | 8 步蒸馏 | 8 步 euler + simple |
| **实测耗时** | **42.5 秒** | **49.5 秒** |
| latent 生成 | 36.92 秒 | 45.64 秒 |
| 引导 | **no cfg**（`guidance_scale = 0`） | 5,458–5,705 ms/步 |
| 调度 | `simple (8 steps, shift 3 linear, rho 7)` | euler + simple |
| 声明峰值内存 | 31,311 MB | 34,014 MB |
| **实际流式驻留峰值** | **18,452 MB** | **15,841 MB** |
| 许可 | Apache-2.0 | 见官方文档 |

> **两者都在 24 GB 统一内存上跑动 24.6/28 GB 的 bf16 权重**，靠的是 vpipe 的 **residency 流式加载**（`plan_streaming`）。官方文档原话："the 28 transformer blocks do not fit beside the conditioner's text encoder even on 24 GB — `plan_streaming` says stream there too"。**不需要交换内存，也不会崩。**

## 快速开始

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

# 1) 准备模型
$VPIPE --launch ./pipelines/prepare-image-models.vpipeline

# 2) 出图
P="A ginger tabby cat wearing a dark blue denim jacket with brass buttons, sitting on a
wooden windowsill in warm late-afternoon sunlight, photorealistic, shallow depth of field"
time $VPIPE --launch ./pipelines/z-image-turbo-t2i.vpipeline \
  --stage-cfg "text-prompt::text=\"$P\"" \
  --stage-cfg "save-image::path=\"out/cat.jpeg\""
```

**注意：`prepare-image-models.vpipeline` 里 Krea-2 的 `mgwr/M87` LoRA 只发布在 HuggingFace**，本机 HF 直连不通会导致该 stage 失败、整条流水线 drain。解决办法见下方「Krea-2 无 LoRA 运行」。

## Z-Image-Turbo 完整流水线

```json
{
  "id": "z-image-turbo-t2i",
  "stages": [
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "Tongyi-MAI/Z-Image-Turbo" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "your prompt here" } },
    { "id": "diffusion-conditioner", "type": "diffusion-conditioner",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": { "unload_when_idle": "always" } },
    { "id": "z-image-model-config", "type": "z-image-model-config", "iports": [], "config": {} },
    { "id": "generate-image", "type": "generate-image",
      "iports": [ {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": { "width": 1024, "height": 1024, "steps": 8, "seed": 42 } },
    { "id": "vae-decode", "type": "vae-decode",
      "iports": [ {"src":"generate-image","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "save-image", "type": "save-image",
      "iports": [ {"src":"vae-decode","oport":0} ],
      "config": { "path": "out/image.jpeg" } }
  ],
  "subpipelines": []
}
```

`save-image` 用 `path`（**不是** `output_url`）；`save-video` 才用 `output_url`。

## Krea-2-Turbo 无 LoRA 运行

官方 `docs/KREA-2.md` 有一节「Running without the LoRA」。做法：

1. 从 `krea2-model-config` 里删掉 `lora` / `lora_scale`（该 stage 的 config 留空 `{}`）
2. 提示词末尾删掉 `--preview` 触发器

这样出的图没有 M87 美学 LoRA 的风格强化，但完全可用。

**官方基准对照**：官方文档给 M5 Pro **20 核** 24 GB = **35 秒**；本机 M5 Pro **15 核** = 49.5 秒。核数比 1.33×、耗时比 1.41×，与官方「随 GPU 核数近似线性缩放」吻合。

## 提示词写法

Z-Image 与 Krea 都吃**自然语言描述**，英文效果更稳。结构：

```
[主体] + [动作/姿态] + [服装/材质细节] + [场景/背景] + [光线] + [画质标签] + --no text, no watermark, no logo
```

**电商主图示例**（实测出片效果很好）：
```
E-commerce product photograph of a dark blue denim jacket hanging on a wooden hanger
against a warm beige wall, soft directional window light from the left, crisp visible
denim weave texture, contrast stitching and brass buttons clearly visible, clean minimal
background, studio quality --no text, no watermark, no logo
```

**`--no text, no watermark, no logo` 很关键**。实测不写会生成水印和假文字。

**跨模态一致性技巧**：视频实验用的是"姜黄虎斑猫 + 深蓝牛仔外套 + 木窗台 + 暖阳逆光"。把这个提示词原样喂给文生图模型，得到的是**同一主体、同一服装、同一场景**的静帧——可以用作视频链路的参考图，让画面与之前的视频对得上。

## 实测成品（可用于验证模型是否正常工作）

| 提示词 | LFM3-VL 的独立复核结果 |
|---|---|
| 猫场景（两个模型都跑） | "动物是一只橘色虎斑猫，穿着一件牛仔布制成的外套。这件外套是蓝色的，款式类似于夹克，有领子和纽扣。背景是一个室内环境，猫坐在窗台上" |
| 牛仔夹克商品图（两个模型都跑） | 两者都读出 **5 个金属扣子**，丹宁织纹与缝线均判为清晰 |

> 细节保真度读数两个模型**完全一致**（猫图 3 扣 / 挂拍商品图 5 扣）。"电商图要数得清扣子"这个硬指标，两者都过关。

## 常见坑

**1. Krea-2 的 M87 LoRA 只在 HuggingFace**
报错：`'mgwr/M87' has no counterpart on ModelScope -- it is published only on HuggingFace`。这个 stage 失败会**导致整条 prepare 流水线 drain**（后面的 `taew2_1` 也下不到）。解法：用无 LoRA 版流水线。

**2. `model_variant` 必须精确匹配**
`model-fetch` 的 variant 匹配是**逐字段**比对（version / variant / name / model_type 四选一），不是子串包含整个显示名。错误写法：
```
"model_variant": "Edit-2511 20B [bf16 (Qwen)]"   ← 匹配 0 个
```
正确写法（用 `model_type`）：
```
"model_variant": "qwen-image-edit"                ← 匹配 1 个
```

**3. HuggingFace 直连不通**
本机 HF curl 超时。所有下载走 ModelScope：
```bash
export VPIPE_MODEL_SOURCE=modelscope
```

**4. `model_variant` 留空时只有单一候选才行**
`variant.empty()` 时要求 `cands.size() == 1`，否则报 `matches 0 of the N models published from ...`。

**5. 4-bit 量化对 Z-Image 不可用**
上游 issue #41 实测：`Z-Image-Turbo` 的 4-bit（w4 g64）产物**完全不可用** —— 1024×1024 会在 28 秒后 GPU command-buffer 报错，更小尺寸直接硬挂。量化本身**报成功且零警告**，非常容易误发布。**8-bit 未被上游验证**，本技能暂不推荐量化图像模型。

## 参考资料

- `references/model-comparison.md` —— 两模型详细参数与官方基准
- `references/prompt-recipes.md` —— 分类提示词模板
- `references/troubleshooting.md` —— 故障排查表
- `assets/z-image-turbo-t2i.vpipeline` —— Z-Image 出片流水线
- `assets/krea-2-turbo-t2i-nolora.vpipeline` —— Krea-2 无 LoRA 出片流水线
- `assets/prepare-image-models.vpipeline` —— 模型准备流水线
