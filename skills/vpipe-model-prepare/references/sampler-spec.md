# H3 的 sampler spec：能接什么、接了会发生什么

> 最后更新：**2026-11-18 03:07**（第 3 轮续作 P15）
> 权威来源：上游 vpipe `docs/MINIMAX-H3.md` + 源码
> （`stages/generate-video-stage.cc` 的 `sampler` iport 文档、
> `stages/diffusion-sampler-select-stage.cc`）——**本地 build `33cda00` 已含全部实现**

---

## 1. 怎么接（端口号已确认）

```
diffusion-sampler-select  ──(oport 0)──▶  generate-video 的 iport 3（名为 sampler）
```

- `diffusion-sampler-select` 是 **0 入 / 1 出** 的 stage（发一次 spec）；
- `generate-video` 的 iport 顺序（**从 0 数**）：
  `0 conditioning` / `1 neg_conditioning` / `2 model` / **`3 sampler`** / `4 scheduler` /
  `5 ref_latent0` / `6 ref_latent1` / `7 ref_latent2` / `8 ref_audio` / `9 model_config`。
- 选器支持的 `method`：`euler` / `heun` / `dpmpp_2m` / `dpmpp_sde` / `dmd` / `res_multistep`
  （别名 `dpm++_2m` / `dpmppsde` / `dmd_student` / `turbo` 会被规范化）。

---

## 2. ★ H3 只认三个 method，其余只会 warn 并回落默认

上游文档原文：

> `heun`, `dpmpp_2m` and `dpmpp_sde` are **not offered for H3**. `heun` and
> `dpmpp_sde` take **two** forwards a step, which on a 33B model is twice
> the cost of a step. A spec naming one is warned about and the default
> runs. `eta` and `s_noise` are `dpmpp_sde`'s and are not read.

| method | H3 上会发生什么 | 每步前向数 |
|---|---|---|
| `euler` | ✅ **默认**：`x += (σ' − σ) · v`，确定性 | 1 |
| `dmd` | ✅ **重注噪**：先算干净估计 `x0 = x + σ · v`，再 `(1 − σ') · x0 + σ' · n`（**fresh noise**） | 1 |
| `res_multistep` | ✅ ComfyUI 的方法：log-sigma 上的二阶，用上一步的 `x0` | 1 |
| `heun` / `dpmpp_2m` / `dpmpp_sde` | ⚠️ **warn 后回落 euler**（在 33B 上每步要两次前向，代价翻倍） | — |

**所以**：上游 issue #55 提出的「让 H3 读 sampler spec iport」这条请求，
**上游已经做了；但 #55 想要的 `dpmpp_sde` 仍然不被支持**（被明确排除）。

---

## 3. ★ `dmd` 就是 issue #55 讨论的「每步受控重注噪」

`dmd` 的更新式（上游原文）：

```
x0        = x + σ · v
x_next    = (1 − σ') · x0 + σ' · n        n 为 fresh noise
```

- 这正是 diffusers 的 `stochastic_sampling`，也是 DMD 类少步学生的采样方式；
- **噪声来源**：默认取 **clip 自己的 seed**；选器上另设了 `seed` 时用选器的 seed
  （`seed: 0` = 用 clip 自己的 seed）；
- **因此 `dmd` 是确定性的**（同 seed 同配置 → 同噪声），
  这与「重注噪会引入随机性」的直觉相反，务必分清。

**与 #55 的关系**：
issue #55 指出 `FlowMatchEuler` 是确定性的 → 误差单调累积 → 纹理沸腾；
ComfyUI 的 `er_sde` 每步受控重注噪 → 误差重新随机化 → 沸腾被压制。
**H3 内置的 `dmd` 正是这个机制**，而且**不需要下载任何模型**（本地 build 已支持）。

> ⚠️ 但 `dmd` 文档另有一句限定（针对图像模型）：
> 「`dmd` … only meaningful on a DMD-distilled checkpoint」
> —— 把非 DMD 蒸馏的 checkpoint 配 `dmd` 是否合适，**尚无量化证据**，需实测。

---

## 4. 优先级：`sigmas` 与 sampler spec 各自管什么

| 设置 | 管什么 | 优先级 |
|---|---|---|
| `sigmas`（`minimax-h3-model-config`） | **网格**（哪些 σ、几步） | 覆盖 flow map / adapter sampling contract 的网格 |
| `diffusion-sampler-select` → iport 3 | **更新式**（每一步怎么走） | 与网格独立 |

上游规则（逐条）：

- HyperFlow 的 flow map 网格、Pika H3 Flex 的 sampling contract 网格 → **被 `sigmas` 替换**（会 warn）。
- **Pika contract 自带的 re-noising 随它走，除非 sampler port 指定 `dmd`。**
- sampler port 指定 `euler` + Pika contract → 保留 contract 的网格，用 Euler 走它。
- **flow map 之下只跑 `euler`**，其它 method 被 warn 并丢弃
  （flow map 的「一步」就是它跳到下一个 σ）。
- refine（Open-H3-Regenerate-2K）上，`sigmas` **就是**它的 σ 串，第一个 σ 是重注噪到的 level。
- **TaoMate-H3 的流式方法两者都不取** —— 它跑自己的网格和自己的步进。

---

## 5. `dmd` 与 Pika H3 Flex 的关系（易混）

- Pika H3 Flex 的 sampling contract **自带 re-noising**（本机第 2 轮日志：
  `6 steps RE-NOISED on the sampling contract's grid (pika-flex-ref2va-v1)`）；
- 因此**默认情况下 Pika 已经在重注噪**；
- 若再接一个 `dmd` 的 sampler spec，则 contract 的 re-noising 被 `dmd` 接管
  （两处都是「重注噪」，不要叠加理解为两次重注噪 —— 是**换实现**，不是叠加）。

---

## 6. 实测建议（写于 P18 之前，**已被第 7 节的 P18 实测取代**；第 3–5 步仍有效）

1. **基线**：静态夹具（22 帧）+ `euler`（默认）。
2. **对照 A**：同一夹具 + sampler spec `dmd`（`seed` 不设 → 用 clip 自己的 seed）。
3. **对照 B**：同一夹具 + `sigmas` = ComfyUI `er_sde` 表（已在 P13 做过一版，需 ≥3 次取方差）。
4. 指标：P13 的 `hf_jitter` / `static_hf_jitter` / `sharpness` / `frame_diff`，
   并按 **P15 测出的漂移基线**判定效应是否超过噪声。
5. **注意**：`dmd` 与 `er_sde` 是**两条不同的 σ 网格 + 不同的更新式**，
   混着比较会同时引入两个混淆项（网格 + 更新式）→ 要拆开测。

---

## 7. ★★ P18 实测判决（2026-11-18 04:30 · 第 4 轮，本机首次跑通 `dmd`）

**实验**：`vpipe-lab/scripts/{make_p18_pipelines.py,p18_runner.sh,p18_analysis.py}`，3 臂串行。
静态夹具（22 帧 / 1344×768 / 8 步 / seed 42 / Ref2VA 8-step 768p 适配器 / shift 6.0-3.0），
**三处 `autotune: false`** → 漂移 = 0（逐位验证见下）。

| 臂 | sampler 端口 | method | 产物字节 | 用时 |
|---|---|---|---|---|
| A `p18-euler` | **接上** | `euler` | 244 535 | 219 s |
| B `p18-dmd` | 接上 | `dmd` | 241 997 | 219 s |
| B2 `p18-dmd2` | 接上 | `dmd` | 241 997 | 220 s |
| 参照 `p15-repro-af1` | **不接** | 缺省 = euler | 244 535 | （第 3 轮续作） |

### 7.1 三条判决

| 判据 | 结果 | 含义 |
|---|---|---|
| **A vs 参照**（接端口+euler vs 不接端口，**跨轮次**） | ★ **framemd5 同、音频 md5 同、SSIM 1.000000、PSNR inf、字节 244 535 = 244 535** | ★ **sampler 端口在 method=euler 时完全透明**；且**跨轮次 bit-for-bit 复现成立**（本轮 vs 第 3 轮续作） |
| **B vs B2**（`dmd` 跑两次） | ★ **framemd5 同、音频 md5 同、SSIM 1.000000、PSNR inf、字节 241 997 = 241 997** | ★ **★ `dmd` 的重注噪路径也是确定性的** —— 重注噪并不引入随机性（噪声取自 clip 自己的 seed，`generate-video-stage.cc:5279-5281`） |
| **A vs B**（euler vs dmd） | 整段 SSIM 口径A **0.635965** / PSNR **15.267388** / **首帧 SSIM 0.440051** | **换采样器 = 换场景**（首帧 SSIM 0.44，比「换 shift」的 0.46–0.56 还低）→ 与「换 shift = 换场景」同族 |

### 7.2 ★★ 效应量（漂移 = 0 ⇒ 差异 100% 归因于采样器）

| 指标 | euler | dmd | 效应 |
|---|---:|---:|---:|
| **HF jitter**（#55 主指标） | 0.1075 | **0.0937** | **−12.82%** |
| **frame diff** | 0.003669 | 0.003324 | **−9.40%** |
| **sharpness** | 559.73 | **617.19** | **+10.27%** |
| **static_hf_jitter**（只在静止像素上） | 0.1010 | 0.0892 | **−11.68%** |
| 静止像素占比 | 0.979 | 0.986 | +0.7 pp |
| **用时** | 219 s | **219 s** | **0%（重注噪不额外耗时）** |

⇒ **`dmd` 既降低纹理沸腾（−12.8%），又更锐（+10.3%），且不花额外时间。**
⇒ **但没有根治**：第 3 轮的静态夹具地板是 **0.0010**，本轮 `dmd` 是 0.0937 → **仍是地板的 94×**。
**正确表述：`dmd` 把沸腾压低约 13%，不是消除。**

### 7.3 ★ 与社区结论的互证（本轮最有价值的一条）

HF `Comfy-Org/MiniMax-H3-Image` 讨论区（社区）断言：
> 「ComfyUI 的 **lcm** 采样器每步取模型的端点预测**再重注噪到下一个 σ**，这正是蒸馏头期望的；
> **euler** 则把当前残差沿速度方向带着走，**陈旧的高频噪声每步都活下来**，读起来就是麻点与颗粒感，
> 而且 **euler 步数越多越累积**。……**病理在采样器侧，不在权重侧。**」

**ComfyUI 的 `lcm` 与 vpipe 的 `dmd` 是同一个机制**（每步取 x0 再重注噪到下一个 σ）。
⇒ **本轮首次在 vpipe/H3 上独立验证了这条社区结论：成立**（HF jitter −12.82%、sharpness +10.27%）。

### 7.4 日志里的显式回显（机制不是推断，是打印出来的）

```
[INFO] DiffusionSamplerSelectStage('sampler-select'): sampler = dmd (eta 1, s_noise 1, seed 0)
[INFO] GenerateVideoStage('generate-video'): sampler 'dmd' from the sampler port -- minimax-h3 steps by renoise
[INFO] h3-denoise: 8 steps RE-NOISED (x0 at each sigma, then fresh noise to the next), as the sampler asks
```

⇒ **`dmd` 在 H3 上确实被实现了**，**不是「被排除后回落默认」**（第 3 轮的担心没有发生）。
⇒ `autotune: false` 生效的旁证：`[h3-dit] first forward at 9294 rows: 68 ms before block 0 (… **gemm autotune 0** …)`
（竞速开时这一项是 **4635 ms**）。

### 7.5 ★ 纪律补两条

1. **「接上 sampler 端口」本身不改变输出**（method=euler 时逐位相同）→
   ⇒ 以后做采样器对照，**「端口是否接线」不再是混淆项**，可以放心把它当常开项。
2. **跨采样器的对照不能表述为「同一场景的画质对比」**：
   首帧 SSIM 0.44 ⇒ 那是**两条不同轨迹**。表述方式与「换 shift = 换场景」完全一致
   （第 3 轮 §3.6 已立此纪律，本轮把它扩展到「换采样器」）。

### 7.6 口径与工具

- 逐帧判据用 `framemd5` **必须 `-map 0:v`**（本轮实测：22 帧片的**全流清单是 51 行** = 22 视频帧 + 29 音频包）。
- ⚠️ **第 3 轮报告里的哈希值 `46bcb264…` 无法复现**：本轮试了四种聚合
  （`-map 0:v` 去注释 / 全流去注释 / 含注释 / 逐帧行拼接）都得不到该值；
  但**「at1 = af1 = af2」这个相等关系成立**，且本轮用**跨轮次**的方式再次独立证实
  （本轮 p18-euler 与第 3 轮 p15-repro-af1 逐位相同）。
  ⇒ **纪律：报哈希时必须同时写清聚合口径，否则数字不可复核。**

---

## 8. ★★★ 2026-11-18 第 5 轮：必须区分「`dmd` 采样器」与「DMD2 蒸馏」

社区里 **`dmd` / `DMD` / `DMD2` / `turbo` / `turbo_student` / `LCM`** 这几个词经常混着写，
读帖时极易把「蒸馏模型」当成「采样器」。对照表：

| 名称 | 是什么 | 作用层次 | 产物 | 本实验室状态 |
|---|---|---|---|---|
| **`dmd`（vpipe 采样器）** | **采样器**：每步重注噪<br>`x0 = x + σ·v` → `(1−σ')·x0 + σ'·n`（**fresh noise**） | **推理期**，不改任何权重 | 同权重换一条 σ 轨迹 | **第 4 轮 P18 已实测**：HF jitter **−12.82%**、sharpness **+10.27%**、用时 **0%** |
| **DMD2（FastH3 蒸馏）** | **蒸馏出的学生模型**：用 DMD2 loss 从冻结 teacher 学出 4/8 步 | **训练期**，改权重 | 新的 DiT 权重（22.90 GB INT8） | 未测（磁盘阻塞） |
| `turbo` / `turbo_student` | 上游**别名**，规范化后落到 `dmd` | 同 `dmd` | — | 同 `dmd` |
| `lcm` | ComfyUI 侧的 LCM 采样器 | 推理期 | — | **社区断言 ≡ `dmd`**（HF `Comfy-Org/MiniMax-H3-Image` #5）；第 5 轮获得跨家族印证 |

**★ 两条易错推论**：

1. **不要把「FastH3 只有 4 步」归因到 `dmd` 采样器。**
   FastH3 的少步能力来自**模型被 DMD2 蒸馏过**；
   本实验室测的是**同权重换采样器**。两者是**不同层次的变量**。
2. **不要把社区的「DMD2 消除了纹理麻点」直接读成本实验室的 `dmd` 结论。**
   但第 5 轮出现了一个**真正的跨家族印证**（见 §9）。

### 8.1 ★ 第 5 轮：H3-Image 上的独立复现（跨家族印证 P18）

社区在 **MiniMax H3-Image**（图像模型，非视频）上独立发现：

> ComfyUI 官方模板默认 `euler` → 皮肤/细节出现「crunchy grid」（过锐块状纹理）；
> 换成 **`SamplerLCM` 节点 + `simple` scheduler + 6 步 + `s_noise` 1.10 → 0.90**
> → 皮肤出现真实毛孔、眼睛干净、牙齿自然。

来源：<https://pixelailabs.com/blog/minimax-h3-image-comfyui-realistic-photos>（2026-11）、
<https://webhill.net/en/telegram/post/three-comfyui-settings-to-eliminate-artifacts-in-minimax-h3-image>

**★ 交叉结论**：

| | vpipe `dmd`（第 4 轮 P18，本实验室实测） | ComfyUI `SamplerLCM`（H3-Image，社区实测） |
|---|---|---|
| 相对 euler | HF jitter **−12.82%**、sharpness **+10.27%** | 「crunchy grid」消失、皮肤变真实 |
| 机制 | 每步重注噪（fresh noise） | LCM 更新式（社区断言 ≡ `dmd`） |
| 家族 | H3 **视频** | H3 **图像** |

⇒ **同一条机理（LCM/DMD 更新式 vs euler）在 H3 视频与 H3 图像两个家族上独立出现。**
P18 的判决从「本机单点观察」升级为「**家族级共识**」。

⚠️ **但都不是根治**：
- 本实验室：`dmd` 的 HF jitter 仍是静态地板（0.0010）的 **94×**；
- 社区那条也没说「完全消除」，只说「明显改善」。
→ **纪律不变（第 4 轮坑 12.4）：任何「效应量」都要同时给出地板值与倍数。**

## 8. PDD (Alibaba PAI) 采样规约 (2026-11-18 23:50 增量)
来源: SDNext / GitCode

- **采样器必须固定为 `euler`**。
- **CFG (Guidance Scale) 必须固定为 `1.0`** (Guidance Distilled)。
- **Shift 锁定**: 8步 PDD LoRA 必须锁定在训练值 (12.0 / 3.0)。
- **注意**: 任何偏离上述参数的尝试都会导致严重的画质劣化或静默失效。

---

## 8. scheduler 端口与 `lcm`（2026-11-21 第 20 轮追加，来源：上游 commit `d72c22f` + P28 实验）

- **`lcm` 加入 H3 采样器映射**：`lcm` ≡ `dmd` ≡ `dmd_student` ≡ `turbo`（都走重注噪步 kRenoise）。上游文档原话确认与 ComfyUI 的 `lcm` 采样器同款 → **P18 的 `dmd` 判决（HF jitter −12.8%）可直接翻译 ComfyUI 社区配方的 `lcm`**。
- **scheduler-select 新增四类型**：`normal` / `sgm_uniform` / `beta`（`beta_alpha`/`beta_beta` 默认 0.6/0.6；RES4LYF beta57 = 0.5/0.7）/ `linear_quadratic`。对 H3：`type=simple` 即模型默认网格；其余按 model config 的 **`schedule_shift`**（新键，未设则 `video_shift`）算，**scheduler stage 自己的 shift 不被读**。
- **`generate-video` iport 4（scheduler）对 H3 从惰性变真读**。优先级：HyperFlow/Pika contract < `sigmas`/scheduler 网格。
- **P28 判决（22 帧静态夹具 / autotune:false / seed 42 / d72c22f）**：
  - sgm_uniform（shift 6, 8 步）σ 回显 `[1, 0.9769, 0.9478, 0.9099, 0.8586, 0.7853, 0.6719, 0.4732, 0]`；音频 `[1, 0.9548, 0.9007, 0.8347, 0.7522, 0.6465, 0.5059, 0.3099, 0]`。
  - vs 默认网格：HF jitter **−3.77%** / sharpness +1.33% → 不作为纹理沸腾解法（`dmd` 仍是唯一超漂移带解）。
  - **首帧 SSIM 0.952 = 同场景** → **修订「换 σ 网格 = 换轨迹」的强度**：粗换（er_sde 表，0.604）换场景；细换（8 点同族网格）同场景微扰。σ 轨迹差是连续谱。
  - **跨 build 陷阱**：33cda00 配方跑在 d72c22f 上与历史锚点**逐位不同**（首帧 SSIM 0.344）→ 锚点臂只在同 build 内有效；跨 build 逐位比较全部作废、漂移基线需重测。d72c22f 自身 `autotune:false` 下 bit-for-bit 成立（复跑逐位相同）。
  - **echo 行为变化**：d72c22f 默认 denoise 不打印 `h3-denoise:` 行（接 scheduler/sampler 端口才打）。

---

## 9. README 采样契约口径确认（2026-11-22 第 21 轮追加，来源：上游 README @ d347808 + commit 7703614 考古）

- **h3.c 对比的采样口径**：6 DiT 步、bf16 无量化、同 prompt 同 seed、h3.c 全 50 块无步复用。VPIPE 在 M5 上开 `i8_gemm`、M4 Pro 上开 `ane_ffn+ane_qkv`。**这对本实验室的意义**：官方性能口径用的是 6 步（Turbo LoRA 档），本机 P13b/P28 的 8 步 Ref2VA 静态夹具口径与其不同族，不可直接互比。
- **7703614（2026-08-19）考古**：README 上最初一版 h3.c 对比表（M4 Pro 21m50s / Air 12m15s）为**旧口径**；当前 d347808 的表（17m43s / 13m7s / **新增 M5 Pro 24GB 行 5m29s vs 7m11s**）是最新实测。**引用 h3.c 数字必须写 commit/日期**——该表历史上至少刷新过一次。
- 采样器/调度器机制本身无新增变化（第 20 轮第 8 节仍为最新判决）。
