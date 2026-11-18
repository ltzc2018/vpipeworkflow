# vpipe 流水线（pipelines/）完全手册

> 盘点时间：2026-11-18 20:10
> 范围：本机 `~/AI-Models/vpipe-workspace/pipelines/` 下**全部 77 条** `.vpipeline`
> 方法：用 `scripts/pipeline_inventory.py` 批量解析 JSON（不靠肉眼猜），生图硬约束逐条从源码 `stages/*.cc` 核出
> 机型：Mac mini M5 Pro / 24 GB / 15 核

---

## 0. 怎么跑一条流水线

```bash
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
cd ~/AI-Models/vpipe-workspace
"/Applications/Vpipe Manager.app/Contents/Helpers/vpipe" run pipelines/<文件名>.vpipeline
```

**三条通用规则**

1. **输出路径是相对工作目录的**（`out/xxx.mp4`），不是相对流水线文件。所以必须在工作目录里跑。
2. **改参数改流水线文件，不改 CLI**。所有可调项都在 `.vpipeline` 的 `config` 里。
3. **同一个 `id` 可以有多个文件**（如 `p13b-default` 有 `-r1/-r2` 两份）→ 这是**复现性实验**用的，同参数跑多次看是否逐位相同。

---

## 1. ★ 生图限制（最容易被忽略的部分）

### 1.1 硬性校验：分辨率必须是 16 的倍数

源码 `stages/generate-image-stage.cc:1106`：

```
GenerateImageStage: height/width must be multiples of 16 (got {}x{})
```

→ **写 1000×1000 会直接 fail_config 报错**，不会自动纠正。1024 / 576 / 384 / 864 / 1536 都合法。

### 1.2 尺寸推断与取整规则

**出图（`generate-image`）—— 硬失败**

| 写法 | 行为 |
|---|---|
| `width` 与 `height` **都不填** | 走 **infer**（由模型/参考图决定） |
| **只填一个** | **不算 infer**！另一个轴退回 **256** 的历史默认值 |
| 都填 | 正常指定 |

→ **要 infer 就两个都别填**；填一半是最隐蔽的坑，会得到 1024×256 的怪图。

**视频（`generate-video`）—— 自动取整 + 打印提示**

| 项 | 规则 |
|---|---|
| 画布倍数 | **32**（出图是 16）→ 源码 `kCanvasMultiple = 32` |
| 行为 | **就近取整 + 在日志打印 `960x544 -> 960x544`**（不报错） |
| 帧数 | `align_num_frames(frames, 17, 5)` → 对齐到 **17n+5** |

→ 视频侧**不会因为尺寸不规范而失败**，但会被悄悄改掉。
**必须核对日志里那行 `-> xx` 提示**，否则你以为跑的是 960×544，其实不是。

### 1.3 CFG（guidance_scale）

| 值 | 行为 |
|---|---|
| `1`（默认） | **关闭 CFG**，单次前向 |
| `>1` **且 iport1 接了负向提示词** | 开启 CFG，**每步跑第 2 次 DiT 前向**（时间翻倍） |
| `>1` 但 iport1 没接负向词 | 不会跑第二次前向 |
| `<=0` | 视为关闭（等同 1） |

源码原文（`generate-image-stage.cc:167`）：
> `1 (default) disables CFG. >1 with a negative prompt on iport1 runs a 2nd DiT pass per step`

- **Z-Image-Turbo 写 `guidance_scale = 0.0`** → 关闭 CFG，这是它 8 步 42.5 秒的原因。
- **Boogu 固定 CFG = 1**（Turbo 蒸馏版），**接了 CFG 会白跑第二次前向**。

### 1.4 步数

- **出图**：步数写在**两处**，必须一致
  （`scheduler-select.steps` 与 `generate-image.steps`）→ 本机 8 条出图流水线全部两处都有且一致。
- **视频**：只写 `generate-video.steps` **一处**即可
  → 实测 **54 条视频流水线的 `scheduler-select` 都不写 `steps`**（`scheduler-select` 默认 8，会被 `generate-video` 覆盖）。
  写两处不冲突，但**别只写 `scheduler-select` 那一处**。
- `steps <= 0` → 默认 **8**。
- **4 步适配器必须把 `generate-video.steps` 改成 4**，否则静默劣化（不报错）。

### 1.5 参考图数量的家族差异（★ 关键）

| 家族 | 参考图支持 | 证据 |
|---|---|---|
| **Krea-2** | **单参考**（硬上限） | 源码 `diffusion-conditioner-stage.cc:2845`「Krea-2 is single-reference by design… ignoring N extra reference image(s)」→ **多接会被忽略并告警** |
| **Boogu-Image-Edit** | **多参考** | 每张参考各得 144 vision tokens（grid 24×24）+ 3 deepstack |
| **Qwen-Image-Edit-2511** | 多参考 | image-aware 家族 |

**两种接法**

| 方式 | 端口 | 说明 |
|---|---|---|
| 逐张接 | `ref_image`(iport3) / `ref_image2`(iport4) | 每张**各接一个 `image-resample`** |
| 列表接 | `ref_images`(iport6) | 一个 list，顺序在 `ref_image`/`ref_image2` 之后 |

> ⚠️ **列表接法要配套 `vae-encode` 的 `images`**，让 latent 对齐。

### 1.6 ★ Boogu 图生图的三个专属坑

1. **调度器必须 `boogu_v1`**（`scheduler-select` 的 `type`），否则不对。
   `boogu_v1` 专有参数：`seq_len`（默认 4096 = 1K 方形）、`base_shift`/`max_shift`、`mu`。
   → **换分辨率要同步改 `seq_len`**，否则 mu 从错误的 token 数读取。
2. **每张参考图必须各接一个 `image-resample`**。
   `load-image` 的 oport 是 `FlexDataPayload`，直接接 `ref_image` 会报
   `FlexDataPayload vs TensorBeatPayload` 类型错。
3. **参考图走 Qwen3-VL 语义条件，不走 latent** → 不需要 `vae-encode`；
   它约束的是内容/结构，**不是逐像素复制**。
   → 参考图应**预裁成单一主体**，两栏拼图会导致脸与体型漂移（实测）。

### 1.7 图片尺寸与显存

| 项 | 值 |
|---|---|
| 峰值内存（1024²） | ~23 933 MB（**声明超物理内存但实测跑完**） |
| 关键设计 | **DiT 与 VAE 从不同时驻留**（`generate-image` 在 `vae-decode` 前释放 DiT，~3712 MB） |
| VAE decode | 1024² 峰值 ~2.8 GB |
| ANE | **M5 上几乎无收益**，官方原话「After M5 it barely moves performance」→ 本机默认关 |

### 1.8 LoRA 支持

| 模型 | LoRA |
|---|---|
| Krea-2 | `mgwr/M87`（**仅 HF 有，ModelScope 侧没有** → 需用 `krea-2-turbo-t2i-nolora.vpipeline`） |
| Boogu / Z-Image | 本机未测 |
| 通用 | `.safetensors` 可直装 LoRA 槽，**FP8 暂不支持** |

### 1.9 出图能力边界速查

| 限制项 | 值 |
|---|---|
| 分辨率 | **出图**：16 的倍数（**硬失败**）<br>**视频**：32 的倍数（**自动取整 + 日志提示**） |
| CFG | 1 = 关；>1 = 双倍耗时 |
| 步数 | 默认 8；蒸馏模型 4 步 |
| Krea-2 参考图 | **1 张**（多接被忽略） |
| Boogu 参考图 | 多张（实测 2 张） |
| Z-Image CFG | 固定 0.0（关） |
| 调度器 | simple / karras / exponential / **boogu_v1** |
| 模型来源 | **全部走 ModelScope**（本机 HF 直连不通） |

---

## 2. 全量流水线清单（77 条）

### 2.1 出图类（IMG，8 条）

| 文件 | 功能 | 规格 | 模型 / LoRA | 步数 | seed |
|---|---|---|---|---:|---:|
| `z-image-turbo-t2i.vpipeline` | **文生图（主力）** | 1024×1024 | Tongyi-MAI/Z-Image-Turbo，CFG=0 | 8 | 42 |
| `krea-2-turbo-t2i.vpipeline` | 文生图（带 M87 LoRA） | 1024×1024 | krea/Krea-2-Turbo + mgwr/M87 | 8 | 0 |
| `krea-2-turbo-t2i-nolora.vpipeline` | **文生图（无 LoRA，ModelScope 可用版）** | 1024×1024 | krea/Krea-2-Turbo | 8 | 0 |
| `boogu-image-edit.vpipeline` | **图生图（单参考，换背景）** | 1024×1024 | Boogu/Boogu-Image-0.1-Edit-Turbo，`boogu_v1` | 4 | 42 |
| `boogu-multi-ref-probe.vpipeline` | **图生图（双参考合成）** | 1024×1024 | 同上，每图各接 image-resample | 4 | 42 |
| `boogu-real-photo1-studio.vpipeline` | 图生图（真人 1 → 影棚）⚠️ 真人素材 | 576×1024 | 同上 | 4 | 42 |
| `boogu-real-photo3-beach.vpipeline` | 图生图（真人 3 → 海滩）⚠️ 真人素材 | 576×1024 | 同上 | 4 | 42 |
| `boogu-real-photo3-single-beach.vpipeline` | 图生图（真人 3 裁单人 → 海滩）⚠️ | 384×1024 | 同上 | 4 | 42 |

> ⚠️ **带 `real-photo` 的 3 条用了真人参考图，一律不进 public 仓库**（`nightly_sync.sh` 有防火墙）。

### 2.2 视频类 · 常规规格（VID，480p/544p）

| 文件 | 功能 | 分辨率 | 帧/步 | 主干 / adapter | 实测耗时 |
|---|---|---|---|---|---:|
| `h3-t2v-turbo.vpipeline` | **文生视频** | 960×544 | 120/4 | FL2VA-8bit + Turbo-LoRA v4 | 5 分 50 秒 |
| `h3-first-last.vpipeline` | **首尾帧插值** | 960×544 | 124/6 | FL2VA-8bit + Turbo-LoRA | 8 分 41 秒 |
| `h3-first-last-vertical.vpipeline` | 首尾帧插值（**竖版 544×960**） | 544×960 | 72/6 | FL2VA-8bit | — |
| `h3-ref2va-img.vpipeline` | 参考生视频（官方 ref2va-like） | 960×544 | 124/6 | Ref2VA-8bit | 12 分 54 秒 ⚠️ 无发布配置 |
| `fl2va-ref2va-like-ablation.vpipeline` | 官方 ref2va-like 对照 | 960×544 | 124/6 | FL2VA-8bit + VDN | 8 分 20 秒 |
| `pika-i2va-shop.vpipeline` | **首帧锚定 i2va** | 832×480 | 124/6 | FL2VA-8bit + Pika fl2va | 5 分 59 秒 |
| `pika-ref2va-ablation.vpipeline` | 参考生视频 A 组（有参考） | 832×480 | 124/6 | Ref2VA-8bit + Pika ref2va | 6 分 49 秒 |
| `pika-ref2va-noref.vpipeline` | 同上但**空参考对照** | 832×480 | 124/6 | 同上 | 5 分 50 秒 |
| `pika-ref2va-panda.vpipeline` | 同上但**换熊猫图（强消融）** | 832×480 | 124/6 | 同上 | 6 分 48 秒 |
| `hyperflow-ref2va-panda.vpipeline` | HyperFlow 8 步 flow-map | 832×480 | 124/8 | Ref2VA-8bit + HyperFlow | 8 分 54 秒 |
| `hyperflow-ref2va-scale0.vpipeline` | **同上但 `lora_scale=0`**（精确回到原始模型） | 832×480 | 124/8 | 同上 | — |
| `real-ref2va-photo1.vpipeline` | 真人参考生视频 ⚠️ | 832×480 | 124/6 | Ref2VA-8bit + Pika | — |

### 2.3 视频类 · 768p 高清

| 文件 | 功能 | 分辨率 | 帧/步 | shift | 适配器 | 耗时 |
|---|---|---|---|---:|---|---:|
| `p3-768p-shift6.vpipeline` | **768p 基准（官方推荐）** | 1344×768 | 124/8 | **6.0** | 8step-768p-split | 29 分 34 秒 |
| `p3-768p-shift12.vpipeline` | 只变 shift | 1344×768 | 124/8 | 12.0 | 同上 | 28 分 47 秒 |
| `p3-768p-4step.vpipeline` | **768p 4 步（最划算）** | 1344×768 | 124/**4** | 6.0 | 4step-768p-v1.2 | **13 分 26 秒** |
| `p3-768p-544p.vpipeline` | 降分辨率对照 | 960×544 | 124/8 | 12.0 | 8step | 9 分 35 秒 |
| `p9-ref2va-768p-a.vpipeline` | Ref2VA@768p 基准 | 1344×768 | 124/8 | 6.0 | ref2va-8step-768p | — |
| `p9-ref2va-768p-b-shift12.vpipeline` | 只变 shift | 1344×768 | 124/8 | 12.0 | 同上 | — |
| `p9-ref2va-768p-d-shift8.vpipeline` | shift 8.0（测台阶性） | 1344×768 | 124/8 | 8.0 | 同上 | — |
| `p9-ref2va-768p-c-multiref.vpipeline` | **768p 多参考** | 1344×768 | 124/8 | 6.0 | 同上 | 19 分 35 秒 |

> ★ **shift 规则按适配器分叉**：FL2VA 768p = 6.0；**Ref2VA 768p 上游官方 = 6.0，但本机实测 12.0 更锐**；544p/Pika/HyperFlow = 12.0。
> ★ **shift 写错完全静默**（日志恒印 12.0/3.0），无告警。

### 2.4 视频类 · 实验对照（同参数多份 = 复现性/消融）

| 文件组 | 用途 | 参数 | 关键结论 |
|---|---|---|---|
| `p13-static-shift6/12/shifter-sde.vpipeline` | 纹理沸腾（#55）复现 | 768p / 22 帧 / 8 步 | HF jitter 地板 0.0010 → 模型 0.0995–0.1293 |
| `p13b-default{,-r1,-r2}.vpipeline` | **默认调度器复现性** | 768p / 22 帧 | `autotune:false` → **逐位相同** |
| `p13b-ersde{,-r1,-r2,-r3}.vpipeline` | er_sde 调度器网格 | 同上 | 换调度器 = 换轨迹 |
| `p15-repro-af1/af2/at1/at2.vpipeline` | bit-for-bit 复现基线 | autotune 开/关 | 漂移基线：sharpness 9.1% / HF jitter 20.3% |
| `p18-euler/dmd/dmd2.vpipeline` | **采样器判决** | 768p / 22 帧 / 8 步 | `dmd` 比 `euler`：HF jitter **−12.82%**、sharpness **+10.27%**、耗时 0% |

> ★ **采样器端口在 `generate-video` 的 iport3**：`diffusion-sampler-select{method}`，
> H3 只映射 `euler`（默认）/ `dmd` / `res_multistep`；其余只 warn 并回落。
> ★ `dmd` = **每步重注噪**（x0=x+σ·v → (1−σ')·x0+σ'·n），确定性路径。

### 2.5 视频类 · 多参考组合（P1）

| 文件 | 参考构成 | 条数 | 前向行数 | 耗时 |
|---|---|---:|---:|---:|
| `p1-a-multi-ref.vpipeline` | 1 图 | 1 | 16 999 | 6 分 48 秒 |
| `p1-b-multi-ref.vpipeline` | 2 图 | 2 | 19 073 | 8 分 01 秒 |
| `p1-c-multi-ref.vpipeline` | 2 图 + 1 视频 + 1 音轨 | 3 | 36 329 | 20 分 28 秒 |
| `p1-d-multi-ref.vpipeline` | 3 图 + 1 视频 + 1 音轨 | 4 | 38 396 | 19 分 35 秒 |

> **官方端口**：多参考图接 `diffusion-conditioner` 的 **iport3/iport4**；
> 参考视频 `load-video → video-to-rgb → image-resample → temporal-stack`；
> 音频 `audio-to-pcm(32000, stereo) → temporal-stack`。
> ★ **贵的不是多一张图，是多一段视频**（加视频 ×3 耗时，加图 +6.5 %）。
> ★ 参考视频**不要上采样到输出画布**，否则参考行翻倍（官方实测 23m07s → 14m17s）。

### 2.6 实时预览类（TAE-H3，5 条 + 3 条 Pika 版）

| 文件 | 功能 | 规格 | 预览延迟 |
|---|---|---|---:|
| `h3-taeh3-preview.vpipeline` | 预览基线 | 512×288 / 39 帧 | ~20 秒 |
| `h3-taeh3-preview-abs.vpipeline` | **绝对路径喂参考图** | 同上 | — |
| `h3-taeh3-preview-dir.vpipeline` | **目录方式喂参考图** | 同上 | — |
| `h3-taeh3-preview-frames.vpipeline` | **帧序列方式** | 同上 | — |
| `h3-taeh3-preview-relfile.vpipeline` | **相对文件路径** | 同上 | — |
| `pika-i2va-preview-fast.vpipeline` | i2va 快速预览 | 512×288 / 39 帧 | **22.11 s** |
| `pika-t2v-preview-fast.vpipeline` | t2v 快速预览（对照） | 512×288 / 39 帧 | **20.26 s** |
| `pika-i2va-preview-prod.vpipeline` | i2va 生产规格预览 | 832×480 / 124 帧 | **90.33 s** |
| `relpath-check.vpipeline` | **相对路径回归检查**（与 fast 版同参数） | 512×288 / 39 帧 | — |

> ★ **五个 preview 变体是同一功能的 5 种喂图写法**（abs / dir / frames / relfile / 基线），
> 用来确定哪种最稳 → 结论是 **relfile 最稳**。
> ★ `preview` 必须接 `generate-video` 的 **oport 2**（接 oport 0 **静默失效**）。
> ★ CLI 下流水线**永不结束**（WebSocket sink），需 `ws_capture.py` 抓流。
> ★ 预览流是**两个 init 段**拼的 fMP4，必须分段解析。

### 2.7 视频续接（官方四段式）

| 文件 | 功能 | 规格 |
|---|---|---|
| `p3-ext-part1.vpipeline` | 第 1 段（FL2VA） | 832×480 / 124 帧 / 6 步 |
| `p3-ext-part2.vpipeline` | 第 2 段（Ref2VA + 上一段做参考） | 同上，16 阶段 |
| `p3-ext-part3.vpipeline` | 第 3 段 | 同上 |
| `p3-ext-part4.vpipeline` | 第 4 段 | 同上 |
| `p3-ext-concat.vpipeline` | 拼接 4 段 → `out/p3-ext-full.mp4` | 工具 |
| `p3-ext-concat2.vpipeline` | 拼接（ffv1 无损版） → `out/p3-ext-full2.mp4` | 工具 |

> ★ 官方续接四件套：`temporal-slice(start=-90)` + `audio-to-pcm(start_s=段长-3.75, duration_s=3.75)`
> + `video-ref-encoder(attach_audio=[2])` + ffv1/alac；**引导长度必须 `17n+5` 帧**。
> ★ **接缝判据必须用相位相关**，不能只靠 LFM3-VL（它会把 76px 重构误读为「自然姿态变化」）。
> ★ 实测：接缝 SSIM 0.457→0.358→0.281 → **只接得住第一处**。

### 2.8 视频超分（FlashVSR，第 6 轮新增）

| 文件 | 功能 | 输入→输出 | 帧 | 耗时 |
|---|---|---|---:|---:|
| `p22-flashvsr-upscale.vpipeline` | FlashVSR v1.1 A 臂 | 320×192 → 1280×768 | 25 | **45.5 s** |
| `p22-flashvsr-upscale-r2.vpipeline` | 同上第二跑（复现性） | 同上 | 25 | — |
| `p22c-plus-upscale-1920.vpipeline` | **FlashVSR+ Turbo 冲 1920×1152** | 480×288 → 1920×1152 | 49 | 待验 |

> ★ 几何契约：输出宽高 **128 的倍数**、帧数 **8k+1**（v1.1 ≥25）、输出 = **4× 源**、`group_size ≤ 帧数`。
> ★ 内存：1920×1152 需 ~20 GB（本机 24 GB 装不下）→ 本机目标定在 1280×768。
> ★ **判决：细节生成器 ≠ 保真放大器**（纹理 12.6× 插值，但 SSIM/PSNR 双双低于插值）。

### 2.9 模型准备类（UTIL，10 条）

| 文件 | 功能 |
|---|---|
| `prepare-minimax-h3-8bit.vpipeline` | 下载 + 8-bit 量化 FL2VA/Ref2VA（**123.6 GB → 49 分 44 秒**） |
| `prepare-minimax-h3-preview.vpipeline` | 下载 TAE-H3 预览解码器 |
| `prepare-image-models.vpipeline` | 下载 Z-Image-Turbo + Krea-2-Turbo |
| `prepare-pika-h3-flex.vpipeline` | 下载 + 注册 Pika H3 Flex（fl2va + ref2va，1 分 14 秒） |
| `register-hyperflow-ref2va.vpipeline` | 注册 HyperFlow adapter |
| `prepare-multimodal-compare.vpipeline` | 下载 LFM3-VL-2B + Qwen3.5-4B（第三方复核用） |
| `p3-fetch-768p.vpipeline` | 拉取 768p 适配器权重 |
| `p3-fetch-544p.vpipeline` | 拉取 544p 适配器权重 |
| `lfm3-vl-vqa.vpipeline` | **LFM3-VL 视频描述 / VQA 复核** |
| `qwen35-4b-chat.vpipeline` | Qwen3.5-4B 对话复核 |

### 2.10 分类统计

| 类别 | 条数 |
|---|---:|
| 出图（IMG） | 8 |
| 视频（VID） | 57 |
| 工具/准备（UTIL） | 12 |
| **合计** | **77** |

> 统计口径：`scripts/pipeline_inventory.py` 递归展开 `stages` + `subpipelines` 后按是否含
> `generate-image` / `generate-video` 分类 → 与 `pipeline_inventory.py` 输出的 TSV 逐行一致。

---

## 3. 改参数的「安全改 vs 危险改」

| 想改什么 | 安全 | 危险（静默劣化） |
|---|---|---|
| 分辨率 | 改成 16 的倍数 | 改成非 16 倍数 → **硬报错**（好） |
| 帧数 | 改成 `17n+5` | 随意改 → 与音频对不齐 |
| 步数 | 出图：两处同改（`scheduler-select` + `generate-image`）<br>视频：改 `generate-video.steps` 一处 | 只改 `scheduler-select` → 静默劣化 |
| shift | 查官方表（见技能包 `768p-adapters.md`） | 填错 → **完全静默**，日志还骗你 |
| 采样器 | `diffusion-sampler-select{method}`，只 euler/dmd/res_multistep | 用 heun/dpmpp → 只 warn 回落 |
| CFG | 出图 `guidance_scale`；视频侧看适配器 | Boogu 接 CFG → 白跑第二次前向 |
| 参考图 | 每张各接 `image-resample` | `load-image` 直连 `ref_image` → 类型错报错 |
| Boogu 调度器 | `boogu_v1` + 同步改 `seq_len` | 换分辨率不改 `seq_len` → mu 读错 |

---

## 4. 复现性纪律（做对照实验必读）

1. **固定 seed**（`generate-image` / `generate-video` 的 `seed`）。
2. **同参数多跑几份**（如 `p13b-default-r1/-r2`）→ 判断是否逐位相同。
3. **关竞速**：`autotune: false` 要在 **`generate-video` + `vae-decode` + `video-ref-encoder` 三处**都关。
4. **比帧哈希**（`framemd5`，必须 `-map 0:v`）+ 音频轨 md5。
   → **不能靠 mp4 文件哈希判断**（容器含时间戳）。
5. **报哈希必须写清聚合口径**（历史教训：同一批文件四种聚合都复现不出来）。
6. **SSIM 口径注明**：视频流直接比 vs 落盘 PNG 再比，差约 0.03（YUV 4:2:0 往返）。
   **跨像素格式比较必须用落盘口径**。

---

## 5. 已知的「静默失效」清单（最该警惕）

| # | 现象 | 后果 |
|---|---|---|
| 1 | **shift 填错** | 无告警，日志恒印 12.0/3.0 |
| 2 | **4 步适配器不把 `steps` 改成 4** | 静默劣化 |
| 3 | **`preview` 接 oport 0** | 静默无预览数据，不报错 |
| 4 | **`video-ref-encoder` 与 `generate-video` 的 `frames` 不等** | **整个请求被跳过** |
| 5 | **旧 build 遇到新 config 键** | 静默丢弃，零报错零日志，输出逐位相同 |
| 6 | **Boogu 用错调度器** | 不报错，画质异常 |
| 7 | **Krea-2 接多张参考图** | 多余的**被忽略**（有告警） |
| 8 | **CLI 下跑 preview 流水线** | 永不结束（不是失败，是设计如此） |
| 9 | **报告引用日志里的 shift 值当证据** | 证据无效（上游 #47/#55） |
| 10 | **ref_images 列表接法不配 vae-encode** | latent 不对齐 |

---

## 6. 相关文档

| 想查什么 | 去哪 |
|---|---|
| 速度与耗时 | `vpipe-能力与速度总表.md` |
| 768p 适配器与 shift 表 | 技能包 `vpipe-model-prepare/references/768p-adapters.md` |
| 采样器规格与 P18 判决 | 技能包 `vpipe-model-prepare/references/sampler-spec.md` |
| 纹理沸腾与三指标 | 技能包 `vpipe-model-prepare/references/texture-boiling.md` |
| 超分手册 | 技能包 `vpipe-model-prepare/references/relayvsr-flashvsr.md` |
| 多参考接线 | 技能包 `vpipe-reference-to-video/references/multi-ref.md` |
| 预览抓流 | 技能包 `vpipe-live-preview/references/cli-capture.md` |
| 全部实测记录 | `vpipe-H3-部署与测试报告.md` |
| 盘点脚本 | `scripts/pipeline_inventory.py`（可重跑，输出 TSV） |
