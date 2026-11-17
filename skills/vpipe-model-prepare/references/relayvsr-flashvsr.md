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
