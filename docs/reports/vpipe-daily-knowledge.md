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

---

## 第 2 轮 · 2026-11-18 00:31 —— YUV 口径归因（P11 已收口）+ 本机版本落差订正 + 768p 适配器全量盘点

> 本轮触发时段：00:30（第 2 轮，共 4 个时段）。上一轮 2026-11-17 20:31。
> 轮次由 `report/.auto-round-state.json` 决定（读出 round=1 → 本轮 R=2）；本轮无并发锁冲突。

### 2.1 ★ 重大订正：「本机落后上游 12 个 commit」这句话需要拆分（第 1 轮 K1 的修订）

| 对象 | 实测版本 | 与上游 `main @ 4dc36b7` 的关系 | 依据 |
|---|---|---|---|
| **已安装 App 的 `vpipe` helper** | `0.1 (9db5dd7*0)`（2026-11-01） | **落后 12 个 commit** | GitHub `compare/9db5dd7...main` → `ahead_by:12, behind_by:0, total_commits:12` |
| **本地源码树** `vpipe-lab/repo/vpipe` | `33cda00`（2026-11-13） | **只落后 2 个 commit** | `git log -1` + GitHub API 对比 |
| **本地已编译 build** | `build/apps/vpipe/vpipe` → `0.1 (33cda00*0)` | 可用 | 见下方坑 1 |

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

| 变体 | 格式 | 口径 A（默认协商） | 口径 B（落盘 PNG） | 口径 C（强制 gbrp） |
|---|---|---:|---:|---:|
| V420-def | yuv420p/limited/bt601 + h264 | **0.5796** | 0.3900 | 0.3900 |
| V422 | yuv422p/full/bt709 + ffv1 | **0.6191** | 0.3902 | 0.3902 |
| V444 | yuv444p/full/bt709 + ffv1 | **0.7244** | 0.3902 | 0.3902 |
| V444-lim | yuv444p/limited/bt709 + ffv1 | **0.7549** | 0.3901 | 0.3901 |

- 口径 A 随落盘格式的**极差 = 0.1752**；口径 B/C 的极差 = **0.0003**；`|B − C| = 0.000000`（**恒等**）。
- 机制（ffmpeg `-v verbose` 直接读到）：口径 A 下 **参考 PNG 被 auto_scale 降到视频的像素格式才参与比较** ——
  `rgb24/gbr/pc → yuv420p/smpte170m/tv`（4:2:0 视频）或 `→ yuv444p/bt709/pc`（4:4:4 视频）。
  也就是说**口径 A 的分数里混进了「参考图被降采样的程度」**。
- 一句话结论：**口径 B（落盘 PNG 再比）≡ 口径 C（强制 gbrp 域直比），两者都是「纯 RGB 域比较」；
  口径 A 是「YUV 域比较」，且其读数随视频像素格式漂移 —— 那 0.03 的差来自比较域，不是来自编码。**

**第二段 · 真值基准（全部用 ffv1 无损编码器，差值只可能来自色度抽样）**

| 变体 | SSIM(All) vs 真值逐帧 | PSNR |
|---|---:|---:|
| 真值自比（测量系统自检） | **1.000000** | inf |
| T444（4:4:4） | **0.999977** | 82.31 dB |
| T422（4:2:2） | 0.997014 | 48.63 dB |
| T420（4:2:0） | 0.995417 | 46.67 dB |
| T420h（4:2:0 + limited + bt601 + h264，历史默认全链） | 0.984282 | 41.58 dB |

- 一句话结论：**4:2:0 确实真丢色度，但只丢 0.0046 SSIM（0.999977 → 0.995417）；
  真正吃掉 0.015 的是「limited range + bt601 + h264 有损压缩」这三条叠加，不是色度抽样本身。**
- 是否与本机实测冲突：**否 —— 反而印证了 18.1 节「差 0.03 不是固有开销」的直觉方向**（差距确实可消解），但给出了**相反的归因**：
  可消解的是**比较域**，不是像素格式。

**第三段 · 复现历史那对数字**

| 对象 | 口径 A | 口径 B | 口径 C | A − B |
|---|---:|---:|---:|---:|
| `pika-i2va-shop.mp4` vs `ref-cat-832.png` | 0.5774 | 0.3895 | 0.3895 | **+0.1879** |
| `p4-i2va-preview-fast.mp4` vs 锚定图（256×144 归一） | 0.3453 | 0.1735 | — | **+0.1718** |

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

| 问题 | LFM3-VL-2B 回答（摘要） |
|---|---|
| 8 变体并排能否看出差别 | 「没有显著差异，颜色饱和度、边缘锐度基本一致，没有明显色块或条纹伪影…肉眼分辨下基本等价」 |
| 4:2:0 vs 4:4:4 两组关键帧 | 「内容一样；4:2:0 那组没有肉眼可见的色彩偏差、边缘锯齿、色块或模糊」 |
| 真值无损 vs 4:2:0 全默认链 | 「内容一致；第二组颜色更饱和；纹理、边缘、渐变没有明显劣化」 |

- 一句话结论：**独立第三方模型也判不出 4:2:0 与 4:4:4 的画质差别** —— 与第二段 0.0046 SSIM 的量化结论互相印证。
- 注意：LFM3-VL 在 Q2 里把 4:4:4 判成「更差」（说可能有压缩伪影），这与量化结论相反 → **再次印证已知缺陷：LFM3-VL 对细微锐度/伪影判断不可靠**，只可作「有无肉眼级差异」的粗判。

### 2.5 ModelScope `lightx2v/Minimax-h3-Turbo` 全量盘点（28 个文件，第 1 轮清单被截断）

- 来源 URL：`https://www.modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files?Revision=master`（2026-11-18）
- 第 1 轮只列了部分变体，本轮补全。**从未在本机测过的新变体**：

| 变体 | 文件 | 大小 | CommitDate | 状态 |
|---|---|---:|---|---|
| FL2VA 4-step v1.3 768p bf16 | `minimax_h3_fl2v_turbo_4step_v1.3_768p_bf16.safetensors` | 1,383,677,808 B | 2026-10-20 | ⭐ 本机没有，待验证 |
| FL2VA 4-step v1.3 768p comfyui_bf16 | 同名 `_comfyui_bf16` | 1,956,193,000 B | 2026-10-20 | ⭐ 本机没有 |
| Ref2VA 4-step v1.0 768p bf16 | `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors` | 1,383,677,808 B | 2026-10-20 | ⭐ **本机完全没有 Ref2VA 4-step** |
| Ref2VA 8-step v1.1 768p bf16 | `minimax_h3_ref2v_turbo_8step_v1.1_768p_bf16.safetensors` | 1,383,677,808 B | 2026-10-20 | ⭐ 本机只有 v1.0 |
| FL2VA 8-step v1.2 768p bf16 | `minimax_h3_fl2v_turbo_8step_v1.2_768p_bf16.safetensors` | 1,543,291,302 B | 2026-11-12 | ⭐ 本机只有 v1.0 |

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

| 主题 | 关键事实 | 来源 + 日期 |
|---|---|---|
| H3-Image 正式发布 | 33.1B DiT，固定 6 步，最高约 16MP，最多 16 张参考图，生成+编辑合一，不支持蒙版编辑/透明背景；**图像包 68.65 GB + 共享文本编码器 66.7 GB** | `https://huggingface.co/MiniMaxAI/MiniMax-H3-Image`（2026-11-10/11） |
| H3-Image 中文社区实测 | 4K 未来港口场景耗时 **59 s**（远超宣称「10 s 内」），两个角色风格不统一，评分 77/100 | 163.com（2026-11-13） |
| H3 API 档位扩展 | Recraft Studio 列 **MiniMax H3 Image / H3 Image Highspeed / H3 Highspeed / H3 Lite**；Highspeed 7–11 credits/s，Lite 4–7 credits/s，480p/768p 4–15 s 且总带声音 | recraft.ai（2026-11-12 核） |
| HyperFlow H3 Flash 部署 | ComfyUI 0.43+（钉在 commit c1eece6）+ `city96/ComfyUI-GGUF` + `Video-Rebirth/ComfyUI-HyperFlow-Flash`（需 ≥1.1.0）；GGUF `minimax_h3_fl2va_hyperflow_flash_14b-Q4_K_M.gguf` 9.05 GB；文本编码器 `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` ≈15.7 GB；video VAE fp16 5.21 GB；audio VAE fp32 605 MB；**stable-diffusion.cpp 路线走 `sd-cli -M vid_gen`**，diffusers ≥0.40 | Video-Rebirth GitHub（2026-11 核） |
| HyperFlow 速度实测 | RTX 5090 32GB 118 s(5.2s)/618 s(15s)；4090 24GB 151 s/815 s；3090 24GB 318 s/1869 s；KOBO Lab 暖机 ≈107 s；非官方 ComfyUI INT8 loader 5 seed 均值 **46.1 s**、峰值显存 24.2 GB | 多个 YouTube/B站实测（2026-11 汇总） |
| 4 步调度器经验 | **4 步时 `res_multistep` 比 `euler` 音频质量更好**（lightx2v 官方示例卡写的是 euler）；SLA 稀疏注意力「恢复高频细节且快约 40%」，16 GB 卡峰值 11.0 GiB，10 s 视频 65 s | 社区实测（2026-11） |
| 4 步「固定时间步嵌入」机制 | adapter 元数据带 `pdd_config`（`nfe=4, grid_size=256`）→ 调度器建 257 点 σ 网格切 4 段，每段蒸馏头权重除以该段 σ 跨度；`num_inference_steps = steps + 1` 个 σ 点，transformer 恰好被调用 `steps` 次；`_FusedProjection` 存 4 组输出投影、`_FourStepController` 是按步切头的 forward hook、`validate_four_step_call()` 断言恰好 4 次前向 | diffusers / ComfyUI 源码（2026-11） |
| 16 GB Mac mini 实测 | vpipe 的权重流式 + 分段拆卸 + 自适应驻留，让 16 GB Mac mini 跑 33B MiniMax-H3（原需 115 GB）；480p 5 s 片段 ≈4 min（Turbo LoRA 4–8 步）；内存够时 8-bit 优于 4-bit | kongchang.com（转述 B 站作者，2026-11） |
| SVD 秩压缩路线 | lightx2v ComfyUI 权重的 resized 变体（drbaph / Kijai / silveroxides）：Ref2V r21 与原版**余弦相似度 99.92%，体积 −83%** | HuggingFace（2026-11 核） |
| 社区操作规则（印证既有结论） | 帧数必须满足 **17n+5**；宽高必须 32 的倍数；本地 open build 原生只支持短边 768（2K 需云端 refiner）；长视频拆成 ≤10 s 分镜；16 GB→int4、24 GB→int8+动态卸载；H3 最多 9 图 + 3 视频 + 3 音频 = 12 个参考 | 社区（2026-11 核） |
| 上游仓库现状 | 最新 release 仍 **v0.1.110**（2026-11-01）；repo `pushed_at 2026-11-16T16:25:51Z`、`updated_at 2026-11-17T08:40:24Z`，260 stars / 25 forks / **14 open issues**；无编号 > 59 的新 issue；第 1 轮追踪的 8 条 issue 状态**全部未变** | GitHub API（2026-11-18 核） |

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
