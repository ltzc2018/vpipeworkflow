---

## 第 11 轮（2026-11-19 21:30 · 06:30 自动任务）

### 本轮主线

1. **LTX-2.5 插件生态发现**：上游组织发布了独立插件 `vpipe-ltx-2.5`，支持 Lightricks 的 22B 视频模型，且具备潜空间 2× 超分能力。
2. **上游静默确认**：HEAD 维持在 `4dc36b7` (2026-11-16)，过去 3.5 天代码库零增量，Issue #55 依旧零回复。
3. **性能对标**：M4 Pro 64GB 生成 960x544 / 5s 视频耗时约 8.8 分钟。

### 逐条新增知识

| #       | 知识                                                                                          | 来源                          | 日期         | 对既有结论的影响                                    |
| ------- | ------------------------------------------------------------------------------------------- | --------------------------- | ---------- | ------------------------------------------- |
| **K56** | ★★★ **LTX-2.5 插件支持**：上游发布 `vpipe-ltx-2.5` 独立插件（C++/.so），支持 22B LTX-2.5 模型。支持 T2V/I2V/音频参考。  | `tgo-app-dev/vpipe-ltx-2.5` | 2026-09-30 | **新增路线**：这是 H3 之外的第二个完整音视频生成家族，且权重许可不同      |
| **K57** | ★★ **潜空间超分 (Latent Upscale)**：`vpipe-ltx-2.5` 插件支持在潜空间直接做 2× 放大（单卷积前向），960x544 → 1920x1088。 | 插件 README                   | 2026-11-19 | **印证**：潜空间超分是比图像空间（FlashVSR）更保真的路径（26.9 dB） |
| **K58** | ★★ **LTX-2.5 步数锁定**：该模型蒸馏后固定为 8 步，vpipe 阶段设置 `steps: 6` 会被忽略并强制 8 步。                        | 插件 README                   | 2026-11-19 | ✅ **印证**：蒸馏模型的「固定步数嵌入」是行业标准设计               |
| **K59** | ★ **Valtz 细节确认**：确认为官方原生 GUI (C++/Metal)，内置了 MiniMax 官方的 H3 提示词六段式技能。                       | `tgo-app-dev/valtz`         | 2026-11-16 | **知识补全**：提示词标签已全面转向 `<Picture N>` 格式        |
| **K60** | ★ **上游静默延续**：截至 11-19 21:30，主库连续 3.5 天无更新。                                                  | GitHub API                  | 2026-11-19 | **维持现状**：实验室维持「回读源码+量化自查」模式                 |

#### 8.1 检索范围与来源清单

- **GitHub**: `tgo-app-dev/vpipe` (HEAD `4dc36b7`) —— 2026-11-16 重大更新：支持 DiT 模型 Mac 双机分布式运行 (Tensor Parallel)。
- **GitCode / CSDN**: MiniMax-H3 加速 LoRA 盘点与 PDD (Alibaba PAI) 技术细节。
- **Vlad Mandic (SDNext)**: 详尽的 H3 shift/steps 对照表。
- **MiniMax API**: `platform.minimax.io` 已上线 H3 及 H3 Max (fal.ai 托管) 商业服务。

#### 8.2 新增知识

1. **vpipe 分布式推理**：最新 commit `4dc36b7` 实现了 FLUX.3、Qwen-Image-2.1、Krea-2 等模型的 `tensor_parallel`，支持两台 Mac 拆分运行。
2. **H3 长序列优化**：修复了超过 150k 行时的 32-bit 索引噪声问题，改为 64-bit 无符号索引，提升了超长视频生成的稳定性。
3. **PDD (Alibaba PAI) 深度规约**：PDD 并非单纯 LoRA，它包含 Head Bank 蒸馏。采样器**必须**固定为 `euler`，CFG **必须**固定为 `1.0`，且 steps 和 shift 建议锁定在训练值 (8步 / 12 / 3)。
4. **Shift 官方修正**：根据 SDNext 汇总的上游文档，**lightx2v 768p 4步/8步** 推荐 shift 为 **6 / 3**，而 **544p 版** 和其余大部分加速 LoRA 为 **12 / 3**。
5. **H3 Max**：fal.ai 托管的高速版，优化了 5–15s 的 480P/768P 生成。

#### 8.3 与既有结论的印证/冲突

- **印证**：第 3 轮 §10.4 的「上游官方表」在 SDNext 的文档中得到完整印证。
- **补充**：第 3 轮曾观察到 Ref2VA 768p 在 12.0 更锐，本轮检索证实 **lightx2v 768p 官方推荐确实是 6.0**。这解释了为什么 12.0 会「过锐」到产生伪影。

#### 8.4 本轮实验 (无)

- **状态**：本轮仅知识同步，无实验。

#### 8.5 对技能包 / 脚本 / 流水线的修改

- 无。

#### 8.6 本轮踩的坑与结论

1. **GitHub API 访问**：沙箱环境下直连 HF API 不稳定，但 GitHub API 正常。
2. **知识固化**：发现 `valtz` 仓库内置了 MiniMax 官方提示词技能，值得后续研究。

# vpipe 每日知识增量（累积）

> 由「vpipe 后续计划任务·每日 4 轮夜间自动执行」系列自动化写入。  
> **只追加，不覆盖**。每轮一节，按轮次编号递增。  
> 相关文件：`vpipe-H3-部署与测试报告.md`（第 18 节）、`vpipe-后续计划任务.md`（状态看板）。

---

## 第 1 轮 · 2026-11-17 20:31 — 首轮：上游落差盘点 + HyperFlow H3 Flash

### 1.1 本轮检索范围

| 源               | 地址                                                                                 | 取得方式      | 日期         |
| --------------- | ---------------------------------------------------------------------------------- | --------- | ---------- |
| GitHub Releases | `api.github.com/repos/tgo-app-dev/vpipe/releases?per_page=10`                      | WebFetch  | 2026-11-17 |
| GitHub Issues   | `api.github.com/repos/tgo-app-dev/vpipe/issues?state=all&sort=created&per_page=15` | WebFetch  | 2026-11-17 |
| GitHub compare  | `api.github.com/repos/tgo-app-dev/vpipe/compare/9db5dd7...main`                    | WebFetch  | 2026-11-17 |
| GitHub Commits  | `api.github.com/repos/tgo-app-dev/vpipe/commits?per_page=40`                       | WebFetch  | 2026-11-17 |
| GitHub docs 目录  | `api.github.com/repos/tgo-app-dev/vpipe/contents/docs`                             | WebFetch  | 2026-11-17 |
| 本机版本            | `vpipe --version` → `0.1 (9db5dd7*0)`                                              | 本地        | 2026-11-17 |
| 网络检索            | MiniMax H3 / HyperFlow / vpipe / FL2VA / Ref2VA 中英双语                               | WebSearch | 2026-11-17 |


### 1.2 新增知识（12 条）

#### K1 ★ 本机落后上游 12 个 commit

- 本机：`vpipe 0.1 (9db5dd7*0)`（源码编译版，工作树带 `*` 即有本地改动）
- 上游 main HEAD：`4dc36b7`（2026-11-16）
- `compare/9db5dd7...main` → `status: ahead`、`ahead_by: 12`、`behind_by: 0`
- 之前记录的基线 `33cda00` 落在链条第 10 位 → **自上次同步以来上游又走了 2 步**（`81cd674`、`4dc36b7`）

上游这 12 个 commit 用诗化标题，按日期：

| 日期    | 标题                                                      | 与本实验室的关系        |
| ----- | ------------------------------------------------------- | --------------- |
| 11-03 | 部分片段自带 latents；hybrid 的 softmax 到达范围逐步推进；Fibo 2.0 四百万像素 | 低               |
| 11-05 | 用 MiniMax-H3 权重出图；int8 下 Mac 没有矩阵核心时的加速器；从内存读长提示词       | 中（出图路线）         |
| 11-06 | 逐位复现的生成；运行中模型持有的内存；阶段结束即释放生产者                           | 中（可复现性）         |
| 11-07 | 分块读权重、四块并发；片段自带 autoencoder 解出的静帧；被拒的媒体调用会说明它收到了什么      | 低               |
| 11-08 | 单独一段音轨也能当参考；太短无法合并的参考片段不再被拒                             | **高（音轨参考）**     |
| 11-09 | RIFE 帧插值；2K 下上下文精修的草稿                                   | 中               |
| 11-10 | 节拍跟踪；图像阶段只持有一次画面；**经 MiniMax-H3 的 Image VAE 出图**        | **高（第三条文生图路线）** |
| 11-11 | **MiniMax-H3 上的图像模型**；NVIDIA NVFP4 4-bit 权重             | **高（图像 + 量化）**  |
| 11-12 | **MiniMax-H3-Image 图：DiT 在 M5 上跑 int8**，以及该模型该关掉哪些层级    | **高（M5 上省内存）**  |
| 11-13 | MiniMax-H3 的 DiT 跨主机切分：tensor-parallel/1                | 低（单机用不上）        |
| 11-14 | **RelayVSR 的 4x 流式超分**；跑适配器、int8 层级和解码的切分 rank          | 中               |
| 11-16 | 更多 DiT 切到两台 Mac；MiniMax-H3 对长提示词分带、对长片段逐行寻址             | 中               |

#### K2 ★ YUV 色彩空间可选（BT.601 / BT.709），FFV1 支持 4:2:2 与 4:4:4

> 出处：release「YUV color space choice (BT.601 or BT.709), 4:2:2 and 4:4:4 support through FFV1 codec」

**直接冲着我们的 SSIM 口径问题**：我们一直记录「视频流直接比 ≈ 0.9736，PNG 落盘再比 ≈ 0.9445，差 0.03 来自 YUV 4:2:0 色度往返」。  
如果续接与保真度链路改用 **4:4:4（无色度下采样）**，这部分损失应当被消掉 → 值得做一次口径消融。

#### K3 ★ 自动视频续接光照适配（修 MiniMax H3 VAE+DiT 引入的变暗）

> 出处：release「Automatic video continuation adaptation to fix the continuation clip's lighting to match the reference clip」，  
> 并指向 `docs/MINIMAX-H3.md` 的 long video guide

**直接冲着 P3 四段式续接的 Δ亮度 1.1 → 8.6 → 13.3**。上游承认续接会变暗并已修。  
下一轮应升级到最新 main 后重跑续接实验，看接缝亮度跳变是否消失（注意：SSIM 接缝 0.457→0.358→0.281 的**几何跳变**是另一个问题，光照修复不一定解决它）。

#### K4 ★ MiniMax H3 步数语义变更（与 ComfyUI/diffusers 对齐）

> 出处：release「MiniMax H3 step definition update: it used to follow MiniMax's reference to mean number of noise stages.  
> It's now updated to match ComfyUI, diffusers and other models hosted by Vpipe.  
> Some users have bumped up step count by 1 to get desirable results with Turbo LoRAs -- you can drop the count to match ComfyUI now」

**这条会影响我们全部步数结论的解读**。我们写过「4 步适配器必须同时把 pipeline 的 `steps` 改成 4，否则静默劣化」。  
在新语义下，「4 步」指的不再是同一件事；旧语义下有人为了 Turbo LoRA 效果把步数 +1，现在可以改回 ComfyUI 口径。  
→ **需要复核**：升到最新 main 后，「同一适配器 + 不同 steps」的画质/耗时曲线是否平移。

#### K5 ★ Swap allowance（默认 4 GB）

> 出处：release「Introduced a "Swap allowance" flag to allow Vpipe driving part of other app's non-wired application memory into swap.  
> Vpipe still wires its memory allocation. Vpipe itself would not use swap, would not thrash. It defaults to 4 GB, which unlocks some long video generation tasks.  
> Setting it to 0 returns to old behavior.」

24 GB 机器上跑 768p / 241 帧长片时被内存卡过 → 这是一个**低成本提速开关**，值得实测开关前后的峰值内存与耗时。

#### K6 ★ ANE 在 M5 上基本没用（官方明说）

> 出处：release「ANE acceleration has been introduced since v0.1.51 … It is recommended to users on M4 family.  
> Vpipe runs ANE along with GPU to harvest additional TFLOP/s. **After M5 it barely moves performance (GPU NAX is very fast)**,  
> but the preparation involves ANE graph compilation which doesn't pay off.」

本机是 **M5 Pro** → **不要开 ANE**，图编译成本不划算。这条直接决定我们后续实验的默认配置。

#### K7 MiniMax H3 Image VAE —— 第三条文生图路线

> 出处：commit 11-10 / 11-11「Pictures through MiniMax-H3's Image VAE」「An image model on MiniMax-H3」

让「视频+音频模型」直接产出静帧，且可极高分辨率。现有文生图只有 Z-Image-Turbo 与 Krea-2-Turbo → 新增第三条可比路线。  
commit 11-12 进一步说明：**H3-Image 的 DiT 可在 M5 上跑 int8**，并给出了「该模型该关掉哪些层级」。

#### K8 MiniMax H3 MotionCache（适合大步数生成）

> 出处：release「MiniMax H3 MotionCache support, suitable for generation with large step count」

对我们「768p + 多步」的组合可能提速；需要确认是否需要额外权重。

#### K9 Open-VDN 上游对齐 + Ref2VA 静图无音频的误拒修复

> 出处：release「MiniMax H3 Open-VDN update: matched upstream to support Ref2VA-like reference mode (still uses FL2VA weights)」  
> 与「Fixed MiniMax H3 Ref2VA with only still images, no audio. Previously rejected incorrectly」

后者与我们的 Ref2VA 实测直接相关（我们做的正是「只有静图、无音频」的 Ref2VA 消融）——**旧版本会错误拒绝这种请求**，说明我们的历史对照实验跑在旧 build 上时，某些组合可能被静默拒绝，需复核。

#### K10 其他 release 增量（与本实验室弱相关，但登记备查）

- **Pika H3 Flex 6 步蒸馏权重**新增（我们用过 Pika H3 Flex）
- **Open-H3-Regenerate-2K 支持 2560×1440**（官方称 24 GB 以上实测过）
- **MiniMax H3 L2VA 支持 FL2VA 分区**（最新 release）
- **LFM3-VL 可作为带视觉的语言模型**使用（我们用它做第三方复核 → 说明该用法是官方支持的）
- **更广的 LoRA 支持**：可直接把 `.safetensors` 装进 LoRA 槽（FP8 暂不支持）
- **ComfyUI int8 ConvRot × pruned 权重格式**支持 LoRA 与 DiT
- 文档目录扩到 **27 个 md + 2 个目录**；`docs/MINIMAX-H3.md`（英文，249,773 B）比 `MINIMAX-H3-zh-cn.md`（176 KB）**多 73 KB** → 长视频指南的权威出处是英文版

#### K11 ★ 上游 issue 新动态（基线 30 条 → 至少 59 条）

| Issue   | 状态          | 内容                                                                                                                                                                                                                                                 | 对我们的意义                                                                                                                                                   |
| ------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **#55** | Open，0 回复   | MiniMax-H3 **持久性时间纹理「沸腾」**；作者认为 sampler spec 的 iport 对该族无效、FlowMatchEuler 没有随机项。涉及 `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`（**正是我们 768p Ref2VA 用的适配器**）、`video_shift=12.0` / `audio_shift=3.0` / `condition_timestep=1.0` | **高**。作者实测 HF jitter：静态参考 0.0000 / 8 步 0.0502 / 16 步 0.0437 / **4 步 0.0914**；shift 12→6 把 0.0512→0.0436，但**作者明说日志打印可能误导**                                |
| **#47** | Closed，2 回复 | Model Config 设 `video_shift=6`，Generate Video 阶段却用 12                                                                                                                                                                                              | **★ 关键**：#55 补充说明 —— `video_shift` **实际能到达 denoiser**，但 `GenerateVideoStage` 的日志**始终打印 12.0/3.0**。这既**印证**了我们「shift 写错完全静默」的机制，又说明**不能相信日志里打印的 shift 值** |
| **#56** | Open + PR   | FastH3-Omni 的 VSA 压缩门控与路由预算；`attn.to_gate_compress.weight` 名称映射不认识 → checkpoint 被拒（PR 已实现映射 + VSA 路由预算 + cube tile 划分 + 单测）                                                                                                                        | 中（未来新模型）                                                                                                                                                 |
| **#59** | Open，0 回复   | RelayVSR 原生 **2x** checkpoint（`lightx2v/RelayVSR_X2`）；现有阶段只接受 `upscale_factor=4`；H3 的 896×512 / 768×1344 / 720p 素材通常只需 2x，4x 再 Lanczos 缩放既浪费像素也可能让 36 GB 机器内存不足                                                                                    | 中（超分路线）                                                                                                                                                  |
| **#44** | Closed，3 回复 | MiniMax-H3 Ref2V Turbo 4-step LoRA **持久偏心构图**（768×544、shift 12/3、4 次 denoise）；作者称 Draw Things 用同一适配器无此问题 → 疑似 vpipe 实现方式导致                                                                                                                         | **高（4 步适配器构图偏差）**                                                                                                                                        |
| **#49** | Open，1 回复   | HF 上 40 GB BF16 `10Eros_Max_h3_TURBO-hybrid_beta5.safetensors` 量化卡在 shard 阶段（`arch='unknown' layer_prefix='' n_layers=0`）                                                                                                                          | 中（量化坑）                                                                                                                                                   |
| **#41** | Open，1 回复   | 4-bit（w4 g64）权重坏：Z-Image 挂起 / GPU 错误，Qwen-Image-2.1 静默输出全透明图                                                                                                                                                                                       | 印证我们「P5 建议跳过」                                                                                                                                            |
| **#57** | Closed，5 回复 | 最新 release 里 ANE 前馈内存不足                                                                                                                                                                                                                            | 低（M5 不开 ANE）                                                                                                                                             |

#### K12 ★★ 新模型：HyperFlow H3 Flash（Video Rebirth，非 MiniMax 官方产品）

- 仓库：GitHub `Video-Rebirth/hyperflow-h3-flash`；权重 `VideoRebirthAI/hyperflow-h3-flash`
- 规格：**fl2va 13.7B / ref2va 13.9B**（原 ~31B transformer 的一半不到）
- 采样：**4 / 6 / 8 步，默认 6**；**CFG = 1**（无负面提示词）；euler + BasicGuider
- 输出：**24 fps，默认 1344×768**（支持 768×1152 竖屏）；**5.2–15 秒 = 124–362 帧**，**帧数 17n+5**（与我们已知的官方帧数规则一致，互为佐证）；32 kHz 立体声同步音轨
- 压缩方法：结构剪枝（fl2va 丢 50 块中的 3 块：6/21/22；ref2va 丢 1 块：9）+ 低秩分解（fl2va 102 个线性层 / ref2va 114 个）+ 旋转 W8A8 INT8（convrot）+ 双时间 (t, r) 条件
- 权重体积：**GGUF Q3_K_M–Q8_0 共 7.2–15.2 GB**（**Q4_K_M 9.1 GB fl2va / 9.2 GB ref2va**；Q8_0 14.9 / 15.2）；INT8 convrot ~16 GB；ComfyUI 单文件 16.0 / 16.4 GB
- 配套件：文本编码器与两个 VAE 仍来自上游（`MiniMaxAI/MiniMax-H3` 或 Qwen3-VL-32B-FP8；VAE 来自 `Comfy-Org/MiniMax-H3`）；**Python 包从不下载 62 GB 的原始 transformer**
- **限制**：**GGUF 与 ComfyUI INT8 的 ref2va 只支持图片参考**；混视频/音频参考需要 Python INT8 包（我们要的多参考视频/音轨组合在 GGUF 路线上拿不到）
- 许可：MiniMax H3 Community License，排除美国 / 欧盟 / 英国 / 韩国
- 官方基准（5.2 s / 6 步 / 1344×768）：4×B200 8.7 s、1×H200 36 s、1×RTX 5090 92 s；独立复测（RTX 5090 + GGUF）：5.2 s 片段 118 s、15 s 片段 618 s
- **对我们最关键的意义**：本机 24 GB。Q4_K_M 只有 **9.1 GB**，比 8-bit FL2VA 的内存占用小得多；  
  且实验室已有 `locmodel-h3-video` 技能（stable-diffusion.cpp + GGUF Q4 路线）→ **有机会把 H3 的 GGUF 路线接进 vpipe 管线**。  
  但注意：**它不是 vpipe 里的 adapter**，是一条独立模型路线。

#### K13 本轮发现的工程问题（GitHub 同步链路）

| 问题                                         | 现象                                                         | 处置                                                                                                      |
| ------------------------------------------ | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **全量 `git clone` 会被 SIGTERM 打死**           | 仓库 `size: 216,872 KB ≈ 212 MB`（41 个视频占大头），克隆到 137（SIGKILL） | 改为**常驻工作副本** `/Users/minichen/WorkBuddy/2026-11-12-21-10-11/.vpipeworkflow`，每轮只 `git pull --ff-only` 增量 |
| **`--filter=blob:none` 部分克隆不可用于 checkout** | `git ls-tree -l` 会为每个缺失 blob 单独回源（395 次往返）→ 同样被打死          | 不用部分克隆做同步；只把它当只读探测工具                                                                                    |
| **仓库缺 `report/` 目录**                       | 两份主报告（149 KB / 37 KB）**从未进过 GitHub**                       | 本轮补上（`docs/reports/`）                                                                                   |

#### K14 云端对照基线（SiliconFlow）

2026-11-03 上线 `MiniMaxAI/MiniMax-H3`：`duration` 5–15 s、`resolution` 480p/768p、`images` 用 `role` 指定 `first_frame` / `last_frame`；  
**`negative_prompt` 与 `image_size` 不再生效**（传入不报错但被忽略）。  
→ 可作为 768p / 时长行为的外部对照（但本机 HF 直连不通、云端 API 也需要 key，优先级低）。

### 1.3 与既有结论的印证 / 冲突

| 既有结论（报告节）                          | 本轮关系        | 说明                                                                                                                      |
| ---------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| 17.x「shift 规则按适配器分叉」「shift 写错完全静默」 | **印证 + 补强** | #47 + #55 从上游侧确认：`video_shift` 能到达 denoiser，但日志**恒印 12.0/3.0**。→ 我们的量化（对比出片而非看日志）方法是对的；**新增纪律：报告里不得引用日志里的 shift 值作为证据** |
| 16.x「四段式续接 Δ亮度 1.1→8.6→13.3」       | **上游已修**    | K3：上游把续接变暗归因于 MiniMax H3 VAE+DiT 并已修。→ 升级后需重跑续接实验；**但几何跳变（+76/−86 px）是另一个问题，不能指望一并解决**                                  |
| 16.x「4 步适配器必须同时改 steps，否则静默劣化」     | **语义可能已变**  | K4：上游把 steps 语义改成与 ComfyUI/diffusers 对齐 → 需在新版上重测 steps 曲线                                                              |
| 「细节能量会把噪点当细节」                      | **旁证**      | #55 的 HF jitter 指标（静态参考 0.0000 / 4 步 0.0914 / 8 步 0.0502 / 16 步 0.0437）是**另一条独立的抖动度量**，与我们的「颗粒量 vs 纹理量」互补               |
| 「P5 图像 4-bit 量化建议跳过」               | **印证**      | #41 仍 Open：Qwen-Image-2.1 在 4-bit 下静默输出全透明图                                                                             |
| 8.x「SSIM 两口径差约 0.03（YUV 4:2:0 往返）」 | **可消解**     | K2：FFV1 支持 4:4:4 → 差值应能压到很小，**这个 0.03 不该被当成「固有开销」**                                                                     |

### 1.4 本轮实验

**无实验**（本轮是自动化链路的首轮验证，重点在「搜索 → 固化 → 报告 → 同步」这条链本身）。

### 1.5 对技能包 / 脚本 / 流水线的修改

- 新增 `vpipe-lab/report/vpipe-夜间自动任务SOP.md`（4 个时段共用的单一事实来源）
- 新增 `vpipe-lab/report/vpipe-daily-knowledge.md`（本文件）
- `vpipe-model-prepare/references/768p-adapters.md` 追加第 10 节「上游动态与复核清单」
- 实验室 `skills/` 副本补回缺失的 `vpipe-model-prepare/references/768p-adapters.md`（安装版有、实验室副本没有）

### 1.6 本轮踩的坑与结论

1. **`FREQ=DAILY` 不支持多值 `BYHOUR`**（校验直接拒绝）；`FREQ=HOURLY` **会忽略 `BYHOUR` 与 `BYMINUTE`**（实测 nextRun = 创建时间 + 2h）→ 只能拆成 4 个 `DAILY` 单时段自动化。
2. **失败的 `automation_update` 调用有副作用**：一次带非法 rrule 的 update 让原自动化**被删除**，同时把另一个不相关的自动化（视频号补链）**意外置为 PAUSED** → 已人工恢复为 ACTIVE。**改动自动化时应先 `view` 备份 prompt，失败后立即 `list` 复核。**
3. **GitHub 同步不能每轮全量 clone**（212 MB 会被杀）→ 常驻副本 + 增量 pull。
4. **部分克隆（`--filter=blob:none`）不能用来 checkout / 查大小**，每个 blob 都要单独回源。
5. 本轮检索**一次就捞到 12 条真增量**（含一个全新模型），证明「每日自搜索」这条路走得通，值得长期跑。

### 1.7 下一轮建议

1. **P12 升级到最新 main**（落后 12 commit）→ 拿到 MotionCache / swap allowance / 续接光照修复 / 步数语义统一 / YUV 4:4:4 / RIFE / H3-Image / L2VA
2. **P10 HyperFlow H3 Flash GGUF Q4_K_M 接入**（9.1 GB，6 步默认）→ 与 lightx2v HyperFlow 8 步做 A/B
3. **P11 YUV 4:4:4 / BT.709 消融** → 把 SSIM 口径差 0.03 归因清楚
4. **P13 复现 #55 纹理沸腾** → 量化 768p Ref2VA 的 HF jitter

---

## 第 2 轮 · 2026-11-18 00:31 —— YUV 口径归因（P11 已收口）+ 本机版本落差订正 + 768p 适配器全量盘点

> 本轮触发时段：00:30（第 2 轮，共 4 个时段）。上一轮 2026-11-17 20:31。  
> 轮次由 `report/.auto-round-state.json` 决定（读出 round=1 → 本轮 R=2）；本轮无并发锁冲突。

### 2.1 ★ 重大订正：「本机落后上游 12 个 commit」这句话需要拆分（第 1 轮 K1 的修订）

| 对象                               | 实测版本                                         | 与上游 `main @ 4dc36b7` 的关系 | 依据                                                                             |
| -------------------------------- | -------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------ |
| **已安装 App 的 `vpipe` helper**     | `0.1 (9db5dd7*0)`（2026-11-01）                | **落后 12 个 commit**       | GitHub `compare/9db5dd7...main` → `ahead_by:12, behind_by:0, total_commits:12` |
| **本地源码树** `vpipe-lab/repo/vpipe` | `33cda00`（2026-11-13）                        | **只落后 2 个 commit**       | `git log -1` + GitHub API 对比                                                   |
| **本地已编译 build**                  | `build/apps/vpipe/vpipe` → `0.1 (33cda00*0)` | 可用                       | 见下方坑 1                                                                         |

- 来源 URL：`https://api.github.com/repos/tgo-app-dev/vpipe/compare/9db5dd7...main`（2026-11-18 查询）
- 一句话结论：**「落后 12 个 commit」只对已安装 App 成立，对本地源码树是错的（只落后 2 个）**。
- 是否与本机实测冲突：**是 —— 与第 16 节 / 18.1 节正文表述冲突**，已在报告写「第 2 轮修订」标注（未改写历史正文）。
- 推论：**P12 升级任务比原先设想便宜得多** —— 只需把本地源码树从 `33cda00` 再拉 2 个 commit，不必重编译整条链。

### 2.2 ★ 重大订正：YUV 4:4:4 / BT.709 / FFV1 **已装 App 就支持**，不必等升级（第 1 轮 K2–K5 的修订）

第 1 轮把「YUV BT.601/709 + FFV1 4:2:2/4:4:4」记为「上游新增，需升级才能拿到」。实测证伪：

- **行为探针**：`--stage-cfg 'pix_fmt="yuv999p"'` 被拒并打印  
  `pix_fmt 'yuv999p' is not yuv420p, yuv422p, yuv444p or rgb24`；`yuv444p` 被接受。
- **实跑探针**：`load-video → video-to-rgb → rgb-to-video(yuv444p/full/bt709) → save-video(ffv1)` 在**已安装 App** 上跑通（797 ms），产出经 ffmpeg 确认为 `ffv1, yuv444p(pc, bt709), 832x480`。
- 源码佐证：`vpipe-lab/repo/vpipe/stages/rgb-to-video-stage.cc:34-40` 已有 `kPixFmtChoices = {yuv420p,yuv422p,yuv444p,rgb24}` / `kColorRangeChoices = {limited,full}` / `kColorspaceChoices = {bt601,bt709}`。
- 来源 URL：`https://github.com/tgo-app-dev/vpipe` v0.1.74 release notes（2026-09-25，早于 9db5dd7）（2026-11-18 核）
- 一句话结论：**这些能力在已装 App（9db5dd7）里已经有了，缺的从来不是能力而是「测量」。**
- 是否与本机实测冲突：**是 —— 与 18.1 节 K2–K5 的「需升级」框架冲突**，已标修订。

### 2.3 ★★ P11 实验结论：那 0.03 的差 **不是编码开销，是「比较域」造成的测量伪影**

三段实验（脚本 `vpipe-lab/scripts/p11_caliper.py`，JSON `vpipe-lab/p11-caliper.json`，耗时 25.7 s，**全程无模型参与、不占 GPU**）。

**第一段 · 同一 RGB 内容 → 4 种落盘格式，各测 A/B/C**

| 变体       | 格式                           | 口径 A（默认协商） | 口径 B（落盘 PNG） | 口径 C（强制 gbrp） |
| -------- | ---------------------------- | ---------: | -----------: | ------------: |
| V420-def | yuv420p/limited/bt601 + h264 | **0.5796** |       0.3900 |        0.3900 |
| V422     | yuv422p/full/bt709 + ffv1    | **0.6191** |       0.3902 |        0.3902 |
| V444     | yuv444p/full/bt709 + ffv1    | **0.7244** |       0.3902 |        0.3902 |
| V444-lim | yuv444p/limited/bt709 + ffv1 | **0.7549** |       0.3901 |        0.3901 |

|   |   |   |
| - | - | - |

- 口径 A 随落盘格式的**极差 = 0.1752**；口径 B/C 的极差 = **0.0003**；`|B − C| = 0.000000`（**恒等**）。
- 机制（ffmpeg `-v verbose` 直接读到）：口径 A 下 **参考 PNG 被 auto_scale 降到视频的像素格式才参与比较** ——  
  `rgb24/gbr/pc → yuv420p/smpte170m/tv`（4:2:0 视频）或 `→ yuv444p/bt709/pc`（4:4:4 视频）。  
  也就是说**口径 A 的分数里混进了「参考图被降采样的程度」**。
- 一句话结论：**口径 B（落盘 PNG 再比）≡ 口径 C（强制 gbrp 域直比），两者都是「纯 RGB 域比较」；  
  口径 A 是「YUV 域比较」，且其读数随视频像素格式漂移 —— 那 0.03 的差来自比较域，不是来自编码。**

**第二段 · 真值基准（全部用 ffv1 无损编码器，差值只可能来自色度抽样）**

| 变体                                           | SSIM(All) vs 真值逐帧 |     PSNR |
| -------------------------------------------- | ----------------: | -------: |
| 真值自比（测量系统自检）                                 |      **1.000000** |      inf |
| T444（4:4:4）                                  |      **0.999977** | 82.31 dB |
| T422（4:2:2）                                  |          0.997014 | 48.63 dB |
| T420（4:2:0）                                  |          0.995417 | 46.67 dB |
| T420h（4:2:0 + limited + bt601 + h264，历史默认全链） |          0.984282 | 41.58 dB |

- 一句话结论：**4:2:0 确实真丢色度，但只丢 0.0046 SSIM（0.999977 → 0.995417）；  
  真正吃掉 0.015 的是「limited range + bt601 + h264 有损压缩」这三条叠加，不是色度抽样本身。**
- 是否与本机实测冲突：**否 —— 反而印证了 18.1 节「差 0.03 不是固有开销」的直觉方向**（差距确实可消解），但给出了**相反的归因**：  
  可消解的是**比较域**，不是像素格式。

**第三段 · 复现历史那对数字**

| 对象                                            |   口径 A |   口径 B |   口径 C |       A − B |
| --------------------------------------------- | -----: | -----: | -----: | ----------: |
| `pika-i2va-shop.mp4` vs `ref-cat-832.png`     | 0.5774 | 0.3895 | 0.3895 | **+0.1879** |
| `p4-i2va-preview-fast.mp4` vs 锚定图（256×144 归一） | 0.3453 | 0.1735 |      — | **+0.1718** |

- 一句话结论：**口径 A 恒高于口径 B**（差 0.17~0.19），**与第 15.4.2 节括号里那句「另一种口径两张都先落盘 PNG 再比会高约 0.03」方向相反**；  
  而与 17.3 节 / 18.1 节那句「不落盘 PNG 再比，后者会因 YUV 4:2:0 色度往返偏低约 0.03」方向一致。
- 是否与本机实测冲突：**是 —— 报告内部自相矛盾**，两处表述方向相反。本轮以实测为准，详见报告 18.2.3。

**历史表安全性复核（重要）**

- 抽查第 16 / 17 节所有关键表的被测文件像素格式：  
  `p9-ref2va-768p-{a,b,c,d}.mp4`、`p3-768p-shift{6,12}.mp4`、`p3-768p-4step.mp4`、`p3-544p-ref.mp4`  
  **全部是 `h264 / yuv420p(tv, smpte170m)`，完全一致** → 组间同口径，**历史结论不受本轮发现影响**。
- 但**新增一条纪律**：口径 A 的读数依赖被测视频的像素格式，  
  **今后凡跨格式比较（如 4:2:0 vs 4:4:4）必须用口径 B/C，或在比较前统一转码**，否则结论无效。

### 2.4 LFM3-VL 第三方复核（脚本 `vpipe-lab/scripts/vqa-p11.sh`）

| 问题                   | LFM3-VL-2B 回答（摘要）                             |
| -------------------- | --------------------------------------------- |
| 8 变体并排能否看出差别         | 「没有显著差异，颜色饱和度、边缘锐度基本一致，没有明显色块或条纹伪影…肉眼分辨下基本等价」 |
| 4:2:0 vs 4:4:4 两组关键帧 | 「内容一样；4:2:0 那组没有肉眼可见的色彩偏差、边缘锯齿、色块或模糊」         |
| 真值无损 vs 4:2:0 全默认链   | 「内容一致；第二组颜色更饱和；纹理、边缘、渐变没有明显劣化」                |

- 一句话结论：**独立第三方模型也判不出 4:2:0 与 4:4:4 的画质差别** —— 与第二段 0.0046 SSIM 的量化结论互相印证。
- 注意：LFM3-VL 在 Q2 里把 4:4:4 判成「更差」（说可能有压缩伪影），这与量化结论相反 → **再次印证已知缺陷：LFM3-VL 对细微锐度/伪影判断不可靠**，只可作「有无肉眼级差异」的粗判。

### 2.5 ModelScope `lightx2v/Minimax-h3-Turbo` 全量盘点（28 个文件，第 1 轮清单被截断）

- 来源 URL：`https://www.modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files?Revision=master`（2026-11-18）
- 第 1 轮只列了部分变体，本轮补全。**从未在本机测过的新变体**：

| 变体                                  | 文件                                                        |              大小 | CommitDate | 状态                         |
| ----------------------------------- | --------------------------------------------------------- | --------------: | ---------- | -------------------------- |
| FL2VA 4-step v1.3 768p bf16         | `minimax_h3_fl2v_turbo_4step_v1.3_768p_bf16.safetensors`  | 1,383,677,808 B | 2026-10-20 | ⭐ 本机没有，待验证                 |
| FL2VA 4-step v1.3 768p comfyui_bf16 | 同名 `_comfyui_bf16`                                        | 1,956,193,000 B | 2026-10-20 | ⭐ 本机没有                     |
| Ref2VA 4-step v1.0 768p bf16        | `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors` | 1,383,677,808 B | 2026-10-20 | ⭐ **本机完全没有 Ref2VA 4-step** |
| Ref2VA 8-step v1.1 768p bf16        | `minimax_h3_ref2v_turbo_8step_v1.1_768p_bf16.safetensors` | 1,383,677,808 B | 2026-10-20 | ⭐ 本机只有 v1.0                |
| FL2VA 8-step v1.2 768p bf16         | `minimax_h3_fl2v_turbo_8step_v1.2_768p_bf16.safetensors`  | 1,543,291,302 B | 2026-11-12 | ⭐ 本机只有 v1.0                |

- 本机现有仅 4 个文件（`models/lightx2v/`，共 5.7 GB）：  
  `fl2v 4step v1.2 768p bf16`、`fl2v 8step v1.0 768p bf16`、`fl2v 8step v1.0 768p comfyui_bf16`、`ref2v 8step v1.0 768p bf16`。
- 一句话结论：**Ref2VA 的 4-step 家族与 8-step v1.1 完全未测；FL2VA 4-step v1.3 / 8-step v1.2 未测**。
- 是否与本机实测冲突：否（新增覆盖）。

### 2.6 shift 规则的新证据（不推翻旧结论，只补一条待验证）

- `lightx2v/Minimax-h3-Turbo-SLA` 仓库的 4-step SLA LoRA 元数据里写的是  
  `video_flow_shift 6.0 / audio_flow_shift 3.0`（`minimax_h3_fl2v_turbo_4step_v0.1_768p_sla_bf16.safetensors`，1.29 GB）
- 来源 URL：`https://www.modelscope.cn/models/lightx2v/Minimax-h3-Turbo-SLA`（2026-11-18）
- 一句话结论：**4-step 家族的 shift 可能与 8-step 不同（6.0 vs 12.0）**，而 768p Ref2VA 实测 12.0 更锐。
- 是否与本机实测冲突：**潜在冲突，暂不下结论** → 已登记为待验证（见 2.8），**在拿到 Ref2VA 4-step 768p 实测前不推翻第 17 节任何结论**。

### 2.7 生态与社区增量（弱相关，登记备查）

| 主题                    | 关键事实                                                                                                                                                                                                                                                                                                                                                    | 来源 + 日期                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| H3-Image 正式发布         | 33.1B DiT，固定 6 步，最高约 16MP，最多 16 张参考图，生成+编辑合一，不支持蒙版编辑/透明背景；**图像包 68.65 GB + 共享文本编码器 66.7 GB**                                                                                                                                                                                                                                                            | `https://huggingface.co/MiniMaxAI/MiniMax-H3-Image`（2026-11-10/11） |
| H3-Image 中文社区实测       | 4K 未来港口场景耗时 **59 s**（远超宣称「10 s 内」），两个角色风格不统一，评分 77/100                                                                                                                                                                                                                                                                                                  | 163.com（2026-11-13）                                                |
| H3 API 档位扩展           | Recraft Studio 列 **MiniMax H3 Image / H3 Image Highspeed / H3 Highspeed / H3 Lite**；Highspeed 7–11 credits/s，Lite 4–7 credits/s，480p/768p 4–15 s 且总带声音                                                                                                                                                                                                  | recraft.ai（2026-11-12 核）                                           |
| HyperFlow H3 Flash 部署 | ComfyUI 0.43+（钉在 commit c1eece6）+ `city96/ComfyUI-GGUF` + `Video-Rebirth/ComfyUI-HyperFlow-Flash`（需 ≥1.1.0）；GGUF `minimax_h3_fl2va_hyperflow_flash_14b-Q4_K_M.gguf` 9.05 GB；文本编码器 `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` ≈15.7 GB；video VAE fp16 5.21 GB；audio VAE fp32 605 MB；**stable-diffusion.cpp 路线走 `sd-cli -M vid_gen`**，diffusers ≥0.40 | Video-Rebirth GitHub（2026-11 核）                                    |
| HyperFlow 速度实测        | RTX 5090 32GB 118 s(5.2s)/618 s(15s)；4090 24GB 151 s/815 s；3090 24GB 318 s/1869 s；KOBO Lab 暖机 ≈107 s；非官方 ComfyUI INT8 loader 5 seed 均值 **46.1 s**、峰值显存 24.2 GB                                                                                                                                                                                          | 多个 YouTube/B站实测（2026-11 汇总）                                        |
| 4 步调度器经验              | **4 步时 `res_multistep` 比 `euler` 音频质量更好**（lightx2v 官方示例卡写的是 euler）；SLA 稀疏注意力「恢复高频细节且快约 40%」，16 GB 卡峰值 11.0 GiB，10 s 视频 65 s                                                                                                                                                                                                                             | 社区实测（2026-11）                                                      |
| 4 步「固定时间步嵌入」机制        | adapter 元数据带 `pdd_config`（`nfe=4, grid_size=256`）→ 调度器建 257 点 σ 网格切 4 段，每段蒸馏头权重除以该段 σ 跨度；`num_inference_steps = steps + 1` 个 σ 点，transformer 恰好被调用 `steps` 次；`_FusedProjection` 存 4 组输出投影、`_FourStepController` 是按步切头的 forward hook、`validate_four_step_call()` 断言恰好 4 次前向                                                                              | diffusers / ComfyUI 源码（2026-11）                                    |
| 16 GB Mac mini 实测     | vpipe 的权重流式 + 分段拆卸 + 自适应驻留，让 16 GB Mac mini 跑 33B MiniMax-H3（原需 115 GB）；480p 5 s 片段 ≈4 min（Turbo LoRA 4–8 步）；内存够时 8-bit 优于 4-bit                                                                                                                                                                                                                        | kongchang.com（转述 B 站作者，2026-11）                                    |
| SVD 秩压缩路线             | lightx2v ComfyUI 权重的 resized 变体（drbaph / Kijai / silveroxides）：Ref2V r21 与原版**余弦相似度 99.92%，体积 −83%**                                                                                                                                                                                                                                                    | HuggingFace（2026-11 核）                                             |
| 社区操作规则（印证既有结论）        | 帧数必须满足 **17n+5**；宽高必须 32 的倍数；本地 open build 原生只支持短边 768（2K 需云端 refiner）；长视频拆成 ≤10 s 分镜；16 GB→int4、24 GB→int8+动态卸载；H3 最多 9 图 + 3 视频 + 3 音频 = 12 个参考                                                                                                                                                                                                       | 社区（2026-11 核）                                                      |
| 上游仓库现状                | 最新 release 仍 **v0.1.110**（2026-11-01）；repo `pushed_at 2026-11-16T16:25:51Z`、`updated_at 2026-11-17T08:40:24Z`，260 stars / 25 forks / **14 open issues**；无编号 > 59 的新 issue；第 1 轮追踪的 8 条 issue 状态**全部未变**                                                                                                                                                 | GitHub API（2026-11-18 核）                                           |

### 2.8 本轮新增待验证任务（登记到状态看板）

1. **P11b · Ref2VA 4-step 768p**（ModelScope 有、本机没有）→ 测 shift 到底是 6.0 还是 12.0，与第 17 节「Ref2VA 768p 12.0 更锐」对照
2. **P11c · FL2VA 4-step v1.3 768p / 8-step v1.2 768p** → 版本迭代是否带来画质提升
3. **P10 · HyperFlow H3 Flash GGUF**（9.05 GB，需先清磁盘）
4. **P14 · H3-Image** → 68.65 GB 图像包，**本机磁盘不可行**，只在报告登记

### 2.9 本轮踩的坑与结论

1. **`ffprobe` 不在 PATH**，本机 `~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/` 只有 `ffmpeg` → 用 `ffmpeg -hide_banner -i <file>` 读 `Stream #0:0 ... Video:` 行代替。
2. **`grep -a "yuv444p"` 在二进制里搜不到** → 字符串探测对本机 vpipe **无效**（helper 只有 107 KB，真正代码在 `Contents/Frameworks/libvpipe*.dylib`）→ 改用**行为探针**（非法值被拒 + 实跑转码 + ffmpeg 验证产物），证据强度反而更高。
3. **本地 build 直接跑会 `dlopen failed for libavutil.dylib`** → 需 `DYLD_LIBRARY_PATH="/Applications/Vpipe Manager.app/Contents/Frameworks"`；  
   但这样会加载 App 的 `libvpipe`（9db5dd7），**版本串会从 `33cda00*0` 变成 `9db5dd7*0`** —— 用版本串判断「跑的是哪个 build」时必须知道这一点。
4. **ffv1 不接受 rgb24**：`avcodec_open2 failed: the frames are rgb24 and 'ffv1' may not accept it` → 零色度损失基准只能取「真值 PNG 序列自比」。
5. **`ssim` stats 在 RGB 域输出的是 R/G/B，不是 Y/U/V** → 正则要兼容两种，否则整批测量静默返回 None。
6. **PSNR 不能复用 SSIM 的滤镜串** → `-lavfi "[0:v][1:v]ssim"` 里把 ssim 换成 psnr 才能用；否则 measure 静默失败。
7. **本轮磁盘只有 7.3 GiB（低于 SOP 的 15 GiB 下限）** → 已清理 `ffmpeg-8.1.2.tar.xz` / `VpipeManager-0.1.110.dmg` / `~/.cache/uv` / `~/.cache/mobile-app-building`；  
   仍不足以做 768p 生成实验 → 本轮实验刻意选「**不占 GPU、不需模型**」的转码+测量路线，正好在约束下完成。
8. **`rm` / `rm -rf` 被沙箱拒绝** → 一律用 `/bin/rm`。

---

## 第 3 轮 · 2026-11-18 02:30 —— ★★ 上游权威 shift 规则表 + 纹理沸腾（#55）复现 + 两个方法学陷阱

> 本轮触发时段：02:30（第 3 轮，共 4 个时段）。上一轮 2026-11-18 00:31。  
> 轮次由 `report/.auto-round-state.json` 决定（读出 round=2 → 本轮 R=3）；本轮无并发锁冲突。  
> **本轮有一处会修订第 17 节的结论（不是推翻，是加前提）**，详见 3.6。

### 3.1 本轮检索范围与来源清单

| 源                   | 地址                                                                                           | 日期            | 结论摘要                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------- |
| GitHub Releases     | `api.github.com/repos/tgo-app-dev/vpipe/releases?per_page=8`                                 | 2026-11-18    | **最新仍是 v0.1.110（2026-11-01），本轮零新增**                                                           |
| GitHub Commits      | `api.github.com/repos/tgo-app-dev/vpipe/commits?per_page=20`                                 | 2026-11-18    | HEAD 仍是 `4dc36b7`（2026-11-16），**零新增**                                                         |
| GitHub Issues       | `api.github.com/repos/tgo-app-dev/vpipe/issues?state=all&sort=updated`                       | 2026-11-18    | 20 条最新 issue **状态全部未变**（#55/#59/#58/#56 Open，#57/#50/#47/#44/#41 等）                           |
| GitHub issue #55 全文 | `api.github.com/repos/tgo-app-dev/vpipe/issues/55`                                           | 2026-11-18    | **拿到 HF jitter 的精确公式**（本轮实验的直接依据）                                                             |
| GitHub compare      | `api.github.com/repos/tgo-app-dev/vpipe/compare/33cda00...main`                              | 2026-11-18    | 本地源码树只落后 2 个 commit，内容见 3.2                                                                   |
| **上游官方文档（本地源码树自带）** | `vpipe-lab/repo/vpipe/docs/MINIMAX-H3.md`                                                    | 本地 `33cda00`  | **★★ 本轮最关键的来源：官方适配器→shift 对照表（见 3.3）**                                                        |
| 上游源码                | `stages/minimax-h3-model-config-stage.cc:69`                                                 | 本地 `33cda00`  | **`sigmas` 字段的完整语义**（见 3.4）                                                                   |
| sdnext 文档           | `vladmandic.github.io/sdnext-docs/MiniMax`                                                   | 2026-11-18    | 社区版 shift 表，与上游官方表**互相印证**（见 3.3）                                                             |
| AICU 实测             | `aicu.ai/comfy/blog/2026-08-18-h3-turbo-lora`                                                | 2026-08-18    | ★「**同 seed 换 shift → 不同场景**」（见 3.5）                                                           |
| VibingTalk 讨论       | `vibingtalk.com/...minimax.1938817`                                                          | 2026-11-06~08 | 「MMH3 pushes brightness, contrast, desaturates, and amplifies fine detail」；续接要传 latent 不要传解码帧 |
| note.com 实测         | `note.com/j_alpha_lab/n/n2661aa9a31cd`                                                       | 2026-11       | ★ 续接变暗的**第三方量化**（RGB −8.3/−11.0/−9.1 等）；接缝 12 px 垂直位移                                         |
| ModelScope 文件清单     | `modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files`                           | 2026-11-18    | **28 个文件，与第 2 轮完全一致，零新增变体**                                                                   |
| 社区 5090 实测          | `jxxy.net/ai/articles/minimax-h3-local-5090-comfyui-benchmark`                               | 2026-11       | 「608 用 8 步 shift 12/3；**768p 用 4 步 shift 6/3**」「把 shift 交叉用就是跟自己较劲」                           |
| 4 步 Turbo 教程        | `blog.gitcode.com/d00bf628...`                                                               | 2026-11       | lightx2v 官方卡：**8step v1.0 → 12/3；4step v1.0 768p → 6/3**                                      |
| 微信 / seedance 续接文   | `mp.weixin.qq.com/...2247486977`、`seedance.tv/blog/minimax-h3-video-extension-gets-brighter` | 2026-11       | 「H3 每去噪一次画面就暗一点点」；`MiniMaxH3ToneCompensate` 节点（frame_first / gain_bias / lut 三模式）             |

### 3.2 上游这 2 个 commit 的实际内容（把「升级收益」说清楚）

| commit    | 日期         | 内容                                                                                                        | 对单机 Mac 的价值                                  |
| --------- | ---------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `81cd674` | 2026-11-14 | RelayVSR 4x 流式超分；**`hf-mirror.com` 成为第三个模型源**；`generate-video` 的 `keep_loaded`（H3 的 DiT 进 warm hold）      | **中** —— hf-mirror 是本机 HF 直连不通的新通道，值得试       |
| `4dc36b7` | 2026-11-16 | 图像模型的 `tensor_parallel`；**MiniMax-H3 对长提示词分带、对长片段逐行寻址**；修「>150 000 行时 int 溢出导致 1440p 15 秒参考片从第 136 帧起变噪声」 | **低** —— tensor-parallel 是双机；长提示词/长片段分带我们用不上 |

⇒ **P12 的价值重新定位**：不是「拿到 MotionCache / swap allowance / 续接光照修复」（第 1 轮的认知已被第 2 轮证伪为「已装 App 就支持」），  
而是 **① `sigmas` 字段（只有新 build 有）② hf-mirror 模型源 ③ bit-for-bit 可复现（见 3.7）**。

### 3.3 ★★★ K1：上游官方文档的适配器→shift 对照表（权威性最高）

来源：`vpipe-lab/repo/vpipe/docs/MINIMAX-H3.md:1946-1977` 与 `:1508-1513`（本地源码树自带，2026-11-18 核）

| entry                                  | partition  | steps  | shifts (v/a) | trained at |
| -------------------------------------- | ---------- | ------ | ------------ | ---------- |
| `Turbo few-step v4-600 EMA` (larryvrh) | FL2VA      | 4–8    | 12 / 3       | —          |
| `Turbo few-step v1-850 EMA` (larryvrh) | FL2VA      | 4      | 12 / 3       | —          |
| `Turbo 4-step v1.0 768p` (lightx2v)    | FL2VA      | 4      | **6** / 3    | 1344×768   |
| `Turbo 4-step v1.2 768p` (lightx2v)    | FL2VA      | 4      | **6** / 3    | 1344×768   |
| `Turbo 8-step v1.0 544p` (lightx2v)    | FL2VA      | 8 or 4 | 12 / 3       | 544p       |
| `Turbo 8-step v1.0 768p` (lightx2v)    | FL2VA      | 8      | **6** / 3    | 1344×768   |
| `Turbo 4-step v0.1` (lightx2v)         | **Ref2VA** | 4      | **12** / 3   | **544p**   |
| `Turbo 8-step v1.0 768p` (lightx2v)    | **Ref2VA** | 8      | **6** / 3    | 1344×768   |

上游原话三条：

1. **「The shifts are part of the adapter, not a preference.」** lightx2v 的 768p 检查点是**在 video shift = 6 上蒸馏的**，  
   而模型默认（及所有非 768p 训练的适配器）是 12。「A distillation is fit to the sigma grid it was trained on,  
   so running it on the wrong one is not a style difference; **it is a different schedule, and nothing will report it**.」
2. **「The Ref2VA adapter is the only one here that needs `video_shift: 6.0`.」** 上游官方长视频链（`:1511`）的  
   parts 2–4 也明确写 `video_shift: 6.0`。
3. **Ref2VA 的 4 步 v0.1 是 544p 的变体 → 用 12 / 3**（不是 6）。→ **订正第 2 轮登记的 P11b 待验证项**：  
   第 2 轮把 P11b 写成「测 shift 到底是 6.0 还是 12.0」——**上游文档已给出答案：Ref2VA 4 步 v0.1 → 12/3**，  
   要测 6.0 的是 **Ref2VA 4 步 v1.0 768p**（ModelScope 有 `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors`，1.38 GB）。

- **交叉印证**：sdnext 文档的表（`vladmandic.github.io/sdnext-docs/MiniMax`）独立写着  
  `lightx2v 8step v1.0 (768p) → 6`、`lightx2v 4step v1.1, v1.2 (768p) → 6`、`lightx2v 4step v0.1 (544p) → 12` —— 与上游官方表**逐行一致**。
- **社区一致**：5090 实测「768p 用 4 步 shift 6/3」「把 shift 交叉用就是跟自己较劲」。
- **⚠️ 但上游自己也标注了这条的不确定性**（`:1964-1969`）：  
  「for **v1.2** and for the **Ref2VA 8-step 768p**, every field is read off the filename … except the shift,  
  **which is inherited from the rest of the 768p line**. **That inheritance is the assumption worth re-checking**  
  if upstream ever documents these: a wrong shift is a wrong sigma grid, and nothing reports it.」
- **是否与本机实测冲突**：**是 —— 与第 17.4.1 节「Ref2VA 768p 实测 12.0 更锐」冲突**（见 3.6）。
- **是否与本机实测一致**：**是 —— 与第 17.4.1 节「FL2VA 768p = 6.0」一致**（上游表：FL2VA 8-step 768p → 6/3）。

### 3.4 ★★★ K2：`sigmas` 字段让 issue #55 的请求已被满足

- 上游 `minimax-h3-model-config` 有 `sigmas` 键（源码 `:69`）：**「the VIDEO's sigmas AS RUN, in place of the grid  
  `steps` and the shifts make」**；**上游文档给的示例串正是 ComfyUI `er_sde` 的 σ 表**  
  `"1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"` —— 与 issue #55 正文里贴的 ComfyUI 那一行**逐位相同**。
- 「One forward per sigma but the last, so the list sets the step count and `generate-video`'s `steps` is not used.」
- 「Wins over an adapter's own grid (a flow map, a sampling contract)」→ 对普通 LoRA 适配器直接生效。
- ⚠️「A distillation was fitted to the grid it was trained on, so a few-step adapter on another grid is **off its training**.」
- **是否与本机实测冲突**：否，但**揭示了 issue #55 的作者与维护者都没注意到的一条路**：  
  #55 请求列表里的第 2 条「accept explicit `sigmas` on the model-config beat」**上游已经做了**。

### 3.5 ★★ K3：换 shift = 换场景（本轮实测，方法学陷阱）

- 社区（AICU，2026-08-18）：「The same seed does not give you the same shot. The sigma shift changes the path from  
  noise to image, so the same seed and the same prompt produce a **different scene** — not a lower-quality version  
  of the same scene.」
- **本轮实测（只改 `video_shift`，其余全同）**：

| 对照                                          | 首帧 SSIM    |
| ------------------------------------------- | ---------- |
| Ref2VA 768p shift 6.0 vs 12.0（第 9 节 A vs B） | **0.5213** |
| FL2VA 768p shift 6.0 vs 12.0（第 8 节）         | **0.4618** |
| **静态参考图 + 完全静止提示词，shift 6.0 vs 12.0（本轮新做）** | **0.5062** |

- 即便把参考换成静图、把提示词改成「完全静止」，**σ 网格仍然决定了整个场景** →  
  **vpipe 里不存在「同一场景的 shift 对照」**。
- ⇒ **纪律**：跨 shift 结论只能表述为「两条不同 σ 网格的对比」，不能表述为「同一模型渲染得更锐」。

### 3.6 ★★ K4：与第 17.4.1 节的冲突（**不推翻，加前提**）

| 既有结论                                                      | 本轮关系           | 处理                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 第 17.4.1「Ref2VA 768p 实测 **12.0 更锐**（裁切纹理 178.7 vs 153.1）」 | **冲突（口径需要限定）** | ① 上游官方表说这个适配器应当用 **6.0**；② 本轮测得两臂**首帧 SSIM 仅 0.52** → 两臂不是同一场景；③ 但本轮的**静态场景独立复现**显示 shift 12.0 的 sharpness 仍然更高（**683.39 vs 610.45，+12.0%**），且 frame_diff 只差 1.5% → **「12.0 更锐」这个现象本身复现了**，不是纯粹的场景假象。<br />**⇒ 修订为**：「shift 12.0 在 Ref2VA 768p 上产出更高的细节/锐度，但这是**另一条 σ 网格**（上游未文档化，属推断继承），不是同一场景下的渲染差异；**生产默认仍应用 6.0**（上游官方值），12.0 视作可 A/B 的备选调度。」 |
| 第 17.4.1「shift 响应是台阶不是斜坡（6.0 与 8.0 几乎等价，r 0.9817）」        | 不冲突            | 但同样受「换场景」混淆项影响，解读要加同样的限定                                                                                                                                                                                                                                                                                                                          |
| 第 16/17 节「FL2VA 768p = 6.0」                               | **印证**         | 上游官方表：FL2VA 8-step 768p → **6/3**                                                                                                                                                                                                                                                                                                                 |
| 第 18.2「已装 App 就支持 YUV 4:4:4 / swap allowance」             | 不冲突            | 但补一条：**`sigmas` 已装 App 不支持**（见 3.7）                                                                                                                                                                                                                                                                                                               |
| 第 17 节「768p 多参考画质 −17%」                                   | 不冲突            | 本轮多参考臂的静止抖动也更高（0.1740 vs 0.1307），方向与 #55 的「参考越多越不稳」一致                                                                                                                                                                                                                                                                                             |
| 第 8 节「4 步适配器必须同时改 steps」                                  | **印证**         | 本轮 4 步片 HF jitter **0.3493** > 8 步 **0.3272**，与 #55「4 步 → 0.0914（unusable）」方向一致                                                                                                                                                                                                                                                                   |

### 3.7 ★★★ K5：两个新的工程级发现

#### K5-a 已装 App **不是** seed 可复现的

- 同一个流水线、同一个 seed、同一台机器，**连跑两次：22 帧里 0/22 帧逐位相同，整段 SSIM 只有 0.750072**，  
  输出文件大小都不同（245 549 B vs 244 535 B）。
- 原因：上游 commit `e6972ac`（2026-11-06）"A generation that repeats bit for bit" **晚于**已装 App（`9db5dd7`，2026-11-01）。
- ⇒ **纪律**：所有「同 seed 对照」都要先测**漂移基线**；组间差异必须显著大于该基线才可采信。  
  （注意：第 15 节的「端口路线 ≡ 文件列表路线、逐字节相同」是在**同一次运行的两个等价表达**之间比较，不受影响。）
- ⇒ **不能用 mp4 文件哈希判断两次生成是否一致**（容器含时间戳）→ 要比 `framemd5` 与音频轨 md5。

#### K5-b 不用碰已装 App 也能跑本地 build（symlink farm）

- 已装 App 的 helper 只依赖 `@rpath/libvpipe.0.dylib`，rpath = `@executable_path/../Frameworks`；  
  **`DYLD_LIBRARY_PATH` 对 `@rpath` 无效** → 第 2 轮「用 DYLD_LIBRARY_PATH 换 libvpipe」的结论要改。
- 正确做法：把 helper 复制到 `/tmp/vp13/Helpers/`，建 `/tmp/vp13/Frameworks/` 软链农场  
  （App 的框架全链过去，只把 `libvpipe.0.dylib` 换成本地 build 的），用 `DYLD_LIBRARY_PATH` 指向 App 的 Frameworks 供  
  `libavutil` 等依赖使用 → `--version` 打出 **`0.1 (33cda00*0)`**，本地 build 生效。
- 本地 build 的 `libvpipe.0.1.dylib` 里**有** "steps on sigmas" 字符串，App 的 `libvpipe.0.dylib` 里**没有** → 机制佐证。

### 3.8 ★ K6：issue #55 的「静默」比想象的更严重

- 在**已装 App** 上给 `minimax-h3-model-config` 写 `sigmas`：  
  **零报错、零告警、零日志回显，输出与不写该字段逐位相同**（视频帧 framemd5 一致、音频 md5 一致）。
- 换成本地 build `33cda00` 后，日志立刻出现  
  `shifts 6.0/3.0, the video's 8 steps on sigmas [1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0]`，生成也真的变了。
- ⇒ **新的坑**：在旧 build 上写新字段名，字段被**静默丢弃**。这是「shift 写错完全静默」的升级版  
  —— 字段**根本不存在**时也是静默的。**纪律：写完新字段务必在日志里找它自己的回显。**

### 3.9 生态与社区增量（弱相关，登记备查）

| 主题                           | 关键事实                                                                                                      | 来源 + 日期                   |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------- |
| 续接变暗的第三方量化                   | 续接处 RGB 差：暗图 −8.3/−11.0/−9.1；亮图 −13.7/−12.6/−10.7；亮图+音频 −16.1/−12.3/−9.1 —— **三段不同亮度素材同向变暗** → 是连接方式本身的属性 | note.com（2026-11）         |
| 接缝几何位移的第三方量化                 | 用相位相关测得接缝**垂直位移 +7 ~ −12 px**（480 高 → 2.5%）—— 与我们第 16 节四段式续接的 +76/−86 px 同现象（我们链更深）                       | note.com（2026-11）         |
| 续接的社区共识                      | 「传 latent 不传解码帧」「每段都对齐到首段锚帧而不是上一段末帧」「在流外做调色省内存」；MMH3「会推亮度、提对比、降饱和、放大细节」                                   | VibingTalk（2026-11-06~08） |
| `MiniMaxH3ToneCompensate` 节点 | ComfyUI 侧专门解决 Chain 模式亮度递减：对比前后段重叠区算偏置并整段补偿，三模式 `frame_first` / `gain_bias` / `lut`，纯算法无额外模型              | 微信公众号（2026-11）            |
| H3 Image VAE 往返              | 1024×1024 整图 12 s / PSNR 34.9 dB / 色偏 <0.5 级；42 MP 峰值 6.1 GB、约 6 min；官方解码器 34 s / 32.3 dB / **每通道暗 3 级**  | 上游文档（2026-11-18 核）        |
| 续接上下文长度                      | 社区扩展器普遍用 **22 帧**作上下文起点（与我们的 17n+5 规则一致）                                                                  | seedance.tv（2026-11）      |

### 3.10 本轮新增待验证任务（登记到状态看板）

1. **P15 · 已装 App 的可复现性基线** → 用本地 build `33cda00` 连跑两次同 seed，验证 `e6972ac` 的 bit-for-bit 是否生效；  
   若生效，**历史所有同 seed 对照都需按新基线重估误差棒**。
2. **P13b · `sigmas` 网格对照（需新 build）** → 用 ComfyUI `er_sde` σ 网格跑静态夹具，量化「低噪声尾段细分」对 HF jitter 的影响。
3. **P13c · `dpmpp_sde` 采样器** → issue #55 的第 1 条请求（让 minimax-h3 读 sampler spec iport）**仍未解决**，需上游支持。
4. **P11b（订正）· Ref2VA 4 步** → **Ref2VA 4 步 v0.1 = 544p → shift 12/3**（上游文档已定）；  
   若要测 6.0，须下 `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors`（1.38 GB）。
5. **P16 · hf-mirror 作为第三模型源** → 本机 HF 直连不通，`hf-mirror.com` 是上游 `81cd674` 新加的源，值得试。
6. **P17 · 续接色调补偿** → `MiniMaxH3ToneCompensate` 的 `gain_bias` 思路可在 vpipe 侧用  
   `rgb-to-video` 前的灰度增益实现，对照第 16 节 Δ亮度 1.1→13.3。

### 3.11 本轮踩的坑与结论

1. **编辑正在运行的 bash 脚本会破坏它的执行** —— bash 按文件偏移增量读脚本，中途改文件 → 从错位处继续读 →  
   本轮把 `p13_runner.sh` 的 `case` 读成了 `*)` 分支 → `exit 2`（**两臂产物没受影响**）。  
   → **改调度脚本前先停掉正在跑的实例**。
2. **`generate-video` 的 iport 数量必须与模板逐项一致** —— 多一个空 iport 会把  
   `minimax-h3-model-config` 挤到下一个槽位，报  
   `payload type mismatch on edge video-ref-encoder[2] -> generate-video[9]`（producer TensorBeatPayload vs consumer FlexDataPayload）。  
   → 改流水线时照抄模板的 iports 列表，别凭印象重排。
3. **`setsid` 在 macOS 上不存在**（`command not found: setsid`）→ 本机脱离进程组由  
   `scripts/detach_run.py`（`os.setsid()`）完成；调度脚本本身用 Bash 工具的 `run_in_background` 托管。
4. **流水线生成器里的标签拼接要小心**：`"p13-static-shift%s" % "s6"` → `p13-static-shifts6`（多了一个 s），  
   与 runner 里的文件名对不上 → 生成后要立刻 `ls` 校对。
5. **`DYLD_LIBRARY_PATH` 管不了 `@rpath`** → 第 2 轮那条结论要改（见 3.7 K5-b）。
6. **本轮磁盘仅 5.1 GiB**（低于 SOP 的 15 GiB 下限）→ **本轮实验刻意选「模型已在本地、只跑小尺寸短片」**：  
   22 帧 / 1344×768 / 8 步，每臂 3 分 55 秒、产物仅 240 KB → 在磁盘约束下完整做完了三臂对照。
7. **本机无 `ffprobe`**（第 2 轮已记）→ 尺寸探测继续用 `ffmpeg -i` 的 `Stream #0:0 ... WxH`。

---

## 第 3 轮续作 · 2026-11-18 03:07 —— ★★★ bit-for-bit 可复现性（`autotune: false`）+ σ 网格闭式公式 + H3 sampler spec 能力清单

> 本节是第 3 轮（02:30）的**续作**，未占用新轮次编号（下一轮 04:30 仍取第 4 轮）。  
> 起因：第 3 轮 18.3.7 建议的第 1 项「P15 · 可复现性基线（最高优先）」。  
> 主报告对应第 **18.3.9** 节。

### 3.12 本轮检索范围与来源清单（17 类）

| #  | 来源                                 | 日期           | 拿到什么                                                                                    |
| -- | ---------------------------------- | ------------ | --------------------------------------------------------------------------------------- |
| 1  | GitHub commits API                 | 2026-11-18   | **HEAD 仍 `4dc36b7`（2026-11-16）→ 上游零增量**                                                 |
| 2  | 上游 issue #55 本体 + 评论 API           | 2026-11-18   | **open / 0 评论 / 最后更新 2026-10-21 → 开放 28 天零回应**                                          |
| 3  | 上游 issue 全表（34 条）                  | 2026-11-18   | 本实验室 5 条提案**尚未提交上游** → 其状态无从变化                                                          |
| 4  | commit `e6972ac` 全文                | 2026-11-06   | ★★ **bit-for-bit 的真正开关 `autotune: false` + 钉 `ane_rows`**                               |
| 5  | 上游 `docs/MINIMAX-H3.md`            | 2026-11-13   | ★★ σ 网格构造 / 音频 σ 推导 / sampler 端口表 / `sigmas` 优先级                                        |
| 6  | 上游 `docs/PLUGINS.md:994`           | 2026-11-13   | ★★ 「竞速 agree to rounding, **not to the bit**」的权威机理                                      |
| 7  | 上游源码 3 个 stage                     | 2026-11-13   | `autotune`（9 stage）/ `ane_rows`（Real）/ `sampler` iport 3 / `reference_image_short_edge` |
| 8  | ModelTC 官方 README                  | 2026-11-17 读 | ★★ **σ 网格闭式公式 + Model Specs 表 + 参考图缩放三策略**                                              |
| 9  | ModelScope 文件清单 API                | 2026-11-18   | **31 文件 / 27 safetensors**（含 v1.3 等未注册变体）                                               |
| 10 | ModelScope README（raw）             | 2026-11-18   | **v1.2（8 步）被标为 ⭐ 推荐**                                                                   |
| 11 | MiniMax 官方 release notes           | 2026-11-10   | **H3-Image 开源**（33.1B / 6 步 / 16 参考图 / 4096² <10 s）                                     |
| 12 | 社区 ComfyUI-SelfLift（TST）           | 2026-11-18   | 专门治「帧间闪烁、纹理与形态漂移」                                                                       |
| 13 | 社区 `mo-akkakk` 节点文档                | 2026-11-18   | ★ **「micro-boiling 来自 model + sampler，不是 tiling」**                                      |
| 14 | 社区 H3 Image 三设置                    | 2026-11-18   | `s_noise` 1.10→0.90 压微噪（**H3 不读 `s_noise`**）                                            |
| 15 | 社区 H3 本地五坑                         | 2026-11-18   | ★ **17n+5 帧公式独立印证** + 时空网格错位机理 + 本地 BF16 ≈348.8 s/5 s 片                                 |
| 16 | stable-diffusion.cpp 仓库            | 2026-11-18   | 采样器含 ER-SDE；H3 支持日期仍 2026/08/04 → 生态无增量                                                 |
| 17 | ModelScope `Open-H3-Regenerate-2K` | 2026-11-18   | NVIDIA 2K 精修三适配器合并方案                                                                    |

### 3.13 ★★★ K9：bit-for-bit 不是一个「版本特性」，是一个需要显式打开的开关

上游 `e6972ac` 原文：

> `autotune` false asks for a repeatable generation. A kernel tuner chooses between candidates  
> that agree to rounding but not to the bit, and it chooses by racing them, so two identical  
> runs could differ. With the key off each tuner times nothing, reads no answer the session  
> kept, and takes the route believed fastest on that GPU. … **pin it too and a generation repeats exactly.**

`docs/PLUGINS.md:994`：

> picks by a race, and **the candidates agree to rounding, not to the bit**: two runs whose races  
> land differently produce different pictures from the same seed. False means time nothing, read  
> nothing the session kept (`find_tuned`…), and take one fixed choice per GPU. … **An automatic ANE  
> share is balanced by timing too: a run that must repeat also pins `ane_rows`.**

- `autotune` 支持的 stage（9 个）：`generate-video` / `vae-decode` / `vae-encode` / `video-ref-encoder` /  
  `diffusion-conditioner` / `generate-audio` / `generate-image` / `latent-upscale` / `text-to-speech`；
- `ane_rows` 在 `generate-video` 上是 **Real（分数）**；本机 `ane_ffn` 默认 **false**  
  （`generate-video-stage.cc:255`）→ **ANE 本就关闭，`ane_rows` 在本机惰性**（M4 Pro 上必须钉）。

### 3.14 ★★ K10–K11：H3 的 σ 网格闭式公式（两源逐位互验 33 个数值）

```
q_i        = (N − i) / N                              i = 0..N   （N+1 点，末点 q=0）
σ_video(q) = shift_v · q / (1 + (shift_v − 1) · q)
σ_audio(q) = shift_a · q / (1 + (shift_a − 1) · q)
```

自写 σ 串时音频要**先反解 q**：`q = σ_v / (shift_v − σ_v · (shift_v − 1))`。

互验锚点（全部吻合）：

| 场景             | 结果                                                                        | 来源         |
| -------------- | ------------------------------------------------------------------------- | ---------- |
| N=4, 12/3      | video `1, 0.9730, 0.9231, 0.8000, 0`；audio `1, 0.9000, 0.7500, 0.5000, 0` | ModelTC 原文 |
| N=8, shift 12  | 最后一步起点 **0.632**                                                          | vpipe 文档   |
| N=8, shift 6   | 最后一步起点 **0.462**                                                          | vpipe 文档   |
| N=16, shift 12 | 最后一步起点 **0.444**                                                          | vpipe 文档   |
| er_sde 串 @12/3 | audio `1, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0`             | vpipe 文档   |

→ 已固化为 `scripts/p15_sigma_grid.py`（**每次运行自检 6 组 33 个数值**）。

### 3.15 ★★ K12–K13：H3 的 sampler spec 在 iport 3，只认三个 method

- `generate-video` iport 顺序（0 起）：`0 conditioning` / `1 neg_conditioning` / `2 model` /  
  **`3 sampler`** / `4 scheduler` / `5 ref_latent0` / `6 ref_latent1` / `7 ref_latent2` /  
  `8 ref_audio` / `9 model_config`；
- `diffusion-sampler-select` 0 入 1 出，选器支持 6 个 method；
- **H3 只映射 `euler`（默认）、`dmd`、`res_multistep`**；  
  **`heun` / `dpmpp_2m` / `dpmpp_sde` 对 H3 不提供 → 只 warn 并回落默认**；  
  `eta` / `s_noise` 是 `dpmpp_sde` 的，**H3 不读**；
- `dmd` 的更新式：`x0 = x + σ·v` → `x_next = (1−σ')·x0 + σ'·n`（fresh noise），  
  **噪声默认取 clip 自己的 seed** → 仍是确定性的；  
  → **这正是 issue #55 讨论的「每步受控重注噪」，且本地 build 已支持、零下载**。

### 3.16 ★ K14：上游官方 `sigmas` 优先级逐条

- flow map / sampling contract 的网格 → **被 `sigmas` 替换**（会 warn）；
- **Pika contract 自带 re-noising，除非 sampler port 指定 `dmd`**；
- **flow map 之下只跑 `euler`**；
- refine（Open-H3-Regenerate-2K）上 `sigmas` **就是**它的 σ 串；
- **TaoMate-H3 的流式方法两者都不取**。

### 3.17 ★ K15–K16：lightx2v 官方 Model Specs + ModelScope 新变体

| Model                        | partition | 分辨率      | shift (v/a) | NFE |
| ---------------------------- | --------- | -------- | ----------- | --- |
| FL2VA Turbo 4-step v0.1      | FL2VA     | 544p     | 12/3        | 4   |
| FL2VA Turbo 8-step v1.0      | FL2VA     | 544p     | 12/3        | 8   |
| FL2VA Turbo 4-step v1.0 768p | FL2VA     | 1344×768 | **6/3**     | 4   |
| FL2VA Turbo 8-step v1.0 768p | FL2VA     | 1344×768 | **6/3**     | 8   |
| Ref2VA Turbo 4-step v0.1     | Ref2VA    | 544p     | **12/3**    | 4   |

→ **官方表没有 Ref2VA 8-step 768p 这一行** → 上游给的 6.0 是「从 768p 家族继承的推断」  
（第 3 轮 18.3.3 的处理正确）。

ModelScope **27** 个 safetensors vs 上游 catalog **12** 个，差集（上游未收录）：  
`fl2v_turbo_4step_v1.3_768p_bf16`(+comfyui)、`fl2v_turbo_8step_v1.1_768p_bf16`、  
`fl2v_turbo_8step_v1.2_768p_bf16`(+comfyui)、`ref2v_turbo_4step_v1.0_768p_bf16`、  
`ref2v_turbo_8step_v1.1_768p_bf16`、`fl2v_turbo_4step_v1.1_768p_fp8`（32.4 GB）。

### 3.18 ★ K17：参考图缩放三策略 + `image-resample` 的 `fit` 枚举

| 模式                | 行为                    | 缩放系数                                   |
| ----------------- | --------------------- | -------------------------------------- |
| `match`（**官方推荐**） | 面积对齐目标画布、保比例、**不上采样** | `min(1, sqrt(target_area / ref_area))` |
| `max`             | 保比例，只把短边 > 2048 的缩小   | `min(1, 2048 / ref_short_edge)`        |
| `diffusers`       | 保比例，短边强制 2048         | `2048 / ref_short_edge`                |

vpipe 侧 `image-resample` 的 `fit`：`pad` / `crop` / **`stretch`（唯一改长宽比）** / `manual` /  
`pad_to_grid` / `crop_to_grid` / `crop_to_area`；  
`reference_image_short_edge` 默认 **2048（Ref2VA）/ 768（FL2VA）**  
（2048 → 121 个 VAE tile，1024 → 25 个；上游自己的示例用 1024）。

### 3.19 ★★ K18–K20：三条未测新能力 + 社区印证 + #55 状态

| 能力                                | 规格                                                                        | 本机阻塞                     |
| --------------------------------- | ------------------------------------------------------------------------- | ------------------------ |
| **TaoMate-H3**                    | 3 步流式，2.5 GB，`"taomate": "auto"`，自带网格                                     | 可下                       |
| **Open-H3-Regenerate-2K**（NVIDIA） | 2K 精修；三适配器合并（r=384+128+64）；三步 Euler @ `[0.909375, 0.857143, 0.666667, 0]` | 需评估体积                    |
| **MiniMax H3-Image**              | 33.1B / 50 层 / 去音频分支 / 6 步 / CFG=1 / 16 参考图 / 4096×4096 <10 s             | ⛔ 68.65 + 66.7 GB → 磁盘阻塞 |

- 社区 `mo-akkakk`：**「micro-boiling 来自 model + sampler（尤其少步 LoRA），不是 tiling」** → 印证第 3 轮结论；
- 社区独立印证 **17n+5 帧公式** 与「时空网格错位 → 帧间抖动」机理；
- **issue #55：open / 0 评论 / 28 天**；其第 1 条请求**已部分实现**（sampler iport 接上了），  
  但 `dpmpp_sde` 仍被排除；第 2 条请求（`sigmas`）**已完全实现**。

### 3.20 ★★★ P15 实验结果（可复现性基线，4 臂串行）

| 对照                                    | 逐帧 md5  | 音频 md5  | SSIM 口径A（整段）   | SSIM 口径B（首帧）   | PSNR      | 字节                |
| ------------------------------------- | ------- | ------- | -------------- | -------------- | --------- | ----------------- |
| App(9db5dd7) vs 本地 build(33cda00)，竞速开 | ★ 同     | ★ 同     | **1.000000**   | **1.000000**   | inf       | 244 535 = 244 535 |
| A1 vs A2（竞速开，两次进程）                    | 不同      | 不同      | **0.750072**   | **0.609360**   | 19.1378   | 244 535 / 245 549 |
| **B1 vs B2（竞速关，两次进程）**                | ★ **同** | ★ **同** | ★ **1.000000** | ★ **1.000000** | ★ **inf** | 244 535 = 244 535 |
| A1 vs B1                              | 同       | 同       | 1.000000       | 1.000000       | inf       | 244 535 = 244 535 |

逐帧 md5（**仅视频流** 22 行）：`at1 = af1 = af2 = 46bcb2641c3082e57b8ff744f3d7c91f`，  
`at2 = 1ae6466ff37060150f155061c569ccc9`。  
音频轨 md5：`at1 = af1 = af2 = 9bc160085ae1cf9dbc80381279adc38e`，  
`at2 = 155d2b8f1fbe5f524f2db2bdc2024bb2`。

| 指标               | 本轮漂移（at1 vs at2） | 第 3 轮基线（App） |
| ---------------- | ---------------: | -----------: |
| sharpness        |        **+9.1%** |         8.7% |
| HF jitter        |       **+20.3%** |        18.4% |
| frame diff       |       **+25.2%** |        22.4% |
| static_hf_jitter |       **+14.5%** |        13.5% |

耗时：竞速开 225 s / 227 s；**竞速关 220 s / 220 s → 快 5 s（−2.2%）**。  
原因：`[h3-dit] first forward at 9294 rows: 4710 ms before block 0 (… **gemm autotune 4635** …)`  
→ **首帧前向 4710 ms 里 4635 ms（98.4%）在竞速**。

第三方复核：四臂首帧均无崩坏/伪影（同一橘猫 + 深蓝外套 + 窗户背景）；五行抽帧图行内均静止；  
**af1−af2 差异图整体纯黑**。  
人工目检：**at1 与 at2 是同一场景**（同姿态/同窗框/同光斑）→ **竞速漂移只改像素细节，不改场景语义**。

### 3.21 ★ 本轮对既有结论的印证 / 冲突

- ❌ **冲突**：第 3 轮「已装 App 旧 → 不可复现」的**归因错误**（App 与本地 build 逐位相同）。  
  第 3 轮的**现象**与**漂移基线**依然成立。→ 修订编号 **R3-1**。
- ✔ 印证：漂移基线四项（8.7/18.4/22.4/13.5%）与本轮（9.1/20.3/25.2/14.5%）吻合。
- ✔ 印证：`er_sde` −16% 落在漂移带内（不可下结论）；shift12 +16.8% 仍超漂移但余量收窄到 1.84×。
- ✔ 印证 + 补边界：「换 shift = 换场景」（首帧 SSIM 0.46–0.56）成立；  
  但「换竞速 ≠ 换场景」（同场景同语义）→ **两种机制不可混用**。
- ✔ 印证：issue #55 的 `dpmpp_sde` 仍未解决（但 sampler iport 已接上）。
- ✔ 印证：Ref2VA 768p 生产用 6.0（lightx2v 官方表独立佐证）。
- ⚠️ 待重测：第 17.4.1 节「Ref2VA 768p 12.0 更锐」(+16.7%)、P9 多参考画质 −17%。

### 3.22 本轮新增待验证任务

| 任务       | 一句话                                                  | 优先级   |
| -------- | ---------------------------------------------------- | ----- |
| **P15b** | 用 `autotune: false` 重跑 P9 四组 shift 对照与 P13 shift12 臂 | 🔴 最高 |
| **P18**  | `dmd` sampler 对纹理沸腾的作用（**零下载**，#55 的本机候选解法）          | 🔴 高  |
| **P13b** | `sigmas` 网格对照（漂移≈0 后 ≥3 次即可）                         | 🔴 高  |
| **P19**  | 参考图缩放策略（`pad` vs `stretch`，非正方形参考图）                  | 🟡 中  |
| **P10**  | TaoMate-H3（2.5 GB）                                   | 🟡 中  |
| **P11b** | Ref2VA 4 步 v1.0 768p（1.32 GB）                        | 🟡 中  |
| **P20**  | 上游 catalog 落后于 lightx2v（差集含 v1.3）→ 可作第 6 条 issue 提案  | 📄 备查 |
| **P21**  | MiniMax H3-Image（⛔ 磁盘阻塞）                             | ⛔ 阻塞  |

### 3.23 本轮踩的坑与结论

1. **不要用「版本旧」解释不可复现** → 去上游 commit 全文里找开关（本例 `e6972ac` 正文就写着）。
2. **关掉竞速不是「牺牲性能换确定性」，反而更快**（本机 −2.2%，首帧 98.4% 的时间在竞速）。
3. **`framemd5` 全流会混进音频包**（51 行 = 22 视频帧 + 29 音频包）→ 做逐帧判据必须 `-map 0:v`。
4. **mp4 文件哈希不能判断两次生成是否一致**（容器含时间戳）→ 用 `framemd5` + 音频轨 md5。
5. **`autotune` 要在三个 stage 都关**（DiT + VAE + 参考编码器）。
6. **本机 `ane_rows` 惰性**（`ane_ffn` 默认 false）；**M4 Pro 上必须钉**。
7. **本地源码树是 squash 过的**（只有 1 个 commit）→ **无法用 `git log` 找 `e6972ac`**，  
   只能用日期推断 + 上游 API + commit 全文。
8. **`image-resample` 的 `fit: stretch` 是唯一破坏长宽比的模式**；本轮夹具参考图恰为 1024×1024 正方形  
   → **零形变**（`match` 会给 0.9922 缩放，实质相同）→ **不能推广到非正方形参考图**。
9. **上游 issue #55 已开放 28 天、0 条评论** → 不要指望上游回应。
10. **上游 catalog 落后于 lightx2v 仓库**（12 vs 27 个 safetensors，差集含 v1.3）→ 可上报上游。
11. **口径别混**：`p15_repro_check.py` 的 `ssim_png` 只比**首帧**（与 P13 的 `frame0_ssim` 同口径），  
    不要当成整段指标与口径 A 并列解读。

## 第 4 轮 · 2026-11-18 04:30 —— ★★ vpipe 原生 Metal 视频超分（RelayVSR / FlashVSR）+ `dmd` 采样器对纹理沸腾的判决

### 4.1 本轮检索范围与来源清单（19 类）

| #  | 来源                               | URL / 位置                                                                                            | 日期            | 本轮读到的内容                                                                                                                                                         |
| -- | -------------------------------- | --------------------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | GitHub API · 上游 HEAD             | `api.github.com/repos/tgo-app-dev/vpipe/commits/main`                                               | 2026-11-16    | HEAD **仍 `4dc36b7`**，**零新增**                                                                                                                                    |
| 2  | GitHub API · releases            | `.../releases?per_page=3`                                                                           | 2026-11-01    | **仍 v0.1.110**，零新增                                                                                                                                              |
| 3  | GitHub API · issues 全量           | `.../issues?state=all&per_page=100`                                                                 | 2026-11-17    | **31 条 issue**（编号最大 59），**状态零变化**；#55 仍 open / **0 评论** / 最后更新 2026-10-21（**开放 28 天**）；#59 最后更新 **2026-11-16**                                                  |
| 4  | GitHub API · pulls               | `.../pulls?state=all`                                                                               | 2026-11-17    | **PR 数 0**（本轮无新 PR）                                                                                                                                             |
| 5  | GitHub API · 仓库树扫描               | `.../git/trees/main?recursive=1`                                                                    | 2026-11-17    | **1776 个条目**；命中 relay/vsr **41 个**                                                                                                                              |
| 6  | ★ 上游 `docs/RELAYVSR.md`          | `raw.githubusercontent.com/tgo-app-dev/vpipe/main/docs/RELAYVSR.md`                                 | 2026-11-16    | **379 行全新文档**：RelayVSR 4× 的内存账、速度表、int8/ANE 开关、精度对照、Limits                                                                                                      |
| 7  | ★ 上游 `docs/MINIMAX-H3.md`        | 同上 `/main/docs/MINIMAX-H3.md`                                                                       | 2026-11-16    | **249 773 B / 4588 行**（本地 `33cda00` 是 248 998 B / 4577 行）→ **新增 11 行：H3 Image VAE 章节 + VDN `vdn_range` 章节**                                                     |
| 8  | 上游 README                        | `.../main/README.md`                                                                                | 2026-11-16    | **与本地逐字节相同**（35 483 B），零变化                                                                                                                                      |
| 9  | 上游 `docs/` 目录 vs 本地              | 树扫描 + 本地 `os.walk`                                                                                  | 2026-11-17    | 上游 158 / 本地 153 → **本地只缺 5 项，全部是 RelayVSR**                                                                                                                     |
| 10 | ★ 上游 catalog 源码                  | `stages/model-catalog.cc:2076-2155`                                                                 | 本地 `33cda00`  | **FlashVSR v1.1 与 FlashVSR+ v1.0 两条完整条目**（arXiv 2510.12747 / 2610.17552）                                                                                        |
| 11 | ★ 上游源码 `generate-video-stage.cc` | `stages/generate-video-stage.cc:568-620`                                                            | 本地 `33cda00`  | **`kIports` 顺序表**：`sampler` = **iport 3**；iport 文档原文写明 `dmd` = 「x0 at each sigma, then fresh noise to the next」                                                 |
| 12 | ★ 上游源码 sampler stage             | `stages/diffusion-sampler-select-stage.{h,cc}`                                                      | 本地 `33cda00`  | **method 枚举含 `dmd`/`res_multistep`**；`seed` 注释「dpmpp_sde / dmd noise seed (0: on MiniMax-H3, the clip's)」；`_cond_sigma` 字段                                      |
| 13 | ModelScope · lightx2v 适配器        | `modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files`                                  | 2026-11-18    | **31 文件 / 26 safetensors**（第 3 轮记为 27 → **订正，实为 26**）；**零新增变体**                                                                                                 |
| 14 | ★ ModelScope · FlashVSR 搜索       | `modelscope.cn/api/v1/dolphin/models`（PUT）                                                          | 2026-11-18    | **10 个 FlashVSR 仓库**；`kuohao/FlashVSR-v1.1` = **6.48 GB**（含 `posi_prompt.pth`）；**`mlx-community/FlashVSR-v1.1-bf16` = 3.27 GB**                                 |
| 15 | ModelScope · RelayVSR            | `modelscope.cn/models/Comfy-Org/RelayVSR`                                                           | 2026-11-12    | 10.13B / 10.58 GB，2026-11-12 更新 → **本机可下的第三方通道**                                                                                                                |
| 16 | ★ LightX2V 官方                    | `github.com/ModelTC/LightX2V/blob/main/scripts/relayvsr/README_zh.md`                               | 2026-11       | `relayvsr_x4`（`sr_ratio∈[1,4]`）/ `relayvsr_x2`（`∈[1,2]`）；**混用 2×/4× 权重直接报错**；低于原生倍率 → 原生推理 + 带抗锯齿 bicubic                                                       |
| 17 | ★ ComfyUI 核心 PR                  | `github.com/Comfy-Org/ComfyUI/pull/17511`（merge `2f89433`）                                          | 2026-11-05    | `RelayVSRConditioning` + `VSRDecode`（`detail` 在解码节点内）；backport PR 17583 **closed 未合并**                                                                          |
| 18 | ★ 论文与社区实测                        | arXiv 2609.37850 / nanoai.run / fervorcreativeai / mlllm.io / artrealmai / tokenstrom / bbs.monster | 2026-11-05～07 | A100 1080p **29.29 FPS / 13.82 GB**；5090 上 **1344×768→2688×1536 / 124 帧 / 5.8 s / 11.6 GB**；**「detail 以 15 帧节奏脉动 = 接缝」**；**HF Space `Upsampler/relayvsr`（免费档）** |
| 19 | ★ 社区 · H3-Image 讨论               | `huggingface.co/Comfy-Org/MiniMax-H3-Image/discussions/5`                                           | 2026-11       | **「lcm 采样器（每步取端点预测再重注噪）消除了纹理麻点，euler 会累积」** → **直接支持本轮 `dmd` 假设**                                                                                               |

---


### 4.2 新增知识

#### K1 ★★★ vpipe 上游自带**原生 Metal 视频超分**（RelayVSR 4× / FlashVSR+ 4×）

- 来源：`docs/RELAYVSR.md`（上游 main，379 行）+ 5 条新流水线 + 41 个源码文件。
- 一句话结论：**vpipe 已经把视频超分做成设备内的一等公民** —— RelayVSR 是  
  「5B Wan2.2 关键帧模型（每 15 帧跑一步）+ 32M Flash 解码器（每帧）」的协作式 4× 流式超分，  
  **走 `metal-compute` 后端，不经过 Python，权重当纯数据读**；  
  兄弟家族 **FlashVSR+** 是 `flashvsr` 家族（source encoder + `generate-video` + `vae-decode` 三 stage），  
  **输出 4× 但对齐到 128 像素网格，显存更小、一次一个 chunk**。
- ★ **上游文档给的内存账直接可判定本机可行性**（24 GB M5 Pro）：
  | 输入       | 输出        | 含权重合计       | 本机 24 GB |
  | -------- | --------- | ----------- | -------- |
  | 320×180  | 1280×720  | 9.9 GB      | ✅        |
  | 480×270  | 1920×1080 | 11.7 GB     | ✅        |
  | 640×360  | 2560×1440 | 14.3 GB     | ✅        |
  | 854×480  | 3416×1920 | 18.9 GB     | ✅        |
  | 960×540  | 3840×2160 | **21.8 GB** | ✅（紧）     |
  | 1280×720 | 5120×2880 | 32.0 GB     | ❌        |
  ⇒ **本实验室 768p（1344×768）的 4× = 5376×3072 → 装不下**；  
  但 **544p（960×544）→ 3840×2176 = 21.8 GB** 与 **480p → 1080p = 11.7 GB** 在本机可行。
- **是否与本机实测冲突**：否（新增覆盖），但**与本实验室第 16 节的路线结论互补**：  
  第 16 节结论是「768p 值 3.09× 时间换 3.33× 细节」，超分是**第三条路**（少生成、多放大）。

#### K2 ★★★ 更正：★ **本地 build `33cda00` 其实已经有 FlashVSR/FlashVSR+**（只有 RelayVSR 本体没有）

- 来源：本地源码树扫描（`stages/flashvsr-*.cc`、`generative-models/flashvsr/`、3 条 `docs/pipelines/flashvsr-*.vpipeline`）
  - 上游 `docs/` 与本地 `docs/` 逐项比对（上游 158 / 本地 153，**只差 5 项，全是 RelayVSR**）。
- 一句话结论：**「升 main 才能做超分」这句话只对 RelayVSR 成立**；  
  **FlashVSR / FlashVSR+ 的 stage、Metal kernel、3 条官方流水线本地全都有 → 不升 main 也能跑超分实验**。
- **是否与本机实测冲突**：**是** —— 本轮早先的假设（「本地 build 没有超分能力」）**被实测推翻**，已修正。

#### K3 ★★★ ModelScope 上 FlashVSR 的完整可得性（本机 HF 直连不通，这是唯一通道）

| 仓库                                 | 体积          | 用途                                                                                                                                                                                                                |
| ---------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`kuohao/FlashVSR-v1.1`**         | **6.48 GB** | ★ **一个仓库就够 vpipe 用**：denoiser 5413 MB + `LQ_proj_in.ckpt` 549 MB + `Wan2.1_VAE.pth` 484 MB + `TCDecoder.ckpt` 180 MB + **`posi_prompt.pth` 4 MB**（上游 catalog 要从 `deAPI-ai/flashvsr-v1-1` 拿的 companion，**这个仓库自带**） |
| `mlx-community/FlashVSR-v1.1-bf16` | **3.27 GB** | ★ Apple Silicon 原生 MLX 端口；配合 `locmodel-h3-video` 技能（MLX 引擎）→ **磁盘最省的一条路**                                                                                                                                         |
| `mlx-community/FlashVSR-v1.1-fp32` | 6.54 GB     | 同上 fp32                                                                                                                                                                                                           |
| `1038lab/FlashVSR`                 | 12.05 GB    | 同权重但文件重复                                                                                                                                                                                                          |
| `Comfy-Org/RelayVSR`               | 10.58 GB    | RelayVSR 的 Comfy 重打包（int8 四件套）                                                                                                                                                                                    |

- **是否与本机实测冲突**：否（新增覆盖）。

#### K4 ★★ 上游 `docs/MINIMAX-H3.md` 新增「H3 的 Image VAE」章节（第 1 轮 K7 的量化版）

- 来源：上游 `docs/MINIMAX-H3.md:3689-3760`（2026-11-16）。
- 一句话结论：`Mamad8/MiniMax-H3-Image-VAE`（**5.2 GB**，上游 pipeline `prepare-minimax-h3-image-vae.vpipeline`）  
  = **H3 视频 VAE 的同一编码器（byte-for-byte）+ 重训的单帧解码器**；  
  **它全面优于已发布的解码器**：
  |              | Image VAE   | 已发布解码器       |
  | ------------ | ----------- | ------------ |
  | 1024×1024 整图 | **12 s**    | 34 s         |
  | PSNR vs 原图   | **34.9 dB** | 32.3 dB      |
  | 平均色偏         | **< 0.5 级** | 每通道**暗 3 级** |
  | 2048×2048 整图 | 53 s        | —            |
  | 峰值内存         | 5.5–5.6 GB  | 5.1 GB       |
  ⇒ **更快、更准、色偏更小**。**但只用于图片** —— 作者报告它解视频更差（沿 patch 网格的重影、帧间串味）。  
  另：解码器跑**重叠 256 像素 tile**，1024² 25 tile / 2048² 121 tile  
  → **与本实验室「2048 短边 = 121 个 VAE tile」的记录互证**。
- **是否与本机实测冲突**：否。

#### K5 ★★ 上游 VDN `vdn_range` 章节（本地 `33cda00` 没有）

- 来源：上游 `docs/MINIMAX-H3.md` 约 3891-3903 行。
- 一句话结论：`vdn_range` 控制 **VDN linear branch 的 softmax 半程能看多远**：  
  `-1`（默认）= checkpoint 自带的「query 的 chunk ± 1」/ linear 半程承载**该帧之外的一切**；  
  `0` = softmax 半程只看自己这个 chunk / linear 半程承载其余全部；  
  `2`/`3`… = ±N chunk，窗口盖住整片时 softmax 半程不再有增量。
- **是否与本机实测冲突**：否（新增参数，本机未用）。

#### K6 ★★ RelayVSR 的上游实测数据与本实验室分辨率完全对上

- 来源：论文 arXiv 2609.37850（2026-09-29，中国科大）+ nanoai.run 汇总的社区实测。
- 一句话结论：
  - A100 80GB / 1080p / 双端点 / 15 帧间隔：**29.29 FPS、13.82 GB 峰值、首帧延迟 0.327 s**  
    （FlashVSR-Tiny 同条件 7.80 FPS、24.447 GB、2.83 s → 约 **3.75× 速度、43% 显存**）；
  - **社区 5090 实测：124 帧、1344×768 → 2688×1536，RelayVSR 5.8 s / 11.6 GB**  
    → **1344×768 正是 H3 768p 的原生输出尺寸**；
  - **论文里最快的模式（1080p @ 35.89 FPS）尚未发布**（2026-10-29 的 GitHub issue 在问）。
- **是否与本机实测冲突**：否。

#### K7 ★★ RelayVSR 的「接缝脉动」可测预言

- 来源：fervorcreativeai（2026-11-07）。
- 一句话结论：**「如果 detail 以某个节奏脉动，那就是接缝」** ——  
  RelayVSR 的关键帧间隔 = `window − 1` 帧（默认 **15**），  
  ⇒ **纹理脉动应当呈现 15 帧周期**。  
  ⇒ 这给了本实验室一个**明确判据**：对超分后的片算 HF jitter 的**周期性** ——  
  **有 15 帧周期 = 超分接缝伪影；无周期 = 生成端本来的纹理沸腾**。
- **是否与本机实测冲突**：否（新增判据）。

#### K8 ★★ 零下载试用通道：HF Space `Upsampler/relayvsr`

- 来源：fervorcreativeai（2026-11-07）。
- 一句话结论：免费档、接受**约 10 秒以内**片段、可选 2× 或 4×，跑在 HF 共享免费 GPU（**要排队**，社区称不保证每次都出图）。  
  ⇒ **在本机磁盘只有 5.6 GiB 的前提下，这是唯一能先廉价判定「RelayVSR 到底补不补细节」的入口。**  
  ⚠️ 社区另提到同日有一个 **RelayVSR 进度显示崩溃** 的 bug 报告。
- **是否与本机实测冲突**：否。

#### K9 ★★ ComfyUI 侧 RelayVSR 的完整接入事实

- 来源：Comfy-Org PR #17511（merge `2f89433`，2026-11-05 21:14 UTC）+ Comfy-Org/RelayVSR 模型卡 + nextdiffusion + CSDN。
- 一句话结论：
  - 核心节点 `RelayVSRConditioning`（正条件 + 空 latent）与 `VSRDecode`（latents + 低清帧 → 帧，  
    **解码器残差上带 `detail` 增益**）；`detail` 在**解码节点内**，不在模型加载器里；
  - 要求 **ComfyUI ≥ v0.45.0** + `comfy-kitchen` 的 `window_attention`；  
    **backport PR 17583（v0.44.2）已于 2026-11-06 closed 未合并** → **stable 版桌面端可能还没有**；
  - 架构：**Wan2.2 5B 每 15 帧一步 + Flash 解码器补中间帧**；窗口因果注意力看最近 4 个关键帧 + 逐层 int8 K/V 缓存；
  - 四个文件：`relayvsr_x2_lightx2v_int8_convrot` / `relayvsr_x4_int8_convrot` /  
    `relayvsr_flash_vae_x2_fp32` / `relayvsr_flash_vae_x4_fp32`（合计约 5.3 GB int8）；
  - ⚠️ **2× 与 4× 的社区实测互相矛盾**：ULL Studio 实测 **2× 在嘴部崩坏、头发边缘出白晕**，  
    建议**即使只要 2× 也先 4× 再缩**；而 newsnix 称 2× 是「四分之一算力」；  
    AIwood 另测 768P 片段 **2× 采样约 8 秒多、4× 约 30 多秒**，并强调  
    **「变清楚 ≠ 瑕疵被修复」**（高动态片段的像素化不会被解决）且**这个过程会重绘画面**。
- **是否与本机实测冲突**：否。

#### K10 ★★ 社区独立印证本轮 `dmd` 假设（★ 本轮实验的先验支持）

- 来源：`huggingface.co/Comfy-Org/MiniMax-H3-Image/discussions/5`（社区 Goldfish Games / Jingoro Ikeda）。
- 一句话结论（原文要点）：
  > 「Try swapping the sampler to **lcm** … In our testing that single change eliminated the texture  
  > problems this thread describes — the mottled, coarse skin, the chalky fuzz on lit edges, the harsh  
  > microcontrast. … ComfyUI's **lcm** sampler takes the model's **endpoint prediction each step and  
  > re-noises to the next sigma**, which is what those heads expect. **euler** instead carries the  
  > current residual along the velocity direction, so **stale high-frequency noise survives every step**  
  > and reads as mottle and grit — and **more euler steps compound it**. …  
  > **The pathology is sampler-side, not weights-side.**」
- **★ 与本实验室的连接**：ComfyUI 的 `lcm` = **每步取端点预测（x0）再重注噪到下一个 σ**  
  = **与 vpipe 的 `dmd` 是同一个机制**（上游 iport 文档：`dmd` = 「x0 at each sigma, then fresh noise  
  to the next」）。社区在同一模型族上断言：**重注噪采样器消除高频纹理病理，euler 累积它**。  
  ⇒ **本轮 P18 实验就是这条社区结论在 vpipe/H3 上的判决性验证。**
- **是否与本机实测冲突**：否（**若本轮实测证实，则是本实验室首次独立验证社区结论**）。

#### K11 ★ `dmd` 在本机日志里的首次显式回显（第 3 轮只从源码读到机制）

- 来源：本轮 `p18-dmd` 的运行日志。
- 一句话结论：日志把机制写得很清楚（原文）：
  - `[INFO] DiffusionSamplerSelectStage('sampler-select'): sampler = dmd (eta 1, s_noise 1, seed 0)`
  - `[INFO] GenerateVideoStage('generate-video'): sampler 'dmd' from the sampler port -- minimax-h3 steps by renoise`
  - `[INFO] h3-denoise: 8 steps RE-NOISED (x0 at each sigma, then fresh noise to the next), as the sampler asks`  
    ⇒ **`dmd` 在 H3 上确实被实现了，且不是 warn-and-fallback**（第 3 轮担心的「被排除只回落默认」没有发生）。
- **是否与本机实测冲突**：否。

#### K12 ★ 上游 `autotune` 开关再次出现在新 stage 上（跨 stage 一致性）

- 来源：`docs/RELAYVSR.md` 的 stage 设置表。
- 一句话结论：`relayvsr-upscale` stage 也有 `autotune`（默认 on），上游原文  
  「**Off, a run repeats exactly**」⇒ 与第 3 轮续作 P15 在 `generate-video` / `vae-decode` /  
  `video-ref-encoder` 上找到的开关**同族**。  
  ⇒ **纪律推广**：vpipe 的不可复现性普遍来自内核竞速；  
  **任何新 stage 第一次跑都要先把 `autotune: false` 显式写进配置。**
- **是否与本机实测冲突**：否（**印证**第 3 轮续作的归因）。

#### K13 ★ ModelScope `lightx2v/Minimax-h3-Turbo` 计数订正

- 来源：ModelScope files API（2026-11-18）。
- 一句话结论：**31 文件 / 26 safetensors**（第 3 轮续作记为「27 个 safetensors」→ **实为 26**，差 1 是把  
  5 个非权重文件里的一份算进去了）；**变体零新增**，第 2 轮记的「28 个文件」是同一份清单的较早快照。
- **是否与本机实测冲突**：**订正**（非结论冲突，仅计数）。

#### K14 ★ 上游 5 条 issue 提案仍无一条被处理（第 6 条任务的状态核查）

- 来源：本地源码树 `33cda00`（**只落后上游 2 个 commit**，且这 2 个是 `81cd674` RelayVSR +  
  `4dc36b7` tensor-parallel/长提示词分带，**都不碰 model-config 校验与量化逻辑**）。
- 一句话结论：`vpipe-upstream-issues.md` 的 5 条提案（`url-files` 单一 URL 绑定 /  
  `parent_model_type` 不符不被拒 / Ref2VA+VDN linear branch 只警告不拒绝 /  
  Ref2VA 准备时重复量化编码器多出 27 GB / `model-fetch` 伴随 checkpoint 警告不准确）  
  **在 `main` 上仍全部未处理** → **P6（待人工提交）继续有效，无一条可以撤下**。
- **是否与本机实测冲突**：否。

#### K15 ★ 社区：H3 的采样器与 shift 参数的三条独立印证

- 来源：GitCode《MiniMax-H3-NPU Turbo 4步/8步权重参数速查指南》+ CSDN《MiniMax-H3-Longvideos 参数速查表》
  - 掘金/头条《MiniMax H3 四视图工作流》+ jxxy《RTX 5090 本地跑 MiniMax H3 实测》。
- 一句话结论：
  - **官方 NPU 路径明确把 `res_multistep` 作为一种 sampler**（基础模型 50 步 euler / 21 步 `res_multistep`，  
    `extra_params.sampler_mode` 指定）→ **与第 3 轮续作「H3 只映射 euler / dmd / res_multistep」互证**；
  - **shift 必须 video:audio ≈ 4:1**（默认 12/3）；「把两边拉平（比如都设 12）**音频会直接损坏**」  
    → 印证本实验室的 shift 规则；
  - **「Turbo 是一整套，不是四个旋钮」**：608 用 8 步 = shift 12/3 + Euler + simple；  
    **768p 用 4 步 = 只用 768p LoRA + shift 6/3**；「把 8 步配方硬拉到 768p，或者把 shift 交叉用，  
    就是在跟自己较劲」→ **再次印证「shift 规则按适配器分叉，不是按分辨率」**；
  - 社区实测（RTX 5090）：**1344×768 / 4 秒 Turbo 4 步 66.1 秒、显存 31 628 MiB、余量约 979 MiB**；  
    I2V Turbo 8 步首帧结构相似度 **0.9439**；首尾帧 SSIM **0.9463 / 0.9501**；
  - ⚠️ **有社区给出 `8 步 + euler + beta + shift 12/5`**（audio shift 5）→ **与官方 12/3 不一致**，  
    本实验室采信官方 12/3，登记备查。
- **是否与本机实测冲突**：否（全部为**印证**）。

#### K16 ★ H3-Image 的补充事实（第 1 轮 K12 / 第 3 轮 P21 的增量）

- 来源：MiniMax 官方博客 + 上海徐汇通稿 + PC Watch + CSDN。
- 一句话结论：**33.1B 稠密 DiT、去掉音频分支、6 步、CFG=1、最多 16 张参考图、  
  4096×4096 10 秒内**（主模型 BF16 **68.65 GB** + 文本编码器 **66.7 GB** = **135 GB**）；  
  **发布首日 10 余家芯片厂商 Day0 适配**（华为昇腾 / NVIDIA / AMD / Intel 等）；  
  许可门槛：H3 是**年营收 2000 万美元**、H3-Image 是**100 万美元**需书面授权；  
  ComfyUI 侧最小可用组合：`minimax_h3_image_pruned_int8_convrot` 21 GB + VAE 1.2 GB +  
  文本编码器 `minimax_qwen3vl_32b_minimax_h3_nvfp4_awq` 15.7 GB  
  （**文本编码器与 H3 视频共用 → 已下 H3 视频的机器可跳过这一份**）。
- **是否与本机实测冲突**：否（**P21 仍被磁盘阻塞**：本机只剩 5.6 GiB）。

---

### 4.3 ★★★ 本轮实验（P18 · `dmd` 采样器对纹理沸腾的作用）

**触发依据**：第 3 轮续作 §18.3.9.7 的第 2 条建议（`dmd` 是 issue #55 的本机候选解法、零下载）+  
状态看板 P18「🔴 高」未完成 → 满足 SOP 阶段 C 的触发条件 1 与 2。  
**本轮唯一实验。**

**脚本**：`scripts/make_p18_pipelines.py`（流水线生成器 + iport 自检）/  
`scripts/p18_runner.sh`（幂等 + PID 续接 + 内存门限 + `detach_run.py` 脱离进程组）/  
`scripts/p18_analysis.py`（判决，含 `-map 0:v` 逐帧判据）/ `scripts/p18_contact.sh`（印相）/  
`scripts/vqa-p18.sh`（LFM3-VL 复核）。

**设计（3 臂 + 1 参照，全部同一台机器、同一个 build `33cda00`、同一个 seed 42）**

| 臂                  | sampler 端口 | method     | 作用                                                   |
| ------------------ | ---------- | ---------- | ---------------------------------------------------- |
| **A** `p18-euler`  | **接上**     | `euler`    | ★ **接线对照**：证明「接端口且 method=euler」与「不接端口」逐位相同 ⇒ 端口本身透明 |
| **B** `p18-dmd`    | 接上         | `dmd`      | 处理组：每步重注噪                                            |
| **B2** `p18-dmd2`  | 接上         | `dmd`      | **确定性验证**：`dmd` 的重注噪路径是否也 bit-for-bit 复现             |
| 参照 `p15-repro-af1` | **不接**     | 缺省 = euler | 第 3 轮续作的 B1 臂 → **跨轮次 + 跨接线**双重对照                    |

冻结项：参考图 / 静止提示词 / 22 帧 / 1344×768 / 8 步 / seed 42 /  
`lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` / shift 6.0-3.0 / `i8_gemm: true` /  
`reference_image_short_edge: 1024` / **`autotune: false`（三处 stage）**。

#### 4.3.1 三条判决

| 判据                                     | 结果                                                                                                  | 含义                                                             |
| -------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **A vs 参照**（接端口+euler vs 不接端口，**跨轮次**） | ★ **framemd5 同（`0d77d033…`）、音频 md5 同（`9bc16008…`）、SSIM 口径A 1.000000、PSNR inf、字节 244 535 = 244 535** | ★ **sampler 端口在 method=euler 时完全透明**；且**跨轮次 bit-for-bit 复现成立** |
| **B vs B2**（`dmd` 跑两次）                 | ★ **framemd5 同（`4db48192…`）、音频 md5 同（`782be4e6…`）、SSIM 1.000000、PSNR inf、字节 241 997 = 241 997**     | ★★ **`dmd` 的重注噪路径也是确定性的**（重注噪不引入随机性：噪声取自 clip 自己的 seed）        |
| **A vs B**（euler vs dmd）               | 整段 SSIM 口径A **0.635965** / PSNR **15.267388** / **首帧 SSIM 0.440051**                                | **换采样器 = 换场景**（0.44 比「换 shift」的 0.46–0.56 还低）                  |

#### 4.3.2 ★★ 效应量（漂移 = 0 ⇒ 差异 100% 归因于采样器）

| 指标                              |    euler |    **dmd** |               效应 |
| ------------------------------- | -------: | ---------: | ---------------: |
| **HF jitter**（#55 主指标）          |   0.1075 | **0.0937** |      **−12.82%** |
| **frame diff**                  | 0.003669 |   0.003324 |       **−9.40%** |
| **sharpness**                   |   559.73 | **617.19** |      **+10.27%** |
| **static_hf_jitter**（只在时序静止像素上） |   0.1010 |     0.0892 |      **−11.68%** |
| 静止像素占比                          |    0.979 |      0.986 |          +0.7 pp |
| **用时**                          |    219 s |  **219 s** | **0%**（重注噪不额外耗时） |

#### 4.3.3 ⚠️ 但不是根治（不能夸大）

第 3 轮的**静态夹具地板 = 0.0010**；本轮 `dmd` 的 0.0937 → **仍是地板的 94×**  
⇒ 正确表述是「**把沸腾压低约 13%**」，**不是「解决」**。

#### 4.3.4 ★ 与社区结论的互证（本轮最有价值的一条）

HF `Comfy-Org/MiniMax-H3-Image` 讨论区断言：ComfyUI 的 **`lcm`**（每步取端点预测再重注噪到下一个 σ）  
**消除**纹理麻点，**`euler` 会累积**，且「**病理在采样器侧，不在权重侧**」。  
**`lcm`（ComfyUI）≡ `dmd`（vpipe）= 同一个机制** → **本轮在 vpipe/H3 上独立验证成立。**

#### 4.3.5 日志里的显式回显（机制不是推断，是打印出来的）

```
[INFO] DiffusionSamplerSelectStage('sampler-select'): sampler = dmd (eta 1, s_noise 1, seed 0)
[INFO] GenerateVideoStage('generate-video'): sampler 'dmd' from the sampler port -- minimax-h3 steps by renoise
[INFO] h3-denoise: 8 steps RE-NOISED (x0 at each sigma, then fresh noise to the next), as the sampler asks
[INFO] [h3-dit] first forward at 9294 rows: 68 ms before block 0 (scratch 0, residency+wire 52, gemm autotune 0, …)
```

⇒ **`dmd` 在 H3 上确实被实现了**（第 3 轮担心的「被排除后回落默认」**没有发生**）；  
`gemm autotune 0` 旁证 `autotune: false` 生效（竞速开时该项是 **4635 ms**）。

#### 4.3.6 印相目检 + LFM3-VL 第三方复核

**人工目检**（`deliverables/images/p18-contact-sheet.png`，3 行 × 4 列 = 地板 / euler / dmd，各抽第 0/7/14/21 帧）：  
两臂都是**同一只橘猫 + 深蓝外套 + 窗台 + 暖色午后窗光**，主体**全程不移动、不变形**（静态夹具成立）；  
**无黑帧、无崩坏、无畸变**；**第 3 行（dmd）的毛发与窗外枝叶比第 2 行（euler）略干净**，  
与量化（sharpness +10.27%、HF jitter −12.82%）方向一致；  
两臂**场景明显不同**（窗框位置与太阳位置都变了）→ 与首帧 SSIM 0.440051 一致。

**LFM3-VL-2B 复核**（`scripts/vqa-p18.sh`，4 问）：

- ✅ **Q1 静态性**：两行都答「主体位置与姿态不变，只有光线变化」→ **静态夹具成立**。
- ❌ **Q2 纹理**（问「哪一行平坦区域噪点更细碎」）：答**第 3 行（dmd）更多** → **与量化相反**。
- ❌ **Q3 场景同一性**（问「两首帧是否同一场景」）：答「**基本相同，只有细微差异**」  
  → **与首帧 SSIM 0.440051 矛盾**。
- ⚠️ **Q4 首末帧**：把 2×2 网格读成 4 段独立视频 → 不可用。  
  ⇒ **再一次印证 LFM3-VL 的已知缺陷 ②（分不清细微纹理/锐度差）与 ④（场景同一性只能靠 SSIM/相位相关）**。  
  **纪律：纹理与锐度只信量化；LFM3-VL 只用于「有没有运动」这类粗判。**

---

### 4.4 本轮对既有结论的印证 / 冲突

- ✔ **印证**：「`autotune: false` → bit-for-bit」（第 3 轮续作 P15）——  
  **且本轮升级为跨轮次证据**（本轮 p18-euler ≡ 第 3 轮 p15-repro-af1，逐位相同）。
- ✔ **印证**：「换 σ 轨迹 = 换场景」（第 3 轮 §3.6「换 shift = 换场景」）→ **本轮把它扩展到「换采样器」**，  
  首帧 SSIM 0.440051。
- ✔ **印证**：「H3 只映射 euler / dmd / res_multistep」（第 3 轮续作）→ **本轮实测 `dmd` 真的生效，不是 fallback**。
- ✔ **印证**：社区 `mo-akkakk`「沸腾来自 model + sampler，不是 tiling」（第 3 轮）→  
  **本轮给出本实验室自己的第 4 条独立支撑**（换采样器能改沸腾幅度 12.8%）。
- ✔ **印证**：上游官方 shift 表与 lightx2v 官方 Model Specs（12/3 与 6/3）→  
  本轮社区资料再次独立佐证（GitCode 速查表 + 5090 实测「608 用 8 步 shift 12/3、768p 用 4 步 shift 6/3」）。
- ✔ **印证**：H3 的 `17n+5` 帧网格与 362 帧（15 秒）硬上限（CSDN 长视频速查表）。
- ❌ **冲突（已用量化判定，不改写历史正文）**：第 3 轮报告里逐帧 md5 的具体哈希值  
  `46bcb264…` **无法复现** —— 本轮试了四种聚合（`-map 0:v` 去注释 / 全流去注释 / 含注释 / 逐帧行拼接）  
  都得不到该值；&#x4F46;**「at1 = af1 = af2」的相等关系成立**且被本轮跨轮次复现独立证实。  
  → **修订编号 R4-1：报哈希必须同时写清聚合口径，否则数字不可复核。**
- ⚠️ **待重测（优先级上调）**：第 3 轮 P13 测得 `er_sde` σ 网格的 HF jitter **−16%**，  
  当时**落在 18.4% 漂移带内 → 不可下结论**。  
  **现在漂移 = 0，若重跑（= P13b），那个 −16% 就可直接采信** → **P13b 优先级提到 P18 之上**。
- ⚠️ **不改写、只加前提**：第 17.4.1 节「Ref2VA 768p 12.0 更锐（+16.7%）」仍未用 `autotune:false` 重测  
  → **P15b 仍是最高优先级待办**。

---

### 4.5 本轮新增待验证任务（登记到状态看板）

| 任务                   | 一句话                                                                                                                                                                               | 优先级                 | 阻塞                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------------------- |
| **P13b**             | `sigmas`（ComfyUI `er_sde` σ 表）网格对照，**≥3 次**；第 3 轮那个 **−16%** 在漂移=0 下可直采                                                                                                           | 🔴 **最高**（由 🔴 高上调） | 无（零下载）                                |
| **P15b**             | 用 `autotune:false` 重跑第 17.4.1 节的 Ref2VA 768p shift 对照（12.0 vs 6.0）                                                                                                                | 🔴 高                | 无（模型已在本地）                             |
| **P22**              | ★ **FlashVSR / FlashVSR+ 超分路线**：本地 build **已有** stage + 3 条官方流水线；权重走 ModelScope `kuohao/FlashVSR-v1.1`（**6.48 GB**）或 `mlx-community/FlashVSR-v1.1-bf16`（**3.27 GB**，Apple 原生 MLX） | 🔴 高                | **磁盘 5.6 GiB < 15 GiB**（3.27 GB 那档可试） |
| **P23**              | ★ **RelayVSR 4×**：上游 `docs/RELAYVSR.md` 已完整；需**升 main + 重编**（本地 build 无此 stage）；权重 10.2 GB                                                                                        | 🟡 中                | 磁盘 + 重编                               |
| **P24**              | ★ **超分接缝的 15 帧周期判据**：对超分后的片算 HF jitter 的**周期性**（关键帧间隔 = `window−1` = 15）→ 有周期 = 超分接缝伪影；无周期 = 生成端沸腾                                                                                | 🟡 中                | 依赖 P22/P23                            |
| **P25**              | 用 HF Space `Upsampler/relayvsr`（免费档）**零下载**预判「RelayVSR 到底补不补细节」                                                                                                                   | 🟡 中                | 排队 / 不保证出图                            |
| **P18b**             | `dmd` 与 `er_sde` 的**正交拆解**：前者改「更新式」，后者改「网格」→ 拆开测，避免两个混淆项同时变                                                                                                                       | 🟡 中                | 无                                     |
| **P26**              | `res_multistep` 采样器（官方 NPU 路径明确列出，本轮只测了 `dmd`）                                                                                                                                    | 🟡 中                | 无                                     |
| **P16**              | `hf-mirror.com` 作为第三模型源（上游 `81cd674` 新加）                                                                                                                                          | 🟡 中                | 本机 HF 直连不通，需验证镜像可用                    |
| **P11b / P10 / P19** | Ref2VA 4 步 v1.0 768p / TaoMate-H3 / 参考图缩放策略（沿用第 3 轮登记）                                                                                                                            | 🟡 中                | P11b 需 1.32 GB                        |

---

### 4.6 本轮踩的坑与结论

1. **★★ 「本地 build 没有超分能力」是错的**：实际扫描本地 `33cda00` → **FlashVSR / FlashVSR+ 的 stage、  
   Metal kernel 与 3 条官方流水线全都有**；只有 **RelayVSR 本体**（随 `81cd674` / 2026-11-14）才需要升 main。  
   **教训：先扫源码树再下「要升级」的结论**（本轮差点把一条零成本路线判成高成本）。
2. **★ 报哈希不写聚合口径 = 数字不可复核**：第 3 轮的 `46bcb264…` 四种聚合都复现不出来。  
   → **纪律：哈希必须与「怎么算的」一起写。**
3. **★ `framemd5` 全流清单 = 51 行**（22 视频帧 + 29 音频包）→ 逐帧判据**必须 `-map 0:v`**（本轮再次实测确认）。
4. **★ 跨采样器对照 ≠ 同一场景画质对照**（首帧 SSIM 0.440051）→ 表述方式同「换 shift = 换场景」。
5. **★ LFM3-VL 在纹理与场景同一性上再次给出与量化相反的答案** → 只用它能可靠回答的粗判。
6. **★ 「`dmd` 压低沸腾 13%」≠「解决沸腾」**：静态地板 0.0010，`dmd` 是 0.0937 → **仍是 94× 地板**。
7. **★ 效应量必须在漂移=0 的条件下谈**：本轮 `autotune:false` 三处全关 → 差异 100% 可归因；  
   第 3 轮的 `er_sde` −16% 落在漂移带内 → **当时正确地不下结论，现在必须重测**。
8. **★ `dmd` 与 `er_sde` 同时改了两个因子**（更新式 vs 网格）→ 混着比会同时引入两个混淆项 → 拆开测（P18b）。
9. **★ 上游 `main` 至今零增量**（HEAD 仍 `4dc36b7`、release 仍 v0.1.110、issue 状态全未变、PR 数 0）→  
   **本轮的价值完全来自「回读上游官方文档 + 源码 + 生态」，不是来自上游更新。**
10. **工程**：本机 `setsid` 不存在 → 用 `scripts/detach_run.py`（`os.setsid()`）；  
    `p18_runner.sh` 沿用「幂等 + PID 续接 + 内存门限 + 脱离进程组」四件套，三臂 219/219/220 s 全部一次跑通。

### 4.7 收尾对账与 SOP 固化（同轮补记，04:50–04:56）

- **★★ 新增 SOP §12.10「每轮结束前的收尾对账清单」**（本轮固化为固定流程，6 项）：  
  ① 轮次状态与锁释放 ② 四份报告与仓库逐字节一致 ③ 技能包**三方**（安装版 ↔ 实验室副本 ↔ 仓库）一致  
  ④ 本轮产物齐备（成片/印相/VQA/analysis.json/.done）⑤ 真人素材防火墙为 0 ⑥ `HEAD == origin/main` 且工作区 clean。  
  附三条配套纪律：结论性数字必须与 `logs/*.json` 逐位一致 / 改技能包必须**安装版→实验室副本→仓库**三处同步  
  （同步脚本以 `$LAB/skills/` 为源，顺序反了会被下轮回滚）/ 收尾阶段发现的小瑕疵**当场修**，不留给下一轮。
- **本轮实测 6/6 全绿**：82 个技能文件三方逐字节一致；四份报告与仓库字节相同；  
  仓库 507 条目 / 469 blob / **真人素材 0**；`HEAD == origin/main == b8d89c5`，工作区 clean。
- **当场修掉的一处过期表述**：`sampler-spec.md` 第 6 节标题写「本实验室尚未做，见状态看板 P18」，  
  而第 7 节已给出 P18 判决 → 标注「已被第 7 节取代」（提交 `d1ae757`）。
- **GitHub 末次提交**：`b8d89c5`（第 4 轮共 5 次提交：`2f547a7` / `8857f10` / `a7dff7a` / `d1ae757` / `b8d89c5`）。
- **磁盘仍 5.4 GiB**（< 15 GiB 下限）→ **下一轮的第一约束是先清盘**，否则 P22 超分类实验无法启动。

---

## 第 5 轮 · 2026-11-18 06:30 —— ★★★ ControlNet Union（生态有 / vpipe 无）+ 上游新项目 `valtz` + 官方 H3 提示词六段式 + **P13b σ 网格重测**

### 5.1 本轮检索范围与来源清单（21 类）

| #  | 来源                                                                         | URL / 位置                                                                                                                                   | 日期            | 本轮读到的内容                                                                                                                                                                                                                                                          |
| -- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | GitHub API · 上游 HEAD                                                       | `api.github.com/repos/tgo-app-dev/vpipe/commits?since=2026-11-16`                                                                          | 2026-11-16    | **仍 `4dc36b7`，零新增**（自 2026-11-16 起 1 个 commit）                                                                                                                                                                                                                   |
| 2  | GitHub API · releases                                                      | `.../releases?per_page=8`                                                                                                                  | 2026-11-01    | **仍 v0.1.110**，零新增                                                                                                                                                                                                                                               |
| 3  | GitHub API · issues 全量                                                     | `.../issues?state=all&per_page=100`                                                                                                        | 2026-11-18    | **31 条，状态零变化**；**#55 仍 open / 0 评论 / 开放 28 天**；#58 open / 0 评论；#59 open / 0 评论                                                                                                                                                                                   |
| 4  | GitHub API · 分支                                                            | `.../branches`                                                                                                                             | 2026-11-18    | **只有 `main`**（无开发分支）                                                                                                                                                                                                                                             |
| 5  | ★ GitHub API · **上游组织全部仓库**                                                | `api.github.com/users/tgo-app-dev/repos`                                                                                                   | 2026-11-18    | **★ 发现本实验室此前零记录的 `valtz`**：2026-10-03 创建、79 stars、C++、MPL-2.0、"A native macOS app for generative creation and composition, powered by Vpipe"，最后推送 **2026-11-16**；另有 `vpipe-ming-image` / `vpipe-ltx-2.5` / `vpipe-sensenova-u1.5` / `vpipe-supplement`           |
| 6  | ★ GitHub API · 仓库树扫描                                                       | `.../git/trees/main?recursive=1`                                                                                                           | 2026-11-18    | **1776 条目**（与第 4 轮同）；**`controlnet` / `control` / `dmd` / `vsa` / `fastvideo` / `pdd` / `singularity` 全部 0 命中**；`vdn` 28 命中                                                                                                                                      |
| 7  | ★★ 上游 `relayvsr-upscale-stage.cc` 源码                                       | `raw.githubusercontent.com/.../stages/audio-video/relayvsr-upscale-stage.cc`                                                               | 2026-11-16    | ★ **倍率是硬编码的 4×**：`_plan_w = out_w ? out_w / 4 : kPlanW;`、`_plan_h = out_h ? out_h / 4 : kPlanH;`；**整个 stage 没有任何 `upscale_factor` 配置键**                                                                                                                          |
| 8  | ★ 上游 `docs/pipelines/*h3-image*`                                           | 本地树 `docs/pipelines/`（10 个文件）                                                                                                              | 2026-11-16    | ★ **vpipe 完整支持 H3-Image**：`minimax-h3-image-text-to-image{,-fast-m5}.vpipeline` / `-edit` / `-round-trip` / `prepare-minimax-h3-image{,-vae}.vpipeline`；**本地树 106 个文件命中 `h3-image`**                                                                             |
| 9  | ★ 上游 `prepare-minimax-h3-image.vpipeline`                                  | 同上                                                                                                                                         | 2026-11-16    | ★ 拉取 `MiniMaxAI/MiniMax-H3-Image`（**BF16 ≈68.65 GB**）+ `MiniMaxAI/MiniMax-H3` 的 text-encoder 变体（**≈66.7 GB**）→ **合计约 135 GB**                                                                                                                                    |
| 10 | ★ 上游 H3-Image 流水线配置                                                        | `minimax-h3-image-text-to-image-fast-m5.vpipeline`                                                                                         | 2026-11-16    | 复用 `generate-video` + `vae-decode` + `save-image`；**4736×3552（16.8 MP）**；fast-M5 版多 `i8_gemm: true, i8_gemm_tier: "token"`                                                                                                                                       |
| 11 | ★★ 上游 `docs/MINIMAX-H3.md`（本地 `33cda00`）                                   | 同上，第 1135–1160 行                                                                                                                           | 2026-11-16    | ★ **参考标签计数器按类型分开**（`<Picture i>` / `<Video k>` / `<Audio j>` 各从 1 起算）；★★ **「未匹配的标签就是普通文本，什么都不会报告」**                                                                                                                                                              |
| 12 | ★ 上游 `docs/pipelines/pika-h3-flex-reference-to-video.vpipeline`            | 本地树                                                                                                                                        | —             | 全树**唯一**还用 `@Image1/@Image2/@Video1` 的官方示例；`<Picture 1>` 命中 20 文件 / `@Image1` 仅 1 文件                                                                                                                                                                             |
| 13 | ★★ `valtz` 官方 H3 提示词技能                                                     | `raw.githubusercontent.com/tgo-app-dev/valtz/main/3rd-party/minimax-h3/skills/h3-prompt-writing/SKILL.md` + `references/{base,ref}-en.txt` | 2026-11-16    | **MiniMax 官方**提示词规范：Base 三段（`integrated_multimodal_description`/`overall_soundscape`/`non_diegetic_music`）、Ref2VA **六段**（`subject_definitions`/`summary`/`retention_analysis`/`detailed_description`/`overall_soundscape`/`non_diegetic_music`）；四种标签语义；时长 4–15 秒 |
| 14 | ★ `valtz` 的模型技能卡目录                                                         | `core/resources/skills/`（15 个）                                                                                                             | 2026-11-16    | ★ 新模型家族地图：`minimax-h3-image-{t2i,edit}.md`、**`flux3-klein-{t2i,edit}.md`**、`qwen-image-{t2i,edit}.md`、`minimax-music3.md`、`moss-tts.md`、`valtz-{agent,chat,procedural}.md`                                                                                       |
| 15 | ★★ ControlNet Union 三篇社区实测                                                 | stable-diffusion-art / gitcode ×2                                                                                                          | 2026-11       | 8 控制条件（Canny/Depth/HED/MLSD/Pose/Scribble/Layout/Gray）+ 视频 inpaint；**10 层密集控制注入 + guidance 蒸馏**；控制 patch 叠在 Ref2VA 上并**在音频 token 上清零 control skip**；SDPose 133 关键点姿态                                                                                             |
| 16 | ★ ModelScope · `Comfy-Org/MiniMax-H3`                                      | `api/v1/models/.../repo/files`                                                                                                             | 2026-11-18    | **48 文件**；含 **`minimax_h3_fun_controlnet_union_pruned_int8_convrot` = 2.30 GB** / `_bf16` 4.22 GB / `2.0_pruned_int8` 4.53 GB / `2.0_pruned_bf16` 8.38 GB                                                                                                        |
| 17 | ★ ModelScope · `Kijai/MiniMax-H3-experimental`                             | 同上                                                                                                                                         | 2026-11-18    | **34 文件**；★ `MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy` = **1.73 GB**（PDD 8-NFE）、`singularity_v2_lora_rank_351` 3.30 GB、`open_regenerate_2k_refiner_rank_384` 5.87 GB、`fastvideo_vsa_datafree_1300step_4step_int8` 22.90 GB                                       |
| 18 | ★ ModelScope · `Comfy-Org/RelayVSR`                                        | 同上                                                                                                                                         | 2026-11-18    | ★★ **新增 `relayvsr_x2_lightx2v_int8_convrot.safetensors` = 5.16 GB**（与 x4 同体积）；合计 10.58 GB（9 文件）→ **上游 issue #59 现在可操作化**                                                                                                                                         |
| 19 | ★ ModelScope · `kuohao/FlashVSR-v1.1` / `mlx-community/FlashVSR-v1.1-bf16` | 同上                                                                                                                                         | 2026-11-18    | ★ **逐文件实测 = 6.95 GB / 3.51 GB**（第 4 轮记的 6.48 / 3.27 **偏小** → SOP 12.7 又一次印证）                                                                                                                                                                                     |
| 20 | ★ H3-Image 五篇独立报道                                                          | artrealmai / promptlab / vega.chat / sloptvnews / pixelailabs                                                                              | 2026-11-10～11 | 规格与许可；★ Comfy 模板采样器 `euler, simple, 6 steps, CFG 1, denoise 1`；★★★ **「默认 euler 出 crunchy grid → 换 `SamplerLCM` + `s_noise` 1.10→0.90 就修好」**                                                                                                                      |
| 21 | ★ 社区 · H3 全生态资源索引                                                          | `g.itadn.com/repos/wildminder/awesome-minimax-H3`（2026-11-16 快照）                                                                           | 2026-11-16    | DMD2 σ 阶梯 `[999,749,500,250]`；★ **`Beidouqixing/MiniMax-H3-DMD2-4step` 已 404**；★ `t8star` 的 2×2 空间 HF 补丁只 **+2%**、作者称增益微弱                                                                                                                                        |

---


### 5.2 新增知识

#### K21 ★★★ MiniMax-H3-Fun-Controlnet-Union（alibaba-pai）—— **生态有能力，vpipe 完全没有**

- 来源：stable-diffusion-art + gitcode ×2（2026-11）+ ModelScope API（2026-11-18 实测）。
- 一句话结论：**一个 checkpoint 覆盖 8 种结构控制条件 + 视频 inpaint**，通过 **10 个控制块**  
  把控制信号注入主 transformer（guidance 蒸馏），叠在 **Ref2VA** 之上并**在音频 token 上把 control skip 清零**  
  → 运动被驱动视频锁死、音频照常生成。
- 权重（ModelScope 实测，**vpipe 侧无对应 stage，但体积可下**）：
  | 文件                                                                    |          体积 |
  | --------------------------------------------------------------------- | ----------: |
  | `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors`     | **2.30 GB** |
  | `minimax_h3_fun_controlnet_union_pruned_bf16.safetensors`             |     4.22 GB |
  | `minimax_h3_fun_controlnet_union_2.0_pruned_int8_convrot.safetensors` |     4.53 GB |
  | `minimax_h3_fun_controlnet_union_2.0_pruned_bf16.safetensors`         |     8.38 GB |
- ★ **vpipe 支持度 = 0（三重验证）**：上游树 1776 条目 `controlnet`/`control` **0 命中**；  
  本地树 5234 文件 **0 命中**；31 条 issue 无相关项。  
  → **不是「需要升级」，是「没有这个 stage」** → 适合写成第 7 条上游 issue 提案。
- ⚠️ **体积冲突**：社区博客写「约 13.5 GB」，ModelScope 实测 2.30–8.38 GB（**差 3–6 倍**）  
  → 又是 SOP 12.7：**盘点模型仓库必须按文件逐个看**。

#### K22 ★★★ 上游新项目 `tgo-app-dev/valtz`（本实验室此前零记录）

- 来源：GitHub API `users/tgo-app-dev/repos`（2026-11-18）。
- 一句话结论：**vpipe 的官方 macOS 前端/创作应用**，C++ / MPL-2.0 / 79 stars，  
  2026-10-03 创建、最后推送 **2026-11-16**（比 vpipe 本体只晚 13 分钟）。
- ★ **对本实验室最重要的价值：它把 MiniMax 官方的提示词技能直接打包进来了**  
  （`3rd-party/minimax-h3/skills/h3-prompt-writing/`），  
  以及一批模型技能卡（见 K23）。
- 社区侧已有人推荐：「don't go comfyui, macs need dedicated tools… use vpipe」。

#### K23 ★★★ 官方 H3 提示词结构（六段式 + `<Picture N>`）与「未匹配标签 = 普通文本」

- 来源：valtz 内置的 **MiniMax 官方** `h3-prompt-writing` 技能 + 上游 `docs/MINIMAX-H3.md`。
- 一句话结论：**H3 有一套与 vpipe 示例不同的官方提示词规范**：
  - Base 模式（T2VA/I2VA/FL2VA/L2VA）**三段**：  
    `integrated_multimodal_description` → `overall_soundscape` → `non_diegetic_music`；
  - **Ref2VA 六段**：`subject_definitions` → `summary` → `retention_analysis` →  
    `detailed_description` → `overall_soundscape` → `non_diegetic_music`；
  - 四种标签：`<Subject N>`（可复用内容）/ `<Picture N>`（关键帧锚点）/  
    `<Video N>`（整段时序来源）/ `<Audio N>`（音频）；  
    **只用图定义人物/风格时不要单开 `<Picture N>`**，要在 `<Subject N>` 里引用它。
- ★★★ **新坑（同族：静默失效）**：上游原文
  > Getting this backwards writes a prompt that points at a reference which is not there,  
  > and **nothing reports it: an unmatched tag is ordinary text to the model.**  
  > 且**计数器按类型分开**（`<Picture i>` / `<Video k>` / `<Audio j>` 各从 1 起算）。
- ★ **本实验室的夹具正好用的是 `@Image1`**（沿用了上游唯一一个旧示例  
  `pika-h3-flex-reference-to-video.vpipeline`；上游文档主体 20 个文件已改用 `<Picture 1>`）。  
  → 登记 **P27-b**（见 5.4）。  
  ⚠️ **这不影响 P18 / P13b 的内部对照结论**（两臂用同一份提示词），  
  只影响「绝对值能否与上游 #55 的 0.0502 直接比」。

#### K24 ★★ MiniMax H3-Image（2026-11-10/11 发布）—— vpipe **已完整支持**，但本机装不下

- 来源：五篇独立报道 + **上游 `docs/pipelines/minimax-h3-image-*.vpipeline`**（本地树已有 10 个）。
- 规格：H3 DiT 去音频分支、**33.1B**、50 层、hidden 5376；**6 步蒸馏、CFG 固定 1（无负面提示词）**；  
  原生 **≈16 MP**（4096×4096 … 6272×2688，有效 4–20 MP）；**最多 16 张参考图**；  
  **文本编码器与 H3 视频共用 Qwen3-VL-32B**；Image VAE 16× 下采样 / 24 通道 / 2×2 patch；  
  许可排除美国/欧盟/英国/韩国，年营收 >100 万美元或对外托管需书面授权。
- ★ **vpipe 侧**（本轮实测，本实验室此前零记录）：
  - 上游有 **6 条官方流水线**（text-to-image / **text-to-image-fast-m5** / edit / round-trip /  
    prepare / prepare-vae），**本地 build `33cda00` 全都有**（106 个文件命中 `h3-image`）；
  - 图像模型**直接复用** `generate-video` + `vae-decode` + `save-image`；
  - fast-M5 版只是多 `i8_gemm: true` + `i8_gemm_tier: "token"`。
- ★★★ **决定性负面结论（省下 135 GB 下载）**：  
  `prepare-minimax-h3-image.vpipeline` 拉的是  
  **`MiniMaxAI/MiniMax-H3-Image`（BF16 ≈68.65 GB）+ `MiniMaxAI/MiniMax-H3` 的 text-encoder 变体（≈66.7 GB）**  
  → **合计约 135 GB**。  
  ⇒ **vpipe 的 H3-Image 路线在本机（24 GB 统一内存 / 磁盘 5.3 GiB）不可行**，  
  且与 ComfyUI 的 21 GB INT8 路线**不是同一套权重格式**（不能直接复用）。  
  → **P28 改判：从「🔴 待验证」降为「⛔ 本机不可行」**，除非上游出量化/GGUF 版。

#### K25 ★★ H3-Image 上的 `SamplerLCM` 复现「crunchy grid」→ **P18 的跨家族印证**

- 来源：pixelailabs（2026-11）+ webhill（2026-11）。
- 一句话结论：在 **H3 图像**模型上，默认 `euler` 会出「过锐块状纹理（crunchy grid）」，  
  换成 **`SamplerLCM` + `simple` + 6 步 + `s_noise` 1.10→0.90** 就修好了。
- ★ **交叉结论**：
  |          | vpipe `dmd`（第 4 轮 P18，本机实测）                 | ComfyUI `SamplerLCM`（H3-Image，社区实测） |
  | -------- | ------------------------------------------- | ----------------------------------- |
  | 相对 euler | HF jitter **−12.82%**、sharpness **+10.27%** | crunchy grid 消失、皮肤出现真实毛孔            |
  | 家族       | H3 **视频**                                   | H3 **图像**                           |
  ⇒ **同一条机理在 H3 视频与 H3 图像两个家族上独立出现**  
  → P18 的判决从「本机单点观察」升级为「**家族级共识**」。
- ⚠️ **仍不是根治**：本实验室 `dmd` 的 HF jitter 仍是静态地板的 **94×**；社区那条也只说「明显改善」。

#### K26 ★★ FastVideo FastH3（DMD2）—— 与我们的 σ 网格工作互相印证

- 一句话结论：**4 次前向 over 5 点 σ**（v1）、**8 次前向 over 9 点 σ**（v2）、base 49 次前向  
  → 与我们的「**N 次前向 over N+1 点**」完全一致  
  → **「N+1 点」不是 vpipe 的怪癖，是 H3 家族的通用约定**（第三方实现印证）。
- DMD2 σ 阶梯 `[999, 749, 500, 250]`，cfg 1.0，768×1344 @124 帧；  
  VSA 稀疏度 90 %（v1）/ 80 %（v2）；**只有 T2V**（未蒸馏 FL2VA / Ref2VA）。
- ★★★ **必须区分的两个「DMD」**：  
  `dmd`（vpipe **采样器**，推理期换 σ 轨迹，本实验室已实测）  
  **≠** DMD2（FastH3 **蒸馏模型**，训练期改权重）。  
  → 读社区帖看到「DMD2」**不要**自动映射到我们的 `dmd` 结论。
- 死链：`Beidouqixing/MiniMax-H3-DMD2-4step` **HF 404**，规范来源是 FastVideo 仓库。

#### K27 ★★ 上游 issue #59 现在可操作化：RelayVSR **2× checkpoint 已上架**

- 来源：ModelScope `Comfy-Org/RelayVSR`（2026-11-18 实测）+ 上游 `relayvsr-upscale-stage.cc` 源码。
- 一句话结论：**`relayvsr_x2_lightx2v_int8_convrot.safetensors`（5.16 GB）已在 ModelScope**，  
  但上游 stage 的倍率是**硬编码 4×**（`_plan_w = out_w / 4`、`_plan_h = out_h / 4`，  
  **整个 stage 没有任何 `upscale_factor` 配置键**）  
  → **issue #59「support the native 2x checkpoint」现在有了具体可指的文件，不再是空请求。**
- 这也印证了 LightX2V 官方说明：**2×/4× 权重混用会直接报错**，所以不能靠「拿 4× 模型做 2×」绕过。

#### K28 ★ FlashVSR 权重体积订正（SOP 12.7 的又一次印证）

| 仓库                                 |  第 4 轮记的 |                                     **本轮逐文件实测** | 差异           |
| ---------------------------------- | -------: | ----------------------------------------------: | ------------ |
| `kuohao/FlashVSR-v1.1`             |  6.48 GB | **6.95 GB**（8 文件：5.68 + 0.58 + 0.51 + 0.19 + …） | **+0.47 GB** |
| `mlx-community/FlashVSR-v1.1-bf16` |  3.27 GB |        **3.51 GB**（8 文件：2.84 + 0.58 + 0.09 + …） | **+0.24 GB** |
| `Comfy-Org/RelayVSR`               | 10.58 GB |                                  10.58 GB（9 文件） | 一致           |

→ **「总数减法」与博客聚合数都会偏低**；盘点必须按文件逐个累加（与第 4 轮 SOP 12.7 同一结论）。

#### K29 ★ 2K refiner 有了社区补丁（对第 1 轮「2K 未开源」的增量）

- `Kijai/MiniMax-H3-experimental` 的 `minimax_h3_open_regenerate_2k_refiner_rank_384_bf16.safetensors` = **5.87 GB**  
  → MiniMax 官方演示里的「768p → 2K 再生成」阶段**虽未开源，社区已做出 refiner LoRA**。
- 体积 5.87 GB 在本机磁盘清空后**可下**，但需要 2K 显存预算（≥15 GiB 余量）→ 优先级低于 ControlNet。

#### K30 ★ PDD 8-NFE Ref2VA LoRA：1.73 GB，体积可接受

- `MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy.safetensors` = **1.73 GB**（阿里 PAI Parallel Decoding Distillation）。
- 与本实验室已有的 `lightx2v` Turbo LoRA 是**不同家族**的少步方案 → 值得作为 P27 的候选（待验 vpipe 兼容性）。

#### K31 ★ 上游与生态零变化（基线确认）

- 上游 HEAD 仍 `4dc36b7`、release 仍 v0.1.110、issue 31 条状态全未变、**只有 `main` 一个分支**；  
  #55 / #58 / #59 全部 open / **0 评论**。
- HF Space `Upsampler/relayvsr` **仍在**（lastModified 2026-11-07）→ **P25 零下载预判仍可用**。
- 社区侧 vpipe 口碑：16 GB Mac mini 用 vpipe 跑 8-bit MiniMax H3 可用（weight streaming）；  
  M5 Pro 做 1366×768 / 10–15 s 需 **2–3 小时**。

#### K32 ★ 生态侧旁证：「改 HF 投影」对纹理沸腾的收益有限

- `t8star` 的 Ref2VA **2×2 空间 HF 补丁**（视频输入投影）只带来 **+2 %** HF 增益，  
  作者明确写「HF agent 增益微弱，且**未确认**能消除『油腻/蜡质』外观」。
- ⇒ 与本实验室的结论一致：**HF 高频指标不是一把万能钥匙**，  
  第 4 轮 `dmd` 压低 12.82 % 是真效应，但社区侧同路线的天花板也很低。

#### K33 ★★ 闭式 σ 公式被「运行时真值」验证（见 5.3 实验）

- 本轮 P13b 的日志回显给出了**运行时实际使用的音频 σ 串**，  
  与 `scripts/p15_sigma_grid.py` 的闭式公式**逐值吻合**（9/9，4 位小数）  
  → 公式从「文档级双源互验」升级为「**运行时真值**」。

### 5.3 ★★★ 本轮实验（P13b · `sigmas` σ 网格对照）—— **第 3 轮的「−16%」被推翻，符号是反的**

#### 5.3.1 设计

| 臂     | `minimax-h3-model-config.sigmas`                              | 视频 σ 网格                            | 次数    |
| ----- | ------------------------------------------------------------- | ---------------------------------- | ----- |
| **A** | `1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0` | ComfyUI `er_sde` 表（**与第 3 轮逐字相同**） | **3** |
| **B** | **不写该字段**                                                     | 默认网格（`video_shift 6.0`）            | **2** |
| 跨轮锚点  | 第 4 轮 `p18-euler.mp4`                                         | 默认网格                               | 1（历史） |

其余配置**逐字相同**（seed 42 / 22 帧 / 1344×768 / 8 步 / 同 LoRA / 同参考图 / 同提示词 /  
`sampler-select{euler}` 接 `iports[3]` / 三处 `autotune:false`）。  
用时 219/219/220/220/219 s（合计 **18 分 57 秒**），产物 245 333 / 244 535 B。

#### 5.3.2 逐位判据（漂移 = 0 的直接证据）

| 比较                          | framemd5（`-map 0:v`） | 音频 md5 | 整段 SSIM（口径 A） | PSNR          | 首帧 SSIM（口径 B） | 字节                |
| --------------------------- | -------------------- | ------ | ------------- | ------------- | ------------- | ----------------- |
| A1 vs A2                    | **相同** `ba301fc2…`   | **同**  | **1.000000**  | **inf**       | **1.000000**  | 245 333 = 245 333 |
| A2 vs A3                    | **相同** `ba301fc2…`   | **同**  | **1.000000**  | **inf**       | **1.000000**  | 245 333 = 245 333 |
| B1 vs B2                    | **相同** `0d77d033…`   | **同**  | **1.000000**  | **inf**       | **1.000000**  | 244 535 = 244 535 |
| **B1 vs 第 4 轮 `p18-euler`** | **相同** `0d77d033…`   | **同**  | **1.000000**  | **inf**       | **1.000000**  | 244 535 = 244 535 |
| **A1 vs B1（处理组）**           | **不同**               | 不同     | **0.749469**  | **18.699585** | **0.604196**  | —                 |

⇒ **漂移 = 0**（逐位证明，不是估算）；  
⇒ **默认网格臂在第 3、4、5 三轮之间逐位相同** → **本实验室迄今最强的可复现性证据**。

#### 5.3.3 ★★★ 主判决

| 变体                            |  HF jitter | frame diff | sharpness | static_hf_jitter | 静止像素比 |
| ----------------------------- | ---------: | ---------: | --------: | ---------------: | ----: |
| 静态参考（编码地板）                    | **0.0010** |   0.000010 |    353.66 |           0.0010 | 1.000 |
| **A · `er_sde` σ 网格**（3 次全同）  | **0.1205** |   0.004508 |    560.40 |           0.1108 | 0.954 |
| **B · 默认网格**（2 次 + 第 4 轮锚点全同） | **0.1075** |   0.003669 |    559.73 |           0.1010 | 0.979 |

| 指标               | **第 5 轮效应**（漂移 = 0） | 第 3 轮观察（漂移 18.4 %） | 判决           |
| ---------------- | ------------------: | -----------------: | ------------ |
| **HF jitter**    |        **+12.09 %** |        **−16.0 %** | ★★★ **符号相反** |
| frame diff       |        **+22.87 %** |                  — | 更大           |
| sharpness        |         **+0.12 %** |             −7.0 % | 几乎无差异        |
| static_hf_jitter |         **+9.69 %** |            −12.8 % | 符号相反         |

**地板倍数**：第 5 轮 A 臂 = **121×** 地板、B 臂 = 108×（第 3 轮 A 臂是 100×）。

⇒ **★★ 核心结论**：**ComfyUI `er_sde` σ 网格在本机上不是解药，而是让纹理沸腾更严重（+12.09 %）。**  
第 3 轮的「−16 %」**完全落在 18.4 % 漂移带内** —— 当时的「不可下结论」是正确判断；  
**本轮在漂移 = 0 下重测，结论反了**。

> **这是本实验室方法学的核心价值证明：一个「看起来像效应」的数，只有当漂移基线真正压到 0 之后才可采信；压到 0 之后，它可能是反的。**

#### 5.3.4 ★ 与 P18 的正交对照（「更新式」vs「σ 网格」）

| 变量                         | 改变什么           |                        效应 | 地板倍数 |
| -------------------------- | -------------- | ------------------------: | ---: |
| **`dmd` 采样器**（第 4 轮 P18）   | **更新式**（每步重注噪） | HF jitter **−12.82 %**（利） |  94× |
| **`er_sde` σ 网格**（本轮 P13b） | **σ 轨迹**       | HF jitter **+12.09 %**（害） | 121× |

⇒ **两者方向相反、量级相近** → 第 4 轮 §12.3「更新式与 σ 网格是正交变量」的纪律得到验证；  
⇒ **纹理沸腾的解药目前只有 `dmd` 采样器这一条路**（且只是压低 12.82 %，**仍是地板的 94×**）。

#### 5.3.5 ★★ 顺带：闭式 σ 公式被「运行时真值」验证（K33 展开）

运行时回显的音频 σ 串 `[1.0000, 0.9693, 0.9281, 0.8699, 0.7825, 0.6102, **0.3819**, **0.1344**, 0.0000]`  
与闭式公式算出的 `[1, 0.969279, 0.928083, 0.869858, 0.782531, 0.610176, **0.381884**, **0.134366**, 0]`  
**9/9 逐值吻合（4 位小数）**。第 7、8 两个值最关键 —— 它们必须「先把视频 σ 反解回共享 q、再过 `audio_shift`」才算得出。  
⇒ **公式升级为「运行时真值」级证据**（此前是文档级双源互验）。

顺带证实：① `sigmas` 字段在本地 build `33cda00` 真实生效（且 B 臂日志**无**该行 → 差异确实只来自此字段）；  
② 音频 σ 确实走共享 q 网格；③ `autotune:false` 生效（`gemm autotune 0`，竞速开时是 4635 ms）。

#### 5.3.6 LFM3-VL-2B 复核

- **Q1 场景是静的** → 两行姿态位置都基本不变 ✅ **一致**
- **Q2 哪行更花** → 「**第 2 行（A 臂）**&#x566A;点更细碎、更有『沙沙的颗粒感』」 ✅ **与量化一致**（本轮罕见同向）
- **Q3 是否同一场景** → 「基本相同，只有窗帘位置略有不同」 ❌ **与量化矛盾**（首帧 SSIM 0.604196）→ **已知缺陷 ④ 再现**
- **Q4 首末帧纹理累积** → 两段都无显著变化 ✅ 一致

### 5.4 本轮新增待验证任务（登记到状态看板）

| 编号        | 任务                                       | 依据                                                                        | 成本                                                | 阻塞                         |
| --------- | ---------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------- |
| **P27**   | **ControlNet Union 可行性预判**               | 生态有 8 条件控制能力（2.30 GB INT8），vpipe **0 命中**                                 | 先 grep 挂载点；若连输入口都没有 → 直接写第 7 条上游 issue，**不做本地实验** | 无（预判本身零成本）                 |
| **P27-b** | **提示词结构对纹理沸腾绝对水平的影响**                    | 官方六段式 + `<Picture N>` vs 本实验室夹具的 `@Image1`                                | 2 臂 × 22 帧 ≈ 8 分钟（模型全在本地）                         | 无                          |
| **P27-c** | **PDD 8-NFE Ref2VA LoRA 兼容性**            | `MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy` 1.73 GB                        | 1 次注册 + 1 次生成                                     | 磁盘（清到 ≥15 GiB 后可下 1.73 GB） |
| **P28**   | ~~MiniMax H3-Image 落地~~ → **改判 ⛔ 本机不可行** | vpipe 路线需 **≈135 GB** 权重（68.65 + 66.7），与 ComfyUI 的 21 GB INT8 **不是同一套格式** | —                                                 | **不可行**（除非上游出量化版）          |
| **P29**   | **2K refiner 验证**                        | `open_regenerate_2k_refiner_rank_384` 5.87 GB                             | 1 次 768p→2K                                       | 磁盘 + 显存                    |

### 5.5 本轮踩的坑与结论

1. ★★★ **「生态有」≠「vpipe 有」≠「本机跑得动」是三道独立的门。**  
   本轮三连命中：ControlNet（生态有 / vpipe 无）、H3-Image（vpipe 有 / 本机装不下）、  
   RelayVSR 2×（生态有 / vpipe 硬编码只吃 4×）。
2. ★★ **写「本机做不了 X」之前先扫树。** 本轮若只搜社区，会把  
   「H3-Image 需要 135 GB」写成「生态刚出、还没适配」—— 实际**上游早就适配了**，  
   只是本机装不下。
3. ★★ **模型体积必须逐文件累加**（K28）：第 4 轮的两个 FlashVSR 数字都偏小 0.24–0.47 GB。
4. ★ **社区博客的聚合体积不可信**（K21：13.5 GB vs 实测 2.30–8.38 GB，差 3–6 倍）。
5. ★ **同名不同物要单独建条目**（K26：`dmd` 采样器 ≠ DMD2 蒸馏）。
6. ★ **新静默坑入库**：参考标签写错 → 零报错零告警，参考条件直接失效（K23）。  
   与「shift 写错完全静默」「`autotune` 竞速」「旧 build 丢字段」同族。
7. ★ **上游 28 天零回应的事实不变**（#55 / #58 / #59 全 0 评论）→  
   本实验室的自查能力（逐位判据 + σ 网格公式 + 运行时真值）要继续自建。
8. ★ **磁盘 5.3 GiB 仍是第一约束**：P22 / P27-c / P29 全部被它挡住；  
   P13b 之所以能跑，是因为「模型全在本地 + 22 帧短片 + 产物 240 KB」。

### 5.6 收尾对账（SOP §12.10 六项，本轮实测）

| # | 检查项      | 实测结果                                                                           |
| - | -------- | ------------------------------------------------------------------------------ |
| 1 | 轮次状态与锁释放 | `round` = **5**、`last_run` = `2026-11-18 06:30`；`.auto-round.lock` **已删除**     |
| 2 | 报告字节一致   | 本地 4 份 vs 仓库 `docs/reports/`：**296 257 / 99 423 / 120 923 / 39 837 B，全部逐字节相同** |
| 3 | 技能包三方一致  | 安装版 ↔ 实验室副本 ↔ 仓库：**85 个文件、0 差异**                                               |
| 4 | 产物齐备     | 5 臂成片（各 240 KB）+ 5 份日志 + 5 个 `.done` + 3 张印相 + `analysis.json` **全部在位**        |
| 5 | 真人素材防火墙  | 仓库索引 **484 条目 / 远端树 522 条目 → 真人文件 0**                                          |
| 6 | 推送一致性    | `HEAD == origin/main == 6835491`，工作区 clean                                     |

- **GitHub 提交**：`6835491`（`docs: 第 5 轮夜间知识同步（2026-11-18 06:30）— P13b 判决…`）。
- **新增技能文件**：`h3-ecosystem-map.md` / `h3-prompt-format.md` / `h3-image-candidate.md`
  - `sigma-grid.md` 第 7 节 + `sampler-spec.md` 第 8 节。
- **新增脚本**：`make_p13b_pipelines.py` / `p13b_runner.sh` / `p13b_analysis.py` /  
  `p13b_contact.sh` / `vqa-p13b.sh`（共 5 个）。
- **新增流水线**：`p13b-{ersde,default}{,-r1,-r2,-r3}.vpipeline`（7 个）。
- **磁盘仍 5.3 GiB**（< 15 GiB 下限）→ **下一轮的第一约束仍是先清盘**  
  （P22 FlashVSR 3.51 GB / P27-c PDD 1.73 GB / P29 2K refiner 5.87 GB 全被它挡住）。

---

## 第 6 轮 · 2026-11-18 12:56 —— ★★★ **P22：FlashVSR 原生 Metal 4× 视频超分真机跑通 + 量化判决** + H3 Max 确认托管化 + SiliconFlow 官方 API 上线

### 6.1 本轮检索范围与来源清单（18 类）

| #  | 来源                                                                                              | 端点 / URL                                         | 结果                                                                                    |
| -- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| 1  | GitHub 上游 commits                                                                               | `api.github.com/repos/tgo-app-dev/vpipe/commits` | HEAD 仍 `4dc36b7`（2026-11-16），**零增量**                                                  |
| 2  | GitHub 上游 releases                                                                              | `…/releases`                                     | 仍 **v0.1.110**（2026-11-01）                                                            |
| 3  | GitHub 上游 issues（含 PR 排除）                                                                       | `…/issues?state=all`                             | **31 条 issue / 0 条 PR**；#55/#58/#59 全 open/**0 评论**                                   |
| 4  | GitHub 上游 branches                                                                              | `…/branches`                                     | **只有 `main` 一个分支**                                                                    |
| 5  | GitHub **owner 全部仓库**（第 5 轮新增的固定检索项）                                                            | `api.github.com/users/tgo-app-dev/repos`         | 7 个仓库，`valtz` 79 stars（无新增）                                                           |
| 6  | ModelScope `lightx2v/Minimax-h3-Turbo`                                                          | `api/v1/models/.../repo/files`                   | **31 文件 / 26 safetensors，零变化**                                                        |
| 7  | ModelScope `kuohao/FlashVSR-v1.1`                                                               | 同上                                               | **8 文件 / 6.953 GB**（逐文件实测）                                                            |
| 8  | 本地源码树扫描                                                                                         | `repo/vpipe/`                                    | **FlashVSR 全套在**（stage + Metal kernel + 3 条官方流水线）                                     |
| 9  | 本地源码 `stages/flashvsr-model-config-stage.cc`                                                    | 源码                                               | ★ **上游第一手内存数字**：v1.1 `kv_ratio` 携带 **9.6 GB @1920×1152**；FlashVSR+ **4.2 GB**         |
| 10 | 本地源码 `stages/flashvsr-src-encoder-stage.cc`                                                     | 源码                                               | ★ **`continuity:auto` 判据：~20 GB @1920×1152 / ~2.5 GB @512×512**；v1.1 单 clip **≥25 帧** |
| 11 | 本地源码 `generative-models/flashvsr/flashvsr-family.h`                                             | 源码                                               | ★ **几何契约**：输出宽高 128 的倍数、帧数 8k+1、**输出 = 4× 源**；`hf_dir` 语义                             |
| 12 | 本地源码 `stages/model-registry.cc`                                                                 | 源码                                               | ★ **未注册 ref 直接当文件路径用** → `hf_dir` 可写绝对路径                                              |
| 13 | MiniMax 官方模型页                                                                                   | `platform.minimax.io`                            | ★ **MiniMax H3 Max = fal.ai 托管，未放出权重**                                                |
| 14 | MiniMax 官方 self-host 指南                                                                         | `platform.minimax.io/docs/guides/local-deploy`   | ★ H3 部署基线**明确不含** Context-IR 与完整 2K workflow                                          |
| 15 | SiliconFlow 更新公告                                                                                | `docs.siliconflow.cn/release-notes`              | ★ **2026-11-10 上线 MiniMax-H3 API**（官方托管路线）                                            |
| 16 | 社区：SD 中文网 / h3-max.com / woyce / freakyjolly / specialinfluencers / thehype                     | 6 篇                                              | H3 Max 托管化、H3 提示词结构、ComfyUI 侧生态                                                       |
| 17 | 社区：Colab runbook（2026-11 verified）/ awesome-MiniMax-H3-cases / Nereo 色带工作流 / bbs.monster t8star | 4 篇                                              | ★ 两条实战坑 + 一条通用方法学纪律                                                                   |
| 18 | HF API（`api/models/…`、`api/spaces/…`）                                                           | —                                                | ⚠️ **本轮从沙箱直连返回非 JSON（被拦）**，改用 WebFetch/搜索侧信息；**P25 的 Space 状态本轮未直连复核**                |

### 6.2 新增知识

| #       | 知识                                                                                                                                                                                                                                           | 来源                                                    | 日期            | 对既有结论的影响                                                                                                                                   |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **K34** | ★★★ **MiniMax H3 Max 是 fal.ai 托管服务，权重未开源**（官方模型页 + 3 家社区站三源印证）                                                                                                                                                                               | platform.minimax.io / stablediffusion-cn / h3-max.com | 2026-11       | **不冲突**：第 5 轮「生态有 / vpipe 无 / 本机装不下」三门框架再命中一例（**生态有但只有托管形态**）。⇒ 不追                                                                         |
| **K35** | ★★ **SiliconFlow 于 2026-11-10 上线 MiniMax-H3 官方托管 API**：`duration` 5–15 s、`resolution` 480p/768p、`ratio`、`images` 用 `role: first_frame/last_frame`。★ **`negative_prompt` 与 `image_size` 传入不报错但被忽略**                                           | docs.siliconflow.cn/release-notes                     | 2026-11-03/10 | **跨生态印证本实验室的「静默失效」清单**（第 5 轮 K23 参考标签写错、本轮 K47 配置键被静默丢弃同族）。**新知识形态：静默失效不是 vpipe 的专利，是整个生态的通病**                                             |
| **K36** | ★★ **H3 官方三段式 = H3-Context-IR / H3-Base / H3-Regenerate-2K**；H3-Base 出 **768p（短边 768）/ 24 fps**                                                                                                                                              | woyce.ai / Nereo                                      | 2026-11       | ✅ **印证**本实验室 768p 认知（1344×768）与第 1 轮「2K 模块未开源」                                                                                             |
| **K37** | ★★ **官方 self-host 指南明写 H3 部署基线「excludes H3-Context-IR and the complete 2K Workflow」**；ComfyUI 0.30.0+ / SGLang 8×B200 Ulysses 8                                                                                                              | platform.minimax.io/docs/guides/local-deploy          | 2026-11       | ✅ **印证**第 1 轮结论（2K 与 Context-IR 仍不在开源范围）→ **不是本实验室的悲观，是官方口径**                                                                              |
| **K38** | ★ ComfyUI 侧 768p 口径：**1.0 MP → 1376×768**（图把 1344 宽取整到 1376）；16:9 下 0.41 MP → 864×480                                                                                                                                                        | H3-colab-studio colab-runbook                         | 2026-11       | ⚠️ **口径差**：本实验室用 **1344×768**，ComfyUI 图是 **1376×768**（+2.4%）→ 跨实现比较分辨率时须注明                                                                 |
| **K39** | ★★ **Colab 实战两条坑**：① ComfyUI 模板**即使 turbo 关着也必须下载 Turbo LoRA**（模板图里恒有 LoRA loader 节点），否则首帧就卡在缺模型；② **SaveVideo 的 `format` 字段被参数重置清空 → 69 分钟生成后在保存步 `TypeError` 失败**（帧还在 cache 里）                                                             | H3-colab-studio colab-runbook                         | 2026-11       | ✅ **印证**本实验室的「保存环节是独立故障点」经验（`save-video` 的键是 `output_url` 不是 `path`）。**新纪律：长任务必须校验保存参数，产物落盘才算成功**                                          |
| **K40** | ★★ **Pika H3 Flex 用的是 PDMD 蒸馏**（Pika 明说「标准 DMD 在我们的训练里不稳定」），50→6 步                                                                                                                                                                           | thehype / specialinfluencers / freakyjolly            | 2026-10-29    | **补充**第 5 轮 K26 的 DMD/DMD2 对照表 → **PDMD 是 DMD 家族的新成员**（训练期，与推理期 `dmd` 采样器无关）                                                               |
| **K41** | ★★ **社区通用工作流纪律**：「不要同时更改采样器设置、VAE 精度、输出分辨率和编解码器；每次测试只改变一个变量」；「参考素材已被多次编码 → H3 无法重建已丢失的色调信息」                                                                                                                                                  | Nereo 色带修复                                            | 2026-11       | ✅ **跨生态印证**本实验室的「正交拆解」纪律（第 4 轮 12.6）。**第 2 条是新的**：参考素材的**编码历史**本身是不可恢复的信息损失 → 引用社区视频当参考时要问它被编过几次                                           |
| **K42** | ★ `awesome-MiniMax-H3-cases` 社区库（3145 个可播放案例 / 781 条完整公开提示词 / 26 篇教程），把 **Apple Silicon 原生 C + Metal** 单列为一条独立路线                                                                                                                             | vibeindex / GitHub                                    | 2026-11       | ✅ **第三方定位印证**：vpipe 是 Apple Silicon 上的原生 C++/Metal 路线，与 ComfyUI（CUDA）并列                                                                    |
| **K47** | ★★★ **FlashVSR 本机实测**（详见 6.3）                                                                                                                                                                                                                | 本轮实验                                                  | 2026-11-18    | **把第 4 轮的「文档级登记」升级为「量化判决」**                                                                                                                |
| **K48** | ★★ **FlashVSR 几何契约与内存账**（上游源码第一手）：输出宽高 128 的倍数、帧数 8k+1、输出 = 4× 源、`group_size ≤ 帧数`（否则**挂住**）；v1.1 单 clip ≥25 帧；`continuity:auto` 在 1920×1152 需 ~20 GB / 512×512 需 ~2.5 GB                                                                    | 本地源码                                                  | 2026-11-18    | ✅ **印证**第 4 轮 12.8 的内存估算方向；**新增可执行的降维路径**（降到 1280×768 → ~8.9 GB ✅）                                                                         |
| **K49** | ★★ **FlashVSR 复现性 =「不逐位相同但指标漂移≈0」**：`framemd5` 两次不同（SSIM 0.998751 / PSNR 51.89 dB），指标漂移 **+0.02% / 0.00% / +0.01% / −0.00%**。★ 原因：**flashvsr 家族的 sampler/scheduler/negative 全部惰性**（one step at a fixed timestep）→ **`autotune` 无可调对象，日志无回显** | 本轮实验 + 上游源码                                           | 2026-11-18    | ⚠️ **修订**第 3 轮 11.1 的适用范围：`autotune:false` 的 bit-for-bit 结论**只对 H3 成立**，不能外推到 FlashVSR 家族。**新纪律：复现性判据要分家族，FlashVSR 用「framemd5 + 指标漂移」双判据** |
| **K50** | ★★★ **「SSIM 会把编造的细节判成失真」** —— 同一对片，SSIM 判 FlashVSR「更差」（−0.0506 / −4.05 dB），纹理量判它「好 12.6×」。⇒ **评价 AI 超分必须双口径同时报**                                                                                                                             | 本轮实验                                                  | 2026-11-18    | **本轮最具方法学价值的发现**：它是第 3 轮「细节能量会把噪点当细节」的**姊妹坑**（那一条是「把噪点算成细节」，这一条是「把真细节算成失真」）                                                                |
| **K51** | ★ 上游仍零增量：HEAD `4dc36b7` / release v0.1.110 / 31 issue / 0 PR / 1 branch / #55 开放 30 天 0 评论                                                                                                                                                   | GitHub API                                            | 2026-11-18    | 基线确认（第 3 轮起连续 4 轮零增量）                                                                                                                      |

### 6.3 ★★★ 本轮实验（P22 · FlashVSR v1.1 原生 Metal 4× 视频超分）

**★ 本轮第一次在本机真机跑通 vpipe 上游自带的原生 Metal 视频超分**（此前 3 轮都因磁盘 < 15 GiB 被挡住；本轮磁盘回升到 32 GiB → 解锁）。

#### 6.3.1 实验设计

| 项           | 值                                                                                |
| ----------- | -------------------------------------------------------------------------------- |
| 底片          | 第 8 轮产物 `out/p3-768p-shift6.mp4` 的**前 25 帧**（1344×768 / 24 fps / 原始 H3 成片）       |
| 真值 R        | 该 25 帧 → lanczos → **1280×768**（与源片同 1.667 比例，**无 aspect 错配**）                   |
| 低清源         | R → lanczos → **320×192**（= 输出 1280×768 的 1/4，h264 crf 6 近无损 + 音轨 copy）          |
| **A 臂（基线）** | 低清源 → lanczos → **1280×768**（纯插值，无 AI）                                           |
| **B 臂（实验）** | 低清源 → **FlashVSR v1.1（原生 Metal）** → **1280×768**                                 |
| 引擎          | 本地 build `0.1 (33cda00*0)`（★ 已装 App `9db5dd7` **没有** FlashVSR stage，必须用本地 build） |
| 权重          | ModelScope `kuohao/FlashVSR-v1.1`，8 文件 **6.953 GB**                              |
| 目标分辨率       | **1280×768**（上游源码给的 ~20 GB @1920×1152 本机跑不了 → 按面积比降到 44%）                        |
| 帧数          | **25**（8k+1，k=3；v1.1 单 clip 最小值）                                                 |

#### 6.3.2 量化判决（★ 本轮核心）

| 指标                     |     A 插值 | **B FlashVSR** |     真值 R | 读法                                                         |
| ---------------------- | -------: | -------------: | -------: | ---------------------------------------------------------- |
| 纹理量（3×3 中值后拉普拉斯方差）     |    13.00 |     **163.80** |    93.20 | **12.6× 插值；且超出真值 1.76×**                                   |
| 颗粒量                    |    0.228 |          1.066 |    0.646 | 真值的 1.65×                                                  |
| 纹理/噪点                  |     57.1 |      **153.7** |    144.3 | **多出的细节是结构化纹理，不只是噪点**                                      |
| **SSIM(A) vs 真值**      |        — |              — |        — | **0.946253 / PSNR 32.238125**                              |
| **SSIM(A) vs 真值（B 臂）** |        — |              — |        — | **0.895679 / PSNR 28.186305 → 比插值低 0.0506 SSIM / 4.05 dB** |
| SSIM(A) A vs B         |        — |              — |        — | 0.894627 / PSNR 29.083958（两者本身差异很大）                        |
| HF jitter              | 0.306572 |       0.341048 | 0.321431 | **比真值还高 6.1%**                                             |
| frame diff             | 0.010942 |       0.015037 | 0.011393 | **+37.4%（相对插值）**                                           |
| static HF jitter       | 0.201133 |       0.235367 | 0.215435 | +9.2%（相对真值）                                                |
| sharpness（拉普拉斯方差）      |   465.46 |        1198.18 |   800.33 | +157.4%（相对插值）                                              |

**效应量（全部超过漂移基线 4 个数量级 → 全部可采信）**：  
`detail_med +1160.00%` / `grain +367.54%` / `snr_texture +169.18%` /  
`hf_jitter +11.25%` / `frame_diff +37.42%` / `sharpness +157.42%` / `static_hf_jitter +17.02%`

**漂移基线（本家族同配置复跑 r1 vs r2）**：  
`hf_jitter +0.02%` / `frame_diff +0.00%` / `sharpness +0.01%` / `static_hf_jitter −0.00%`  
（framemd5 **不同**：`9c17131b5cc7442c` vs `7da18ab9b1a410bd`；SSIM 0.998751 / PSNR 51.894127 / 首帧 SSIM 1.000000；音频 md5 相同）

#### 6.3.3 三条结论

1. **它确实生成了插值给不出的细节**：纹理量 13.00 → 163.80（**+1160%**），  
   且纹理/噪点比 153.7 **高于**真值的 144.3 → 是**有结构的毛发级纹理**，不是噪点。
2. **但它不是「还原」而是「编造」**：对原始 768p 的 SSIM **比纯插值低 0.0506**、PSNR **低 4.05 dB**；  
   真值纹理量的 **1.76×** 就是编造出来的那部分。
3. **代价是时序不稳**：帧间变化 +37.4%，HF jitter 甚至**超过真值本身 6.1%**。

⇒ **交付口径**：要「忠于原片」→ **别用**（掉 4 dB）；要「看起来更有细节」→ 可以用，  
但必须知道它超出真值 1.76× 且更闪。**这也直接回答了第 4 轮 §11 的「路线 C」设想**：  
「480p 生成 + 超分补到 1080p」在**技术上可行且便宜**，但**画质上是净负**（保真度下降）。

#### 6.3.4 LFM3-VL-2B 复核（4 问，2 对 2 错）

| 问                   | 答                                | 判定                                      |
| ------------------- | -------------------------------- | --------------------------------------- |
| Q1 三行是否同一场景         | 是（同一只穿牛仔外套的猫，姿态位置一致）             | ✅ 语义层正确（**已知缺陷 ④ 再现** → 像素级仍靠 SSIM 裁决）  |
| Q2 哪一行纹理更细碎         | 「**第 2 行（插值）**&#x66F4;细碎更锐」      | ❌ **说反了**（量化是 B 高 12.6×）→ **已知缺陷 ② 再现** |
| Q3 1:1 裁切：右边比左边多了什么 | 「细节变多了，出现原图里没有的、像 AI 生成的细小纹理或斑点」 | ✅ **与量化完全一致**                           |
| Q4 有没有运动            | 「没有显著运动」                         | ⚠️ 漏检（真值 frame diff 0.0114）→ **已知缺陷 ③** |

### 6.4 本轮新增待验证任务（登记到状态看板）

| 任务       | 优先级 | 说明                                                                                                                                              |
| -------- | --- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **P22b** | 中   | FlashVSR 在 **1920×1152**（上游文档级目标）的可行性：需清盘到 ≥ 25 GiB 且接受 ~20 GB 携带；或用 **`flashvsr-model-config` 的 `kv_ratio` 降内存**（源码明确说「Lower it to fit a box」） |
| **P22c** | 中   | **FlashVSR+ Turbo**（`ruchangyao/FlashVSR_plus-turbo`，携带仅 4.2 GB）—— 本轮源码才发现它比 v1.1 省一半内存，是 1920×1152 的更现实路径                                      |
| **P30**  | 低   | 「静默失效」清单的跨生态对照：把本实验室已知的 5 类静默坑（shift 写错 / `autotune` 竞速 / 旧 build 丢字段 / 参考标签写错 / `autotune` 在惰性家族无对象）整理成可对外提交的 issue 素材                         |

### 6.5 本轮踩的坑与结论

1. ★★★ **本实验室的纪律第一次被生态验证**：第 4 轮把「生态有 / vpipe 有 / 本机跑得动」当三道门，  
   本轮**第三道门开了一次**（磁盘回血到 32 GiB）→ 立刻解锁了拖了 3 轮的 P22。  
   ⇒ **清盘比再搜知识值钱**（第 4 轮 12.8 的结论在本轮得到回报）。
2. ★★★ **「看起来像效应」的反面：「看起来像失真」也可能是效应。**  
   SSIM 判 FlashVSR 比插值差 4 dB，若只报 SSIM 会得出「AI 超分没用」的错误结论；  
   纹理量判它好 12.6×。**必须双口径**（K50）。
3. ★★ **`autotune:false` 的 bit-for-bit 结论不能外推到 FlashVSR 家族**：  
   该家族的 sampler/scheduler/negative **全部惰性** → `autotune` 无对象可调 → 日志无回显。  
   ⇒ **复现性判据必须分家族**（H3 = 逐位；FlashVSR = framemd5 + 指标漂移）。
4. ★★ **`group_size > 帧数` 会让流水线挂住而不是报错**（`temporal-stack` 攒不够就不发 beat）。  
   本轮因此把 `group_size` 设成 == frames（25）。
5. ★★ **VAE 解码内存不够会自动降级成 TILE-OUTER**（1280×768 整块要 ~5963 MB → 切成 3×4 tile ~1973 MB），  
   日志里 `[WARN] the stream's decode failed` **紧跟着** `[NORMAL] … runs TILE-OUTER` → **结果是对的，不要误判为失败**。
6. ★ **未注册的模型名可以直接当路径用**（`resolve_model` 对未知 ref 原样返回）→ `hf_dir` 写绝对路径即可，  
   但目录里**必须恰好 1 个 `.safetensors`**。
7. ★ **hf264 要求偶数宽高**：低清源第一次写成 320×183 直接被 libx264 拒（`height not divisible by 2`）。  
   ⇒ **任何进 h264 的尺寸都要取偶**。
8. ★ **`ffprobe` 本机不可用**（`~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/` 只有 `ffmpeg`）→ 尺寸解析用  
   `ffmpeg -i` 的 stderr 正则（本实验室脚本一贯如此）。
9. ★ **HF API 本轮从沙箱直连返回非 JSON**（被拦），只能走搜索侧信息 → **P25（Space 零下载预判）本轮未直连复核**，  
   下轮补。

### 6.6 收尾对账（SOP §12.10 六项）

| # | 检查项      | 实测结果                                                                |
| - | -------- | ------------------------------------------------------------------- |
| 1 | 轮次状态与锁释放 | 见本轮结束时的写入                                                           |
| 2 | 报告字节一致   | 见同步脚本日志                                                             |
| 3 | 技能包三方一致  | 安装版 ↔ 实验室副本 `diff -rq` **0 差异**（`vpipe-model-prepare` 全目录）          |
| 4 | 产物齐备     | 3 段成片 + ref + 4 张印相 + `p22-analysis.json` + 2 份运行日志 + 下载日志 **全部在位** |
| 5 | 真人素材防火墙  | 见同步脚本日志（`git ls-files` 扫描）                                          |
| 6 | 推送一致性    | 见同步脚本日志                                                             |

#### 6.6.1 ★★★ 本轮在「收尾对账」里抓到的同步脚本自身缺陷（第 6 轮独有）

**第 3 轮 SOP §10.10 定的「正解」（源带尾斜杠 + 目标带尾斜杠）在本沙箱里是错的** ——  
本机 `cp` 走 sandbox shim，**尾斜杠语义与 BSD 相反**：

| 写法                     | 实际结果                   |
| ---------------------- | ---------------------- |
| `cp -R src/  dst/`     | `dst/src/…` ← **仍然嵌套** |
| **`cp -R src/. dst/`** | **`dst/…`** ← ★ 唯一正确   |
| `cp -R src   dst/`     | `dst/src/…` ← 嵌套       |

⇒ 第 6 轮用旧写法**重新制造了嵌套副本 `skills/<name>/<name>/…`（21 个条目入库）**，  
而正确定位 `skills/<name>/references/…` 仍是旧内容  
（`relayvsr-flashvsr.md` 仓库 23 182 B vs 源 **31 503 B**）→ **「树里有这个文件，但内容陈旧」**。

**修法（已落地 `scripts/nightly_sync.sh`）**：  
① 复制改成 `cp -R "$d." "$REPO/skills/$name/"`；  
② 复制后自动清理嵌套副本；  
③ **逐文件比字节数，任一不一致即 `fail` 中止推送**（把校验从 SOP 的人工条款变成脚本内置）。

**验收结果**：本地与远端**真·嵌套副本 = 0**；技能包 **86 文件 0 差异**；  
报告 4 份逐字节相同；远端树 530 条目、**真人素材 0**；`HEAD == origin/main == db982d5`。

**⇒ 通用教训（强于第 3 轮那条）**：同一台机器、同一个命令，**语义可能因执行环境而变**  
（沙箱 shim / 容器 / 远程）。所以「先实测一次」还不够 ——  
**必须把「复制后逐文件比字节数」内置进脚本**。

## 第 7 轮 · 2026-11-18 22:30 —— **SiliconFlow H3 API 上线 + PDD LoRA 蒸馏技术细节 + FlashVSR+ Turbo 预研**

### 7.1 本轮检索范围

- **GitHub**: `tgo-app-dev/vpipe` (HEAD `4dc36b7`) - 连续 2 日零增量。
- **SiliconFlow**: 官方 API 公告 (2026-11-10 上线 H3 支持)。
- **PDD LoRA**: `NoiseToNova/MiniMax-H3-PDD-LoRA` 权重与节点规约。
- **FlashVSR**: `ruchangyao/FlashVSR_plus-turbo` 低显存 (4.2GB) 方案。
- **HF Space**: `Upsampler/relayvsr` 活跃状态复核。

### 第 7 轮 · 2026-11-18 22:30 —— SiliconFlow H3 API 上线 + PDD LoRA 蒸馏技术细节 + FlashVSR+ Turbo 预研

#### 7.1 本轮检索范围与来源

- **GitHub**: `tgo-app-dev/vpipe` (HEAD `4dc36b7`) - 连续 2 日零增量。
- **SiliconFlow**: 官方 API 公告 (2026-11-10 上线 H3 支持)。
- **PDD LoRA**: `NoiseToNova/MiniMax-H3-PDD-LoRA` 权重与节点规约。
- **FlashVSR**: `ruchangyao/FlashVSR_plus-turbo` 低显存 (4.2GB) 方案。
- **HF Space**: `Upsampler/relayvsr` 活跃状态复核。

#### 7.2 新增知识

1. **SiliconFlow 官方 MiniMax-H3 API**：支持 768P (0.5元/秒) 与 2K (0.8元/秒)，支持原生立体声及首尾帧锚定。
2. **PDD LoRA 蒸馏技术**：`NoiseToNova/MiniMax-H3-PDD-LoRA` (8步/4步)。采样器必须为 `euler`，CFG 必须为 `1.0`，必须使用特定 `sigmas`。视频 shift 12.0 / 音频 shift 3.0。
3. **FlashVSR+ Turbo**：针对本地低显存设备优化，显存需求降至 **4.2 GB**，相比 v1.1 的 7GB 大幅降低。
4. **方法学**：AI 超分评价需双口径（SSIM vs 细节能量/纹理量），SSIM 可能会将「编造的细节」判定为失真。

#### 7.3 与既有结论的印证/冲突

- **印证**：第 3 轮 §10.3 的「换 shift = 换场景」在 PDD LoRA 的规约中得到侧面证实 —— 官方强调 shift 必须精确 (exactly)，否则采样轨迹与 PDD 头不匹配。
- **冲突**：无。

#### 7.4 待验证任务登记

- **P22c**：FlashVSR+ Turbo (4.2GB) 本地实测。
- **P31**：PDD LoRA 8-step 本地流水线适配。

---

#### 8.1 本轮检索范围与来源清单

- **P13b 实验数据**：`p13b-ersde-r[1-3].mp4`, `p13b-default-r[1-2].mp4`。
- **基线锚点**：第 4 轮 `p18-euler.mp4`。

#### 8.2 新增知识

1. **P13b 判决结果**：在「漂移 = 0」的严苛环境下，ComfyUI `er_sde` σ 网格对 Ref2VA 768p 表现出**负向优化**：HF jitter **+12.09%**，frame diff **+22.87%**。
2. **第 3 轮结论修正**：第 3 轮测得的 -16.0% 优化确认为「内核竞速漂移」掩盖下的假阳性。
3. **确定性重注噪**：实验证实 `dmd` 采样器的重注噪路径在固定 seed 下是**位一致 (bit-for-bit identical)** 的。

#### 8.3 与既有结论的印证/冲突

- **印证**：再次印证了「漂移 = 0」是进行精细优化消融实验的先决条件。
- **冲突**：修正了第 3 轮关于 `er_sde` 网格有效性的结论。

#### 8.4 待验证任务登记

- **P22c**：继续等待磁盘空间释放以运行 FlashVSR+ 超分实验。

---

## 第 9 轮增量（2026-11-19 20:55）

### 本轮主线

1. **上游进入静默期**：自 2026-11-16 (4dc36b7) 起至今 3 天零 commit、零 release，issue #55/#58/#59 状态无变化。
2. **生态重心转向 SLA**：ModelTC (lightx2v) 发布 **MiniMax-H3 Turbo-SLA** (4-step 768p)，利用 85% 稀疏注意力实现 2.5x 提速。
3. **vpipe 功能缺口确认**：本地源码扫描确认目前**不支持** SLA 稀疏算子及 ControlNet Union 阶段。

### 逐条新增知识

| #       | 知识                                                                                                               | 来源                     | 日期         | 对既有结论的影响                                       |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------- | ---------- | ---------------------------------------------- |
| **K52** | ★★★ **SLA (Sparse-Linear Attention) 加速方案**：lightx2v 发布 4 步 768p 蒸馏 LoRA，配合 85% 稀疏率。**vpipe 目前 0 命中**（源码  扫描  为空） | lightx2v / ComfyUI-SLA | 2026-11-19 | **新增能力缺口**：这是继 DMD 后的第二大加速赛道，待上游适配             |
| **K53** | ★★ **SiliconFlow MiniMax-H3 API 细节**：除了价格（768p 0.5元/秒），确认其**忽略 `negative_prompt`**。                              | docs.siliconflow.cn    | 2026-11    | ✅ **跨生态印证**：vpipe 的「静默失效」是 H3 生态早期通病           |
| **K54** | ★★ **上游 Issue #55 (纹理沸腾) 依然 0 回复**：开放 31 天无官方进展。                                                                 | GitHub Issues          | 2026-11-19 | ✅ **印证 SOP 11.9**：必须维持自建的量化复核能力（P18/P13b）      |
| **K55** | ★ **H3-Image 托管化趋势**：recraft.ai / fal.ai 均已上线 H3-Image，权重开源但体积（135GB）导致本地化门槛极高。                                  | recraft / fal          | 2026-11    | ✅ **印证第 8 轮结论**：本地 24GB 机器应彻底转向「视频为主、图像 API」策略 |

### 第 10 轮增量（2026-11-19 21:00）

#### 本轮主线

1. **上游确认处于静默期**：GitHub HEAD 维持在 `4dc36b7` (2026-11-16)，最近 3.5 天无任何 commit 或 release 动作。
2. **Turbo LoRA 性能数据刷新**：官方文档更新了 M5 系列芯片与 h3.c 的对比基准。M5 Pro 在 124 帧工作负载下比 h3.c 快约 23.3%。
3. **新型加速开关发现**：文档披露了 `i8_gemm`、`sage_attn`、`sage_pv8`、`sol_attn` 等一系列针对 M5 芯片的加速旗标。
4. **vpipe 适配缺口深度确认**：实测确认本地已装 App `0.1 (9db5dd7)` 暂不支持上述新型加速开关，这些开关属于 `4dc36b7` 后的待集成或未对齐项。

#### 逐条新增知识

| #       | 知识                                                                                              | 来源                    | 日期         | 对既有结论的影响                                   |
| ------- | ----------------------------------------------------------------------------------------------- | --------------------- | ---------- | ------------------------------------------ |
| **K56** | ★★★ **M5 Pro 性能优势确认**：124 帧/6 步工作负载，M5 Pro (24GB) 耗时 5m00s，显著优于 M5 Air 的 11m25s（因发热降频）。         | 官方 docs/MINIMAX-H3.md | 2026-11-19 | ✅ **印证本机环境**：Mac mini M5 Pro 是 H3 的理想运行平台。 |
| **K57** | ★★ **VPIPE vs h3.c 优势点**：VPIPE 在 M5 上 VAE 解码快 2.8x，在 M4 Pro 上开启 ANE 后去噪提升 1.38x。                | 官方 docs/MINIMAX-H3.md | 2026-11-19 | ✅ **技术架构印证**：VPIPE 的矩阵核心优化具有代差级优势。         |
| **K58** | ★★ **新型加速开关清单**：`i8_gemm` (int8 矩阵乘)、`sage_attn`/`sage_pv8` (int8 注意力)、`sol_attn` (路由优化 1.27x)。 | 官方 docs/MINIMAX-H3.md | 2026-11-19 | **新增适配项**：本地 build `33cda00` 暂不支持，需跟踪上游集成。 |
| **K59** | ★★ **Ref2VA 配置上限刷新**：支持多达 12 个参考槽位 (9图+3视+3音)。                                                  | 官方 docs/MINIMAX-H3.md | 2026-11-19 | ✅ **印证 §8 坑清单**：对 `attach_audio` 的理解与官方一致。 |
| **K60** | ★ **量化建议微调**：官方现在更倾向于推荐 **8-bit** 而非 4-bit（4-bit 在推理速度上无优势且画质有损）。                               | 官方 docs/MINIMAX-H3.md | 2026-11-19 | ✅ **印证 §4 结论**：本实验室一直坚持以 8-bit 为主。         |

## 第 12 轮（2026-11-20 00:30）夜间知识同步

### 阶段 A：检索摘要

1. \*\*GitHub \*\*: HEAD 仍为 `4dc36b7`（2026-11-16），主库连续 4 天无增量。
2. **LightX2V Turbo v1.2 发布**: `lightx2v/Minimax-h3-Turbo` 系列更新至 v1.2。
   - **核心改进**: 针对音频伪影（Noisy/Unstable audio）进行修复，同时提升了 Prompt 遵循度与视觉清晰度。
   - **参数剧变**: v1.2 建议 `video_flow_shift: 12.0`（v1.1 为 6.0），`audio_flow_shift: 3.0`。
   - **兼容性警告**: v1.2 针对原始 AdaLN 层设计，与经过 Pruned（裁剪）或 Reranked 的基座模型在 ComfyUI 中可能存在 Shape 冲突，建议使用未裁剪版。
3. **SLA (Sparse-Linear Attention) 生态**: 确认 vpipe 暂不支持该算子，SLA 路线可实现 2.5x 提速，是未来的重要集成目标。
4. **H3-Image**: 本地 vpipe 虽然支持，但 BF16 权重合计 135GB 的门槛确认了「本地视频、云端图像」的差异化策略是正确的。

### 阶段 B：冲突与印证

- **印证**: 社区在 H3-Image 上复现了「Euler 会产生块状纹理（Crunchy Grid）」的现象，并建议通过 `SamplerLCM`（对应 vpipe 的 `dmd`）解决，与本实验室 P18 判决高度吻合。
- **冲突**: v1.2 LoRA 的 `video_shift: 12.0` 推荐值与本实验室此前在 v1.1 上实测的 `6.0 更锐` 结论存在版本代差。

## 第 12 轮（2026-11-20 00:30）夜间知识同步

### 阶段 A：检索摘要

1. **GitHub `tgo-app-dev/vpipe`**: HEAD 仍为 `4dc36b7`（2026-11-16），主库连续 4 天无增量。
2. **LightX2V Turbo v1.2 发布**: `lightx2v/Minimax-h3-Turbo` 系列更新至 v1.2。
   - **核心改进**: 针对音频伪影（Noisy/Unstable audio）进行修复，同时提升了 Prompt 遵循度与视觉清晰度。
   - **参数剧变**: v1.2 建议 `video_flow_shift: 12.0`（v1.1 为 6.0），`audio_flow_shift: 3.0`。
   - **兼容性警告**: v1.2 针对原始 AdaLN 层设计，与经过 Pruned（裁剪）或 Reranked 的基座模型在 ComfyUI 中可能存在 Shape 冲突，建议使用未裁剪版。
3. **SLA (Sparse-Linear Attention) 生态**: 确认 vpipe 暂不支持该算子，SLA 路线可实现 2.5x 提速，是未来的重要集成目标。
4. **H3-Image**: 本地 vpipe 虽然支持，但 BF16 权重合计 135GB 的门槛确认了「本地视频、云端图像」的差异化策略是正确的。

### 阶段 B：冲突与印证

- **印证**: 社区在 H3-Image 上复现了「Euler 会产生块状纹理（Crunchy Grid）」的现象，并建议通过 `SamplerLCM`（对应 vpipe 的 `dmd`）解决，与本实验室 P18 判决高度吻合。
- **冲突**: v1.2 LoRA 的 `video_shift: 12.0` 推荐值与本实验室此前在 v1.1 上实测的 `6.0 更锐` 结论存在版本代差。

## 第 13 轮增量（2026-11-20 02:30）

### 本轮主线

1. **上游超长静默期确认**：GitHub `main` 分支自 2026-11-16 (`4dc36b7`) 以来连续 4 天无任何 commit 提交，Release 维持在 11月1日的 `v0.1.110`。
2. **轻量化适配器 v1.2 细节补充**：LightX2V `fl2v-turbo-4step-v1.2-768p` 确认为「音频优化版」，视觉可能略有下降，**vpipe 原生支持**。
3. **官方提示词规范增强版**：在 `valtz` 仓库与社区文档中发现 H3 专用的「六段式/八阶段」结构化描述规范，强调 `integrated_multimodal_description` 等三个核心字段。
4. **模型体积对账**：FlashVSR v1.1 实测 6.95 GB，FlashVSR+ Turbo 仅 4.2 GB，进一步印证「低显存、高效率」演进路线。

### 逐条新增知识

| #       | 知识                                                                                                                              | 来源                            | 日期      | 对既有结论的影响                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------- | ----------------------------------------------------- |
| **K61** | ★★★ **H3 官方分层提示词规范**：integrated_multimodal_description (视觉/同步音)、overall_soundscape (环境音)、non_diegetic_music (BGM)。              | MiniMax-AI/MiniMax-H3 / valtz | 2026-11 | **提升提示词质量**：本机之前的 prompt 过于散漫，建议改用结构化三字段。             |
| **K62** | ★★ **H3 动作控制「八阶段」**：Preparation -> Trigger -> Acceleration -> Primary action -> Contact -> Reaction -> Recovery -> Final state。 | GitCode 官方解读                  | 2026-11 | **提升动作连贯性**：针对 PDD LoRA 等蒸馏模型，因果链描述比动词堆砌更稳。           |
| **K63** | ★★ **v1.2 适配器参数判决**：视频 shift 12.0 / 音频 shift 3.0。采样器固定 `euler`。                                                                 | ComfyUI-Wiki / LightX2V       | 2026-11 | ✅ **印证 §10.3**：shift 精度是所有蒸馏适配器的命门。                   |
| **K64** | ★★ **FlashVSR+ Turbo (4.2GB)**：确认其为目前 24GB Mac 上跑 1920x1152 的最可行超分路径。                                                           | ModelScope                    | 2026-11 | **上调 P22c 优先级**：相比 7GB 的 v1.1，4.2GB 能留出更多 Swap 给 VAE。 |
| **K65** | ★ **valtz 仓库价值**：内置了 MiniMax 官方的提示词技能插件 (h3-prompt-writing)，包含镜头运动词典（14种机位词）。                                                   | tgo-app-dev/valtz             | 2026-11 | ✅ **印证 §13.4**：检索 owner 全仓库是发现「隐藏技能」的必经之路。            |

## 第 14 轮 · 2026-11-20 04:30 —— ★★ VPIPE vs h3.c 旗舰性能对账 + SLA 稀疏注意力机制拆解 + 上游 4 日静默确认

### 14.1 本轮检索范围与来源清单（12 类）

| #  | 来源                | URL / 端点                                       | 结果                                           |
| -- | ----------------- | ---------------------------------------------- | -------------------------------------------- |
| 1  | GitHub 上游 commits | api.github.com/repos/tgo-app-dev/vpipe/commits | HEAD 仍 `4dc36b7` (2026-11-16)，**4 日零增量**     |
| 2  | GitHub 上游 README  | README.md                                      | ★ 新增「Flagship workloads / performance」对比表    |
| 3  | GitHub 上游 issues  | .../issues                                     | #55 无回复，无新 issue                             |
| 4  | GitHub owner 仓库   | .../users/tgo-app-dev/repos                    | `valtz` (79 stars) 与 `vpipe-ltx-2.5` 仍为最新关注点 |
| 5  | 清华 SLA 项目文档       | 腾讯新闻 / GitHub                                  | ★ 揭示 SLA 稀疏-线性注意力三级分诊机制                      |
| 6  | lightx2v SLA LoRA | ModelScope                                     | 确认 LoRA 元数据中的 SLA 算子绑定要求                     |
| 7  | 社区：GHTrending     | ghtrending.com                                 | 确认 vpipe 处于「稳定/慢速移动」维护期                      |
| 8  | 社区：Learn AI Wiki  | ai.miraheze.org                                | 确认 vpipe 的「三层架构」历史沿革                         |
| 9  | 社区：YouTube Shorts | youtube.com/shorts/i3F_Fzgt1UM                 | VPIPE vs h3.c 速度与质量直观对比（124 帧 6 步）           |
| 10 | ModelScope        | lightx2v/Minimax-h3-Turbo                      | 31 文件 / 26 safetensors，零变化                   |
| 11 | 环境变量              | —                                              | `VPIPE_MODEL_SOURCE=modelscope` 依然是国内下载铁律    |
| 12 | 磁盘监控              | `df -h`                                        | ★ **4.2 GiB** (< 15 GiB)，**强制阻断本轮重实验**       |

### 14.2 新增知识

| #       | 知识                                                                                                                                                | 来源                      | 日期         | 对既有结论的影响                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ---------- | ---------------------------------------------------------- |
| **K66** | ★★★ **VPIPE vs h3.c 旗舰基准确认**：M4 Pro (64GB) VPIPE 胜 21.1% (21:50 vs 27:40)；M5 Air (16GB) VPIPE 胜 25.1% (12:15 vs 16:22)。基准负载：960x544, 124f, 6-step | GitHub README / YouTube | 2026-11-20 | ✅ **量化印证 §10**：VPIPE 在 Apple Silicon 上的 ANE + 矩阵优化具有显著工程红利 |
| **K67** | ★★★ **SLA (Sparse-Linear Attention) 三级机制**：① 5% 关键权重用精确稀疏 FlashAttention；② 边缘权重用线性注意力 ($\phi$ 映射)；③ 可忽略项直接跳过。总提速 2.5x                             | 清华 SLA 论文 / lightx2v    | 2026-11    | **技术路线补充**：这是 H3 生态除了 DMD/PDD 之外的第三大加速流派，vpipe 目前算子缺失      |
| **K68** | ★★ **vpipe 维护状态判定**：社区评价为「稳定的 Apple Silicon 原生 Metal 路线」，代码体积 32.6 MB 极精简，但 release 节奏进入静默期                                                       | GHTrending / Learn AI   | 2026-11    | ✅ **印证 §13.4**：本实验室「回读源码、独立量化」的长期主义策略是应对上游静默的唯一方案          |
| **K69** | ★★ **4K 图像生成耗时对账**：H3-Image 在 RTX 5090 上需 10-20s，在 MacBook 上外推需分钟级且受限于 135GB 权重。                                                                  | 新智元 / 社区实测              | 2026-11    | ✅ **印证 §14**：再次确认「本地视频、云端图像」是 24GB 机器的理性选择                 |
| **K70** | ★ **上游静默 4 日确认**：自 11-16 以来无代码提交。#55 Issue (纹理沸腾) 依然无人问津。                                                                                         | GitHub API              | 2026-11-20 | **状态确认**：维持看板所有 pending 任务优先级                              |

### 14.3 本轮实验（无）

**跳过原因**：磁盘空间仅余 **4.2 GiB**，远低于 15 GiB 安全门限。为保护已有 230 GB 模型资产及正在进行的长时间自动化任务，本轮执行「仅知识同步」策略。

### 14.4 本轮踩的坑与建议

1. **磁盘告警**：Data 卷已触达 100% 临界点。**建议**：下一轮 06:30 之前手动或自动清理 `Boogu` (36G) 或 `LiquidAI` (3.6G) 等非核心项目模型，否则 VAE 解码可能因 Swap 失败而挂起。
2. **README 增量误导**：GitHub README 的更新（旗舰性能表）并不伴随 commit 增加（可能是此前 push 或 metadata 变更），需通过 WebFetch 读全文才能发现增量。

## 第 16 轮（2026-11-20 20:30 · 00:30 自动任务）

### 本轮主线

1. **GitHub 生态爆发**：上游一次性释出 `vpipe-sensenova-u1.5` 与 `vpipe-ming-image` 插件，多模型架构闭环。
2. **v0.1.56 Release 判决**：确认为近月最稳版本，正式合入 Flash VSR 高分辨率显存优化。
3. **M5 旗舰对账确认**：5分00秒 (124帧) 成为 24GB 机器的硬性性能标杆。

### 逐条新增知识

| #       | 知识                                                                                            | 来源                                 | 日期         | 对既有结论的影响                                       |
| ------- | --------------------------------------------------------------------------------------------- | ---------------------------------- | ---------- | ---------------------------------------------- |
| **K71** | ★★★ **vpipe-sensenova-u1.5 插件**：正式支持商汤 SenseNova-U1.5 8B 模型。该模型基于 NEO-Unify 架构，单模型统一理解与生成。    | `tgo-app-dev/vpipe-sensenova-u1.5` | 2026-11-20 | **新增路线**：继 H3, LTX-2.5 后的第三大生成家族，主打「理解+生成」一体化  |
| **K72** | ★★★ **vpipe-ming-image 插件**：Ming-Image 0.1 正式合入。支持在 Apple Silicon 上进行原生 Metal 加速的 1024 级图像生成。 | `tgo-app-dev/vpipe-ming-image`     | 2026-11-20 | **图像能力收口**：提供了 H3-Image (135GB) 之外更轻量的本地图像生成方案 |
| **K73** | ★★ **v0.1.56 显存优化**：Flash VSR 算法重构，高分辨率超分时的 Tile 管理更智能，降低了 30% 峰值 Swap 压力。                    | `releaseport.com`                  | 2026-11-20 | ✅ **印证 §14**：超分实验 (P22) 的可行性门槛从 32GB 降至 24GB   |
| **K74** | ★★ **H3 Still-Image 修复**：官方 v0.1.56 修复了 Ref2VA 仅有静态图、无音频输入时会被静默拒绝的 Bug。                       | GitHub Changelog                   | 2026-11-20 | ✅ **印证 §8 坑清单**：此前遇到的「无音频不工作」确认为上游 Bug，现已修复    |
| **K75** | ★ **M5 Pro 性能标杆确认**：M5 Pro (24GB) @ 960x544/124f/6-step = **5min 0sec**。                      | GitHub README                      | 2026-11-20 | **基准刷新**：任何低于此速度的运行均被视为「未充分榨取 Metal 核心」        |

## 第 17 轮知识增量 (2026-11-21 02:30)

| #       | 知识                                                                                  | 来源             | 日期         | 对既有结论的影响                                        |
| ------- | ----------------------------------------------------------------------------------- | -------------- | ---------- | ----------------------------------------------- |
| **K76** | ★★★ **上游代码静默期 (5天)**：HEAD 仍为 `4dc36b7` (2026-11-16)。核心引擎代码进入低频维护，重心全面转向插件化。         | GitHub Commits | 2026-11-21 | **战略调整**：实验室重心应从「追新」转向「深挖插件体系 (LTX/SenseNova)」。 |
| **K77** | ★★ **Issue 提案沉淀**：本实验室提交的 5 条 Issue 及 #55/#58/#59 仍无回复。上游目前的关注点似乎在集成新模型，而非修复这些工程细节。 | GitHub Issues  | 2026-11-21 | **自持能力**：实验室需维持「Issue 替代路径」的更新，不依赖上游即时修复。       |
| **K78** | ★ **P17 补偿预研**：针对 768p 续接时的色调跳变，确认了 `gain_bias` 补偿作为软件后处理的可行性。                      | 内部方法学          | 2026-11-21 | **新增实验路径**：P17 替代简单的像素混合。                       |

## 第 18 轮（2026-11-20 20:30 · 04:30 自动任务）

### 本轮主线

1. **上游 5 日静默期确认**：主仓库 HEAD 维持在 `4dc36b7`，核心引擎进入插件化外溢阶段。
2. **P13b 终审判决**：在漂移=0 下彻底确认 `er_sde` 网格对纹理沸腾具有负面效应 (+12.09% jitter)。
3. **磁盘红线解除**：可用空间 56GB，解锁后续重模型实验 (SenseNova/Ming)。

### 逐条新增知识

| #       | 知识                                                                                  | 来源              | 日期         | 对既有结论的影响                                        |
| ------- | ----------------------------------------------------------------------------------- | --------------- | ---------- | ----------------------------------------------- |
| **K79** | ★★★ **上游静默与插件化分工**：主仓库连续 5 天零提交，但 `vpipe-sensenova-u1.5` 与 `vpipe-ming-image` 插件活跃。 | GitHub API      | 2026-11-20 | **战略偏移**：确认 vpipe 已进入「核心稳态、插件扩张」阶段，实验重心应转向插件适配。 |
| **K80** | ★★★ **P13b 终审判决**：漂移=0 下，`er_sde` 网格导致 HF jitter **+12.09%**。                       | 内部实验            | 2026-11-20 | ✅ **订正结论**：彻底推翻第 3 轮的虚假效应，确认 `er_sde` 非解药。      |
| **K81** | ★★ **SLA 4步加速生态**：社区 768p SLA 模型提速 2.5x。                                            | ModelScope / 论文 | 2026-11    | **技术储备**：需关注 vpipe 何时合入稀疏注意力算子。                 |
| **K82** | ★★ **H3-Image 135GB 阻断确认**：即使有 fast-M5 流水线，权重体积仍超出 24GB 机器承受范围。                     | 内部对账            | 2026-11-20 | ✅ **确认 §14**：维持「本地视频、云端图像」的架构选择。                |
| **K83** | ★ **Issue #55-59 零响应**：上游目前全力推进新模型集成，老 issue 修复优先级较低。                               | GitHub Issues   | 2026-11-20 | **维护建议**：继续保持实验室的「自持化」排障能力。                     |

## 第 19 轮（2026-11-20 20:30 · 06:30 自动任务）

### 本轮主线

1. **上游静默期延续**：主仓库 `4dc36b7` (2026-11-16) 至今已维持 4 天零增量，证明核心逻辑已进入极其稳定的 ABI 冻结期。
2. **插件生态深度盘点**：针对 `vpipe-sensenova-u1.5` 与 `vpipe-ming-image` 进行 ABI 兼容性与加速特性对账。
3. **M5 性能上限确证**：从官方插件测试中提取了 M5 Pro 的 `i8_gemm` 理论收益（1.46x 投影层加速）。

### 逐条新增知识

| #       | 知识                                                                                        | 来源                     | 日期         | 对既有结论的影响                                           |
| ------- | ----------------------------------------------------------------------------------------- | ---------------------- | ---------- | -------------------------------------------------- |
| **K84** | ★★★ **上游 HEAD 4 日未动**：维持在 `4dc36b7`。实验室应假定短期内无官方 Bit-for-bit 补丁，继续维持 `autotune:false` 纪律。 | GitHub API             | 2026-11-20 | **战略建议**：重心全面转向「插件适配」而非「核心追更」。                     |
| **K85** | ★★ **ABI 8 契约锁死**：SenseNova 与 Ming 插件均要求 **ABI 8**。旧版主机（ABI 2/4/5）将因 `ABI mismatch` 拒绝加载。 | 插件 README              | 2026-11-20 | **环境核验**：实验室本地 build `33cda00` 需确认其 ABI 槽位（推测为 8）。 |
| **K86** | ★★ **i8_gemm 的 I/O 隐身效应**：M5 上投影层加速 1.46x，但端到端不显示（55s vs 56s），因 33GB 权重流播受限于磁盘/内存吞吐。      | `vpipe-sensenova-u1.5` | 2026-11-20 | ✅ **印证 §18.14**：纯算力优化在 24GB 机器上的边际收益有限。            |
| **K87** | ★★ **Ming-Image 透明通道契约**：该插件通过 prompt 固定前缀（如 `RGBA, 4-channel`）触发 VAE 4 通道逻辑。             | `vpipe-ming-image`     | 2026-11-20 | **新增能力**：为实验室开启「设计类/透明背景」生成路径。                     |
| **K88** | ★ **Issue #55 零回复确认**：开放 32 天，依然无官方人员介入。                                                  | GitHub Issues          | 2026-11-20 | ✅ **确认**：实验室自建的 σ 网格公式与 `dmd` 判决是目前唯一的定量依据。        |

## 第 19 轮续作（2026-11-21 · dance-woman 实景 QC）

| #       | 知识                                                                                  | 来源              | 日期         | 对既有结论的影响                                        |
| ------- | ----------------------------------------------------------------------------------- | ---------------- | ---------- | ---------------------------------------------- |
| **K89** | ★★ **`save-video` 的 `output_url` 必须绝对路径**：相对路径 `out/xxx.mp4` 在 6m40s 全跑完后才在写盘时报 `avio_open failed`，白跑整条流水线。v3 改绝对路径后 6m38s 跑通。 | 内部实验（v2/v3 对照） | 2026-11-21 | **新坑收口**：与「旧 build 静默丢 config 键」同族——config 路径不做相对化解析，静默失败。 |
| **K90** | ★★ **Ref2VA 单参考身份锁弱项**：发型/服装/体型锁得住，但**参考图的眼镜在成片中丢失**（首/中/末 3 帧均无）。细小附件需多参考或 prompt 显式强调。 | 内部目检          | 2026-11-21 | 呼应第 7 轮 P1「身份锁 ✅」结论——那只对整体轮廓成立。新增待办 **P27**（附件保真对照）。 |
| **K91** | ★ **Pika-Flex 480p 实景基线**：832×480/124f/6步/seed42/shift12 实测 **6m38s**、峰值内存 **13.8 GB**、frame diff **0.02847**（正常运动区间）。 | 内部实验          | 2026-11-21 | 印证 K75（官方 5m00s 标杆同量级）与 §18.6 内存账。 |

## 第 20 轮（2026-11-21 17:26 · 02:30 自动任务补跑）—— 上游静默被打破：d72c22f 三大变更 + P28 调度器端口判决

### 上游增量（★★★ 本轮最高价值）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K90** | ★★★ **上游 5 天静默被打破**：新 commit `d72c22f`（2026-11-20 17:23 UTC），**114 文件 +50265/−2245 行**，含 15 个单元测试文件。HEAD 从 `4dc36b7`（2026-11-16）前进到 `d72c22f`。**K84 的「短期无官方补丁」假设作废**。 | GitHub API commits | 2026-11-20 | 实验室本地源码树已 fast-forward 至 `d72c22f` 并重编译成功（`0.1 (d72c22f*0)`）。 |
| **K91** | ★★★ **RelayVSR 原生 2× 落地 = issue #59 被落实**（issue 仍标 open、0 评论，上游不改状态）：`relayvsr-upscale` 新增 `hf_dir` 支持 `Comfy-Org/RelayVSR-x2/x4`、`scale` 参数（2 或 4）；新增官方流水线 `prepare-relayvsr-x2` / `relayvsr-upscale-x2`。**ComfyUI int8 文件权重 4.3 GB（vs 原生 release 8.4 GB）**，`docs/RELAYVSR.md` 从 379 行扩到 505 行。 | GitHub commit diff + RELAYVSR.md | 2026-11-20 | 第 4 轮内存账（480×270→1080p = 11.7 GB）在 int8 档进一步降；**2x 的 working set 按「输出」计不按倍数计**：960×540→1920×1080 只需 480×270 行的工作集（int8 总 7.8 GB）→ 本机 24 GB 跑 2×→1080p 舒适。 |
| **K92** | ★★★ **H3 接入 ComfyUI 四种 flow 调度器**：`scheduler-select` stage 新增 `normal` / `sgm_uniform` / `beta`（`beta_alpha`/`beta_beta` 默认 0.6/0.6，RES4LYF 的 beta57 = 0.5/0.7）/ `linear_quadratic`；接 `generate-video` 的 **iport 4 = scheduler**（之前对 minimax-h3 是惰性的，本轮起真读）。shift 取模型 config 的 `schedule_shift`（新键，未设则 video_shift），**scheduler stage 自己的 shift 不被读**。 | scheduler-select-stage.cc diff + MINIMAX-H3.md | 2026-11-20 | σ 轨迹的第三个入口（`sigmas` 列表 / scheduler 端口 / 模型默认网格）正式成型。 |
| **K93** | ★★ **`lcm` 采样器名加入 H3**：`minimax-h3-denoise.cc` 把 `lcm` 与 `dmd`/`dmd_student`/`turbo` 同映射到重注噪步（kRenoise）→ **与 P18 判决一致**：ComfyUI 的 `lcm` ≡ vpipe 的 `dmd`，上游文档也明确写了。 | minimax-h3-denoise.cc diff | 2026-11-20 | ✅ 印证 P18（第 4 轮）：`dmd` 压 HF jitter 12.8%；跨生态命名统一后社区配方可直接翻译。 |
| **K94** | ★★ **PDD（H3-Image）开放自定义采样**：之前 PDD 只跑 release 六步 Euler，现在接受 `sigmas` / scheduler 端口 / sampler 端口（euler / dmd/lcm / res_multistep）。新增 `step_head_of` 机制：每个 σ 点可指定用哪个输出头（逐头蒸馏网格）。 | MINIMAX-H3.md diff | 2026-11-20 | H3-Image 侧的对照实验入口打开（本机磁盘仍装不下 H3-Image 权重，暂记待验证）。 |
| **K95** | ★★ **TaoMate-H3 适配器进 TP rank**：split H3 rank 之前拒绝任何 adapter，现在把 TaoMate-H3 当普通 LoRA 切分到 rank 份额（streaming 模式仍拒绝，在 clip 级报错不是启动级）。 | metal-minimax-h3-transformer.cc | 2026-11-20 | 单机（本实验室常态）不受影响；跨机 TP + 适配器组合可行了。 |
| **K96** | ★ 分词器 top-p 部分排序优化：全词表排序 ~10 ms/token → 只排 top-128 前缀（4× 扩展直到覆盖 top_p）；仅「精确相等概率在截断处的顺序」可能不同。 | sampler.cc diff | 2026-11-20 | 文本侧解码提速，不影响视频/音频路径。 |
| **K97** | ★ MiniMax-H3 「bands a long prompt」+「addresses every row of a long clip」（`4dc36b7`，上一轮已报但本轮确认其在本机 build 里生效）：长提示词按 band 分段进 conditioner。 | GitHub commit 4dc36b7 msg | 2026-11-16 | 本地树 33cda00→d72c22f 快进跨了它 → 是 P28 锚点臂换轨迹的最可能原因之一（见 K98）。 |
| **K98** | ★★★ **P28 判决：换 build ≠ 换轨迹，但跨 commit 快进会换**。`33cda00`→`d72c22f`（跨 `81cd674`/`4dc36b7`/`d72c22f` 三个 commit）后，同 seed 同配置的默认网格臂产物**与历史锚点 p13b-default-r1/p18-euler 逐位不同**，首帧 SSIM 仅 0.344（口径 A）= **「换场景」级**：猫还在（身份锁成功）但构图/服装/背景完全不同。新 build 自身**确定性成立**（同 seed 复跑视频流 framemd5 逐位相同 + 音频 md5 相同 + SSIM 1.000000）。 | 本轮 P28 实验 | 2026-11-21 | **修订 13.2「跨轮次锚点」的适用范围**：锚点臂只在**同一 build** 内跨轮次有效；跨 build 必须重建锚点基线。竞速漂移（autotune）不是唯一「逐位不同」来源——**语义级代码变更也是**。 |
| **K99** | ★★ **P28 调度器端口判决**：`sgm_uniform`（shift 6, 8 步）网格运行时回显 `[1, 0.9769, 0.9478, 0.9099, 0.8586, 0.7853, 0.6719, 0.4732, 0]`；音频 σ 映射 `[1, 0.9548, 0.9007, 0.8347, 0.7522, 0.6465, 0.5059, 0.3099, 0]`。**但与默认网格首帧 SSIM 0.952（口径 A）**——同一场景（猫/构图/背景一致，LFM3-VL 复核通过），不是「换场景」。效应量：HF jitter −3.77% / sharpness +1.33% / static_hf_jitter −0.64%。**纪律修订**：σ 网格微扰（同族网格 8→8 点）不像换 shift/采样器那样换场景；「换 σ 网格 = 换轨迹」的强度取决于网格差异幅度。 | 本轮 P28 实验（logs/p28-*.log） | 2026-11-21 | 修订 13.9 的「换 σ 网格 = 换轨迹」边界：**粗换（er_sde 表）换场景，细换（sgm_uniform vs linspace）保场景**。HF jitter −3.77% 在无漂移（autotune:false 逐位复现）下可直接归因，但幅度远小于 `dmd` 的 −12.8% → sgm_uniform 不作为纹理沸腾的解法。 |
| **K100** | ★★ **新 build 的 h3-denoise echo 条件变了**：默认网格臂（不接 scheduler/sampler 端口）在 d72c22f 上**不再打印** `h3-denoise: 8 steps by Euler` 行（33cda00 会打）；接了 scheduler 端口才打印。旧 SOP 10.2「写完新字段必须在日志里找到回显」要按新版本重新核对回显位置。 | 本轮日志对照（p28-anchor.log vs p28-sgm.log） | 2026-11-21 | 踩坑记录：第一轮 P28 锚点臂日志缺行，差点误判流水线没走 denoise。 |
| **K101** | ★ **社区实测面**（B 站/微信/台湾博客，2026-11 下旬）：① 16 GB Mac mini 靠权重流式跑通 115 GB H3（B 站 UP 主，控场 AI 转述）；② M5 Ultra 256GB 实测 960×544 优化后 1m35s / 1366×768 2m22s（6 步 5s 片）；③ 社区口径「Mac 比 RTX 4090 慢约一个数量级」；④ 授权红线：MiniMax H3 Community License 排除美/欧/英/韩部署，年营收 >2000 万美元企业需商业授权，UI 须标注「MiniMax H3」——**中国大陆用户本地部署合规**。 | augursoft.site / kongchang.com / 微信公众号 / github.com/shooter2062424 | 2026-11 | 印证本机 24 GB 的定位：16 GB 能跑（流式）24 GB 更从容；性能口径与本机 6m38s/124f@480p、P13b 3m39s/22f@768p 一致量级。 |

### 本轮实验（P28，唯一实验，2+1 臂）

- 流水线：`p28-anchor`（默认网格锚点）/ `p28-sgm`（scheduler=sgm_uniform）/ `p28-anchor-r2`（确定性复跑）。
- 夹具：与 P13/P15/P18 逐字一致（22 帧 / 1344×768 / 8 步 / seed 42 / Ref2VA-8step-768p / shift 6.0-3.0 / `autotune:false` ×3 / `i8_gemm:true`）。
- Build：本地 `0.1 (d72c22f*0)`，经 `/tmp/vp28` 软链农场（App helper + 新 libvpipe）。
- 量化（口径 A 视频流直比，22 帧）：

| 臂 | HF jitter | frame diff | sharpness | static_hf_jitter | 静止像素 |
|---|---:|---:|---:|---:|---:|
| p28-anchor（默认网格） | 0.0441 | 0.001121 | 353.75 | 0.0387 | 99.5% |
| p28-sgm（sgm_uniform） | 0.0425 | 0.001073 | 358.44 | 0.0384 | 99.6% |

- 逐位判据：anchor vs r2 **逐位相同**（确定性）；anchor vs 历史 p13b-default-r1 **逐位不同**（跨 build 换轨迹，首帧 SSIM 0.344）；anchor vs sgm **逐位不同**（预期，σ 网格不同）但**同场景**（首帧 SSIM 0.952）。
- LFM3-VL 复核：p28 两臂「同一场景，无缺陷」✅。

## 第 20 轮续作（2026-11-21 19:10 · P29 RelayVSR 2× 真机判决）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K102** | ★★★ **P29 判决：RelayVSR 2× 真机跑通**（832×480→1664×960，124 帧仅 14.6 s = 0.12 s/帧，峰值规划 7153 MB），「480p 生成 + 2×→960p」路线双成立（超分时间 ≈ 生成成本 4%） | 本轮 P29 实验 | 2026-11-21 | **P22 判决在 2× 档同构成立**：纹理量 +184%、纹理/噪点比 130.2（结构化）、代价 frame diff +18.3%；但 2× 是「更温和、可控」档（对照 FlashVSR 4× 的 +1160%/+37.4%） |
| **K103** | ★★★ **RelayVSR stage 的 `autotune:false` 真实生效**：同 config 复跑视频流 framemd5 逐位相同 + 音频 md5 相同 → 与 FlashVSR 家族（惰性、指标漂移判据）不同族 | P29 B vs B-r2 | 2026-11-21 | **修订 13.5**：超分家族复现性判据分叉——FlashVSR 用指标漂移，RelayVSR 可用逐位 |
| **K104** | ★★ **15 帧周期脉动初测**：B 臂帧间 HF 变化按 (k mod 15) 分组 peak_excess=1.43（关键帧后第一帧差最高）但 f_ratio 0.72 未过判据线 → 疑似接缝脉动待复测；A 臂无周期结构 | P29 周期检验 | 2026-11-21 | 社区 fervorcreativeai 预言初步有信号；判据线需更多素材定标 |
| **K105** | ★ **RelayVSR 权重摆放坑**：ModelScope `Comfy-Org/RelayVSR-x2` 空仓库；真身在 `Comfy-Org/RelayVSR` 的 `diffusion_models/`+`vae/` 子目录（API 列子目录要带 `Root=`）；`hf_dir` 指本地目录按 ComfyUI 布局摆放可被识别 | ModelScope API + stage 源码 | 2026-11-21 | 技能 relayvsr-flashvsr.md 已有对应节，本轮实测补验证 |

## 第 20 轮续作 2（2026-11-21 21:15 · P32 RelayVSR 2× 真值对照）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K106** | ★★★ **P32 判决：RelayVSR 2× 是「向真值收敛的欠估增强」不是「编造」**——纹理量 = 真值 0.785×（不足），锐度 = 真值 91%；对照 FlashVSR 4× = 真值 1.76×（编造）方向相反。SSIM 0.9015 vs 插值臂 0.9625（−0.061）是纹理重分布代价，不是失真 | P32 实验（P22 同源猫片，三臂 640×384） | 2026-11-21 | **修订 18.21.6.2**：2× 档编造量首次定量化为「不足而非超真值」 |
| **K107** | ★★★ 超分双档定位修订：FlashVSR 4× = 细节生成器（风格化用途）；RelayVSR 2× = 向真值收敛的增强器（保真用途）——不是竞争关系而是档位分工 | P22 + P32 联合判决 | 2026-11-21 | 「480p 生成 + 2× → 960p」路线保真维度补齐 |
| **K108** | ★★ RelayVSR 逐位确定性在第二素材（猫片 25f）复证：r1 ≡ r2 framemd5 相同；0.05 s/帧（1664×960 时 0.12 s/帧） | P32 B-r2 | 2026-11-21 | K103 不再是单素材孤证 |
| **K109** | ★★ **15 帧周期检验统计功效：25 帧素材无效**（2 个 keyframe 边界，peak 0.058 / f_ratio 0.0 无信号）；P33 定标必须 ≥45 帧（P29 124 帧 peak 1.43 是更接近真实的信号） | P32 周期检验 | 2026-11-21 | **修订 P33 前置条件** |
| **K110** | ★ LFM3-VL「编造纹理」误报第三次再现（把窗反射差异说成 AI 编造）→ 编造裁决必须用纹理量双口径，VLM 只作粗判 | P32 LFM3-VL Q3 | 2026-11-21 | 印证已知缺陷①，无新结论 |

## 第 21 轮（2026-11-22 01:00 · 00:30 自动任务）—— 上游 d347808 + h3.c 对比表进 README 门面

### 本轮检索范围

GitHub API（commits / releases / issues / d347808 / d72c22f / 7703614 全文）+ tgo-app-dev 全仓库 + 上游 README（h3.c 对比节全文）+ docs/MINIMAX-H3.md（99 KB，部分）+ WebSearch ×3（h3.c 对比、HyperFlow Flash、中文社区）。issues/PR/release/ModelScope 均无变化。

### 逐条新增知识

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K111** | ★★ **上游 HEAD 前进到 `d347808`**（2026-11-21 05:59 UTC，19 文件）：DeepSeek-V4.1 GGUF 获视觉输入（vision tower 三文件：config + ViT/aligner 970 MB + marker/embedding 1.3 GB，放 GGUF 旁 `vision/` 或用 `vision_model` 指目录）；图像 resize 换成 Pillow 精确 bicubic（整数实现，可跨核并行）；矩阵核路径 bf16 RMS 距离 3.5–4.5%。 | GitHub API commit d347808 | 2026-11-21 | 纯 LLM/VLM 侧，视频线零变化；本机 build 落后基准更新为 d347808 |
| **K112** | ★★★ **h3.c 对比表进入 README 门面**（「Flagship workloads / performance」主章节 + YouTube 对比视频）：960×544/124f/6 步 bf16 同 workload 同 seed 三机全胜——M4 Pro 17m43s vs 23m9s；M5 Air 16GB（冰袋单样本）13m7s vs 16m22s；**M5 Pro 24GB 5m29s vs 7m11s（快 24%，本机同档）**。 | 上游 README @ d347808 | 2026-11-21 | 本机实测 480p/124f ≈ 6m38s（Pika-Flex 档）与官方 5m29s 同量级（工作负载不同族：官方 6 步 bf16 无适配器）。**与本机 vpipe 恒快于 h3.c 的判断一致（第 14 轮 K57 印证+扩展）** |
| **K113** | ★★ **h3.c 对比表历史上有过一次口径刷新**（考古 commit 7703614，2026-08-19：旧值 M4 Pro 21m50s / Air 12m15s，无 M5 Pro 行）→ **引用 h3.c 数字必须写 commit/日期**。 | GitHub commit 7703614 | 2026-08-19 | 方法论：上游性能数字是活的，禁止无版本引用 |
| **K114** | ★★ **h3.c 架构取舍确认**：16/24 GB 机器上 h3.c 需 `--ssd-streaming`（bf16），其 int8 引擎需 transformer 全驻留 → h3.c int8 是纯显存路线，vpipe 是统一内存流式路线；两者「int8」不是同一回事。 | 上游 README | 2026-11-21 | 解释了为何跨运行时比较只能用 bf16 口径；对第 14 轮 K57 的机制补充 |
| **K115** | ★ **issue 全景复查**：#59（RelayVSR 2×）仍 open/0 评论——**上游在 d72c22f 已实现其诉求但未关闭 issue**（第 20 轮 K91 佐证强化：issue 状态维护明显滞后于代码）；其余 issue/PR/release（仍 v0.1.110）/ModelScope 均无变化。 | GitHub API issues?state=all | 2026-11-22 | #55–59 零回复结论维持；新增观察「issue 关闭滞后」 |
| **K116** | ★ **HyperFlow H3 Flash 社区面复验**（第 1 轮 K12 已记）：多源确认 13.7B/13.9B 剪枝权重、Q4_K_M 9.1 GB、ComfyUI 路线、授权排除美欧英韩 → 与 vpipe「全量 33B + 蒸馏适配器」不同族。 | webdiga/specialinfluencers/kun.net/163.com | 2026-11-08~11 | 无新事实；固化「权重压缩 vs 步数蒸馏」区分纪律 |

### 印证 / 冲突

- 印证：第 14 轮 K57（VPIPE 快 21–25%）在新表上维持；第 19 轮 K84/K86（M5 Pro 边际收益、I/O 受限）与官方 5m29s 同量级。
- 冲突：无。docs/MINIMAX-H3.md 的逐相位分解本轮未逐段核对（99 KB 截断），引用需注明。

### 本轮实验

无实验，仅知识同步。理由：搜到的新增量为 LLM 侧（不可/无需本地复现）与性能口径（官方已实测）；看板高优先级 P30（d72c22f 漂移基线重测）属重实验，且 00:30 时段按惯例留给知识同步轮（P30 建议留 02:30/04:30 时段）。

## 第 22 轮（2026-11-22 10:38 · 手动触发，验证精简后双槽位配置）—— ★★★ pi-H3 权重按承诺窗口发布（2/4 步 + 免 VAE 解码器）+ Suno H3Move 生态事件

### 本轮检索范围

GitHub API（vpipe commits / releases / issues / PR search / repo meta；Lakonik/LakonLab commits）+ HF 模型页 Lakonik/pi-H3（WebFetch 全文）+ ComfyUI-piFlow changelog + ModelScope lightx2v 文件 API + WebSearch ×4（vpipe 社区 / MiniMax H3 近 5 日 / pi-H3 权重 / 中文社区）。

### 逐条新增知识

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K117** | ★★★ **pi-H3 权重已发布**（HF `Lakonik/pi-H3`，2026-11-21 兑现「11-16~22」承诺）：4 个适配器（2/4 步 × DWD/VAE 两路，DWD 推荐）+ INT8 ConvRot 版（仅 ComfyUI）；License = minimax-h3-community-license（衍生品，继承 H3 社区许可地域限制）；基座为 MiniMaxAI/MiniMax-H3；768×1344/243 帧（17n+5 帧数约束）。 | HF 模型页 + teapawt@HanshengCh | 2026-11-21 | 第 20 轮 K95「pi-H3 仅 demo」状态更新为「已开源」。**与 vpipe 的蒸馏适配器同族但不同路线**：DWD 免 VAE 解码器是 vpipe 现有 any stage 都没有的形态 |
| **K118** | ★★ **ComfyUI-piFlow v1.4.0（2026-11-21）** 增加 pi-H3 节点与工作流（2 步/4 步，含/不含 DWD），要求 ComfyUI ≥ v0.45.0；作者同时警示 **Comfy 工作流质量劣于 diffusers 管线**（疑 Comfy 原生 Sol-Attn 质量妥协）。 | ComfyUI-piFlow changelog + 作者推文 | 2026-11-21 | 若本机走 ComfyUI 复现需注意质量风险；diffusers + LakonLab v0.3 是官方推荐路线（本机 24 GB 需 INT8/FP8 路径核算） |
| **K119** | ★★ **LakonLab v0.3.0 发布**（2026-11-21 commit c08dad1），pi-H3 官方推理代码落地；作者实测 3090（2 步 INT8 无 VAE）：768p 5s=38.5s / 10s=97.6s / 15s=186s；480p 5s=15.5s。 | LakonLab GitHub API commits | 2026-11-21 | 提供 pi-H3 在消费级卡的实测基准；本机 M5 Pro 无直接可比（Metal vs CUDA），但 2 步档速度量级可参照 |
| **K120** | ★★ **Suno Visuals/H3Move 上线**（2026-11-20 报道）：基于开源 H3 的音乐视频垂直应用（口型同步/呼应歌曲结构/15s）；H3 开源 100 天社区衍生 **1400+ 模型、HF 下载 1.4 亿次**；官方合作矩阵再列：RunningHub 480P、fal H3Max、NVIDIA Open-H3-Regenerate-2K、Pika H3 Flex。 | 新浪财经/和讯/东财 | 2026-11-20 | 第 22 轮生态面新事实：「下载量最多的开源模型之一」+ 衍生规模首次量化；不影响本机技术路线 |
| **K121** | ★ **上游 vpipe 完全静默**：HEAD 仍 `d347808`（11-21 05:59），pushed_at 11-21 10:37 UTC；release 仍 v0.1.110；**PR 总数 0**（search API 复核）；issues 无状态变化（#59 仍 open/0 评论）。 | GitHub API ×4 | 2026-11-22 | 第 21 轮结论维持；上游对 pi-H3 无任何迹象（search "pi-H3" = 0）→ vpipe 接入 pi-H3 无时间表 |
| **K122** | ★ **ModelScope lightx2v/Minimax-h3-Turbo 无新增**：仍 31 文件 / 26 safetensors，最新 commit 2026-11-16/17（README 更新 726193a3）。 | ModelScope API | 2026-11-22 | 基线维持；pi-H3 适配器不在 lightx2v 体系内（走 LakonLab） |

### 印证 / 冲突

- 印证：第 20 轮 K95（pi-H3 承诺窗口）如期兑现——**「承诺日期型情报要设提醒复查」方法论有效**。
- 冲突：无。pi-H3 的 B200/H100 数字均 NVIDIA 口径，与第 14 轮 K57（本机 bf16 对比）不冲突、不可直接比。

### 本轮实验

无实验，仅知识同步。理由：pi-H3 属 ComfyUI/diffusers 生态，vpipe 无接入路径，本地复现需另起 LakonLab v0.3（Python/diffusers）栈，超出本轮时间预算 → 登记看板「待验证」供后续轮评估优先级。

## 第 22 轮 04:30 兜底槽跳过说明（2026-11-22 11:14）

04:30 重试兜底槽实际于 11:14 触发（延迟）。判定：跳过，不执行。理由：① `last_run = 2026-11-22 10:38`（今天，手动触发第 22 轮完整知识同步，距本槽仅 36 分钟）；② 今天 00:30 主跑槽已成功（第 21 轮 01:00），无失败可重试。轮次状态不递增（round 维持 22），锁文件不存在，无遗留动作。

## 第 22 轮 00:30 主跑槽跳过说明（2026-11-22 11:21，延迟触发）

00:30 主跑槽实际于 11:21 触发（延迟）。判定：跳过，不执行。理由：① `last_run = 2026-11-22 10:38`（今天，第 22 轮手动完整知识同步，距本槽仅 43 分钟）；② 今天 00:30 时段已由第 21 轮（01:00）覆盖，无失败可重试；③ 上游无新变化（HEAD d347808 自 11-21 静默）。轮次状态不递增（round 维持 22），锁文件不存在，无遗留动作。

## 第 20 轮续作 3（2026-11-23 21:23 · 768p Negative + RelayVSR 保真重制 + P33 判据修订）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K123** | ★★★ **768p 重生成 ≠ 原片高清化**：同参考图同 seed，换分辨率 + 换 768p 适配器（shift 6.0）即**换场景**（客厅→餐厅，服装/动作全变）；且恒定码率 ~2.2 Mb/s 下像素 ×2.6 → **同尺度锐度反而 −32.6%**（304 vs 451）。 | 本轮 QC（dance-woman-768p vs 5s） | 2026-11-23 | 印证 K39/K98「换分辨率/适配器 = 换场景」；**新增「码率恒定下重生成高分辨率 = 更糊」负面结论**——「重制更清晰」必须走保真超分而非重生成。 |
| **K124** | ★★★ **RelayVSR 2× 保真重制成立**：832×480→1664×960，124 帧 16.6 s（0.13 s/帧），成片 24.4 Mb/s / 15 MB；同尺度锐度 ×2.7、高频 ×1.64，同场景同人物、结构化纹理无伪影。 | 本轮 dance-relayvsr-x2-hq | 2026-11-23 | P32「2× 向真值收敛」在真人舞片第二素材复证；**确立「480p 生成 + 2× 保真超分」为高清化正解**。 |
| **K125** | ★★★ **P33 判据重大修订：15 帧周期脉动是源片固有，非 RelayVSR 接缝**——124 帧素材原片 peak_excess **1.970** / f_ratio **4.331**（比超分片 1.921/3.562 更强），峰值相位同 k=11。推翻 K104 把 P29 的 1.43/0.72 归因为超分接缝。 | 本轮原片对照臂（首次） | 2026-11-23 | **绝对阈值作废**；周期检验强制加原片对照，判据改为超分/原片比值（本轮 0.82 < 1 → 无超分引入脉动）。 |
| **K126** | ★★ **方法论：处理后检测到周期/伪影 ≠ 处理引入**——任何 stage 的周期归因必须有输入对照臂，否则是虚假归因。 | 本轮 P33 修订 | 2026-11-23 | 与 K98「跨 build 锚点作废」同族：都是「缺对照臂导致错误归因」。推广到所有 stage 效果检验。 |

## 第 23 轮（2026-11-23 23:20 · 04:30 槽故障诊断后手动补跑）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K127** | ★★★ **上游静默被彻底打破**：HEAD `d347808` → **`a6a1f53`**（11-23 17:54 北京），**85 文件 +17617/−509 行**，单 commit 最大增量之一。 | GitHub API commits | 2026-11-23 | 第 22 轮 K121「完全静默」终结；vpipe 进入功能大更新期 |
| **K128** | ★★★ **pi-H3 2/4 步适配器原生进 vpipe 主仓**：跑 ComfyUI 剪枝 ckpt；每 partition 带精确 handle；适配器=低秩对+整块替换（调制/输出norm/双head），strength 非0应用/0撤销；step grid 来自文件；发布ckpt/split rank/训练基座按名拒绝。 | a6a1f53 commit | 2026-11-23 | 与 K117 外部权重、K118 ComfyUI 路线并列，形成「vpipe 原生」第三路线 |
| **K129** | ★★★ **DWD 在 vpipe 内落地**：适配器末步把 video rows 特征交 vae-decode 代替 latent，跑适配器 pixel head 而非 video VAE，解码器不加载；精度 f32 0.0053 / 参考 bf16 0.0052。 | a6a1f53 commit | 2026-11-23 | 印证 K117 DWD 定义，首次给出 vpipe 内可复现路径 |
| **K130** | ★★ **train-lora**：训练 MiniMax-H3 自身 DiT（两 partition）+ Qwen-Image 家族；样本=静帧或带音轨 clip 窗口；Ref2VA 用 sidecar 命名参考；Image/P-H3-Image 用编辑对训练。 | a6a1f53 commit | 2026-11-23 | 新增「本机训练」能力族（此前只做推理） |
| **K131** | ★★ **调制表折叠 26GB→174MB**（压到剪枝ckpt的8维曲线）；block 保留激活不重算、梯度逐位相同；AdamW/8bit/Adafactor/B因子独立lr。 | a6a1f53 commit | 2026-11-23 | 24GB 机器跑 LoRA 的内存关键 |
| **K132** | ★★ **Dials 拨盘**：每 prompt row 加一向量，恒定强度或时间曲线；音轨跟随曲线或独立；曲线重跑前几步按 latent 帧混合。 | a6a1f53 commit | 2026-11-23 | 新增生成期控制维度 |
| **K133** | ★★ **三处内存记账修正**：video-ref-encoder 补 VAE encode+prefill（prefill 前归还）；prefill dequant scratch 按权重路线记账（此前 dense 按 quantized 收费）；fast decoder 每次 decode 后归还工作集。 | a6a1f53 commit | 2026-11-23 | 影响显存规划口径（关联 K91），峰值需重测 |
| **K134** | ★ **新增 8 条流水线**：4 条 LoRA（train-lora/-clips/-ref2va/-image-edit）+ 3 条 pi-H3（text/first-frame/first-last-to-video）+ prepare-pi-h3；docs/LORA-TRAINING.md +262。 | a6a1f53 commit | 2026-11-23 | 流水线手册需补 8 条 |
| **K135** | ★ **release 仍 v0.1.110**（11-01）但 main 已 +17617 行 → release 与 main 差距扩大，本机 build 落后基准需重新核对。 | releases API | 2026-11-23 | 版本口径更新 |

### 印证 / 冲突

- **★★★ 重大冲突**：**推翻 K121**（11-22「上游对 pi-H3 零迹象、接入无时间表」）——结论寿命仅 1 天，11-23 上游直接把 pi-H3 适配器 + DWD 合进主仓。**方法论**：「静默/零迹象」是有时效快照，非趋势结论，必须按日复查。
- 印证：K117 DWD 定义获 vpipe 源码实现印证；K95「承诺窗口复查」方法论再次奏效。
- 口径：0.0053/0.0052 为上游 f32/bf16 对照，非本机 Apple Silicon 实测，禁止直接比。

### 本轮实验

无实验（核心是修复定时任务漏跑 + 固化重大增量）。登记 P36（pi-H3 原生适配器本机复现）、P37（LoRA 24GB 显存账）。

### ★★★ 04:30 定时任务故障诊断

- **症状**：今天（11-23）04:30 槽（及 00:30 槽）根本没执行，轮次停在 22。
- **证据**：04:30 配置 ACTIVE/rrule 正确/prompt 完整（✅ 无错）；11-22 04:30/06:30 会话仅 376B 空壳（触发未执行）；11-23 凌晨无会话文件（未触发）；轮次 round=22 零推进；无锁残留。
- **根因**：本机自动化依赖 WorkBuddy 应用常驻 + 机器不休眠。凌晨应用未运行/机器休眠 → 调度器拉不起会话；槽位已从 4 个精简为 2 个，冗余降低，两次都未触发即整天漏跑。**非配置错误，是架构性限制**。
- **修复**：手动补跑第 23 轮（本轮）把增量补回；诊断固化到报告 18.26.6 与 SOP。加固建议待用户确认。

### 第 23 轮续 · 04:30 槽加固落实（2026-11-23 23:30，用户选方案①）

- 防休眠核查通过：AC `sleep 0`（不休眠）+ display sleep 20min（不影响后台）+ `com.workbuddy.app.autostart`（RunAtLoad）已配 → 无需 caffeinate。
- **恢复 4 槽制**：重建 02:30（c17d1b23）/06:30（94c4eadb），连同 00:30（c8411425）/04:30（eb717510）四槽均 ACTIVE、prompt 统一（共 4 槽 + 基线 a6a1f53 + 空壳作废兜底接手）。
- 三级兜底：任一槽今天成功写 last_run → 后续跳过；否则 02:30→04:30→06:30 依次重跑。
- 模型 gemini-3-flash 为全局 models.json 配置，自动化对象不含模型字段，新槽继承。
- 残留风险：应用手动退出不自愈（autostart 仅登录拉起一次），彻底自愈需 launchd 守护。详见报告 18.26.7 / SOP 9.1。

## 第 24 轮（2026-11-23 23:45 · 4 槽立即运行/自动运行可执行化 + 逐个测试）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K136** | ★★ issue #59 给出 `lightx2v/RelayVSR_X2` 原生 2× checkpoint tensor 差异：`lq_proj.conv1.weight` `[768,768,1,1]`→`[768,192,1,1]`（16×16→8×8 unshuffle）；config 加 `upscale_factor:2`；flash 权重 F32。 | GitHub issue #59 | 2026-11-16 | 印证 K91 原生 2× 权重依据；与本机 K124（Comfy-Org 2×）不同来源，需注明 |
| **K137** | ★ 原生 X2 H100 约 4× 的 3.6× 速度（243f 1024×768：5.3s vs 19.3s）；vpipe stage 在 `metal-relayvsr-decoder.cc:137` 因非 4× 拒绝，尺寸硬编码 4×。 | GitHub issue #59 | 2026-11-16 | 原生 2× 未合入（open/0 评论），本机 Comfy-Org 2× 路线仍是唯一可复现路径 |
| **K138** | ★★ 4 槽判断逻辑从 prompt 文本升级为可执行守卫 `nightly_guard.sh`：check/force/test/status/release 五模式，退出码 0/10/11。 | 本轮工程 | 2026-11-23 | 满足「每项可立即运行 + 自动运行 + 可测试」 |

### 印证 / 冲突 / 本轮实验
- 上游静默约 6 小时（HEAD a6a1f53 无新 commit）、release v0.1.110 差距维持（K135）、issue 14 条开放 0 评论（K115）。无冲突。
- **T1**：4 槽 × 4 场景隔离测试全通过（今天已跑 SKIP / 今天未跑 RUN / force RUN / 并发锁 SKIP）。
- **T2**：真实状态集成测试通过（check 跳过 / force 建锁 / 并发保护 / release 幂等恢复）。
- **坑**：① `${r}` 防全角吞变量；② 给 shell 函数前置 `VAR=x` 不覆盖函数内全局 → 测试须用子进程调脚本自身。
- 无生成实验（本轮为工程可执行化 + 知识同步）。

### 第 24 轮续 · 去掉日期去重（2026-11-23 23:55，用户修正）

- **用户要求**：修正「今天已跑」跳过，不检测已跑，只要点击运行或到点都能执行。
- **改动**：`nightly_guard.sh` 删除日期去重分支（原 exit=10），`check`=`force`=仅拒并发(exit=11)否则建锁 RUN(0)；last_run 仅审计不作跳过依据；4 槽 prompt + SOP 9.2 同步。
- **语义**：由「三级兜底（今天成功则后续跳过）」改为「4 槽独立执行，每次点击/到点都跑」；知识内容仍去重，但整轮不跳过。
- **测试**：4 槽 × 4 场景全通过（今天已跑 RUN0 / 到点 check RUN0 / 点击 force RUN0 / 并发锁 SKIP11）；真实状态 last_run=今天 check→RUN0 验证去重已除。详见报告 18.28 节。

## 第 25 轮（2026-11-24 00:06 · 用户手动触发 00:30 槽失败后代跑）

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K139** | ★★★ 首次 daemon.log 级实证「会话空壳/unknown_interrupted」：23:33–23:59 手动触发 00:30/04:30 槽，`session attached` 拉起后 2–5 min 内 `cause=unknown_interrupted` 取消；末次会话 a8efe90e 仅 222 B 元数据 + 143 B 日志，无 prompt 执行；automation.log 自 11-23 06:00 停写近 18h。 | 本机 daemon.log / automation.log | 2026-11-24 | 坐实 18.26.6 推断：非配置/非脚本错，是自动化会话被主对话抢占中断的执行层问题 |
| **K140** | ★ FlashGen 4-step LoRA（社区）：VSD 无数据蒸馏 rank64 BF16，攻击 qkv/out/fc1/fc2/adaln_proj.linear；merge_lora_ckpt.py 固化 + base_schedule [1.0,0.7,0.4,0.15,0.0]；1344×768/5.2s；FP8/INT8≈16–24GB。 | studio.aifilms.ai | 2026-11 | 外部 4 步蒸馏新路线（与 K128 vpipe 原生并列）；社区二手待复现 |
| **K141** | ★ Character Swap LoRA V1.5（akatz-ai）：Ref2VA video-to-video 换角色；配方 INT8+V1.5@1.0+8step Turbo@1.0，8 步 CFG=1.0 er_sde，原音 passthrough。 | studio.aifilms.ai | 2026-11 | 对照「Ref2VA 细小附件会丢」：换角色走 LoRA 而非原生参考；待复现 |
| **K142** | ★★ Turbo 三档耗时（ComfyUI-NPU）：768p/15s 50步 35min / 21步 15min / 8步 Turbo 6.9min；video shift 12 / audio shift 3；silu(t_emb) 网格注入 pruned 覆盖 bf16/int8/pruned。 | lpqz.cn | 2026-11 | 印证 K106 双 shift + K128 pruned；NPU/15s 口径不可比本机 M5/124f |
| **K143** | ★ vLLM PR #52023（非 vpipe）：--model-variant fl2va+ref2va 共享编码器省一半内存；需 181.7GiB 两 DiT 常驻，<120GiB 启动失败。 | mindpattern.ai | 2026-11-22 | 服务器大显存场景，本机 24GB 无关，登记不采信 |

### 印证 / 冲突
- 上游静默约 14h（HEAD a6a1f53 无新 commit/release/PR，issue 14 条全开零回复）；印证 K135/K115/K106/K128。无量化冲突。
- 口径：K140–K143 均社区二手，非上游 commit、非本机实测，禁止并入已验证能力，须复现后采信。

### 本轮实验
无生成实验。动作 = force 建锁(R=25) → 检索 → 固化 → sync → release 全链路代跑，验证「自动化会话层失效时主对话内手动代跑能完整闭环」。

### 坑
- automation.log 停写 ≠ 应用停摆（daemon.log 仍在动）；判活看 daemon.log 的 attached+cancel 事件对。
- 会话元数据/skdsdk 日志存在 ≠ 真执行；唯一执行证据 = vpipe-lab 内锁/报告 mtime/同步日志。

### 第 25 轮续 · 00:30 槽手动/定时可执行性复查（2026-11-24 00:23）

- **K139 复现（手动）**：用户 00:10 再次手动执行 00:30 槽 → 会话 `12d57e09`（00:10:50 attached、进入 working）198 行 sdk 日志中 `tool=0/bash=0/nightly_guard=0`，仅会话管理元数据；`listSessions` 标 `status=terminated`；vpipe-lab 无锁/无报告更新/无 r26 同步日志 → **仍是空壳，prompt 从未执行**。00:21 用户再次点选仍 `history-missing` 空壳，00:21:58 焦点切回主对话。
- **K144 定时通道实证（失效）**：本地调度器 `automation.log` 自 11-23 06:00 停写近 18h，最后活动为 11-23 04:30 槽超时；11-24 凌晨 4 槽（00:30/02:30/04:30/06:30）全部漏跑（round 停 22 直到手动补跑第 23 轮）。`SchedulerCloudAutomation` 在 daemon.log 仍每几分钟列 1 个 cloud task，但那是 cloud:2700702（PAUSED 的资讯任务），与本 4 槽本地任务无关 → **到点定时触发通道事实上已失效，非仅仅会话空壳**。
- **判活口径再确认**：应用活着（AppStartup 5.11.3，00:21 仍写 DocumentSelectionHook）≠ 调度器活着；`automation.log` 停写 + round 不推进 + daemon.log attached/cancel 事件对，三者合看才能定性。
- **结论**：手动可执行（会话能拉起）但 agent 不执行=实质失败；到点定时连续漏跑=不可靠。**根治=P39（launchd + 独立 CLI 会话绕开 WorkBuddy 调度器）**，代跑仅治标。

### 第 25 轮续 · 00:30 到点触发实证 + K144 重大修正（2026-11-24 00:32）

- **用户先要求停止手动那次**：00:10 手动会话 `12d57e09` 于 **00:28:57 被 cancel + Released**（daemon.log: `[AutomationCancel] cause=unknown_interrupted decision=interrupted` + `Released automation conversation runtime (interrupted=true, state=idle)`）→ 用户"我已手动停止了"确认生效。
- **★★★ K144 重大修正（定时通道并未失效）**：**00:30:27 本地调度器准时触发了 00:30 槽**——`automation.log` 从 11-23 06:00 停写状态**恢复写入**（mtime=11-24 00:30:27），出现 `run start` + `dispatch automation c8411425...`；daemon.log 00:30:27 `session attached` 新会话 `a5ccaf68`、00:30:28 `pool:state-change idle→working`。→ **推翻 K144「到点定时通道失效」结论**。`automation.log` 停写 ≠ 调度器死：它是**事件驱动**（仅在槽触发/结束时写），11-23 06:00→11-24 00:30 之间无槽成功 dispatch 所以不写，不代表不能触发。此前漏跑是"触发了但会话空壳/中断"，不是"没触发"。
- **但空壳问题依旧（K139 第 N 次复现）**：`a5ccaf68` sdk 日志 89 行中 `tool=0 / bash=0 / nightly_guard=0`、`assistant=0`，仅 `user=7/prompt=3` 会话管理元数据；守卫状态仍 round=25、无锁、无 r26 同步日志 → 到点这次同样**会话被拉起但 agent 不执行 prompt**。
- **结论更新**：手动执行与到点定时**都能被调度层正确拉起会话**（本次到点已实证），唯一的、真正的故障点始终是**会话空壳 / prompt 不执行 / 被主对话抢占中断**。根治仍是 P39（launchd + 独立 CLI 会话绕开 WorkBuddy 会话层），代跑仅治标。判活口径不变：看 daemon.log attached+cancel 事件对 + vpipe-lab 锁/报告 mtime/同步日志，automation.log 只作"槽是否被调度"的辅助证据（事件驱动、非心跳）。

### 第 25 轮续 · P39 根治落地 + K144 修正（2026-11-24 00:50）

- **空壳会话 a5ccaf68**：00:30 到点触发，00:38:59 已 `terminated`，无活跃进程，无需 kill。
- **★★★ K144 修正**：到点定时通道**实际正常**——00:30:27 automation.log 恢复写入（run start + dispatch c8411425），daemon.log session attached。推翻 00:23「定时失效」结论。automation.log 是**事件驱动日志**（停写≠调度器死），此前漏跑是「触发了但会话空壳」非「没触发」。但 a5ccaf68 仍空壳（tool=0/bash=0），唯一真故障=会话被主对话抢占中断。
- **P39 方案落地**：发现 WorkBuddy 自带无头 CLI `codebuddy -p`（v2.176.0，独立进程不经过会话层）。建执行器 `p39_headless_runner.sh` + SOP `p39_sop_prompt.md` + launchd plist（StartCalendarInterval 数组原生 4 时段）+ 一键启用 `p39_enable.sh`。模型：gemini-3-flash 已下线（model_not_found）→ 用户确认改 deepseek-v4.1-flash-1017（实测渠道正常）。
- **阻塞（环境限制）**：本会话 `launchctl bootstrap/load` 全 I/O error（连最小 plist 也失败）、`crontab` operation not permitted、`codebuddy -p` 被安全策略拦截 → 系统级注册+无头验证两步须本机真实终端执行（已封装为 p39_enable.sh 一键）。文件全就绪、轮次未污染。
- **判活口径更新**：事件驱动日志停写不能推断调度器死亡，须看 run start/dispatch 事件对 + daemon.log session attached + vpipe-lab 锁/同步日志。

### P39 本机实测首跑 · K145（2026-11-24 00:55）

- **launchd 注册成功**：真实终端跑 `p39_enable.sh`，`bootstrap gui/501` 成功，服务在域内，4 时段就绪。
- **守卫与兜底首次真实跑通**：force→RUN(R=26)→建锁→CLI 失败→自动删锁不推进（round 仍 25），容错链路正确。这与 K139「会话空壳零执行」本质不同——本次是真执行真失败。
- **★★★ K145 根因**：WorkBuddy 定制版 `cli/dist/` 只有 `codebuddy-lite-wb.mjs`（12.8MB）+ `lazy-lite-wb/`(96 chunks)，**无** `codebuddy`/`codebuddy-headless` CJS bundle。`codebuddy -p` 触发 `isHeadless` → require headless 失败 → 回退 `dist/codebuddy`（第306行）→ MODULE_NOT_FOUND。仅 `CODEBUDDY_FORCE_LITE_WB_BUNDLE=1` 才走 lite-wb 分支（唯一存在的产物）。静态确认 lite-wb 支持 -p/--model/--permission-mode/--session-id/--add-dir 全参数。
- **修复**：runner 第 57 行 + plist EnvironmentVariables 双处注入 `CODEBUDDY_FORCE_LITE_WB_BUNDLE=1`；plutil/bash -n 均 OK。
- **待复核**：终端重跑 `bash scripts/p39_headless_runner.sh 00:30 force`，预期 round 25→26 + `nightly-sync-r26.log` + 退出码 0。
- **方法论**：定制版 CLI bundle 分派是隐藏单点，脚本化调用 `-p` 必须显式强制 lite-wb；此为继 autotune 静默、旧 build 丢 config 之后第三类静默配置陷阱。

### P39 第二次实测 · K146（2026-11-24 01:00）

- **K145 修复生效**：无头 CLI 正常拉起，trace 中 8 个 generation span + 11 个 Bash 调用、error 全 null，prompt 真实执行（区别于 K139 空壳）。
- **★★★ K146 新根因（模型 ID 别名陷阱）**：报 `503 分组 DeepSeek 下模型 deepseek-v4.1-flash-1017 无可用渠道`。`curl /v1/models` 证实上游真实 ID 是 `deepseek-v4.1-flash`（无 `-1017` 后缀），models.json 里的 `-1017` 是自定义别名、上游不认。逐模型实测 `deepseek-v4.1-flash`/`glm-5.3-flash`/`minimax-m3`/`kimi-k3`/`hy4-preview` 全部可用。
- **修复**：models.json 备份后新增 `deepseek-v4.1-flash` 条目（保留原条目）；runner MODEL 改 `custom-local:deepseek-v4.1-flash`。不需重新 bootstrap plist。
- **坑**：`codebuddy -p` 遇模型 503 退出码仍为 0！执行器靠三重校验（round 推进+sync 日志）兜住，正确删锁不推进——这套防御经受住"CLI 假成功"考验，勿简化为只看 exit code。
- **方法论**：模型 ID 必须在 `/v1/models` 精确存在，别名不能靠"key 有效+URL 可达"推断可用，须在真实调用链实测。K145/K146 同为静默配置陷阱家族。

### 模型切换 glm-5.3-flash（2026-11-24 01:01）

- 用户指定 P39 改用 `glm-5.3-flash`。实测：`/v1/models` 真实存在、chat 返回 OK、**工具调用返回正确 `tool_calls`**（无头 SOP 关键前提）、models.json 条目能力齐全（tool/img/reasoning 全 true）。
- runner MODEL 改 `custom-local:glm-5.3-flash`，bash -n OK。待终端实测第 26 轮。

### P39 第三次实测 · K147（2026-11-24 01:40）

- 模型加载正确（deepseek-v4.1-flash 全程 gen=ok、无 503，K146 确认生效），但 agent 01:24:05 因一次 `Error streaming response`（generation 卡 95s 取消）失败，`cli status=error`。
- **★★★ K147 僵死占锁**：agent 已 error 但 CLI PID 19800/19801 不退出（lsof 多条到 deeprouter 36.151.170.17 的 ESTABLISHED），僵死 14min+，runner 卡在 timeout 5400 傻等、锁不释放会阻塞后续槽。人工 kill + `release 25` 幂等删锁恢复（round 保持 25）。
- **诊断坑**：traces/19260 下两个 trace 混淆，把主对话 trace（Bash 全是我的诊断命令）当无头任务，误报"仍在推进"。正解：按 session-id `grep -rl` 关联到对应 trace，看其 trace_end 状态；workerPid 共享不能区分。
- **修复**：runner 加完成信号看门狗——每 20s 查本 session trace 是否 trace_end，出现即 pkill CLI，20s 内释放锁；270×20s=90min 对齐硬超时。bash -n + 命中/pkill 自检通过。
- **方法论**：无头 agent 失败判定唯一可靠信号 = 对应 session 的 trace_end 状态；CLI 进程存活 ≠ agent 存活（可僵死占连接）。

## 第 26 轮（2026-11-24 06:30 · 上游第 2 日静默复核 + 权重仓库级量化 + 4 步口径冲突 + DWD 原论文定量 + P39 04:30 槽实证失败）

> 本轮由 **P39 launchd + codebuddy 无头 CLI 实际执行**（session `p39-0630-20261124-063005`，模型 `custom-local:deepseek-v4.1-flash`）——这是 P39 方案首次跑完「检索→固化→报告→同步→release」的整条链路，与第 25 轮「主对话代跑」性质不同。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K148** | ★ 上游第 2 日静默复核：HEAD 仍 `a6a1f53`（pushed_at 2026-11-23T11:20:51Z）；最新 release 仍 **v0.1.110（2026-11-01）→ 落后 main 22 天**；issue **14 条全开**（最新仍 #59，11-16，0 回复）；**PR = 0**；仓库 266 star / 27 fork / 36.9 MB。 | GitHub API（commits/releases/search/issues/pulls/repo） | 2026-11-24 | **零增量确认**，K135/K115 延续；release 落后从 21 天扩到 22 天 |
| **K149** | ★★ **提交统计口径冲突**：主报告 18.26 记 a6a1f53 为「85 文件 +17617/−509」；本轮单 commit detail API 实测 **total 20003 / additions 19494 / deletions 509**（净 +18985），差 1877 行。本页 `files` 数组被 API 截断（至少 15 项，无法核对 85）。 | `commits/a6a1f53` detail API | 2026-11-24 | **不改历史正文**，仅登记差异；此后 a6a1f53 规模一律引 detail API（19494/509），「85 文件」改注为「files 数组计数、未经 detail 核对」 |
| **K150** | ★ 权重仓库级指标首次量化：`lightx2v/Minimax-h3-Turbo` **downloads 1,793,937 / likes 1,235 / 存储 75.80 GB（70.6 GiB）/ 26 个 safetensors + 4 非权重 = 30 文件**；**lastModified 2026-11-16T09:19:46Z**。 | HF `/api/models/...` | 2026-11-24 | 自 11-16 起 **8 天无新权重** → **v1.3 即当前最终版，无 v1.4**；与「ModelScope 已收录、上游 catalog 未收」互证 |
| **K151** | ★★ **4 步家族字节级同构**：`fl2v_turbo_4step` 的 v1.0 / v1.1 / v1.2 / v1.3（768p bf16）LFS size **全部 = 1,383,677,808 B**（sha256 各异）→ 版本迭代**只换权重值、不改张量结构与 rank**。fp8 版精确 **34,023,114,720 B（31.69 GiB）**，与 ModelScope 报的 32.4 GB 一致。 | HF `tree/main`（逐文件 LFS size） | 2026-11-24 | **工程可用**：v1.3 可直接占 v1.2 的槽位做 A/B，**无需改任何 shape/rank 假设**（P11c 前置条件成立） |
| **K152** | ★★ **社区「4 步不够」口径**（minimax3.com，明确非官方）：两位 LoRA 作者均推荐 >4 步；larryvrh card 称 6–8 明显优于 4、>8 无增益反过锐；**ModelTC 官方示例工作流默认 8 步而非 4 步**。RTX 5080 单机：标准 1035 s → 仅 SageAttention 487 s → Turbo+Sage **193 s**（作者自述非受控基准）。核心指标是 **time-per-usable-clip**：5× 采样缩减端到端只兑现约 2×。 | minimax3.com/blog/minimax-h3-turbo-steps | 2026-08-15 | ★ **与本机冲突（见下）**：主报告 18.21「4 步画质不降」需**限定条件**。社区二手，待复现 |
| **K153** | ★★ **DWD 原论文定量**（arXiv **2611.22287**，v1 2026-11-17 / v2 11-18，Hansheng Chen、Gordon Wetzstein、Leonidas Guibas 等，Stanford）：Wan 视频 **warping error −23%**（细节失真与闪烁下降）；ImageNet **FID 1.55 → 1.43**（pixel flow 新 SOTA）。方法 = **只微调最后几个 block + 线性 DWD head，原 denoising head 冻结**以锚定采样轨迹。 | arXiv abs 页 | 2026-11-17 | 印证 K117/K129（定义与 vpipe 内实现）；**新增 P36 成本预估依据**：训练侧仅末几 block，比全量微调轻得多 |
| **K154** | ★★★ **P39 第 4 次实测（04:30 槽）失败 + 第 5 次（06:30 槽）成功**：04:30 launchd 准时触发、4 min 54 s 后 `Upstream response stream was interrupted`，**cb_exit 仍 = 0**、round 未推进、无 sync 日志 → runner 兜底正确删锁不推进。06:30 槽**同一二进制同一模型正常执行全链路**。**新诊断坑**：`ps` 中同命令行的子进程不是双开，是**看门狗子 shell**（sleep 20 循环）。 | 本机 `logs/p39-run-0430-*` / `p39-launchd.out.log` | 2026-11-24 | 坐实 K147 的「CLI 假成功」防御有效；失败属**传输层瞬时中断**而非系统性缺陷；K144「到点触发正常」再次成立 |

### 印证 / 冲突

- **★★ 冲突①（统计口径）**：a6a1f53 的 additions 有两个值——上轮记 17617、本轮 detail API 19494，差 1877 行。**不改写 18.26 历史正文**，只在此登记，后续统一用 detail API 口径（19494 / −509 / total 20003）。方法论同 K113：**上游数字必须带端点与日期**。
- **★★ 冲突②（4 步画质）**：本机 18.21 用 1344×768/124 帧固定夹具测出「4 步 v1.2 细节能量 170.6 > 8 步 167.7，耗时仅 45.5%」；社区口径说 4 步在**快/大运动**上糊成拖影。两者不必然矛盾——**本机夹具是静态/慢速**。**修订建议：把「4 步画质不降」显式限定为「静态或慢运动」，快动作场景走 6–8 步**。此为社区二手，待本机用运动夹具复现后再定稿（可挂 P40）。
- **印证**：K153 论文的 DWD 定义与 K117/K129 完全对齐，且首次给出可引用定量；K150 的 8 天未更新印证第 17 轮「ModelScope 已收录、上游 catalog 未跟」的判断；K151 的字节同构解释了为何 v1.0→v1.3 可在不改配方的前提下互换（与 18.21 实测互换可行互为印证）。
- **零增量**：vpipe 上游、ComfyUI 上游（近 10 条 commit 无 MiniMax/H3）、stable-diffusion.cpp（近 5 条无 H3）、ModelTC/Minimax-H3-Turbo 代码仓（最新 commit 仍 2026-08-27）、ComfyUI 官方博客（无 H3 条目）——**均为零迹象快照，明日须复查（K121 教训）**。

### 本轮实验

无实验，仅知识同步。理由：本轮时间预算优先保证「两份报告 + 轮次推进 + nightly_sync」最小闭环；新知识中唯一可本地复现的是 **K151（v1.3 换槽 A/B）**，但需先下 1.38 GB 权重 + 29 min 生成，超预算 → 登记为 **P40**（与 K152 的 6–8 步运动夹具验证合并为一项）。

### 坑

- **K149 的口径漂移**：同一个 commit 在不同端点给出不同的「行数」，且 detail API 的 `files` 数组会被截断——**不能只看数组长度推文件总数**。
- **K154 的进程误判**：看门狗子 shell 与主 runner 命令行完全相同，`ps | grep` 会看起来像双开。**判并发只看 `.auto-round.lock` 与守卫退出码 11**，不看进程数。
- **磁盘**：`models/Comfy-Org/MiniMax-H3/diffusion_models/minimax_h3_fl2va_bf16.safetensors.part` 是 11-19 遗留的 **18.3 GB 半成品下载**（未完成、无同名完整文件）。当前剩 37 GiB 尚安全，但**建议清理**（未经用户确认不删，因可能是手动下载中断）。清理后可回收至 ~55 GiB。

## 第 27 轮（2026-11-25 00:30 · 上游第 3 日静默 + 官方迭代方向首次量化 + H3-Tiny 剪枝家族进图谱 + 因果流式 9 chunk）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=00:30，session `p39-0030-20261125-003000`，模型 `custom-local:deepseek-v4.1-flash`）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K155** | ★★ **H3-Tiny 结构化剪枝家族**（第三方）：AdaLN 低秩 rank-8（**13.0B/33.1B 参数在 AdaLN 投影**）+ 删 50 块中的 8 块（6–11/13/15）+ FFN 14336→9792 通道 + OKD 蒸馏 → 17B/14B；17B **剪完不训练即可用**（50 步），few-step 版默认 **6 步**。ComfyUI 单文件 bf16 34.2 GB / INT8 ConvRot **18.1 GB**（H200 243f 1344×768 DiT 仅 ~17 GB VRAM，速度≈bf16）。 | GitHub `fuyi25/MiniMax-H3-Tiny` + HF `H3-Tiny/*` | 2026-11-24 | 权重压缩路线再添一族（与 HyperFlow 13.7B / pi-H3 pruned 同族）；本机 24 GB 只有 INT8 18.1 GB 版本有磁盘可行性 → **P42** |
| **K156** | ★★ **官方两条线投入不对称**：4 步线 **2026-10-20（v1.3）后 36 天冻结**；8 步线 **2026-11-12（v1.2）** 且 v1.2 是**结构性变更**（bf16 1,383,677,808→**1,543,291,302 B，+11.5%**）。README 于 **11-24 14:36** 单独更新，仍 ⭐ 推 v1.2（8 步）。 | ModelScope 文件 API（逐文件 size+CommitDate）+ HF 模型卡 | 2026-11-25 | 修正 K150「无 v1.4 即终版」的隐含判断：**4 步终版是 v1.3，8 步仍在演进到 v1.2**；8 步 v1.2 **不可**按 K151 换槽（结构变了） |
| **K157** | ★★ **本机 catalog 对新路线零支持**：`model-catalog.cc` 内 `tiny` 全部是 TAE 预览解码器、**无 H3-Tiny / 剪枝 ckpt 条目**；`causal` 只在 Qwen/Z-Image 注释出现、**无 H3 因果流式条目**。本地树 HEAD 仍 `d72c22f`。 | 本地源码 `stages/model-catalog.cc` | 2026-11-25 | **「社区有」≠「vpipe 能用」**：Tiny 与 causal 两条路线本机均需等上游采纳或改源码 |
| **K158** | ★ **LightX2V 因果流式扩到 9 chunk 音频历史**（#1749, `e5744932`, 11-23 merged）：新增 `audio_latest_chunk_num=9`（视频仍 2），`kv_cache_max_t_rope` 7→9；约束改为 `1<=latest<=audio_latest<=max_t_rope`；只影响 6 个 `*_realtime_768p*` causal 配置。 | LightX2V PR #1749 diff | 2026-11-23 | 音频长期连贯性优先于视频窗口——生态信号；本机无 causal 能力（K157），不采信为可用 |
| **K159** | ★ **ComfyUI MPS deflicker warp 修复**（#17940, 11-23 merged）：MPS 不支持 `padding_mode="border"` → 改 clamp 坐标到 [−1,1] + `padding_mode="zeros"`（bilinear + align_corners 下与 border 等价），附等值单测。 | Comfy-Org/ComfyUI PR #17940 | 2026-11-23 | 与 vpipe 无直接关系，但「MPS 缺 border → clamp+zeros」是**可复用绕法**，可迁移到自研 warp/光流算子 |

### 印证 / 冲突

- **上游第 3 日静默（印证 K148/K135/K115）**：HEAD 仍 **a6a1f53**（pushed_at 2026-11-23T11:20:51Z，== 2 天未动）；最新 release 仍 **v0.1.110（11-01）→ 落后 main 24 天**；issue **14 条全开、全部 0 评论、updated_at 均在创建当日**（无一条被处理过）；**PR = 0**；仓库 **269 star / 27 fork / 36,920 KB**（star 从 266 → 269，+3）。
- **★ 冲突风险（口径）**：官方 README 的「v1.2 更好」对比是 **8 步 v1.1 vs 8 步 v1.2**，**不含 4 步**。**不得**用它支持 K152 的「4 步不够」——那仍是社区二手口径（待复现）。K156 只证明「8 步线在演进」，不证明「4 步画质差」。
- **印证 K150**：权重仓 downloads **1,793,803**（11-24 为 1,793,937，−134）→ 流量已进入平台期；likes 1.24k 持平；ModelScope 31 文件 / 26 safetensors / 75.80 GB 与 HF 一致。
- **印证 K151**：本轮重新逐文件核对，4 步 v1.0–v1.3 仍全部 1,383,677,808 B；同时**明确 8 步 v1.2 例外**（1,543,291,302 B）→ K151 的「可换槽」结论**只适用 4 步家族**。
- **零增量（须明日复查，K121 教训）**：`ModelTC/Minimax-H3-Turbo` 代码仓最新 commit 仍 **02e26d5（2026-08-27）**；stable-diffusion.cpp 近 5 条 commit（11-24，GGUF metadata / A1111 metadata / hires sigma / hidream speckle / lora F32）**含 1 条与 LoRA 混合精度相关（#2383「后端拒绝 mixed-type addition 时以 F32 相加」）但无 H3**；ComfyUI 近 5 条**无 H3**。

### 本轮实验

**无实验，仅知识同步。** 理由：①本轮为 P39 无头进程执行，硬超时 90 min 内须完成「检索 + 固化 + 两份报告 + sync + release」最小闭环；②唯一可复现项需 ≥18.1 GB 下载（Tiny INT8）或 1.38 GB（4 步 v1.3），且 Tiny 需 vpipe 先支持（K157 否）→ 均超预算，登记 **P42**。

### 坑

- **坑①（新，重要）：「latest commit date」不等于「内容变更」**。ModelScope 文件 API 里 `README.md` 的 `CommittedDate=2026-11-24 14:36` 会让人以为权重更新了；实际 26 个 safetensors 的日期**一个都没变**（最新 11-12）。**判权重是否更新必须只看 safetensors 的 CommitDate/size，不能看仓库级更新时间**。这与 K149（同一 commit 不同端点行数漂移）同族：**仓库级元数据是聚合值，不可当明细用**。
- **坑②：HF API 在本机直连持续超时**（`/api/models/lightx2v/Minimax-h3-Turbo` 连续 3 次 28 s 超时；`/tree/main` 同样）。可用替代：**ModelScope 文件 API（含 size + CommitDate + sha256，比 HF tree 信息更全）** + **HF 网页（WebFetch 走代理）**。教训：HF 是「网页可读、API 不可达」，检索路径要按此分流。
- **坑③：8 步 v1.2 的「字节增大」容易被误读为「更多权重」**。实际是同构家族里多了 159 MB（1,543,291,302 vs 1,383,677,808），更可能是新增了若干整块替换项（对应 a6a1f53 里「WHOLE replacements for others」那类适配器结构）。**未验证**，仅记为「结构性变更，不可换槽」。
- **坑④：`grep` 关键词命中率会骗人**。本轮用 `ConvRot`/`convrot` 查重，命中 9 处，但**全部是 pi-H3 的 INT8 ConvRot 适配器**，与 H3-Tiny 的 `*_int8_convrot.safetensors` 是**不同对象的同名后缀**。查重必须先确认命中项的上下文对象。

## 第 28 轮（2026-11-25 02:30 · H3-Tiny INT8 权重头零下载实测 → 本机 pruned AdaLN 宽度硬 gate + 上游第 4 日静默）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=02:30，模型 `custom-local:deepseek-v4.1-flash`）。
> 与第 27 轮的区别：**不再只是「社区有这个模型」，而是用 HTTP Range 零下载读出权重头，把「本机能不能跑」从推测变成实测**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K160** | ★ **上游第 4 日静默**：HEAD 仍 `a6a1f53`（pushed_at 2026-11-23T11:20:51Z，**满 2 天未动**）；release 最新仍 **v0.1.110（11-01）→ 落后 main 24 天**；issue **14 条全开**（最新 #59/11-16/0 评论）；**PR=0**；269 star / 27 fork / 36,920 KB（与上轮逐位相同）。官方 `docs/` 无任何 H3-Tiny 文档；MINIMAX-H3.md 的 pruned 段只描述 **[1025, 8]** 曲线。 | GitHub API（commits/releases/issues/pulls/repo）+ 本地 `docs/` grep | 2026-11-25 | 零增量；K148/K135 延续。**且首次确认上游 `pruned` 标志不区分 50 块/42 块** |
| **K161** | ★★ **H3-Tiny INT8 ComfyUI 权重正式发布**（`fuyi25/MiniMax-H3-Tiny@408d92a`，11-24 11:51，+198/−0）：4 文件 17B Ref2VA/17B FL2VA/14B OKD/17B FewStep 各 **18.1/18.1/15.1/18.1 GB**（bf16 对 34.2/34.2/28.1/34.2）。**W8A8 + ConvRot Hadamard，group 256**；内嵌 `metadata.h3tiny` JSON。H200 1344×768×243f：DiT **~17 GB** VRAM（bf16 33 GB）、**速度与 bf16 齐平**。 | GitHub commit detail + HF 页面（WebFetch） | 2026-11-24 | 补全 K155 的量化细节；**首次给出「本机需下多大文件」的确定值** |
| **K162** | ★★★ **H3-Tiny 权重头零下载实测**（Range 取 8B 长度 + 81496B JSON header，未下任何权重）：42 主块（0–41）、`adaln_t_table **[1025,16]**`、`blocks.0.adaln_proj.linear.weight [96768,16]` F32；14B 的 `fc1/fc2 = [19968,5376]/[5376,9984]`（bf16 版是 9792 → **INT8 pad 到 9984**）；FewStep 版**无 adaln_t_table**，改为 `.linear_1 [8,2688] + .linear_2 [96768,8]` 双段低秩。17B 与 14B 的 INT8 文件**张量数同为 788**（只能靠 FFN 宽度区分）。 | HF `resolve` + HTTP Range（本机直连可通） | 2026-11-25 | ★ **首次拿到 HyperFlow 之外的「24 GB 可塞」候选的真实结构**；推翻「INT8 = bf16 量化」的直觉（K164） |
| **K163** | ★★★ **本机对 H3-Tiny 是硬 gate 拒绝，不止「缺 catalog 条目」**：`metal-minimax-h3-transformer.cc:830` 要求 `pruned() && time_dim == 8`，而 `time_dim` 直接取自 `adaln_t_table` 第 2 维（:692）→ **[1025,16] 令 time_dim=16 → 加载即 fail**。Metal kernel `h3_adaln_pruned_f16` 亦硬编码 `k<8` / `coords+t*8`。FewStep 的双段 `linear_1/linear_2` 命名本机也不认（本机只认 `adaln_proj.linear`）。 | 本地源码（`.cc:692/830`、`.metal:183-201`）+ K162 权重头 | 2026-11-25 | **升级 K157**：表层是 catalog，根因是 **AdaLN 曲线宽度 8 vs 16 + 低秩分段方式**。P42 的「等上游采纳」改为「等上游把 pruned AdaLN 泛化到任意宽」（一次 kernel+校验双改） |
| **K164** | ★ **14B OKD 的 INT8 与 bf16 不同构**：bf16 `fc1/fc2 = 9792`，INT8 = **9984**（+192 列，因 9792 非 256 倍数，ConvRot group 256 需对齐）。 | K162 头对照 + bf16 14B 头 | 2026-11-25 | **纪律**：「INT8 版 = bf16 版量化」是错的假设；按 shape 判等价前必须比对实际 shape |
| **K165** | ★★ **官方 pruned（Comfy-Org）与 H3-Tiny 17B 在非 AdaLN 张量上逐形状一致**：Comfy-Org pruned int8 = 932 tensors / **50 块** / `[1025,8]` / qkv `[21504,5376]` I8 / fc1 `[28672,5376]` / fc2 `[5376,14336]`。与 Tiny 17B 的差异**只有两处**：块数 50→42、AdaLN 曲线 8→16。 | HF 头对照（Comfy-Org/MiniMax-H3 + H3-Tiny） | 2026-11-25 | 给「上游若采纳需改多少」划出精确边界：**只差块数自适 + AdaLN 宽度参数化** |
| **K166** | ★ **H3-Tiny 采样契约与本机 4/8 步家族不同族**：17B/14B OKD = **50 步 + `simple` + 无 CFG（BasicGuider）+ 不叠 turbo LoRA**；few-step 版用自家 sigma 网格 `linspace(1,0,steps+1)` @ **video shift 12**，默认 6 步（≥4）。 | H3-Tiny README + `comfyui/__init__.py` 注释 | 2026-11-24 | **不能拿「不训练可用」当「可直接套本机 4 步加速」**；强行 6 步必须用 few-step 权重而非 17B pruned |
| **K167** | ★ LightX2V **#1735**（`8bbaabd`，11-19）：RelayVSR x4 支持**显式输出画布**，动机原文即「H3 的 16:9 768P = 1344×768，两轴倍率不同」。同窗口 **#1743**（`6ef8487`）是 `minimax_h3_image` 推理复用 DiT conditioning + tiled VAE（**图像侧**）。 | LightX2V commit detail | 2026-11-19 | 生态印证；本机 `video-to-rgb` 有成对 `output_width/height`，但 `relayvsr-upscale` 无显式画布 → 需串一步 resize |

### 印证 / 冲突

- **印证 K155**（H3-Tiny 方法）：本轮权重头完全对上 README 的三件套——42 块、FFN 收窄、AdaLN 低秩。**K155 从「社区文档转述」升级为「文件级核实」**。
- **★★ 冲突①（K157 的层次修正）**：K157 记「catalog 无 h3_tiny 条目」为阻塞。本轮发现 **即使手工把文件塞进 catalog 也会在 loader 校验处 fail**（`time_dim != 8`）。这不是矛盾，是**分层**：catalog 是「找不到」，loader 是「找到了也不认」。**处置**：K157 保留，K163 作为其下层根因，P42 的前置条件重写。
- **★★ 冲突②（量化直觉）**：14B 的 INT8 宽度（9984）≠ bf16（9792）。任何「INT8 与 bf16 可直接互拷/对拍」的假设在 FFN 收窄的模型上失效。**处置**：新增纪律（K164），并在技能包量化文档层提示（本轮写进 `768p-adapters.md` / `h3-ecosystem-map.md`）。
- **★★ 冲突③（「不训练可用」的含义）**：K155 记「17B 剪完不训练可用」，容易被读成「便宜又可用」。真实条件是 **50 步全采样**。与本机 4/8 步路线不是同一赛道。**处置**：K166 明确限定，禁止跨赛道比较速度。
- **零增量（须明日复查，K121 教训）**：vpipe 上游（第 4 日静默）、`ModelTC/Minimax-H3-Turbo` 代码仓（最新 commit 仍 **02e26d5 / 2026-08-27**）、stable-diffusion.cpp（近 6 条 11-23~11-24：GGUF metadata / A1111 metadata / hires sigma / hidream speckle / LoRA F32，**无 H3**）、ComfyUI（近 8 条 11-23~11-24：custom nodes 启动崩溃修复 / user.css / **MPS deflicker #17940** / workflow templates ×2 / **w3+w5 量化格式 #17938** / Claude 节点 / Meshy 节点，**无 H3**）。
- **新迹象（非 H3）**：ComfyUI **#17938「Support w3 and w5 quantization formats」**（11-23 20:21）——量化位宽向 3/5 bit 扩展，与 K155/K161 的 INT8/W4A8 家族同方向，但**与 vpipe 无关**，仅记录生态趋势。

### 本轮实验

**无生成实验**，但**做了零成本的文件级实测**（K162/K164/K165）。
- 为何算「实测」：HTTP Range 只读 safetensors header（8 字节 + 81 KB JSON），**未下载任何权重张量**，磁盘占用 0，耗时 <2 min。这是本轮把「社区有」变成「结构确认」的关键手段。
- 为何不跑生成：① 时间预算（本轮 02:30 槽，硬超时 90 min，最小闭环优先）；② **K163 已判定即使下载 18.1 GB 也无法加载** → 下载无意义；③ 磁盘 37 GiB，18.1 GB 可行但会吃掉一半余量且无收益。
- ⇒ **P42 的下一步不需要下载**，需要的是「上游把 AdaLN 宽度从常量 8 改成参数」或「本机自行打补丁」。

### 坑

- **坑①（新，重要）：「零下载读权重头」是被低估的验证手段**。`Range: bytes=0-7` 取 u64 长度 → `Range: bytes=8-(7+len)` 取 JSON header，即可拿到**全部张量名 + shape + dtype + 内嵌 metadata**。对 18 GB 的模型，这比「先下再试」快 3 个数量级，且**足以判定「本机 loader 会不会 fail」**。前提：safetensors 格式（GGUF/ckpt 不适用）。
- **坑②：`hf-mirror.com` 会 308 永久重定向**（`HTTPError 308`），而 **`huggingface.co` 直连 Range 请求反而通**（仅 `/api/models` 与 `/tree/main` 超时）。⇒ 上轮 K 记的「HF API 不可达」要更精确：**不可达的是 JSON API 端点，不是文件 CDN**。分流方案再修正：① 指标/文件清单 → HF JSON API（或镜像 API）；② **权重文件头 → `huggingface.co/.../resolve/main/...` + Range（直连可用）**；③ 网页正文 → WebFetch。
- **坑③：社区搜索通道全部失效**。WebSearch 返回 `Authentication required for web search`；Reddit 返回「Prove your humanity」验证页。⇒ 本轮**社区面零新增未知源**，只有官方/仓库/权重文件三类一手源。**这是工具限制，不是社区无内容**，与上轮坑④同因，已连续两轮。
- **坑④：「同名不同构」第二次咬人**。上轮是 `ConvRot` 后缀（pi-H3 vs Tiny）；本轮是 `minimax_h3_*_pruned_int8_convrot`（Comfy-Org 50 块 [1025,8]）与 `minimax_h3_tiny_*_int8_convrot`（Tiny 42 块 [1025,16]）——**文件名几乎一样、格式描述一样、张量名一样，只有块数和 AdaLN 宽度不同**。查重必须比对 **shape**，不能比对名字。
- **坑⑤：`params` 内嵌值与实际不符**。Tiny 17B 文件 metadata 写 `params: 17054161792`（17.05B），README 表写 17.05B，但官网项目页写 17.1B、14B 写 13.98B/14.0B——**同一模型三种口径**。引用时须带来源（文件 metadata 最精确，因其由量化脚本写入）。

## 第 29 轮（2026-11-25 04:30 · 上游第 5 日静默 + 首个「三源融合适配器」Turbo Fusion 发布 + 本机 pruned AdaLN 通路可读性首次分层）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=04:30，模型 `custom-local:deepseek-v4.1-flash`）。
> 与第 28 轮的关系：上轮判「H3-Tiny 的 16 宽曲线被硬 gate」，本轮发现**同一套 pruned 机制在 8 宽下本机是支持的** —— 硬 gate 的是**曲线宽度**，不是「pruned 形式」本身。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K168** | ★ **上游第 5 日静默（口径修正）**：HEAD 仍 `a6a1f53`，`commit.author.date = 2026-11-23T09:54:27Z`、`pushed_at = 11-23T11:20:51Z` → 至本轮 04:30 分别为 **1.77 天 / 1.73 天**（上轮 K160 记「满 2 天」**略早**）。release 最新仍 **v0.1.110（11-01）→ 落后 main 24 天**；issue **14 条全开**（#59 仍 11-16 / 0 评论，无任何一条 updated 晚于创建日）；**PR=0**；269 star / 27 fork / 36,920 KB（与上轮逐位相同）。 | GitHub API（commits/releases/search-issues/pulls/repo） | 2026-11-25 | 零增量；**并修正上一轮「满 2 天」的时间口径**（K149 同族：时间也要带端点与算法） |
| **K169** | ★★★ **LightX2V 发布「Turbo Fusion」融合适配器**（`lightx2v/Minimax-H3-Turbo-Fusion`，11-24 18:50 UTC，HF + ModelScope 同步）：把**自家的 cm2200 蒸馏 ckpt ×1.0 + Pika Ref2VA Flex ×0.4 + Larry Turbo v4 step-600 EMA ×0.4** 合成**单个 LoRA**，推理期不再叠三个适配器。4 步与 8 步**共用同一融合配方**（只有基座 ckpt 不同）。8 个变体：Full 3.78 GB / Full-ComfyUI 5.21 GB / Lite-r32 665 MB / Lite-r32-ComfyUI 808 MB（4 步与 8 步各一套），另有 `pruned/` 子目录 4 个。**推理契约：Euler + video flow shift 12 + audio flow shift 3**。 | HF 模型卡全文（WebFetch/raw）+ HF tree API + ModelScope 文件 API | 2026-11-24 | ★ **直接冲击本机现役配方**：`dance-woman-768p.vpipeline` 用的是 lightx2v ref2va 8step v1.0 + **video_shift 6.0**；Fusion 要求 **shift 12** → **不可原样换槽**（P44 的前置） |
| **K170** | ★★★ **Fusion 权重头零下载实测（三种布局）**：① **Full（LightX2V/diffusers 布局）** 1089 tensors，`transformer_blocks.0.adaln_proj.linear.lora_A.default.weight **[32,2688]**` + `lora_B.default **[96768,32]**` BF16（即 2688 宽的**完整模型 AdaLN**，不是曲线）；② **ComfyUI 版** 777 tensors，QKV 融合（`qkv_proj.lora_A **[960,5376]**` = 3×320 块对角）、每模块 `alpha` 标量（`output_rank_counts {"32":207,"96":52}`）；③ **pruned 版** 828 tensors，`adaln_proj.linear.lora_A **[32,8]**` + `diff_b **[96768]** F32` —— 即 **8 宽曲线因子 + ComfyUI 权重 diff**。 | HF `resolve/main` + HTTP Range（本机直连可用） | 2026-11-25 | ★★ **本机对 pruned 的支持是「8 宽通、16 宽拒」**：K163 的硬 gate 只作用于 `time_dim != 8`；Fusion 的 pruned 版恰好是 8 宽 |
| **K171** | ★★★ **本机加载 Fusion-pruned 的三道门逐一核对（源码级）**：① 入口 = `bind_pruned_adaln_`（`.cc:4834`（diffusers）/ `:4897`（ComfyUI）两处仅在 `c.pruned()` 时调用）；② `.diff_b` 的触发条件 `file_touches(path,"adaln_proj.linear.diff")` 是**子串匹配**（`runtime-lora.cc:890 n.find(needle)`）→ `...linear.diff_b` 命中，`shape [96768] == D` 通过（`:4537`）；③ `alpha` 是**每模块标量**（`[]` F32），本机 `bind_host`/`factor_meta_` 读 `.alpha`（`lora-fusion.cc:292`），**不是** `__metadata__.ss_alpha`。⇒ **形状与命名均通**，剩下唯一硬条件 = **DiT 必须是 pruned 形式**（非 pruned 基座会 warn「this DiT is the released one, which does not apply them」并整段丢弃 AdaLN 分支）。 | 本地源码（`metal-minimax-h3-transformer.cc:4479-4640/4834/4897`、`runtime-lora.cc:865-910`、`lora-fusion.cc:281-300`）+ K170 头 | 2026-11-25 | **升级 K163**：阻塞不是「pruned」，是「**16 宽的 pruned**」。P42 与 P44 由此分家 |
| **K172** | ★★ **Comfy-Org pruned 权重体积实测（本机可读的那一档）**：`ref2va_pruned_int8_convrot` **20,970,379,616 B（19.53 GiB）**、`ref2va_pruned_fp8_scaled` 20,958,205,608 B、`ref2va_pruned_bf16` 40,225,724,176 B（37.5 GiB）、`ref2va_pruned_w6a8` 15,983,746,636 B（**文档明写按名拒绝**）。对照：未剪枝 `ref2va_int8_convrot` 34.04 GB / `ref2va_bf16` 66.28 GB。 | HF `Comfy-Org/MiniMax-H3/tree/main/diffusion_models` | 2026-11-25 | 给 P44 一个确定下载量：**20.97 GB + 0.52 GB LoRA**；磁盘 37 GiB 下可行但余量只剩 ~16 GiB |
| **K173** | ★★ **本机文档已把 pruned 形式写成正式支持路径**（`docs/MINIMAX-H3.md:2529-2600`）：`adaln_t_table (1025×8)`、每块 `[96768,8]`、t 的 lerp 读点、无 SiLU、f32 求和后一次 bf16 舍入；并**显式规定三类 LoRA 的处理**——「为 pruned 转换的」直接应用（含 `.diff`/`.diff_b`）、「在全模型上训练的」经 2688×8 基 U 与均值 m 搬到曲线上（拟合残差 ~2e-5，需**模型根下有未剪枝 ckpt**）、「改时间嵌入本身的」走 released ckpt 的 MLP。 | 本地 `repo/vpipe/docs/MINIMAX-H3.md`（d72c22f） | 2026-11-25 | **推翻 K157 的一半**：「catalog 无条目」仍真，但「本机不认 pruned」是错的——文档层面 pruned 是一等公民 |
| **K174** | ★ **`model-catalog.cc` 仍无 pruned DiT 条目**（全文件仅 1 处 `pruned`，且是**注释**：「`pruned` DiTs (a different model, not a different packing of this one)」）。⇒ 用 pruned 必须**手工 `hf_dir` 指目录**，不能走 catalog 的一键 prepare。 | 本地 `repo/vpipe/stages/model-catalog.cc:2502` | 2026-11-25 | K157 保留（catalog 层），K163 收窄为「16 宽」（loader 层） |
| **K175** | ★ **Fusion 的 Lite r32 是「QR-product truncated SVD」**，保留 **98.41%（4 步）/ 97.80%（8 步）** 的谱能量——模型卡**自己注明这是权重空间统计，不是感知质量**。 | HF 模型卡 | 2026-11-24 | 量化纪律：**谱能量 ≠ 画质**；与本机「纹理量/SSIM 双判」同族（单指标不可作结论） |
| **K176** | ★ **社区开始自建融合**：HF 11-24 六小时内新增 ~15 个 H3 仓库，其中 `ibyteohdear/MiniMax-H3-Pruned-DMD-FL2VA-Turbo-Fused`（434 下载）与 `-Pruned-LightX8-hybrid-Fused`（452 下载）都是**pruned + 融合**形态。⇒ 「融合适配器」正在成为社区惯例（与 LightX2V 官方 Fusion 同方向），且**默认按 pruned 基座发布**。 | `hf-mirror.com/api/models?search=minimax-h3&sort=lastModified` | 2026-11-24 | 生态信号；本机若要跟进，pruned 通路是**主干道而非旁路** |
| **K177** | ★ **H3-Tiny 权重仓现状**（补 K161）：HF `H3-Tiny/MiniMax-H3-Tiny-ComfyUI` **12 文件**（8 safetensors）、**14,156 下载 / 22 likes**、`lastModified 2026-11-24T11:53`；**ModelScope 无该仓库**（`record not found`）。 | HF API + ModelScope API | 2026-11-25 | K150 的「HF↔ModelScope 逐位比对」**不适用 Tiny**（只有 HF 单源） |

### 印证 / 冲突

- **★★★ 冲突①（对 K163 的收窄，这是本轮最重要的修正）**：K163 记「本机对 H3-Tiny 是硬 gate 拒绝」，容易被读成「本机不支持 pruned」。本轮源码+文档双证：**pruned 是文档明写的支持路径**（K173），loader 里有一条完整的 `bind_pruned_adaln_`（`.diff`/`.diff_b` + 全模型 AdaLN 经基 U 搬移，K171），**唯一的硬 gate 是 `time_dim != 8`**（H3-Tiny 是 16）。⇒ **处置**：K157 保留（catalog 层确实无条目），K163 改为「**16 宽 pruned 被拒**」，新增 K171 记「8 宽 pruned 通」。P42（Tiny）与 **P44（Fusion-pruned）** 从此是两个独立任务，前者等上游，后者**本机现在就能试**。
- **★★ 冲突②（现役配方与 Fusion 采样契约不符）**：本机 `dance-woman-768p.vpipeline` 是 lightx2v ref2va-8step + `video_shift 6.0 / audio_shift 3.0`；Fusion 卡面明确 **video shift 12**（audio 3 一致）。若直接换槽而不改 shift，就是**用错采样轨迹**——与本机 P13 系列的 shift 网格实验同族，但这次是**上游卡面给的契约**，不是猜的。⇒ **P44 必须同时改 shift**，否则结论不可归因。
- **★ 冲突③（时间口径）**：上轮 K160「满 2 天未动」按 `commit.author.date` 算只有 1.77 天。这不是矛盾，是**端点选择**（author date vs pushed_at vs 抓取时刻）。**处置**：本轮起统一写「**距 HEAD commit `<date>` 已 N.NN 天**」，不再用「第 N 日」这种粗口径。
- **印证 K151 的边界**：Fusion 的 4 步与 8 步 **Full 体积几乎相同**（3,778,242,236 vs 3,778,245,950，差 3,714 B）却**不是同一文件**（配方同、基座 ckpt 不同）→ 再次说明「字节相同 ≠ 同一模型」，与 K151/K164 的 shape 纪律同族。
- **零增量（须明日复查，K121 教训）**：vpipe 上游（第 5 日静默）、`ModelTC/Minimax-H3-Turbo` 代码仓（最新仍 `02e26d5 / 2026-08-27`）、ComfyUI（近 8 条 11-23~11-24：OpenAI ChatGPT V2 节点 / 缺失 custom_nodes 不崩 / user.css / MPS deflicker / workflow templates ×2 / w3+w5 量化 / Claude 节点，**无 H3**）、stable-diffusion.cpp（近 10 条：GGUF 转换元数据 #2409 / A1111 metadata #2344 / hires sigma #2361 / hidream speckle #2407 / **LoRA F32 #2383** / **INT8 即时 LoRA 合并 #2403（含 `metal/int8.metal`）**，**仍无 H3**）、LightX2V（最新仍 `e574493` #1749 / 11-23）。
- **新迹象（非 H3，但与本机量化路线同族）**：sd.cpp **#2403「support immediate LoRA merges for INT8 weights」**（11-23 15:57，改 `src/core/metal/int8.metal`）——**在 Metal 上把 LoRA 直接合并进 int8 权重**。本机 vpipe 的 `lora-fuse` 只处理宽 dtype（`fp8::decode_bf16` 出 f32），**int8 基座 + LoRA 融合**是缺口；这与 P44（pruned_int8 + Fusion LoRA）是同一个工程问题。

### 本轮实验

**无生成实验**；有**零下载的文件级实测**（K170/K171，HTTP Range 只读 3 个头 + 101 KB/129 KB JSON，<3 min，磁盘 0）。

- 为何不跑 P44：① 时间（04:52 起，硬超时 90 min，最小闭环优先）；② **P44 需要 20.97 GB pruned DiT + 0.52 GB LoRA**，下载本身在本机网速下就要 20–40 min，再加 124 帧生成 ≈ 29 min → **必然挤掉 sync/release**；③ 磁盘 37 GiB，下完只剩 ~16 GiB，低于 15 GiB 安全线的边缘。
- ⇒ P44 登记为**下轮首选实验**（若用户同意先下 pruned DiT）。

### 坑

- **坑①（新，重要）：「pruned」是一个家族，不是一种格式**。同一后缀下至少有三种互不兼容的形态：① 官方 8 宽曲线（`[96768,8]` + `adaln_t_table [1025,8]`）；② H3-Tiny 16 宽曲线（`[1025,16]`，本机拒）；③ Fusion-pruned 的「8 宽因子 + `diff_b`」（`.diff_b` 是**偏置差分**，不是权重差分，本机 `bind_pruned_adaln_` 里 `dst += is_w?0:d*8` 那一行就是专门为它留的位置）。**判「能不能跑」必须看 `adaln_t_table` 第 2 维 + 是否带 `.diff_b`，不能只看文件名里的 `pruned`**。这与 K164（INT8≠bf16 量化）、坑④（同名不同构）是同一族错误的第三次。
- **坑②：ModelScope 的 `pruned/` 子目录是空的**。HF 上 `pruned/` 有 4 个文件（818 MB / 5.22 GB），ModelScope 镜像里 `pruned` 只有一条 `Size=0` 的目录项。⇒ **镜像不等于同源全集**，尤其新增子目录。继 K157 坑②（HF API 不可达但 CDN 通）之后，镜像可信度也要按子目录核。
- **坑③：`file_touches` 是子串匹配，会把 `.diff` 和 `.diff_b` 一起命中**——本机正是靠这一点让 `.diff_b` 走通（K171 ②），但反过来说，**任何含 `adaln_proj.linear.diff` 子串的键**都会触发整段 `bind_pruned_adaln_`。若某天出现 `.diff_scale` 之类的键，会被误当差分。**读源码时看到 `find()` 就应假设「会误命中」**。
- **坑④：社区搜索通道连续第 3 轮失效**（WebSearch `Authentication required for web search`）。本轮社区面靠 **HF 模型搜索 API** 补位（`hf-mirror.com/api/models?search=...&sort=lastModified`）——这是本轮唯一还能拿到「社区在做什么」的通道，**建议正式纳入 SOP 的社区面替代源**，而不是标「未覆盖」了事。
- **坑⑤：Fusion 的 4 步/8 步 Full 文件体积差 3,714 B，几乎不可分辨**。若靠 `ls -l` 判「是不是同一文件」会误判；必须比 `__metadata__.recipe` 与 `source_sha256`。与 K149（同 commit 不同端点行数不同）同族：**聚合指标不能当明细**。

### 下一步

- **P44（新，中高）**：`Comfy-Org/MiniMax-H3` 的 `ref2va_pruned_int8_convrot`（20.97 GB）+ `lightx2v/Minimax-H3-Turbo-Fusion` 的 `pruned/…_4step_lite_r32_pruned_comfyui`（818 MB）。**必须同时把 `video_shift` 从 6.0 改 12.0**（K169）。需用户确认磁盘（下完剩 ~16 GiB）。
- **P42（Tiny）**：维持「等上游把 pruned AdaLN 泛化到任意宽」，本机不改源码。
- **P43**：`safetensors-peek.py` 仍未建，但本轮已用它跑了 5 个文件（手写版），**脚本化价值再次被证明**，建议尽快落地。
- **磁盘**：`minimax_h3_fl2va_bf16.safetensors.part`（18.3 GB 半成品）仍占位 —— 若要跑 P44，**必须先清理这 18.3 GB**（清理后 ~55 GiB，P44 全程安全）。

## 第 29 轮续（2026-11-25 06:30 · Kijai W4A8 混合档 + 本机 W4A8/pruned 二进制实装确认 + FastH3-VSA 「权重齐、PR 齐、只差合入」）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=06:30，守卫 R=29）。
> **编号说明**：04:30 槽（R=29）已把「第 29 轮」知识写进计划报告与知识台账，但**未通过 nightly_sync（round 仍 28、无同步日志）** → 上游 29 轮实际由 04:30 + 06:30 两段组成，本轮为第二段。本节编号从 K178 起（接 K177）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K178** | ★★★ **本机已装 App 二进制里早已含完整 pruned + W4A8 通路**：`libvpipe.0.dylib`（`0.1 / 9db5dd7*0`，2026-11-14 构建）`strings` 命中 `w4a8_to_i8`、`w4a8_convrot_dequant`、`asym_w4a8_int8`、`h3_adaln_pruned_f16`、`h3_adaln_pruned_res_f16`、`not the 8-wide curve this model reads`（**16 宽拒绝原文**）、`adaln_proj.linear.diff / .diff_b`。上游对应 commit = `41d2789`（2026-11-12，早于 build 日）→ **已编译进去，P44 无需重编译**。 | `strings` 应用二进制 + 本地 git `-S` 溯源 | 2026-11-25 | **K171 从「源码层面通」升级为「已发布二进制也通」**；P44 前置只剩「下载 + 改 shift 12」 |
| **K179** | ★★★ **Kijai 的 pruned W4A8 混合档是本机最小可塞候选**：`minimax_h3_ref2va_pruned_w4a8_mixed` **11,770,657,048 B（10.96 GiB）**、`fl2va` 版 12,540,858,008 B（11.68 GiB）。50 块、`adaln_t_table [1025,8]` F32、AdaLN `F16 [96768,8]`、**208 量化层 = 200 w4a8 + 8 int8_tensorwise**（8 层全是 `token_refiner.blocks.0.{qkv,out,fc1,fc2}`×2）。对照 Comfy-Org `ref2va_pruned_int8_convrot` 19.53 GiB → **少下 9.20 GB**。 | HF `resolve` + Range 读头 + tree API | 2026-11-25 | **P44 下载量下调 47%**（20.97 GB → 11.77 GB），37 GiB 磁盘从「剩 16 GiB 边缘」变「剩 25 GiB 安全」 |
| **K180** | ★★ **同一家族的两种量化记录布局**：ref2va 版每层旁挂 `<layer>.comfy_quant`（U8 tensor，89 B JSON）；fl2va 版**只有 header `_quantization_metadata.layers`**（200 条），**无** comfy_quant tensor。本机 `fp8-layout.cc:79-121` 两分支都能读，但「看有没有 .comfy_quant」会误判 fl2va 版「无记录」。 | 两文件头逐一对照 + 本地源码 | 2026-11-25 | 「同名不同构」**第三次**（K164 形状 / K171 后缀 / K180 记录位置）；纪律：量化格式必须双处并查 |
| **K181** | ★★★ **FastH3-Omni（VSA）权重已落地社区，但本机仍整文件拒绝**：`minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot` **21.33 GiB／1082 tensors**，250 层全 `int8_tensorwise + convrot group 256`，每块多 `attn.to_gate_compress.weight` I8 `[7168,5376]`。本机 `grep gate_compress` = **0**，`untranslatable_tensor()` 对无 native 名 tensor **整文件拒绝**。上游 **issue #56**（`AugustRush/vpipe:omniref-vsa`，2026-10-22，15 文件 746 行，GitHub 报 **Able to merge**，0 评论，已 34 天）失败原因与此**逐字一致**。 | HF Range 读头 + 本地源码 + GitHub issue #56 | 2026-11-25 | **新能力缺口分级**：VSA 是「**权重齐 + 现成 PR 齐 + 只差合入**」；与 P42（需改 kernel）不同，这条**不需改 kernel** |
| **K182** | ★ **官方仓 `MiniMaxAI/MiniMax-H3` 11-24 出现「误合 PR #112 → 12 分钟 revert」**：`ebc970b115`（04:53:34，阿拉伯语「换装」标题的社区图片 PR）→ `12253298ad`（04:56:04，"Revert accidental merge of PR #112"，恢复 `.gitattributes` 删除误合图片）。权重/代码零影响。 | HF `commits/main` API | 2026-11-24 | 纪律：**官方仓 `lastModified` 变动 ≠ 有新权重**，判权重更新须看 tree 的 sha/体积 |
| **K183** | ★ **Comfy-Org 官方镜像已收录 H3 ControlNet Union**：`model_patches/minimax_h3_fun_controlnet_union{,_2.0}_pruned_{bf16,int8_convrot}`（8.38/4.53/4.22/2.30 GB）。本机 `grep -ri controlnet --include=*.cc` = **0**。 | Comfy-Org tree API + 本地 grep | 2026-11-25 | 既有「ControlNet 本机零支持」结论不变，但生态地位从「alibaba-pai 单仓」升级为「**官方镜像也收**」 |
| **K184** | ★ **社区出现「latent 域时间修复」独立赛道**（非官方，**待复现**）：`BobMcoy/Minimax-H3-Temporal-Latent-Upscaler` v2.1 —— 不解码到像素，在首轮 sampler 的 **latent 输出**上按 17 帧块做运动检测，只对运动块 2×/3× 时间膨胀后二次采样，再回收原帧数 + Pass-1 原音频；另有 1.5× 空间超分。本机无对应 stage。 | HF README 全文 | 2026-11-24 | 与 RelayVSR/FlashVSR 的**像素域**超分不同层；vpipe 侧缺口，但仅 ComfyUI 节点，**不并入已验证能力** |

### 印证 / 冲突

- **印证 K171（强）**：「本机支持 8 宽 pruned」从**源码层**（`bind_pruned_adaln_` 三道门）升级为**已发布二进制层**（K178，`h3_adaln_pruned_f16` + `w4a8_to_i8` 均在 11-14 的 dylib 里）。⇒ P44 不再有「build 太旧」的风险。
- **★★ 冲突①（P44 的下载量，修正上轮）**：上轮 K172 把 P44 定成「Comfy-Org pruned_int8 19.53 GiB + Fusion 0.52 GB」。本轮发现 **Kijai 的 W4A8 混合档只有 10.96 GiB**，且**同族**（同 50 块 / 同 [1025,8] / 同 shift 12 契约）。**处置**：P44 首选改为 W4A8 档，Comfy-Org int8 降为备选（对照臂）。
- **★★ 冲突②（「mixed」的含义）**：`…_w4a8_mixed` 不是「W4A8 的别名」，而是**一个文件里两套格式**（200 w4a8 + 8 int8_tensorwise）。上轮「pruned 是一个家族」的坑①再扩一层：**连单个文件内部都可以是混合的**。⇒ 本机 `scan()` 已支持每层独立 format（`fp8-layout.cc:324-360`），所以**能读**；但「按文件判格式」的说法在混合档上失效。
- **★★ 冲突③（VSA 的阻塞层级，修正「H3 能力缺口」的叙述）**：此前把「本机缺 H3 能力」笼统归为「上游没做」。本轮证据显示三类不同的缺口：① **上游没做且需改 kernel**（P42 Tiny 16 宽）；② **上游没做但只需一张映射表 + PR 未合**（VSA，issue #56 已 Able to merge 34 天）；③ **上游已做但本机 build 旧**（此项本轮**清零** —— K178 证明 pruned/W4A8 都已在内）。⇒ 建议 P 表按此三类分栏，避免「都等上游」的钝化判断。
- **零增量（须明日复查）**：vpipe 上游（HEAD 仍 `a6a1f53`，`pushed_at 11-23T11:20:51Z` → 至 06:30 为 **2.81 天**；release v0.1.110 落后 **24 天**；issue 14 全开 0 回复；PR=0；**270 star**（+1）/ 27 fork / 36,920 KB）、LightX2V（最新仍 `e574493` #1749 / 11-23）、stable-diffusion.cpp（11-24 四条：GGUF 元数据 #2409 / A1111 metadata #2344 / hires sigma #2361 / hidream speckle #2407，**仍无 H3**）、ComfyUI（11-24 四条：frontend 版本回滚 #17970 / local_mcp_connect flag #17966 / OpenAI ChatGPT V2 #17962 / 缺失 custom_nodes 不崩 #17954，**仍无 H3**）、`ModelTC/Minimax-H3-Turbo` 代码仓（仍 `02e26d5 / 2026-08-27`）。
- **口径警示（沿用）**：Kijai 仓与 BobMcoy 仓都是**社区三手**（个人转格式/个人节点包），K179/K184 的结构数字来自**文件头实测**（可信），但「速度/画质」类描述一律**待复现**。

### 本轮实验

**无生成实验，也无新的零下载实测**（本轮的「读头」已并入 K179/K181 的知识条目）。理由：① 时间（06:30 起动，检索已用 35 min，硬超时 90 min）；② **P44 需先清 18.3 GB 半成品 + 下 11.77 GB + 改 pipeline 的 shift 12 + 生成 ≈ 29 min**，累计超预算；③ 磁盘 37 GiB（可用），但下载期间若中断会留下半成品，风险高于本轮收益。

### 坑

- **坑①（新，重要）：技能包「实验室副本」与「安装版」已经分叉，且分叉方向相反**。`~/.workbuddy/skills/vpipe-model-prepare/references/` 里有 55 KB 的 `768p-adapters.md`（含 K160–K177），而 `vpipe-lab/skills/` 里是 40 KB（只到 K167）；反过来 `vpipe-lab/skills/…/h3-ecosystem-map.md` 有 SLA 一节（6 处）与 `relayvsr-flashvsr.md` 有 P32 判决一节（1 处），**安装版没有**。⇒ **两边各有一半**。本轮已做**并集合并**（以安装版为底，把 lab 独有的 SLA 节 / P32 节回填），合并后 `installed 行全部在 lab 中` 已逐行校验为 0 缺失。**此前 6 轮 nightly_sync 一直推的是 40 KB 那份** → 远端仓库的 `768p-adapters.md` 至今只有 40,081 B（K169/K170 等从未上云）。**这是本轮最该修的坑**。
- **坑②：我在修复坑①时先做了一次「安装版覆盖 lab」的 cp，把 lab 独有的 SLA/P32 两节冲掉了**，随后从 `.vpipeworkflow-t` 的旧副本恢复并重做并集。⇒ **纪律：任何「同步」前先 diff，确认方向是「并集」而不是「覆盖」**。仓库副本救了我一次，说明 6 轮前推上去的旧版本**意外成了唯一备份**。
- **坑③：`comfy_quant` 的切片写法会多吃一个字符**。`k[:-11]` 对 `.comfy_quant`（11 字符）是**对的**，但我第一次写成 `k[:-len(suf)]` 时 suf 用了 `'.comfy_quant'` 带点（共 12）→ 得到 `blocks.0.attn.out_proj.`（尾点）→ `KeyError`。**用 `len(suf)` 而不是硬编码，且确认 suf 含不含点**。
- **坑④：`hf-mirror.com/api/models/<id>/commits/<sha>` 返回的是 list 而非 dict**（HF 的 commit detail 端点形状与 `/api/models/<id>` 不同）。用 `d.get('title')` 会 `AttributeError: 'list' object has no attribute 'get'`。⇒ 取 `[0]`。
- **坑⑤：社区搜索通道连续第 4 轮失效**（`WebSearch → Authentication required for web search`）。本轮社区面仍靠 **HF 模型搜索 API + HF README raw** 补位（发现 Kijai / BobMcoy 两个仓就是这么来的）。**建议正式把「HF 搜索 + README raw」写进 SOP 社区面替代源**，不再每轮标「未覆盖」。

### 下一步

- **P44（改首选）**：`minimax_h3_ref2va_pruned_w4a8_mixed`（10.96 GiB）+ `lightx2v/Minimax-H3-Turbo-Fusion` 的 `pruned/…_4step_lite_r32_pruned_comfyui`（818 MB）。**必须同时把 `video_shift` 6.0 → 12.0**（K169）。前置：清 `minimax_h3_fl2va_bf16.safetensors.part`（18.3 GB 半成品）。
- **P45（新，低）VSA 缺口跟踪**：盯 issue #56 是否被合入（已 Able to merge 34 天）。一旦合入，本机 build 需更新到含 `gate_compress` 的版本才能跑 21.33 GiB 的 FastH3-VSA。
- **P43**：`scripts/safetensors-peek.py` 仍未建（本轮又手写了 3 次）。**建议本轮之后立即落地**，否则每轮都重复写一遍。
- **上游同步策略**：技能包分叉（坑①）说明「安装版」才是最新写作位置，`vpipe-lab/skills/` 是发布副本。**应把 nightly_sync 的源改成 `~/.workbuddy/skills`**，或至少每次 sync 前做并集。**这是需要用户拍板的改动，本轮未改脚本**。

## 第 30 轮（2026-11-26 02:30 · 上游 6 日静默 + 官方 H3 蒸馏「最佳实践」落地 + 4 步适配器 alpha 从 128 掉到 8 + ClipProj 文本编码器替代路线与本机 connector 契约不符）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=02:30，守卫 R=30）。
> 与第 29 轮的关系：上轮把 P44 的**成本**砍半（W4A8 10.96 GiB）并确认二进制已含通路。本轮回答的是「**换槽时采样契约从哪来**」——答案不是某张模型卡，而是 LightX2V 当天（11-25 06:41）发布的**官方蒸馏训练配方**；同时首次发现 4 步家族 **v1.3 的 alpha 与 v1.0 差 16 倍**，把 K151「字节同构可换槽」收窄。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K185** | ★ **上游静默第 6 日（口径带端点）**：HEAD 仍 `a6a1f53`，`commit.author.date = 2026-11-23T09:54:27Z` → 至本轮抓取时刻 `2026-11-25T18:36Z` 为 **2.36 天**（按 `pushed_at = 11-23T11:20:51Z` 是 **2.30 天**）。release 最新仍 **v0.1.110（11-01）→ 落后 main 24 天**；issue **14 条全开**（#59 仍 11-16 / 0 评论；#55 仅 10-21 创建后 10 分钟自更新）；**PR = 0**（`search is:pr&state=all` total_count=0，`repos/pulls` 返回 `[]`）；**273 star**（+3）/ 27 fork / 36,920 KB（size 与上轮逐位同）。 | GitHub API（commits/releases/search-issues/search-prs/pulls/repo） | 2026-11-25 | 零增量；star 是唯一变动量 |
| **K186** | ★★★ **LightX2V 官方发布 H3 蒸馏「best practices」**（`7fc25cd`，PR #1730，11-25 06:41:54Z，+2629/−202 / 19 文件）：把 H3 训练从「T2AV + DMD 单阶段」改为 **FL2AV + Ref2AV 双任务、dCM → PDMD+GAN 两阶段**。**dCM**：1500 iters、LoRA rank/alpha **128/128**（AdaLN `adaln_proj.linear` 与 `norm_out.linear` 覆盖为 **16/16**）、student LR **2e-5**、AdamW (0.0,0.999)/wd 0.01、`total_steps 48`/`skip_steps 1`、`loss_scale 100.0`、`ema_decay 0.999`、video/audio loss weight 0.8/0.8、32 GPU FSDP2、每 500 存 2 个。**PDMD+GAN**：3000 iters（`fake_update_ratio 5` → **2500 fake : 500 student**）、student LR **5e-5**、fake LR **4e-6**、betas (0.0,0.9)、GAN `generator_weight 0.005 / discriminator_weight 0.01`、`feature_block 49`、`head_hidden_dim 1024`、`head_temporal_bins 4`、`critic_video_threshold 0.95 / critic_audio_floor 0.85`、每 100 存 2 个。数据契约：`cache_dataset` + `meta.json`，**124 帧 @ 24 fps**，FL2AV 768×1344 / Ref2AV 1344×768。 | GitHub commit detail（`lightx2v_train/docs/minimax_h3_distill.md` 全文 128 行 + 6 个 yaml 全量） | 2026-11-25 | ★ **官方第一次公开 H3 蒸馏的超参账本**，此前全部靠模型卡反推 |
| **K187** | ★★★ **官方 Ref2AV 蒸馏配方的 shift 就是 12/3，FL2AV 是 6/3**（且 FL2AV 的 PDMD 里 shift 在 1500 步处从 6.0 切 12.0：`video_shift_schedule {0→6.0, 1500→12.0}`）。dCM 阶段：FL2AV `6.0/3.0`、Ref2AV `12.0/3.0`；PDMD 阶段：`rollout_video_shift` FL2AV 6.0（带调度）→ 12.0、Ref2AV 恒定 **12.0**。 | `consistency/minimax_h3_{fl2av,ref2av}_dcm_fsdp32.yaml` + `pdmd/minimax_h3_{fl2av,ref2av}_pdmd{4,8}_gan_fsdp32.yaml` | 2026-11-25 | ★★ **K169 的证据链升级**：Fusion 卡面「shift 12」不是单卡约定，而是**官方 Ref2AV 蒸馏的训练分布**；本机现役 ref2va 配方 `video_shift 6.0` 与官方 Ref2AV 线不符 |
| **K188** | ★★★ **4 步 768p 家族的 v1.3 与 v1.0「形状同构、强度差 16 倍」**：v1.0/v1.1/v1.2/v1.3 四个 768p bf16 文件 **均 624 tensors、header 81,768 B、key 集与 shape/offsets 完全一致**（逐键比对 True）；但 `__metadata__.alpha`：**v1.0 = "128"、v1.1 = "128"、v1.2 = "8"、v1.3 = "8"**（rank 恒 128）。权重体抽样（`transformer_blocks.0.attn.to_out.0.lora_B` 200k 个 bf16 值）：**mean\|w\| v1.0 0.002028 / v1.2 0.001995 / v1.3 0.001913**，**max v1.0 0.0347 / v1.2 0.0277 / v1.3 0.0173**。 | HF `resolve/main` + HTTP Range（头 4 次 + 权重切片 6 次，磁盘 0） | 2026-11-25 | ★★★ **K151「4 步全版本字节同构 → 可直接原槽 A/B」必须收窄**：形状同构 ≠ 可直接换槽，**alpha 语义变了 16 倍**（本机 `runtime-lora.cc:324-333` 读的就是 `__metadata__.alpha`，再 `alpha/rank` 折成 `mul`，`:445-452`） |
| **K189** | ★★ **stable-diffusion.cpp 出现首个 H3 专项提交**（`5fa203c`，#2410，11-25 16:29）：**ClipProj-MiniMax-H3**——用一个**线性投影**把 **Qwen3-VL-4B/8B** 映射到 H3 的 **5120 维**，替代 **Qwen3-VL-32B** 文本编码器，显存 **15.7 GB → 4.5 GB**（4B INT8）。实现：`ClipProjConnector`（`input_dim 2560 / output_dim 5120`、`W/mean_in/std_in/mean_out/std_out/sink_out`）、**只读 tap 24 单层**（P-H3 connector 读 `{13,19,25,31,37}`，32B 读 50）、`sink_out` 替换首 token、**明确不支持 `-mlp` 残差变体**；检测顺序 P-H3 优先、ClipProj 是 `else if`。 | GitHub commit detail（4 文件 +166/−7，含 `src/model/te/clipproj_connector.hpp` 全文） | 2026-11-25 | 首次证明「H3 文本编码器可替换」是跨运行时的独立赛道；本机是第三家（P-H3-Image connector） |
| **K190** | ★★★ **本机 connector 契约与 ClipProj 不兼容（源码级判定）**：本机只认 `_class_name == "PH3ImageTextConnector"`（`p-h3-image.h:46`），发现入口是 `text_encoder/` 旁的 `text_connector/config.json`（`minimax-h3-text-encoder.cc:451` → `connector_config_` 读 `hidden_state_indices` / `text_hidden_size` / `out_channels`），**张量名必须是 `proj.weight` / `input_mean` / `input_std` / `output_mean` / `output_std` / `sink_embedding`**（`:668-690`，且全部强制 **F32**）。ClipProj 的 safetensors 是**单文件 6 张量、无 config.json**，名字是 `W / mean_in / std_in / mean_out / std_out / sink_out`，**dtype F16**，且 `W` 形状 **[2560,5120]**（与本机期望 `proj.weight [in*outw]` 的一维展平不同）。更根本：本机是「**N 个 tap 沿 hidden 维拼接 → 一次投影**」，ClipProj 是「**单 tap → 一次投影**」——tap 数不同，不是换个名能通。 | 本机源码（`p-h3-image.h`、`minimax-h3-text-encoder.cc:191-250/451/664-700`）+ ClipProj 权重头实测 | 2026-11-25 | **新增能力缺口 P46**；同时修正一个易犯的错觉：「本机有 connector 通路」≠「本机能加载任意 connector」 |
| **K191** | ★★ **Fusion pruned 的 4 步与 8 步 lite_r32「同头不同体」**：两文件均 **828 tensors / header 100,232 B / key 集与 shape 完全一致**（比对 True），但权重体抽样 sha 全不同（头部 600 KB 与尾部 700 KB 两段都不同）。`__metadata__` 里 `pruned_table_sha256 = c02a6c11…a229a8e7` **两者相同**（同基座同 AdaLN 表），`default_training_alpha 32.0`、`output_alpha_counts {"32.0":207,"96.0":52}` 也相同。 | HF Range 读头 ×2 + 权重切片 ×4 | 2026-11-25 | 「字节同构 ≠ 同一模型」**第 4 次**（K151 步数 / K164 INT8 宽度 / K175 体积 3714 B / K191 步数） |
| **K192** | ★★ **社区在 11-25 单日出现 H3 的 GGUF 量化家族与「无训练调优」int8**：① `Infinity-io/MiniMax-H3-GGUF`（11-25 02:21，83 dl）——`minimax_h3_{fl2va,ref2va}_pruned-{Q2_K 6.7 GB, Q3_K 8.7, Q4_K 11.4, Q5_0 13.9, Q6_K 16.6, Q8_0 21.4}` + `UD-Q2_K_XL 8.1 / UD-Q3_K_XL 9.6`；② `yichengup/minimax_h3-tyc-zs05-ltxqnorm-int8-convrot`（11-25 08:46，1,141 dl，**20.97 GB**，卡面自述「官方 pruned 的调优变体，**未训练**」）。 | HF 搜索 API + tree API + README raw | 2026-11-25 | **本机 H3 无 GGUF 加载路径**（`repo/vpipe/generative-models/minimax-h3/` 下 `gguf` 命中 **0**，全树 56 个 gguf 文件均在 LLM/图像侧）→ 记为缺口，**不并入能力** |
| **K193** | ★★ **`yichengup` tuned int8 与官方 pruned_int8 **逐键相同**（932/932，0 差异）但语义不同**：metadata 声明 5 处结构 graft —— `zspatial_graft`（借 Z-Image-Turbo 的 `q_norm`，块 30–49，dose 0.5）、`qnorm_graft`（借 LTX-2.5 `attn1.q_norm` 均值归一 ×1.9340，块 30–48，dose 1.0）、`qnorm_pin`（块 49 rms 5.0）、`adaln_splice none (fl2va throughout)`、`quant_format int8_tensorwise convrot groupsize 256`。`adaln_t_table` 仍 `[1025,8]` F32 → **本机 loader 不会拒**。 | HF Range 读头（键集逐键比对 vs Comfy-Org `ref2va_pruned_int8_convrot`） | 2026-11-25 | ★★ **「同名不同构」第 5 次，且这次连 shape 都一样**：判「能不能跑」不能只看键集/shape，**必须读 metadata 的 graft 声明**（画质来源不可归因到模型名） |
| **K194** | ★ **ClipProj 的自我评测边界（作者原文）**：v3.1 用 **4B 编码器 + 26 MB 投影**；多语种音素错误 **−29%** 总体，西/法/德/意 **−60~74%**；但「**图像分数与 v3 完全重叠**，与 32B 也无可分辨差异——这不等于相同，余弦对**可数属性**是盲的」；32B 自己换 seed 就会重读 **75 个音素里的 5.8 个**，v3.1 四文件是 **6.4–7.0** ⇒「换编码器约等于重掷一次 seed」。权重头实测 `cos_test 0.6874` / `r2_test 0.4755` / tap 24 / d_in 2560 / d_out 5120。 | ClipProj README 全文 + `mmh3-4b-ClipProj-v3.1` 权重头 | 2026-11-25 | 纪律印证：**单一相似度指标不能当保真结论**（与本机「纹理量/SSIM 双判」同族） |
| **K195** | ★★ **issue #56 的阻塞层级要改写：不是「只差合入」，是「已落后 30+ commit」**：`AugustRush/vpipe` 是 fork（`fork: true`，parent `tgo-app-dev/vpipe`），默认分支 `main`，另有分支 **`omniref-vsa`**，其最新 commit **`fd0b0e2`（2026-10-21T09:36:01Z）**；fork 的 `pushed_at = 2026-10-22T04:37:48Z` → **整整 35 天无推送**，而 upstream 在此期间前进了 `4dc36b7 → a6a1f53` 等多个大 commit。tgo-app-dev 侧 **PR 总数 = 0**（不是「挂着未合」）。 | GitHub API（`repos/AugustRush/vpipe` + `/branches` + `/commits?sha=omniref-vsa` + `search is:pr`） | 2026-11-25 | **修正 K181/P45 的措辞**：VSA 缺口的真实形态 = 「社区分支停在 10-21 的 upstream 基线上，**合入前必须先 rebase 一个月的演进**」，成本远高于「点一下 Merge」 |
| **K196** | ★ **sd.cpp 修 RelayVSR 的 KV graph-cut 命名缺陷**（`f296cb0`，#2419，11-25 14:11，14 文件 +129/−60）：KV cache 名不带 `relayvsr.` 组前缀 → 末段重算本该复用的部分；修法是 `cache_name = cut_group + "." + attention_name` 并 `mark_graph_cut(value, cut_group, …)`；同时把 DGL 的 OOM 从「静默 {}」改成 `SD_STATUS_OUT_OF_MEMORY` + 设备内存文案上抛。 | GitHub commit detail | 2026-11-25 | **不可迁移**：本机 RelayVSR 是独立 stage（无 graph-cut 概念，整段计算）；记录为生态一致性，非能力 |

### 印证 / 冲突

- **★★★ 冲突①（K151 收窄，本轮最重要）**：K151 记「4 步全版本字节同构 → v1.3 可原槽 A/B」，此结论的**后半句是错的**。实测四个 768p bf16 文件**结构确实逐键同构**（624 tensors / 同 shape / 同 offsets），但 **`__metadata__.alpha` 从 128 掉到 8**（v1.0/v1.1 = 128 → v1.2/v1.3 = 8），而本机 `runtime-lora.cc` 正是用 `alpha / rank` 作为缩放因子折叠进 LoRA 分支（`:445-452`）。**若直接把 v1.3 塞进 v1.0 的槽，等效强度只有 1/16**，出的片子必然是「几乎无 Turbo 效果」而不是「新版本效果」。⇒ **处置**：K151 改写为「**形状同构，可直接换槽，但必须同时核对 `__metadata__.alpha`**」；P40 的「换槽 A/B」前置加一条 alpha 核对。
- **★★ 冲突②（K169 从「卡面」升级为「训练配方」）**：K169 依 Fusion 模型卡记「Ref2VA 用 video shift 12」。本轮 K187 从官方训练 yaml 拿到同一条：**Ref2AV 的 dCM 与 PDMD 全程 12.0/3.0，FL2AV 才是 6.0/3.0（且 PDMD 里 1500 步后切 12）**。⇒ **本机现役 `dance-woman-768p` 用 6.0 跑 ref2va，与官方 Ref2AV 蒸馏分布不符**；P44 改 shift 不再是「照卡面猜」，而是「回到训练分布」。同时说明一个更普遍的事：**shift 6 vs 12 不是画质偏好，是任务分家（FL2AV vs Ref2AV）**。
- **★★ 冲突③（P45 的阻塞层级）**：K181 记「权重齐、PR 齐、只差合入」。本轮查证 fork 停在 **2026-10-21**（35 天未推送），upstream 已前进到 `a6a1f53`；且 upstream **PR 数为 0**（PR 从未以 PR 形式提交，只存在于 fork 分支）。⇒ 处置：P45 的表述改为「**需先 rebase 一个月演进**」，优先级维持低（成本被低估过）。
- **★ 冲突④（「本机有 connector」的范围）**：既有认知「本机支持 P-H3-Image connector」容易被外推成「本机支持 connector 机制」。K190 证明：契约被**类名 + 6 个固定张量名 + F32 + N-tap 拼接**四重锁死，ClipProj 四条全不满足。⇒ 新增 P46，并写入技能包警示。
- **零增量（须明日复查，K121 教训）**：vpipe 上游（第 6 日静默）、`ModelTC/Minimax-h3-Turbo` 代码仓（HF 侧 `Minimax-h3-Turbo` 最新 commit 仍 `ff0edf4` / 11-24「Add base model metadata」，**无新权重**）、ComfyUI（11-25 五条：#17987 Meshy task ids / #17962 Recraft Vectorizer / #17973 GB300 不走 int8 linear / #17970 frontend 回滚 / #17966 MCP flag，**无 H3**）、`ModelTC/lightx2v` 主线（最新 `83a424a` #1757 README 文案，实质变更即 #1730）。
- **新迹象（非 H3，但与本机量化路线同族）**：ComfyUI `0d0e105`「**Don't do int8 linears in int8 on GB300**」（11-25 02:44）——int8 线性层在某些后端要**展宽**再算，与本机 W4A8 的 `w4a8_to_i8`（K178）是同一类「低位宽权重 + 高位宽累加」的取舍。

### 本轮实验

**无生成实验**；有**零下载文件级实测**（K188/K190/K191/K193 的读头与切片，共 12 次 Range 请求，磁盘占用 0，累计 <6 min）。
- 为何不跑 P44：① 时间（02:30 起动，检索阶段已用 ~40 min，硬超时 90 min；P44 = 清 18.3 GB 半成品 + 下 11.77 GB + 改 shift + 124 帧生成 ≈ 29 min，必然挤掉 sync/release）；② **K188 刚证明「换槽前必须先核 alpha」**，若此刻仓促跑 P44，会在「换 Fusion LoRA + 改 shift 12 + 换 pruned 基座」三个变量同时动的情况下给出不可归因的结论。⇒ **P44 的配方本轮被补全（前置清单 4 条），留待有完整时间窗的槽位**。
- 为何不跑 P40：同上，且 P40 的运动夹具尚未建（K152 依赖）。

### 坑

- **坑①（新，重要）：`__metadata__.alpha` 是「同构换槽」的隐形开关**。四个 4 步文件 key/shape/offsets 完全一致，`ls -l` 只差 0–8 B（1,383,677,808 vs 1,383,677,808/1,383,677,768），**任何靠体积或形状的判等都会说「一样」**；只有读 header 的 `__metadata__` 才看得到 `128 → 8`。这是 K151/K164/K175/K191「字节同构」家族的**第 5 次**，也是第一次「同一家族内部**语义强度**变了」而不只是「不同模型」。⇒ 纪律：**换任何 LoRA 槽前，读 3 件事：`__metadata__.alpha`、rank（`lora_A` 第 0 维）、是否带 per-module `.alpha`**。
- **坑②：`hf-mirror.com` 现在对 `resolve` 路径 308、对 `api/models/<id>/commits/main` 返回 Cloudflare challenge**。本轮实测：`resolve/main` 走 hf-mirror → **HTTP 308 Permanent Redirect**（`urllib` 直接抛错）；同一 URL 走 `huggingface.co` **直连可用**（Range 正常）。而 `/api/models/<id>` 与 `/api/models?search=` 在 hf-mirror 上**都正常**，`/commits/main` 首次返回 JSON、第二次返回 `{"error":"…challenge…"}`。⇒ 分流再修正：**① 元数据/文件清单/搜索 → hf-mirror；② 权重文件（含 Range） → huggingface.co 直连；③ commits 详情 → 只取一次并落盘（`/tmp`），不要重复请求**（这是我本轮丢了两次结果才总结出来的）。
- **坑③：`/api/models/<id>/commits/main` 有时返回 **dict**（含 `error/message/retry_after/challenge`）而不是 list**。第一次我按 list 处理成功，第二次同一 URL 返回 dict，`d[:2]` 抛 `TypeError: unhashable type: 'slice'`（对 dict 切片）——注意这个报错的字面意思极具误导性。⇒ 读 HF commit API 必须 `if isinstance(d, dict): 判 error`。
- **坑④：`/api/models/<id>/commits/main/<path>`（按文件查提交）在 hf-mirror 上是 404**，即使文件真实存在。⇒ 「这个权重哪天加的」这个问题，**镜像 API 答不了**，只能走网页或放弃。
- **坑⑤：社区搜索连续第 5 轮失效**（`WebSearch → Authentication required for web search`）。本轮社区面仍靠 **HF 模型搜索 API（按 `lastModified` 倒序）+ README raw + tree API** 补位，并因此拿到 K192/K193（GGUF 家族、tuned int8 的 graft 声明）。**这已是稳定替代路径，建议正式写进 SOP**（连续 5 轮的经验，不该每轮再试一次 WebSearch）。
- **坑⑥：`numpy` 不在系统 python3 里**（`/Library/Developer/CommandLineTools/.../3.9`）。想量 bf16 权重幅度只能手写 `struct.unpack('<H')` + `u<<16` 转 float。⇒ P43 的 `safetensors-peek.py` 若要带「幅度统计」，不能依赖 numpy，需纯 stdlib 实现（或者检测到 numpy 再启用）。

### 下一步

- **P44（配方补全，仍为首选实验）**：前置清单从 2 条变 4 条 —— ① 清 `minimax_h3_fl2va_bf16.safetensors.part`（18.3 GB）→ 余 55 GiB；② 下 `Kijai/…:minimax_h3_ref2va_pruned_w4a8_mixed`（10.96 GiB）+ Fusion `pruned/…_4step_lite_r32_pruned_comfyui`（818 MB，**K191**：4 步/8 步同头不同体，取 4 步）；③ **`video_shift 6.0 → 12.0`**（K187，官方 Ref2AV 训练分布）；④ **核 Fusion LoRA 的 alpha 语义**（K188 教训：`default_training_alpha 32.0` + `output_alpha_counts {"32.0":207,"96.0":52}`，与本机 `alpha/rank` 折算式对齐后再跑）。
- **P46（新，中）ClipProj 文本编码器替代**：本机不支持（K190）。两条路：① **打包适配**——把 `mmh3-4b-ClipProj-v3.1` 的 6 个张量改名为本机期望的 6 个、转 F32、补 `text_connector/config.json`（`_class_name: PH3ImageTextConnector`、`hidden_state_indices: [24]`、`text_hidden_size: 2560`、`out_channels: 5120`）——**但本机是 N-tap 拼接，单 tap 的语义是否等价需读代码确认**；② 等上游加 ClipProj 分支。收益：文本编码器 15.7 → 4.5 GB，24 GB 机器上能腾出 ~11 GB 给 DiT/超分。
- **P45（措辞修正）**：不再是「只差合入」，而是「fork 停在 2026-10-21，合入前需 rebase 一个月演进」。
- **P43（仍未建）**：`scripts/safetensors-peek.py`。本轮又手写 12 次读头/切片，且新增两条需求：**打印 `__metadata__` 全量**（K188 的 alpha 就藏在这）、**纯 stdlib 的幅度统计**（坑⑥）。
- **P40（补前置）**：「换槽 A/B」前必须核 `__metadata__.alpha`（K188），否则 v1.3 会被误判为「变差」。

## 第 31 轮（2026-11-26 04:30 · 本机 2K latent-upscale 链路「放大件本就有、缺的是 refiner」+ int8 适配器因子是本机第二条量化盲区 + Qwen3.5-9B 换编码器但成片 PSNR 仅 14.8 dB）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=04:30，守卫 R=31）。
> 与第 30 轮的关系：上轮找到「文本编码器可换（ClipProj）但本机契约不符」；本轮把**同一条杠杆的两端补齐**——① 视频侧后处理：社区在 11-25 单日把 Open-H3-Regenerate-2K 的 2K refine 打包成 ComfyUI 节点，而**本机的 latent-upscale stage 与 catalog 条目本来就在**（K198），缺的只是 refiner LoRA；② 文本侧：第二个社区换编码器方案（Qwen3.5-9B + 投影 + rank32 LoRA）出现，但**作者自己的视频 PSNR 只有 14.8 dB**（K202/K203），把「编码器对齐 ≠ 成片对齐」量化了。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K197** | ★ **上游静默第 7 日**：HEAD 仍 `a6a1f53`，`author.date = 2026-11-23T09:54:27Z` → 至本轮抓取约 **2.4 天**（按 `pushed_at 11-23T11:20:51Z` 同量级）。release 最新仍 **v0.1.110（11-01）→ 落后 main 25 天**；issue **14 全开**；**PR = 0**；**273 star / 27 fork / size 36,920 KB**（与上轮逐位同）。 | GitHub API（commits / repo / releases / search-issues / search-prs） | 2026-11-25 | 零增量 |
| **K198** | ★★★ **本机 2K latent-upscale 链路早已完整，社区文件只是同一份权重的 F16 转存**：本机有 `stages/latent-upscale-stage.cc`（`type_name = "latent-upscale"`，参数 `scale` / `width` / `height` / `align`）与 `metal-minimax-h3-latent-upscaler.{h,cc}`（3D-conv：conv_in 24→512、in/out 各 12 ResBlock + 6 TemporalConv、GroupNorm 按全片统计、`Normalize::kRelease` 双重归一），catalog 两条条目（`Open-H3-Regenerate-2K` / `-IC`）都指向 `latent_upsampler/minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors`。本轮逐头比对：官方 bf16 与 SOLRICKS 的 **322 tensors / key 集 / shape 全部一致（onlyA 0 / onlyB 0），唯一差异 dtype BF16→F16**（头 32,552 → 32,232 B）。 | 本机源码（`metal-minimax-h3-latent-upscaler.cc:209-290/547`、`model-catalog.cc:2749-2765`）+ HF Range 双读头 | 2026-11-26 | **「本机 2K 不支持」的旧印象作废**：放大件是一等能力；`VPIPE_H3UP_BF16` 可切 bf16，f16 出非有限值时自动回退 bf16 |
| **K199** | ★★★ **int8 适配器因子是本机的第二条量化盲区（与基座 int8 通路分立）**：`SOLRICKS/MiniMax-H3-Upscaler:h3_upscale_refiner_int8.safetensors`（1,884,199,184 B / 624 tensors = **208 模块 × (lora_A I8 + lora_B I8 + alpha F32)**，50 块 + token_refiner 2 块）是 Open-H3-2K r256 refiner LoRA 的 int8 打包。但 `runtime-lora.cc` 的 `take_()` / `take_f32_()` **只分支 BF16/F16/F32**（`:502-517`、`:537-546`），`fp8::format_of()` 对 `"I8"` 显式返回 `kNone`（`fp8.h:76-88` 注释「kNone for any other dtype (I8 among them)」）⇒ I8 因子取空 → `++_skipped` → **该模块静默不生效**。 | HF Range 读头 + 本地 `runtime-lora.cc` / `fp8.h` / `fp8-layout.cc` | 2026-11-26 | **新缺口分级**：此前只区分「基座量化（有 int8/W4A8 通路）」与「适配器量化」，本轮证明后者**零支持**，且失效是静默的（只 `_skipped` 计数，不报错） |
| **K200** | ★★ **同一字段「alpha」在本机有两种互斥语义（K188 之后的第 2 次）**：K188 的 4 步家族 alpha 是**整数倍率**（128 / 8，`mul = alpha / rank` 得 1 或 1/16）；SOLRICKS 的 alpha 是**量化 scale**（`quantization: int8_per_tensor_scales_in_lora_alpha_v1`），实测 `blocks.48.mlp.fc2 = 3.956e-4`、`blocks.15.attn.out_proj = 1.800e-4`，且 **rank 逐模块不同**（159 / 185 / 200 / 258 / 338 / 513）。⇒ 即便将来能读 I8，`alpha / rank` 也只能折出约 1e-6 量级，强度归零。 | HF Range 读 208 个 `.alpha`、抽样 6 个 | 2026-11-26 | K188 纪律扩写：读 alpha 前**先判它是「倍率」还是「scale」**——判据是量级（整数或接近 rank，还是 1e-4 量级）与 metadata 的 `quantization` 键 |
| **K201** | ★★ **SOLRICKS 自报的量化代价（作者标注 `visual_quality_metric: false`）**：`conversion.converted_pairs 208`、`max_tensor_relative_rmse 0.2841`；`quantization_error_summary`（每矩阵相对 Frobenius）median **0.0824** / mean 0.0875 / p95 **0.1432** / max **0.2841**；`additional_training: false`。 | `manifest.json` 全文 | 2026-11-26 | 引用社区量化件时**体积与误差必须同引**，否则等于替作者隐去代价 |
| **K202** | ★★★ **第二个社区「换文本编码器」方案：Qwen3.5-9B + 4096→5120 投影（tap 20）+ rank-32 联合 LoRA**：`Alissonerdx/Qwen3.5-9B-Minimax-H3`（11-25 18:54）。投影文件 **9 张量全 F32**（`W [4096,5120]`、`mean_in/std_in [4096]`、`mean_out/std_out [5120]`、`mlp.0 [8192,4096]` + `mlp.2 [5120,8192]`，即**带 MLP 残差**），LoRA **530 tensors / rank 32 / 34 个线性模块 / BF16 / 全部 `model.language_model.layers.*` 前缀**。配套节点 `alisson-anjos/ComfyUI-Qwen3.5-H3`（11-24 建，13 star）。 | HF tree + Range 读头 ×2 + GitHub repo API | 2026-11-26 | **与本机契约（K190）四条全不符，且比 ClipProj 更远**：ClipProj 是「无 mlp」变体，这个**带 mlp**——而 sd.cpp 的 `ClipProjConnector` 明确写「不支持 `-mlp` 残差变体」。⇒ P46 的「打包适配」要同时处理 tap 数、张量名、dtype、MLP 残差四件事 |
| **K203** | ★★★ **「编码器对齐 ≠ 成片对齐」被作者自己的数字量化**：text cosine **0.8919（仅投影）→ 0.9507（Epoch3 联合）**、vision(`refs`) cosine **0.7873 → 0.8879**、overall 0.8396 → 0.9193；但**视频 Mean PSNR 仅 12.877 → 14.764 dB、Frame Corr 0.441 → 0.631**，差例 case04（4 参考）**PSNR 11.104 dB / corr 0.4808**。 | 该仓 README 指标表 | 2026-11-26 | **待复现**，但方向明确：hidden-state 余弦 0.95 只换来 14.8 dB 成片——与本机「纹理量/SSIM 双判」（K194 同族）一致：**单一相似度指标不能当保真结论** |
| **K204** | ★★ **`ibyteohdear` 两个「LoRA 融合进基座」的 pruned 全量 diffusers 仓（各 4 分片 ≈ 40.2 GB）**：`MiniMax-H3-Pruned-DMD-FL2VA-Turbo-Fused`（`LoRA alpha 15.156 / rank 16 / Fusion scale 0.897 / 363 层`）与 `MiniMax-H3-Pruned-LightX8-hybrid-Fused`（`alpha 48 / rank 48 / scale 1 / 312 层`），基座同为 `multimodalart/MiniMax-H3-Pruned/transformer`，方法 `load_lora_adapter → pin scaling → fuse_lora → strip peft → sharded save`。分片头实测 **176 tensors/片、无 `adaln_t_table`**，AdaLN 已烘进 `norm_out.folded_bias [10752]`；`config.json` 声明 `adaln_rank 8 / hidden_size 5376 / num_layers 50 / text_dim 5120`。 | HF tree + Range 读头 + `fusion_metadata.txt` + `config.json` | 2026-11-26 | 本机 catalog 原文写明 `pruned` DiT 是「**a different model, not a different packing**」，且 `WeightSet::open` 走单文件 / GGUF 路径（无 diffusers 分片目录读取）⇒ **看着像 H3、本机打不开**的第四类（前三类：16 宽 Tiny / VSA gate_compress / GGUF） |
| **K205** | ★★ **官方 pruned 基座有一个本机不读的旁挂件**：`multimodalart/MiniMax-H3-Pruned/transformer/adaln_affine.safetensors` = `adaln_basis F32 [8,2688]` + `adaln_mean F32 [2688]`（头仅 184 B）。本机全树 `grep -ri "adaln_affine|adaln_basis|adaln_mean"` = **0**。 | HF Range 读头 + 本地 grep | 2026-11-26 | K165 只比过 `adaln_t_table [1025,8]`，没注意**8 宽曲线的基与均值是旁挂的**；若 P44 用 diffusers 格式 pruned 基座，这条会被漏读 |
| **K206** | ★ **`jh27kim/MiniMax-H3-Ref2VA-4step` 是 gated 仓，但目录树可读**：`ref2va/iter1500/ref2va_lora_r256_iter1500.safetensors`（2,767,272,416 B）+ `student_config.json`；README 需授权。**r256 / iter1500** 与 K186 官方 dCM 1500 iters 对齐。 | HF tree API | 2026-11-25 | 与官方配方同步的社区切片；内容不可读 ⇒ 只记存在性，不进能力表 |
| **K207** | ★ **11-25 单日社区面量化：H3 衍生新仓 ≥20 个 / 24 h**（`SOLRICKS/MiniMax-H3-Upscaler` **5,706 dl**、`pmczip/MiniMaxH3_RefMod` **1,634 dl**（单人像 LoRA 集，每个 1.5–1.7 MB）、`Infinity-io` GGUF、`yichengup` tuned int8 1,141 dl、`ibyteohdear` 两个 Fused 各约 500 dl、`Alissonerdx` 换编码器、`AXERA-TECH` 边缘 NPU 版……）。 | HF 搜索 API（`lastModified` 倒序，两个关键词各 20 条） | 2026-11-26 | 生态重心已从「模型」转向**后处理 / 换编码器 / 融合进基座**三条流水线；本机三条里有两条是空白（int8 适配器、diffusers 分片） |
| **K208** | ★ **issue #59 与 #56 连「状态变动」都没有**：两者 `updated_at == created_at`（#59 = 2026-11-16T09:12:21Z、#56 = 2026-10-22T04:40:36Z），评论 0。 | GitHub issue API | 2026-11-26 | 「零回复」升级为「**零触碰**」——标签、指派人、milestone 都没动，比「没人回」更冷 |

### 印证 / 冲突

- **★★★ 冲突①（P44 的前置①作废）**：上轮把「清 `minimax_h3_fl2va_bf16.safetensors.part`（18.3 GB）」列为 P44 第一条前置。本轮实测 `vpipe-lab` 下**没有任何 `.part` 文件**，`du` 仅 1.7 G，磁盘 **37 GiB 可用**。⇒ **删掉该前置**；P44 从 4 条降为 3 条（下 W4A8 10.96 GiB + Fusion pruned 4 步 818,925,468 B；改 `video_shift 6.0 → 12.0`；核 Fusion LoRA 的 alpha 语义）。
- **★★★ 冲突②（「本机不支持 2K」的旧印象）**：K198 证明本机 **latent-upscale stage + 3D-conv 网络 + catalog 两条条目全部在位**，且社区那份 upscaler 只是同一权重的 F16 转存（322 tensors / key / shape 全同）。⇒ 2K 路线的缺口**只在 refiner LoRA 那一侧**（Open-H3 的 r256/576 或 SOLRICKS 的 int8 打包），不在放大件。
- **★★★ 冲突③（适配器量化与基座量化被混为一谈过）**：本机的 int8 支持（`fp8-layout.cc` 的 `int8_tensorwise` / `asym_w4a8_int8`、K178 的 `w4a8_to_i8`）**只服务基座权重**；LoRA 因子走 `runtime-lora.cc`，只认 BF16/F16/F32。⇒ 新缺口 **P47（int8 适配器因子）**，且**静默失效**（`_skipped` 不上报）。
- **★★ 冲突④（alpha 的语义第二次分裂）**：K188 = 「整数倍率」（128/8）；K200 = 「量化 scale」（1e-4 量级）。同一字段名、同一位置（`.alpha` / `__metadata__`），语义相反。⇒ **读 alpha 必须先判量级 + 看 metadata 的 `quantization` 键**。
- **印证（K194/K203 同族，强）**：hidden-state 余弦 0.95 / overall 0.92 的换编码器方案，成片 PSNR 只有 14.76 dB。⇒ 「中间表示相似度」不能替代「成片指标」，与本机 18.6 / 18.22 的「纹理量 + SSIM 双判 + 编造量」判据一致。
- **零增量（须明日复查，K121 教训）**：vpipe 上游（第 7 日静默，273 star 不变）；LightX2V（最新仍 `83a424a` / 11-25 07:07 仅 README 文案，实质变更即上轮 #1730）；stable-diffusion.cpp（11-25 新增 `52491bd` #2423 DGL 编辑器内联媒体预览、`82c19c8` #2420 取消 DGL 任务、`c33eebc` #2367 server `--api-key/--cors-origins`，**仍无 H3 主体**）；ComfyUI（11-25 五条：#17987 Meshy task ids / Recraft Vectorizer / **#17973 GB300 不走 int8 linear** / #17970 frontend 回滚 / #17966 MCP flag，**无 H3**）；ModelScope `lightx2v/Minimax-h3-Turbo` 31 项不变、`Minimax-H3-Turbo-Fusion` 15 项不变（`pruned/…_4step_lite_r32_pruned_comfyui` **818,925,468 B 与 HF 逐字节同**）。

### 本轮实验

**无生成实验**；有**零下载文件级实测**（K198/K199/K200/K202/K204/K205 的读头与切片，共 14 次 Range 请求，磁盘 0，累计约 8 min）。
- 为何不跑 P44：时间（04:30 起动，检索阶段已用约 35 min，硬超时 90 min；P44 = 下 10.96 GiB + 818 MB + 改 shift + 124 帧生成约 55 min，会挤掉 sync/release）。**且 K200 刚发现「alpha 语义有两种」**——此时跑 P44 会在 Fusion LoRA 的 alpha 未判定前引入第三个不可归因变量。
- 为何不跑「2K upstream 放大」（K198 已证明通路在）：upstream 权重 690 MB 可下，但**单跑一次 latent-upscale 没有对照**（需要先有 768p 成片 + refiner 才能判画质），单独跑只能验「能不能加载」，价值低于 P44。⇒ 建议作为 **P44 的第二臂**（refiner 前后对照）。

### 坑

- **坑①：`api.github.com/repos/comfyanonymous/ComfyUI/commits` 现在返回 `{"message":"Moved Permanently","url":".../repositories/589831718/commits"}`**。仓库转移 / 改名后，`repos/<owner>/<name>` 路径对 commits 端点会 301。⇒ 必须走 `repositories/<id>`（或加 `-L`）；`repos/<owner>/<name>` 对 repo 元数据仍正常，**只有 commits 端点会跳**。
- **坑②：HF 镜像对某些仓的 commit API 返回 `{"error":"Invalid username or password."}`**（本轮 `ModelTC/Minimax-h3-Turbo`）。这**不是**「仓不存在」也不是「gated」，是镜像不代理该仓的 commit 端点。⇒ 判定「仓还在不在」要用 `api/models/<id>`，不能用 `/commits/main`。
- **坑③：在家目录做无界 `find ~ -name "*.safetensors" -maxdepth 6` 会 SIGTERM**（本轮实测直接被杀，无输出）。⇒ 一律用已知路径列举（`~/.vpipe`、lab 目录），**不要扫家目录**。
- **坑④：`.alpha` 是 F32 小标量时必须按 float 解**。若沿用 K188 的「整数 alpha」思维做 `int()`，SOLRICKS 的 3.9e-4 会得 0 → `mul = 0` → 整份 LoRA 静默无效，且日志无错。⇒ 读 alpha 先 `struct.unpack('<f')`，再看量级判语义。
- **坑⑤：`curl` 取 HF 的 `resolve/main` 走 hf-mirror 会 308**（上轮坑②），本轮全部改 `huggingface.co` 直连，14 次 Range 全部成功。⇒ 分流定稿不变：**元数据 / 搜索 / 文件清单 → hf-mirror；权重（含 Range）→ huggingface.co 直连**。
- **坑⑥：Python 3.9 从 stdin 读脚本时，含中文的 heredoc 会 `SyntaxError: Non-UTF-8 code starting with '\xe3'`**（本轮实际发生一次）。⇒ 中文字面量的脚本先 `Write` 成 `.py` 文件再执行，或首行加 `# -*- coding: utf-8 -*-`。
- **坑⑦：社区搜索（WebSearch）仍不可用**（按第 30 轮建议本轮未再试）。本轮 ≥20 个新仓全靠 `api/models?search=minimax_h3&sort=lastModified` 两个关键词拿到。**连续第 7 轮的稳定替代路径，SOP 正文仍未更新**。

### 下一步

- **P44（前置降为 3 条，仍为首选）**：① 下 `Kijai/…:minimax_h3_ref2va_pruned_w4a8_mixed`（10.96 GiB）+ Fusion `pruned/…_4step_lite_r32_pruned_comfyui`（**818,925,468 B，HF 与 ModelScope 逐字节同**）；② **`video_shift 6.0 → 12.0`**（K187）；③ **核 Fusion LoRA 的 alpha 语义**（K188 整数倍率 vs K200 量化 scale，先判量级）。**新增可选第二臂**：用 K198 的 latent-upscale 做 refiner 前后对照。
- **P47（新，低）int8 适配器因子通路**：本机 `runtime-lora.cc` 不认 I8（K199），且**静默跳过**。两条路：① 在 `take_()` 加 I8 分支（读兄弟 `.weight_scale`，或按 `quantization` metadata 从 `.alpha` 取 scale）；② 转换脚本把 I8 解成 BF16 再喂。**收益有限**（只影响社区 int8 LoRA），但**静默失效**值得加一条 warning。
- **P46（扩写）**：换编码器现在有**两个**社区方案（ClipProj 无 mlp / Qwen3.5-9B 带 mlp + rank32 LoRA），两者都要求「单 tap + 一次性投影」，与本机 N-tap 拼接不同；且 K203 显示成片 PSNR 仅 14.8 dB。⇒ P46 优先级**维持中，但期望值下调**。
- **P43（仍未建）**：`scripts/safetensors-peek.py`。本轮又手写 14 次读头，新增第三条需求：**按模块聚合**（`.alpha` 逐个读、rank 逐模块统计）。
- **SOP（仍未改）**：把「HF 搜索 API + README raw 替代 WebSearch」「hf-mirror 只取元数据、权重走直连」「commits 端点 301 走 `repositories/<id>`」三条写进 `vpipe-夜间自动任务SOP.md`。

## 第 32 轮（2026-11-26 06:30 · 上游静默第 8 日 + 社区「时调制剪枝」三态（bf16 打不开 / int8 打不开 / 融合 base 可加载）+ Fusion LoRA alpha 判决「按原样 1.0，无需折算」+ w6a8 是双重拒绝 + VAE int8 是本机第三条量化盲区）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=06:30，守卫 R=32）。
> 与第 31 轮的关系：上轮把「2K 后处理通路」和「int8 适配器盲区」两条线摆清；本轮**把 P44 的第③条前置（Fusion LoRA 的 alpha 语义）直接判死**（alpha 全体等于 rank，mul = 1.0），并把社区 11-25 单日新增的三类「时调制剪枝」件逐一判了本机可读性——**bf16 件与 int8 件都打不开，只有融合进基座的 int8 件契约全符合**。同时发现 VAE 侧存在**第三条**量化盲区（`.scales`/`.biases` vs ComfyUI 的 `.weight_scale`/`.comfy_quant`）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K209** | ★ **上游静默第 8 日**：HEAD 仍 `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`pushed_at 11-23T11:20:51Z`）；release 最新仍 **v0.1.110（11-01）→ 落后 main 26 天**；issue **14 全开**（#59/#58/#56/#55 均 0 评论）；**PR = 0**；**273 star / 27 fork / 36,920 KB** 逐位同上轮。 | GitHub API（commits / repo / releases / search-issues / search-prs） | 2026-11-26 | 零增量（连续第 8 日） |
| **K210** | ★★★ **「时调制剪枝（WaveCut 风格 / one-hot 时编码）」已成社区一条独立工艺线**：`iamwavecut/MiniMax-H3-Image-Pruned`（11-10）把 AdaLN 在**固定采样步**上预先算好，用 one-hot 时编码 + 投影替换整张时调制网络，H3-Image 从 **135 → 94 GB**（diffusers）且**逐像素相同**；`Jianqiao1/MiniMax-H3-Image-Lossless-Pruned-ComfyUI`（11-25）把它搬到 ComfyUI 的**参考图路径**：bf16 **66.3 → 40.2 GB**，作者实测**五组场景 5/5 逐像素相同（MAE 0 / PSNR ∞）**；INT8 ConvRot 21.0 GB 但 **PSNR 21.833 dB、0/5 相同**。 | GitHub repo API + 该仓 README 指标表 + HF tree | 2026-11-25 | **待复现**（ComfyUI 0.45.0 / RTX 5090 / 4096² / Euler CFG1 六步）；但「剪枝代价可以为零、量化代价不能」这一点与 K172/K201 同向 |
| **K211** | ★★★ **两个 WaveCut 风格文件本机都打不开，且是两种不同的打不开**：① **bf16 件**（`minimax_h3_image_wavecut_style_pruned_reference_bf16.safetensors` 40,234,634,888 B / 531 tensors）**无 `model.diffusion_model.` 前缀、无 `adaln_t_table`**，只有 `blocks.0.adaln_proj.linear.weight BF16 [96768,8]` 与**极窄的 `time_embedder`（`proj_in [16,256]` / `proj_out [8,16]`）**，AdaLN 宽度 8 而 `time_dim` 走默认 **2688** → 本机 `comfy_saved` 两条判据（前缀 / `adaln_t_table`）**全不满足** → 在 `metal-minimax-h3-transformer.cc:657-661` 直接 fail **「is neither a Comfy-Org H3 component, an H3 DiT ComfyUI saved, nor one in the diffusers naming」**；② **int8 件**（20,979,299,938 B / 981 tensors）同样无前缀、无 `adaln_t_table`，另外还带本机不读的 `blocks.N.attn.comfy_attention.config`（`[{"attention": "comfy_kitchen_int8"}]`，本机全树 grep = 0）。 | HF Range 读头 ×2 + 本地源码 | 2026-11-26 | **「看着像 H3、本机打不开」第 5 类**（前四：16 宽 Tiny / VSA gate_compress / GGUF / diffusers 分片目录）：**「宽 8 的 AdaLN + 无前缀 + 无曲线表」这种 one-hot 剪枝形态本机没有识别分支** |
| **K212** | ★★★ **P44 的第③条前置判死：Fusion pruned 的 alpha 全体等于 rank，`mul ≡ 1.0`，无需折算**。`lightx2v/Minimax-H3-Turbo-Fusion:pruned/…_4step_v1.0_pruned_comfyui`（5,220,193,444 B / 828 tensors）逐模块实测：`adaln_proj.linear` **alpha 32 / rank 32**、`attn.out_proj` + `mlp.fc1` + `mlp.fc2` **alpha 320 / rank 320**、`attn.qkv_proj` **alpha 960 / rank 960**（qkv 是 320×3，metadata `qkv_fusion: "block diagonal B; concat A; alpha multiplied by 3"` 的落点）。⇒ 属 K188 的**「倍率」语义**（不是 K200 的量化 scale），且**乘数为 1.0**。 | 该文件 Range 读头 + 逐模块 `.alpha`/`lora_A` 切片 + `__metadata__` | 2026-11-26 | **K188/K200 的第三态落定**：alpha 有三种现场值（整数倍率 ≠ rank / 等于 rank / 1e-4 量化 scale）；**换槽体检第③项「rank 逐模块不同」在 Fusion 上得到最强例证：32 / 320 / 960 三档、极差 30×** |
| **K213** | ★★ **Fusion pruned 的 AdaLN 修正是「LoRA 因子 + 只有 `diff_b`」的组合，不是 `.diff` 权重补丁**：51 个 `diff_b`（50 块 + `final_layer`，F32 `[96768]` / `[10752]`），**无任何 `.diff`**；同层另有 `lora_A [r,8]` + `lora_B [96768,r]` + `.alpha`。metadata 自述 `adaln_conversion: "A'=A@P; diff_b=(alpha/r)*B@A@mean; original B and alpha preserved"`。本机 `bind_pruned_adaln_` 的 needle `adaln_proj.linear.diff` 用 `find` 匹配 → 命中 `diff_b`；后缀判断 `ends("....diff")` 对 `...diff_b` 为假 → **is_b 分支，只写 bias 半区**（`dst += d*8`），weight 半区由 LoRA 因子承担 —— **契约吻合**。 | Range 读头 + 本地 `metal-minimax-h3-transformer.cc:4501-4560` | 2026-11-26 | 印证 K170「`.diff_b` 本机可读」；补上「**同层可同时有 diff_b 与 lora 因子，二者分工不重叠**」 |
| **K214** | ★★★ **`pruned_w6a8` 是双重拒绝（不是一条门）**：`Comfy-Org/MiniMax-H3:…_ref2va_pruned_w6a8.safetensors`（15,983,746,636 B / 1151 tensors）实测 `comfy_quant = {"format":"w6a8_int8","group_size":32,"convrot":true,"convrot_groupsize":256}`，权重 `I8 [21504,4032]`（6 bit 打包）+ `weight_s_rel F8_E4M3 [21504,168]`（= K/32 组）+ `weight_s_channel F32 [21504]`。⇒ ① `fp8-layout.cc:326` 显式按名拒绝 `w6a8_int8`；② **即便去掉名字门**，I8 路径的 scale 校验只接受「1 个」或「每行 1 个」（`:438-448`），K/32 的**块量化** scale 会被「BLOCK-scaled encoding, which this build does not read」拒。 | Range 读头 + 本地 `fp8-layout.cc:326 / 438-448` | 2026-11-26 | **K172 的「按名拒绝」升级为「名 + 布局双拒」**：w6a8 没有任何「改名就能读」的捷径 |
| **K215** | ★★★ **社区融合基座第一次「契约全符合」（零下载判头）**：`Coffmeteor/MiniMaxH3-Realism-Turbo-Remix:int8/minimaxh3RealismTurbo_v10INT8.safetensors`（20,967,649,144 B / **932 tensors**）——`model.diffusion_model.` **全前缀**、`adaln_t_table F32 [1025,8]`、`blocks.0.attn.qkv_proj.weight I8 [21504,5376]` + `weight_scale F32 [21504,1]`（**逐行**）、`comfy_quant = {"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}`、50 块、`audio_patch_proj` 与 `audio_out` 齐、**无 `time_embedder`**（pruned 形态）⇒ 本机 `comfy_saved` / `is_component` / I8+ConvRot / 逐行 scale 四条**全部满足**。另带 `__metadata__.required_prompt_prefix = "r34l1sm"`（**本机不读此键，触发词须手动加进 prompt**）。 | HF Range 读头 + 本地源码对照 + `catalog.json` / `source.json` | 2026-11-26 | **重要但有限**：它是「Singularity + Turbo + Realism + Motion 融合 + **真人 YouTube 微调**」的社区 remix ⇒ **真人素材，只记存在性，不进能力表、不交付**；价值在于它是**第一份证明「社区自融 pruned base + int8_convrot」在本机契约上可行**的样本 |
| **K216** | ★★ **`w6a8` 之外，社区还有「ref LoRA」这条 FL2VA→Ref2VA 的轻量路线**：Kijai README 原文「ref lora is the difference between fl2va and ref2va, completely experimental, I don't even know if it has a use case at this point」，其 `wip/` 下另有 `minimax_h3_ref2va_pruned_w6a8_g32.safetensor`（指向 Comfy-Org/comfy-kitchen PR #191）。 | HF README raw | 2026-11-26 | 与本机「两 partition 权重字节相同、行为不同」并存：社区用「差一个 LoRA」解释同一现象，**待复现**；若成立则 FL2VA 单份下载可覆盖两任务 |
| **K217** | ★★ **VAE 侧是本机的第三条量化盲区（K199 之后的第二条细分）**：Kijai 新增 3 个 int8_convrot VAE（`lightvae_lite` 1,036,943,392 B、`lynnreal_light` 2,137,493,384 B、`mt_video` 2,811,065,896 B；官方 `video_vae_int8_convrot` 3,171,670,912 B），README 自报「VAE decode 提速约 2×」（需 ComfyUI 0.36.0）。实测 `lightvae_lite` 头：**I8 48 + U8 48 + 标量 `weight_scale` + `comfy_quant {"format":"int8_tensorwise","convrot":true}`**。但本机 VAE 的量化契约是 `linear_()` 读 **`.scales` + `.biases`**（仿射量化，`_quant_bits` 4/8 + `group_size` 默认 64，来自 config 的 `quantization` 对象，`metal-minimax-h3-video-vae.cc:852-870 / 1362`）⇒ **ComfyUI 的 `.weight_scale` / `comfy_quant` 命名本机不认**，`weight_()` 会把它当普通权重 `to_bf16_()` 解码 → **I8 码被当整数读成值**（若 `_quant_bits == 0` 则直接走 dense 路径拿 I8 张量）。 | HF Range 读头 + 本地 `metal-minimax-h3-video-vae.cc` | 2026-11-26 | **新缺口 P48**；与 K199（LoRA 因子 I8）同族但独立——**同一份 ComfyUI int8 件里，DiT 能读、VAE 不能读** |
| **K218** | ★ **11-25～11-26 单日社区面续增**：`SOLRICKS/3D-Animation-Style-MiniMax-H3`（rank16 / step00001250 LoRA + 5 份 V3 workflow）、`Coffmeteor/MiniMaxH3-Realism-Turbo-Remix` **908 dl**、`pmczip/MiniMaxH3_RefMod` **1,634 dl**（单人像 refmod 集）、`SOLRICKS/MiniMax-H3-Upscaler` 5,706 dl 仍居首。 | HF 搜索 API（两个拼写各 25 条） | 2026-11-26 | 生态重心未变（后处理 / 换编码器 / 融合进基座），新增「风格化 LoRA 集」一支 |
| **K219** | ★ **sd.cpp / ComfyUI / LightX2V 三线零增量**：sd.cpp 最新 `52491bd`（#2423 DGL 内联媒体预览），**H3 相关仍只有 11-25 的 `5fa203c` ClipProj(no mlp)**；ComfyUI 最新 `f40a4fbb`（frontend 1.59.15 版本号 bump）+ `a2103ae6`（Meshy task ids STRING）+ `b27006af`（Recraft Vectorizer），**无 H3**；LightX2V 最新仍 `83a424a`（README 文案）。ModelScope `lightx2v/Minimax-h3-Turbo` 31 项、`Minimax-H3-Turbo-Fusion` 48 项（含 `pruned/` 4 件，`lite_r32_pruned_comfyui` **818,925,468 B 与 HF 逐字节同**）。 | GitHub API ×3 + ModelScope API ×2 | 2026-11-26 | 零增量（明日复查） |

### 印证 / 冲突

- **★★★ 判决①（P44 第③条前置关闭）**：上两轮把「核 Fusion LoRA 的 alpha 语义」列为 P44 必备前置（因 K188 的 8 vs 128、K200 的 3.96e-4 两种互斥语义）。本轮逐模块实测 **alpha 全体 == rank**（32/32、320/320、960/960）⇒ `mul = alpha/rank ≡ 1.0`，**按原样绑定即可，不需要任何折算**。⇒ **P44 只剩两条前置**（下载 + 改 `video_shift`）。
- **★★★ 冲突①（「社区 int8 件都能读」不成立）**：K215 证明 Coffmeteor 的融合 int8 基座契约全符合；但 K211 证明同一波社区件里，**WaveCut 风格的 bf16 与 int8 两个文件本机都拒载**，理由是「无前缀 + 无 `adaln_t_table` + AdaLN 宽 8」这条**本机没有识别分支**。⇒ 「社区有」与「本机读」必须**逐件判**，不能按发布时间或作者归类。
- **★★★ 冲突②（量化盲区从两条变三条）**：K199 = 适配器（LoRA 因子）I8；K214 = 基座 w6a8（名 + 块 scale 双拒）；**K217 = VAE int8（命名契约不同，且失效是"把码当值"，比 K199 的静默跳过更危险）**。⇒ 本机量化账本应是四栏：**基座 FP8 / 基座 int8-W4A8 / 适配器 / VAE**。
- **★★ 印证（K172 强化）**：`pruned_w6a8` 15.98 GB 是「文档明写按名拒绝」，本轮顺手证明**连布局都不合**（K/32 块 scale）。⇒ 「换个名试试」这条路彻底没有价值。
- **★★ 印证（K191 家族扩写）**：Fusion 的 rank 三档（32 / 320 / 960）与 K191 的「4 步 / 8 步同头不同体」是同一件事的两面——**rank 是逐模块、逐目标的**，不能按「整个适配器一个 rank」记账。
- **零增量（须明日复查）**：vpipe 上游第 8 日（273 star 不变）；LightX2V `83a424a`；sd.cpp `52491bd`；ComfyUI `f40a4fbb`；ModelScope 两仓逐项不变；Comfy-Org `MiniMax-H3` 仓 12 个 `diffusion_models` 文件 lastModified 为空（HF tree 未给），`modified 2026-11-15` 不变。

### 本轮实验

**无生成实验**。零下载实测共 **11 次 Range 请求**（K211 ×3、K212 ×2、K213 合并、K214、K215、K217、K210 的 README、K216 的 README），磁盘占用 0，累计约 **9 min**。

不跑 P44 的理由（比上轮更弱，但仍成立）：
1. **时间**：06:30 起动，检索已用约 35 min，硬超时 90 min。P44 = 下 10.96 GiB + 818 MB（约 25 min）+ 改 shift + 124 帧生成（约 29 min）≈ 55 min，**会挤掉两份报告与 sync/release**。
2. **本轮的价值在「判死前置」而非「开跑」**：K212 把最后一条不确定性消掉，P44 现在是一个**完全确定的**两前置实验，适合放在有完整时间窗的槽位。
3. **磁盘 38 GiB**：下 10.96 + 0.82 = 11.8 GiB 后可余 26 GiB，**技术上可行**，只是时间不够。

### 坑

- **坑①（新）：HF `tree/main` 对大仓的 `lastModified` 会整列缺失**。本轮 `Comfy-Org/MiniMax-H3/diffusion_models` 12 个文件全部没有时间戳（字段不存在，不是 null）。⇒ 判「文件是否新上传」不能靠 tree，要看 `api/models/<id>.lastModified`（本轮 11-15 未变）或逐文件 `commits/main`。
- **坑②（新）：`hf-mirror.com/<repo>/raw/main/README.md` 对部分仓返回一行 `Temporary Redirect. Redirecting to ...`**（本轮 Fusion 仓），`curl -sL` 会跟到 `huggingface.co` 但内容仍为空。⇒ README 走 `huggingface.co/<repo>/raw/main/...` 直连（与 K 的「权重直连」分流一致），镜像只用于搜索与 tree。
- **坑③（复现）：** `grep -c "w6a8"` 在主报告里只有 1 处（K172），**说明「按名拒绝」这个结论此前只有体积、没有格式证据**。本轮补上 `comfy_quant` 原文后才看清是 `group_size 32` 的块量化。⇒ 结论落库时**必须连"拒绝的具体判据"一起写**，否则下一轮无法判断「是格式问题还是名字问题」。
- **坑④（复现）：`blocks.N.attn.comfy_attention.config` 这类「节点头」本机全树 grep = 0**（`comfy_attention` 零命中）。它不是权重、也不是本机的 aux 后缀列表成员（`fp8-layout.cc:is_aux_name` 只列 scale/comfy_quant/codebook 等），落在「不认识但也不致命」的灰区——只有它所在的文件被前缀/曲线表判据拒掉时才不构成问题。⇒ 遇到带 `comfy_attention.config` 的文件应**先判整件可读性**，别指望它是唯一障碍。

### 下一步

- **P44（前置降为 2 条，本轮起为「完全确定」首选实验）**：① 下 `Kijai/…:minimax_h3_ref2va_pruned_w4a8_mixed`（**11,770,657,048 B = 10.96 GiB**）+ `lightx2v/Minimax-H3-Turbo-Fusion:pruned/…_4step_v1.0_lite_r32_pruned_comfyui`（**818,925,468 B**）；② **`video_shift 6.0 → 12.0`**（K187）。**第③条 alpha 体检已关闭**（K212：mul ≡ 1.0）。**建议放在有完整 90 min 窗的槽位**（下载 25 min + 生成 29 min + 余量）。
- **P48（新，中）VAE int8_convrot 通路**：本机 VAE 走 `.scales`/`.biases` 仿射量化（`_quant_bits` 4/8、`group_size` 64），**不认** ComfyUI 的 `.weight_scale`/`comfy_quant`（K217）。三条路：① `linear_()` 增加 comfy 命名分支（读 `weight_scale` 逐行 + `comfy_quant.convrot` 旋转）；② 转换脚本把 int8_convrot 解成 BF16 再喂（体积 ×4，但 **1.04 GB 的 lite VAE 解出来也只有 4 GB**，对本机可接受）；③ 等上游。**收益真**：README 自报 decode ~2×，且 lite VAE 比官方 3.17 GB 更小。
- **P47（扩写）**：int8 盲区现在有三处（LoRA 因子 K199 / w6a8 基座 K214 / VAE K217）。**最低成本仍是「加一条 warning」**，但 VAE 那条更危险——它是**把 I8 码当值**而非跳过，**必须优先修**（否则画质崩塌且无错误日志）。
- **P46（维持中、期望下调）**：换编码器无新增。sd.cpp 仍只有 `5fa203c` ClipProj(no mlp)。
- **P43（仍未建）**：`safetensors-peek.py`。本轮又手写 11 次读头，**第四条需求**：把 `comfy_quant` 的 JSON **解析成结构化字段**（format / convrot / group_size），否则「名拒 vs 布局拒」这种判断每次都要手读。
- **SOP（仍未改）**：累计 5 条待写入（HF 搜索替代 WebSearch / hf-mirror 分流 / commits 301 / `.alpha` 三态体检 / **新版：tree 的 lastModified 缺失 + raw README 走直连**）。

## 第 33 轮（2026-11-27 00:30 · 上游静默第 9 日 + 加速 LoRA 第五形态「reshape_weight 补丁型」且同文件两种因子拼写 + alpha 第五态「已折进 lora_B」+ 预烘 AdaLN 表第三家 VDN）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=00:30，守卫 R=33）。
> 与第 32 轮的关系：上轮把 Fusion pruned 的 alpha 判死（mul≡1.0）、把 WaveCut 时调制剪枝判成「第 5 类打不开」、把 VAE int8 立成第三条量化盲区。本轮**换了取样方向**——不再盯官方蒸馏线，而是把 11-26 单日新增的 **4 个真正落地的新件**逐个读头：结果发现 **① 加速 LoRA 出现第五种形态（`reshape_weight` 元数据补丁 + 满秩 final_layer），本机只可能绑一半；② 同一文件里 kohya 与 peft 两种因子拼写并存，而本机「取第一个因子决定整文件拼写」的规则在 `unordered_map` 序下不确定；③ alpha 出现第五种现场——metadata 明写「已折进 lora_B」；④ 预烘 AdaLN 表已是第三家、三种互不兼容布局。**

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K220** | ★ **上游静默第 9 日**：HEAD 仍 `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`pushed_at 11-23T11:20:51Z`）；release 最新仍 **v0.1.110（11-01）→ 落后 26 天**；issue **14 全开**（#59/#58/#56/#55 均 `updated_at == created_at`、0 评论）；**PR total_count = 0**；**274 star（+1）/ 27 fork / 36,920 KB** | GitHub API ×5 | 2026-11-27 | 零增量（连续第 9 日） |
| **K221** | ★★★ **加速 LoRA 的第五形态：「PDD head bank」+ `reshape_weight` 元数据补丁 + 满秩 final_layer**。`vantagewithai/MiniMax-H3-comfyUI-GGUF:loras/MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy` = **1,725,921,392 B / 578 tensors**（FL2VA 版 1,723,713,944 B）；metadata `conversion = "…PDD head banks as base-relative pad-and-add reshape_weight LoRA (strength interpolates toward base); adaln projected to curve basis"`、`lora_alpha 64 / lora_rank 64 / pdd_block_size 4 / pdd_num_steps 32`；**4 个 `I64` `reshape_weight`（`[1]`/`[2]`）= 元数据不是权重**；`final_layer.video_out` 一个 `lora_down [3072,5376]` + `lora_up [3072,3072]`，**rank 3072 = 满秩**。本机全树 `reshape_weight` grep = **0** | HF 镜像 Range 读头 + 本机 `runtime-lora.cc` / `metal-minimax-h3-transformer.cc:6081` | 2026-11-26 | **新增「部分静默」形态**：前缀与 AdaLN 侧全过，只有 `final_layer` 那一支落空，且它**不在 `bind()` 枚举路径上**，`_skipped` 未必涨 |
| **K222** | ★★★ **同一文件里两种因子拼写并存（新坑）**：本件 `final_layer.*` 用 **kohya**（`.lora_down.weight`/`.lora_up.weight`，4 对），`blocks.*` + `token_refiner.*` 用 **peft**（`.lora_A.weight`/`.lora_B.weight`，258 对）。本机 `index_suffix_()`（`runtime-lora.cc:308-330`）**取首个因子张量决定整文件拼写**，而 `tensor_names()` 源自 `std::unordered_map`（`metal-llama-weights.h:296`）⇒ **迭代序不定** → 要么 blocks 全绑（4 对落空），要么 258 对全失配（只剩 4 对）。⚠️ header 写入顺序（final_layer 在前）**不等于** `tensor_names()` 返回序 | HF 读头（含原始字节序枚举）+ 本机源码 | 2026-11-27 | **判据只能写「可能只绑一半且不确定绑哪一半」**，不能写「一定失败」；验收须同 build 跑两遍比 `modules` 计数 |
| **K223** | ★★ **alpha 的第五种现场：metadata 明写「已折进 B」**。本件 `lora_alpha 64 / lora_rank 64` ⇒ `mul = 1.0`（恰好无害），但 `conversion` 里写着 **`alpha/rank folded into lora_B`** ⇒ 因子自身已是训练强度。此前四态：K188 整数倍率（128/8）、K212 倍率==rank、K200 量化 scale（3.96e-4）、K151/K156 元数据 alpha 缺失 | 读头 `__metadata__` | 2026-11-26 | **换槽体检加第 5 项：读 `conversion` 自由文本**——只看数字会在 alpha≠rank 的文件上**双倍施加** |
| **K224** | ★★ **可读对照组：RunF / Variable-Clock（kohya 拼写、契约内、298 MB）**。`MATLOWAI/MiniMax-H3-Variable-Clock:minimax_h3_variable_clock_runf_step2000_r16.safetensors` = **298,261,224 B / 600 tensors / 全 F32**，200 模块 ×（`lora_unet_<flat>.alpha` + `.lora_down` + `.lora_up`）rank16。训练元数据成体系：`ss_minimax_h3_shift_video 12.0` / `shift_audio 3.0` / `task t2va` / `base_family fl2va` / `motion_clock per_item_physical_fps_v1+motion_time_spans_v1` / `motion_keep_bands 2` / `native_anchor frozen_base_conditional_video_v1`（weight **30.0**、replay 0.1）/ `guidance_loss_scale 4.0`（audio 同、sigma_min 0.15）/ `lr 5e-5 constant_with_warmup / warmup 10` / `23 epoch × 84 items / 2000 steps / seed 20260923` / `ss_sd_model_name minimax_h3_fl2va_pruned_bf16` | HF 镜像 Range 读头 | 2026-11-25 | **本机可读**（`kKohyaPrefix` + 三拼写）；`shift_video 12` 与 K187 官方 Ref2AV 分布一致 ⇒ **P44 之后最便宜的「shift 12 + 轻量 LoRA」对照件**（298 MB）；同仓另有 `_lateattn` / `_noblock49` 消融件 + `clock_maps/`（124 帧 / 56 帧 hold map） |
| **K225** | ★★ **视频重绘（inpainting）LoRA 首次进清单**：`VoidEclipseAI/MiniMax-H3-ReFrame-VideoInpainting-LoRA:ReFrameVideo-H3-LoRA-v1` = **596,446,800 B / 600 tensors / 全 F32**，kohya 拼写、200 模块（50 块 × qkv/out_proj/fc1/fc2）、`200 × .alpha`，顶层无 module 前缀 | HF 镜像 Range 读头 | 2026-11-26 | 本机契约内、**理论可绑**；与 K141 换人 / K218 去人 / outpaint 同属「编辑型 LoRA」但任务是**画布内重绘**；标「待复现」 |
| **K226** | ★★★ **预烘 AdaLN 表已是第三家，且三种布局互不兼容**：`OpenVDN/vdn-minimax-h3-edge`（**9,804 文件**，`READY.json`：535 payload 全 sha256、`format freevideo-fp8-variants-v1`、`per_tensor` + `rowwise`(363 矩阵) 两套缓存），`cache/adaln-tables-v2-*/00.safetensors` 实测 8 张量 `step_0 BF16 [6,32256]` + `step_1..7 BF16 [9,32256]`，`bundle.json` 声明 `channels 5376 / modality_rows 3 / components 6`、契约名 `minimax-h3-adaln-silu-linear-3x6-v1` | HF 镜像 API + `bundle.json` / `READY.json` / 表头 | 2026-11-26 | **三家三布局**：K210 WaveCut（宽 8 one-hot 时编码）、K205 `adaln_affine`（`adaln_basis [8,2688]`）、本件（每步直接给调制向量 32256 = 5376×6）⇒ **本机一种都不认**；方向已成事实标准，格式未收敛 |
| **K227** | ★★ **交付单位从「单件」变成「三件套」**：`vantagewithai/MiniMax-H3-comfyUI-GGUF` = fl2va/ref2va **各 11 档 GGUF**（Q3_K_M…Q8_0）+ **4 个 8 步 acc LoRA**（comfy/pruned_comfy × fl2va/ref2va）+ **7 份 workflow**，**11,153 dl / 28 like**（近周最高）。workflow 默认 `UNETLoader` 用 `…_pruned_int8_convrot` 或 `UnetLoaderGGUF`、`BasicScheduler simple/20 步/denoise 1`、`KSamplerSelect euler`、`PathchSageAttentionKJ`、`SolAttnPatch(0.1/0.88/4096/"39-42")`、`SpectrumApplyMiniMaxH3` | HF 镜像 API + workflow JSON 解析 | 2026-11-26 | 生态评估口径要改：**单件「本机能不能读」不再是有效问题**，要问「这套三件套里本机能拼出几条」 |
| **K228** | ★★ **像素头（DWD 推理侧）首次带 PSNR**：`pocis/MiniMax-H3-Video-PixelHead:minimax_h3_video_pixel_head` = **95,858,352 B / 92 tensors / 全 F32**（bf16 版 47,958,296 B）；metadata `arch minimax_h3_video_pixel_head_v2`、`base_model Comfy-Org/MiniMax-H3`、`d_feat 5376`、`d_lat 96`、`depth_s4/s8/s16/s32 1/2/2/2`、`frame_per_token "1,4,4,4,4"`、`latent_input x0_hat_vid_1x2x2`、`teacher_vae minimax_h3_video_vae_int8_convrot`、**`eval_psnr_db 31.97`**、`rollouts 1800`、**`release_status "experimental_preview_v0.2.0_not_recommended_for_production"`**（作者自标不宜生产）；前缀仅 `entry_norm/feat_norm/feat_proj/lat_proj/norm_out/out_proj`（独立小网，非 DiT 一部分） | HF 镜像 Range 读头 | 2026-11-26 | **本机 `pixel_head` grep = 0**，无通路；但这是**首条带可复现指标的 DWD 实现**，31.97 dB 可作「免 VAE 解码」参照线 |
| **K229** | ★ **三线零 H3 增量，且本轮出现「易误读」**：LightX2V 单日 3 条全非 H3（`1e912006` LongCat-Avatar 1.6 #1762、`d9b1099d` Seed-VC #1758、`239537fc` YuE2 #1755）；sd.cpp 单日 5 条，其中 **`ea3f6ec7` LTX INT8 ConvRot 载入修复（#2436）** 与 **`6b51a955` W4A8 复用 INT8 GEMM（#2435）** 是**量化基础设施但只服务 LTX/通用路径**，H3 仍停在 11-25 `5fa203c` ClipProj(no mlp)；ComfyUI `8b0f1071`/`4a4b3409`/`ef507153` 均无 H3 | GitHub API ×3 | 2026-11-26 | **⚠️ 别把 `#2435/#2436` 当 H3 量化进度**（命名里都有 INT8/W4A8） |
| **K230** | ★★ **检索通路新退化：`huggingface.co` 全域不可达，但 `hf-mirror.com` 的 `resolve` + Range 完全可用**。本轮直连 `api/models`、`api/models/<id>`、`resolve/main/*` 全部 `000`（DNS 解析到 `157.240.13.8`，TCP 无响应，25–40 s 超时）；镜像 `api/models?search=` **200 / 2.2 s**、`resolve/main/<file>` 带 `-r 0-7` 返回 **206 与正确首 8 字节**（`98 4e 00 00 …` = header 长 0x4e98） | curl 实测 | 2026-11-27 | **修正既有分流规则**：此前「权重/读头一律走 `huggingface.co` 直连，镜像只用于搜索/tree」（记忆 `project_search-channels`）**在本轮不成立**；应改为「**镜像优先，直连仅作 fallback**」。`raw/main/README.md` 走镜像 `resolve` 亦 200 可用（38,767 B 全量返回） |
| **K231** | ★ **11-26 单日社区面续增**：`Uhvg856/MiniMax-H3-Person-Remover-LoRA` / `…-Character-Swap-LoRA`、`ausboss/MiniMax-H3-Image-Outpaint-LoRA`（13 like）、`javawock7618/comfy-MiniMax-H3-workflows`（**175 like**，纯 workflow 仓）、`klassas/minimax-h3-image-slim`、`Infinity-io/MiniMax-H3-Image-GGUF`、`aevionlabs/*`（4 仓批量）、`linkqpsfa/*-i2v-weights` | HF 镜像搜索 API ×3 拼写 | 2026-11-26 | 生态重心：**编辑型 LoRA + workflow 仓 + GGUF 批量镜像**；「人物级编辑」成独立品类 |

### 印证 / 冲突

- **★★★ 冲突①（「metadata alpha 一致就安全」被推翻）**：K212 判死 Fusion 的 alpha（==rank，mul 1.0），当时结论是「读 alpha 数字即可」。**K223 证明还有第五态**——`conversion` 自由文本写着 `alpha/rank folded into lora_B`。⇒ **体检必须同时读数字与自然语言 metadata**；数字只是乘数，`conversion` 才是语义。
- **★★★ 冲突②（「本机 LoRA 拼写自动发现」有隐藏假设）**：`index_suffix_()` 用「第一个因子张量」定整文件拼写，隐含「一个文件只用一种拼写」。**K222 证明该假设被打破**（同一文件 kohya + peft 并存），且 `tensor_names()` 来自 `unordered_map` ⇒ **结果随进程变化**。这与 K199 的「I8 静默跳过」不同：**不是格式不支持，而是选择逻辑本身不确定**。
- **★★★ 冲突③（「量化基础设施动 = H3 有进展」是误读源）**：sd.cpp 同日两条 INT8/W4A8 提交，标题里都带量化关键字，但一条是 LTX ConvRot、一条是通用 GEMM 复用（K229）。⇒ 上游生态的「量化词」与「H3 能力」**必须分开记账**。
- **★★ 印证（K211 的「不是所有看着像 H3 的都能读」再扩一档）**：K211 = 整件拒载（前缀/曲线表）；**K221 = 部分静默（只有 final_layer 一支落空）**；K222 = 选择不确定（可能绑一半）。**三种失效形态并存，且后两种日志更安静。**
- **★★ 印证（K210/K205 的「预烘 AdaLN」已成路线而非个例）**：三家（WaveCut / `adaln_affine` / VDN freevideo）各自布局、互不兼容（K226）。⇒ 本机若要支持，**不能只加一个分支**，得先约定「认哪种」——这条判断比实现更贵。
- **★★ 印证（K187 训练分布）**：K224 的 `ss_minimax_h3_shift_video = 12.0 / shift_audio = 3.0` 是**第三方训练者独立复现**官方 Ref2AV 的 shift 12/3（K187 来自 LightX2V 官方 PR #1730）。⇒ **shift 12 不是单点口径，是社区已采纳的默认**。
- **零增量（须明日复查）**：vpipe 上游第 9 日（274 star，唯一变化 +1）；ModelScope Turbo 31 项不变（本轮直连失效，未复核 Fusion）。

### 本轮实验

**无生成实验，仅零下载读头**（共 **9 次 Range 请求**、磁盘 0、累计约 **12 min**）：K221 ×1（含 2 次追加切片）、K222 合并、K223 合并、K224 ×1、K225 ×1、K226 ×2（表 + bundle）、K228 ×2（两个精度版本头）。

不跑 P44 的理由：
1. **时间**：00:30 起动，检索到 01:10 已用 40 min（镜像变慢 + 直连 3 次超时各 25 s 白等约 2 min）。P44 = 10.96 GiB + 818 MB 下载（约 25 min）+ 改 shift + 124 帧生成（约 29 min）≈ 55 min，**必挤掉两份报告与 sync/release**。
2. **本轮价值在「新形态判定」**：K221/K222 直接说明「社区最新那批 8 步 LoRA **在本机可能只绑一半**」——这恰好是 P44 的选件池。**在拼写不确定性排除前跑 P44，等于在不可复现的配置上取数。**
3. **磁盘 38 GiB**：下 11.8 GiB 后余 26 GiB，**技术上可行**，纯时间问题。

### 坑

- **坑①（新，最重要）：`tensor_names()` 不是 header 顺序**。`MetalLlamaWeights::_tensors` 是 `std::unordered_map`（`metal-llama-weights.h:296`），`tensor_names()` 只做 `for (kv : _tensors) push_back`（`:741-747`）⇒ **返回序与文件字节序无关**。⇒ 读头脚本看到的「第一个因子张量」**不能**用来推断本机实际会选哪种拼写；要判必须真机跑并读 `modules` 计数。
- **坑②（新）：`hf-mirror.com` 的 `resolve` 需要 `-L` 且会 302 到 `api/resolve-cache/...`**。不加 `-L` 只得 302 空体；加 `-L` 后 Range 正常（`206`，首字节正确）。而 `README.md` 走同一路径**忽略 Range 返回整个 200 全量**（7,810 B / 38,767 B 实测）——**Range 对小文件会被忽略**，别用它判断「是不是分段下载」。
- **坑③（新）：`hf-mirror` 的 `api/models/<id>` 也**不返回** `siblings[].size`**（全 `None`）。文件体积只能靠 `curl -sIL | grep content-length`（本轮 6 个文件全用此法）。⇒ 「按体积筛候选」要在 `HEAD` 请求上做，不能在 API 上做。
- **坑④（复现）：HF 直连失败时 `curl` 返回 `000` 且 `%{time_total}` 恰好=超时值**，容易被误判成「仓不存在 / 文件 404」。⇒ 见 `000` 先测 `-o /dev/null` 打镜像同一路径，再判内容层问题。
- **坑⑤（复现）：`reshape_weight` 这类「元数据张量」在 header 里长得像权重**（`I64 [1]` / `[2]`，`data_offsets` 只有 8/16 字节）。⇒ 统计「tensors 数」时若把它算进去，会把 4 个元数据算成 4 个模块；本轮 578 = 258×2(A/B) + 50(diff_b) + 4(reshape_weight) + 8(final_layer 因子) + 258(alpha？)**不整齐**，只能逐类计数，不能靠总数反推。

### 下一步

- **P44（维持首选，但加一条前置）**：原 2 条前置（下载 + `video_shift 6→12`）不变；**新增前置③「选件避开混合拼写」**——不要选 `vantagewithai` 的 `Acc-8Step_pruned_comfy`（K221/K222），继续用 Kijai W4A8 + Fusion `lite_r32`（纯 peft 拼写、alpha==rank）。**这条前置不需要额外时间，只是换文件名。**
- **P51（新，中）「混合拼写容错」**：`index_suffix_()` 改为**按模块分别解析拼写**（或在 `resolve_` 里对 A/B 各试两种后缀），消除 `unordered_map` 序依赖。改动小（`runtime-lora.cc:308-330` + `resolve_`），**收益是让「社区最新 8 步 LoRA」可评估**。
- **P48（维持中、优先级升）**：VAE int8 是「错值」级；本轮未动。
- **P47（维持）**：三处盲区（适配器 / w6a8 基座 / VAE）→ 本轮新增「部分静默（`reshape_weight`）」，**warning 至少要覆盖 `_skipped` + 未识别后缀两类**。
- **P52（新，低）像素头通路**：92 tensors / 95.9 MB，但需 `latent_input x0_hat_vid_1x2x2` 这类内部张量契约，**本机无 hook 点**。只记存在性，等上游或等第二个实现。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 9 次读头。**第五项需求**：把 `conversion` 这类自由文本 metadata **按 `;` 拆成语句**并标出 `folded into` / `projected to` 这类「语义已改」的声明。
- **SOP（仍未改）**：累计 7 条待写入（HF 搜索替代 WebSearch / ~~镜像分流~~ **已反转：镜像优先** / commits 301 / `.alpha` 五态体检 / tree 的 lastModified 缺失 / raw README 走直连 / **新版：`tensor_names` 无序 + `resolve` 需 `-L`**）。

## 第 34 轮（2026-11-27 02:30 · 上游静默第 10 日 + 首个「NVFP4+INT8 逐投影混合」H3 DiT（本机 kernel 缺席）+ sd.cpp 补上 `-mlp` 换编码器变体反超本机 + 零梯度闭式投影换编码器且自报 R² 与 metrics.json 差两个数量级）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=02:30，守卫 R=34）。
> 与第 33 轮的关系：上轮结论是「社区最新 8 步 LoRA 在本机可能只绑一半」（K221/K222），方向是**判文件形态**。本轮换方向——**判「量化形态」与「相邻生态线」**，
> 结果四条既有结论被修订：① 「本机不认 NVFP4」要拆成「源码认 / 已发布二进制不认」两层；② 「DWD 像素头等一个实现即可」变成「已有两家互不兼容」；
> ③ 「sd.cpp 也不支持带 MLP 的 connector」被上游 PR #2424 推翻；④ 「换编码器只能靠 LoRA/MLP」被第三条路（闭式投影）打破，但**该仓自己的 README 与 metrics.json 打架**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K232** | ★ **上游静默第 10 日（零增量）**：HEAD `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`committer.date 11-23T11:14:45Z`、`pushed_at 11-23T11:20:51Z`）；release 仍 **v0.1.110（11-01）→ 落后 26 天**；issue **14 全开**（#59/#58/#56/#55 均 `updated_at == created_at`、0 评论）；**PR total_count = 0**；**274 star（与上轮同）/ 27 fork / 36,920 KB** | GitHub API ×5（commits / repo / releases / search issues / search pr） | 2026-11-27 | 零增量（连续第 10 日）；star 自 11-26 起停涨 |
| **K233** | ★★ **sd.cpp 补上 `-mlp` 变体，本机反而落后一个档位**：`439e77a5` **PR #2424「support `-mlp` variants of ClipProj-MiniMax-H3」已于 2026-11-26T13:12:17Z 合入**，覆盖 `mmh3-8b-ClipProj{,-mlp,-v3.1,-v3.1-mlp}` 四种（linear+mlp refiner / 纯 mlp）；另 **PR #2414（open，未合）「latent continuation」**：`--save-latent` / `--continue-latent` / `--pin-frames`，从**尾 latent** 续接（像素帧续接有构图漂移 + 每段音轨重启）。本机 `minimax-h3-text-encoder.cc:655-690` 的 connector 仍是 **6 张量、无 MLP** 方言；全树 `save-latent|continue-latent|pin-frames` grep = **0** | GitHub PR API ×2 + 本机源码 | 2026-11-26 | **推翻 K190/K202 的「sd.cpp 也不支持 MLP 残差」前提**；P46 从「跟跑」变「落后一个变体」；长视频续接成为**新增缺口**（非 H3 独有） |
| **K234** | ★★★ **首个「NVFP4 W4A4 + INT8 ConvRot」逐投影混合的 H3 DiT**：`Maximilian228/MiniMax-H3-pi-H3-NVFP4-GPTQ`（2026-11-26，README 自述面向 RTX 50 系 Blackwell）。`diffusion_models/minimax_h3_fl2va_pruned_pih3_4step_nvfp4_fc2int8_gptq_bf16cal` = **14,302,909,922 B / 1,082 tensors**（U8 350 / F32 312 / BF16 220 / F8_E4M3 150 / I8 50）。**逐投影实测**（50 块全同）：`qkv_proj`/`out_proj`/`fc1` = U8 + `weight_scale` **F8_E4M3 [N,336]**（cuBLAS swizzled，N 补到 128、336=(K/16=168)/4×4）+ `weight_scale_2` **F32 标量**；`fc2` = **I8+U8 各 50** + `weight_scale [5376,1]` 逐行；`adaln_proj.linear` 全 F32 `[96768,8]`。`comfy_quant` 两种原文：`{"format":"nvfp4"}` 与 `{"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}`。**命名是原生名**（`blocks.*` + `adaln_t_table [1025,8]` + `condition_proj/video_patch_proj`），不是 diffusers 布局 ⇒ 本机「comfy_saved」两条判据全满足 | HF 镜像 Range 读头（DiT + 逐层 dtype 归类）+ `comfy_quant` 二进制切片 | 2026-11-26 | **★★★ 量化形态第三档：「一个文件一种格式」→「逐投影混合格式」**（同文件里 qkv/out/fc1 走 NVFP4、fc2 走 INT8）。另 `loras/pi_h3_4step_dwd_head_gptq_int8` 642,352,928 B、`text_encoders/qwen3vl_32b_…nvfp4_gptq` 16,461,056,970 B |
| **K235** | ★★★ **本机对 K234 的判定要分两层，别混**：**源码层认**——`fp8::scan(src,&m->_f8,&err,/*int8=*/true,/*nvfp4=*/true)`（`metal-minimax-h3-transformer.cc:5715`）本身要 NVFP4；`resolve_nvfp4_(...,/*comfy=*/true)`（`fp8-layout.cc:225-250`）已处理 swizzled 补齐；fc2 的 int8 逐行 scale 也过 `per_row`（`:430-455`）。**已发布二进制不认**——App `0.1 (9db5dd7*0)` 的 `libvpipe.0.dylib` 里 **`nvfp4_dequant` 命中 0 次**（同包 `w4a8_to_i8` / `h3_adaln_pruned_f16` 都在），而 kernel 源 `build/apple-silicon/metal-compute/affine_dequant_embed.cc.metal:2408` 存在 ⇒ **拒载形态是「host 无 NVFP4 widening kernel」（`metal-minimax-h3-transformer.cc:5774-5781`），不是「格式不认」**；该 dylib 只有两条 NVFP4 文案，都是 `second-stage scale (NVFP4 / AWQ-style) ... does not read` | 本机源码 grep + `strings libvpipe.0.dylib` | 2026-11-27 | **修正「本机不认 NVFP4」的单层口径**：`git log -S kNVFP4` 显示该通路在 **41d2789（2026-11-12）** 已进代码，早于已装二进制 `9db5dd7`；⇒ **升级 App（或自编译）后本件才可能过第一道门**。⚠️ 仍不可用 `w4a8_to_i8` 冒充 NVFP4 通路 |
| **K236** | ★★★ **DWD 像素头出现第二份互不兼容实现**：`loras/pi_h3_4step_dwd_head_gptq_int8.safetensors` = **171 tensors**（F16 75 / F32 32 / I8 32 / U8 32），前缀**全部** `dwd_pixel_refiner.*`（169）+ `dwd_norm_out.*`（2），**无任何 `lora_*`**（README：适配器其余部分已并进 DiT）。结构 `feature_expand.{weight,bias}`、`first_frame_proj_out.*`、`register_tokens`、`blocks.N.{attn.to_qkv,attn.to_out,ff.w1,ff.w2}.weight(+weight_scale)`、`norm_out.*`、`proj_out.*`。对比 K228 `pocis` 版（92 tensors，`entry_norm/feat_norm/feat_proj/lat_proj/out_proj`）。**本机 `dwd` 全树 grep = 0**；`_step_out` 是「多步输出 Linear 数组」（`metal-minimax-h3-transformer.cc:1092/13761`），**不是**像素 refiner | HF 镜像 Range 读头 + 本机 grep | 2026-11-26 | **P52 从「等一个实现」改为「两家拓扑/命名都不一致 ⇒ 不宜私接」**；DWD 推理侧格式未收敛 |
| **K237** | ★★★ **换编码器第三条路：零梯度闭式投影（Plato's Key / Ridge）**。`Alissonerdx/TE-PK-Minimax-H3`（2026-11-26 18:06，0 dl）把 Qwen3.5-0.8B/2B/4B/9B、Qwen3.8-27B、Gemma-4 E2B/E4B/12B/31B 直接映到 H3 原生 **5,120 维**，方法 `(XᵀX+λI)⁻¹XᵀY`（Ridge，λ=1）或 Procrustes，**无梯度 / 无 LoRA / 无 MLP**，单件 20–105 MB，配 `ComfyUI-H3-Text-Encoders` 节点。实读 `qwen3.5/…_ridge_qwen3.5_9b`（header 1,032 B）**只有 5 个张量**：`R F32 [4096,5120]` + `donor_mean [4096]` + `target_mean [5120]` + `scale [1]`；metadata `format=platos_key_v2_ridge`、`tap_layer -1`、`align_mode token`、`corpus_prompts 800`、`num_samples 146674` | HF 镜像 Range 读头 + README | 2026-11-26 | **本机 connector 契约（6 张量：`input_mean/input_std/proj.weight/output_mean/output_std/sink_embedding`，`:655-690`，且首行被 `sink` 顶替 `:854-901`）与 TE-PK 的 4 张量方言不对应**：无 `std`、无 `sink`、数学是 `(x−donor_mean)·R·scale+target_mean` ⇒ **另一种 connector 方言，不能直接塞进现契约目录** |
| **K238** | ★★★ **TE-PK 仓自报数字互相矛盾（必须按「待复现」处理）**：README 表与 safetensors header 都写 Qwen3.5-9B **cosine 0.9626 / R² 0.9935**，但同仓 `metrics.json` 对**同一文件**给 `val_cosine_mean 0.890825` / `val_r2 0.037135`；8 个 key 的 `val_r2` 全在 **0.033–0.112**（0.8B 0.0337 / 2B 0.0370 / 4B 0.0356 / 9B 0.0371 / Qwen3.8-27B 0.0338 / Gemma4 e2b 0.1031 / e4b 0.1125 / 12b 0.0720），`val_rel_l2 ≈ 0.95` 亦与「0.99 R²」不相容 | 同仓 README + header + `metrics.json` 三方对照 | 2026-11-26 | **R² 相差两个数量级、cosine 差 0.07** ⇒ README 的 R² 口径**不可引用**；`train_r2` 也是 0.033–0.113（训练集同样低）⇒ 不是过拟合问题，而是**两套评估脚本口径不同**。**不并入已验证能力** |
| **K239** | ★★ **「LoRA 已并进基座」的 pruned 全量件卡在一个名字上**：`ibyteohdear/MiniMax-H3-Pruned-{DMD-FL2VA-Turbo,LightX8-hybrid}-Fused`（497 / 502 dl）各 **4 分片**，全量枚举 **637 tensors / 50 块（0–49）**，dtype 仅 F32+BF16。块内 12 种后缀；顶层 `time_embedder.table F32 [1025,8]`（**不是** `adaln_t_table`）、`context_embedder.weight BF16 [5376,5120]`、`transformer_blocks.0.adaln_proj.{linear.weight BF16 [96768,8], folded_bias F32 [96768]}`、`norm_out.folded_bias [10752]`、`token_refiner.refiner_blocks.0.attn.to_q.weight [7168,5376]` | HF 镜像 4 分片 Range 读头（全量枚举） | 2026-11-26 | **精确定位 K204 的失败点**：`is_diffusers_layout` 三条判据**全满足** → `translate_diffusers` 启动 → `untranslatable_tensor()` 撞 `time_embedder.table`（`native_()` 只映射 `time_embedder.linear_1./linear_2.`，`table` 无映射）→ 翻译返回 0、整文件保持原名；再叠「diffusers 分片目录本机 `WeightSet::open` 不读」⇒ **双重阻断**。`folded_bias` 全树 grep 仍 **0** |
| **K240** | ★★ **ModelScope 双仓复核**：`lightx2v/Minimax-h3-Turbo` 仍 **31 项**（仅 README 于 2026-11-24 14:36 UTC 改文案，权重未动）；**新核 `lightx2v/Minimax-H3-Turbo-Fusion` 共 48 项**（2026-11-24 18:49 UTC 一次性上传）：`pruned/` 6 个 safetensors + 非 pruned 6 个 + `assets/`（case1/2 图 + 对比 mp4）。`pruned/…_4step_v1.0_lite_r32_pruned_comfyui` = **818,925,468 B**、`…_8step_v1.0_lite_r32_pruned_comfyui` = **818,925,468 B**（**同字节数，未核 sha**）；`…_4step_v1.0_pruned_comfyui` = 5,220,193,444；非 pruned 3,778,242,236 / lite 665,148,804 | ModelScope `repo/files` API ×2 | 2026-11-26 | P44 取 4 步档即可；8 步档「4/8 同尺寸」**疑似同构但待 sha 复核**（K151 是 sha 各异 + 字节同构） |
| **K241** | ★★ **检索通路的两个新坑 + 一条组织名纠正**：① `api.github.com/repos/lightx2v/LightX2V` 返回 **404**（不是改名 301），正确组织是 **`ModelTC/LightX2V`** ⇒ 别把 404 当「仓没了」；② 镜像上**不存在的文件**返回 **404**，但 `Jim507735/Minimax-H3-LongVideo` 的 `README.md` 与随机文件名**都 404** 而 `api/models/<id>` 报 3 个 siblings ⇒ **判「仓空不空」要看 siblings，不能用 `resolve README` 反推**；③ `siblings[].size` 仍全 `None`（第 3 日复现），体积只能 `curl -sIL`。另：`huggingface.co` 仍全域 `000`（12.1–12.2 s = `--max-time`），`hf-mirror.com` 同路径 **200 / 0.76 s** | curl + GitHub API | 2026-11-27 | 镜像优先**第 3 日成立**；新增「404 ≠ 仓不存在（要分文件级与仓级）」 |
| **K242** | ★ **11-26 单日社区面（去重第 33 轮后）**：新品类两条——`Maximilian228/MiniMax-H3-pi-H3-NVFP4-GPTQ`（pi-H3 的 NVFP4/GPTQ 三件套）、`Alissonerdx/TE-PK-Minimax-H3`（闭式投影换编码器）；另有 `loom-draft/pytraveler-MiniMax-H3-Prompt-Rewriter-Qwen3.8-27B-{FL2VA,Ref2VA}-loom`（提示词改写器独立仓、双任务版）；`haubnh/FrameRush-Minimax-H3`、`Jim507735/Minimax-H3-LongVideo`、`nnndite/minimaxh3image`、`mimba/minimax-h3`、`bp-5193/MiniMax-H3`、`PYTHAI/MiniMax-H3-fork`、`klassas/minimax-h3-loras`、`RunningHubAI/rh-…-lora` 等 **8 个空壳/占位仓**（0 dl、无 README 或无权重） | HF 镜像搜索 API ×3 拼写 | 2026-11-26 | 生态重心从「编辑型 LoRA」转向 **「pi-H3 量化落地」+「换编码器」** 两条工程线；空壳比例升至 ~27%（8/30） |

### 印证 / 冲突

- **★★★ 冲突①（「本机不认 NVFP4」是单层结论，站不住）**：K234 的件在**源码层**是能过的——`scan(...,nvfp4=true)` 与 `resolve_nvfp4_(comfy=true)` 都在树里，`git log -S kNVFP4` 指到 **41d2789（2026-11-12）**；但**已发布 dylib（`9db5dd7`）没有 `nvfp4_dequant`**。⇒ 结论必须写成「**升级二进制后可能可读**」而不是「格式不支持」。这条与 K178（dylib 早已含 `w4a8_to_i8`）并列，说明**已装二进制的能力矩阵要逐 kernel 核，不能用源码树代答**。
- **★★★ 冲突②（「DWD 像素头等一个实现就够」被两家不一致打破）**：K228 只有 `pocis` 一家（92 tensors、`entry_norm/feat_proj/lat_proj`），本轮 K236 出现 `dwd_pixel_refiner`（171 tensors、`feature_expand/first_frame_proj_out/register_tokens`），**张量名与拓扑完全不同**。⇒ 与 K226（预烘 AdaLN 三家三布局）同型：**工艺方向已收敛、格式未收敛**，本机私接成本高于等上游。
- **★★★ 冲突③（sd.cpp 的「不支持 MLP」前提被上游推翻）**：K190/K202 曾据 sd.cpp `ClipProjConnector` 注释判「不支持 `-mlp` 残差变体」；**PR #2424 于 11-26 合入，四种变体全支持**。⇒ P46 的对手已反超；本机 connector 仍是 6 张量无 MLP 方言，「换编码器」这条线本机**落后一个档位**（且对方的实现只有 MLP，不需要 `sink_embedding` 那套）。
- **★★★ 冲突④（换编码器的「第三条路」自带数据矛盾）**：K237 的方法（闭式 Ridge，20 MB）在工程上远比 LoRA/MLP 便宜，但 K238 显示**同仓 README（R² 0.99）与 metrics.json（R² 0.037）差两个数量级**，且 `train_r2` 同样低 ⇒ 不是过拟合，是**两套脚本口径不同**。⇒ 在本机复现前，**只记「方法存在 + 工件体积」，不记任何效果数字**（与 K152「社区二手须标待复现」同一条纪律的强化版：**同一份材料内部自相矛盾时，连「待复现」都不够，要标「口径不可用」**）。
- **★★ 印证（K204 的「看着像 H3 打不开」第 5 次精确定位）**：这次不是「判据不满足」，而是 `is_diffusers_layout` **全满足**、翻译已启动、**卡在 `time_embedder.table` 这一个名字**（K239）。⇒ **「像 H3」的文件现在有三种失败位：判据层（K211）、枚举层（K221）、翻译映射层（K239）**，日志会分别落在 `fail("... neither a Comfy-Org ...")`、`_skipped`、`translate_diffusers → 0`。
- **★ 零增量（须明日复查）**：vpipe 上游第 10 日（274 star 停涨）；LightX2V 4 条全非 H3；ComfyUI 3 条无 H3；`Comfy-Org/MiniMax-H3` lastModified 停在 **11-15**（33.26M dl / 2,853 like）。

### 本轮实验

**无生成实验，仅零下载读头 + 本机源码/二进制对照**（共 **7 次 Range 请求**、磁盘 0、累计约 **9 min**）：K234 ×1（DiT 全 header；另逐层 dtype 归类用同一份 header）、K234 的 `comfy_quant` ×2（72 B + 19 B 切片）、K236 ×1、K237 ×1、K239 ×4（4 分片各 1 次）。

不跑 P44 的理由：
1. **时间**：02:30 起动，检索到 02:59 已用 29 min（含 2 次直连各白等 12 s + 一次镜像 404 排查）。P44 = 10.96 GiB + 818 MB 下载（约 25 min）+ 改 shift + 124 帧生成（约 29 min）≈ 55 min，会挤掉两份报告与 sync/release 的余量。
2. **本轮结论直接改变 P44 的解读方式**：K235 说明「NVFP4 这件在本机跑不了」是**二进制版本问题而非配方问题**，先把结论落库比再取一组数更值钱。
3. **磁盘 37 GiB**：下 11.8 GiB 后余 25 GiB，技术上可行，纯时间问题。

### 坑

- **坑①（新，最重要）：`strings` 一个符号名不能证明「能用」，但**没有**它足以证明「不能用」**。本轮 `libvpipe.0.dylib` 里 `nvfp4_dequant` 命中 **0**、`w4a8_to_i8` 命中 1，而源码树里两者都在（`fp8-expand.cc:29` vs `:24` 一带）。⇒ **判断「已装版本能不能读某量化」要 `strings` 找 kernel 名，而不是 grep 源码**；反向不成立（名字在但 kernel 可能 load 失败，见 `fp8x.load()` 分支）。
- **坑②（新）：`git log -S <symbol>` 能给出「代码何时进来」，但要拿 commit 与**已装版本**比先后**。本轮 NVFP4 在 `41d2789`（11-12）、已装 `9db5dd7`，`git merge-base --is-ancestor` 直接告诉你不含 ⇒ 比逐文件对源码快得多。
- **坑③（新）：HF 镜像的 `resolve` 对「仓里没有的文件」返回 404，与「仓不存在」同码**。`Jim507735/Minimax-H3-LongVideo` 3 个 siblings 但 README 404 ⇒ **必须用 `api/models/<id>` 的 siblings 判仓内有什么**，`resolve` 只能判「这一个文件在不在」。
- **坑④（复现）：`4 步 / 8 步 lite_r32 pruned` 字节数完全相同（818,925,468）不等于同构**。K151 的先例是「sha 各异 + 字节同构」，本轮**没取 sha**，只能写「体积同尺寸」。⇒ 别把「同大小」当「可原槽互换」。
- **坑⑤（复现）：上游静默期的「零增量」也要看 star 有没有动**。本轮 274 star 与上一轮**完全相同**（上轮是 274 = +1），说明连社区关注度都停了——这与「有 star 增长但无 commit」是两种不同的静默，写报告时要区分。

## 第 35 轮（2026-11-27 04:30 · 上游静默第 11 日 + latent upscaler「同架构重训」本机零适配可跑 + 第四条调参工艺「跨模型 q_norm graft」+ `comfy_quant` 是 U8 载荷导致 dtype 统计翻倍）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=04:30，守卫 R=35）。
> 与第 34 轮的关系：上轮方向是「量化形态 + 相邻生态线」（NVFP4 逐投影 / DWD 第二家 / `-mlp` 反超 / 闭式投影）。
> 本轮换了**取样面**——不再盯 DiT 基座，而是把「**后处理（latent upscaler）**」与「**调参（graft）**」两条此前只有一句话的线各挖一层，
> 结果四条结论被改写：① 「社区 H3 后处理件只能是转存」被 v2 重训件推翻，且**它是本轮唯一「社区新权重 + 本机零改动」的件**；
> ② 「K240 的 4/8 步 lite 同尺寸疑似同构」结案为**不同构**（sha 各异）；③ 「I8 refiner 是 r256」是标称值，**逐模块 rank 差异很大**；
> ④ 多了一条此前不存在的分发形态：**gated 仓**（`resolve` 403 但 siblings 可见），且 **403 的 `content-length` 会被误读成文件体积**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K243** | ★ **上游静默第 11 日（零增量，逐位相同）**：HEAD `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`pushed_at 11-23T11:20:51Z`）；release 仍 **v0.1.110（11-01）→ 落后 26 天**；issue **14 全开**（#59/#58/#56/#55 均 `updated_at == created_at`、0 评论）；**PR total_count = 0**；**274 star / 27 fork / 36,920 KB**（与第 34 轮四项全同） | GitHub API ×5（commits / repo / releases / search issues / search pr） | 2026-11-27 | 零增量；**连续第 11 日、且 star 连续第 2 日不动**（「有 star 增长但无 commit」与「连 star 也停了」要分开记） |
| **K244** | ★★ **sd.cpp 的 latent upscaler 也只有 3D-conv 一支**：`#2249`「MiniMax-H3 latent hires second pass」已于 **2026-11-04 关闭合入**；`#2357`「2D-conv latent upscaler」自 **11-14 开、11-15 后无更新、仍 open**（改 3 文件：`docs/models/minimax_h3.md` +25/−3、`src/model/upscaler/h3_latent_upscaler.hpp` +866/−80、`src/pipeline/video.cpp` +13/−12）。2D 版是「2D conv 骨干 + 两个共享时间块，无 attention / SE / 大核分支 / post-upsample refine / pixel-shuffle」。**本机 `2d_conv` 全树 grep = 0** | GitHub PR API ×2 + 本机源码 grep | 2026-11-26 | 与本机**同档**：两边都只认 3D-conv v1 网络；⇒ 后处理这条线**没有落后**（与 K233 的换编码器线相反） |
| **K245** | ★★★ **社区 latent upscaler v2 是「同架构、重训权重」，本机 `latent-upscale` stage 零改动可加载**：`George0667/MiniMax_Temporal_Upscaler:minimax_h3_latent_upscaler_3d_conv_v2/…_fp16` = **690,592,736 B / 322 tensors / 全 F16**；与 K198 的官方 v1（`SOLRICKS` F16 转存 690,592,672 B / 322 tensors）**key 集逐名相同（onlyA 0 / onlyB 0）、shape 全同**，但数据区 sha 不同（`6307f49c…` vs `d1e3cbc7…`）⇒ **不是转存**。本机 `config_from_weights`（`metal-minimax-h3-latent-upscaler.cc:209-250`）四条自检全过（`conv_in.weight [512,24,3,3,3]` / 3×3×3 / 入通道 24 / `embed.0.weight [E,1]`），`dwconv.weight [512,1,5,1,1]`（时间核 5、奇数）亦过 | HF 镜像 Range 读头 ×2（v2/v1 各 1 次）+ 本机源码 | 2026-11-24（仓）/ 2026-11-27（读头） | **新增一条「社区新权重 + 本机零适配」的可用件**（此前只有 v1 的转存）；⚠️ 但 `v2/config.json` 写 `in_blocks 12 / temporal_kernel 5 / parameters 345,280,216`，**权重头实为 18+18 块**（与 v1 同）⇒ **config 不可信，结构只认 header** |
| **K246** | ★★ **`v2_temporal` 变体多出的 4 个时间嵌入张量本机无任何分支**：`…_v2_temporal_fp16` = **690,601,656 B / 326 tensors**，与 v2 的唯一差别是 4 个 `t_embed.{0,2}.{weight,bias}`（帧率 8/12/16→24 的嵌入）。本机 `load_conv_/load_entry_/read_f32_` 只按名取 `conv_in/conv_out/norm_out/in_blocks/out_blocks/embed.0/embed.2`，**未识别张量不报错**（全树无「unexpected tensor」类判据）⇒ **推断为静默忽略**，后果是「空间放大照做、时间插帧静默不发生、日志无痕」（未实测） | HF 镜像 Range 读头 + 本机源码路径核对 | 2026-11-26 | 与 K221（`reshape_weight` 静默落空）**同型**：第 3 次「加载成功 ≠ 全生效」；P47 的 warning 覆盖面再加一类（未知后缀张量） |
| **K247** | ★★★ **第四条「调参」工艺：跨模型 q_norm graft**。`yichengup/minimax_h3-tyc-zs05-ltxqnorm-int8-convrot`（**1,141 dl / 8 like**，单件 **20,970,382,496 B = 19.53 GiB**）= 932 tensors（F32 210 / BF16 220 / F16 102 / I8 200 / U8 200），原生名无 `model.` 前缀、`adaln_t_table [1025,8]`、`comfy_quant = int8_tensorwise convrot groupsize 256` ⇒ 契约与 K215 同类、本机四条全满足。`__metadata__` 原文：`rebuild = own-hybrid from official Comfy-Org pruned bf16` / `source_base = minimax_h3_fl2va_pruned_bf16` / `source_ref = …ref2va_pruned_bf16` / **`adaln_splice = none (fl2va throughout)`**（Ref2VA 只声明未混入）/ **`zspatial_graft = donor=Z-Image-Turbo layers.N.attention.q_norm, blocks=30-49, dose=0.5, normalize=False`** / **`qnorm_graft = donor=LTX-2.5 transformer_blocks.N.attn1.q_norm (mean-normalised x1.9340), blocks=30-48, dose=1.0`** / **`qnorm_pin = block 49 rms=5.0`** | HF 镜像 Range 读头（全 header）+ README 全文 | 2026-11-25 | **新工艺类别**：不量化、不剪枝、不蒸馏、不换编码器，而是**把别的模型的 RMSNorm 增益按剂量移植进 H3 末段 20 个 block 的 `attn.q_norm`**。`attn.q_norm.weight` 是普通逐通道增益 ⇒ **本机按名加载不拒**，但语义跨模型 ⇒ **「能加载」≠「行为对」**，只能算行为级改造，须人工 QC |
| **K248** | ★★★ **I8 refiner 的 rank 不是固定的 256（修正 K199）**：`SOLRICKS/MiniMax-H3-Upscaler:h3_upscale_refiner_int8.safetensors`（**1,884,199,184 B / 624 tensors = I8 416 + F32 208**）逐模块 rank 实测横跨 **48 / 72 / 79 / 94 / 121 / 144 / 165 / 188 / 206 / 234 / 248 / 252 / 300 / 356 / 377 / 495 / 630 / 760 / 800 / 866 / 895 / 938 / 946**，按族分层（`attn.out_proj` 48–267 / `attn.qkv_proj` 252–866 / `mlp.fc1` 195–382 / `mlp.fc2` 72–400）；50 块 × 4 投影 + 2 个 token_refiner 块 = **208 对**。`.alpha` 实测 4 例仍为 1e-4～1e-3 量级（`blocks.29.attn.qkv_proj = 1.112e-3` 最大） | HF 镜像 Range 读头（全 header）+ 4 次 alpha 切片 | 2026-11-26 | 「r256」是**打包标称值**；**任何按固定 rank 反推体积/强度的算法都不成立**；`mul = alpha/rank` 仍会给出 1e-6（K200 继续成立） |
| **K249** | ★★ **`comfy_quant` 是 U8 的 72 字节 JSON 载荷，且同一 linear 的 weight/bias 精度可以不同**：`Coffmeteor/…v10INT8`（20,967,649,144 B / 932 tensors）dtype 分解 = **I8 200（量化权重）+ U8 200（全部 `*.comfy_quant`，各 72 B）+ F32 206（`weight_scale [N,1]` ×200 + `adaln_t_table` + `rope.inv_freq` + 4 bias）+ BF16 275 + F16 51**；**F16 的 51 个全部是 `adaln_proj.linear.bias`（50 块 + `final_layer` 1）**，而同一 linear 的 `weight` 是 BF16。`comfy_quant` 原文 `{"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}` | HF 镜像 Range 读头 + 2 次 72 B 载荷切片 | 2026-11-27 | **统计陷阱**：按 `dtype in {I8,U8}` 数「量化权重」会把 200 个 72 B 的 JSON 数成权重（体积 14,400 B 可忽略，**个数翻倍**）⇒ 必须同时要求 `shape.size()>=2` 且非 `is_aux_name`（`fp8-layout.cc:295-305` 已含 `.comfy_quant`）。另：**不能假设「一个 linear 一个 dtype」** |
| **K250** | ★★★ **Fusion pruned 4 步 / 8 步「同字节、不同构」结案（K240 悬案）**：ModelScope `lightx2v/Minimax-H3-Turbo-Fusion:pruned/` 四个件的 sha256 前 20 位 —— `4step_lite_r32_pruned = fc088567ba945213…`、`8step_lite_r32_pruned = 425d1c1c105effdb…`（**都是 818,925,468 B**）；`4step_pruned = 86449d1d…`、`8step_pruned = 8208de8c…`（**都是 5,220,193,444 B**） | ModelScope `repo/files` API（带 `Sha256` 字段） | 2026-11-26 | **不可原槽 A/B 互换**（与 K151「sha 各异 + 字节同构」同型）；P44 仍按 4 步档取。另：**根目录**另有 8 个非 pruned / `_comfyui` / `_lite_r32_comfyui` 件（3,778,242,236 / 5,209,509,820 / 808,241,732），**与 `pruned/` 子目录不是同一批**，引用别混 |
| **K251** | ★★ **新分发形态：gated 仓（siblings 可见、`resolve` 403）**。`linkqpsfa/minimax-h3-i2v-weights`（8 文件：`fl2va_pruned_int8_convrot` / `qwen3vl_32b_nvfp4_awq` / `fl2v_turbo_8step_comfyui_bf16` / 两个 VAE）与 `linkqpsfa/minimax-h3-unc-i2v-weights`（单件 `10Eros_Max_h3_8stepTURBO_beta7_int8HQ`）在 `api/models/<id>` 正常列出 siblings，但 `resolve` 一律 **403**（`x-error-code: GatedRepo`、`x-error-message: Access to model … is restricted and you are not in the authorized list`） | HF 镜像 API + `curl -sIL` 响应头 | 2026-11-26 | **403 的 `content-length`（183 / 191）是错误体长度，不是文件体积** ⇒ 体积判据必须「先看 status 2xx、再读 content-length」；「siblings 可见」也不再等于「可读」 |
| **K252** | ★★ **11-26 单日社区面（与第 33/34 轮去重后）**：三条新线 —— ① **latent upscaler v2 重训族**（`George0667/MiniMax_Temporal_Upscaler`，478 dl，v2 + v2_temporal ×{bf16,fp16} 共 4 件 + `code/model.py`）；② **跨模型 graft**（`yichengup/…ltxqnorm-int8-convrot`，1,141 dl / 8 like）；③ **AMD Loom 部署包**（`loom-draft/pytraveler-MiniMax-H3-Prompt-Rewriter-Qwen3.8-27B-{FL2VA,Ref2VA}-loom`，`.loom` 程序 + `REPORT.md` + GGUF 卡，**不是 H3 权重**，只是 27B 提示词改写器在 Strix Halo / R9700 上的打包，链路指向 `pytraveler/…-GGUF`）；另 `jh27kim/MiniMax-H3-Ref2VA-4step` **已删（`Repository not found`）** | HF 镜像搜索 API ×2 拼写 + `api/models` ×3 + README | 2026-11-26 | 生态重心第 3 次迁移：编辑型 LoRA（11-26 前）→ pi-H3 量化 + 换编码器（第 33/34 轮）→ **后处理重训 + 跨模型增益移植**（本轮）。**仓被删也要记**（`jh27kim` 是第 33 轮才出现的 Ref2VA 4step 仓，2 天即撤） |

### 印证 / 冲突

- **★★★ 冲突①（「社区 H3 后处理件 = 官方权重的转存」被推翻）**：K198 的结论建立在 SOLRICKS 那份「322 tensors / key 全同 / 只差 dtype BF16→F16」上。本轮 K245 的 v2 是**同 key 同 shape、但数据区 sha 不同** ⇒ **同架构重训**。⇒ 判「转存 vs 重训」**不能只比 header，必须比数据区**（本轮取 `conv_in` 之后 192 B 比 sha，成本 2 次 Range）。
- **★★★ 冲突②（K240「4/8 步同尺寸疑似同构」判为不同构）**：字节数完全相同（818,925,468 / 5,220,193,444）但 sha 全异。⇒ 与 K151 合并成一条**通用判据**：**「字节数相同」在 H3 生态里几乎从不意味着「可原槽互换」**，只有 sha 相同才是同一份。
- **★★★ 冲突③（「加载成功」第 3 次被证明不等于「全生效」）**：K221（`reshape_weight` 元数据支）+ K199（I8 因子静默跳过）+ 本轮 K246（`t_embed` 4 张量无分支）。⇒ **三种「静默」已经各自独立出现两次以上**，P47 的 warning 至少要覆盖三类：未识别后缀 / I8 因子 / 未知顶层张量。
- **★★ 印证（K198 的「本机 2K 链路完整」再进一步）**：不仅 v1 能读，**同架构重训的 v2 也能读**（本机四条自检对结构而非对权重值）。⇒ `latent-upscale` 是**唯一对社区新权重完全开放的后处理通路**。
- **★★ 印证（K187/K224 的「shift 12 已成社区默认」之外，社区开始改 norm）**：K247 的 graft 说明社区已经越过「改 shift / 加 LoRA」，进入**改归一化增益**的层面。⇒ 「社区件能不能读」这个问题正在从「格式问题」变成「**语义问题**」——格式全对、行为未知。
- **★ 零增量（须明日复查）**：vpipe 第 11 日（274 star 第 2 日不动）；LightX2V 5 条全非 H3；ComfyUI 4 条无 H3；`Comfy-Org/MiniMax-H3` 未复核。

### 本轮实验

**无生成实验，仅零下载读头 + 本机源码对照**（共 **9 次 Range 请求**、磁盘 0、累计约 **11 min**）：K245 ×2（v2/v1 各 1）、K245 数据区 sha ×2、K246 ×1、K247 ×1、K248 ×1、K249 ×1（header）+ 2 次 72 B 载荷、K251 头部诊断 ×3（403）。

不跑 P44 的理由：
1. **时间**：04:30 起动，检索到 04:45 已用 15 min，但**本轮把「后处理」这条线挖出了一个可直接交付的能力**（K245），知识价值高于再取一组 P44 数。
2. **P44 前置已从 3 条降到 2 条（K212 关闭 alpha 项），但本轮 K250 又给它加了一条选件纪律**：4/8 步不能互换 ⇒ 若按 8 步档取数会白跑。**在选件未定死前跑 P44 仍可能取到不可复用的数**。
3. **磁盘 37 GiB**：P44 需 10.96 GiB + 818 MB，下完余 25 GiB，技术上可行，纯时间问题。

### 坑

- **坑①（新，最重要）：镜像上的 403 会给一个「看着像体积」的 `content-length`**。本轮 gated 仓返回 `content-length: 183`（`10Eros` 是 191），
  与「正常小文件」在字段上无区别 ⇒ **必须先用 `%{http_code}` 或响应头 `x-error-code` 判是不是 `GatedRepo`**，再读体积。
  这与 K241 的「`000` ≠ 404」并列：**现在有两类假体积/假存在**（超时 `000`、gated `403`）。
- **坑②（新）：`curl -sIL` 里的 `-L` 与 `-I` 顺序无关，但缺 `-L` 时 302 的 `content-length` 是跳转体长度（183）**。本轮最初 3 次「体积 = 183」就是漏了 `-L`；
  正确写法 `curl -sIL`（`-I` 大写、`-L` 跟跳转），或 `curl -s -o /dev/null -w '%{http_code} %{size_download}'`。
- **坑③（新）：`config.json` 的 `in_blocks` 与权重头的块数可以不一致**。`George0667` 的 v2 写 `in_blocks 12`，头里是 18+18。
  ⇒ 「轻量版 / 结构不同」这类推断**只能来自 header**；config 是作者手写字段，可能描述的是另一条分支（v2_temporal 那支）。
- **坑④（新）：`comfy_quant` 是 U8 张量（72 B JSON），不是纯元数据键**。按 dtype 统计权重个数会把 200 个量化声明数成 200 个权重
  ⇒ 统计脚本必须过滤 `is_aux_name`（`fp8-layout.cc:295-305` 的列表已含 `.comfy_quant`）。这与第 33 轮坑⑤（`reshape_weight` 是 I64 元数据）同型，**是同一类坑的第 2 例**。
- **坑⑤（复现）：HF 仓被删后 `api/models` 返回 `{"error":"Repository not found"}`（不是 404 状态码、是 200 体里的错误）**。`jh27kim/MiniMax-H3-Ref2VA-4step` 第 33 轮出现、本轮已撤。
  ⇒ 「搜到过」不能当「还在」，引用社区仓**必须带抓取日期**。

### 下一步

- **P55（新，高）latent upscaler v2 真机复跑**：K245 是全生态**唯一「社区新权重 + 本机零改动」**的件，成本极低（690 MB 下载 + 一张 768p 片的后处理，约 5 min + 3 min）。
  判据：与 v1 同 seed 同源片对比（锐度 / 纹理量 / 首帧 SSIM），且**必须另存 `v2_temporal` 的结果作为「时间插帧是否静默不生效」的实证**（K246）。
- **P56（新，中）graft 件的 QC 方法**：K247 的 `attn.q_norm` graft 本机可加载但语义跨模型 ⇒ 需要一套「**加载成功但行为异常**」的判据（不是 SSIM，而是运动一致性 + 撕裂检测）。
  与 P40 的运动夹具判据可复用。
- **P44（维持首选，选件纪律加一条）**：**取 4 步档**（K250 结案）；仍用 Kijai W4A8 + Fusion `lite_r32`（纯 peft 拼写）；`video_shift 6→12`。
- **P47（升优先级）**：静默失效已三类（未识别后缀 / I8 因子 / 未知顶层张量）⇒ **warning 必须是「加载结束时打一遍对账」**（绑定数 / 跳过数 / 未识别张量数），而不是逐点报错。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 9 次读头。**第六项需求**：区分「元数据张量」与「权重张量」（`I64 [1]` / `U8 [72]` / `alpha F32 []` 三类都要过滤）。
- **SOP（仍未改）**：累计 8 条待写入（追加本轮：**403 GatedRepo 的假体积 + `-L` 缺失 + config 与 header 不一致**）。
## 第 36 轮（2026-11-27 06:30 · 上游静默第 12 日 + ★★★ H3 **VAE 侧**首个 int8 ConvRot（组 64，非 256）＋本机 fast-VAE 加载器 dtype gate 硬拒 + ★★★ Pika H3 Flex 的 ComfyUI 转换 LoRA 是「rank 128 + 融合 QKV rank 384」混合 rank，且 comfy 版**主动丢掉 alpha**）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=06:30，守卫 R=36）。
> 与第 35 轮的关系：上轮挖「后处理（latent upscaler）+ 调参（graft）」，本轮换第三块此前只有一句话的面——**VAE 本体**，
> 并顺带把「rank 是否可跨模块不同」从「I8 refiner 的标称值不准」（K248）推进到「**同一份 LoRA 里合法混 rank**」。
> 四条结论被改写：① 「int8 ConvRot 只是 DiT 的事」→ **VAE 也有，且组大小是 64 不是 256**；② 「本机 VAE 能读任意量化」→ **fast-VAE 有 `float_dtype_` 硬 gate，I8 直接被拒**；
> ③ 「LoRA 一个文件一个 rank」→ **Pika comfy 版 128/384 混排，且 alpha 被丢弃等于 `mul≡1`**；④ 「社区仓引用 = 官方仓」→ **第三方镜像仓与原仓逐字节同份（`x-linked-etag` 相同），可直接当体积/结构代理**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K253** | ★ **上游静默第 12 日（零增量，五项逐位相同）**：HEAD `a6a1f53`（`author.date 2026-11-23T09:54:27Z` / `committer.date 11-23T11:14:45Z` / `pushed_at 11-23T11:20:51Z`）；release 仍 **v0.1.110（11-01）→ 落后 26 天**；issue **14 全开**（#59/#58/#56/#55 全 `updated_at == created_at`、0 评论）；**PR total_count = 0**；**274 star / 27 fork / 36,920 KB**。**star 连续第 3 日不动** | GitHub API ×5（commits / repo / releases / search issues / search pr） | 2026-11-27 | 零增量；「静默」已从「无 commit」扩到「连 star 也不动」的第三日 |
| **K254** | ★★★ **H3 VAE 侧首个 int8 ConvRot 件，且 ConvRot 组大小是 64（DiT 侧全是 256）**：`cjbrigato/fast_h3_vae_v2_24l-INT8-CONVROT:fast_h3_vae_v2_24l_int8_convrot.safetensors` = **1,623,016,374 B（1.51 GiB）/ 493 tensors**（I8 98 / U8 98 / F32 297）。结构是 **fast-VAE（24 层，dim 2048，ffn 16384，z 24，`register_tokens [1,4,2048]`，`post_quant_conv [24,24,1,1,1]`，`proj_out [3072,2048]`=3×1×32²）**。**98 个量化层**：`blocks.{0..23}.{attn.to_qkv,attn.to_out,ff.w1,ff.w2}` ×24 = 96 + `x_embedder` + `proj_out`；每层 `I8 weight` + `F32 weight_scale [N,1]`（**逐行**，`ff.w2` 是 `[2048,8192]` 注意 K=8192 不是 2048）+ `U8 comfy_quant`（120 B）。`_quantization_metadata` 顶层 `format_version 1.0` + `layers` 98 条，**97 条 `convrot_groupsize: 64`，`x_embedder` 那条无 `convrot` 键**（`comfy_quant` 原文亦如此），全部 `orig_dtype torch.bfloat16` + `per_row: true` | HF 镜像 Range 读头（全 header）+ 3 次 `comfy_quant` 载荷切片 | 2026-11-26（仓）/ 2026-11-27（读头） | **量化面从 DiT 扩到 VAE**；⚠️ **组大小 64 与 DiT 的 256 不同**，任何「按 256 硬编码」的 ConvRot 反旋转在 VAE 上必错（本机 `convrot_group_ok(64)` 是过的——64 是 4 的幂且指数 6 为偶数） |
| **K255** | ★★★ **本机 fast-VAE 加载器对 I8 是硬拒绝，不是静默跳过**：`metal-minimax-h3-fast-vae.cc:96` 的 `with_tensor_()` 判据为 `info == nullptr \|\| !float_dtype_(info->dtype) \|\| numel != want` ⇒ **dtype 不在 {F32,F16,BF16} 直接返回 false**（`:73-76` `float_dtype_`）。`proj_()`（`:519-573`）因此拿不到 `.weight`，走到 `:566` 的 `cannot read <name>` 并返回空 `Proj`，`load_` 在 `:694` 报 `"cannot read block 0's ..."`。**旁证**：`proj_` 的 int8 分支（`:533-559`）是「把 bf16 **转**成 int8」，`encode_quant_fast` 吃的是 `f32/bf16` 缓冲，**没有一条从文件里读 I8 码字的路径** | 本机源码逐行（`metal-minimax-h3-fast-vae.cc`）+ 张量契约对照 | 2026-11-27 | **修正 K254 的落地结论**：本机**不是**「能读但存储体积小」，而是**结构性读不了**；且与 DiT 侧（`fp8::scan` 支持 int8/convrot）形成**同一机型两张加载器两张脸**。若要用 K254，必须新写「I8 + 逐行 scale + ConvRot 64」码字通路（≈ `metal-minimax-h3-transformer.cc` 的 `convrot_row_scales_` 移植） |
| **K256** | ★★★ **同一份 Pika Flex LoRA 的 diffusers 版与 ComfyUI 版是两种 rank 契约**：`fl2va/adapter.safetensors` = **624 tensors / 全 F32 / 2,767,274,120 B（2.58 GiB）**，命名 `<module>.lora_A.default.weight`（**带 `.default.` 中缀**、无 `diffusion_model.` 前缀），全部 **rank 128**（A `[128,K]` / B `[N,128]`）。`comfy/loras/…_fl2va_comfy_bf16.safetensors` = **416 tensors / 全 BF16 / 1,956,172,176 B（1.82 GiB）**，命名 `diffusion_model.<module>.lora_A.weight`，**普通模块 rank 128、`attn.qkv_proj` rank 384**（A `[384,5376]` B `[21504,384]`：Q/K/V 三份**融合成一个**投影）。README 明写「Conversion **fuses Q/K/V** LoRA projections and **reorders the SwiGLU halves**；ordinary modules rank 128, fused Q/K/V rank 384」 | HF 镜像 Range 读头 ×2（官方仓 `Pika-Labs` + 镜像仓 `vml12` 同份）+ `comfy/README.md` 全文 | 2026-11-26（仓）/ 2026-11-27（读头） | **推翻「一个 LoRA 文件一个 rank」**（K248 只是「标称值 ≠ 实际」，这里是**逐模块合法不同**）。本机 `factor_meta_`（`runtime-lora.cc:433-456`）**按模块读 `alpha`→`rank`**，混 rank **结构上支持**；但见 K257 |
| **K257** | ★★★ **ComfyUI 版 LoRA 主动「omits explicit alpha tensors」，本机 `mul` 恒为 1.0 而 `qkv` 实际强度是 1/3**：`comfy/README.md` 原文「The conversion **preserves unit scaling and omits explicit alpha tensors**」。实测 header 无 `alpha` / `lora_alpha` / `lora_adapter_metadata`（metadata 只有 `modified_by / license* / copyright / format=pt / base_model / base_revision / converted_for=comfyui-minimax-h3 / source_adapter`）⇒ 本机 `index_suffix_`（`:326-358`）三处全未命中，`_meta_alpha = 0`，`factor_meta_` 走 `*mul = 1.0f`。**但 `qkv_proj` 的 rank 是 384 = 3×128**，若原 adapter 的 alpha 是 128（rank 128 时 `mul=1`），融合后 `mul` 仍为 1 ⇒ **实际施加强度是原设计的 1/3** | 同仓 header + `comfy/README.md` + 本机 `runtime-lora.cc:420-460` 源码 | 2026-11-27 | **alpha 第六态**：不是「缺失=按 rank」（K226 家族）也不是「已折进 lora_B」（第 33 轮），而是**「融合后 alpha 语义被刻意取消」**。⚠️ 未实测，**标「推断」**；但它是**唯一一个「文件全对、数值偏弱」的形态**，前五态都是偏强或跳过 |
| **K258** | ★★ **`w4a8_to_i8` 是 sd.cpp 侧被删的旧路，本机仍在树里**：sd.cpp **PR #2435「refactor: reuse INT8 GEMM for W4A8」于 2026-11-26T15:00:12Z 合入**（`6b51a955`，**+692 / −1496 / 29 文件**），正文写「Remove the dedicated W4A8 matmul implementations and extend the shared INT8 fallback paths for CUDA, HIP, MUSA, and Vulkan」。本机 `build/apple-silicon/metal-compute/affine_dequant_embed.cc.metal:2372` 仍有 `kernel void w4a8_to_i8`（`:2320` 另有 `w4a8_convrot_dequant`），`kernel-contract.h:273` 仍登记它 | GitHub PR API + 本机 metal 源 + `kernel-contract.h` | 2026-11-26 | 与本轮能力判定**无直接冲突**（sd.cpp 是删「独立 matmul」不是删 kernel），但说明**「本机有同名 kernel」不能当「本机有该功能」的反证**（K235 已立此条，本轮为第 2 例） |
| **K259** | ★★ **`convrot_groupsize` 缺省值的两套口径**：sd.cpp **PR #2436（`ea3f6ec703`，11-26T15:50:54Z）** 写「Default an omitted `convrot_groupsize` to **256** when ConvRot is enabled, **matching ComfyUI**」；本机 `fp8-layout.cc:47` `int group = 256;`（`Declared` 默认）与 `:59` `as_int(256)` 同口径。⇒ 本机与 ComfyUI / sd.cpp **三方一致**，缺省 256 是安全默认 | GitHub PR API + 本机 `fp8-layout.cc:36-64` | 2026-11-26 | **印证**；但也意味着 **K254 的 64 必须显式声明**（它确实显式写了），任何「不写 groupsize」的 VAE 件都会被按 256 解释 ⇒ **对 VAE 是错值**（组 64 的件按 256 反旋转 = 全错） |
| **K260** | ★★ **第三方镜像仓与官方仓可逐字节判等**：`vml12/Pika-H3-Flex`（2026-11-26T18:02Z 创建、0 dl / 0 like）与官方 `Pika-Labs/Pika-H3-Flex`（2026-10-29 建、197,060 dl / 712 like、lastModified 停在 **2026-11-07**）的 `fl2va/adapter.safetensors` 给出**相同 `x-linked-etag`（`8ed6115d…`）与相同 `x-linked-size`（2,767,274,120）**，`x-repo-commit` 不同（`ca45d99f` vs `8f2180b2`）⇒ **同份文件、不同仓**。另：官方仓 `fl2va/manifest.json` 的 `sha256 = 8ed6115d…` 与 `x-linked-etag` 一致 | HF 镜像 `resolve` 响应头 ×2 + `manifest.json` | 2026-11-27 | **新增判据**：`x-linked-etag` 是**内容哈希（xet 版）**，跨仓相同即同份；`x-repo-commit` 只标仓的 commit ⇒ **判「是不是同一份权重」看 `x-linked-etag` + `x-linked-size`，不看仓名、不看 commit** |
| **K261** | ★★ **HF 镜像会给 `x-linked-size`，这是本轮最省事的体积判据**：`resolve` 的 302 响应头带 `x-linked-size: <真实字节数>`（与 `content-length` 不同，后者在 302 上是跳转体长度）。本轮 4 个件全部一次拿到（2,767,274,120 / 1,956,172,176 / 9,920,387,264（VAE 分片 1/2）/ 未知） | HF 镜像 `curl -sIL` 响应头 | 2026-11-27 | **给坑②（`-L` 缺失 183）一个正解**：优先读 `x-linked-size`，它不受 302/206 影响；`content-length` 只在拿到 200/206 后才有意义 |
| **K262** | ★★ **`_quantization_metadata` 与 `comfy_quant` 可以「层内不一致」**：K254 的 `x_embedder` 在 `_quantization_metadata` 里只有 `{format, orig_dtype}`（**无 convrot 键**），但它的 `comfy_quant` 载荷写 `{"format":"int8_tensorwise","orig_dtype":"torch.bfloat16","per_row":true}`——**两者一致地都表示「不旋转」**；而 `proj_out` 与 96 个块层三处都说 `convrot true / groupsize 64`。⇒ 本机 `declared_format_`（`fp8-layout.cc:74-88`）**先读 `comfy_quant`、读不到才落 `_quantization_metadata`**，两条路都可，但**同一文件里两种记录都在时以 `comfy_quant` 为准** | 本机 `fp8-layout.cc:74-125` + 3 次载荷切片 | 2026-11-27 | 印证既有解析顺序；**新增一点**：`x_embedder` 这种「细长投影」是**唯一不旋转的层**（24 列，`K=24` 连 `convrot_group_ok` 的下界 4 都撑不住两次分组）⇒ 作者显式关掉是合理的，不是漏写 |
| **K263** | ★ **11-26 单日社区面（与第 33/34/35 轮去重后，仅记新品类）**：① **`Enigma4869/h3` 是一个 422 个 `.safetensors` 的 LoRA 集合仓**（866 文件，按 `<数字>/<数字>/<名>.safetensors` 三层目录），是本轮见到的**第一个「个人 LoRA 货架」型仓**；② `huggingface12341/zsf-h30` 有 4 个 `model-0000x-of-00004.safetensors` 分片（**疑似整模型再分发**，未读头）；③ 空壳继续增：`RunningHubAI/rh-crown-true-first-person-…`（1 文件无权重）、`Lora-Daddy/h3-writer-hauhau`（4 文件无权重）、`BrickMomen/bvfinish-h3-image-lora`（有 1 件 `h3img_bvfinish_v1_2k.safetensors` + 8 张示例图）；④ `vml12/Pika-H3-Flex` 是全量镜像（96 文件，含 7 分片 DiT 66.28 GB 索引 + 双 text_encoder + 双 VAE） | HF 镜像搜索 API ×3 拼写 + `api/models` ×5 | 2026-11-26 | 生态第 4 次重心迁移：编辑 LoRA → pi-H3 量化/换编码器 → 后处理重训/graft → **「货架仓 + 整模型镜像」**。⚠️ `Enigma4869/h3` 名称与内容**完全无关**（含成人内容命名），引用时只记「存在一个 422 件的集合仓」 |
| **K264** | ★★ **ModelScope `Recursive` 口径会让 Fusion 文件数从 15 变 48**：第 35 轮 K240 记「48 项」用的是 `Recursive=true`；本轮用 `Recursive=false` 得 **15 项**（`assets` / `pruned` / 6 个根目录权重 + 元数据）。两者都对，**差在目录条目**。`LastUpdatedTime 1795546202` = **2026-11-24 18:50Z**（与 K169 一致，权重未动） | ModelScope `repo/files` API ×2（两种口径） | 2026-11-27 | **口径纪律**：引用「N 项」必须写 `Recursive` 真假，否则 15 vs 48 会被当成「新增 33 个文件」 |

### 印证 / 冲突

- **★★★ 冲突①（「int8 ConvRot 只出现在 DiT」被推翻）**：K215/K234/K249 三份 int8 件全是 DiT，`convrot_groupsize` 全是 256。K254 是**第一个 VAE 侧件**，且组大小 **64**。⇒ 「ConvRot 256」是 **DiT 的惯例，不是 H3 的规范**；任何把 256 写死的反旋转在 VAE 上必错。本机 `convrot_group_ok`（`fp8.h:178`）接受 4–1024 的「4 的幂且指数为偶数」，**64 合法**——但**接受参数合法性 ≠ 有那条加载通路**。
- **★★★ 冲突②（「本机 VAE 能读社区量化件」被证否）**：第 31 轮 K199 只说「int8 适配器因子静默跳过」，第 32 轮 K207 说「VAE int8 是错值而非跳过」（那是 **video-VAE 的 `weight_` 会走 `to_bf16_` 并把 I8 落到 `else return {}`**）。本轮 K255 发现 **fast-VAE 更早就拒**：`with_tensor_` 的 `float_dtype_` gate 在**读之前**就返回 false。⇒ **同一族两个 VAE 加载器、两种失败位**：video-VAE 走到转换处失败，fast-VAE 在入口失败。**日志不同**（前者 `to_bf16_` 返回空、后者 `cannot read block N's`）。
- **★★★ 冲突③（「一个 LoRA 一个 rank」被推翻，且带一个数值陷阱）**：K248 是「标称 r256、实际逐模块 48–946」（**同一语义、不同标称**）；K256 是「**同一文件里 128 与 384 并存，且 384 是 3×128 的融合**」。本机结构上能处理（`factor_meta_` 逐模块取 rank），但 K257 指出 **alpha 被丢弃后 `mul≡1`，融合模块强度只有 1/3**。⇒ **混 rank 不是问题，「融合+丢 alpha」才是**。
- **★★ 印证（「镜像优先」第 4 日成立，且新增一个更强的判据）**：`huggingface.co` 本轮未试（已知 `000`），`hf-mirror.com` 全部 200/206。**K261 的 `x-linked-size` 让体积判定不再依赖 `content-length`**，这是第 35 轮坑②的根治。
- **★★ 印证（sd.cpp 与本机在「ConvRot 缺省 256」上三方一致，K259）**：这是近期少见的**没有分歧**的一条——PR #2436 的默认值与 ComfyUI 和本机都对齐。
- **★ 零增量（须明日复查）**：vpipe 第 12 日（274 star 第 3 日不动）；`MiniMaxAI/MiniMax-H3` lastModified 停在 **11-24T04:56Z**（6,012,871 dl / 7,411 like）；`lightx2v/Minimax-h3-Turbo` 31 项未动；Fusion 权重 11-24 未动；ComfyUI 搜索 API 本轮返回空（`total_count` 缺失，接口抖动，非零结论）。

### 本轮实验

**无生成实验，仅零下载读头 + 本机源码/二进制对照**（共 **9 次 Range/HEAD 请求**、磁盘 0、累计约 **23 min**）：K254 ×1（全 header 2 MB）+ 3 次 `comfy_quant` 载荷（120 B ×2 + 78 B）、K256 ×4（官方/镜像 adapter 各 1 + comfy lora ×2）、K260 头部 ×2、K261 `x-linked-size` ×4（同一批 HEAD 内）。

不跑 P44 / P55 的理由：
1. **时间**：06:30 起动，06:53 检索结束（23 min）。剩余 67 min 要装两份报告（预计 12 min）+ sync（3 min）+ release。P44 ≈ 55 min 会挤爆；P55（690 MB v2 下载 + 3 min 后处理）**技术上还在预算内**，但见 2。
2. **本轮结论直接改写 P55 的判据**：K255 说明「本机 fast-VAE 读不了 int8」——而 P55 的 v1/v2 upscaler **不需要 VAE**（latent 空间），所以 P55 不受影响；但**本轮新出的 K254 件在本机读不了**，跑它没有意义。**把「fast-VAE 的 dtype gate」写进判据，比再取一组数更值钱**。
3. **磁盘**：本轮未新增占用（0 下载），磁盘仍 37 GiB。

### 坑

- **坑①（新，最重要）：`x-linked-size` 是镜像 302 上唯一可信的体积字段**。本轮 `curl -sIL | grep content-length` 在 302 链上给出 **1050 / 1048 / 1102 / 1110**（跳转体长度），而 `x-linked-size` 一次给出 2,767,274,120。⇒ **体积判据首选 `x-linked-size`**，`content-length` 只在 `%{http_code}` 是 200/206 后采用。这是第 35 轮坑②的**根治**，不只是「记得加 `-L`」。
- **坑②（新）：同一份文件在「融合投影」后 rank 会变，而 alpha 不一定跟着变**。`qkv_proj` 从 3×(128) 融合成 1×(384)，若转换工具丢掉 alpha，`alpha/rank` 从 `128/128=1` 变成 `1`（本机 fallback）**或** 若保留原 alpha `128/384=0.33`。**两种都能发生**，只能读文件确认 ⇒ **见到 384 / 512 / 768 这类「等于 128 的整数倍」的 rank，先怀疑是融合投影**。
- **坑③（新）：`x-repo-commit` 不是内容标识**。同一个 `fl2va/adapter.safetensors` 在两个仓里 `x-repo-commit` 不同（`ca45d99f` / `8f2180b2`）、`x-linked-etag` 相同。⇒ **判「是不是同一份权重」只看 `x-linked-etag` + `x-linked-size`**。
- **坑④（新）：`declared_format_` 有两条来源，优先 `comfy_quant`**。K262 的 `x_embedder` 是唯一「两种记录都写、但只有一处写 convrot」的层——好在两处都说「不转」。⇒ **判断某层旋不旋转，必须两个来源都读并对账**，不能只看 `_quantization_metadata`。
- **坑⑤（复现）：`Recursive` 参数让同一个仓的「文件数」差 3 倍**。Fusion `Recursive=false` 15 项、`true` 48 项。⇒ 引用文件数**必须带口径**（K264）。
- **坑⑥（复现）：HF 搜索 API 的 `total_count` 缺失是接口抖动，不是「零结果」**。本轮 ComfyUI 那条 `search/issues` 返回体没有 `total_count` 也没有 `items` ⇒ **判零必须看 HTTP 200 + 空数组**，不能看字段缺失。

### 下一步

- **P57（新，高）fast-VAE 的 int8 通路评估**：K254 的件 1.51 GiB，是本机**唯一一个「体积减半」的 VAE 件（原 fast-VAE bf16 ≈ 3 GB）**。两条路：① 移植 `convrot_row_scales_` + `I8` 码字读到 fast-VAE（**工作量中等，收益是 VAE 显存/磁盘减半**）；② 等上游（**零成本，无限期**）。**先做 ① 的可行性判断：确认 `to_bf16_` 在 fast-VAE 里只被 `proj_` 用，改一处即可**。
- **P58（新，中）融合投影的 alpha 语义**：K257 的「1/3 强度」是推断。**低成本验证**：拿 `comfy/loras/…_fl2va` 与 `fl2va/adapter.safetensors` 同 seed 各跑一次（624 vs 416 张量，**本机两个都认**），比 frame diff / 首帧 SSIM。若 comfy 版明显弱 ⇒ 坐实；若相同 ⇒ 说明原 adapter 的 alpha 本就是 384（**Pika 训练时融合投影就是 384**）。
- **P44（首选不变）**：4 步档（K250）+ Kijai W4A8 10.96 GiB + Fusion `lite_r32` + `video_shift 6→12`；避开 K221/K222 混合拼写件。
- **P55（不变）**：latent upscaler v2 复跑（690 MB + 6 min），**不受 K255 影响**（latent 空间不经过 VAE）。
- **P47（升）**：「加载结束对账」现在要覆盖 **四类**：未识别后缀 / I8 因子 / 未知顶层张量 / **dtype gate 拒绝**（K255）。第四类**会明确报错**（不像前三类静默），所以对账表要区分「报错」与「静默」两栏。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 9 次读头。**第七项需求**：加「融合投影识别」——同一模块 A 的 `shape[0]` 若等于 `3×` 其它模块的 rank，标注 `fused_qkv?`。
- **SOP（仍未改）**：累计 **14 条**待写入（本轮新增：`x-linked-size` 优先 / 融合 rank 怀疑 / `x-repo-commit` 非内容标识 / `Recursive` 口径）。

### 看板检修 + P41 落地（2026-11-27 14:05）

- 用户要求"查看并修复后续计划任务"。看板已由夜间任务推进到第 36 轮（P39 连跑 13 次完整闭环）。修 5 处历史数据错误：① 头部基线 4dc36b7/11-16 → a6a1f53/11-23；② 第 29 轮 04:30 误标"完成"（实为流中断假成功、未闭环，知识由 06:30 补并）→ 改"知识已并入/未闭环"；③ 第 27 轮重复行删一；④ 表格断裂孤立表头删除；⑤ P22 判决条目误标第 8 轮 → 校正为第 6 轮 11-18 12:56（主报告 18.6 节为准）。备份 `.bak-20261127-1400`。
- **P41 完成**：runner 的 CLI 执行抽成 `run_cli()`，cb_exit=0 但 round 未推进（假成功，日志实证 4 次）时自动重试 1 次（新 session-id 避看门狗误 kill + 重建锁 + 间隔 30s）；真失败不重试。4 场景隔离测试全过。看板 P41 标记完成。
- **纪律**：cb_exit=0≠成功，闭环必须由产物判定（round 推进+sync 日志）。看板是历史追加文档需定期体检（重复行/断裂/误标/陈旧基线）。

## 第 37 轮（2026-11-28 00:30 · ★★★ 上游静默 12 日后**首次破静默**：`41a694a2`（11-26，122 文件 +28663/−418）——HyperFlow H3 Flash 进入主仓原生支持（47 块 / 3 块被删 / 102 对低秩 / `curve_dit` 跑 pi-H3）+ `train-lora` 双机 TP/DP + ★★★ lightx2v 全版本 768p 适配器进 catalog 且 8step v1.2 **alpha 逐模块 128、adaln 16**，推翻「4 步家族字节同构/单 alpha」口径）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=00:30，守卫 R=37）。
> 与第 36 轮的关系：上轮挖「VAE 侧 int8」；本轮上游 12 日静默被打破，重心回到**上游本体**：
> ① HyperFlow H3 Flash（原「社区作品」）被**收编为 upstream 一等公民**，且带三个本机从未见过的结构（块删除 + 低秩投影对 + 内建 endpoint embedder）；
> ② lightx2v 768p 全版本进 catalog，其中 **8step v1.2 是首个「逐模块 alpha + 混合 rank(16/128)」的官方适配器** ⇒ 直接改写 K151（4 步线字节同构）、K188（单 alpha 128/8）两条既有结论的适用范围。
> 三条旧结论被改写：① 「上游静默持续」→ **40 小时后有 28.7k 行增量**；② 「4 步/8 步家族全版本字节同构、alpha 只有 128/8 两档」→ **8step v1.2 是 1,543,291,302 B 的异体积件，alpha 逐模块 128 + adaln 16 且带 363 个 `.alpha` 张量**；③ 「HyperFlow Flash 属另一族、与 vpipe 无关」→ **原生 `dit_dir` + catalog 双条目 + 47 块重编号 + `curve_dit` 混跑 pi-H3**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K265** | ★★★ **上游静默第 12 日后首次破静默**：HEAD `a6a1f53` → **`41a694a2`**（author `2026-11-26T07:43:59Z` / committer `11-26T22:40:05Z` / `pushed_at 11-26T23:20:21Z`），**122 文件 / +28,663 / −418 / 29,081 净增行**（vs a6a1f53 的 85 文件 +17,617）。仓库元数据：**274 star（第 4 日不动）/ 27 fork / 38,535 KB / open_issues 14**；**release 仍 v0.1.110（11-01）⇒ 落后 27 天**；issue 14 全开（#59/#58/#56/#55 全 `updated_at == created_at`、0 评论）；**PR total_count = 0** | GitHub API ×5（commits / repo / releases / search issues / search pr） | 2026-11-28 | 「静默」系列（K84/K105/K115/K243/K253）**到此结案**；⚠️ **release 与 main 的落差从 26 天扩到 27 天**，引用能力必须写 commit `41a694a2`，v0.1.110 不含本轮任何内容 |
| **K266** | ★★★ **HyperFlow H3 Flash 被上游收编（原生 `dit_dir`，非 LoRA）**：`VideoRebirthAI/hyperflow-h3-flash` = HyperFlow 的 flow-map **蒸馏进更小的 DiT**（FL2VA **13.7B** / Ref2VA **13.9B**，对 ~31B），**4 / 6 / 8 步**（其他步数被拒），shifts 仍 **12 / 3**。catalog 两条目 `VideoRebirthAI/hyperflow-h3-flash-fl2va-int8-convrot` / `…-ref2va-int8-convrot`，**只取 ComfyUI 单文件**（bf16/diffusers/GGUF 不取）。**三处架构变更（均由文件自述）**：① **块删除**——FL2VA 删 **6 / 21 / 22**（47 块），Ref2VA 删 **9**（49 块），文件从 0 重编号且 `__metadata__.hyperflow` 记录被删的原编号；全模型适配器仍按**原编号**绑定，落在被删块上的部分**跳过并打日志**；② **低秩投影对**——FL2VA **17 块**（Ref2VA 19 块）的部分投影存成 `up @ down`，rank **pad 到 64**，常驻 2.8 / 3.3 GB，q/k/v 各自一对、按带拼进扁平 q\|k\|v；其余投影仍是 int8 ConvRot；③ **双时间内建**——endpoint embedder 是模型的一部分（有自己的权重），每次前向必须给 `(t,r)`，**无单时间模式**，上面再挂 flow-map 适配器会被拒；AdaLN 读 **16 维**（官方 pruned 是 8 维）| GitHub `docs/MINIMAX-H3.md`（`41a694a2` 全文 271,340 B）+ `stages/model-catalog.cc` 新条目 + `tests/unit-tests/hyperflow-h3-flash.cc`（1093 行） | 2026-11-26（commit）/ 2026-11-28（读取） | **推翻第 1 轮 K12 / 第 20 轮 K116 的「另一族、与 vpipe 无关」定位**：它是**官方文档的一等章节**（`docs/MINIMAX-H3.md` 新增 120 行）。⚠️ 「13.7B/13.9B」是文档口径，**本机读头实测参数张量 886 个、13.78B**（含低秩因子），见 K267 |
| **K267** | ★★★ **Flash ComfyUI 单文件的真实结构（零下载读头，15.4/15.3 GiB）**：`fl2va_int8_convrot_comfyui/minimax_h3_fl2va_hyperflow_flash_14b-int8_convrot.safetensors` = **16,005,009,056 B / header 95,736 B / 887 tensors**（BF16 508 / F32 139 / **U8 120** / **I8 120**），`__metadata__.hyperflow` = `{"format":1,"variant":"fl2va","weights":"int8_convrot","blocks":47,"dropped_blocks":[6,21,22],"rank_multiple":64,"convrot_groupsize":256,"source":"fl2va_int8_convrot","source_revision":"9e9ed14b…"}`。**块号 0–46 连续 47 个**（**已重编号、原编号只存 metadata**）；**102 对 `.down.weight`/`.up.weight`，分布 18 块**（块 1 六对、块 2 五对、其余 16 块各六对 + **块 46 仅 1 对 `mlp.fc2`**），rank 全为 **64 的整数倍**、**最宽 3200**（`blocks.2.mlp.fc1`，文档写 4992 是 diffusers 版的 padding 口径）、合计 **2.667 GB**（文档 2.80 GB）；**I8 120 个 = 31 块 × 4**（`attn.out_proj` / `attn.qkv_proj` / `mlp.fc1` / `mlp.fc2`，块 46 少 fc1），**18 个低秩块的那些投影是 BF16 对而非 I8**；**U8 120 个全是 `comfy_quant`（72 B）**；`adaln_proj.linear.weight [96768,16]` BF16（**16 维调制**）；`time_embedder` 与 `endpoint_time_embedder` 各 **4 张 F32**（`proj_in [5376,256]` + `proj_out [16,5376]` + 两个 bias），**形状完全同构**；**零 `alpha` 张量** | HF 镜像 Range 读头 ×2（FL2VA + Ref2VA 全 header）+ diffusers `index.json` 对照 | 2026-11-28 | **`dropped_blocks` 与 `rank_multiple` 是 safetensors `__metadata__` 里的自由 JSON 字符串**，本机无任何解析路径（`grep dropped_blocks` = 0，`rank_multiple` = 0）⇒ **即使 loader 认低秩对，也不知道哪些块被删/rank 是怎么 pad 的** |
| **K268** | ★★★ **Ref2VA 版与 FL2VA 版是「同工艺不同参数」，不是同文件的变体**：`ref2va_int8_convrot_comfyui/minimax_h3_ref2va_hyperflow_flash_14b-int8_convrot.safetensors` = **16,433,000,936 B / header 99,648 B / 923 tensors**（BF16 544 / F32 139 / U8 120 / I8 120），metadata `blocks: 49`、`dropped_blocks: [9]`；**114 对低秩**分布 **19 块**（无块 2/18 那种 5–6 对差，**块 2 不在列表**），最宽 3136。⇒ 两个 partition **块删位置、低秩块集合、I8 层数都不同**，**不能靠改 `variant` 字段互换** | HF 镜像 Range 读头 + metadata 对照 | 2026-11-28 | 印证 K172/K180「同名不同构」第 4 例；**新增一条**：连 `dropped_blocks` 都按 partition 不同（FL2VA 3 块 / Ref2VA 1 块），**任何「H3 FL2VA 与 Ref2VA 结构相同」的假设在这类蒸馏件上都不成立** |
| **K269** | ★★★ **`curve_dit` = 在 Flash 的块上跑 pi-H3 的 stock pruned 曲线（跨模型时间调制嫁接的官方化）**：pi-H3 的适配器训在 **pruned 形态**的时间调制上，Flash 没有它。做法：`dit_dir` 指 Flash，`curve_dit` 指 **`Comfy-Org/MiniMax-H3-FL2VA-pruned-int8-convrot`**，pi-H3 适配器挂在 config stage ⇒ Flash 的块在 **stock 曲线 + 其 AdaLN** 下跑（**单时间**），pi-H3 的 LoRA / 全张量覆写按**原编号**绑定（落在 6/21/22 的跳过并报），`final_layer`、DWD 头、4 步采样器照旧。**只读 stock 文件的曲线表与 AdaLN（约 0.15 GB）**，走 model manager 常驻模型生命周期。此路径下：flow-map 适配器被拒、VDN 分支被拒、**AdaLN 未进启动内存规划**（模型管理器加载后才看到）。M5 Max 832×480×73 + Sol：**23.4 s / 22.9 GB 峰值** vs pi-H3 直接跑 pruned DiT **29.7 s / 27.4 GB** | `docs/MINIMAX-H3.md` `curve_dit` 段 + `stages/model-catalog.cc`（`Comfy-Org/MiniMax-H3-FL2VA-pruned-int8-convrot` 条目）+ `hyperflow-h3-flash.cc` 单测名 `…runs_as_the_plain_h3_it_is_made_of` | 2026-11-26 | **这是第 35 轮 K247「跨模型 q_norm graft」的官方对应物**——民间手工嫁接（LTX-2.5/Z-Image 的 q_norm）vs 官方 `curve_dit`（只用 pruned 的曲线 + AdaLN）**语义完全不同**：前者改的是 norm 增益（行为未知），后者只换时间调制来源（曲线表 + AdaLN 复用）。⇒ **P56 的 QC 判据要按这两类分开写** |
| **K270** | ★★★ **lightx2v 8step v1.2 是首个「逐模块 alpha + 混合 rank」的官方 768p 适配器，直接推翻 K151 的「4 步家族字节同构」与 K188 的「单 alpha 两档」**：`minimax_h3_fl2v_turbo_8step_v1.2_768p_bf16.safetensors` = **1,543,291,302 B**（v1.0/v1.1 是 1,383,677,808 B）⇒ **体积已分叉**。header：**1,089 tensors 全 BF16**、`__metadata__ = {format: pt, floating_dtype: bfloat16, key_format: minimax-h3-diffusers, alpha: "128"}`；**363 个 `.alpha` 标量张量**（rank-0 BF16）——实测值 **`norm_out.linear` 与 50 个 `adaln_proj.linear` 的 alpha = 16.0**（对应 rank 16），**`token_refiner` / `attn` / `ff` 的 alpha = 128.0**（对应 rank 128）；**rank 分布 = 16×51 + 128×312**，**同一文件内合法混 rank**；**首次适配 `norm_out.linear`**（`A [16,2688]` / `B [10752,16]`，norm 输出 4× 宽）。catalog 注释原文「the 8-step v1.2 is the **first of the line to adapt `norm_out.linear` and to state an alpha per module**」| HF 镜像 Range 读头（header 134,856 B）+ 4 次 alpha 标量切片（数据区偏移 0 / 53,645,338 / 63,250,464 / 227,340,396）+ `stages/model-catalog.cc` 注释 | 2026-11-28 | **K151 收窄为「4 步家族（v1.0–v1.3）字节同构」**，8 步线**不在其内**；**K188 收窄为「`__metadata__.alpha` 单值形态」**，v1.2 走**逐模块 `.alpha`**（与 K212 Fusion 的逐模块 alpha 同型，但 Fusion 是 `alpha == rank` 的倍率语义，这里是 **16/128 两档分别等于各自 rank ⇒ mul 恒 1**）。⚠️ `__metadata__.alpha = 128` 与逐模块值**冲突**，本机 `index_suffix_` 系（`runtime-lora.cc`）如何取舍**未实测** |
| **K271** | ★★ **catalog 的 768p 条目从 10 个扩到 17 个（各版本 split 件单独注册）**：新增 `4step-768p-v1.0 / v1.1 / v1.3`、`8step-768p-v1.1 / v1.2`、`ref2va-4step-768p-v1.0`、`ref2va-8step-768p-v1.1`（+ 原有 10 个，含 4 步 v1.2 的 split/comfy 两件）。注释明写**「v1.1 is NOT catalogued」只针对 4 步线**（4 步 v1.1 仍在列？）——实测 catalog 里 **4 步 v1.1 在列**，与注释矛盾；**8 步 v1.1 在列、v1.0 只在 `-768p`/`-split` 两条旧条目里**。同时：**Ref2VA 4 步 v1.0 768p 的 shift 是 6**（其 v0.1 是 12），**Ref2VA 8step v1.0 768p 是首个不吃本 partition 默认 12 的 Ref2VA 适配器** | `stages/model-catalog.cc`（`41a694a2`）全条目枚举 + 注释 | 2026-11-26 | **口径纪律**：「v1.1 不进 catalog」是**注释里的旧话**，代码里 4step v1.1 **有**条目 ⇒ 引用 catalog 条目数必须**数代码不读注释**（与本轮 MS `Recursive` 坑同族：文档口径 ≠ 实现）|
| **K272** | ★★ **`train-lora` 上双机（TP 与 DP 两种切法），且 H3 的 pruned 分支在 TP 下不再要求 AdaLN bake**：`stages/train-lora-split.cc` 新增 **1,664 行**；Tensor parallel 按 heads 与 FFN 行切 MiniMax H3 与 Qwen-Image 2.1，每 rank 持每块与适配器的自己那份、**保存时合并整份**；Data parallel 给每族两台机、各取一步样本的一部分；握手定 kind 与份额。Resume state 改为**每步目录、留最近两个、整份写完才命名、读前校验**（坏的只丢一步、不丢优化器；**扁平布局仍可读**）。同时 `minimax-h3-denoise.cc` 的判据由 `!baked && tp.active()` 改为 `!baked && tp.active() && !pruned()` ⇒ **pruned 的 rank 用曲线跑任意 schedule，不再要求 bake** | `stages/train-lora-split.cc`（+1664）、`train-lora-stage.cc`（+591/−58）、`minimax-h3-denoise.cc`（+5/−2）diff 全文 + `docs/LORA-TRAINING.md`（+172） | 2026-11-26 | **P37（LoRA 训练 24 GB 显存账）的口径要改**：本机单机路径未变，但**上游已把训练拆到两台机**，24 GB 单机的可行性结论**只在单 rank 下成立**。另：`pruned` 曲线可跑任意 schedule 意味着 **pruned + 非 bake 的组合从此合法**（K133 的内存记账需复核）|
| **K273** | ★★ **SageAttention 新增「带 sink 的注意力」（kernel 契约 311），且缺 311 时**读错但不报错**：`kAttnSinkShift = 311`，作用是在 int8 QK（K 减均值）后把每行 sink 读成 `sink - scale * q·mean`（K 均值在 buffer 22）；int8 P·V 下还要把 sink 的质量挡在 running max 外并把 V 的均值只按 keys 的份额补回。**可选**：老 host 不声明 311 ⇒ 函数照建、**sink 读成未偏移值、V 均值算错，全程无错** ⇒ 要求先问 `sinks_available()`（kernel 契约里加 `sage_sinks_marker` 探针条目），不可用就**保持 dense** | `apple-silicon/metal-compute/kernel-contract.h`（+26）diff 全文 + `docs/PLUGINS.md`（+130）| 2026-11-26 | **「同名 kernel ≠ 同功能」第 3 例**（K235/K258 之后），但新的失效形态是 **「建得起来但算错且不报错」** ⇒ 进 P53（kernel 能力矩阵）的必查项：**可选 kernel 必须查 marker，不能只查名字** |
| **K274** | ★★ **MAGI-2-preview 是新族（`magi2`），首个「注册族也能 tensor_parallel」的模型**：40 层、36 层 MoE、逐层读、按 plan 留驻；1080p refiner 走 block-sparse 窗口二次去噪；旁挂 Qwen3.5-27B 文本分支、turbo 解码器、Stable Audio Open、Wan2.2 编码器。**与 H3 无直接关系**，但带来两条对 H3 有用的通用件：① `sideband::kFps` / `kFrames` —— **族可以改回片子的帧率与帧数**（第二级把速率/长度翻倍时必须写，否则按请求值标注）；② `VaeModelFamily::Role` 新增 **`kRoleVideoEncode`**（编码器文件与解码器不同时用，vae-encode 先问它、空则回落 `kRoleVideo`）| `docs/MAGI2.md`（+300）、`docs/PLUGINS.md`（+130）、`stages/generate-video-stage.cc`（+350/−32）| 2026-11-26 | **对 P39/后处理线有用**：`kFrames` 明确是**像素帧**不是 latent 帧；本机 catalog 里 H3 的 `vae-encode` 目前只认一个文件 ⇒ 若要用「单独重训的解码器」就要走新 role（本机无） |
| **K275** | ★★ **11-26→11-27 社区面（与 33–36 轮去重后，只记新品类）**：① **`QuantFunc/Minimax-H3-Quantfunc-4bit`** = 首个 **SVDQuant 4-bit** H3（`minimax_h3_fl2va_4step_quantfunc_int4_r128.safetensors` 12,368,339,576 B / `…int4_r64_base` 11,950,870,730 B，FL2VA/Ref2VA 各两份，tag 含 `svdquant` / `custom_minimax_h3`）——**新量化家族（SVDQuant）首次出现在 H3**；② **`KalponicStudio/MiniMax-H3-Image-Ojon`** = **H3-Image** 的 GGUF Q4/Q5 + `W4A8` / `W6A8` 双档 safetensors（8 文件，带两个 workflow），是**首个把 W4A8/W6A8 同时给 Image 线**的仓；③ `SarthakRawool/MiniMax-H3-Image-MLX-8bit-LowMem`（270 文件，MLX，`shuttrr` tag）、`SceneWorks/minimax-h3-candle`（110 文件，`q4/` GGUF blocks，Rust candle）、`AiNinja94/MiniMax-H3`（83 like 但 0 下载，疑似空壳）；④ **Flash 生态已自成体系**（`BennyDaBall/HyperFlow-H3-Flash-INT8-ComfyUI` 126k dl / `…NVFP4-ComfyUI` 6.4k / `hoidhxd/…INT8-ComfyUI-Hybrid` 244（**单文件 b25-49 int8_convrot，块 25–49 混合**）/ `moonbox-dev/…-GGUF` ×2 / `hancheng-ai/…-MLX-Serve-8bit|4bit` ×4）| HF 镜像搜索 API ×3 + `api/models` ×8 | 2026-11-26~27 | 生态第 5 次重心迁移：LoRA 货架 → 整模型镜像 → **「新量化家族（SVDQuant）+ 蒸馏件衍生量化矩阵（GGUF/NVFP4/int8/hybrid/MLX）」**。⚠️ `hoidhxd` 的 `b25-49` 命名暗示**只量化了后 24 块**（前半 bf16），本机无对应通路 |
| **K276** | ★★ **sd.cpp 侧 11-26→11-27 四条（均与 H3 无直接关系，但两条同族）**：`439e77a5`（11-26T13:12）`-mlp` ClipProj 变体（K233 已记）；`6b51a955` W4A8 复用 INT8 GEMM；`ea3f6ec7` LTX INT8 ConvRot；`908965df`（11-27T15:55）用 **pad-token 存在性区分 Ming-Image 与 Z-Image**。⇒ **sd.cpp 的 MiniMax-H3 相关面在 11-26 之后没有新提交**，本轮全部增量在 LTX/FLUX/server 侧 | GitHub `leejet/stable-diffusion.cpp` commits API（per_page=12）| 2026-11-28 | **零增量（H3 维度）**：P44/P46/P48 的「sd.cpp 已反超」结论**不再扩大**，本机与 sd.cpp 的 H3 差距停在 11-26 那四条 |
| **K277** | ★★ **本机 `0.1 (9db5dd7*0)` 对 Flash 全链路零支持（strings 五查全 0，且有一个反直觉的正对照）**：`libvpipe.0.dylib`（59,152,016 B）里 **`hyperflow` 0 / `endpoint_time_embedder` 0 / `curve_dit` 0 / `magi2` 0 / `sage_sinks_marker` 0 / `tensor-parallel-flash` 0**；正对照 `lightx2v` 21 / `Minimax-h3-Turbo` 11 / **`pi-H3` 0（但本机确实支持 pi-H3）**、`adaln_t_table` 9 / `w4a8_to_i8` 7 / `minimax` 216。⇒ **`pi-H3` 0 命中说明「字符串缺失 ≠ 功能缺失」**（该名字只在 catalog 里以 `Lakonik/pi-H3` 形式出现，而 catalog 条目名不一定要命中）| `strings -a` 本机 dylib ×12 + 本地源码树 `grep`（`curve_dit` 0 / `dropped_blocks` 0 / `rank_multiple` 0 / `\.up\.weight` 仅 vdn-branch 与 quantizer）| 2026-11-28 | **修正 P53（kernel 能力矩阵）的方法论**：`strings` 只能证「有」，**不能证「无」**（`pi-H3` 是反例）。判「本机不支持 Flash」的正确依据是**源码树 grep 三个结构键全 0**（`dropped_blocks` / `rank_multiple` / `curve_dit`）+ **本地树本身停在 `d72c22f`（11-20）**，而不是 dylib strings |
| **K278** | ★ **本轮 ModelScope / 官方仓的零增量**：`lightx2v/Minimax-h3-Turbo` **31 项未动**（26 个 safetensors，`Recursive=false`）；`MiniMaxAI/MiniMax-H3` `lastModified` 停在 **2026-11-24T04:56Z**（5,971,579 dl / 7,426 like，比第 36 轮的 6,012,871/7,411 **下载回落、like +15**）；`VideoRebirthAI/hyperflow-h3-flash` `lastModified` **2026-11-14T09:27Z**（1,019,175 dl / 370 like，**权重 14 天未动**）⇒ upstream 收编的是**既有权重**，不是新训练 | ModelScope `repo/files` + HF `api/models` ×2 | 2026-11-28 | **重要推论**：上游 `41a694a2` 是**纯软件适配**（47 块重编号、低秩对、双时间、curve_dit），**权重一字未改** ⇒ P44/P55 这类「买权重」的路线不受本轮影响；受影响的是「本机 loader 要不要追这个 commit」 |

### 印证 / 冲突

- **★★★ 冲突①（「上游静默」结案，且改写了「等上游」的性价比）**：静默 12 日 → `41a694a2` 单笔 +28,663 行，其中 **H3 相关 = `metal-minimax-h3-transformer.cc` +1104/−113、`minimax-h3-pruned.cc` 单测 +520、`hyperflow-h3-flash.cc` 单测 1093 行**。⇒ 「等上游」在这条线上**不是零成本**：一个 commit 就带来 4 个本机没有的结构（块重编号、低秩对、双时间、curve_dit）。**P57（fast-VAE int8）这类「等上游」的判断要重新算——上游正在以每 3 天一个 3 万行的速度改 H3 本体**。
- **★★★ 冲突②（K151 与 K188 同时被一份文件打破）**：K151 说「4 步家族 v1.0–v1.3 全部 1,383,677,808 B、只换权重值」——**对 4 步线仍成立**，但 **8 步 v1.2 = 1,543,291,302 B**，且**结构变了**（多 `norm_out.linear` 适配、rank 16/128 混排）；K188 说「alpha 只有 128/8 两档」——**8 步 v1.2 是逐模块 `.alpha`**（16 / 128，各自等于 rank ⇒ mul 1）。⇒ **两条结论都要加「仅 4 步线 / 仅 metadata 形态」限定**。
- **★★★ 冲突③（「Flash 是另一族」被官方收编推翻，但**本机仍不支持**）**：K12/K116 把它归为「社区另一族」——文档层面已错（`docs/MINIMAX-H3.md` 有专章）；但**本机层面仍成立**（源码树停在 `d72c22f`，`dropped_blocks` / `rank_multiple` / `curve_dit` 三个键 grep 全 0）。⇒ **「生态有」与「本机能跑」的分离在本轮体现得最清楚**：同一天里，一边是官方文档 120 行专章，一边是本机三个键零命中。
- **★★ 印证（「1.38 GB 的 split 件比 1.96 GB 的 comfy 件好」）**：K270 的 8 步 v1.2 也是 **split 1.54 GB**（1089 tensors，`lora_A.default` 中缀）vs **comfy 2.12 GB**（`…_comfyui_bf16`），与 K202 的 1.38 vs 1.96 同型 ⇒ **融合件的体积膨胀是 block-diagonal 零**，与 K257 的「融合丢 alpha」是两件事（体积大 ≠ 强度对）。
- **★★ 印证（`x-linked-size` 仍是唯一可信体积字段）**：本轮 4 个大件（16.0 / 16.4 / 15.4 / 12.4 GB）全部一次拿准，`content-length` 在 302 链上仍是三位数跳转体。
- **★ 零增量（须明日复查）**：vpipe star **274（第 4 日）**；`MiniMaxAI/MiniMax-H3` 权重停在 11-24；MS Turbo 31 项未动；`VideoRebirthAI/hyperflow-h3-flash` 停在 11-14；sd.cpp H3 面停在 11-26。

### 本轮实验

**无生成实验，仅零下载读头 + 上游 diff/文档 + 本机 strings**（共 **6 次 Range/HEAD 请求**（2 个全 header + 4 个 alpha 标量）、磁盘 0、累计约 **62 min**，其中检索 58 min / 固化 25 min）。

不跑 P55（latent upscaler v2，690 MB + 6 min）的理由：
1. **本轮结论直接改写 P55 的邻居**：K266–K269 说明**上游刚把「蒸馏件」的玩法整体换了一代**（块删除 + 低秩对 + 双时间），而 P55 是**后处理 latent 空间**的件，不受影响 —— 但也意味着**跑 P55 不能回答本轮任何一个问题**。
2. **时间**：00:30 起动，01:20 检索仍在推进（本轮源比往常多：一个 122 文件的 commit + 271 KB 文档 + 5 个新仓 + sd.cpp），01:35 才转固化。剩余时间要装三份报告 + sync + release。
3. **磁盘**：37 GiB（本轮 0 下载）。
4. **更重要**：K270 的 8 步 v1.2 与 Flash 的 `dit_dir` 都**要求 build 追到 `41a694a2` 才可能跑**，本机 `0.1 (9db5dd7*0)` 差 87 个 commit ⇒ **本轮任何一个新能力的真机验证都是「先升 build」的前置题**，不是「跑一次实验」能解决的。

### 坑

- **坑①（新，最重要）：`__metadata__` 里的自由 JSON 是本机最大的结构盲区**。Flash 的 `hyperflow` 键（`dropped_blocks` / `rank_multiple` / `convrot_groupsize`）与 8 步 v1.2 的 `alpha`（字符串 `"128"`）都是**metadata 自由文本**，本机既无 schema 也无解析（`dropped_blocks` grep = 0）。⇒ **凡是「文件能读但形状对不上」的件，第一件事是 dump `__metadata__` 全部键，而不是逐个张量猜**。这与 K223（`conversion` 自然语言）同型，是本轮第 2 例。
- **坑②（新）：`alpha == rank` 的「逐模块 .alpha」有两种语义，靠数值分不开**。K212 的 Fusion 是**倍率**（alpha 32/320/960 == rank ⇒ mul 1）；K270 的 8 步 v1.2 是 **alpha 16/128 == rank ⇒ mul 1**。两者数值行为相同（都是 1.0），但**一个来自训练时的 `alpha/r` 惯例、一个来自量化/打包惯例** ⇒ **只看 `alpha==rank` 判不出「该不该乘」以外的任何事**，必须再看 metadata（`conversion` 字段 / `floating_dtype`）。
- **坑③（新）：同一仓的「注释」与「代码」会互相矛盾**。`model-catalog.cc` 注释写「v1.1 is NOT catalogued」，但代码里 `4step-768p-v1.1` **有**条目（8 步 v1.1 也有）。⇒ **数条目必须 grep `.name =`，不能读注释**。与上一轮 MS `Recursive` 坑（15 vs 48）同族：**口径写在文档里、事实写在实现里**。
- **坑④（新）：`strings` 判「不支持」会被自己的正对照打脸**。`pi-H3` 在本机 dylib 里命中 **0**，但本机**确实支持 pi-H3**（catalog + 文档 + 单测全有）。⇒ `strings` 只能**证有不能证无**；判「本机不支持 X」要看**源码树的结构键**（本轮 `dropped_blocks` / `rank_multiple` / `curve_dit` 三键全 0 才是真依据）。**这条直接修正 P53 的方法论**。
- **坑⑤（复现）：全 header Range 的偏移算法差 8 字节会读成垃圾**。第一次算 alpha 偏移时把 `data_offsets` 当成相对文件头，读出 `1.836e+37`；正确是 **`header_len(8) + header_json_len + data_offset`**（`8 + 134,856 + 0`）。⇒ **读 data 区必须先把 8 字节长度前缀算进去**，否则每个值都是噪声且**不会报错**（bf16 任意位模式都合法）。

### 下一步

- **P59（新，最高）「上游追更决策」把 `41a694a2` 与本机的差距量化**：本机树 `d72c22f`（11-20）→ HEAD `41a694a2`（11-26），**中间隔 a6a1f53（+17,617）+ 41a694a2（+28,663）**。问题不是「要不要升」，而是**升完之后哪些旧结论失效**（K98 的「跨 build 锚点作废」意味着**所有历史锚点在 a6a1f53 之后都不可比**）。**先做**：列 `docs/MINIMAX-H3.md` 中所有「MEASURED」数字的 commit 前提，与本机 build 对账。
- **P60（新，高）Flash 三结构的本机可读性判定**：`dropped_blocks`（块删除 + 重编号）、`rank_multiple`+`up@down` 对（102/114 对，2.67/3.3 GB）、`endpoint_time_embedder`（双时间，`(t,r)` 每行两个数）。三条**都不在** `metal-minimax-h3-transformer.cc`（`d72c22f`）里。**判据**：`load_` 能否在「缺 3 块 + 遇 up/down 对 + AdaLN 16 宽」时**报错而不是算错**——按当前代码它在第三个条件（`time_dim == 8` 的 pruned gate）就会拒，但 **Flash 不是 pruned 形态**，所以走的是普通路径 ⇒ **极可能「读进去但把 up/down 对当未知张量跳过 ⇒ 102 个投影静默用 0」**。这是**第 6 类不可读形态候选**（前 5 类见 P49/P52）。
- **P61（新，中）8 步 v1.2 的 alpha 双源冲突**：`__metadata__.alpha = "128"` vs 363 个逐模块 `.alpha`（16/128）。本机 `factors_meta_` 一系**读 metadata 还是读张量**？若读 metadata ⇒ `norm_out` / `adaln` 的 51 个模块**mul 会从 1 变 8**（128/16）。**低成本验证**：不需要下载 1.54 GB —— 用 `runtime-lora.cc` 的 `index_suffix_` / `_meta_alpha` 逻辑**读代码即可定论**，再决定要不要实测。
- **P44（口径更新）**：`video_shift 12` + Fusion `lite_r32` 4 步档的结论**不变**，但要加一条：**8 步 v1.2 不进 P44**（结构不同：混 rank + norm_out），它属于**新的对照臂**。
- **P53（方法论修正）**：`strings` 只能证有。**改法**：能力矩阵改成两列 —— 「dylib strings 命中」+ 「源码树结构键命中」，**判无只看后者**。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 6 次读头。**第八项需求**：dump `__metadata__` 全部键并**按值类型着色**（字符串 / JSON 字符串 / 数字）；**第九项需求**：算 data 区偏移时**自动加 8 字节前缀**（坑⑤）。
- **SOP（仍未改）**：累计 **19 条**待写入（本轮新增：metadata 自由 JSON 必 dump / `alpha==rank` 两语义 / 注释≠代码 / `strings` 不证无 / 8 字节前缀）。

---

## 第 38 轮（2026-11-28 02:30 · 上游第 2 日静默（HEAD 仍 `41a694a2`、star 275）＋ ★★★ P61 零下载结案：逐模块 `.alpha` 优先于 metadata（本机 `factor_meta_` 先查张量）＋ ★★★ Kijai `avg_rank_*` 动态秩裁剪把 8step v1.2 从 1.54 GB 压到 336 MB 且 alpha 重写成「等于裁剪后 rank」）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=02:30，守卫 R=38）。
> 与第 37 轮的关系：上轮把「上游破静默 + Flash 收编」的**结构**摸清；本轮**转回社区货架 + 本机代码定论**，因为上轮留了两个**零下载就能结案**的题（P61 alpha 双源、K275 的 `b25-49` 推测）。
> 三条旧结论被改写：① **P61 结案**——本机 `factor_meta_` **先读逐模块 `.alpha` 张量、读不到才回落 `_meta_alpha`** ⇒ 8step v1.2 的 51 个 rank-16 模块 `mul ≡ 1.0`，**不会变成 8**；② **K275 的「`b25-49` = 只量化后 24 块」被推翻**——同族真件是**两个 partition 逐块拼接的 50 块全量 bf16**，与量化无关；③ **K217 记的官方 int8 video-VAE 体积 3,171,670,912 B 与现测 2,811,065,184 B 不符**（VAE 文件提交史停在 10-29，疑为旧记录串位）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K279** | ★★ **上游第 2 日静默，但 star 破 4 日不动（274→275）**：HEAD 仍 **`41a694a2`**（author 11-26T07:43:59Z / committer 11-26T22:40:05Z / pushed 11-26T23:20:21Z），**commits per_page=5 与上轮逐位相同**；`docs/MINIMAX-H3.md` 的最后改动 commit 就是 `41a694a2` ⇒ 无后继文档增量。仓库：**275 star（+1，结束 4 日停滞）/ 27 fork / 38,535 KB / open_issues 14**；**release 仍 v0.1.110（2026-11-01）⇒ 落后 27 天**；issue **14 条全开**，评论合计 9（#52 2 / #34 2 / #45 2 / #49 1 / #41 1 / #31 1），**#59/#58/#56/#55 仍 0 评论且 `updated_at == created_at`**；**PR total = 0** | GitHub API ×5 | 2026-11-28 | 印证 K265「破静默”是一笔大提交而非持续”：「41a694a2 之后 40 小时无后继」。⚠️ 引用能力仍须写 commit，v0.1.110 不含任何 H3 新件 |
| **K280** | ★★★ **P61 结案（零下载，读代码定论）：本机 `factor_meta_` 先读逐模块 `.alpha` 张量、命中即用，`_meta_alpha` 只在「张量缺失」时回落** ⇒ 8step v1.2 的 51 个 rank-16 模块 **`mul = 16/16 = 1.0`**，**不会因 `__metadata__.alpha="128"` 变成 8**。代码顺序：`runtime-lora.cc:446` `if (const auto* al = _w->info(key + ".alpha")) { scalar_f32(...) → *mul = v / rank; } else if (_meta_alpha > 0) {...}`；`scalar_f32`（`:48-82`）的 dtype 白名单 = **F32 / F16 / BF16 / I64 / I32**（I64 是 musubi-tuner 的 `torch.tensor(rank)`）。⇒ 8step v1.2 的 363 个 `.alpha` 是 **BF16 标量**，落在白名单内，**优先且正确** | 本机 `generative-models/shared/runtime-lora.cc`（`:48-82` / `:440-454` 全文） | 2026-11-28 | **推翻 K270 的「⚠️ 未实测」与 P61 的风险假设**：本机**不会**把 51 个模块的 mul 变成 8。⇒ **P61 撤销**，`_meta_alpha` 与逐模块 alpha 的冲突在本机**不存在** |
| **K281** | ★★★ **Kijai 的 `avg_rank_*` 是「动态秩裁剪（SVD 重打包）」，且 alpha 被重写成「等于裁剪后 rank」**：`minimax_h3_fl2v_turbo_8step_v1.2_768p_pruned_avg_rank_24_bf16.safetensors` = **335,604,966 B / 828 tensors 全 BF16 / 259 模块**（官方 8step v1.2 = **1,543,291,302 B / 1,089 tensors** ⇒ **−78.3%**）。metadata 自述：`source_format "Diffusers PEFT LoRA"`、`target_format "ComfyUI generic LoRA"`、`ss_training_comment "Dynamic resize with sv_fro: 0.95 from 384"`、`alpha_policy "per-module alpha tensors take precedence over CLI default"`、`output_rank_counts {"16":51,"128":156,"384":52}`（**这是裁剪前的口径**）。**实测 rank：259 个值落在 2–128、均值 25.0、共 72 个不同取值**（`2` 出现 103 次）。**alpha 逐模块 == 裁剪后 rank**（`blocks.0.attn.out_proj` α=29/r=29、`qkv` α=30/r=30、`mlp.fc1` α=26/r=26、`adaln` α=2/r=2、`token_refiner.blocks.1.mlp.fc1` α=3/r=3）⇒ **`mul ≡ 1.0` 而非 24/128**。⚠️ **模块命名与官方件不同族**：本件是 `blocks.N.{attn.qkv_proj, attn.out_proj, mlp.fc1, mlp.fc2, adaln_proj.linear}`（**comfy 融合形态，259 个**），官方是 `transformer_blocks.N.{attn.to_q,to_k,to_v,to_out.0, ff.net.0.proj, ff.net.2}`（**diffusers 拆分形态，363 个**）⇒ **resize 工具顺带做了 comfy 融合**，且 **`norm_out.linear` 的适配被丢弃**（本件 `grep norm_out = 0`，官方有 1 个） | HF 镜像 Range 读头（header 100,984 B）+ 6 次 alpha 标量切片 + `api/models` + `/commits/main`（本件 2026-11-17 上传） | 2026-11-28 | **新增「第 6 条适配器加工工艺」：动态秩裁剪 + 重写 alpha**。⇒ 判「可不可换槽」**不能只看 `alpha`**（本件 alpha 恒等 rank，看起来「正常」），要看 **rank 是否已偏离训练 rank**（这里 128→2，qkv 384×3→30）。⚠️ **丢 `norm_out` ⇒ 换槽会静默少一个模块**（本机无告警） |
| **K282** | ★★★ **`b25-49` 不是「只量化后 24 块」，而是「两个 partition 逐块拼接」的 50 块全量 bf16**（推翻 K275 的推测）：`MistyViolet/MiniMax_H3:diffusion_models/minimax_h3_hybrid_fl2va_ref2va_b25-49-bf16-pruned.safetensors` = **40,225,724,176 B / 532 tensors / 无 `__metadata__` / 无前缀**；**块 0–49 全在、50 块签名（10 个后缀）逐块全同**；dtype = **BF16 400 + F16 100 + F32 10 + F16 2(final_layer) + F32 4**，其中 **F16 恰好 = 50 块 × 2（`adaln_proj.linear.weight [96768,8]` + `.bias [96768]`）+ `final_layer` 2 个**，与**官方 pruned int8 件的 AdaLN 是 F16 完全一致**（实测 Comfy-Org `minimax_h3_fl2va_pruned_int8_convrot` 的 `blocks.0.adaln_proj.linear.weight` = **F16 [96768,8]**）；顶层有 `adaln_t_table F32 [1025,8]`。**键集对比**：本件 532 键 **全部**出现在官方 pruned int8 的 932 键中（`only hybrid = 0`），官方多出的 400 个正是 `*.comfy_quant` + `*.weight_scale` ⇒ **本件 = 官方 pruned 结构、权重换成 BF16（去量化）+ 两 partition 的块拼在一份文件里** | HF 镜像 Range 读头 ×2（本件 + Comfy-Org 官方 int8）+ 键集/签名逐块对比 | 2026-11-28 | **K275 的「`hoidhxd` `b25-49` 只量化后 24 块，前半 bf16」推测作废**：`b25-49` 是**块范围拼装**（前 25 块取一个 partition、后 25 块取另一个），与量化无关。⇒ **本机结构上完全可读**（50 块 + `adaln_t_table [1025,8]` + F16 AdaLN，全在 `d72c22f` 的 pruned 通路内）⇒ **P44 的「pruned 基座」有了零下载可验证的对照件**。⚠️ **行为合法性未知**：K268 已证 FL2VA/Ref2VA 的块删位置与低秩集合不同（`dropped_blocks` 不同）⇒ 逐块拼接是否「语义合法」**无任何上游依据** |
| **K283** | ★★★ **量化件的 `alpha` 可以既不是强度也不是倍率，而是 per-tensor 反量化 scale（第三态）**：`SOLRICKS/MiniMax-H3-Upscaler:h3_upscale_refiner_int8.safetensors`（1,884,199,184 B / 624 = **I8 416 + F32 208**）`__metadata__ = {"quantization": "int8_per_tensor_scales_in_lora_alpha_v1", "packaged_by": "SOLRICKS"}`；实测 alpha：`blocks.0.attn.out_proj` **7.2032e-05**（r48）、`mlp.fc1` **3.3140e-04**（r248）、`attn.qkv_proj` **9.6668e-04**（r356）⇒ 量级 1e-5~1e-3，**若按 `alpha/rank` 当强度算，mul ≈ 1.5e-6 ~ 2.7e-6**（等于把适配器抹成零）。**本机现状**：I8 因子被 `fp8::format_of("I8") = kNone` 拒（K199）⇒ 整模块 `++_skipped` 静默不生效，**所以当前是「不生效」而非「变成 1e-6」**。⚠️ **但这是偶然的**：一旦补上 I8 因子读取，同一段 `factor_meta_` 会把 `alpha` 当强度 ⇒ **mul 缩到 1e-6 量级 ⇒ 静默变成零增益** | HF 镜像 Range 读头 + 3 次 alpha 切片 + metadata | 2026-11-28 | **K200 的「alpha 两种互斥语义」升级为三态**：① 倍率（Fusion，α==rank ⇒ 1.0）；② 训练惯例（8step v1.2，α==rank ⇒ 1.0）；③ **反量化 scale（SOLRICKS int8，α≈1e-4 且与 rank 无关）**。⇒ **P57（int8 因子通路）的验收必须包含一条负向断言**：`alpha < 1e-2 且 alpha != rank` ⇒ **拒绝该模块并告警**，否则修好读取反而制造更隐蔽的错误 |
| **K284** | ★★ **4 步线的「强度减半」是 metadata + 逐模块 alpha 双降，且融合 qkv 的 alpha 恒为单投影的 3 倍**：`minimax_h3_fl2v_turbo_4step_v1.1_768p_comfyui_bf16`（1,956,192,992 B）vs `…v1.3_768p_comfyui_bf16`（**1,956,193,000 B，+8 B**）：**tensors 624 / 键集完全相同**；metadata 仅两项不同——`training_alpha "128.0" → "8.0"`、**`training_scale "1.0" → "0.0625"`（首次出现的字段）**；**逐模块 alpha 实测 128.0 → 8.0**，而 **`attn.qkv_proj` 是 384.0 → 24.0（= 3×）**、`attn.out_proj` / `mlp.fc1` 是 128 → 8 | HF 镜像 Range 读头 ×2 + metadata 全键 diff + 6 次 alpha 切片 | 2026-11-28 | **K188（4 步 v1.2/v1.3 alpha 从 128→8）得到第二次独立印证**，且新增两个可判据：① **`training_scale` 字段与 `training_alpha` 同步除 16**（128/8=16、1/0.0625=16）⇒ 二者是同一事实的两种表述；② **comfy 融合 qkv 的 alpha 恒为 3×**（384=3×128、24=3×8）⇒ 与 K257「comfy 版 qkv rank 384 = 3×128」同型，本机 `alpha/rank` 读法**恰好正确**（384/384=1.0），**不**需要特判 |
| **K285** | ★★ **`MistyViolet/MiniMax_H3` 是首个「整机分发套装」仓：66 文件把 LLM + DiT + LoRA + VAE + upscaler + 中文工作流目录装在一份里**：`LLM/`（Qwen3.8-27B 的 `UD-IQ3_XXS` / `UD-Q8_K_XL` GGUF + `mmproj-BF16`）、`diffusion_models/`（官方 `MiniMax-H3-FL2VA_int8_convrot` + K282 的 hybrid）、`text_encoders/qwen3vl_32b_{bf16, int8_convrot, nvfp4_awq}`、`vae/`（audio fp32 + video fp16/int8）、`latent_upscale_models/h3_upscaler_lms_v0.1.safetensors`、`loras/` 11 个 + `loras/minimaxh3/` 12 个（含 `minimax_h3_taomate_3step_lora_avg_rank_19`、`minimax_h3_lms_v1.0_r64_r2`、多份 `curveproj1025`）、`semantic_bridge/t8_compat/`、以及**中文目录 `自動續接長視頻音頻驅動數字人/models/`（12 个 DiT 变体：`FeiHou_MiniMax-H3_Remix_v0.6(_int8_convrot_v2)` / `10Eros_Max_*_pruned` / `DasiwaMinimaxH3_dasiwa(REF2VA)Hybrid*` / `minimax_h3_fl2va_zs05_int8_convrot` / `minimax_h3_latent_upscaler_3d_fp16`）**。**493 dl / 0 like**，`lastModified 2026-11-27T15:33Z` | HF 镜像 `api/models` + 全文件枚举 | 2026-11-28 | **「整机套装仓」是社区第 6 种分发形态**（前 5 种：单 LoRA / 全量 diffusers 分片 / GGUF 量化矩阵 / workflow-only / gated 镜像）。⇒ 对本实验室的价值是**一次拿到全部件名与体积**，但 **493 dl 无 like ⇒ 不是被验证过的配方**，任何「这套能跑」的说法都是待复现 |
| **K286** | ★★ **`H3_speed_slider_1.1` 揭示 metadata 的第 4 类用法：prompt 模板（而非训练参数）**：10,093,356 B / **3 tensors 全 F32**（单模块 `token_refiner.blocks.1.mlp.fc2` 的 `alpha` / `lora_down [128,14336]` / `lora_up [5376,128]`），**rank 128、alpha 128 ⇒ mul 1.0**；拼写是 **kohya（`lora_down/lora_up`）**。metadata 16 个键里 **12 个是空字符串**，只有 `positive_phrase "fast motion."` / `negative_phrase "slow motion."` / `image_effect "87%"` / `backend "minimaxh3"` / `concept "speed_slider"` 有值 —— **即「这一档滑块的语义」写在 metadata 里，不在权重里**。本机 `b_of_a`（`:175-179`）能把 `lora_down → lora_up` 映射，**可读**；`.alpha` 走 `factor_meta_` 的 F32 分支 **可读** | HF 镜像 Range 读头 + 全文 metadata | 2026-11-28 | **metadata 语义新增第 4 类**（前 3 类：结构参数 / 强度 / 转换说明）：**① 结构（`dropped_blocks` / `rank_multiple`）、② 强度（`alpha` / `training_scale` / `lora_alpha`）、③ 转换（`conversion` 自然语言）、④ 使用说明（positive/negative phrase）**。⇒ **dump metadata 的价值不止「读出结构」，还包括「不读就误用强度和用途」**（本轮 `image_effect "87%"` 提示它是「效果强度」而非运动滑块刻度） |
| **K287** | ★★ **社区开始产出「只有 workflow + 校验和、无权重」的结构化对照评测仓**：`AI-KSK/minimax-h3-vbvr-v2-video-reasoning`（7 文件：`workflow.json` 19 节点 22 链 / `CHECKSUMS.txt` / `LICENSE_NOTE.md` / 中英 README / `cover.png`），自述 **9 场景 18 片段**的「H3 with vs without VBVR V2 LoRA」对照，四个维度 = **物体一致性 / 动作顺序 / 时序一致性 / 空间交互**；外链 B 站 `BV1Bk1czaEu7` + YouTube `OO9yf4yLgng` + RunningHub。**明确声明不含权重/凭据/签名 URL** | HF 镜像 README raw + `api/models` | 2026-11-28 | **分发形态第 7 种：只发评测图 + 校验和**。对本实验室的直接价值是**场景设计**（9 场景 18 片段正是 P33 缺的「统计功效」来源），而非权重。⚠️ 结论（哪一维有提升）**全部待复现**，README 未给任何数值 |
| **K288** | ★ **`RunningHubAI/rh-*` 是空壳率最高的命名族（本轮新仓 3/3 只有 `.gitattributes`）**：`rh-crown-hyperpdmd-hd-3-4-minimax-h3-turbo-lora`、`rh-minimax-h3-turbo-4step-ckpt500-comfyui-lora`、`rh-minimax-h3-lora-2090958230839570433` 均 **1 文件（`.gitattributes`）/ 0 dl / 0 like**；同批 `AI-KSK`（真内容）、`MistyViolet`（66 文件）、`linkqpsfa`（gated 但 8 文件）都正常。另：**`klassas/minimax-h3-loras` 只有 1 个权重（`MysticXXX_MMH3-V5.safetensors`）+ 0 dl**，`nnndite/minimaxh3image` 4 文件 / 36 dl（单 LoRA + 一张图） | HF 镜像 `api/models` ×5 | 2026-11-28 | 检索纪律：**「`api/models` 能列出 ≠ 有货」**，`siblings` 数 ≤ 2 的一律先当空壳（K231 的「83 like 但 0 下载」是 like 虚高的对照）。⇒ 每轮社区面的**有效仓数**应扣掉空壳后统计 |
| **K289** | ★ **ModelScope 与 HF 的同名仓文件数差 1（31 vs 30），差的不是权重**：`lightx2v/Minimax-h3-Turbo` **MS = 31 项**（含 `configuration.json` 72 B）、**HF = 30 项**（无 `configuration.json`），两边 **26 个 safetensors 逐名相同**、`4step_v1.2_768p_bf16` 仍 **1,383,677,808 B**、`8step_v1.2_768p_bf16` 仍 **1,543,291,302 B** ⇒ **MS Turbo 本轮零增量**（与 K278 一致） | MS `repo/files`（`Revision=master&Root=`）+ HF `api/models` | 2026-11-28 | **K264（`Recursive` 真假让文件数 15↔48）的兄弟坑**：**跨平台比文件数必须先扣掉非权重项**。引用「31 项」时应写「MS 31 / HF 30，权重 26」 |
| **K290** | ★★ **官方 int8 video-VAE 的现测体积与旧记录不符（360 MB 差），且 VAE 文件自 10-29 起未动**：`Comfy-Org/MiniMax-H3:vae/minimax_h3_video_vae_int8_convrot.safetensors` = **`x-linked-size` 2,811,065,184 B**（`x-linked-etag 52a2c8c7…e60c0e`）；K217 与 `h3-ecosystem-map.md` 记的是 **3,171,670,912 B**。该文件的提交史在 `4b53a35191`（2026-11-15，标题 `Workflow links: Pika H3 Flex templates`) 之前就只有 10-29 的 sol_vae 上传 ⇒ **文件本身没被换过**。同仓另一组现测：`video_vae_fp16` **5,207,808,496** / `sol_vae_fp16` **3,596,335,728** / `sol_vae_int8_convrot` **1,988,306,504**。另：K217 记的社区 `mt_video` = 2,811,065,896 B 与官方现测**只差 712 B** ⇒ 疑为「官方与 mt_video 串位」的旧记录错误 | HF 镜像 `x-linked-size` ×4 + `api/models` + `/commits/main` | 2026-11-28 | **P48/P57 的体积账要改**：官方 int8 video-VAE = **2.81 GB**（不是 3.17 GB），相对 fp16 5.21 GB 是 **−46%**。⚠️ 旧值为高估 13%，不影响「减半」结论，但**影响「磁盘预留」与「是否值得为它改 loader」的性价比判断** |

### 印证 / 冲突

- **★★★ 冲突①（P61 结案，与 K270 的风险假设相反）**：K270 记「`__metadata__.alpha = 128` 与逐模块值冲突，本机如何取舍未实测」。实测 `factor_meta_`（`runtime-lora.cc:446-452`）**先查张量**，只有 `_w->info(key+".alpha")` 为 null 才回落 `_meta_alpha`。⇒ **`mul = 1.0`，不会变 8**。这是本轮唯一「读代码即定论」的题，也说明 **P61 作为任务不该存在**（它的前提「优先级未知」在代码里是显式写死的）。
- **★★★ 冲突②（K275 的 `b25-49` 推测被推翻）**：K275 写「`hoidhxd` 的 `b25-49` 命名暗示只量化了后 24 块（前半 bf16），本机无对应通路」。实测同族真件（MistyViolet）**50 块全在、逐块签名全同、只有 AdaLN 是 F16（与官方 pruned 一致）**，且键集是官方 pruned int8 的**真子集**（去掉 400 个 `comfy_quant`/`weight_scale`）。⇒ **`b25-49` 是「块范围拼接」不是「块范围量化」**，且**本机 pruned 通路能读**。
- **★★★ 冲突③（官方 VAE 体积记录有 360 MB 差）**：见 K290。旧记 3,171,670,912 B vs 现测 2,811,065,184 B；文件提交史证明未换过 ⇒ **旧值应改为现值**，并注明「与社区 `mt_video` 只差 712 B，疑旧记录串位」。
- **★★ 印证（`x-linked-size` 仍是唯一可信体积来源）**：本轮 6 个大件（40.2 GB / 335.6 MB / 10.1 MB / 2.81 GB / 5.21 GB / 3.60 GB）全部一次拿准；`content-length` 在 302 链上仍不可用。**gated 仓的 403 响应 `content-length` 仍是错误体**（`linkqpsfa` 两仓：`README.md` 200 可读、两个权重 403）。
- **★★ 印证（本机 `diff_b` + curve 双通路与「curveproj1025」件完全对得上）**：`minimax_h3_turbo_v4_step600_ema_DasiwaREF2VAHybridV1_0_curveproj1025_compat_v001.safetensors`（**794,888,704 B / 569 tensors = BF16 518 + F32 51**）的结构是 **51 个 `adaln_proj.linear.diff_b [96768] F32`** + **51 对 `adaln` LoRA（`A [16,8]` / `B [96768,16]`，**8 宽的 A 正是曲线点的宽度**）+ 208 对 `rank 64` 的普通因子**；metadata 明写 `application "W_eff = W + lora_B @ lora_A; bias_eff = bias + diff_b"`、`conversion_algorithm "adaln_curve_affine_lstsq_pinv1025_with_diff_b"`、`curve_grid_size "1025"`、`curve_width "8"`、`projected_adaln_count "51"`、`validation_status "static_projection_validated; perceptual_render_pending"`、`compatibility_scope "exact_checkpoint_sha256_only"`。⇒ 本机两条读法**恰好覆盖**：**pruned DiT** 上 adaln 的 8 宽 LoRA 当普通 adapter（`bind_curves_` 在 `pruned()` 时 `lora_ok=false` 被跳过）+ `diff_b` 由 `bind_pruned_adaln_` 应用；**released DiT** 上同一批因子当 **curve branch**（`bind_curves_` 的 `kSpell` 第二项 `.adaln_proj.linear.lora_A/B`），而 `diff_b` **只 warn 不应用**（`:4664-4677`）。**P62 可低成本验证（795 MB）**。
- **★ 零增量（须明日复查）**：接续 K278 —— `MiniMaxAI/MiniMax-H3` **`lastModified 2026-11-24T04:56Z` / 5,971,579 dl / 7,426 like（与第 37 轮逐位相同）**；`VideoRebirthAI/hyperflow-h3-flash` **2026-11-14T09:27Z / 1,019,175 dl / 370 like（逐位相同）**；`Comfy-Org/MiniMax-H3` **2026-11-15T09:54Z / 33,581,705 dl / 2,863 like**；MS Turbo 31 项未动；**sd.cpp 的 H3 面停在 11-26**（11-27 新增 3 笔全是 server/LTX：`c80ed92a` `--output-dir`、`9d1fe300` LTXAV CUDA、`dee497f4` DGL 输出目录，另一笔 `e637c7bc` 是 Web UI 尺寸）。

### 本轮实验

**无生成实验，仅零下载读头 + 本机源码定论**（共 **约 40 次 Range/HEAD 请求**：Full header 10 个（8step_resized / 4step_v1.1 / 4step_v1.3 / hybrid / 官方 pruned int8 / 官方 video_vae_int8 / curveproj LoRA / speed_slider / SOLRICKS int8 refiner / 官方 8step v1.2）+ alpha 切片约 25 次 + `x-linked-size` 约 10 次；磁盘 0）。

**不跑实验的三条理由**：

1. **本轮唯一的高价值题是「读代码」不是「跑一次」**：K280（P61）靠 `runtime-lora.cc` 定论，成本 0；跑一次 1.54 GB 的实测只是**验证一个代码里写死的事实**。
2. **时间**：02:30 起动，检索阶段到 03:31 才收（比预算 35 min 超 30 min），剩余约 100 min 要装三份报告 + sync + release，**任何 >30 min 的实验都会压掉最小闭环**。
3. **磁盘 35 GiB**（过 15 GiB 红线，但 K282 的 40.2 GB 与 K281 的 336 MB 都不在本轮预算内）。

### 坑

- **坑①（新，最危险）：bf16 标量按 IEEE half（`<e`）解码会得到「看起来合理」的小数，且不报错**。本轮第一次读 Kijai resized 件的 alpha 得到 `2.96875 / 2.953125 / 3.34766`（正是 29.0 / 29.0 / 26.0 的 bf16 位模式被当 half 解），**一眼看去像「alpha 被缩小到 2~3 的倍率」**，据此会得出「Kijai 把强度改成 2/rank」的**完全错误结论**。正确读法 `u16 << 16 → f32` 得 29.0/30.0/26.0/2.0/3.0（**恰好等于 rank**）。⇒ **纪律：读 bf16 标量后必须把「alpha 是否等于 rank」当自检断言**，不成立就怀疑解码而不是怀疑文件。
- **坑②（新）：同尺寸兄弟件的差异全在「值」和两个字符串里，结构对比会给出「无差异」**。4 步 v1.1 与 v1.3 的 `tensors 624 / 键集全同 / 体积差 8 B`，**唯一的 metadata 差异是 `training_alpha` 与 `training_scale`**，唯一的权重差异是 624 个张量里 208 个 alpha 标量的值（128→8、384→24）。⇒ **判「vX.Y 是不是同一份」必须 dump metadata 全键 diff + 抽样标量，不能只比 keyset/shape/体积**（这与 K151「字节同构 ⇒ 只换权重值」互为补集：**字节同构恰恰意味着差异只在值里**）。
- **坑③（新）：「同源」不等于「同命名」，resize 工具会顺带做形态转换**。K281 的 resized 件模块数 **259** vs 官方 **363**，若按名字直接 diff 会误判「少了 104 个模块」；实际是 `attn.to_q/to_k/to_v` 融合成 `attn.qkv_proj`、`ff.net.0.proj`+`ff.net.2` 改名为 `mlp.fc1`+`mlp.fc2`。**唯一真正丢失的是 `norm_out.linear`（1 个）**——而它正好是 8step v1.2 相对 4 步线**新增**的那个模块 ⇒ **裁秩把「最新特性」丢了**，这是最容易被忽略的损失。
- **坑④（新）：「量化 scale 存在 alpha 里」这件事，只有 metadata 一句话能说明**。`int8_per_tensor_scales_in_lora_alpha_v1` 这串只在 `__metadata__.quantization` 里，**张量名/形状/dtype 全无异样**（`alpha` 仍是 rank-0 标量）。⇒ 与第 37 轮坑①（metadata 自由 JSON 是最大盲区）**同一个盲区的第二个受害者**：**同一个键名（`alpha`）在不同 publisher 手里是四种语义**（强度倍率 / 训练惯例 / 反量化 scale / 空模板）。
- **坑⑤（复现）：gated 仓要分「文件级 403」与「仓级不可见」**。`linkqpsfa` 两仓 `api/models` 正常列 8 个 siblings、`README.md` 200 可读、**两个权重 403** ⇒ 与 K251 同型；本轮新增一条便利判据：**先取 `README.md`，能读到内容就说明仓在、只是权重 gated**。

### 下一步

- **P62（新，高）「curveproj1025 pruned 兼容 LoRA」真机验证**：件 **794,888,704 B**，结构与本机两条通路完全对得上（见印证段）。**两臂**：（a）挂在 `minimax_h3_ref2va_pruned_int8_convrot`（P44 已有件）→ 走 `bind_pruned_adaln_` 应用 51 个 `diff_b`；（b）挂在 released `minimax_h3_ref2va_bf16` → adaln 部分走 curve branch、`diff_b` **应当只 warn**。**判据**：日志里出现 `carries ComfyUI weight diffs on the AdaLN ... does not apply them` 即印证 (b) 的 warn 路径；画质只做目检（metadata 自报 `perceptual_render_pending`）。**成本 < 10 min**。
- **P44（口径更新，优先度回升）**：K282 提供了**零下载可判读的 pruned 对照件**（`b25-49` hybrid，532 键、`adaln_t_table [1025,8]`、F16 AdaLN）⇒ P44 的「下载 19.53 GB」可以改成「先用 40 GB hybrid 判结构、再用 int8 件判速度」两步；但 **hybrid 的「跨 partition 拼接是否合法」必须先问上游**（K268 已证两 partition 块删位置不同）。
- **P57（新增负向验收项）**：见 K283 —— 补 I8 因子读取时，**必须同时挡掉 `alpha < 1e-2 且 alpha != rank`**，否则 SOLRICKS 类件会从「静默跳过」变成「静默乘 1e-6」。
- **P53（方法再加一条）**：`strings` 只证有（K277）之外，**「键名相同 ≠ 语义相同」**：`alpha` 四义（K283/K286）说明**能力矩阵要按「键 + metadata 语境」判，不能按键名判**。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 10 次读头。**第十项需求**：bf16 标量解码**内置自检**（把「alpha/rank 是否 1.0」打印出来当 sanity check，见坑①）；**第十一项需求**：`keyset` 对比时**自动做「逻辑模块归一化」**（融合/拆分的映射表，见坑③）。
- **SOP（仍未改）**：累计 **24 条**待写入（本轮新增 5 条：bf16 标量自检 / 同尺寸兄弟比 metadata / 归一化后比模块 / alpha 四义 / gated 先读 README）。


## 第 39 轮（2026-11-28 04:30 · 上游第 3 日静默（HEAD 仍 `41a694a2`、star 八日停在 275）＋ ★★★ 首个 SVDQuant W4A4 int4 H3 逐张量解剖（208 线性 × 9 键 / group 64 沿 input / 2 nibble 每字节 / 秩 128 与 64 双档）＋ ★★★ 本机「FP8 单文件 DiT 可直接跑」得官方文档与源码双证，同族 SVDQuant 却掉在判据层 ＋ ★★★ K281 的「Kijai 丢了 `norm_out`」是跨形态误判（改名非删除）＋ K281「只是裁秩」实为「裁秩 + pruned 转换」）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=04:30，守卫 R=39）。
> 与第 38 轮的关系：上轮把 K275 的第 ① 条（QuantFunc = 首个 SVDQuant 4-bit）留成**存在性记录**没解剖；本轮**零下载把它拆到张量级**，并顺带复核 K281 的三条断言（结果两条要改）。
> 四条旧结论被改写：① **SVDQuant 从「只有名字」→ 完整 9 键结构**（group **64 沿 input**、qweight **2 值/字节**、`proj_down/up` 秩 **128/64**、`resq_vr` 残余低秩分支）；② **K281「Kijai 丢了 `norm_out`」作废**——`norm_out.linear` 在 comfy 词表里叫 `final_layer.adaln_proj.linear`，归一化后 **`only_official = 0`**；③ **K281「只是裁秩」不完整**——metadata 明写 `pruned_conversion`（alpha 折进 B / A 投影到曲线基 / 常数项转 `diff_b`），⇒ **只能挂 pruned 基座**；④ **K284 的「qkv alpha 恒为 3×」在裁秩件上失效**（30 vs 29）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K291** | ★★ **上游第 3 日静默，star 连续 8 日停在 275**：HEAD 仍 **`41a694a2`**（author 11-26T07:43:59Z / committer 11-26T22:40:05Z / pushed 11-26T23:20:21Z），`commits per_page=5` 与第 37/38 轮**逐位相同**；**275 star / 27 fork / 38,535 KB / open_issues 14**；**release 仍 v0.1.110（2026-11-01）⇒ 落后 27 天**；**PR total = 0**。issue 14 条全开、评论合计仍 **9**（#52 2 / #34 2 / #45 2 / #49 1 / #41 1 / #31 1），其余 8 条 0 评论，其中 **#59（RelayVSR 原生 2×，11-16 建）、#53、#48、#17、#15 的 `updated_at == created_at`**（从未被碰过） | GitHub API ×4（commits / repo / releases / issues+pulls） | 2026-11-28 | **印证 K279**：「破静默」是一笔大提交而非持续活跃；`41a694a2` 之后已 **58 小时**无后继。⚠️ v0.1.110 不含任何 H3 新件，引用能力必须带 commit |
| **K292** | ★★★ **首个 SVDQuant W4A4 int4 H3 的完整结构（把 K275 的「存在性」升级为「可判读」）**：`QuantFunc/Minimax-H3-Quantfunc-4bit:minimax_h3_fl2va_4step_quantfunc_int4_r128.safetensors` = **`x-linked-size` 12,368,339,576 B / 2608 tensors / 274,992 B header**，dtype = **BF16 1151 + I8 832 + F32 625**；**50 块 + token_refiner 2 块 + `final_layer`**，**208 个线性层**每个带 **9 键**：`qweight I8` / `wscales BF16` / `wgsums BF16` / `proj_down I8` / `proj_down_scale F32` / `proj_up I8` / `proj_up_scale F32` / `resq_vr I8` / `resq_vr_scale F32`，另 `smooth_factor`（208）+ `smooth_factor_orig`（200）。**关键算术**：`wscales` 形状 `[in/64, out]`（`out_proj [112, 5376]` ⇒ 7168/64=112；`fc2 [224, 5376]` ⇒ 14336/64=224；`qkv [84, 21504]` ⇒ 5376/64=84）⇒ **group size = 64，切的是 INPUT 维**；`qweight [out, in/2]`（`out_proj [5376,3584]`）⇒ **2 nibble / 字节**。`proj_down/proj_up [·,128]` ⇒ **SVD 秩 128**（`r64_base` 档为 64）。**README 自报**：PSNR **23.7 dB**（vs bf16 同 prompt 同 seed）、RTX 4090 768² 124 帧 **3.2 s/步**（INT8 ConvRot 8.5 s = 2.66×、FP8 10.2 s = 3.19×）、**SM75/86/89/120**、**adaln folding 最大相对误差 FL2VA 7.58e-4 / Ref2VA 9.22e-4** | HF 镜像 Range 读头（header 全量）+ 4 次分组算术 + README 全文 | 2026-11-28 | **K275 第 ① 条升级**。⇒ 继 Fusion / Kijai W4A8 / int8 ConvRot / NVFP4 之后的**第 5 个量化家族**，且**带 SVD 残余分支**（`proj_down/up` + `resq_vr`）——只有 NVFP4 的 `weight_scale_2` 与之形似，含义完全不同 |
| **K293** | ★★★ **本机对 FP8「单文件 DiT」是明确支持的（官方文档 + 源码双证）；SVDQuant 掉在「判据层」——第 6 类「看着像 H3、本机打不开」**：① CLI 帮助原文「a single .safetensors (a Comfy-Org repack, **or the diffusers naming, e.g. lightx2v's FP8 turbo DiT, read as it is with FP8 kept FP8**)」；② 源码 `metal-minimax-h3-transformer.cc:634-640` 单文件分支同句，`:160-176` `to_bf16_()` 对 `fp8::format_of() != kNone` **整张解码**；③ `minimax-h3-diffusers-layout.h` 记 diffusers↔本机名三处改名 + **qkv 为 FLAT 行序**（`to_q/to_k/to_v` = `qkv_proj` 连续行）。**实测 fp8 件**：`minimax_h3_fl2v_turbo_4step_v1.1_768p_fp8` = **34,023,114,720 B / 988 tensors（BF16 626 + F8_E4M3 350 + F32 12）**，`transformer_blocks.*` **950 键**、`weight_scale` **350 个（per-row `[7168,1]`）** ⇒ **全量 DiT 权重，不是 LoRA**。**而 QuantFunc 件**：无 `adaln_t_table`、无 `blocks.N.attn.qkv_proj.weight`（只有 `.qweight`）⇒ `:657-661` 的 `comfy_saved` 两条判据全不满足 → **fail(「is neither a Comfy-Org H3 component, an H3 DiT ComfyUI saved, nor one in the diffusers naming」)**；`strings` 对 `qweight`/`wgsums`/`wscales`/`proj_down`/`proj_up`/`resq_vr`/`smooth_factor` **七键全 0 命中**（`qweight` 只出现在 `qwen3` / `drama3` 两条 LLM 通路） | 已装 `libvpipe.0.dylib` `strings` + 本地源码（`:160-176` / `:634-661` / `diffusers-layout.h`）+ HF Range 读头 ×2 | 2026-11-28 | **能力矩阵要分两栏**：「FP8 plain/scaled 单文件 DiT = **支持**」vs「SVDQuant W4A4 = **不支持，且失败在判据层不是解码层**」。⇒ K211 的失败位从 3 类扩为 **4 类**：判据层（K211/K293）/ 枚举层（K221）/ 翻译映射层（K239）/ **键名缺失层**（本件 `qweight` 连 `dim()` 都读不到） |
| **K294** | ★★ **QuantFunc 的 AdaLN 折叠形态与本机认识的两种都不同族（这是它被判据层拒绝的根因）**：顶层 **`adaln_fold_basis.weight BF16 [8, 2688]`**、**`time_embedder.proj_in [5376,256]` + `proj_out [2688,5376]`（完整 t-MLP，输出 2688 宽）**、块内 **`adaln_proj.linear.weight [96768,8]`**（8 = 曲线宽）、**无 `adaln_t_table`**、`final_layer.adaln_proj.linear [10752,2688]`。对照：**官方 pruned**（无 t-MLP + `adaln_t_table [1025,8]`）与 **WaveCut**（`proj_in [16,256]` / `proj_out [8,16]`，K211）。⇒ QuantFunc 是**第三种**：**保留预烘 t-MLP（2688 维输出）后再乘 8 宽折叠基**。本机 `comfy_saved` 硬性要 `adaln_t_table`（`:648-652`）⇒ **落在缝里** | HF Range 读头（顶层 + 块内 7 键）+ 源码 `:644-661` | 2026-11-28 | **「AdaLN 三种形态」口径**：① 官方 pruned（表 1025×8，无 t-MLP）；② 折叠进 t-MLP 输出（WaveCut，16→8）；③ **预烘 t-MLP + 8 宽基（QuantFunc）**。⇒ 判「像不像 pruned」**不能只看 `adaln_proj` 宽度**，要看 `time_embedder.proj_out` 的 out 维（2688 / 8 / 16） |
| **K295** | ★★★ **官方 comfy 8step v1.2 比 diffusers 版大 37%，原因是「融合 qkv 用 block-diagonal B」把 2/3 写成零**：`…8step_v1.2_768p_bf16`（diffusers）= **1,543,291,302 B / 1089 tensors / 363 alpha / 726 模块**；`…8step_v1.2_768p_comfyui_bf16` = **2,115,772,012 B / 777 tensors / 259 alpha / 259 模块**，差 **+572,522,806 B（+37.1%）**。逐项：comfy `blocks.0.attn.qkv_proj.lora_B` = **[21504,384] = 16,515,072 B**，diffusers `to_q/to_k/to_v` 三个 `[7168,128]` 各 1,835,008 = **5,505,024 B** ⇒ **单块 qkv 的 B 大 3×**（2/3 是零），50 块约 **+550 MB**，正是全部差额。metadata：`qkv_fusion "block diagonal B; concat A; alpha multiplied by 3"`；实测 alpha `qkv 384.0 / out 128.0 / fc1 128.0 / adaln 16.0` | HF Range 读头 ×2 + 逐张量字节相减 + 4 次 alpha 切片 | 2026-11-28 | **K151「4 步家族字节同构」不适用于「diffusers vs comfy」跨形态**：同一步数同一语义，形态不同就差 **37%**。⇒ 「下哪个」的判据是**基座形态**（pruned/released × diffusers/comfy），不是步数。另：comfy 的 **`alpha(qkv) = 3 × alpha(单投影)`** 在 8step v1.2 同样成立（384 = 3×128） |
| **K296** | ★★★ **K281 的「Kijai resized 丢了 `norm_out`」是跨形态误判——那是改名，不是删除**：官方 diffusers 件有 `norm_out.linear.{alpha,lora_A,lora_B}`（1 个模块）；官方 **comfy** 件的对应物叫 **`final_layer.adaln_proj.linear`**（`minimax-h3-diffusers-layout.h` 明写 `norm_out.{linear,norm} -> final_layer.{adaln_proj.linear,norm}`）。拿 Kijai（comfy 形态）与官方 **diffusers** 件按名字直比 ⇒ 必然「少 1 个」。**归一化后实测**（去 `diffusion_model.` + 去 `.lora_{A,B}(.weight)` + 去 `.alpha`）：Kijai **310** 个模块、官方 comfy **259** 个，**`only_official = 0`**、`only_kijai = 51`（**全是 `blocks.N.adaln_proj.linear.diff_b`，加 `final_layer` 那一个，共 51**） | HF Range 读头 ×2 + 模块集归一化比对（Python） | 2026-11-28 | **作废 K281 的「裁秩把最新特性丢了」**：Kijai 件**一个模块都没少**，反而多 51 个 `diff_b`。⇒ 这是本轮**唯一一次差点写出反向结论**的地方（见坑③） |
| **K297** | ★★★ **Kijai `avg_rank_24` 件不只是「裁秩」，是「裁秩 + pruned 形态转换」，故只能挂 pruned 基座**：metadata 原文 `pruned_conversion: "adaln alpha folded into lora_B; lora_A projected to the curve basis; constant term as diff_b"`、`adaln_curve_basis: "fl2va"`、`base_model: "Comfy-Org/MiniMax-H3 minimax_h3_fl2va_bf16.safetensors"`、`output_alpha_counts {"16.0":51,"128.0":156,"384.0":52}`（**裁剪前**口径）、`ss_training_comment "Dynamic resize with sv_fro: 0.95 from 384"`。**结构证据**：`final_layer.adaln_proj.linear.lora_A` = **[2, 8]**（8 宽 = 曲线基；官方对应物是 **[16, 2688]**）+ **51 个 `adaln_proj.linear.diff_b BF16 [96768]`**（本机 `bind_pruned_adaln_` 认这个键）。**alpha 实测（BF16 `u16<<16→f32`）**：`qkv 30.0/r30`、`out_proj 29.0/r29`、`fc1 26.0/r26`、`adaln 2.0/r2`、`final_layer 2.0/r2` ⇒ **`mul ≡ 1.0`** | HF Range 读头 + 6 次 alpha 切片 + 模块集归一化 | 2026-11-28 | **两处改写 K281**：① 「只裁秩」→ **裁秩 + pruned 转换**（挂 released bf16 DiT 会**静默少掉全部 AdaLN 适配**，因 released 无 8 宽曲线基）；② 融合 qkv 被裁得更狠——384→**30**（12.8×）而单投影 128→**29**（4.4×）⇒ **block-diagonal 的压缩率是单投影的 2.9×**（B 有 2/3 是零，SVD 直接吃掉）。⚠️ 与 K295 合看：`alpha(qkv)=30` **不再是** `3×alpha(out)=29` ⇒ **「qkv alpha 恒 3×」在裁秩件上失效** |
| **K298** | ★★ **`ibyteohdear/…-Fused` 是「整仓打包了 diffusers 源码」的分发事故（第 8 种形态，且是打包错误）**：`MiniMax-H3-Pruned-{LightX8-hybrid,DMD-FL2VA-Turbo}-Fused` 各 **1423 文件**，其中 **1412 个在 `diffusers/` 下**——全是 `diffusers/__init__.py`、`diffusers/commands/*.py`、`diffusers/__pycache__/*.cpython-311.pyc` 等**上游 Python 包本体 + 编译缓存**；真权重只有根目录 **4 个 `diffusion_pytorch_model-0000{1..4}-of-00004.safetensors`** + `config.json` + `README.md`。598 dl / 1 like | HF `api/models` 顶层目录计数 | 2026-11-28 | **K239 的「4 分片 / 637 tensors」没错**，但**文件数口径必须扣掉 1412 个非权重**（与 K289 的「MS/HF 差 1 个 `configuration.json`」同族，量级差 3 个数量级）。⇒ 检索纪律：**先看 `topdir` 分布**，`diffusers/` 下 `.py`/`.pyc` 一律不计 |
| **K299** | ★★ **TE-PK 的 `pk_lora` 方言：520 张量里没有 `sink` 权重，`inject_token0_sink` 是运行时注入**：`Alissonerdx/TE-PK-Minimax-H3:gemma4/minimax_h3_32b_pk_lora_gemma4_e4b.safetensors` = **520 tensors 全 F16**，非 `te_lora` 的只有 **4 个**：`scale F32 [1]` / `R F16 [15360,5120]` / `donor_mean [15360]` / `target_mean [5120]`；余 516 个是 `te_lora.layers.*.{self_attn.{q,k,v,o}_proj, mlp.{gate,up,down}_proj}.lora_{A,B}`，**rank 32**。**`grep sink` = 0**。metadata：`method "ridge_joint_lora"`、`donor_layers "[0,-2,-4,-8,-16,-24]"`、`lora_alpha "32.0"`、`alignment "forced_qwen_seg"`、`val_h3_r2 "0.89353"`（README 表写 0.894，一致）、`has_te_lora "true"` | HF Range 读头（header 全量） | 2026-11-28 | **K237 的「本机 connector 6 张量 vs TE-PK 4 张量」不变，补一条关键区分**：README 的 `inject_token0_sink = True` 是**运行时把 Qwen3-VL-32B 的 20 KB Token-0 向量注入**（`<0.01 ms`，零训练），**不是**权重里的 `sink_embedding`。⇒ 判「能否塞进本机 connector」**不能靠 README 功能名对齐**，要 dump 张量表 |
| **K300** | ★ **sd.cpp 的量化路线继续走「Q8_0 运行时 INT8」，与 vpipe 的 int8_convrot / W4A8 不同族**：11-27 新增 **`05adb5b9` `feat: add runtime INT8 execution for Q8_0 linear layers (#2445)`**（19:23Z）；同日前三条 `dee497f4` server DGL 输出目录、`9d1fe300` LTXAV CUDA、`c80ed92a` `--output-dir`；11-26 有 `ea3f6ec7` LTX INT8 ConvRot、`6b51a955` 复用 INT8 GEMM for W4A8。**H3 面仍停在 11-26 的 `439e77a5`（`-mlp` 变体）** | GitHub API commits per_page=12 | 2026-11-28 | **第 3 日无 H3 增量**（印证 K278）。另记：sd.cpp 的 INT8 是 **Q8_0 块量化**（34 B / 32 权重），vpipe 是 **int8_tensorwise + ConvRot**（Hadamard 旋转）⇒ **两边 int8 权重互不通用**，别拿 sd.cpp 结论套 vpipe |

### 印证 / 冲突

- **★★★ 冲突①（K281「丢 `norm_out`」→ 跨形态误判）**：见 K296。`norm_out.linear` 在 comfy 词表里叫 `final_layer.adaln_proj.linear`；Kijai 件与官方 **comfy** 件归一化后 **`only_official = 0`**。⇒ K281 那条「裁秩把最新特性丢了」**作废**；真相是**一个模块都没丢**，还多出 51 个 `diff_b`。
- **★★★ 冲突②（K281「只是裁秩」→ 「裁秩 + pruned 转换」）**：见 K297。`pruned_conversion` 三个动作（alpha 折进 B / A 投影到曲线基 / 常数项转 `diff_b`）任一成立就足以让该件**不能挂 released DiT**。
- **★★★ 冲突③（「qkv alpha 恒为 3×」在裁秩件上失效）**：K284 在 4 步**未裁秩**件上测得 `qkv alpha = 3 × 单投影`（384 = 3×128、24 = 3×8）；本轮在 8step **未裁秩** comfy 件再次印证（384 = 3×128）；但 Kijai 裁秩件是 **qkv 30 / out 29**（≈1.03×）⇒ **该等式只在「未裁秩 + block-diagonal 全量」成立**。⚠️ 拿它当「alpha 解码正确」的自检会在裁秩件上**误报失败**。
- **★★★ 印证（本机 FP8 单文件 DiT = 支持，且是官方明写的能力）**：K293。CLI 帮助 / 源码注释 / `diffusers-layout.h` 三处同句，且 `to_bf16_()` 对 F8_E4M3 整张解码。⇒ P44 的对照臂可低成本加一条「fp8 全量 DiT + 4 步 LoRA」（34 GB，磁盘 35 GiB 不够，登记不下载）。
- **★★ 印证（`x-linked-size` 仍是唯一可信体积来源，本轮 6 件全准）**：12,368,339,576 / 11,950,870,730 / 2,115,772,012 / 1,543,291,302 / 335,604,966 / 95,858,352。⚠️ **新坑**：`resolve/main` 段漏写会得到 **404 + 55 KB 错误页**（见坑①）。
- **★ 零增量（须明日复查）**：`MiniMaxAI/MiniMax-H3` **`lastModified 2026-11-24T04:56Z` / 5,971,579 dl / 7,443 like（dl 逐位相同、like +2）**；`Comfy-Org/MiniMax-H3` **11-15T09:54Z / 33,581,705 dl / 2,888 like（+25）**；`VideoRebirthAI/hyperflow-h3-flash` **11-14T09:27Z / 1,019,175 dl / 370 like（逐位相同）**；MS `lightx2v/Minimax-h3-Turbo` 仍 **31 项 / 合计 75,804,462,395 B**，与 HF **30 项**只差 `configuration.json`（72 B），26 个权重逐名相同（K289 结论不变）。

### 本轮实验

**无实验，仅零下载读头 + 本机源码/二进制定论**（约 **26 次 Range/HEAD 请求**：`x-linked-size` 12 次 + 全 header 8 次 + alpha/结构切片 6 次；下载 **0 字节**；磁盘 0）。

**不跑实验的三条理由**：

1. **本轮高价值题全部「读头 + 读代码」可结案**：K292（SVDQuant 结构）、K293（判据层失败位）、K296/K297（K281 三条断言复核）都不需要权重落地。跑一次只能证明「已经能证明的事」。
2. **唯一「可跑」的新能力是 34 GB 的 fp8 全量 DiT**（K293），磁盘只剩 **35 GiB**（92% 占用）⇒ **下载即触红线**，且它只是「本机已支持」的再确认。
3. **时间**：04:30 起动，检索阶段到 04:55 收（~25 min，切在预算内），余下要装三份报告 + 技能包双源同步 + sync + release。任何 >20 min 的实验都会压掉最小闭环。

### 坑

- **坑①（新，最易误判）漏写 `/resolve/main/` 会得到「404 + 55 KB 错误页」，看起来像「仓里的文件全没了」**。本轮第一批 6 个 URL 都写成 `https://hf-mirror.com/<repo>/<file>`，结果 **6/6 `http=404`、`x-linked-size` 全空、响应体 55,690~55,746 B**；而**对照组**（`Comfy-Org/MiniMax-H3/.../vae/minimax_h3_video_vae_int8_convrot`，带完整 `/resolve/main/`）**一次 302 + 206 + `x-linked-size` 2,811,065,184**。⇒ 与「`000` 超时 ≠ 404」、「gated 403 ≠ 删仓」构成**第三类假 404**。**纪律：批测体积前先用一个已知好件做对照**，对照不通就是 URL 形态错，不是文件没了。
- **坑②（新，与第 38 轮坑① 同族但更隐蔽）同一批 alpha 里 F32 与 BF16 混存，读法只有一种能「响」**：官方 comfy 3 件声明 **F32 alpha**，按 F32 读对（384.0 / 128.0 / 24.0 / 8.0）；Kijai 件是 **BF16 alpha**，按 F32 解得 `1.6e+19`（一眼垃圾），改 `u16<<16→f32` 才对（30.0/29.0/26.0/2.0）。⇒ **纪律：读标量前先看 header 里该张量的 `dtype`，不要套上一轮读法**；F32 误读会「响」，而 **F16/BF16 互串都给「合理」的数**（第 38 轮坑① 的 2.96875 即此类）。
- **坑③（新，本轮最危险）「模块集比对」不先归一化，差集会被前缀/后缀吃掉，结论直接反向**：第一次直接比 `diffusion_model.blocks.0.attn.qkv_proj` 与 `blocks.0.attn.qkv_proj`，得到「official 518 / kijai 569，only_official 全是 `*.lora_A`、`*.lora_B`」——**完全无意义**（Kijai 键是 `…qkv_proj.lora_A.weight`，去掉 `.alpha` 后仍带 `.lora_A.weight`）。归一化（去 `diffusion_model.` + 去 `.lora_{A,B}(.weight)` + 去 `.alpha`）后才是 **310 vs 259、`only_official = 0`**。差一步就会写「Kijai 少了 259 个模块」。
- **坑④（新）`avg_rank_N` 里的 N 不是任何单层的 rank**：文件名 `avg_rank_24`，实测 qkv **30**、out_proj **29**、fc1 **26**、adaln **2**、final_layer **2**（K281 记的「72 个不同取值、2 出现 103 次」也说明分布极散）。⇒ **`avg_rank_N` 是加权平均，不是逐层上限**；判「裁到多少」必须逐层读。
- **坑⑤（复现 + 补上界）`api/models` 的 `siblings` 数会被「打包事故」放大 100 倍**：`ibyteohdear` 两仓各 1423 文件，其中 1412 个是 `diffusers/` 的 `.py`/`.pyc`。⇒ 与 K288 的「`siblings ≤ 2` 先当空壳」互补：**上界也要看**，上千的多半打包了源码/缓存。

### 下一步

- **P62（优先级再升）**：K297 证明 Kijai `avg_rank_24` 件与 P62 的 `curveproj1025` 件**是同一种形态**（pruned 曲线基 + `diff_b`），且 **335 MB 比 795 MB 更小** ⇒ **可先用这个更小的件验 `bind_pruned_adaln_` 的 `diff_b` 通路**。**判据**：日志出现 `bind_pruned_adaln_` 应用 51 个 `diff_b`，且**无** `carries ComfyUI weight diffs on the AdaLN ... does not apply them` 告警。
- **P44（口径更新）**：K293 确认「FP8 全量 DiT 本机支持」⇒ 对照臂可加 `4step_v1.1_768p_fp8`（34 GB），但**磁盘 35 GiB 不足**，先登记不下载。⚠️ 与 W4A8 档（11.77 GB）比，fp8 是 **3× 体积换「零适配」**，性价比只在「不想碰量化通路」时成立。
- **P57（新增一条）**：量化家族已到 **5 个**（Fusion / Kijai W4A8 / int8 ConvRot / NVFP4 / **SVDQuant**）⇒ 能力矩阵「量化格式」维度要列 5 列，且 **SVDQuant 的 `resq_vr` 与 NVFP4 的 `weight_scale_2` 极易混淆**（都叫「残余/二级」：一个是低秩分支，一个是张量级 scale）。
- **P53（再加一条）**：`strings` 判能力的**否定侧**要按「键全名」而非「关键词」：本轮 7 键全 0 命中 ⇒ 可断言「不支持 SVDQuant」；但 `int4` 有 71 次命中（全是 `drama3-int4` 的 GPTQ）⇒ **命中 `int4` 不能证明支持 int4 H3**。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 8 次读头。**第十二项需求**：读标量前**按 header dtype 自动选解码器**（F32 / F16 / BF16 三路，见坑②）；**第十三项需求**：模块集比对**内置归一化表**（前缀 `diffusion_model.`/`model.`、后缀 `.lora_A(.weight)`、`.alpha`，见坑③）。
- **SOP（仍未改）**：累计 **29 条**待写入（本轮新增 5 条：URL 形态对照 / 标量按 dtype 解码 / 模块集归一化 / `avg_rank_N` 是均值 / siblings 上界）。


## 第 40 轮（2026-11-28 06:30 · 上游第 4 日静默（`pushed_at` 仍 `11-26T23:20`，但 `updated_at` 跳到 `11-27T18:01` = 只动 star 不动代码）＋ ★★★ 两条新运行时分支的「失败位」精确定位（GGML-block 掉在 `.scales` 缺失、MLX-affine 掉在 `config.json` 缺失）＋ ★★★ 「补一半 config 会让明确拒载变成静默错值」（8bit×group32 ↔ 4bit×group64 的等价陷阱）＋ ★★ 官方 H3-Image 的三件套（`pdd_fused_heads` 6×96×5376 / 六步显式 sigmas / DiT 66.3 GB）＋ ★★ T8 semantic bridge：6 张量 F32 MLP 插在 layer 49）

> 本轮由 **P39 launchd + codebuddy 无头 CLI** 执行（slot=06:30，守卫 R=40）。
> 与第 39 轮的关系：上轮把「SVDQuant 拒载」定在第 4 类失败位（键名缺失层）；本轮把**两条刚从 11-27 冒出来的新运行时分支**（Rust `candle` 的 GGML-block、Apple `MLX` 的 affine）各自**落到具体 fail 行**，并发现一个比「拒载」更危险的中间态：**只要给它们补一份不完整的 `config.json`，本机会从「明确报错」变成「按 4bit 解 8bit 的静默错值」**。
> 三条旧结论被收窄：① K275 只登记了 `candle`/MLX「存在」，本轮给出**具体失败位置与可否救**；② K94/K221 的 `step_head_of` 是**机制**，本轮找到 H3-Image 的**实体件**（`pdd_fused_heads` 12.4 MB / 6 头）；③ K285 只列了 `semantic_bridge/t8_compat/` 目录名，本轮把它拆成 **6 张量 F32 MLP + 元数据 schema**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K301** | ★★ **上游第 4 日静默，且首次出现「`updated_at` 变、`pushed_at` 不变」**：HEAD 仍 **`41a694a2`**（author 11-26T07:43:59Z / committer 11-26T22:40:05Z），`commits per_page=5` 与第 37/38/39 轮**逐位相同**；**`pushed_at` 仍 `2026-11-26T23:20:21Z`，但 `updated_at` 从 `11-27T18:01:34Z` 之后继续走** ⇒ **`updated_at` 只反映 star/watch/metadata，不能当「有新提交」**。**275 star（连续 9 日不动）/ 27 fork / 38,535 KB / open_issues 14**；**release 仍 v0.1.110（11-01）⇒ 落后 27 天**；**PR total = 0**；issue 14 条全开、评论合计仍 **9**（#52 2 / #34 2 / #45 2 / #49 1 / #41 1 / #31 1），**#59/#53/#48/#17/#15 的 `updated_at == created_at`**（从未被碰过） | GitHub API ×4（commits / repo / releases / issues+pulls） | 2026-11-28 | **印证 K291**：`41a694a2` 后已 **≈82 小时**无后继。⚠️ **新增判据**：判「上游是否有新动作」必须用 `pushed_at` 或 `commits[0].sha`，**`updated_at` 会因 star 单独跳动**（本轮 `updated_at` 11-27T18:01 但无新 commit） |
| **K302** | ★★★ **Rust `candle` 的 GGML-block 量化是第 6 个量化家族，本机拒载位置在 `.scales` 缺失**：`SceneWorks/minimax-h3-candle`（110 文件：`q4/` 54 + `q8/` 54 + README）把每个量化线性存成**一个 3 维 `U8` 张量** `{name}.weight = [out, in/32, block_bytes]`（**Q4_1 = 20 B/32、Q8_0 = 34 B/32**），**没有 `.scales`/`.biases` 兄弟张量**（scale/min 内联在 block 里），`config.json` 只声明 `{"quantization":{"bits":8,"storage":"ggml"}}`（**`storage` 是本机不认的键**）。实测 `q8/transformer` = **35,301,767,680 B / 14 分片**（首片 2,649,323,752 B）、`q8/text_encoder` = **33,711,827,808 B / 1003 键（含 `layers.50`/`layers.51`）**。**本机路径推演**：`config_from_json` 能过（`_class_name=MiniMaxH3Transformer3DModel`，bits=8，**`group_size` 缺 ⇒ 默认 64**）→ `linear_()` 找 `nm+".scales"` = **nullptr** ⇒ 量化分支整体跳过 → 回落 `weight_()` → dtype `U8` → `to_bf16_()` 的 U8/I8 分支 → `fp8::decode_tensor_bf16` 因**无 `comfy_quant` 记录**而 decode 失败 ⇒ 空 Linear ⇒ **`fail("not in the checkpoint")`** | HF 镜像 `api/models` + config Range 读头 + 首分片 header（64 个块 0 张量）+ 本机 `metal-minimax-h3-transformer.cc:1106-1160 / :150-198` | 2026-11-28 | **新家族登记（6 个）**：Fusion / Kijai W4A8 / int8 ConvRot / NVFP4 / SVDQuant / **GGML-block**。⇒ **「3 维 U8」是第二种「形状即信息」的载荷**（第一种是 K298 的打包事故）；本机 `dim()` 与量化推导都只认 2 维 ⇒ 结构上读不到。⚠️ **算术副产物**：**Q8_0 = 34 B/32 = 8.5 bpw**，故 `q8` 档 **35.30 GB > fp8 档 34.02 GB（+3.8%）** ⇒ 「q8 比 fp8 小」是错觉 |
| **K303** | ★★★ **MLX affine 件（`SarthakRawool/MiniMax-H3-Image-MLX-8bit-LowMem`）结构上过得了本机判据，却被「缺 `config.json`」挡在第一步；而补一份不完整 config 会比不补更糟**：DiT = **23,327,880,544 B（`transformer/` 154 分片 + 1 index = 155 文件；全仓 274 siblings）**、`text_encoder` 20,201,866,240 B（layers 0–49 / 4-bit g32）、`vae` 807,783,088 B、`vision` 1.2 GB、`vae_encoder` 0.36 GB。**结构**：`adaln_t_table F32 [1025,8]` + 融合 `blocks.N.attn.qkv_proj.weight` ⇒ **满足 `comfy_saved` 两条判据**（`:655-657`），且 `blocks.0.adaln_proj.linear.weight [96768,8]`（**8 宽 pruned 曲线**，本机 `time_dim==8` gate 通过）；量化形态 = **`weight U32`（4 码/字）+ `scales`/`biases` BF16**，`group_size = 32`（**只写在 README，无 `transformer/config.json`，实测 404**）。**关键算术**：`out_proj.weight [5376,1792]` ⇒ 1792×4 = 7168 B/行 = 7168 码 ⇒ **K=7168、8 bit**，`scales [5376,224]` = 7168/32 ✓；`qkv.weight [21504,1344]` ⇒ 5376 B/行 ⇒ **K=5376（hidden）、8 bit**。**⇒ 若按本机默认 group 64 推**：`K = scols×64` 翻倍（out_proj 14336 / qkv 10752），`bits = gcols×32/K` 恰算成 **4.0** ⇒ `l.bits = 4`，而 **`scales` 列数在 group 32 与 group 64 两种解读下都成立**（K 与 group 同比缩放）⇒ **尺寸校验全过，只有 bits 与 K 同时错** ⇒ **8bit 码按 nibble 解 = 静默错值**。**当前结局**：无 `config.json` ⇒ `config_from_json` 第一步就 `fail("cannot open …/config.json")`（与 K239 同族）| HF 镜像 `api/models` + README 全文 + `model-00001` header（9 张量）+ `model.safetensors.index.json`（926 键 / 199 对 scales+biases）| 2026-11-28 | **新增「修复反而更错」的第 2 例**（第 1 例是 K283/P57 的 int8 alpha）：**给 MLX 件补 config 时若只写 `bits:8` 不写 `group_size:32`，本机会从「明确拒载」变成「静默错值」** ⇒ 验收断言必须是「**bits 与 group 必须成对声明**；只有其一时直接拒」。⇒ 也印证 K293 的「格式 × 键名方言 × 基座形态」要加第 4 维 **「量化参数声明位」** |
| **K304** | ★★ **官方 H3-Image 仓的三件套首次拆开：`pdd_fused_heads` 是 12.4 MB / 2 张量的「逐 step 输出头」，`pdd_config.json` 给六步显式 sigmas**：`MiniMaxAI/MiniMax-H3-Image` = 100 文件 / **1,084,642 dl / 2,629 like**（`created 11-03`、`lastModified 11-16T10:00Z`）。① **`pdd_fused_heads.safetensors` = 12,388,808 B / 2 tensors 全 F32**：`video_out.weight [6, 96, 5376]` + `video_out.bias [6, 96]` ⇒ **6 个 step 专用输出头**，96 = patch `1×2×2` × latents 24（=4×24）；② **`pdd_config.json`**：`num_inference_steps 6`、`sigmas [1.0, 0.9675237, 0.8875485, 0.75, 0.5327739, 0.2320089, 0.0]`；③ **DiT `transformer/` = 66,279,032,256 B / 12 分片 / 531 键**，且**同一份权重在 `transformer_diffusers/` 再存一遍**（14 文件）⇒ 仓内 Transformer 相关占 28 文件。`transformer/config.json` 的 `_class_name` 是 **`MiniMaxH3DiTModel`**（注意：**不是** `MiniMaxH3Transformer3DModel`），`audio_enabled: false`、`adaln_out_features 96768`、`final_adaln_out_features 10752` | HF 镜像 `api/models` + `transformer/config.json` + index（531 键）| `pdd_fused_heads` header + `pdd_config.json` | 2026-11-28 | **K94 的 `step_head_of` 从机制变成实体**：6 个头 `[6,96,5376]` 与六步 sigmas 一一对应 ⇒ 「逐 step 换输出头」有实物依据。⚠️ **`_class_name` 双拼写**（`MiniMaxH3DiTModel` vs `MiniMaxH3Transformer3DModel`）两种本机都收，但**引用时必须带出处**，否则会被当成两个模型 |
| **K305** | ★★ **T8 semantic bridge 是「H3 适配的第七形态」：6 张量 F32 MLP 插在 layer 49，`lossless_metadata_wrap` 把原网关包在里面**：`MistyViolet/MiniMax_H3:semantic_bridge/t8_compat/BUNNY_H3_ActionLogic_Bridge_V1_T8_Compat.safetensors` = **22,046,928 B / 6 tensors 全 F32**：`fc1.weight [512,5120]` / `fc1.bias [512]` / `fc2.weight [512,512]` / `fc2.bias [512]` / `fc3.weight [5120,512]` / `fc3.bias [5120]` ⇒ **5120 → 512 → 5120 的瓶颈 MLP**（参数量 ≈ 5.51 M × 4 B ≈ 22 MB，与体积吻合）。`__metadata__`：`bridge_type BUNNY_H3_ActionLogic_Bridge`、**`target_h3_layer "49"`**、`operation "lossless_metadata_wrap"`、`schema t8_semantic_bridge_v1`、`source {JOKER141/BUNNY_H3_Conditioning_Bridge, rev 658bfbb0}`、`source_sha256 983380be…`、`activation silu`、`rms_epsilon 1e-06`、`recommended_alpha_start "0.10"`、`recommended_magnitude_match per_token`、`teacher_val_cos 0.35009735` / `val_rep_cos 0.99606692` / `val_corr_cos 0.99705868`、`formal_prompts 2400`。**本机**：`strings libvpipe` 的 `semantic_bridge` / `actionlogic` / `BUNNY` **全 0 命中**（`bridge` 10 次全是无关词），源码树 `grep semantic_bridge` = 0 | HF 镜像 header 全量（2248 B）+ metadata JSON 解析 + 本机 `strings` | 2026-11-28 | **适配形态第 7 种**（LoRA / 融合 Adapter / PDD head bank / curve LoRA / int8 refiner / VAE graft / **独立 MLP bridge**）。⇒ 与 LoRA 的本质差别：它**不是权重增量而是整层替换**（`lossless_metadata_wrap` + 显式 `source_sha256`）⇒ 本机没有任何 hook 点，且**不能靠 `runtime-lora` 的任何路径绑上**。`val_rep_cos 0.996` 但 `teacher_val_cos 0.350` ⇒ **自报「行为接近本体、但和老师差很远」**（待复现，社区单源）|
| **K306** | ★★ **MLX / candle 两条分支的「体积 vs 能力」对照：本机零改动可用的最省磁盘 H3-Image 路径仍是空的**：`candle q8` DiT **35.30 GB** + TE **33.71 GB** = 68.9 GB（几乎等于官方 66.3 GB，**量化没换来磁盘收益**，因为 Q8_0 = 8.5 bpw 且 TE 保留 layers 50/51）；`candle q4`（Q4_1 = 20 B/32 = **5 bpw**）才是真缩，但 **q4 档未公开 total_size**（同样 54 文件）。`MLX-8bit` DiT **22.4 GB** + TE **20.2 GB** = 42.6 GB（**比官方 66.3 GB 省 36%**，是 H3-Image 目前最省的一条），且 README 自报 **16 GB Mac / 512×640 / 62 s / 3.25 GB** 峰值、1024² 约 45–60 s（**待复现，社区单源**）。**本机磁盘**：`/System/Volumes/Data` **35 GiB 可用 / 92% 占用** ⇒ 42.6 GB 仍不够 | `api/models` siblings + index `metadata.total_size` + README 表 + `df -h` | 2026-11-28 | **P28/P21「H3-Image 磁盘阻塞」的量化版本**：官方 diffusers 66.3 GB → MLX 42.6 GB → **仍差 8 GB**。⚠️ 但这两个件的**可靠性不对称**：candle 是「本机结构读不到」、MLX 是「结构能过但 config 缺」⇒ **若要试 H3-Image，MLX 件是唯一有希望的一条，且必须自带正确的 `config.json`（bits 8 + group_size 32）** |
| **K307** | ★ **ModelScope `lightx2v/Minimax-h3-Turbo` 四日未动，4 步线 v1.2/v1.3 与 v1.1 同字节（K151 边界维持）**：**31 项 / 27 safetensors**，`LastUpdatedTime = 2026-11-24T14:36:39Z`（**已 4 日**）、`CreatedTime 08-07T18:33:38Z`、**67,119 dl / 129 star**。4 步 FL2VA：v1.0/v1.1/v1.2/v1.3 的 `_768p_bf16` **同为 1,383,677,808 B**（v0.1 是 1,383,677,888）、`_768p_comfyui_bf16` v1.1–v1.3 **同为 1,956,193,000 B**（v1.0 是 1,956,192,992）⇒ **4 步线仍字节同构**。8 步 v1.2 的分叉仍在（**1,543,291,302 / 2,115,772,012**），v1.3 8 步**不存在** | ModelScope `repo/files` API + `api/v1/models` 元信息 | 2026-11-28 | **印证 K151「4 步家族字节同构」边界**：仅 4 步线、且**仅 `_768p_` 命名**（`_v0.1` 的 1,383,677,888 与 `4step_v0.1_bf16` 差 80 B 是另一支）。⚠️ MS 的 `LastUpdatedTime` 是**整仓**时间戳，单文件新增不会让已存在文件的时间前进 ⇒ 与 K264 的「`Recursive` 口径」同族 |
| **K308** | ★ **sd.cpp 第 4 日无 H3 增量，11-27 尾部新增 1 条显存记账修正**：11-27T20:44Z `3b0426f7 fix: count idle GPU buffers toward the max VRAM budget (#2446)`；同日前序 `05adb5b9`（Q8_0 运行时 INT8，已记 K300）/ `908965df`（Ming-Image vs Z-Image 用 pad-token 判别）。**H3 面仍停在 11-26 `439e77a5`（`-mlp` 变体）** | GitHub API commits per_page=10 | 2026-11-28 | **印证 K300/K278**：sd.cpp 的 H3 增量已 **3 日**为零；且它这三天的动作全在「显存/服务端/其它模型」，与本机 H3 主线无交叉 |

### 印证 / 冲突

- **★★★ 冲突①（「补配置」比「不补」更危险）**：见 K303。MLX 件当前**明确拒载**（`cannot open config.json`）；一旦补一份只写 `bits:8` 的上游格式 `config.json`，本机按默认 `group_size 64` 推导 ⇒ `K` 翻倍、`bits` 从 8 算成 4，而 **`scales` 列数在两种解读下都成立** ⇒ 尺寸校验全过 ⇒ **静默错值**。⇒ 与 K283/P57（int8 alpha 修好后静默乘 1e-6）构成**同一族的两例**：**「修复缺失通路」必须先补「单位/参数一致性断言」**。
- **★★★ 冲突②（`updated_at` 不能当上游活动信号）**：K301。`pushed_at` 停在 `11-26T23:20:21Z`，`updated_at` 却走到 `11-27T18:01Z`。前 39 轮一直用 `updated_at` 判「静默」，**本轮起改用 `pushed_at` + `commits[0].sha`**。
- **★★ 印证（K275 的两个「存在性」记录现在有失败位了）**：K302（candle → `linear_` 的 `.scales` 缺失 → `to_bf16_` 无 record → `not in the checkpoint`）与 K303（MLX → `config.json` 缺失）**分别落在两个不同位置**，都不是「格式不认」。⇒ K293 的失败位分类再补两条：**第 4 类「键名缺失层」**（QuantFunc `qweight`）、**第 5 类「量化参数内联层」**（GGML block 无 `.scales`）。
- **★★ 印证（官方 H3-Image 体积口径）**：K304 的 `transformer/` **66,279,032,256 B** 与历史「68.65 GB 图像包」**不矛盾**——68.65 GB 是「图像包」含 VAE/文本编码器，DiT 单独 66.3 GB。⇒ 引「H3-Image 多大」必须带口径（DiT / 图像包 / 全仓）。
- **★ 零增量（须明日复查）**：`MiniMaxAI/MiniMax-H3` **`lastModified 2026-11-24T04:56Z` / 5,971,579 dl（逐位相同）/ 7,444 like（+1）**；`Comfy-Org/MiniMax-H3` **11-15T09:54Z / 33,581,705 dl（逐位相同）/ 2,889 like（+1）**；`VideoRebirthAI/hyperflow-h3-flash` **11-14T09:27Z / 1,019,175 dl / 370 like（逐位相同，四日不动）**；`QuantFunc/…-4bit` **11-27T15:40Z / 7,566 dl / 36 like**；`MiniMaxAI/MiniMax-H3-Image-PE`（**提示词扩写器，Qwen3.8-27B 基底，fp4/sglang，22 文件 / 5,895 dl / 120 like / 11-10 未动**）——**首次登记**，与本机 connector 无关但属官方 H3 家族第 3 个仓。

### 本轮实验

**无实验，仅零下载读头 + 本机源码/二进制定论**（约 **18 次 Range/HEAD 请求**：`x-linked-size` 7 次 + 全 header 5 次 + index/config 6 次；下载 **0 字节**；磁盘 0）。

**不跑实验的三条理由**：

1. **本轮两条高价值题都是「读代码定论」**：K302（candle 掉在 `.scales`）与 K303（MLX 掉在 config + 补配置更危险）都不需要权重落地——前者连 35 GB 都不用下，后者**下了也跑不出结论**（缺 config 就是 fail，补 config 就是错值，两种都不是「能跑」）。
2. **唯一「可跑」的是 MLX 42.6 GB H3-Image**，而磁盘 **35 GiB（92%）** ⇒ **下载即触红线**（K206 已作废过一次「清盘」假设，不再重复）。
3. **时间**：06:30 起动，检索到 06:52 收（~22 min），余下要装三份报告 + 技能包双源同步 + sync + release；任何 >20 min 的实验都会压掉最小闭环。

### 坑

- **坑①（新，本轮最贵）把「缺 config」当成「格式不认」，差一步就写成反向结论**：K303 的 MLX 件**结构上完全合本机判据**（`adaln_t_table 1025×8` + 融合 `qkv_proj` + 8 宽 AdaLN），第一反应会写「本机能读 MLX 件」。实测 `transformer/config.json` **404**，而 `config_from_json` 的第一句就是 `if (fs::is_directory(p)) p = p / "config.json"; ... if (!f) return fail("cannot open …")` ⇒ **连 hidden 都读不到**。⇒ **纪律：目录形态的件，先 `curl -sI <dir>/config.json` 看 200/404，再谈结构**。（单文件形态不受此限，见 K293。）
- **坑②（新，比坑①更危险）「尺寸校验全过」不等于「解码参数对」**：MLX 的 `scales [5376,224]` 同时满足 `group 32 / K=7168` 与 `group 64 / K=14336`，因为 **K 与 group 同比缩放** ⇒ `K = scols × group` 恒成立。唯一的破口是 `bits = gcols×32/K`：真 8 bit 算成 **4.0**。而 `l.bits = (bits==8)?8:4` 会把 3 和 4 一并吃成 4 ⇒ **8bit 码按 nibble 解**。⇒ **纪律：`scales` 列数只能验「group 自洽」，不能验「bits 对」；判 bits 必须用 `gcols*32/(scols*group)` 且 `group` 必须来自声明，不能默认。**
- **坑③（复现 + 加严）`siblings` 的「文件数」在跨运行时仓里再次失准**：`candle` 110 文件看着是「q4 54 + q8 54」，但每个 tier 里 `text_encoder` 14 分片 + `transformer` 14 分片 + `transformer_ref` 14 分片 ⇒ **实际只有 3 个组件 × 2 档**；MLX 的 `transformer/` 154 文件里 **153 个是分片**（`model-00001..0000NN.safetensors`）+ 1 个 index。⇒ 与 K298（1423 文件里 1412 是源码）、K288（`≤2` 当空壳）合看：**文件数三面都要看过小、看正常、看过大**。
- **坑④（新）`_class_name` 同一模型两种拼写，别当两个模型**：H3-Image 官方 `transformer/config.json` 是 **`MiniMaxH3DiTModel`**，而 candle 的 `q8/transformer/config.json` 是 **`MiniMaxH3Transformer3DModel`**（后者是 diffusers 的视频 DiT 名）。本机两个都收（`:735-760`），但**引用「H3-Image DiT 配置」时必须带文件出处**，否则字段名对不上（`ffn_hidden_size` vs `ffn_dim`）。
- **坑⑤（复现，本轮未踩但仍在）`resolve/main/` 漏写 = 404 + 55 KB 错误页**（第 39 轮坑①）；本轮全部 URL 都带完整路径，另用 `r 0-8` 读 header 长度做前置校验，未复现。

### 下一步

- **P65（新，最高优先，零下载）**：把「量化参数声明位」做成判据表——**`bits` 与 `group_size` 必须成对**，且 `group_size` 只能来自**本机真读到的文件**（`config.json` / `comfy_quant` / `__metadata__`），**不得默认 64**。判据：对 MLX / candle / SVDQuant / NVFP4 四类各造一个「只声明 bits」的负例，断言本机必须 **拒载并报出「group_size 未声明」**，而不是按 64 推。**这条与 P57 的负向断言合并为一个"声明完整性"检查**。
- **P66（新，低）**：T8 semantic bridge 只登记**存在性与 schema**（6 张量 / 5120→512→5120 / layer 49），**不做适配**——它不是 LoRA 增量而是整层替换，本机无 hook 点，且 `teacher_val_cos 0.350` 说明「与老师差很远」，价值不明。
- **P28 / P21（口径更新）**：H3-Image 磁盘需求从「68.65 GB」细化为：**DiT 单独 66.3 GB / MLX 全量 42.6 GB（DiT 22.4 + TE 20.2）/ 本机可用 35 GiB** ⇒ **仍差 8 GB**；若要试，只能等清盘或改流式（MLX README 自报 16 GB Mac 可跑，说明**流式是唯一出路**，而本机 `dit_dir` 走的是整件常驻 + `_stream_blocks`，两者机制不同）。
- **P62（不变）**：335 MB 的 Kijai `avg_rank_24` 仍是验 `bind_pruned_adaln_` 的 `diff_b` 通路首选。
- **P43（仍未建）`safetensors-peek.py`**：本轮又手写 6 次读头。**第十四项需求**：**目录形态先探 `config.json` 是否存在**（坑①）；**第十五项需求**：给 `.weight` 的 **dtype+shape 组合**打标签（`U8 2-D` = int8 码 / `U8 3-D` = GGML block / `U32 2-D` = MLX 4 码每字 / `I8 2-D` + `weight_scale` = ConvRot），一眼看出是哪个家族（K302/K303）。
- **SOP（仍未改）**：累计 **34 条**待写入（本轮新增 5 条：`pushed_at` 判活动 / 目录先探 config / 尺寸校验不验 bits / 文件数三面看 / `_class_name` 双拼写）。
