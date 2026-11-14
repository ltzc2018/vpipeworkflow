---
name: vpipe-image-edit
description: 使用 vpipe 做图生图与参考图编辑：把一张或多张已有图片作为条件，生成新图或按提示词修改。已验证的模型包括 FLUX.2-klein-9B（多参考合成）、Qwen-Image-Edit-2511、Boogu-Image-0.1-Edit-Turbo。适用于"把商品图换个场景"、"按参考图风格重绘"、"两张图合成一张"、"换装/换背景"等场景。本技能应在本机需要基于已有图片生成或修改图片时使用。
agent_created: true
---

# vpipe 图生图与参考图编辑

以已有图片为条件生成新图。参考图以 **latent** 形式进入 DiT（不是像素），因此它约束的是**内容与结构**，不是逐像素复制。

## 何时使用

- 电商：商品图换背景、换场景、换灯光
- 风格迁移：把商品图重绘成插画/水彩/油画风格
- 多图合成：把 A 图的主体放到 B 图的场景里
- 换装：保持人脸与姿态，换服装
- 生成视频链路需要的参考图（避免用有版权的网上素材）

**不适用**：纯文字生成 → `vpipe-text-to-image`；把图变成视频 → `vpipe-first-frame-to-video` / `vpipe-reference-to-video`。

## 三种已验证路径

| 模型 | 类型 | 特性 | 状态 |
|---|---|---|---|
| **Boogu-Image-0.1-Edit-Turbo** | `boogu-image-edit` | 10B，**4 步蒸馏**，**参考图走 VLM 不走 latent**，**支持双参考图** | ✅ **本机已装已验证**（17.6–32.6 秒/张） |
| **FLUX.2-klein-9B** | `flux2` | 支持**多参考图**（`klein-multi-ref`）、KV 缓存变体提速 | 官方文档完整，本机待装（**gated 模型**） |
| **Qwen-Image-Edit-2511** | `qwen-image-edit` | 20B，指令式编辑能力强 | **本机装不下**（需 57.7 GB，24 GB 机器） |

> **本机当前唯一跑通的图生图路径是 Boogu**（2026-11-14 实测）。
> 详见 `references/boogu-edit.md`；流水线模板见 `assets/boogu-image-edit.vpipeline`。
>
> **Boogu 的核心机制与下面「参考图走 latent」那一节不同**：
> 它的 DiT **没有任何 `ref_latent` 通路**，参考图**只**经 Qwen3-VL 视觉塔进入条件。
> 所以它**不需要 `vae-encode`**，而且**两张参考图可以直接同框生成**（各 144 个视觉 token）。

## 核心机制：参考图走 latent

```
load-image → image-resample → vae-encode ─┐
                                           ├→ generate-image 端口 5（参考 latent）
text-prompt → diffusion-conditioner ───────┴→ generate-image 端口 0
```

**参考图以 latent 而非像素的形式进入 DiT**。这意味着：

- 参考图约束的是**语义/结构**，输出**不会**与参考图逐像素相同
- 参考图的**尺寸由 `image-resample` 决定**，不是模型自己决定 —— 这和视频链路的 `reference_image_short_edge` 是两套机制
- 提示词**按端口指称图片**："image 1"、"image 2"

## 完整流水线（单参考图编辑）

```json
{
  "id": "my-image-edit",
  "stages": [
    { "id": "load-image", "type": "load-image", "iports": [],
      "config": { "url": ["/abs/path/to/reference.jpg"] } },
    { "id": "image-resample", "type": "image-resample",
      "iports": [ {"src":"load-image","oport":0} ],
      "config": { "width": 512, "height": 512, "fit": "crop" } },
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "local/FLUX.2-klein-9B-4bit" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "Paint the reference picture in impressionist style..." } },
    { "id": "diffusion-conditioner", "type": "diffusion-conditioner",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "vae-encode", "type": "vae-encode",
      "iports": [ {"src":"image-resample","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "generate-image", "type": "generate-image",
      "iports": [ {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0}, {"src":"","oport":0},
                  {"src":"","oport":0}, {"src":"vae-encode","oport":0} ],
      "config": { "width": 768, "height": 512, "steps": 4, "i8_gemm": true } },
    { "id": "vae-decode", "type": "vae-decode",
      "iports": [ {"src":"generate-image","oport":0}, {"src":"model-select","oport":0} ],
      "config": {} },
    { "id": "save-image", "type": "save-image",
      "iports": [ {"src":"vae-decode","oport":0} ],
      "config": { "path": "out/edited.jpeg" } }
  ],
  "subpipelines": []
}
```

**参考图接在 `generate-image` 的端口 5**。

## Boogu-Image-Edit 接线（本机已验证，**优先用这个**）

Boogu 与 klein / Qwen 的**三点关键差异**（照抄 klein 的接线会静默出错）：

1. **必须接 `boogu-image-model-config`**，且**同时**接到
   `diffusion-conditioner` 的 iport5 **和** `generate-image` 的 iport7。
   前者给 VLM 的 `vl_*` 边界，后者让 DiT 认出家族；少接 `generate-image` 那条会打印
   `the model_config beat is for the 'boogu-image' family but the resident checkpoint is ...`。
2. **调度器必须 `type: "boogu_v1"`**。Boogu 的 sigma 约定**是反的**（0 = 噪声，1 = 干净），
   用默认 `simple` 会往反方向采样。
3. **不需要 `vae-encode`**（没有 latent 通路），**不要接 negative prompt、不要设 `guidance_scale > 1`**
   （Turbo 蒸馏版固定 CFG = 1）。

```json
{ "id": "model-select", "type": "model-select",
  "config": { "hf_dir": "Boogu/Boogu-Image-0.1-Edit-Turbo" } },
{ "id": "load-ref", "type": "load-image",
  "config": { "url": ["/abs/path/ref.jpg"] } },
{ "id": "ref-resample", "type": "image-resample",
  "iports": [ {"src":"load-ref","oport":0} ],
  "config": { "width":1024, "height":1024, "fit":"crop", "algorithm":"lanczos" } },
{ "id": "text-prompt", "type": "text-prompt",
  "config": { "text": "Replace the background with a neon-lit rainy alley, keep the same cat, same fur pattern, same pose." } },
{ "id": "boogu-model-config", "type": "boogu-image-model-config", "config": {} },
{ "id": "scheduler-select", "type": "scheduler-select",
  "config": { "type": "boogu_v1", "steps": 4, "seq_len": 4096 } },
{ "id": "diffusion-conditioner", "type": "diffusion-conditioner",
  "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
              {"src":"model-select","oport":0}, {"src":"ref-resample","oport":0},
              {"src":"","oport":0}, {"src":"boogu-model-config","oport":0} ],
  "config": {} },
{ "id": "generate-image", "type": "generate-image",
  "iports": [ {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
              {"src":"model-select","oport":0}, {"src":"","oport":0},
              {"src":"scheduler-select","oport":0}, {"src":"","oport":0},
              {"src":"","oport":0}, {"src":"boogu-model-config","oport":0} ],
  "config": { "width":1024, "height":1024, "steps":4, "seed":42 } },
{ "id": "vae-decode", "type": "vae-decode",
  "iports": [ {"src":"generate-image","oport":0}, {"src":"model-select","oport":0} ], "config": {} },
{ "id": "save-image", "type": "save-image",
  "iports": [ {"src":"vae-decode","oport":0} ],
  "config": { "path": "out/edited.jpeg", "quality": 95 } }
```

### Boogu 多参考图（实测：猫 + 熊猫同框）

```
load-ref-1  → ref-resample-1 ─→ diffusion-conditioner[3]  (ref_image)
load-ref-2  → ref-resample-2 ─→ diffusion-conditioner[4]  (ref_image2)
```

**每张参考图必须各接一个 `image-resample`**。
`load-image` 的 `url` 数组写多个元素时，多出来的 oport 是 `FlexDataPayload`，
而 `ref_image` 要 `TensorBeatPayload`，直连会报
`payload type mismatch ... producer FlexDataPayload vs consumer TensorBeatPayload`。

### Boogu 实测要点（本机，24 GB）

| 项 | 实测值 |
|---|---|
| 1024×1024 编辑 | **32.6 秒** |
| 576×1024 竖版 | **25.7 秒** |
| 384×1024 竖版 | **17.6 秒** |
| 双参考图 1024×1024 | **26.1 秒** |
| 参考图视觉 token | 每张 **144**（grid 24×24，3 层 deepstack） |

**参考图必须预先裁成「单一主体」**：同一张两栏拼图作参考 → 脸与体型大幅漂移；
裁成单人单幅后 → 姿态、服装、配件（含口罩）、亮片鞋全部保留。

**Boogu 会「美化」人像**：脸型、体型、肤色、发色都会朝模型审美漂。
**换背景/换场景够用；要保脸请走 `vpipe-first-frame-to-video` 的首帧锚定。**

## 多参考合成（商品图 + 场景图）

官方 `klein-multi-ref.vpipeline` 的接法：**每个参考各自一条 `load-image → image-resample → vae-encode`**，然后分别接 `generate-image` 的端口 5 和 6。

```
load-image-1 → image-resample-1 → vae-encode-1 → generate-image 端口 5
load-image-2 → image-resample-2 → vae-encode-2 → generate-image 端口 6
```

官方示例提示词（注意**按端口指称**）：
```
The orange tabby cat wearing the navy velvet jacket from image 1 sits beside the giant
panda from image 2 on a mossy rock in a misty bamboo forest. The panda offers the cat a
bamboo stalk. Keep the cat's face, fur pattern and jacket exactly as in image 1.
Paint the whole scene in the soft watercolor style of image 2.
```

**分工原则**（来自社区实测，重要）：**图片负责身份，视频负责动作**。
如果把参考视频也拿去锁身份，画面会拧巴。

## 两种模型变体

| 变体 | 说明 |
|---|---|
| `FLUX.2-klein-9B` | 基准。参考图 token **每步重新计算** |
| `FLUX.2-klein-9b-kv` | KV 缓存蒸馏。参考图 token **只算一次并复用**，带参考图时提速 **1.21–2.66×**，参考图越多提速越明显 |

## Qwen-Image-Edit 接线（不同）

Qwen 系列的 stage 略有不同，多一个 `qwen-image-21-model-config`：

```json
{ "id": "load-ref", "type": "load-image", "config": { "url": ["./reference.png"] } },
{ "id": "ref-resample", "type": "image-resample",
  "config": { "width": 1024, "height": 1024, "fit": "crop", "algorithm": "lanczos" } },
{ "id": "text-prompt", "type": "text-prompt",
  "config": { "text": "Put the subject on a quiet beach at sunset, warm rim light, the same face and clothing." } },
{ "id": "qwen-image-21-model-config", "type": "qwen-image-21-model-config", "config": {} },
{ "id": "scheduler-select", "type": "scheduler-select", "config": { "steps": 20 } },
{ "id": "vae-encode", "type": "vae-encode", "config": {} },
{ "id": "diffusion-conditioner", "type": "diffusion-conditioner", "config": {} },
{ "id": "generate-image", "type": "generate-image",
  "config": { "height": 1024, "width": 1024, "steps": 20, "seed": 7 } },
{ "id": "vae-decode", "type": "vae-decode", "config": {} },
{ "id": "save-image", "type": "save-image", "config": { "path": "out/edited.png", "format": "png", "compression": 6 } }
```

注意 Qwen 的 `generate-image` **不需要显式接 `vae-encode` 的 iport**（它自己内部处理参考图），而 klein 需要显式接端口 5。

## 提示词写法

**参考图编辑的三段式**：
```
[对参考图做什么] + [要保留什么] + [不要什么]
```

实例：
```
Put the subject on a quiet beach at sunset, warm rim light, the same face and clothing.
-- no text, no watermark, no logo
```

```
The jacket from image 1 hanging on a wooden hanger against a warm beige wall,
soft window light from the left, crisp denim weave visible, brass buttons clear,
clean minimal background -- no text, no watermark
```

**必须点名要保留的东西**。不写，模型会顺手把 logo、吊牌、包装纹理一起改掉。

## 常见坑

**1. `save-image` 用 `path`，`save-video` 用 `output_url`**
写反了会报 `config.output_url is required`（save-video 场景）。

**2. `model_variant` 匹配规则**
逐字段比对 `version`/`variant`/`name`/`model_type` 四选一。用 `model_type` 最稳：
```json
"model_variant": "qwen-image-edit"
```

**3. klein 需要 4-bit 量化，且 gated**
`FLUX.2-klein-9B` 在 HuggingFace 是 **gated 模型**（需要 token 申请权限）。本机 HF 不通 → 需要 ModelScope 是否有镜像。官方 prepare 流水线是 `prepare-klein-9b-4bit.vpipeline`，跑 bf16 版本则不需要量化。

**4. 4-bit 量化对 Qwen-Image-2.1 静默失败**
上游 issue #41：Qwen-Image-2.1 的 4-bit 产物会**静默输出全透明图**，量化报成功且零警告。**务必目检输出是不是空白。**

**5. `image-resample` 的 `fit` 会裁切**
可选值是 `pad | crop | stretch | manual | pad_to_grid | crop_to_grid | crop_to_area`
（**没有 `letterbox`**，`pad` 就是留边）。
`crop` 居中裁切、`pad` 留边。参考图与输出比例差异大时，选错会切掉主体 ——
竖版人像长图（如 520×2400）配 `crop` 到 576×1024 会**直接切掉头和脚**，用 `pad`。

**5b. Boogu：调度器不用 `boogu_v1` 会采样到反方向**
Boogu 的 sigma 约定是反的（0 = 噪声，1 = 干净），`scheduler-select.type` 必须是 `boogu_v1`。

**5c. Boogu：`load-image` 直连 `ref_image` 会报类型不匹配**
`load-image` 出 `FlexDataPayload`，`ref_image` 要 `TensorBeatPayload` —— 中间必须加 `image-resample`。

**5d. Boogu：多主体参考图会让脸和体型漂移**
两栏拼图作参考 → 模型把两个主体当成「一个人 + 场景」来折中。
**先裁成单人单幅再喂。**

**6. `compare-image` stage 可用于并排对照**
klein 官方流水线里有一个 `compare-image` stage，同时接原图和解码图，输出并排对照图 —— 调试时很方便。

## 参考资料

- `references/boogu-edit.md` —— **Boogu 完整实测报告**（机制对照、五个用例、漂移分析、故障排查）
- `references/troubleshooting.md` —— 故障排查表
- `assets/boogu-image-edit.vpipeline` —— **Boogu 单参考编辑（本机实测通过）**
- `assets/boogu-multi-ref.vpipeline` —— **Boogu 双参考同框（实测通过）**
- `assets/klein-ref-edit.vpipeline` —— klein 单参考编辑（未在本机实测）
- `assets/klein-multi-ref.vpipeline` —— klein 多参考合成（未在本机实测）
- `assets/qwen-image-2.1-edit.vpipeline` —— Qwen-Image-Edit 编辑（未在本机实测）
