# vpipe 每日知识增量（累积）

> 由「vpipe 后续计划任务·每日 4 轮夜间自动执行」系列自动化写入。
> **只追加，不覆盖**。每轮一节，按轮次编号递增。
> 相关文件：`vpipe-H3-部署与测试报告.md`（第 18 节）、`vpipe-后续计划任务.md`（状态看板）。

---

## 第 1 轮 · 2026-11-17 20:31 — 首轮：上游落差盘点 + HyperFlow H3 Flash

### 1.1 本轮检索范围

| 源 | 地址 | 取得方式 | 日期 |
|---|---|---|---|
| GitHub Releases | `api.github.com/repos/tgo-app-dev/vpipe/releases?per_page=10` | WebFetch | 2026-11-17 |
| GitHub Issues | `api.github.com/repos/tgo-app-dev/vpipe/issues?state=all&sort=created&per_page=15` | WebFetch | 2026-11-17 |
| GitHub compare | `api.github.com/repos/tgo-app-dev/vpipe/compare/9db5dd7...main` | WebFetch | 2026-11-17 |
| GitHub Commits | `api.github.com/repos/tgo-app-dev/vpipe/commits?per_page=40` | WebFetch | 2026-11-17 |
| GitHub docs 目录 | `api.github.com/repos/tgo-app-dev/vpipe/contents/docs` | WebFetch | 2026-11-17 |
| 本机版本 | `vpipe --version` → `0.1 (9db5dd7*0)` | 本地 | 2026-11-17 |
| 网络检索 | MiniMax H3 / HyperFlow / vpipe / FL2VA / Ref2VA 中英双语 | WebSearch | 2026-11-17 |

### 1.2 新增知识（12 条）

#### K1 ★ 本机落后上游 12 个 commit

- 本机：`vpipe 0.1 (9db5dd7*0)`（源码编译版，工作树带 `*` 即有本地改动）
- 上游 main HEAD：`4dc36b7`（2026-11-16）
- `compare/9db5dd7...main` → `status: ahead`、`ahead_by: 12`、`behind_by: 0`
- 之前记录的基线 `33cda00` 落在链条第 10 位 → **自上次同步以来上游又走了 2 步**（`81cd674`、`4dc36b7`）

上游这 12 个 commit 用诗化标题，按日期：

| 日期 | 标题 | 与本实验室的关系 |
|---|---|---|
| 11-03 | 部分片段自带 latents；hybrid 的 softmax 到达范围逐步推进；Fibo 2.0 四百万像素 | 低 |
| 11-05 | 用 MiniMax-H3 权重出图；int8 下 Mac 没有矩阵核心时的加速器；从内存读长提示词 | 中（出图路线） |
| 11-06 | 逐位复现的生成；运行中模型持有的内存；阶段结束即释放生产者 | 中（可复现性） |
| 11-07 | 分块读权重、四块并发；片段自带 autoencoder 解出的静帧；被拒的媒体调用会说明它收到了什么 | 低 |
| 11-08 | 单独一段音轨也能当参考；太短无法合并的参考片段不再被拒 | **高（音轨参考）** |
| 11-09 | RIFE 帧插值；2K 下上下文精修的草稿 | 中 |
| 11-10 | 节拍跟踪；图像阶段只持有一次画面；**经 MiniMax-H3 的 Image VAE 出图** | **高（第三条文生图路线）** |
| 11-11 | **MiniMax-H3 上的图像模型**；NVIDIA NVFP4 4-bit 权重 | **高（图像 + 量化）** |
| 11-12 | **MiniMax-H3-Image 图：DiT 在 M5 上跑 int8**，以及该模型该关掉哪些层级 | **高（M5 上省内存）** |
| 11-13 | MiniMax-H3 的 DiT 跨主机切分：tensor-parallel/1 | 低（单机用不上） |
| 11-14 | **RelayVSR 的 4x 流式超分**；跑适配器、int8 层级和解码的切分 rank | 中 |
| 11-16 | 更多 DiT 切到两台 Mac；MiniMax-H3 对长提示词分带、对长片段逐行寻址 | 中 |

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

| Issue | 状态 | 内容 | 对我们的意义 |
|---|---|---|---|
| **#55** | Open，0 回复 | MiniMax-H3 **持久性时间纹理「沸腾」**；作者认为 sampler spec 的 iport 对该族无效、FlowMatchEuler 没有随机项。涉及 `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`（**正是我们 768p Ref2VA 用的适配器**）、`video_shift=12.0` / `audio_shift=3.0` / `condition_timestep=1.0` | **高**。作者实测 HF jitter：静态参考 0.0000 / 8 步 0.0502 / 16 步 0.0437 / **4 步 0.0914**；shift 12→6 把 0.0512→0.0436，但**作者明说日志打印可能误导** |
| **#47** | Closed，2 回复 | Model Config 设 `video_shift=6`，Generate Video 阶段却用 12 | **★ 关键**：#55 补充说明 —— `video_shift` **实际能到达 denoiser**，但 `GenerateVideoStage` 的日志**始终打印 12.0/3.0**。这既**印证**了我们「shift 写错完全静默」的机制，又说明**不能相信日志里打印的 shift 值** |
| **#56** | Open + PR | FastH3-Omni 的 VSA 压缩门控与路由预算；`attn.to_gate_compress.weight` 名称映射不认识 → checkpoint 被拒（PR 已实现映射 + VSA 路由预算 + cube tile 划分 + 单测） | 中（未来新模型） |
| **#59** | Open，0 回复 | RelayVSR 原生 **2x** checkpoint（`lightx2v/RelayVSR_X2`）；现有阶段只接受 `upscale_factor=4`；H3 的 896×512 / 768×1344 / 720p 素材通常只需 2x，4x 再 Lanczos 缩放既浪费像素也可能让 36 GB 机器内存不足 | 中（超分路线） |
| **#44** | Closed，3 回复 | MiniMax-H3 Ref2V Turbo 4-step LoRA **持久偏心构图**（768×544、shift 12/3、4 次 denoise）；作者称 Draw Things 用同一适配器无此问题 → 疑似 vpipe 实现方式导致 | **高（4 步适配器构图偏差）** |
| **#49** | Open，1 回复 | HF 上 40 GB BF16 `10Eros_Max_h3_TURBO-hybrid_beta5.safetensors` 量化卡在 shard 阶段（`arch='unknown' layer_prefix='' n_layers=0`） | 中（量化坑） |
| **#41** | Open，1 回复 | 4-bit（w4 g64）权重坏：Z-Image 挂起 / GPU 错误，Qwen-Image-2.1 静默输出全透明图 | 印证我们「P5 建议跳过」 |
| **#57** | Closed，5 回复 | 最新 release 里 ANE 前馈内存不足 | 低（M5 不开 ANE） |

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

| 问题 | 现象 | 处置 |
|---|---|---|
| **全量 `git clone` 会被 SIGTERM 打死** | 仓库 `size: 216,872 KB ≈ 212 MB`（41 个视频占大头），克隆到 137（SIGKILL） | 改为**常驻工作副本** `/Users/minichen/WorkBuddy/2026-11-12-21-10-11/.vpipeworkflow`，每轮只 `git pull --ff-only` 增量 |
| **`--filter=blob:none` 部分克隆不可用于 checkout** | `git ls-tree -l` 会为每个缺失 blob 单独回源（395 次往返）→ 同样被打死 | 不用部分克隆做同步；只把它当只读探测工具 |
| **仓库缺 `report/` 目录** | 两份主报告（149 KB / 37 KB）**从未进过 GitHub** | 本轮补上（`docs/reports/`） |

#### K14 云端对照基线（SiliconFlow）

2026-11-03 上线 `MiniMaxAI/MiniMax-H3`：`duration` 5–15 s、`resolution` 480p/768p、`images` 用 `role` 指定 `first_frame` / `last_frame`；
**`negative_prompt` 与 `image_size` 不再生效**（传入不报错但被忽略）。
→ 可作为 768p / 时长行为的外部对照（但本机 HF 直连不通、云端 API 也需要 key，优先级低）。

### 1.3 与既有结论的印证 / 冲突

| 既有结论（报告节） | 本轮关系 | 说明 |
|---|---|---|
| 17.x「shift 规则按适配器分叉」「shift 写错完全静默」 | **印证 + 补强** | #47 + #55 从上游侧确认：`video_shift` 能到达 denoiser，但日志**恒印 12.0/3.0**。→ 我们的量化（对比出片而非看日志）方法是对的；**新增纪律：报告里不得引用日志里的 shift 值作为证据** |
| 16.x「四段式续接 Δ亮度 1.1→8.6→13.3」 | **上游已修** | K3：上游把续接变暗归因于 MiniMax H3 VAE+DiT 并已修。→ 升级后需重跑续接实验；**但几何跳变（+76/−86 px）是另一个问题，不能指望一并解决** |
| 16.x「4 步适配器必须同时改 steps，否则静默劣化」 | **语义可能已变** | K4：上游把 steps 语义改成与 ComfyUI/diffusers 对齐 → 需在新版上重测 steps 曲线 |
| 「细节能量会把噪点当细节」 | **旁证** | #55 的 HF jitter 指标（静态参考 0.0000 / 4 步 0.0914 / 8 步 0.0502 / 16 步 0.0437）是**另一条独立的抖动度量**，与我们的「颗粒量 vs 纹理量」互补 |
| 「P5 图像 4-bit 量化建议跳过」 | **印证** | #41 仍 Open：Qwen-Image-2.1 在 4-bit 下静默输出全透明图 |
| 8.x「SSIM 两口径差约 0.03（YUV 4:2:0 往返）」 | **可消解** | K2：FFV1 支持 4:4:4 → 差值应能压到很小，**这个 0.03 不该被当成「固有开销」** |

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
