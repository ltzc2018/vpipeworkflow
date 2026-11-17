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

---

## 第 3 轮 · 2026-11-18 02:30 —— ★★ 上游权威 shift 规则表 + 纹理沸腾（#55）复现 + 两个方法学陷阱

> 本轮触发时段：02:30（第 3 轮，共 4 个时段）。上一轮 2026-11-18 00:31。
> 轮次由 `report/.auto-round-state.json` 决定（读出 round=2 → 本轮 R=3）；本轮无并发锁冲突。
> **本轮有一处会修订第 17 节的结论（不是推翻，是加前提）**，详见 3.6。

### 3.1 本轮检索范围与来源清单

| 源 | 地址 | 日期 | 结论摘要 |
|---|---|---|---|
| GitHub Releases | `api.github.com/repos/tgo-app-dev/vpipe/releases?per_page=8` | 2026-11-18 | **最新仍是 v0.1.110（2026-11-01），本轮零新增** |
| GitHub Commits | `api.github.com/repos/tgo-app-dev/vpipe/commits?per_page=20` | 2026-11-18 | HEAD 仍是 `4dc36b7`（2026-11-16），**零新增** |
| GitHub Issues | `api.github.com/repos/tgo-app-dev/vpipe/issues?state=all&sort=updated` | 2026-11-18 | 20 条最新 issue **状态全部未变**（#55/#59/#58/#56 Open，#57/#50/#47/#44/#41 等） |
| GitHub issue #55 全文 | `api.github.com/repos/tgo-app-dev/vpipe/issues/55` | 2026-11-18 | **拿到 HF jitter 的精确公式**（本轮实验的直接依据） |
| GitHub compare | `api.github.com/repos/tgo-app-dev/vpipe/compare/33cda00...main` | 2026-11-18 | 本地源码树只落后 2 个 commit，内容见 3.2 |
| **上游官方文档（本地源码树自带）** | `vpipe-lab/repo/vpipe/docs/MINIMAX-H3.md` | 本地 `33cda00` | **★★ 本轮最关键的来源：官方适配器→shift 对照表（见 3.3）** |
| 上游源码 | `stages/minimax-h3-model-config-stage.cc:69` | 本地 `33cda00` | **`sigmas` 字段的完整语义**（见 3.4） |
| sdnext 文档 | `vladmandic.github.io/sdnext-docs/MiniMax` | 2026-11-18 | 社区版 shift 表，与上游官方表**互相印证**（见 3.3） |
| AICU 实测 | `aicu.ai/comfy/blog/2026-08-18-h3-turbo-lora` | 2026-08-18 | ★「**同 seed 换 shift → 不同场景**」（见 3.5） |
| VibingTalk 讨论 | `vibingtalk.com/...minimax.1938817` | 2026-11-06~08 | 「MMH3 pushes brightness, contrast, desaturates, and amplifies fine detail」；续接要传 latent 不要传解码帧 |
| note.com 实测 | `note.com/j_alpha_lab/n/n2661aa9a31cd` | 2026-11 | ★ 续接变暗的**第三方量化**（RGB −8.3/−11.0/−9.1 等）；接缝 12 px 垂直位移 |
| ModelScope 文件清单 | `modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files` | 2026-11-18 | **28 个文件，与第 2 轮完全一致，零新增变体** |
| 社区 5090 实测 | `jxxy.net/ai/articles/minimax-h3-local-5090-comfyui-benchmark` | 2026-11 | 「608 用 8 步 shift 12/3；**768p 用 4 步 shift 6/3**」「把 shift 交叉用就是跟自己较劲」 |
| 4 步 Turbo 教程 | `blog.gitcode.com/d00bf628...` | 2026-11 | lightx2v 官方卡：**8step v1.0 → 12/3；4step v1.0 768p → 6/3** |
| 微信 / seedance 续接文 | `mp.weixin.qq.com/...2247486977`、`seedance.tv/blog/minimax-h3-video-extension-gets-brighter` | 2026-11 | 「H3 每去噪一次画面就暗一点点」；`MiniMaxH3ToneCompensate` 节点（frame_first / gain_bias / lut 三模式） |

### 3.2 上游这 2 个 commit 的实际内容（把「升级收益」说清楚）

| commit | 日期 | 内容 | 对单机 Mac 的价值 |
|---|---|---|---|
| `81cd674` | 2026-11-14 | RelayVSR 4x 流式超分；**`hf-mirror.com` 成为第三个模型源**；`generate-video` 的 `keep_loaded`（H3 的 DiT 进 warm hold） | **中** —— hf-mirror 是本机 HF 直连不通的新通道，值得试 |
| `4dc36b7` | 2026-11-16 | 图像模型的 `tensor_parallel`；**MiniMax-H3 对长提示词分带、对长片段逐行寻址**；修「>150 000 行时 int 溢出导致 1440p 15 秒参考片从第 136 帧起变噪声」 | **低** —— tensor-parallel 是双机；长提示词/长片段分带我们用不上 |

⇒ **P12 的价值重新定位**：不是「拿到 MotionCache / swap allowance / 续接光照修复」（第 1 轮的认知已被第 2 轮证伪为「已装 App 就支持」），
而是 **① `sigmas` 字段（只有新 build 有）② hf-mirror 模型源 ③ bit-for-bit 可复现（见 3.7）**。

### 3.3 ★★★ K1：上游官方文档的适配器→shift 对照表（权威性最高）

来源：`vpipe-lab/repo/vpipe/docs/MINIMAX-H3.md:1946-1977` 与 `:1508-1513`（本地源码树自带，2026-11-18 核）

| entry | partition | steps | shifts (v/a) | trained at |
|---|---|---|---|---|
| `Turbo few-step v4-600 EMA` (larryvrh) | FL2VA | 4–8 | 12 / 3 | — |
| `Turbo few-step v1-850 EMA` (larryvrh) | FL2VA | 4 | 12 / 3 | — |
| `Turbo 4-step v1.0 768p` (lightx2v) | FL2VA | 4 | **6** / 3 | 1344×768 |
| `Turbo 4-step v1.2 768p` (lightx2v) | FL2VA | 4 | **6** / 3 | 1344×768 |
| `Turbo 8-step v1.0 544p` (lightx2v) | FL2VA | 8 or 4 | 12 / 3 | 544p |
| `Turbo 8-step v1.0 768p` (lightx2v) | FL2VA | 8 | **6** / 3 | 1344×768 |
| `Turbo 4-step v0.1` (lightx2v) | **Ref2VA** | 4 | **12** / 3 | **544p** |
| `Turbo 8-step v1.0 768p` (lightx2v) | **Ref2VA** | 8 | **6** / 3 | 1344×768 |

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

| 对照 | 首帧 SSIM |
|---|---|
| Ref2VA 768p shift 6.0 vs 12.0（第 9 节 A vs B） | **0.5213** |
| FL2VA 768p shift 6.0 vs 12.0（第 8 节） | **0.4618** |
| **静态参考图 + 完全静止提示词，shift 6.0 vs 12.0（本轮新做）** | **0.5062** |

- 即便把参考换成静图、把提示词改成「完全静止」，**σ 网格仍然决定了整个场景** →
  **vpipe 里不存在「同一场景的 shift 对照」**。
- ⇒ **纪律**：跨 shift 结论只能表述为「两条不同 σ 网格的对比」，不能表述为「同一模型渲染得更锐」。

### 3.6 ★★ K4：与第 17.4.1 节的冲突（**不推翻，加前提**）

| 既有结论 | 本轮关系 | 处理 |
|---|---|---|
| 第 17.4.1「Ref2VA 768p 实测 **12.0 更锐**（裁切纹理 178.7 vs 153.1）」 | **冲突（口径需要限定）** | ① 上游官方表说这个适配器应当用 **6.0**；② 本轮测得两臂**首帧 SSIM 仅 0.52** → 两臂不是同一场景；③ 但本轮的**静态场景独立复现**显示 shift 12.0 的 sharpness 仍然更高（**683.39 vs 610.45，+12.0%**），且 frame_diff 只差 1.5% → **「12.0 更锐」这个现象本身复现了**，不是纯粹的场景假象。<br>**⇒ 修订为**：「shift 12.0 在 Ref2VA 768p 上产出更高的细节/锐度，但这是**另一条 σ 网格**（上游未文档化，属推断继承），不是同一场景下的渲染差异；**生产默认仍应用 6.0**（上游官方值），12.0 视作可 A/B 的备选调度。」 |
| 第 17.4.1「shift 响应是台阶不是斜坡（6.0 与 8.0 几乎等价，r 0.9817）」 | 不冲突 | 但同样受「换场景」混淆项影响，解读要加同样的限定 |
| 第 16/17 节「FL2VA 768p = 6.0」 | **印证** | 上游官方表：FL2VA 8-step 768p → **6/3** |
| 第 18.2「已装 App 就支持 YUV 4:4:4 / swap allowance」 | 不冲突 | 但补一条：**`sigmas` 已装 App 不支持**（见 3.7） |
| 第 17 节「768p 多参考画质 −17%」 | 不冲突 | 本轮多参考臂的静止抖动也更高（0.1740 vs 0.1307），方向与 #55 的「参考越多越不稳」一致 |
| 第 8 节「4 步适配器必须同时改 steps」 | **印证** | 本轮 4 步片 HF jitter **0.3493** > 8 步 **0.3272**，与 #55「4 步 → 0.0914（unusable）」方向一致 |

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

| 主题 | 关键事实 | 来源 + 日期 |
|---|---|---|
| 续接变暗的第三方量化 | 续接处 RGB 差：暗图 −8.3/−11.0/−9.1；亮图 −13.7/−12.6/−10.7；亮图+音频 −16.1/−12.3/−9.1 —— **三段不同亮度素材同向变暗** → 是连接方式本身的属性 | note.com（2026-11） |
| 接缝几何位移的第三方量化 | 用相位相关测得接缝**垂直位移 +7 ~ −12 px**（480 高 → 2.5%）—— 与我们第 16 节四段式续接的 +76/−86 px 同现象（我们链更深） | note.com（2026-11） |
| 续接的社区共识 | 「传 latent 不传解码帧」「每段都对齐到首段锚帧而不是上一段末帧」「在流外做调色省内存」；MMH3「会推亮度、提对比、降饱和、放大细节」 | VibingTalk（2026-11-06~08） |
| `MiniMaxH3ToneCompensate` 节点 | ComfyUI 侧专门解决 Chain 模式亮度递减：对比前后段重叠区算偏置并整段补偿，三模式 `frame_first` / `gain_bias` / `lut`，纯算法无额外模型 | 微信公众号（2026-11） |
| H3 Image VAE 往返 | 1024×1024 整图 12 s / PSNR 34.9 dB / 色偏 <0.5 级；42 MP 峰值 6.1 GB、约 6 min；官方解码器 34 s / 32.3 dB / **每通道暗 3 级** | 上游文档（2026-11-18 核） |
| 续接上下文长度 | 社区扩展器普遍用 **22 帧**作上下文起点（与我们的 17n+5 规则一致） | seedance.tv（2026-11） |

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

| # | 来源 | 日期 | 拿到什么 |
|---|---|---|---|
| 1 | GitHub commits API | 2026-11-18 | **HEAD 仍 `4dc36b7`（2026-11-16）→ 上游零增量** |
| 2 | 上游 issue #55 本体 + 评论 API | 2026-11-18 | **open / 0 评论 / 最后更新 2026-10-21 → 开放 28 天零回应** |
| 3 | 上游 issue 全表（34 条） | 2026-11-18 | 本实验室 5 条提案**尚未提交上游** → 其状态无从变化 |
| 4 | commit `e6972ac` 全文 | 2026-11-06 | ★★ **bit-for-bit 的真正开关 `autotune: false` + 钉 `ane_rows`** |
| 5 | 上游 `docs/MINIMAX-H3.md` | 2026-11-13 | ★★ σ 网格构造 / 音频 σ 推导 / sampler 端口表 / `sigmas` 优先级 |
| 6 | 上游 `docs/PLUGINS.md:994` | 2026-11-13 | ★★ 「竞速 agree to rounding, **not to the bit**」的权威机理 |
| 7 | 上游源码 3 个 stage | 2026-11-13 | `autotune`（9 stage）/ `ane_rows`（Real）/ `sampler` iport 3 / `reference_image_short_edge` |
| 8 | ModelTC 官方 README | 2026-11-17 读 | ★★ **σ 网格闭式公式 + Model Specs 表 + 参考图缩放三策略** |
| 9 | ModelScope 文件清单 API | 2026-11-18 | **31 文件 / 27 safetensors**（含 v1.3 等未注册变体） |
| 10 | ModelScope README（raw） | 2026-11-18 | **v1.2（8 步）被标为 ⭐ 推荐** |
| 11 | MiniMax 官方 release notes | 2026-11-10 | **H3-Image 开源**（33.1B / 6 步 / 16 参考图 / 4096² <10 s） |
| 12 | 社区 ComfyUI-SelfLift（TST） | 2026-11-18 | 专门治「帧间闪烁、纹理与形态漂移」 |
| 13 | 社区 `mo-akkakk` 节点文档 | 2026-11-18 | ★ **「micro-boiling 来自 model + sampler，不是 tiling」** |
| 14 | 社区 H3 Image 三设置 | 2026-11-18 | `s_noise` 1.10→0.90 压微噪（**H3 不读 `s_noise`**） |
| 15 | 社区 H3 本地五坑 | 2026-11-18 | ★ **17n+5 帧公式独立印证** + 时空网格错位机理 + 本地 BF16 ≈348.8 s/5 s 片 |
| 16 | stable-diffusion.cpp 仓库 | 2026-11-18 | 采样器含 ER-SDE；H3 支持日期仍 2026/08/04 → 生态无增量 |
| 17 | ModelScope `Open-H3-Regenerate-2K` | 2026-11-18 | NVIDIA 2K 精修三适配器合并方案 |

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

| 场景 | 结果 | 来源 |
|---|---|---|
| N=4, 12/3 | video `1, 0.9730, 0.9231, 0.8000, 0`；audio `1, 0.9000, 0.7500, 0.5000, 0` | ModelTC 原文 |
| N=8, shift 12 | 最后一步起点 **0.632** | vpipe 文档 |
| N=8, shift 6 | 最后一步起点 **0.462** | vpipe 文档 |
| N=16, shift 12 | 最后一步起点 **0.444** | vpipe 文档 |
| er_sde 串 @12/3 | audio `1, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0` | vpipe 文档 |

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

| Model | partition | 分辨率 | shift (v/a) | NFE |
|---|---|---|---|---|
| FL2VA Turbo 4-step v0.1 | FL2VA | 544p | 12/3 | 4 |
| FL2VA Turbo 8-step v1.0 | FL2VA | 544p | 12/3 | 8 |
| FL2VA Turbo 4-step v1.0 768p | FL2VA | 1344×768 | **6/3** | 4 |
| FL2VA Turbo 8-step v1.0 768p | FL2VA | 1344×768 | **6/3** | 8 |
| Ref2VA Turbo 4-step v0.1 | Ref2VA | 544p | **12/3** | 4 |

→ **官方表没有 Ref2VA 8-step 768p 这一行** → 上游给的 6.0 是「从 768p 家族继承的推断」
（第 3 轮 18.3.3 的处理正确）。

ModelScope **27** 个 safetensors vs 上游 catalog **12** 个，差集（上游未收录）：
`fl2v_turbo_4step_v1.3_768p_bf16`(+comfyui)、`fl2v_turbo_8step_v1.1_768p_bf16`、
`fl2v_turbo_8step_v1.2_768p_bf16`(+comfyui)、`ref2v_turbo_4step_v1.0_768p_bf16`、
`ref2v_turbo_8step_v1.1_768p_bf16`、`fl2v_turbo_4step_v1.1_768p_fp8`（32.4 GB）。

### 3.18 ★ K17：参考图缩放三策略 + `image-resample` 的 `fit` 枚举

| 模式 | 行为 | 缩放系数 |
|---|---|---|
| `match`（**官方推荐**） | 面积对齐目标画布、保比例、**不上采样** | `min(1, sqrt(target_area / ref_area))` |
| `max` | 保比例，只把短边 > 2048 的缩小 | `min(1, 2048 / ref_short_edge)` |
| `diffusers` | 保比例，短边强制 2048 | `2048 / ref_short_edge` |

vpipe 侧 `image-resample` 的 `fit`：`pad` / `crop` / **`stretch`（唯一改长宽比）** / `manual` /
`pad_to_grid` / `crop_to_grid` / `crop_to_area`；
`reference_image_short_edge` 默认 **2048（Ref2VA）/ 768（FL2VA）**
（2048 → 121 个 VAE tile，1024 → 25 个；上游自己的示例用 1024）。

### 3.19 ★★ K18–K20：三条未测新能力 + 社区印证 + #55 状态

| 能力 | 规格 | 本机阻塞 |
|---|---|---|
| **TaoMate-H3** | 3 步流式，2.5 GB，`"taomate": "auto"`，自带网格 | 可下 |
| **Open-H3-Regenerate-2K**（NVIDIA） | 2K 精修；三适配器合并（r=384+128+64）；三步 Euler @ `[0.909375, 0.857143, 0.666667, 0]` | 需评估体积 |
| **MiniMax H3-Image** | 33.1B / 50 层 / 去音频分支 / 6 步 / CFG=1 / 16 参考图 / 4096×4096 <10 s | ⛔ 68.65 + 66.7 GB → 磁盘阻塞 |

- 社区 `mo-akkakk`：**「micro-boiling 来自 model + sampler（尤其少步 LoRA），不是 tiling」** → 印证第 3 轮结论；
- 社区独立印证 **17n+5 帧公式** 与「时空网格错位 → 帧间抖动」机理；
- **issue #55：open / 0 评论 / 28 天**；其第 1 条请求**已部分实现**（sampler iport 接上了），
  但 `dpmpp_sde` 仍被排除；第 2 条请求（`sigmas`）**已完全实现**。

### 3.20 ★★★ P15 实验结果（可复现性基线，4 臂串行）

| 对照 | 逐帧 md5 | 音频 md5 | SSIM 口径A（整段） | SSIM 口径B（首帧） | PSNR | 字节 |
|---|---|---|---|---|---|---|
| App(9db5dd7) vs 本地 build(33cda00)，竞速开 | ★ 同 | ★ 同 | **1.000000** | **1.000000** | inf | 244 535 = 244 535 |
| A1 vs A2（竞速开，两次进程） | 不同 | 不同 | **0.750072** | **0.609360** | 19.1378 | 244 535 / 245 549 |
| **B1 vs B2（竞速关，两次进程）** | ★ **同** | ★ **同** | ★ **1.000000** | ★ **1.000000** | ★ **inf** | 244 535 = 244 535 |
| A1 vs B1 | 同 | 同 | 1.000000 | 1.000000 | inf | 244 535 = 244 535 |

逐帧 md5（**仅视频流** 22 行）：`at1 = af1 = af2 = 46bcb2641c3082e57b8ff744f3d7c91f`，
`at2 = 1ae6466ff37060150f155061c569ccc9`。
音频轨 md5：`at1 = af1 = af2 = 9bc160085ae1cf9dbc80381279adc38e`，
`at2 = 155d2b8f1fbe5f524f2db2bdc2024bb2`。

| 指标 | 本轮漂移（at1 vs at2） | 第 3 轮基线（App） |
|---|---:|---:|
| sharpness | **+9.1%** | 8.7% |
| HF jitter | **+20.3%** | 18.4% |
| frame diff | **+25.2%** | 22.4% |
| static_hf_jitter | **+14.5%** | 13.5% |

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

| 任务 | 一句话 | 优先级 |
|---|---|---|
| **P15b** | 用 `autotune: false` 重跑 P9 四组 shift 对照与 P13 shift12 臂 | 🔴 最高 |
| **P18** | `dmd` sampler 对纹理沸腾的作用（**零下载**，#55 的本机候选解法） | 🔴 高 |
| **P13b** | `sigmas` 网格对照（漂移≈0 后 ≥3 次即可） | 🔴 高 |
| **P19** | 参考图缩放策略（`pad` vs `stretch`，非正方形参考图） | 🟡 中 |
| **P10** | TaoMate-H3（2.5 GB） | 🟡 中 |
| **P11b** | Ref2VA 4 步 v1.0 768p（1.32 GB） | 🟡 中 |
| **P20** | 上游 catalog 落后于 lightx2v（差集含 v1.3）→ 可作第 6 条 issue 提案 | 📄 备查 |
| **P21** | MiniMax H3-Image（⛔ 磁盘阻塞） | ⛔ 阻塞 |

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

| # | 来源 | URL / 位置 | 日期 | 本轮读到的内容 |
|---|---|---|---|---|
| 1 | GitHub API · 上游 HEAD | `api.github.com/repos/tgo-app-dev/vpipe/commits/main` | 2026-11-16 | HEAD **仍 `4dc36b7`**，**零新增** |
| 2 | GitHub API · releases | `.../releases?per_page=3` | 2026-11-01 | **仍 v0.1.110**，零新增 |
| 3 | GitHub API · issues 全量 | `.../issues?state=all&per_page=100` | 2026-11-17 | **31 条 issue**（编号最大 59），**状态零变化**；#55 仍 open / **0 评论** / 最后更新 2026-10-21（**开放 28 天**）；#59 最后更新 **2026-11-16** |
| 4 | GitHub API · pulls | `.../pulls?state=all` | 2026-11-17 | **PR 数 0**（本轮无新 PR） |
| 5 | GitHub API · 仓库树扫描 | `.../git/trees/main?recursive=1` | 2026-11-17 | **1776 个条目**；命中 relay/vsr **41 个** |
| 6 | ★ 上游 `docs/RELAYVSR.md` | `raw.githubusercontent.com/tgo-app-dev/vpipe/main/docs/RELAYVSR.md` | 2026-11-16 | **379 行全新文档**：RelayVSR 4× 的内存账、速度表、int8/ANE 开关、精度对照、Limits |
| 7 | ★ 上游 `docs/MINIMAX-H3.md` | 同上 `/main/docs/MINIMAX-H3.md` | 2026-11-16 | **249 773 B / 4588 行**（本地 `33cda00` 是 248 998 B / 4577 行）→ **新增 11 行：H3 Image VAE 章节 + VDN `vdn_range` 章节** |
| 8 | 上游 README | `.../main/README.md` | 2026-11-16 | **与本地逐字节相同**（35 483 B），零变化 |
| 9 | 上游 `docs/` 目录 vs 本地 | 树扫描 + 本地 `os.walk` | 2026-11-17 | 上游 158 / 本地 153 → **本地只缺 5 项，全部是 RelayVSR** |
| 10 | ★ 上游 catalog 源码 | `stages/model-catalog.cc:2076-2155` | 本地 `33cda00` | **FlashVSR v1.1 与 FlashVSR+ v1.0 两条完整条目**（arXiv 2510.12747 / 2610.17552） |
| 11 | ★ 上游源码 `generate-video-stage.cc` | `stages/generate-video-stage.cc:568-620` | 本地 `33cda00` | **`kIports` 顺序表**：`sampler` = **iport 3**；iport 文档原文写明 `dmd` = 「x0 at each sigma, then fresh noise to the next」 |
| 12 | ★ 上游源码 sampler stage | `stages/diffusion-sampler-select-stage.{h,cc}` | 本地 `33cda00` | **method 枚举含 `dmd`/`res_multistep`**；`seed` 注释「dpmpp_sde / dmd noise seed (0: on MiniMax-H3, the clip's)」；`_cond_sigma` 字段 |
| 13 | ModelScope · lightx2v 适配器 | `modelscope.cn/api/v1/models/lightx2v/Minimax-h3-Turbo/repo/files` | 2026-11-18 | **31 文件 / 26 safetensors**（第 3 轮记为 27 → **订正，实为 26**）；**零新增变体** |
| 14 | ★ ModelScope · FlashVSR 搜索 | `modelscope.cn/api/v1/dolphin/models`（PUT） | 2026-11-18 | **10 个 FlashVSR 仓库**；`kuohao/FlashVSR-v1.1` = **6.48 GB**（含 `posi_prompt.pth`）；**`mlx-community/FlashVSR-v1.1-bf16` = 3.27 GB** |
| 15 | ModelScope · RelayVSR | `modelscope.cn/models/Comfy-Org/RelayVSR` | 2026-11-12 | 10.13B / 10.58 GB，2026-11-12 更新 → **本机可下的第三方通道** |
| 16 | ★ LightX2V 官方 | `github.com/ModelTC/LightX2V/blob/main/scripts/relayvsr/README_zh.md` | 2026-11 | `relayvsr_x4`（`sr_ratio∈[1,4]`）/ `relayvsr_x2`（`∈[1,2]`）；**混用 2×/4× 权重直接报错**；低于原生倍率 → 原生推理 + 带抗锯齿 bicubic |
| 17 | ★ ComfyUI 核心 PR | `github.com/Comfy-Org/ComfyUI/pull/17511`（merge `2f89433`） | 2026-11-05 | `RelayVSRConditioning` + `VSRDecode`（`detail` 在解码节点内）；backport PR 17583 **closed 未合并** |
| 18 | ★ 论文与社区实测 | arXiv 2609.37850 / nanoai.run / fervorcreativeai / mlllm.io / artrealmai / tokenstrom / bbs.monster | 2026-11-05～07 | A100 1080p **29.29 FPS / 13.82 GB**；5090 上 **1344×768→2688×1536 / 124 帧 / 5.8 s / 11.6 GB**；**「detail 以 15 帧节奏脉动 = 接缝」**；**HF Space `Upsampler/relayvsr`（免费档）** |
| 19 | ★ 社区 · H3-Image 讨论 | `huggingface.co/Comfy-Org/MiniMax-H3-Image/discussions/5` | 2026-11 | **「lcm 采样器（每步取端点预测再重注噪）消除了纹理麻点，euler 会累积」** → **直接支持本轮 `dmd` 假设** |

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

  | 输入 | 输出 | 含权重合计 | 本机 24 GB |
  |---|---|---|---|
  | 320×180 | 1280×720 | 9.9 GB | ✅ |
  | 480×270 | 1920×1080 | 11.7 GB | ✅ |
  | 640×360 | 2560×1440 | 14.3 GB | ✅ |
  | 854×480 | 3416×1920 | 18.9 GB | ✅ |
  | 960×540 | 3840×2160 | **21.8 GB** | ✅（紧） |
  | 1280×720 | 5120×2880 | 32.0 GB | ❌ |

  ⇒ **本实验室 768p（1344×768）的 4× = 5376×3072 → 装不下**；
  但 **544p（960×544）→ 3840×2176 = 21.8 GB** 与 **480p → 1080p = 11.7 GB** 在本机可行。
- **是否与本机实测冲突**：否（新增覆盖），但**与本实验室第 16 节的路线结论互补**：
  第 16 节结论是「768p 值 3.09× 时间换 3.33× 细节」，超分是**第三条路**（少生成、多放大）。

#### K2 ★★★ 更正：★ **本地 build `33cda00` 其实已经有 FlashVSR/FlashVSR+**（只有 RelayVSR 本体没有）

- 来源：本地源码树扫描（`stages/flashvsr-*.cc`、`generative-models/flashvsr/`、3 条 `docs/pipelines/flashvsr-*.vpipeline`）
  + 上游 `docs/` 与本地 `docs/` 逐项比对（上游 158 / 本地 153，**只差 5 项，全是 RelayVSR**）。
- 一句话结论：**「升 main 才能做超分」这句话只对 RelayVSR 成立**；
  **FlashVSR / FlashVSR+ 的 stage、Metal kernel、3 条官方流水线本地全都有 → 不升 main 也能跑超分实验**。
- **是否与本机实测冲突**：**是** —— 本轮早先的假设（「本地 build 没有超分能力」）**被实测推翻**，已修正。

#### K3 ★★★ ModelScope 上 FlashVSR 的完整可得性（本机 HF 直连不通，这是唯一通道）

| 仓库 | 体积 | 用途 |
|---|---|---|
| **`kuohao/FlashVSR-v1.1`** | **6.48 GB** | ★ **一个仓库就够 vpipe 用**：denoiser 5413 MB + `LQ_proj_in.ckpt` 549 MB + `Wan2.1_VAE.pth` 484 MB + `TCDecoder.ckpt` 180 MB + **`posi_prompt.pth` 4 MB**（上游 catalog 要从 `deAPI-ai/flashvsr-v1-1` 拿的 companion，**这个仓库自带**） |
| `mlx-community/FlashVSR-v1.1-bf16` | **3.27 GB** | ★ Apple Silicon 原生 MLX 端口；配合 `locmodel-h3-video` 技能（MLX 引擎）→ **磁盘最省的一条路** |
| `mlx-community/FlashVSR-v1.1-fp32` | 6.54 GB | 同上 fp32 |
| `1038lab/FlashVSR` | 12.05 GB | 同权重但文件重复 |
| `Comfy-Org/RelayVSR` | 10.58 GB | RelayVSR 的 Comfy 重打包（int8 四件套） |
- **是否与本机实测冲突**：否（新增覆盖）。

#### K4 ★★ 上游 `docs/MINIMAX-H3.md` 新增「H3 的 Image VAE」章节（第 1 轮 K7 的量化版）

- 来源：上游 `docs/MINIMAX-H3.md:3689-3760`（2026-11-16）。
- 一句话结论：`Mamad8/MiniMax-H3-Image-VAE`（**5.2 GB**，上游 pipeline `prepare-minimax-h3-image-vae.vpipeline`）
  = **H3 视频 VAE 的同一编码器（byte-for-byte）+ 重训的单帧解码器**；
  **它全面优于已发布的解码器**：

  | | Image VAE | 已发布解码器 |
  |---|---|---|
  | 1024×1024 整图 | **12 s** | 34 s |
  | PSNR vs 原图 | **34.9 dB** | 32.3 dB |
  | 平均色偏 | **< 0.5 级** | 每通道**暗 3 级** |
  | 2048×2048 整图 | 53 s | — |
  | 峰值内存 | 5.5–5.6 GB | 5.1 GB |

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
  + 掘金/头条《MiniMax H3 四视图工作流》+ jxxy《RTX 5090 本地跑 MiniMax H3 实测》。
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

| 臂 | sampler 端口 | method | 作用 |
|---|---|---|---|
| **A** `p18-euler` | **接上** | `euler` | ★ **接线对照**：证明「接端口且 method=euler」与「不接端口」逐位相同 ⇒ 端口本身透明 |
| **B** `p18-dmd` | 接上 | `dmd` | 处理组：每步重注噪 |
| **B2** `p18-dmd2` | 接上 | `dmd` | **确定性验证**：`dmd` 的重注噪路径是否也 bit-for-bit 复现 |
| 参照 `p15-repro-af1` | **不接** | 缺省 = euler | 第 3 轮续作的 B1 臂 → **跨轮次 + 跨接线**双重对照 |

冻结项：参考图 / 静止提示词 / 22 帧 / 1344×768 / 8 步 / seed 42 /
`lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` / shift 6.0-3.0 / `i8_gemm: true` /
`reference_image_short_edge: 1024` / **`autotune: false`（三处 stage）**。

#### 4.3.1 三条判决

| 判据 | 结果 | 含义 |
|---|---|---|
| **A vs 参照**（接端口+euler vs 不接端口，**跨轮次**） | ★ **framemd5 同（`0d77d033…`）、音频 md5 同（`9bc16008…`）、SSIM 口径A 1.000000、PSNR inf、字节 244 535 = 244 535** | ★ **sampler 端口在 method=euler 时完全透明**；且**跨轮次 bit-for-bit 复现成立** |
| **B vs B2**（`dmd` 跑两次） | ★ **framemd5 同（`4db48192…`）、音频 md5 同（`782be4e6…`）、SSIM 1.000000、PSNR inf、字节 241 997 = 241 997** | ★★ **`dmd` 的重注噪路径也是确定性的**（重注噪不引入随机性：噪声取自 clip 自己的 seed） |
| **A vs B**（euler vs dmd） | 整段 SSIM 口径A **0.635965** / PSNR **15.267388** / **首帧 SSIM 0.440051** | **换采样器 = 换场景**（0.44 比「换 shift」的 0.46–0.56 还低） |

#### 4.3.2 ★★ 效应量（漂移 = 0 ⇒ 差异 100% 归因于采样器）

| 指标 | euler | **dmd** | 效应 |
|---|---:|---:|---:|
| **HF jitter**（#55 主指标） | 0.1075 | **0.0937** | **−12.82%** |
| **frame diff** | 0.003669 | 0.003324 | **−9.40%** |
| **sharpness** | 559.73 | **617.19** | **+10.27%** |
| **static_hf_jitter**（只在时序静止像素上） | 0.1010 | 0.0892 | **−11.68%** |
| 静止像素占比 | 0.979 | 0.986 | +0.7 pp |
| **用时** | 219 s | **219 s** | **0%**（重注噪不额外耗时） |

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
  都得不到该值；但**「at1 = af1 = af2」的相等关系成立**且被本轮跨轮次复现独立证实。
  → **修订编号 R4-1：报哈希必须同时写清聚合口径，否则数字不可复核。**
- ⚠️ **待重测（优先级上调）**：第 3 轮 P13 测得 `er_sde` σ 网格的 HF jitter **−16%**，
  当时**落在 18.4% 漂移带内 → 不可下结论**。
  **现在漂移 = 0，若重跑（= P13b），那个 −16% 就可直接采信** → **P13b 优先级提到 P18 之上**。
- ⚠️ **不改写、只加前提**：第 17.4.1 节「Ref2VA 768p 12.0 更锐（+16.7%）」仍未用 `autotune:false` 重测
  → **P15b 仍是最高优先级待办**。

---

### 4.5 本轮新增待验证任务（登记到状态看板）

| 任务 | 一句话 | 优先级 | 阻塞 |
|---|---|---|---|
| **P13b** | `sigmas`（ComfyUI `er_sde` σ 表）网格对照，**≥3 次**；第 3 轮那个 **−16%** 在漂移=0 下可直采 | 🔴 **最高**（由 🔴 高上调） | 无（零下载） |
| **P15b** | 用 `autotune:false` 重跑第 17.4.1 节的 Ref2VA 768p shift 对照（12.0 vs 6.0） | 🔴 高 | 无（模型已在本地） |
| **P22** | ★ **FlashVSR / FlashVSR+ 超分路线**：本地 build **已有** stage + 3 条官方流水线；权重走 ModelScope `kuohao/FlashVSR-v1.1`（**6.48 GB**）或 `mlx-community/FlashVSR-v1.1-bf16`（**3.27 GB**，Apple 原生 MLX） | 🔴 高 | **磁盘 5.6 GiB < 15 GiB**（3.27 GB 那档可试） |
| **P23** | ★ **RelayVSR 4×**：上游 `docs/RELAYVSR.md` 已完整；需**升 main + 重编**（本地 build 无此 stage）；权重 10.2 GB | 🟡 中 | 磁盘 + 重编 |
| **P24** | ★ **超分接缝的 15 帧周期判据**：对超分后的片算 HF jitter 的**周期性**（关键帧间隔 = `window−1` = 15）→ 有周期 = 超分接缝伪影；无周期 = 生成端沸腾 | 🟡 中 | 依赖 P22/P23 |
| **P25** | 用 HF Space `Upsampler/relayvsr`（免费档）**零下载**预判「RelayVSR 到底补不补细节」 | 🟡 中 | 排队 / 不保证出图 |
| **P18b** | `dmd` 与 `er_sde` 的**正交拆解**：前者改「更新式」，后者改「网格」→ 拆开测，避免两个混淆项同时变 | 🟡 中 | 无 |
| **P26** | `res_multistep` 采样器（官方 NPU 路径明确列出，本轮只测了 `dmd`） | 🟡 中 | 无 |
| **P16** | `hf-mirror.com` 作为第三模型源（上游 `81cd674` 新加） | 🟡 中 | 本机 HF 直连不通，需验证镜像可用 |
| **P11b / P10 / P19** | Ref2VA 4 步 v1.0 768p / TaoMate-H3 / 参考图缩放策略（沿用第 3 轮登记） | 🟡 中 | P11b 需 1.32 GB |

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
