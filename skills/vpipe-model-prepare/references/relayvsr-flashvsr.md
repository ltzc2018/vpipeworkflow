# RelayVSR / FlashVSR —— vpipe 原生 Metal 视频超分（第 4 轮 · 2026-11-18 04:30 登记）

> **来源**：上游 `tgo-app-dev/vpipe` `main` @ `4dc36b7`（2026-11-16）的 `docs/RELAYVSR.md`（379 行）
> + `docs/pipelines/{prepare-relayvsr,relayvsr-upscale,flashvsr-*}.vpipeline`（5 条）
> + 仓库树扫描（41 个 relayvsr/flashvsr 相关文件）
> + LightX2V 官方 `scripts/relayvsr/README_zh.md`（ModelTC/LightX2V）
> + Comfy-Org PR #17511（2026-11-05 合并，commit `2f89433`）
> + Comfy-Org/RelayVSR 模型卡 + ModelScope `Comfy-Org/RelayVSR`
>
> **状态：本机未测（磁盘阻塞 + 本地 build 无此 stage）**。以下全部是**文档转述**，不是本机实测。

---

## 1. 一句话

**vpipe 上游已经自带一条原生 Metal 的视频超分链路**（RelayVSR 4× 与 FlashVSR+ 4×），
全程在设备上跑、不经过 Python、权重当纯数据读 —— 这是把 **768p H3 出片**继续推到
**1080p / 1440p / 4K** 的**第三条路线**（前两条是「直接生成高分辨率」与「云端 API」）。

**上游 `main` 已有，本机 `33cda00` 没有**（RelayVSR 的 commit `81cd674` 是 2026-11-14，晚于本地树的 2026-11-13）。

---

## 2. 两个模型家族（别混）

| | **RelayVSR** | **FlashVSR+** |
|---|---|---|
| 输出尺寸 | **精确 4×** 输入 | 4×，但对齐到 **128 像素网格** |
| 图结构 | **一个 stage**（`relayvsr-upscale`） | source encoder + `generate-video` + `vae-decode`（三个 stage） |
| 显存 | 更大（5B 关键帧模型 + 其 KV ring） | 更小 |
| 延迟 | 一帧最多晚 `window−1` 帧离开 stage | 一次一个 chunk |

- **RelayVSR** = 论文 *RelayVSR: Large-Small Model Collaboration for Efficient Real-World
  Video Super-Resolution*（arXiv 2609.37850），权重 `kopper/RelayVSR`（Apache-2.0）。
  - **大模型**：5B 参数的扩散 Transformer（Wan 2.2-TI2V-5B 形状），**重训为一步**输出
    一个锐利 latent；**每 15 帧才跑一次**。
  - **小解码器**：**32M 参数**，把**每一帧**直接变成它的 4× 帧（RGB 直出）。
  - **没有 VAE、没有文本编码器** —— 关键帧模型的文本上下文是 checkpoint 里内置的常量。

---

## 3. ★ 内存账（本机 24 GB Mac 的可行性判定）

上游给的表（每格都对着 GPU 实际峰值分配核过）：

| 输入 | 输出 | KV ring | 其他工作集 | **含权重合计** | 24 GB Mac |
|---|---|---|---|---|---|
| 320×180 | 1280×720 | 1.3 GB | 0.2 GB | **9.9 GB** | ✅ |
| 480×270 | 1920×1080 | 2.8 GB | 0.5 GB | **11.7 GB** | ✅ |
| 640×360 | 2560×1440 | 4.9 GB | 1.0 GB | **14.3 GB** | ✅ |
| 854×480 | 3416×1920 | 8.8 GB | 1.7 GB | **18.9 GB** | ✅ |
| 960×540 | 3840×2160 | 11.2 GB | 2.2 GB | **21.8 GB** | ✅（紧） |
| 1280×720 | 5120×2880 | 19.8 GB | 3.9 GB | **32.0 GB** | ❌ |

- 权重：**8.4 GB**（`fast` / `token` int8 档在 M5 上只要 **4.3 GB**）。
- **磁盘：10.2 GB**（`wan.safetensors` 10.1 GB + `flash.safetensors` 128 MB）。
- 关键帧模型的权重**整体驻留**（不做 block streaming）→ 16 GB Mac 只能跑 320×180 级别。
- **★ 坑：`output_width` / `output_height` 缺省是 0，而 0 表示「按 3840×2176 规划」**
  → 也就是按上表 **21.8 GB** 那行预订！**必须显式写成真实输出尺寸**，
  否则一次小图任务也会按 4K 规划、在启动时告警「可能装不下」。
  两个值要么都给要么都不给，各须是 32–32768 的 4 的倍数。

### 拒绝机制（上游明确写了「宁可不跑也不换页」）
1. **启动时**：若给了 `output_width/height` 而需求超过 macOS 给进程的 GPU working set
   → 直接报错，**权重都不读**。
2. **第一帧时**：若在其它 stage 加载后剩下的内存里装不下 → 报错。
两种情况都会归还全部预订并让流水线结束（无输出帧）。

---

## 4. 速度（模型时间，16 帧窗口平均）

| 输入 → 输出 | M4 Pro | M5（基础版 16 GB Air） | M5 Max |
|---|---|---|---|
| 320×180 → 1280×720 | 0.23 s/帧 | 0.27 s/帧\* | **0.030 s/帧** |
| 480×270 → 1920×1080 | 0.51 s/帧 | — | **0.063 s/帧** |
| 624×360 → 2496×1440 | 0.91 s/帧 | — | **0.109 s/帧** |
| 960×540 → 3840×2160 | — | — | **0.263 s/帧** |

\* 基础版 M5 的数字是「注意力搬上矩阵核」之前测的，**已过时**。

M4 Pro 上 624×360 的分解：**关键帧 5.3 s（每 15 帧一次）/ 预热 0.26 s / 每帧 0.49–0.54 s**；
**整个图（48 帧）57 s = 1.19 s/帧**（含首个关键帧、末尾残窗、前后解码编码）。

**⚠️ 对本机的意义（推算，非实测）**：本机是 **M5 Pro / 24 GB**，
M4 Pro 的 0.51 s/帧（480×270）大致可作上界 → **1080p 超分 ≈ 0.5 s/帧**。
而本实验室 P3 实测 **768p 原生生成 = 29 分 34 秒 / 124 帧 = 14.3 s/帧**。
⇒ **「768p 生成 + RelayVSR 4×」在时间上完全不可行（768p 的 4× 需要 32 GB Mac）；
   但「544p 或 480p 生成 + RelayVSR 4× → 1080p/1440p」在时间与内存上都可能成立** —— 待测。

---

## 5. 加速开关（本机是 M5，重点看这两个）

| 开关 | 默认 | 作用 | 本机相关 |
|---|---|---|---|
| `i8_gemm` | off | 两个模型的 block 投影走 int8 GEMM（**M5 及以后**） | ✅ 本机适用 |
| `i8_gemm_tier` | `accurate` | `accurate`（按 64 组量化，权重 8.4 GB）/ **`fast`**（int8 驻留 512 组旋转，**4.3 GB**）/ **`token`**（每输出通道一个 scale，旋转，**4.3 GB**，最快）/ `token_plain`（不旋转，**明显更不准**） | **`token` 是推荐档** |
| `sage_attn` | off | 注意力的 QK 乘积走 int8（**M5 及以后**） | ✅ 本机适用 |
| `sage_pv8` | off | 连 P·V 也走 int8 | ✅ 适用 |
| `ane_ffn` | off | 用 Neural Engine 分担 FFN 行（**M4**） | ⚠️ **M5 Max 上上游实测「两边都不划算，保持纯 GPU」** |
| `ane_rows` | 0 | ANE 分担的行数比例 | 本机 `ane_ffn` 默认 false（第 3 轮续作实测本机 `ane_ffn` 惰性） |
| `window` | 16 | 关键帧间隔 = `window − 1` 帧；2–64。越大越快（少跑关键帧模型）但更依赖小解码器 | |
| `seed` | 42 | 关键帧噪声：**torch 的 CPU 正态抽样**（release 用 CUDA 抽样，所以**两边结果不同**） | ★ 见 §7 |
| `output_dtype` | `auto` | `auto` 跟随输入；`u8` 按 release 的 `(v+1)×127.5` 截断；`f32` 给 [0,1] 不截断 | |
| `autotune` | on | **`accurate` 档的 kernel tuner 是否测量。关掉 → 一次运行精确复现** | ★ 与第 3 轮续作 P15 同一开关族 |

**M5 Max 实测加速（模型时间）**：`i8_gemm token` 让关键帧快 **1.55×**（228→136 ms @320×180），
整窗快 1.25×；`sage_attn + sage_pv8` 让 960×540 的窗口注意力 162 ms vs 277 ms
（但**单帧只快 2–4%**，因为每帧都要把 4 帧的 K/V 重新量化，抵消了收益）。

**精度代价（相对 release 自己 bf16 误差的倍数，最坏值）**：

| 档 | 关键帧 | 一帧 | 仅解码器 |
|---|---|---|---|
| 全关 | 1.05× | 0.95× | 0.20× |
| `i8_gemm accurate` | 1.31× | 1.03× | 0.32× |
| `i8_gemm fast` | 1.36× | 1.16× | 1.20× |
| `i8_gemm token` | 1.51× | 1.21× | 1.19× |
| **`i8_gemm token_plain`** | **3.91×** | **3.10×** | 1.62× |
| `sage_attn` | 1.19× | 1.10× | 1.15× |
| `sage_attn + sage_pv8` | 1.73× | 1.31× | 1.15× |

⇒ **`token_plain` 是明确的坑**，别用。`accurate`/`fast`/`token` 都还在 release 自己的 bf16 误差量级内。

---

## 6. 精度（上游拿 fp32 重述版当基准，2 段真实片子）

| | vpipe | release 的 bf16 |
|---|---|---|
| 解码器（喂 fp32 关键帧） | **0.07%** | 0.50–0.52% |
| 一个关键帧 | 2.2–2.7% | 2.2–2.7% |
| **整条流** | **0.59–0.77%** | 0.80–0.92% |

→ **vpipe 的移植比 release 自己的 bf16 还准**（解码器跑 f16，激活值都在 20 以下）。
关键帧模型跑 bf16，与 release 相同。

---

## 7. ★ 与本实验室既有结论的三条交叉

1. **`autotune` 开关再次出现**：RelayVSR stage 也有 `autotune`（默认 on），
   上游原文「**关掉 → 一次运行精确复现**」。
   ⇒ 与第 3 轮续作 P15 的发现**同族**：**vpipe 的不可复现性普遍来自内核竞速**，
   而**关掉竞速既更可复现、又更快**（P15 实测 −2.2%；RelayVSR 的竞速占比上游未给数）。
   ⇒ **纪律不变：任何新 stage 第一次跑，都要先把 `autotune: false` 显式写进配置。**
2. **σ 网格 / 采样器不是唯一解**：上游 iport 文档明确「minimax-h3 的网格不是 spec 的，
   而是 model-config 源的（`sigmas`，或 `steps` 与两个 shift）」——
   与第 3 轮续作固化的 σ 网格闭式公式**完全一致**。
3. **「换 shift = 换场景」这条纪律对换采样器同样适用**：换采样器会换 σ 轨迹，
   所以任何「A 采样器 vs B 采样器」的对照都**不能**表述成「同一场景的画质对比」，
   只能表述成「两条不同采样轨迹的对比」。

---

## 8. 权重与获取（★ 本机 HF 直连不通，全走 ModelScope）

| 用途 | 文件 | 大小 | 来源 |
|---|---|---|---|
| RelayVSR 4× 关键帧模型 | `wan.safetensors` | 10.1 GB | `kopper/RelayVSR`（HF） |
| RelayVSR 4× 解码器 | `flash.safetensors` | 128 MB | 同上 |
| **RelayVSR 原生 2×** | `wan_x2.safetensors` + `flash_x2.safetensors` | ~10 GB + 小 | `lightx2v/RelayVSR_X2`（HF，2026-10-29 发布） |
| Comfy-Org 重打包（4 个文件） | `relayvsr_x4_int8_convrot.safetensors` / `relayvsr_x2_lightx2v_int8_convrot.safetensors` / `relayvsr_flash_vae_x4_fp32.safetensors` / `relayvsr_flash_vae_x2_fp32.safetensors` | 合计 ~5.3 GB（int8） | HF `Comfy-Org/RelayVSR` / **ModelScope `Comfy-Org/RelayVSR`（10.58 GB，2026-11-12 更新）** ✅ |

- vpipe 的模型浏览器**按 checkpoint 自己元数据里的格式标识识别**
  （`refvsr-wan-v1` / `refvsr-flash-v1`）→ 手工拷的副本也能认；
  把两个文件放**同一个目录**并把 `hf_dir` 指过去即可。
- **★ `model_cls` 与权重必须配对，混用直接报错**（LightX2V runner 会校验格式、倍率与关键结构）：
  - `relayvsr_x4` → `wan.safetensors` + `flash.safetensors`，`sr_ratio` 接受 `[1, 4]`，**内部按 4× 计算再缩**；
  - `relayvsr_x2` → `wan_x2.safetensors` + `flash_x2.safetensors`，`sr_ratio` 接受 `[1, 2]`，**内部按 2× 计算**；
  - 低于原生倍率时：先做原生推理，再**带抗锯齿的 bicubic** 缩放；
  - 输出宽高向下取整，**为兼容 YUV420 再对齐到偶数**（最小 2 像素）。
  - 配置后缀必须与 `model_cls` 对应：`_x4` / `_x2`。
- **`vpipe` 侧的限制**：上游 issue **#59**（2026-11-16 更新，0 回复）明确写着
  **「现有阶段只接受 `upscale_factor=4`」**，请求支持原生 2× checkpoint。
  → **vpipe 的 RelayVSR stage 目前只有 4×；2× 要么等上游，要么用 ComfyUI 那条路。**

---

## 9. ★ ComfyUI 侧生态（另一条可走的路，与 vpipe 并行）

| 事实 | 日期 | 来源 |
|---|---|---|
| Comfy-Org 把 RelayVSR 打进 ComfyUI 核心（PR #17511，commit `2f89433`） | 2026-11-05 | artrealmai / Comfy-Org |
| 核心节点：`RelayVSRConditioning`（正条件 + 空 latent）与 `VSRDecode`（latents + 低清帧 → 帧，解码器残差上带 **detail** 增益） | 2026-11-05 | 同上 |
| 依赖 `comfy-kitchen` 的 `window_attention`；要求 ComfyUI **≥ v0.45.0** | 2026-11-05 | nextdiffusion |
| 架构：**Wan2.2 5B 每 15 帧跑一步**，Flash 解码器补中间帧；窗口因果注意力看最近 4 个关键帧，逐层 int8 K/V 缓存 | 2026-11-05 | 同上 |
| `relayvsr_x2_lightx2v_int8_convrot.safetensors` = 10.1 GB Wan 主模型 + 127 MB 紧凑解码器 | 2026-11-05 | newsnix |
| **ModelScope `Comfy-Org/RelayVSR`**：10.58 GB，2026-11-12 更新 | 2026-11-12 | ModelScope ✅ **本机可下的第三方通道** |

**⚠️ 2× 与 4× 的实测分歧（社区互相矛盾，必须两条都记）**
- ULL Studio（note.com 对比）：**2× 变体在嘴部区域崩坏、头发边缘出白晕** →
  建议**即使只要 2× 也先 4× 再缩**（两者耗时几乎相同，缩过的 4× 比 SeedVR2 的 2× 还细）。
- newsnix：2× 是「四分之一的像素算力」，且 LightX2V 的官方基准就是 **MiniMax H3 输出**
  （1024×768 无人机屋顶 @24fps，对比 bicubic / FlashVSR+Turbo / Open-H3-Regenerate-2K）。
- AIwood（B 站，2026-11-07）：`detail` 在 **VSRDecode 节点内**（不在模型加载器里）；
  2× `detail 1.0` 偏硬偏锐、`detail 0.5` 偏柔和；4× `detail 0.7` 质感较好但文件很大；
  **768P 片段 2× 采样约 8 秒多、4× 约 30 多秒**；
  **「变清楚」≠「瑕疵被修复」** —— 高动态片段的像素化**不会**被这一步解决；
  且这个过程**会重绘画面**（面部噪点减少、皮肤更光滑、发丝与衣物细节改变）。
  ⚠️ 该文自述**未核验**下载目标/依赖/安装目录，耗时数字为作者自测、无完整硬件条件。

**论文出处**（补，第 4 轮检索）：中国科大团队，arXiv **2609.37850**（2026-09-29 上传），
方法名 **Sparse Generative Relay**：大的 Wan 系模型只在**稀疏关键帧**上出参考 latent，
小的 Dual-Memory Video Transformer 重建所有中间帧（靠参考帧 + 近期上下文）。
训练用 **VARO**（RL 信号直接作用在「小网络拼出的最终视频」上，而不是只看关键帧好不好看）——
上游文档转述的「一个参考帧出错会被继承并扩散」正是这个 RL 目标要治的病。
论文数字（**单张 A100 80GB，1080p，双端点，15 帧间隔**）：
RelayVSR **29.29 FPS / 13.82 GB 峰值 / 首帧延迟 0.327 s**；
FlashVSR-Tiny 同条件 **7.80 FPS / 24.447 GB / 2.83 s** → **约 3.75× 速度、约 43% 显存**。
⚠️ **论文里最快的那个模式（1080p @ 35.89 FPS）尚未发布**（社区 2026-10-29 的 GitHub issue 在问何时放）。

**★ 社区 5090 实测（与本实验室分辨率完全对上）**：
BennyDaBall，2026-11-05 22:35 UTC，RTX 5090，热机，3 次取中位，
**124 帧、1344×768 → 2688×1536**：RelayVSR **5.8 s / 11.6 GB 显存**；
对照 RTX VSR **1.3 s / 2.9 GB**；**「detail」相对朴素 2× 放大 = 4.8× vs 2.7×**；
**「flicker 相对草稿」= 0.98 vs 1.18**。
⇒ **1344×768 正是 H3 768p 的原生输出尺寸** → 这条数据直接对应本实验室的 768p 产物。

**★ 零下载试用通道（★ 本机磁盘 5.6 GiB 阻塞下的唯一可行入口）**：
**Hugging Face Space `Upsampler/relayvsr`**（2026-11-07 出现）——
免费档、接受**约 10 秒以内**的片段、可选 2× 或 4×，跑在 HF 共享免费 GPU 上（**要排队**，
社区称「不保证每次都能出图」）。→ **本实验室可以先用它做「RelayVSR 到底补不补细节」的廉价预判**，
再决定要不要为 10.2 GB 权重腾磁盘。⚠️ 社区另提到同日有一个 **RelayVSR 进度显示崩溃**的 bug 报告。

**★ 社区给的一条可量化预言（★ 本实验室正好能测）**：
fervorcreativeai 建议「逐帧看纹理**跨越一个重绘关键帧时**是否变化；
**如果 detail 以某个节奏脉动，那就是接缝**」。
RelayVSR 的关键帧间隔 = `window − 1` 帧（默认 **15**）→ **纹理沸腾/脉动应当呈现 15 帧周期**。
⇒ 这给了本实验室一个**明确的判据**：对超分后的片算 HF jitter 的**周期性**（若纹理脉动以 15 帧为周期
则是超分接缝伪影，若无周期则是生成端的纹理沸腾）。**这是 P22 的核心度量设计。**

**LightX2V 官方 runner 的执行模式**：`relayvsr_x4.json`（权重常驻显存）/
`relayvsr_x4_block_offload.json`（Wan 按 block 卸载、Flash 常驻）/
`relayvsr_x4_sp.json`（双卡序列并行）；2× 有对应的 `_x2` 配置。
默认都开编译与预热（可关）。

---

## 10. ★★ FlashVSR / FlashVSR+：**本地 build 已经有了**（第 4 轮实测更正）

**这一条推翻了本文件早先版本的写法。** 实际扫描本地源码树 `repo/vpipe`（`33cda00`）：

| 资产 | 本地 `33cda00` 有吗 |
|---|---|
| `stages/flashvsr-model-config-stage.{cc,h}` | ✅ **有** |
| `stages/flashvsr-src-encoder-stage.{cc,h}` | ✅ **有** |
| `generative-models/flashvsr/`（含 `metal-flashvsr-transformer.cc`） | ✅ **有** |
| `docs/pipelines/flashvsr-upscale-1920x1088.vpipeline` | ✅ **有** |
| `docs/pipelines/flashvsr-plus-upscale-1920x1088.vpipeline` | ✅ **有** |
| `docs/pipelines/flashvsr-restore.vpipeline` | ✅ **有** |
| `stages/audio-video/relayvsr-upscale-stage.cc`（RelayVSR 本体） | ❌ **没有**（随 `81cd674` / 2026-11-14 才进来） |
| `docs/RELAYVSR.md` + 两条 relayvsr 流水线 | ❌ **没有** |

⇒ **本机想跑「视频 → 4× 超分」，用 FlashVSR+ 不需要升 main、不需要重编**；
只有 **RelayVSR（那套 5B 关键帧模型）** 才需要升级。

### 10.1 上游 catalog 的两条 FlashVSR 条目（`stages/model-catalog.cc:2076-2155`）

| | FlashVSR v1.1 | FlashVSR+ v1.0 |
|---|---|---|
| 来源 | OpenImagingLab，arXiv **2510.12747** | OpenImagingLab，arXiv **2610.17552**（Apache-2.0） |
| 参数 | 1.3B | 1.3B |
| 骨干 | **Wan 2.1-T2V-1.3B**（30 blocks @1536，12×128 heads，block-sparse attention over (2,8,8) windows） | **同一个 transformer 重训（RY-DMD）** |
| 形态 | one-step streaming 4× VSR，**一次一个 chunk**（带 KV 窗口） | **一次四个 latent 帧** |
| 仓库 | `JunhaoZhuang/FlashVSR-v1.1` | `ruchangyao/FlashVSR_plus`（**用 `turbo/` 与 `base/` 两个子目录**当模型，`local_subdir` 机制） |
| 变体 | — | `turbo` = **hybrid attention**（30 层里 25 层跑 3×3 band、留一个窗口，**这才是 turbo 的全部差别，权重里看不出来**）；`base` = sparse attention |
| 文件 | `diffusion_pytorch_model_streaming_dmd.safetensors` / `LQ_proj_in.ckpt` / `Wan2.1_VAE.pth` / `TCDecoder.ckpt` | 同上，但 `turbo/dit.safetensors` + `turbo/lq_proj_in.safetensors` |
| 上下文 | 不条件化文本 —— **上下文是 checkpoint 自带的常量**（`posi_prompt.pth`，来自 `deAPI-ai/flashvsr-v1-1`，与 GitHub 原版 byte-identical） | 同上 |

- **`TCDecoder.ckpt`（180–189 MB）**：reference 的**默认**解码器（TAEHV 解码器，**读源图**），
  `vae-decode` 可选 Wan VAE 作为替代。
- ⚠️ `LQ_proj_in.ckpt` 是**因果源投影**，读的是**放大后的像素** —— 由 `flashvsr-src-encoder` stage 跑。
- 上游流水线形态（本地 `flashvsr-upscale-1920x1088.vpipeline` 可见）：
  `load-video → video-to-rgb → image-resample(1920×1152) → temporal-stack → flashvsr-src-encoder
   → generate-video → vae-decode → rgb-to-video → save-video`
  ⚠️ **它先用 `image-resample` 把低清帧拉成目标画布**（`fit: stretch`！本实验室已知这是唯一改长宽比的模式），
  **再让 FlashVSR 细化** —— 所以「超分」与「重采样」是两步，不是一步。

### 10.2 ★ ModelScope 上的 FlashVSR（本机 HF 直连不通，这是可行通道）

| 仓库 | 体积 | 备注 |
|---|---|---|
| **`kuohao/FlashVSR-v1.1`** | **6.48 GB** | ✅ **最完整且最小**：`diffusion_pytorch_model_streaming_dmd.safetensors` 5413 MB + `LQ_proj_in.ckpt` 549 MB + `Wan2.1_VAE.pth` 484 MB + `TCDecoder.ckpt` 180 MB + **`posi_prompt.pth` 4 MB**（上游 catalog 要从 `deAPI-ai/flashvsr-v1-1` 拿的 companion，**这个仓库自带**）→ **一个仓库就够 vpipe 用** |
| `1038lab/FlashVSR` | 12.05 GB | 同权重但**文件重复**（`FlashVSR1_1.safetensors` 与 `Wan2_1-T2V-1_3B_FlashVSR_fp32.safetensors` 同为 5413 MB） |
| `mlx-community/FlashVSR-v1.1-bf16` | **3.27 GB** | ★ **Apple Silicon 原生 MLX 端口**，本机磁盘紧张时的最优解 |
| `mlx-community/FlashVSR-v1.1-fp32` | 6.54 GB | 同上 fp32 |
| `lzx1413/FlashVSR-v1.1-BF16` / `ausboss/FlashVSR-v1.1-ComfyUI` / `svjack/FlashVSR` / `dong625/FlashVSR` / `poiu00197/FlashVSR-v1.1` | — | 其他镜像/重打包 |

⇒ **两条 FlashVSR 路线**：
1. **vpipe 路线**：`kuohao/FlashVSR-v1.1`（6.48 GB，格式原生匹配 catalog，本地 build 直接能跑）；
2. **MLX 路线**：`mlx-community/FlashVSR-v1.1-bf16`（**3.27 GB**）→ 配合本实验室已有的
   `locmodel-h3-video` 技能（stable-diffusion.cpp/MLX 引擎）→ **磁盘最省的一条路**。

---

## 11. 对本实验室路线的意义（★ 待验证，本轮只登记）


本实验室第 16 节的结论是「**768p 值 3.09× 时间换 3.33× 细节**」，并推荐
「**单段 ≤241 帧 + 多个独立短段各自成片**」。
RelayVSR 给出了**第三条路**：

| 路线 | 时间成本 | 内存 | 备注 |
|---|---|---|---|
| A. 直接生成 768p（现状） | 29m34s / 124 帧 | 24 GB 内可跑 | 细节 3.33× |
| B. **544p 生成 + RelayVSR 4× → 2176×1360** | 9m35s + 超分 | **21.8 GB**（紧） | 待测 |
| C. **480p 生成 + RelayVSR 4× → 1920×1080** | 更便宜 | **11.7 GB** ✅ | 待测，最有希望 |

路线 C 的诱惑：H3 支持 480p（社区实测 608×352 的 8 步配方是 `shift 12/3` + euler + simple），
生成便宜得多，再靠超分补到 1080p 交付。
**但要警惕**：超分是「重绘」，不是「还原」；且第 16 节已证明
「细节能量会把噪点当细节」—— **必须同时看中值滤波后纹理量与颗粒量**才能判定它是真细节还是假锐。

**本轮不跑这个实验的原因**（三条硬阻塞）：
1. **磁盘 5.6 GiB < 15 GiB 下限**；RelayVSR 权重需 10.2 GB（FlashVSR 路线需 6.48 GB，MLX 版只要 3.27 GB —— **后者其实装得下**）；
2. **RelayVSR 本体本地 build 没有**（随 `81cd674` / 2026-11-14 才进来）→ 需先升 main 并重编；
   ⚠️ **但 FlashVSR/FlashVSR+ 本地 build 已经有了**（见第 10 节）→ **不升 main 也能做超分实验**；
3. 已装 App `9db5dd7` 更早，也不可能有。

---

## 12. 坑清单

1. **`output_width`/`output_height` 不写 = 按 3840×2176 规划（21.8 GB 那行）** → 必写真实值。
2. **权重 4×/2× 不能混用** → runner 直接报错，不是警告。
3. **`token_plain` 精度掉 3.1×**（相对 release 的 bf16 误差）→ 别用。
4. **M5 上 `ane_ffn` 不划算**（M5 Max 上游实测「两边都保持纯 GPU」）→ 本机默认关。
5. **`seed` 只管关键帧噪声，且用的是 torch CPU 抽样**（release 用 CUDA）→ 与 release 的输出**不逐位相同**。
6. **2× 的画质有社区实测争议**（嘴部崩坏 vs 四分之一算力）→ 两说并存，实测为准。
7. **vpipe 的 stage 只支持 `upscale_factor=4`**（issue #59 未解决）→ 2× 走 ComfyUI 路线。
8. **ComfyUI 路线要求 ≥ v0.45.0 + `comfy-kitchen` 的 `window_attention`**，且 `detail` 在 `VSRDecode` 节点里。
9. **超分会重绘画面**（AIwood：面部噪点减少但皮肤/发丝细节被改写）→ 不能当无损放大用。

---

## 13. ★★★ 第 6 轮（2026-11-18 12:56）**本机实测**：FlashVSR v1.1 真机跑通 + 量化判决

> 第 4 轮只做了「文档级登记」；本轮**在 24 GB Mac mini 上第一次真机跑通 FlashVSR**，
> 并给出「它到底加了什么、代价是什么」的量化答案。

### 13.1 权重与模型目录（ModelScope 全通道）

| 文件 | 大小 | 说明 |
|---|---:|---|
| `diffusion_pytorch_model_streaming_dmd.safetensors` | **5.676 GB** | 唯一的 `.safetensors`（DiT 本体，30 blocks，1536 wide） |
| `LQ_proj_in.ckpt` | 0.576 GB | 源投影（16×16 pixel unshuffle） |
| `Wan2.1_VAE.pth` | 0.508 GB | Wan 视频 VAE |
| `TCDecoder.ckpt` | 0.189 GB | FlashVSR 的 tiny decoder |
| `posi_prompt.pth` | 4.19 MB | 固定上下文（**不是**文字提示词） |
| `configuration.json` | 50 B | `{"framework":"Pytorch","task":"motion-generation"}` |
| **合计** | **6.953 GB / 8 文件** | ModelScope `kuohao/FlashVSR-v1.1` |

- **文件名与本地 build 期望的完全一致**（`flashvsr-family.cc:45-47`：`kPublishedSource=kLQ_proj_in.ckpt`、
  `kPublishedContext=posi_prompt.pth`、`kPublishedVae=Wan2.1_VAE.pth`）→ **下载即可用，无需转换**。
- ★ **`hf_dir` 直接写绝对路径**：`kuohao/FlashVSR-v1.1` 不在 registry（LMDB）里，
  `resolve_model()` 对未注册的 ref **直接当文件路径用** → 写
  `"hf_dir": "/Users/minichen/AI-Models/vpipe-workspace/models/kuohao/FlashVSR-v1.1"` 即可，
  不必写 registry 条目。
  ★ **目录里必须恰好只有 1 个 `.safetensors`**（`resolve_adapter_file`：「several are not」——
  目录遍历顺序不是任何人做的选择）。
- 下载端点：`https://modelscope.cn/api/v1/models/<repo>/repo?Revision=master&FilePath=<file>`
  （会 302 到 `cdn-lfs-cn-1.modelscope.cn`）。

### 13.2 ★ 几何契约（上游 `flashvsr-family.h` 明写，违反会被「改写」而不是「拒绝」）

1. **输出宽高必须是 128 的倍数**（窗口划分要求 token grid 能被 8 整除）。
2. **帧数必须 8k+1**（去噪每块吃 8 源帧）；**v1.1 单个 clip 至少 25 帧**（= 8×3+1）。
   不满足时**向上取整**，并在日志里报告。
3. **输出 = 4× 源片** → 想出 1280×768，源片就必须是 320×192。
4. `temporal-stack.group_size` **必须 ≤ 实际帧数**，否则它永远攒不够、**一个 beat 都不发**，
   流水线会**挂住**（不是报错）。单组放完最稳：`group_size == frames`。
5. `generate-video` 的 `width/height` 在本家族里是**上限（cap）**，不是目标值。

### 13.3 ★★ 内存账（**上游源码给的数，本轮实测吻合**）

| 分辨率 | 上游声明 | 本轮实测 |
|---|---|---|
| 1920×1152 | 流式携带 ~20 GB（`continuity:auto` 的判据） | **本机 24 GB 跑不了** |
| **1280×768** | 按面积比 ≈ 8.9 GB | **实测：携带 ~8483 MB、合计 ~11372 MB / 24576 MB ✅** |

- 日志原话：`restoring the source as ONE STREAM at 1280x768 -- the projection, the denoiser and
  the decode carry ~8483 MB of state from group to group (~11372 MB in all of 24576 MB)`。
- ★★ **VAE 解码有自动降级**：整块 1280×768 解码要 ~5963 MB，不够时会自动切成
  **TILE-OUTER（3×4 tile，halo 16 px，~1973 MB）** 逐 tile 跑完。
  日志里那行 `[NORMAL] MetalWanVae: 1280x768 decode runs TILE-OUTER …` **不是错误，是降级成功**；
  上面那行 `[WARN] the stream's decode failed (insufficient free RAM …)` 才是需要留意的信号
  （本轮它紧跟着 TILE-OUTER 出现 → 结果是对的）。
- 用时：**25 帧 1280×768 = 45.5 s**（含模型加载）。

### 13.4 ★★★ 量化判决（本轮核心）：**它是「细节生成器」，不是「保真放大器」**

实验设计（同一份 320×192 低清源）：
- **真值 R** = 原始 768p H3 成片 → 1280×768（lanczos，与源片同比例，无 aspect 错配）
- **A 臂** = 320×192 → lanczos 插值 → 1280×768（纯插值基线）
- **B 臂** = 320×192 → **FlashVSR 4×** → 1280×768

| 指标 | A 插值 | **B FlashVSR** | 真值 R | 读法 |
|---|---:|---:|---:|---|
| 纹理量（3×3 中值后拉普拉斯方差） | 13.00 | **163.80** | 93.20 | **12.6× 插值；且超出真值 1.76×** |
| 颗粒量（\|帧-中值\| 均值） | 0.228 | 1.066 | 0.646 | 也是真值的 1.65× |
| 纹理/噪点 | 57.1 | **153.7** | 144.3 | **多出来的细节是结构化纹理，不只是噪点** |
| **SSIM(A) vs 真值** | — | — | — | **0.946253 / PSNR 32.238** |
| **SSIM(A) vs 真值（B 臂）** | — | — | — | **0.895679 / PSNR 28.186 → 比插值低 0.0506 SSIM / 4.05 dB** |
| HF jitter | 0.306572 | 0.341048 | 0.321431 | **比真值还高 6.1%** |
| frame diff | 0.010942 | 0.015037 | 0.011393 | **+37.4%（相对插值）** |
| static HF jitter | 0.201133 | 0.235367 | 0.215435 | +9.2%（相对真值） |

⇒ **结论（三条，都可复算）**：
1. **它确实生成了插值给不出的细节**：纹理量 13.00 → 163.80（**+1160%**，远超漂移基线 0.01%），
   且纹理/噪点比 153.7 **高于**真值的 144.3 → 那是**有结构的毛发级纹理**，不是噪点。
2. **但它不是「还原」**：对原始 768p 的 SSIM **比纯插值低 0.0506**、PSNR **低 4.05 dB**
   → 它在**编造**细节（真值纹理量的 1.76× 就是编造的量）。
3. **代价是时序不稳**：帧间变化 +37.4%，HF jitter 甚至**超过真值本身 6.1%**。

⇒ **交付口径**：要「忠于原片」→ **别用**（会掉 4 dB）；要「看起来更有细节」→ 可以用，
但必须知道它超出真值 1.76× 且更闪。

### 13.5 ★★ 复现性：**不逐位相同，但指标漂移 ≈ 0**（与 H3 的 bit-for-bit 不是一回事）

- 复跑两次：**`framemd5` 不同**（`9c17131b…` vs `7da18ab9…`），音频轨 md5 相同。
- 但 **SSIM(A) = 0.998751 / PSNR = 51.894 dB / 首帧 SSIM(B) = 1.000000**，
  指标漂移 **hf_jitter +0.02% / frame_diff +0.00% / sharpness +0.01% / static_hf_jitter −0.00%**
  → **实质上可重复**。
- ★ **为什么 `autotune:false` 在这里不管用**：flashvsr 家族的
  **sampler / scheduler / negative port 全部是惰性的**（`one step at a fixed timestep`，
  guidance 已蒸馏掉）→ **`autotune` 没有可调对象** → 日志里**没有 `autotune` 回显**
  （符合第 3 轮坑 10.2「字段没被消费 = 静默丢弃」）。
- ⇒ **纪律**：**FlashVSR 的复现性判据必须用「framemd5 + 指标漂移」双判据**，
  不能沿用 H3 那一套「关 `autotune` 就该逐位相同」的预期。

### 13.6 LFM3-VL-2B 复核（4 问，2 对 2 错）

| 问 | 答 | 判定 |
|---|---|---|
| Q1 三行是否同一场景 | 是（同一只穿牛仔外套的猫，姿态位置一致） | ✅ 语义层正确（像素级差异仍靠 SSIM 裁决 → **已知缺陷 ④ 再现**） |
| Q2 哪一行纹理更细碎 | 「**第 2 行（插值）**更细碎更锐」 | ❌ **说反了**（量化是 B 高 12.6×）→ **已知缺陷 ② 再现** |
| Q3 1:1 裁切：右边比左边多了什么 | 「细节变多了，出现原图里没有的、像 AI 生成的细小纹理或斑点」 | ✅ **与量化完全一致**（编造量 = 真值的 1.76×） |
| Q4 有没有运动 | 「没有显著运动」 | ⚠️ 漏检（真值 frame diff 0.0114）→ **已知缺陷 ③** |

### 13.7 本轮新增坑（接第 12 节）

10. **FlashVSR 不在 registry** → `hf_dir` 用**绝对路径**；且目录里**只能有 1 个 `.safetensors`**。
11. **几何是硬契约**：输出宽高 128 的倍数、帧数 8k+1（v1.1 ≥ 25）、输出 = 4× 源、
    `group_size ≤ 帧数`（否则**挂住**）。
12. **VAE 解码内存不够会自动降级成 TILE-OUTER**（日志 `[NORMAL]` 行）→ 看到 `[WARN] the stream's
    decode failed` 别慌，**看它后面有没有跟着 TILE-OUTER**。
13. **`autotune:false` 在 flashvsr 家族无回显也无效果** → 复现性改用指标漂移判据。
14. **评价 AI 超分不能只看 SSIM**：本轮 SSIM 判它是「更差」，而纹理量判它是「好 12.6×」——
    **两个口径必须同时报**（第 3 轮坑「细节能量会把噪点当细节」的姊妹坑：
    **SSIM 会把「编造的细节」判成「失真」**）。

---

## 13. 原生 2× 与 ComfyUI int8 档（2026-11-21 第 20 轮追加，来源：上游 commit `d72c22f` 2026-11-20 + `docs/RELAYVSR.md`）

- **`relayvsr-upscale` 从 4× 专用变成 2×/4× 双模**：`hf_dir` 接受 `Comfy-Org/RelayVSR-x2` / `Comfy-Org/RelayVSR-x4` / 目录 / 单文件（文件自带 scale 声明）；`scale: 2|4|0`（0=按文件名）。2× 权重本体 = `lightx2v/RelayVSR_X2`（HF），vpipe 侧推荐 ComfyUI 的 int8 repack。
- **体积账（逐文件口径）**：ComfyUI int8 每档 **5.3 GB 磁盘 / 4.3 GB 内存**；原生 release 8.4 GB 内存 / 10.2 GB 磁盘。
- **★★ working set 按「输出」计，不按倍数**：2× 的 latent 是输出的 1/16（4× 是 1/8）→ 同一输出尺寸下两档订同样的 ring。**960×540→1920×1080（2×）只需 480×270 行的工作集**，int8 档总计 **7.8 GB** → 24 GB Mac 舒适（对比 4×→4K 的 21.8 GB 紧）。
- **几何契约变化**：2× 的 pad 倍数是 **16**（4× 是 8）；输出宽高须为 scale 的倍数。
- **issue #59 已实现但仍 open**（0 评论）—— 上游不改状态，引用功能时别看 issue 状态。
- **官方流水线**：`prepare-relayvsr-x2.vpipeline` + `relayvsr-upscale-x2.vpipeline`（ComfyUI「RelayVSR 2x」模板同款接线）。
- **待验证（P29 候选）**：本机 24 GB 实测 2×→1080p 的 SSIM/纹理量双口径（对照 P22 的「细节生成器」判决是否在 2× 档同样成立）。

## P32 真值对照判决（2026-11-21，第 20 轮续作 2）

**社区「2× 崩坏/白晕」说法在本机 d72c22f build 上不成立**（P22 猫片三臂 640×384 对照）：

| 维度 | RelayVSR 2×（本机实测） | FlashVSR 4×（P22 实测） |
|---|---|---|
| 纹理量 vs 真值 | **0.785×（欠估，方向正确）** | 1.76×（编造，超真值 76%） |
| 锐度 vs 真值 | 91%（730.7 / 802.5） | —（超真值） |
| SSIM vs 真值 | 0.9015（插值臂 0.9625，差是纹理重分布代价） | 比插值低 0.05 |
| frame_diff vs 插值臂 | +13.7% | +37.4% |
| 复现性 | 逐位（autotune:false 真生效，双素材复证） | 指标漂移（家族惰性） |
| 速度 | 0.05 s/帧 @640×384；0.12 s/帧 @1664×960 | 0.11 s/帧 @1280×768 |

**双档定位（修订社区矛盾说法）**：FlashVSR 4× = 细节生成器（风格化用途，细节全编）；
RelayVSR 2× = 向真值收敛的增强器（保真用途）。二者是档位分工，不是竞争。
ULL Studio 观察到的 2× 崩坏可能是旧权重/旧实现的锅，Comfy-Org int8 重打包 + d72c22f
stage 无此现象（至少本素材上）。

**15 帧周期检验功效警告**：25 帧素材只有 2 个 keyframe 边界，检验无效（peak 0.058）；
定标判据线必须 ≥45 帧（P29 124 帧 peak 1.43 才是有信息量的信号）。
