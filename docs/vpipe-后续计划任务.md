# vpipe 后续计划任务清单

> 基于 GitHub `tgo-app-dev/vpipe`（`main` @ `33cda00`，本机源码编译版 `0.1 (9db5dd7*0)`）、官方 `docs/MINIMAX-H3-zh-cn.md`、官方 26 个 release、30 条 issue，以及 YouTube/社区实测资料整理
> 生成时间：2026-11-14
> 机器：Mac mini M5 Pro / 24 GB / 15 核 / macOS 27.2

---

## 0. 先说结论：对原「仍可做」清单的修正

原清单的 6 项里，**有 2 项的判断需要修正**，1 项已经完成，1 项风险很高。

| 原清单项 | 原判断 | 修正后的判断 | 依据 |
|---|---|---|---|
| 多参考组合 | 待做 | ✅ **可做，且是最有价值的一项** | 官方 `minimax-h3-reference-to-video.vpipeline` 有完整的端口路线示例，上限 9图/3视频/3音频 |
| 锚定 + 参考图叠加 | 待做 | ⚠️ **官方设计里互斥，不是配置问题** | 官方文档明写「用了锚定帧就要放弃参考列表」 |
| HyperFlow 8 步 adapter | 待做 | ✅ **权重已下载并注册完成** | 本轮已下载 2.8 GB，4/4 校验通过 |
| 768p / 10s / 15s | 待做 | ✅ **可做，但要用 lightx2v 的 768p 专用 adapter** | 不是给 H3 换参数就行，shift 必须改成 6.0 |
| TAE 预览接进 i2va | 待做 | ✅ 可做，链路已验证 | `preview_vae` 挂在 `generate-video` 上，与 i2va 兼容 |
| 量化 Z-Image / Krea | 待做 | 🔴 **高风险，不建议做 4-bit** | 上游 issue #41：4-bit 产物直接不可用且量化报成功、零警告 |

---

## 任务 P1 · 多参考组合（商品图 + 场景图 + 动作参考视频）

**优先级：最高。** 这是带货「一物多场景」的正路，也是 Ref2VA 唯一还没被充分使用的能力。

### 目标
一次生成中同时喂：商品图（锁身份）+ 场景图（锁风格）+ 动作参考视频（锁运动），验证三者是否各司其职。

### 官方规格
- 上限：**9 张图 + 3 段视频 + 3 条音频 = 共 12 项**，且音频不能是唯一的种类
- 图片承载**主体与风格**，视频承载**运动与镜头**，音轨承载**人声或音乐**
- 单段参考视频 **2–15 秒**，总时长 ≤ **15 秒**
- 本地生成视频时长 **4–15 秒**

### 两条交付路径

**路径 A：`references` 文件列表（简单）**
```json
"references": ["product.jpg", "scene.jpg", "motion.mp4", "voice.wav"]
```
优点：简单。缺点：模型自己决定各参考的几何尺寸。

**路径 B：端口路线（可控，官方示例用这个）**
```
load-image  → image-resample(1024×1024)                              → ref1
load-image  → image-resample(1024×1024)                              → ref2
load-video  ┬→ video-to-rgb → image-resample(1344×768) → temporal-stack → ref3
            └→ audio-to-pcm(32000, stereo) → temporal-stack             → ref4
```

四个承重细节：
1. `attach_audio: [N]` —— 按**参考编号**（不是端口号）把音轨折叠到它前面那个参考上，保持 `<Video 1>` + `<Audio 1>` 配对
2. `channels: 2` —— 真正的立体声
3. `max_mb: 384` —— 124 帧 @ 1344×768 = 366 MiB，超过默认 256 MiB 会被截到 86 帧并告警
4. `reference_video_short_edge: 0` —— 参考视频保持在输出画布尺寸上，行数不翻倍（否则 14,580 → 约 2 倍）

### 执行步骤

| # | 步骤 | 产出 |
|---|---|---|
| P1.1 | 建 `multi-ref-port.vpipeline`：商品图 → ref1，场景图 → ref2，动作视频 → ref3（带音轨） | 流水线 |
| P1.2 | 准备素材：复用已验证的猫参考图 + 熊猫参考图 + 已有的 5.18s 视频 | 素材 |
| P1.3 | 跑 3 组：仅商品图 / 商品+场景 / 商品+场景+动作 | 3 支视频 |
| P1.4 | 逐组算 SSIM + LFM3-VL 语义复核（谁的身份？什么风格？动作来自哪？） | 分析表 |
| P1.5 | 写结论：**分工是否真的成立**（图锁身份、视频锁动作） | 报告章节 |

### 成功判据
- 商品图锁住主体身份，场景图锁住风格，动作视频的运镜能被复现
- 三者同时给时不互相干扰（没有"动作来自图"或"身份来自视频"的串味）

### 风险
- 参考视频的 `fps` 必须在端口上声明，否则被拒绝
- 参考视频超过 `frames` 会被截断，**而且是先缩放全部帧再截断**（低效）
- 多参考时 `reference_image_short_edge` 必须降到 1024，否则显存爆

---

## 任务 P2 · HyperFlow 8 步 adapter 对照实验

**优先级：高。** 权重已就位（`videorebirth/hyperflow`，2.8 GB，4/4 校验通过），只差跑对照。

### 关键认知（官方文档）
HyperFlow **不是 LoRA**，是「LoRA + 时间步 MLP 的一处结构改动」：
```
temb = emb(t) + gate * (emb_r(r) - emb(t))        gate = 0.25
```
每一步每行需要两个数 `(t, r)`。条件行（关键帧/参考帧）没有要去的地方，所以那里 `r == t`。

### 接线（只需改两处）
```json
"lora": "videorebirth/hyperflow",
"lora_scale": 1.0
```
- **不需要设置步数**。适配器文件里写明了蒸馏时的 sigma 网格（9 点、8 次前向），只要适配器生效，vpipe 就跑这个网格；图里的 `steps` 在此期间不被使用
- **Ref2VA 的图要用 `videorebirth/hyperflow-ref2va`** —— 同一个文件，在模型目录里登记了第二次。⚠️ **本机尚未注册这个别名，需补**
- `video_shift` / `audio_shift` 保持 **12 / 3**，与训练时一致。改成别的值会警告
- `lora_scale` 保持 **1.0**。设 0 是"精确回到原始模型"，可以同一份权重做 A/B；中间值是**未训练过的状态**

### 官方性能（M4 Pro 64GB，640×352×56 帧，3943 行）

| | 前向次数 | 每次前向 | 去噪 |
|---|---:|---:|---:|
| 原始模型 `steps: 7` | 7 | 27.7 s | 194 s |
| 原始模型 `steps: 15`（良好质量） | 15 | 27.7 s | ~415 s |
| **HyperFlow** | **8** | **30.2 s** | **241 s** |

适配器让每次前向**慢 9%**。换来的是：原始模型要 15 步以上的片段，它 8 次前向完成。

### 执行步骤

| # | 步骤 |
|---|---|
| P2.1 | 注册 `videorebirth/hyperflow-ref2va` 别名（给同一文件在模型目录登记第二次） |
| P2.2 | 同一 seed 跑两组：Pika 6 步 renoise vs HyperFlow 8 步 flow-map |
| P2.3 | 对比：耗时、前向次数、画质（逐帧 SSIM vs 参考图 + LFM3-VL 复核） |
| P2.4 | 试 `lora_scale: 0` 做同模型 A/B（验证「精确回到原始」） |
| P2.5 | 写结论：HyperFlow 在本机的性价比（相对 Pika 的 6 步 renoise） |

### 风险
- **不能同时加载两个流映射适配器**（会被拒绝）
- 和 Turbo 适配器搭配不会报错，但**也没用**（两者都是同一模型的蒸馏，会叠加）
- 官方说 HyperFlow + Sol-Attn 组合的画面质量**没测过**，要用自己熟悉的种子判断

---

## 任务 P3 · 768p / 10 秒 / 15 秒 长规格

**优先级：中高。** 官方对 768p 有专门的 adapter 家族。

### 关键认知（容易做错）
**768p 不是给 H3 换参数就行**，要用 lightx2v 的 768p 专用 adapter，并且 **shift 必须改成 6.0**。

> **shift 是适配器的一部分，不是个人偏好。** 768p 的模型文件是在 768p 上训练的适配器，蒸馏拟合的是它训练时的 sigma 网格。

### 官方 adapter 表

| adapter | partition | 步数 | shift | 备注 |
|---|---|---|---|---|
| `lightx2v/Minimax-h3-Turbo-4step-768p` | FL2VA | 4 | 6/3 | |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2` | FL2VA | 4 | 6/3 | **4 步时优先试这个** |
| `lightx2v/Minimax-h3-Turbo-8step-768p` | FL2VA | 8 | 6/3 | 上游默认选择 |
| `lightx2v/Minimax-h3-Turbo-8step-768p-split` | FL2VA | 8 | 6/3 | **优先取拆分版** |
| `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` | Ref2VA | 8 | 6/3 | 唯一需要 `video_shift: 6.0` 的 Ref2VA 适配器 |

**split 版 vs 融合版**：官方说应优先取拆分版（`-split` 后缀）。

### 时长规格
| 目标时长 | 帧数 | 说明 |
|---|---|---|
| 5.18 s | 124 | 本轮默认 |
| 10 s | 241 | 常规 |
| 15 s | 362 | 官方记载的 768p 规格 |

官方还有 `minimax-h3-extend-part1..4.vpipeline` 的**四段式长视频**方案：
- 每段 10 秒，用上一段的**末帧 + 音轨**作为下一段的参考（续接）
- 引导片段必须是从开头起能整除到 `17n + 5` 帧的长度 —— **90 帧 = 17×5+5**，这样什么都不会被丢掉。24 fps 下两秒是 48 帧，会被截成 39 帧
- 每部分用 `save-video` 的 `video_codec: ffv1` + `audio_codec: alac` 无损写出，色度不折半
- 续接提示词：`summary` 以 `[video continuation + audio reference]` 开头
- 官方提醒：**按行数平方计算，40 秒片段跑四次普通 10 秒生成更便宜**

### 执行步骤

| # | 步骤 |
|---|---|
| P3.1 | 从 ModelScope 查 `lightx2v/Minimax-h3-Turbo-8step-768p-split` 是否可用（HF 不通是已知障碍） |
| P3.2 | 若可得：跑 768p FL2VA，验证 `video_shift: 6.0` 的必要性（对比 shift 12 的画质） |
| P3.3 | 跑 15 秒（362 帧）单段生成，记录耗时与内存峰值 |
| P3.4 | 跑四段式续接（各 10 秒），验证末帧续接的跳变控制 |
| P3.5 | 写结论：本机 24GB 上 768p / 15 秒的可行性与耗时 |

### 风险
- 768p 的权重比 8-bit FL2VA 大得多，24GB 上需要确认 residency 能否扛住
- 帧数上去后耗时近似线性增长（124 帧 ≈ 8 分钟 → 362 帧可能 25+ 分钟）
- `lightx2v` 系列主要在 HuggingFace，ModelScope 是否有镜像需先确认

---

## 任务 P4 · TAE-H3 实时预览接进 i2va

**优先级：中。** 链路已验证，只是换到 i2va 流水线。

### 背景
TAE-H3 预览在 t2v 流水线上验证过（`h3-taeh3-preview.vpipeline`），i2va 是另一条链路，没验过。

### 执行步骤

| # | 步骤 |
|---|---|
| P4.1 | 在 `pika-i2va-shop.vpipeline` 上加 `preview_vae` + `preview_every` + `preview_max_edge` + `preview_frames` |
| P4.2 | 在 Web UI 里跑（`preview` 是 WebSocket sink，CLI 下不会自动结束） |
| P4.3 | 观察首帧锚定模式下预览是否正常（keyframe latent 的预览路径可能与纯 latent 不同） |
| P4.4 | 写结论：i2va 场景下"先出低清预览再出正片"是否可行 |

### 风险
- **曾出现过预览静默失效**（三种路径写法都试过、配置完全正确、日志零警告，原版重跑即好）。判定原则：配置无误时先原版重跑再改配置
- keyframe anchor 的预览可能需要额外处理，实测才知道

---

## 任务 P5 · 图像模型量化（**高风险，建议降级**）

**优先级：低 → 建议改为「先做 8-bit 验证，4-bit 不要碰」**

### 风险等级：🔴 高

上游 **issue #41** 实测（v0.1.68，M4 16GB）：
- **Z-Image-Turbo 4-bit**：1024×1024 跑 28 秒后 GPU command buffer 错误，更小尺寸直接硬挂
- **Qwen-Image-2.1 4-bit**：**静默输出全透明图**
- **量化本身报成功、日志零警告** —— 极容易误发布
- 对照实验证明 4-bit 路径本身没坏（FLUX.2 klein 4-bit 正常）—— 是特定模型族的问题

**8-bit 在 Z-Image / Krea 上没有被上游验证过。** 本轮 H3 的 8-bit 是官方支持的路径。

### 建议改为
1. **不量化图像模型**（Z-Image 31 GB + Krea 33 GB = 64 GB，但都是官方公开权重，可随时重下）
2. 如果确实需要省空间：**只做 8-bit，并且必须目检输出**（检查是不是空白/异常）
3. **4-bit 一律不做**
4. 真要省空间，优先删整个模型目录（官方公开权重，可重下），而不是量化

### 更有价值的替代：复用已有的 8-bit 量化路径
`model-quantize` 的 `target: "dit"` 路径在 H3 上已验证可用（535 tensors → 8-bit g64，259 量化 / 276 直通，82 秒）。若要量化图像模型，**用 `target: "dit"` + `bits: 8` + `group_size: 64`**，并对照官方 issue #41 的量化日志检查 tensor 数量是否合理。

---

## 任务 P6 · 上游 issue 提交（5 条）

**优先级：低但必做**（用户侧一次手动操作）

5 条已写成可直接粘贴的文件：`report/issues/issue-1.md` … `issue-5.md`。

| # | 标题 | 性质 |
|---|---|---|
| 1 | `url-files` 型模型只绑定单一 GitHub URL，受限网络下无备用通道 | feature/bug |
| 2 | `parent_model_type` 与当前 partition 不符的 LoRA 不被拒绝 | bug |
| 3 | Ref2VA partition + VDN linear branch 只警告不拒绝 | bug |
| 4 | 准备 Ref2VA 时编码器被无谓地重新量化（多出 27 GB） | feature |
| 5 | `model-fetch` 的「伴随 checkpoint 未拉取」警告不准确 | bug |

**本轮新增可提交的第 6 条**（调研中发现）：

> **issue #6：`model_variant` 的错误提示给出的字符串无法用于匹配**
> 错误提示列出 `- Edit-2511 20B [bf16 (Qwen)] type=qwen-image-edit`，但把这串**原样**填回 `model_variant` 会得到 `matches 0 of the 1 models published from ...`。
> 根因（`stages/model-catalog.cc:3546` `catalog_pick_variant`）：匹配是**逐字段**比对 `version`/`variant`/`name`/`model_type` 四个字段，**没有任何一个字段等于那个显示串**（显示串是这四项的拼接）。只有 `model_type` 能匹配上。
> 建议：错误提示应该列出**可直接使用的取值**（四个字段各自的值），而不是拼接后的显示名。

---

## 任务 P7 · 图生图链路补全（**新增，来自本轮实测**）

**优先级：中高。** 本轮发现的问题：

### P7.1 Boogu-Image-0.1-Edit-Turbo 完整下载 + 图生图出片
- 本轮已下载 6.8 GB，需确认是否完整注册
- 4 步蒸馏，是三个候选里最快的
- 接线参考官方 `qwen-image-2.1-edit.vpipeline` 的形态（但 Boogu 的 stage 名不同）

### P7.2 Qwen-Image-Edit-2511（20B）
- **完整下载需要 57.7 GB** —— 本机磁盘装不下（下载到 12 GB 时磁盘只剩 14 GiB）
- 建议：**列入"等磁盘空间充足时再做"**，本轮已主动中止并清理半成品
- 若做，必须先删 Z-Image 或 Krea 腾空间

### P7.3 FLUX.2-klein-9B（多参考合成正路）
- 官方 `klein-multi-ref.vpipeline` 是**图像侧的多参考组合**正路
- 需 4-bit 量化版本（`prepare-klein-9b-4bit.vpipeline`）
- **HF gated 模型**，需申请权限；本机 HF 不通 → 先确认 ModelScope 有无镜像
- 若 klein 不可得，**用 Boogu 或 Z-Image + image-resample 做两图合成的近似**（能力弱于 latent 参考，但可跑通）

---

## 执行顺序建议（按机器空闲时段）

| 优先级 | 任务 | 预估耗时 | 依赖 |
|---|---|---|---|
| **1** | P2 HyperFlow 对照 | ~30 分钟（两支视频 + 分析） | 权重已就位；需先注册 ref2va 别名 |
| **2** | P7.1 Boogu 图生图出片 | ~15 分钟 | 下载已完成 |
| **3** | P4 TAE 预览接 i2va | ~15 分钟 | 需 Web UI 手动操作 |
| **4** | P1 多参考组合 | ~60 分钟 | 素材已有 |
| **5** | P3 768p / 长规格 | ~2 小时 | 需先确认 lightx2v 在 ModelScope 可用 |
| **6** | P7.3 klein 多参考 | ~30 分钟 | 需确认 gated 模型可达 |
| **7** | P5 图像量化 | **建议跳过** | 高风险 |
| — | P6 提交 issue | 用户手动 | 文档已备好 |

---

## 通用注意事项（每次任务都要遵守）

1. **重任务串行**。本轮实测：并行下载 66 GB 模型时，同期跑的生成流水线被杀掉（日志一切正常后无错消失）。下载结束后重跑即通过。
2. **磁盘下限 15 GiB**。低于这个数就要先清理。本轮实测下载到 14 GiB 时已很紧张。
3. **每个生成任务结束后立刻抽帧目检**，不要只看日志。日志正常 ≠ 画面正常。
4. **固定 seed**，便于对照。
5. **改完配置先核对四个必写项**：`save-video` 的 `output_url`、两路输入边、两个 stage 的 `frames` 一致、`i8_gemm: true`。
6. **每个结论都要有量化证据**（SSIM/PSNR + 第三方模型复核），不要只靠目视。
