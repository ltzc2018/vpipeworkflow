# Boogu-Image-0.1-Edit-Turbo 图生图（vpipe 本机实测）

> 实测日期 2026-11-14 · 机器 Mac mini M5 Pro / 24 GB / 15 核 · vpipe 源码编译版 `0.1 (9db5dd7*0)`
> 权重 `Boogu/Boogu-Image-0.1-Edit-Turbo`（ModelScope，35.8 GB，30 个文件全部校验通过）

## 一句话结论

**这是本机目前最快、且实测可用的图生图路径。** 1024×1024 编辑出片 **32.6 秒**，
384×1024 竖版 **17.6 秒**，**两张参考图同时给也能跑**（各 144 个视觉 token）。

它与 klein / Qwen-Image-Edit 的根本差别：**参考图走 VLM 语义条件，不走 latent**。

---

## 1. 三条已验证路径的机制对照

| | FLUX.2-klein-9B | Qwen-Image-Edit-2511 | **Boogu-Image-0.1-Edit-Turbo** |
|---|---|---|---|
| 参考图进入方式 | **latent**（`vae-encode` → 端口 5/6） | VLM + latent 双路 | **只有 VLM**（无 latent 通路） |
| 条件器 | CLIP/T5 | Qwen2.5-VL | **Qwen3-VL（`mllm/`，16 GB）** |
| 参考图分辨率 | 由 `image-resample` 决定 | 同 | **由 VLM 处理器决定**：`vl_long_edge` 默认 768、`vl_pixel_budget` 147456 px |
| 多参考 | 支持（端口 5/6 或 `ref_images` 列表） | 支持（`ref_image` + `ref_image2`） | **支持**（`ref_image` + `ref_image2`，实测两只动物同框） |
| 步数 | 4 步（Turbo） | 20 步 | **4 步 DMD 蒸馏** |
| CFG | — | 需 negative prompt | **CFG = 1（关闭）**，不要接 negative |
| 调度器 | simple/karras | simple | **`boogu_v1`**（见 §3） |
| 本机实测耗时 | 未装 | 装不下（57.7 GB） | **17.6–32.6 秒 / 张** |

**结论**：klein 是 gated 模型（HF 不通）、Qwen-Image-Edit-2511 装不下 24 GB 机器，
**Boogu 是本机唯一跑通的图生图路径**，而且实测能力比预期强。

---

## 2. 完整流水线（单参考图）

来自 `assets/boogu-image-edit.vpipeline`，骨架与官方 `qwen-image-2.1-edit.vpipeline` 同构：

```
model-select(hf_dir="Boogu/Boogu-Image-0.1-Edit-Turbo")
load-ref ──→ ref-resample ──┬──→ diffusion-conditioner[3] (ref_image)
                            └──→ vae-encode → generate-image[5] (ref_latent0)   ← Boogu 其实用不到
text-prompt ──────────────────→ diffusion-conditioner[0] (prompt)
boogu-image-model-config ────→ diffusion-conditioner[5] + generate-image[7]
scheduler-select(boogu_v1,4) ─→ generate-image[4]
diffusion-conditioner[0] ─────→ generate-image[0]
generate-image[0] → vae-decode → save-image(path="out/xxx.jpeg")
```

**与 klein / Qwen 的三点差异（最容易踩）**

1. **必须接 `boogu-image-model-config`**，而且要**同时接到 `diffusion-conditioner` 的 iport5 和
   `generate-image` 的 iport7**。前者给 VLM 的 `vl_*` 边界，后者给 DiT 读 family。
   少接任何一个：conditioner 会退到家族默认值，DiT 会打印
   `the model_config beat is for the 'boogu-image' family but the resident checkpoint is ...`。
2. **调度器必须用 `type: "boogu_v1"`**。Boogu 的 sigma 约定是**反的**（0 = 噪声，1 = 干净），
   用默认的 `simple` 会采样到反方向去。用 `boogu_v1` 时日志会打印
   `scheduler = boogu_v1 (4 steps, shift 1.15 exponential, rho 7)`。
3. **不需要 `vae-encode`**。Boogu 的 DiT 没有任何 `ref_latent` 通路
   （`generative-models/boogu/metal-boogu-transformer.cc` 里 grep 不到 `ref_latent`），
   参考图**只**通过 Qwen3-VL 的视觉塔进入条件。

---

## 3. `boogu_v1` 调度器的四个旋钮

`scheduler-select` 在 `boogu_v1` 模式下额外接受：

| 键 | 默认 | 含义 |
|---|---|---|
| `seq_len` | 4096 | 读 sigma 网格的**静态** token 数（= 1K 方形）。checkpoint 的 `scheduler_config.json` 就是 `seq_len: 4096` |
| `base_shift` | 0.5 | base_seq 处的 mu |
| `max_shift` | 1.15 | max_seq 处的 mu |
| `base_seq` / `max_seq` | 256 / 4096 | 固定写死，改不了 |

**`seq_len` 是静态的**（checkpoint 里 `dynamic_time_shift: false`），所以
**输出改成竖版不会让 mu 跟着变** —— 这是与「动态分辨率」模型的差别，别指望换尺寸自动获得正确的时间偏移。

---

## 4. 实测结果

| # | 参考图 | 输出 | 耗时 | 结果 |
|---|---|---|---|---|
| 1 | `ref-cat.png`（橘猫 + 牛仔衬衫） | 1024×1024 | **32.6 s** | ✅ 猫的身份/虎斑纹/绿眼/深蓝衬衫铜扣全保留；背景按提示词换成霓虹雨夜巷 |
| 2 | `ref-photo1-portrait.jpg`（商业写真） | 576×1024 | **25.7 s** | ✅ 同一人物、深蓝白拼上衣 + 深蓝百褶裙 + 圆形金扣全保留；背景换成浅灰无缝影棚 |
| 3 | `ref-photo3-stage.jpg`（**两栏拼图**） | 576×1024 | 19.0 s | ⚠️ 服装/粉色 preserved，但**脸与体型漂移**（见 §5） |
| 4 | `ref-photo3` 裁出的**单人主体** | 384×1024 | **17.6 s** | ✅ 姿态、粉色比基尼（含白色滚边）、**粉色口罩**、亮片高跟鞋全部保留；背景换成金色海滩 |
| 5 | `ref-cat.png` + `ref-panda.png`（**两张**） | 1024×1024 | **26.1 s** | ✅ 猫与熊猫同框，各自毛色花纹保留；日志 `reference 0 -> 144 vision tokens` / `reference 1 -> 144 vision tokens` |

### 内存画像（24 GB 机器）

```
memory-plan (generate-image): peak 23933 MB at 'vae-decode' streaming
memory-plan (vae-decode):    peak 27645 MB
```

**声明峰值超过物理内存**，但实测能跑完：DiT（19 GB）在去噪前被释放，
VAE 解码时只剩 ~3.7 GB。日志明写：

```
GenerateImageStage('generate-image'): freeing the Boogu-Image DiT for the 1024x1024 vae-decode (~3712 MB)
```

这就是 vpipe 的 **memory-bounded** 设计：DiT 与 VAE **从不同时驻留**。

---

## 5. 最重要的实测教训：参考图必须先裁成「单一主体」

第 3 组与第 4 组用的是**同一张照片**（`ref-photo3-stage.jpg`），只是一张是整张拼图、
一张是预先裁出的单人。**结果差距是数量级的**：

| | 整张拼图（1440×2560，两栏） | 预裁单人（520×2400） |
|---|---|---|
| 服装 | ✅ 粉色比基尼 | ✅ 粉色比基尼 + 白色滚边 |
| 姿态 | ❌ 变成正面站立 | ✅ 侧身、双手抱拳于胸前 |
| 配件 | ❌ 丢失 | ✅ **粉色口罩**保留、亮片高跟鞋保留 |
| 脸 | ❌ 变成另一张脸 | ⚠️ 仍是漂移（见下） |
| 体型 | ❌ 明显「美颜化」 | ⚠️ 轻微漂移 |

**原因**：VLM 看到的是**两栏拼图**，于是把两个主体理解成「一个人 + 场景」，
输出时就必然在两者之间折中、并且重画体态。

**操作准则**：

1. 电商/写真参考图**先裁成单人单幅**，再喂给 Boogu；
2. 裁完的图**比例要贴近目标画幅**（本例 520×2400 ≈ 0.217，输出给 384×1024 ≈ 0.375，用 `fit: "pad"` 留白保住全身）；
3. 用 `fit: "pad"` + `pad_color`（白色或与背景同色）保住全身，别用 `fit: "crop"`——
   `crop` 在这种超长比例上会**直接切掉头或脚**。

### 仍然存在的漂移

**Boogu 会「美化」人像**：脸型偏向了模型自身的审美，体型更纤细，肤色偏亮，
连发色都会从深黑漂到浅棕。**服装颜色、款式、配件、姿态是可靠的；面部身份不可靠。**

**实操建议**：
- 商业写真的**换背景/换场景** → Boogu 完全够用（服装与姿态保真度实测很高）；
- 需要**脸完全一致**（同一张脸出现在不同图里）→ 走 `vpipe-first-frame-to-video` 的
  首帧锚定（SSIM 0.9505），或者等 Qwen-Image-Edit-2511 / klein 就位。

---

## 6. 多参考图接法（实测可行）

**Boogu 原生支持两张参考图**，不需要 latent：

```
load-ref-1  → ref-resample-1 ─→ diffusion-conditioner[3]  (ref_image)
load-ref-2  → ref-resample-2 ─→ diffusion-conditioner[4]  (ref_image2)
```

**坑**：`load-image` 的 oport 是 `FlexDataPayload`，而 `diffusion-conditioner` 的
`ref_image` 要 `TensorBeatPayload` —— **直接接会报类型不匹配**：

```
[WARN] PipelineRuntime: cannot launch '...': payload type mismatch on edge
load-ref[1] -> diffusion-conditioner[4]: producer FlexDataPayload vs consumer TensorBeatPayload
```

**必须给每张参考图各接一个 `image-resample`**，`load-image` 的 `url` 数组可以有多个元素
（`url: [a.jpg]` 出 oport0，`url: [a.jpg, b.jpg]` 出 oport0/oport1），
但多出来的 oport 仍是 FlexData，**过不了类型检查**。

**Boogu 不走 `ref_images` 列表端口**（那是给 Qwen-Image-Edit-2511 那种多参考族用的），
它走 `ref_image` + `ref_image2` 两个独立端口，每张图各 144 个视觉 token、各 3 层 deepstack。

---

## 7. 提示词写法

Boogu 的模板是 `kBooguTi2i`（图像接地时自动切换），提示词就是**一条编辑指令**：

```
[对参考图做什么] + [要保留什么]
```

实例（本机实测通过）：

```
Keep the same woman, the same face, the same hairstyle and the exact same outfit and colors.
Place her in a clean high-end e-commerce studio with a soft light grey seamless backdrop,
soft even key light, natural skin texture, full body visible, centered.
Commercial fashion product photography, sharp focus.
```

```
Replace the background with a neon-lit rainy cyberpunk alley at night, keep the same cat,
same fur pattern, same pose and framing. Photorealistic, sharp focus, moody teal and magenta rim light.
```

**要点**：
- 必须**逐项点名要保留的东西**（服装、配件、姿态），否则模型会顺手改掉；
- **不要接 negative prompt、不要设 `guidance_scale > 1`**：Turbo 蒸馏版固定 CFG = 1，
  接了 negative 会触发第二次 DiT 前向，白白翻倍耗时且 Turbo 的 CFG 路径没训过；
- 不需要 `--preview` 之类后缀（那是 Krea-2 的 LoRA 约定）。

---

## 8. 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `payload type mismatch ... FlexDataPayload vs TensorBeatPayload` | `load-image` 直连 `ref_image` | 中间加 `image-resample` |
| 画面全黑 / 全透明 | 参考图没进条件器 | 查日志有没有 `reference 0 -> N vision tokens` |
| 主体/姿态完全不像参考图 | 参考图是多主体拼图 | 预先裁成单人单幅（§5） |
| 人物被「美颜」 | Boogu 的固有倾向 | 接受；或换首帧锚定链路保脸 |
| `the model_config beat is for the 'boogu-image' family but ...` | `boogu-image-model-config` 没接到 `generate-image` 的 iport7 | 补上该边 |
| 采样结果反向 / 一片噪点 | 调度器没用 `boogu_v1` | `scheduler-select.type = "boogu_v1"` |
| 首次启动加载 mllm 很久 | 16 GB 的 Qwen3-VL 要读完 | 正常，约 30–60 秒 |

---

## 9. 相关文件

- `assets/boogu-image-edit.vpipeline` —— 单参考图编辑（本机实测通过）
- `assets/boogu-multi-ref.vpipeline` —— 双参考图同框（实测通过）
- `references/boogu-edit.md` —— 本文件
- 上级：`vpipe-text-to-image`（同模型的文生图分支）、`vpipe-model-prepare`（权重准备）
