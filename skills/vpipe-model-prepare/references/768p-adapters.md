# 768p / 长规格：lightx2v 适配器家族与 24 GB 实测

> 适用：MiniMax-H3 FL2VA / Ref2VA 想跑 **1344×768**、**10 秒以上**、**四段式续接** 时。
> 结论先行：**768p 不是一个参数，而是「换适配器 + 换 shift 网格」**；
> 在 Mac mini M5 Pro / 24 GB 上，**1344×768 × 124 帧可行**（约 30 分钟），
> **241 帧（10 秒）单段也可行**（约 55 分钟），但权重会被完全换出到磁盘。

---

## 1. 关键认知：适配器家族只有「一个仓库」

官方文档把 768p 适配器列成 5 个「仓库」，**实际上它们全在同一个 ModelScope 仓库里**：

```
hf_path: lightx2v/Minimax-h3-Turbo      ← 全部 768p / 544p 适配器都在这
```

区分靠 **注册名（name）** + **变体（variant）**：

| 注册名（写进 `lora`） | variant | 落到哪个文件 |
|---|---|---|
| `lightx2v/Minimax-h3-Turbo-8step-768p` | 8-step v1.0 768p, shift 6 | `minimax_h3_fl2v_turbo_8step_v1.0_768p_bf16.safetensors` |
| `lightx2v/Minimax-h3-Turbo-8step-768p-split` | 8-step v1.0 768p, shift 6, **split qkv** | 同上（split 优先） |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2` | 4-step v1.2 768p, shift 6, split qkv | `minimax_h3_fl2v_turbo_4step_v1.2_768p_bf16.safetensors` |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2-comfyui` | 4-step v1.2 768p, shift 6, **fused qkv** | `minimax_h3_fl2v_turbo_4step_v1.2_comfyui_bf16.safetensors` |
| `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` | Ref2VA 8-step 768p, shift 6, split qkv | `minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16.safetensors` |
| `lightx2v/Minimax-h3-Turbo-8step` | **8-step v1.0 544p**（无 768p） | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` |

> **split vs fused qkv**：官方建议优先取 **split**（`-split` 后缀）。
> 两者文件大小差很多（split 1.29 GiB / fused 1.82 GiB），因为 fused 把 qkv 合并成一个矩阵。

**HuggingFace 直连在本机不通，ModelScope 完整可用**（31 个文件全在）。
`VPIPE_MODEL_SOURCE=modelscope` 必须设。

---

## 2. shift 是适配器的一部分，不是个人偏好

| 适配器 | `video_shift` | `audio_shift` |
|---|---|---|
| 768p 系列（全部） | **6.0** | 3.0 |
| 544p / 基础 Pika / HyperFlow | 12.0 | 3.0 |

**768p 适配器是在 768p 上蒸馏出来的，蒸馏拟合的是它训练时的 sigma 网格。**
把它接到 shift 12 的图上 = 用错误的网格去走一个为另一个网格蒸馏出来的模型。

shift 写错时 vpipe **不一定报错**，会照跑并给出看起来正常但对不上的画面 ——
所以必须用「shift 6 vs shift 12 的成对实验」去验证，而不是看日志有没有 ERROR。

---

## 3. 24 GB 实测资源画像（1344×768 / 124 帧 / 8 步 / seed 42）

| 项 | 实测值 |
|---|---|
| 前向行数 | **37 804**（`first forward at 37804 rows`） |
| 总耗时 | **29 分 34 秒** |
| denoise 节奏 | 每 10 % ≈ **2 分 45 秒**（8 步共 400 个进度单位） |
| DiT 常驻块 | 结束时只剩 **25 / 50 块** |
| 权重常驻率 | **0 %**（221 / 221 页被换出，wired **10 396 MB**） |
| 系统可用内存最低点 | **8 %** |
| 显存门槛 | wire budget 18 186 MB，是真正的闸门 |

日志里这三行是判断「这台机器扛不扛得住」的关键：

```
MetalMiniMaxH3Transformer: residency probe 50 blocks of 50 (390 MB each, 12607 MB reclaimable, wire budget 18186 MB) -- uncapped, the wire budget is the gate
MetalMiniMaxH3Transformer: resident weights are only 0% in RAM (221 of 221 sampled pages paged out, 10396 MB wired) -- released 415 MB, now 25 blocks resident
GenerateVideoStage('generate-video'): DiT residency ended at 25 of 50 blocks (10396 MB), 0 pinned at load
```

**`sage_attn` 会因为序列长度限制自动关闭** —— 这不是故障，是 768p 在 24 GB 上的必然结果。

---

## 4. 帧数 ↔ 时长 ↔ 成本

24 fps 下：

| 帧数 | 时长 | 本机实测耗时（768p / 8 步） |
|---|---|---|
| 39 | 1.63 s | 5 分 11 秒 |
| 124 | 5.17 s | **29 分 34 秒** |
| 241 | **10.04 s** | ≈ 57 分钟（行数 ≈ 73 500） |
| 362 | 15.08 s | ≈ 86 分钟（行数 ≈ 110 000，**24 GB 上不推荐**） |

> **行数 ≈ 305 × 帧数**（124 帧 → 37 804）。耗时近似线性，**不是平方**。
> 官方「按行数平方计算」那句说的是单段长片的注意力代价，
> 所以官方自己推荐 **四段式续接**（见第 6 节）而不是硬拉一段 40 秒。

---

## 5. 可直接跑的 768p 流水线

关键配置就四处（其余照抄普通 FL2VA 流水线）：

```json
{
  "id": "minimax-h3-model-config",
  "type": "minimax-h3-model-config",
  "config": {
    "video_shift": 6.0,
    "audio_shift": 3.0,
    "condition_timestep": 1.0,
    "lora": "lightx2v/Minimax-h3-Turbo-8step-768p-split",
    "lora_scale": 1.0
  }
},
{
  "id": "generate-video",
  "type": "generate-video",
  "config": {
    "height": 768, "width": 1344,
    "frames": 124, "fps": 24, "steps": 8, "seed": 42,
    "i8_gemm": true, "unload_when_idle": "always"
  }
}
```

`model-select` 仍指向本地 8-bit 主模型：`local/MiniMax-H3-FL2VA-8bit`
（Ref2VA 则是 `local/MiniMax-H3-Ref2VA-8bit`）。

**改帧数不用改流水线**，用 stage 级覆盖：

```bash
vpipe --launch ./pipelines/p3-768p-shift6.vpipeline \
      --stage-cfg generate-video::frames=241 \
      --stage-cfg 'save-video::output_url="out/p3-768p-shift6-241f.mp4"'
```

---

## 6. 四段式续接（官方长视频正路）

官方示例：`minimax-h3-extend-part1..4.vpipeline` + `minimax-h3-extend-concat.vpipeline`
（在本机 vpipe 源码树 `docs/pipelines/` 下）。

**机制（官方原样）：**

```
load-video(上一段)  → video-to-rgb → temporal-slice(start=-90) → temporal-stack → 参考1(视频)
load-audio(上一段, start_s=段长-3.75, duration_s=3.75) → audio-to-pcm → temporal-stack → 参考2(音频)
video-ref-encoder(attach_audio=[2])     ← 音频参考是**第 2 条参考**，槽位 1 起算
```

- **末 90 帧 = 3.75 秒**，和音频引导的 3.75 秒**刻意对齐**
- `attach_audio` 里的数字是**音频那条参考自己的槽位号**（1 起算），不是端口号
- `temporal-stack` 必须带 `max_mb: 384`，否则引导视频会被截帧
- `reference_video_short_edge: 0`，避免行数翻倍
- `save-video` 用 `video_codec: ffv1` + `audio_codec: alac` **无损**写出，色度不折半
  （实测 ffv1 装进 .mp4 可正常读回，`yuv444p` 保留）
- 续接提示词必须以 `[video continuation + audio reference]` 开头，
  并保留 `subject_definitions` / `retention_analysis` / `detailed_description` /
  `overall_soundscape` / `non_diegetic_music` 五个段落

**续接质量的判据**（不是「看着还行」）：

> **接缝处相邻帧的 SSIM，是否落在段内相邻帧 SSIM 分布的正常区间内。**
> 接缝 SSIM < 段内 p5 → 可见跳变。

官方是 960×576 / 243 帧 / 20 步；24 GB 机器上要缩到 **832×480 / 124 帧 / 6 步 / Pika 适配器**。

---

## 7. 坑

1. **shift 错了不报错**。768p 适配器 + shift 12 会照跑，必须成对实验验证。
2. **「一个仓库五个模型」是错觉**。全在 `lightx2v/Minimax-h3-Turbo`，
   靠注册名 + variant 区分；`-split` 后缀不是仓库名。
3. **24 GB 上权重 0 % 常驻是正常态**，不是故障；日志里 `resident weights are only 0% in RAM`
   看着吓人，但那正是设计意图（用 wire budget 换速度）。
4. **`sage_attn` 自动关闭**属于预期，不是 OOM。
5. **别在 24 GB 上硬拉 362 帧**（15 秒单段）。行数涨到 11 万左右时，
   系统可用内存会逼近 0，风险远高于收益；用四段式。
6. **ffv1 装 .mp4 没问题**（实测可读回、保留 yuv444p），不必改成 mkv。
7. **`attach_audio` 的槽位号**：≥2 条参考时，官方示例 `attach_audio: [2]`
   指的是**第 2 条参考（音频那条）**自己，不是「第 2 个端口」。

---

## 8. 相关

- `references/model-registry.md` —— 注册表与 `model_variant` 匹配规则
- `references/disk-management.md` —— 磁盘回收手册
- `references/quantization.md` —— 量化机制与已知缺陷

---

## 9. Ref2VA 的 768p 适配器（2026-11-16 实测补完）

> 第 8 轮只跑了 FL2VA 的 768p 适配器。适配器家族里**唯一一个下载了却从没被跑过**的
> 是 Ref2VA 专用那个：`lightx2v/Minimax-h3-Turbo-ref2va-8step-768p`
> （`minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16.safetensors`，1.38 GB）。
> 第 9 轮把它跑通，并发现**它的 shift 偏好和 FL2VA 相反**。

### 9.1 怎么开

```json
{
  "id": "model-select",
  "type": "model-select",
  "config": { "hf_dir": "local/MiniMax-H3-Ref2VA-8bit" }
},
{
  "id": "minimax-h3-model-config",
  "type": "minimax-h3-model-config",
  "config": {
    "video_shift": 12.0,
    "audio_shift": 3.0,
    "condition_timestep": 1.0,
    "lora": "lightx2v/Minimax-h3-Turbo-ref2va-8step-768p",
    "lora_scale": 1.0
  }
},
{
  "id": "generate-video",
  "type": "generate-video",
  "config": {
    "height": 768, "width": 1344,
    "frames": 124, "fps": 24, "steps": 8, "seed": 42,
    "i8_gemm": true, "unload_when_idle": "always"
  }
}
```

- **基础模型必须用 Ref2VA 那套**：`local/MiniMax-H3-Ref2VA-8bit`
  （官方明写：适配器是针对单一任务蒸馏出来的，parent 链接会拒绝另一个模式的适配器）。
- **参考图照样走端口路线**：`load-image → image-resample(1024×1024) → video-ref-encoder.iport2`。
- **参考视频要 resample 到 1344×768**（输出画布），并把 `temporal-stack` 的 `max_mb` 提到 **384**
  （124 帧 @ 1344×768 = 366 MiB，默认 256 会把参考截到 86 帧）。
- `attach_audio` 填**音频那条参考自己的槽位号**（1 起算）：喂 1 图 + 1 视频 + 1 音轨 → `[3]`。
  日志会打 `2 reference(s)`（视频与音轨折叠成一条）。

### 9.2 ★ shift 不是按分辨率一刀切，而是按适配器

| 适配器 | 官方文档写的 shift | 本机实测（1344×768 / 124 帧 / 8 步 / 单图参考 / seed 42）|
|---|---|---|
| FL2VA `8step-768p-split` | **6.0** | **6.0 更好**：主体纹理 319.1 vs 300.3（+6.3%），纹理/噪点 162.8 vs 154.9 |
| Ref2VA `ref2va-8step-768p` | **6.0** | **12.0 更好**：主体纹理 178.7 vs 153.1（**+16.7%**），纹理/噪点 162.1 vs 139.5 |

**细节口径**（两个指标方向一致，不是噪声假象）：

| 口径 | 含义 | Ref2VA shift 6 | Ref2VA shift 8 | Ref2VA shift 12 |
|---|---|---:|---:|---:|
| 拉普拉斯方差（原始帧） | 第 8 轮口径：细节 **+ 噪点** | 306.2 | 280.7 | 413.2 |
| 拉普拉斯方差（3×3 中值滤波后） | 压掉孤立噪点后的**真实纹理** | 153.1 | 138.1 | **178.7** |
| 颗粒噪点 | \|帧 − 中值(帧)\| 的均值 | 1.097 | 0.967 | 1.102（几乎不变）|
| 纹理 / 噪点 | 越大越干净 | 139.5 | 142.8 | **162.1** |
| 全片细节能量 | 第 8 轮口径 | 102.5 | 103.0 | **137.5** |

> **「颗粒几乎不变、纹理多 16.7%」= shift 12 真的画得更细，不是把噪点当细节。**
> 第 8 轮 FL2VA 的结论在同一套双指标下**仍然成立**（shift 6 更好），所以那条结论没被推翻，
> 被推翻的是「768p 一律用 6.0」这条**推广**。

**★ shift 的响应是「台阶」不是「斜坡」**（第 9 轮加的 shift 8.0 中间档带来的新信息）：

| 证据 | 6.0 → 8.0 | 8.0 → 12.0 |
|---|---|---|
| 全片细节能量 | 102.5 → 103.0（**+0.5%**）| 103.0 → 137.5（**+33.5%**）|
| 裁切区纹理 | 153.1 → 138.1（−9.8%）| 138.1 → 178.7（**+29.4%**）|
| 运动能量曲线相关 r | **0.9817**（几乎是同一条曲线）| A–B 0.7486 / D–B 0.8174 |

> **6.0 与 8.0 的产出几乎是同一条曲线**（运动 r = 0.98、细节 +0.5%），
> **12.0 才换了一套采样网格**。
> 落到操作上：**Ref2VA 768p 只需试 6.0 与 12.0 两档，中间值可以省掉**。

**适用边界（别过度推广）**：

- 本轮只测了 **1344×768 + 单图参考 + 新生成 + seed 42** 这一种场景。
- 官方把 `ref2va-8step-768p` 用在**四段式续接链**里（960×576、**视频参考**），
  那里仍应按官方文档写 **6.0** —— 那个场景本轮没复验。
- **单种子**，更稳的结论需要换 seed 复验（第 9 轮计划里的 P9.2）。
- 768p **多参考**（图 + 动作视频 + 音轨）下画质要掉 17%，见第 10 节。

### 9.3 成本

| 组合 | 前向行数 | 耗时 |
|---|---:|---:|
| Ref2VA 768p + 1 图参考（shift 6.0 / 8.0 / 12.0）| 39 865 | **27 分 32 秒 / 27 分 19 秒 / 27 分 47 秒** |
| Ref2VA 768p + 1 图 + 动作视频 + 音轨 | **83 695**（2.10×）| **1 小时 40 分 36 秒**（3.64×）|

参考视频在 1344×768 下要编 37 个 latent，**光这一步就 88.5 秒**（480p 下是 40 秒），
并带来 **38 320 reference video rows**（480p 的 P1 是 16 478，2.33×）。

**每行成本随行数上升**这条规律本轮再次成立：83 695 行时约 0.0695 s/行
（第 8 轮 37 804 行时 0.0469、73 480 行时 0.0669）。

### 9.4 坑（补充第 7 节）

8. **「768p = shift 6.0」不是铁律**。至少 Ref2VA 的 768p 适配器在本机实测里相反，
   而且**依然零告警**（lightx2v 是普通 LoRA，没有 sampling contract）。
9. **参考视频上采样到 1344×768 会让参考行数翻 2.33×**。768p 下如果不需要
   像素级对齐，把参考视频保持在更小的画布上能省一半时间 —— 但要先验证模型是否接受非画布尺寸的参考。
10. **细节能量会把噪点算成细节**。评价「哪组更锐」时至少要同时看中值滤波后的纹理量和颗粒量，
    否则 shift 这类会让噪点上升的变量会得出反向结论。
11. **shift 的响应是台阶不是斜坡**。6.0 与 8.0 的产出几乎是同一条曲线（运动能量曲线相关 0.9817、
    全片细节 +0.5%），**中间值不值得单独跑**；要试就试 6.0 与 12.0 两档。

---

## 10. 768p 多参考（图 + 动作视频 + 音轨）

第 9 轮把 480p 的多参考结论拿到 768p 上复验了一遍（`lightx2v/Minimax-h3-Turbo-ref2va-8step-768p`，
1344×768 / 124 帧 / 8 步 / seed 42，1 张猫图 + 1 段净横移 +334 px 的动作参考视频 + 其音轨）：

| 通道 | 480p（P1）| 768p（第 9 轮）|
|---|---|---|
| 图 → 主体身份 | ✅ | ✅ |
| **视频 → 运镜（相机轨迹）** | ✅ 净横移 +160 px（参考 +334 px）| ❌ **净横移 −1 px**（帧间 mean\|dx\| = 0.008）|
| 视频 → 运动强度/节奏 | ❌（r = 0.01）| 🟡 r 从 0.067 升到 0.199 |
| 音轨 → 声景 | ✅ 谱形 r = +0.710 | ✅ 谱形 r = **+0.420**（无音频参考的组是 −0.15 ~ −0.20）|
| 互不串味 | ✅ | ✅ |
| 画质代价 | — | ⚠️ 细节 **−17%**、对比 −6.5%、色调转冷 |

**接线要点（768p）**：

```
load-video → video-to-rgb → image-resample(1344×768) → temporal-stack(max_mb 384) → 编码器
load-video(oport1) → audio-to-pcm(32000, stereo) → temporal-stack → 编码器（attach_audio 用音频自己的槽位号）
```

- 参考视频**必须缩到输出画布 1344×768**，且 `temporal-stack.max_mb` 提到 **384**
  （124 帧 @ 1344×768 = 366 MiB，默认 256 会截到 86 帧）。
- `attach_audio` 填**音频那条参考自己的槽位号**（1 起算）：1 图 + 1 视频 + 1 音轨 → `[3]`。
  日志会打 `2 reference(s)`（视频与音轨折叠成一条参考）。
- **768p 目前锁不住相机轨迹**，只能锁「运动强度/节奏」。要精确复刻运镜请留在 480p。



---

## 11. 上游动态与复核清单（2026-11-17 起，随夜间自动任务滚动更新）

> 本节由「vpipe 后续计划任务·每日 4 轮夜间自动执行」自动追加。**动手前先扫一遍这里**，
> 上游可能已经修了我们踩过的坑，或改了我们的结论赖以成立的语义。

### 11.1 版本落差（2026-11-17 实测）

- 本机：`vpipe 0.1 (9db5dd7*0)`（源码编译版，工作树带 `*` 即有本地改动）
- 上游 main：`4dc36b7`（2026-11-16）
- `git ls-remote` / compare API 都能查；**不要用 `strings` 探二进制**（本机二进制只读得出 157 条字符串，方法无效）

### 11.2 ★ shift 的值不要看日志（上游 issue #47 + #55）

- `video_shift` **确实能到达 denoiser**，但 `GenerateVideoStage` 的日志**恒打印 `12.0/3.0`**（#47 已 Closed 但 #55 复现了）
- → **报告与实验里禁止引用日志打印的 shift 值作为证据**；只能靠「改 shift → 量化出片 → 比 SSIM/纹理量」判断
- 这也解释了为什么 shift 写错「完全静默」：没有告警 + 日志还骗你

### 11.3 ★ 步数语义已变（上游 release）

上游把 MiniMax H3 的 `steps` 语义从「跟随 MiniMax 官方的噪声级数」改为**与 ComfyUI / diffusers 对齐**。
旧语义下有人为 Turbo LoRA 效果把步数 +1，现在可以改回 ComfyUI 口径。

**影响**：第 16 节「4 步适配器必须同时把 pipeline `steps` 改成 4，否则静默劣化」的**语义前提已变**。
→ 升级到新版后，**必须重测 steps 曲线**（4 / 6 / 8 步的画质-耗时关系），不能直接套用旧数字。

### 11.4 ★ 续接变暗上游已修

上游新增「自动视频续接光照自适应」，修的是 MiniMax H3 VAE + DiT 引入的变暗（release 明说，并指向 `docs/MINIMAX-H3.md` 的 long video guide）。

- 第 16 节四段式续接的 **Δ亮度 1.1 → 8.6 → 13.3** 属于这个症状 → 升级后重跑续接实验
- **但几何跳变（+76 px / −86 px 垂直重构）是另一个问题，别指望一并解决**

### 11.5 ★ SSIM 口径：FFV1 现在支持 4:2:2 / 4:4:4

上游支持**可选 BT.601 / BT.709 + FFV1 4:2:2 / 4:4:4**。

- 我们长期记录的「视频流直接比 0.9736 vs PNG 落盘再比 0.9445，差 0.03 来自 4:2:0 色度往返」
  → **这 0.03 不是固有开销**，4:4:4 下应显著变小
- 做保真度对比时：**优先用 4:4:4 存储**，并在结论里写明像素格式
- 历史素材多数是 4:2:0 → 旧数字只能标注偏置，不能重算

### 11.6 ANE：在 M5 上关掉

上游原话：ANE 自 v0.1.51 起可用，**推荐 M4 用户**；**「After M5 it barely moves performance (GPU NAX is very fast)」**，
且要付 ANE 图编译成本，不划算。

→ **本机 M5 Pro：默认关闭 ANE**。若要对比，只在专门测 ANE 收益的那一组里开。

### 11.7 Swap allowance（默认 4 GB）

上游新增：允许 vpipe 把其它 app 的**非 wired** 内存驱入 swap，自己仍用 wired 内存、不抖动。
默认 4 GB，**解锁部分长视频任务**；设 0 恢复旧行为。

→ 24 GB 机器跑 768p / 241 帧时被内存卡住 → 值得实测开关前后的峰值内存与耗时。

### 11.8 纹理「沸腾」与 4 步适配器构图偏差

| 上游 issue | 内容 | 动作 |
|---|---|---|
| **#55**（Open） | 静态表面逐帧重绘；涉及 `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`（**我们 768p Ref2VA 用的就是它**）；`video_shift=12` / `audio_shift=3` / `condition_timestep=1.0`。作者测得 HF jitter：静态参考 0.0000 / 4 步 0.0914 / 8 步 0.0502 / 16 步 0.0437 | 加一条**抖动指标**（HF jitter），与「颗粒量 vs 纹理量」交叉验证；**步数越多抖动越小**这条要自己复现 |
| **#44**（Closed） | Ref2V Turbo 4-step LoRA **持久偏心构图**（768×544、shift 12/3）；Draw Things 同适配器无此问题 | 4 步适配器出图后**检查构图是否偏心**，不要只看清晰度 |

### 11.9 新路线：HyperFlow H3 Flash（GGUF 9.1 GB）

Video Rebirth（非 MiniMax 官方）的 H3 压缩少步版：

- fl2va **13.7B** / ref2va **13.9B**；4/6/8 步（默认 6）；**CFG = 1**；euler + BasicGuider
- 24 fps、默认 **1344×768**、**5.2–15 秒 = 124–362 帧（17n+5）**、32 kHz 立体声
- **GGUF Q4_K_M 仅 9.1 GB**（fl2va）/ 9.2 GB（ref2va）；Q8_0 14.9 / 15.2；INT8 convrot ~16 GB
- 文本编码器与两个 VAE 仍来自上游；**Python 包不下载 62 GB 的原始 transformer**
- **限制：GGUF / ComfyUI INT8 的 ref2va 只支持图片参考**（混视频 + 音频参考要走 Python INT8 包）
- 许可：MiniMax H3 Community License（排除美国 / 欧盟 / 英国 / 韩国）

**对本机的意义**：9.1 GB 比 8-bit FL2VA 轻得多 → 24 GB 机器值得试。
另可参考本机 `locmodel-h3-video` 技能（stable-diffusion.cpp + GGUF Q4 路线）。
**注意**：它**不是 adapter**，是一条独立模型路线，权重要从 ModelScope 侧确认可达。

### 11.10 其它上游增量（登记备查）

- **MiniMax H3 Image VAE 出图** / **H3-Image 图（DiT 可在 M5 上跑 int8）** → 第三条文生图路线
- **MiniMax H3 MotionCache** → 大步数生成可能提速
- **Open-VDN 与上游对齐**，支持类 Ref2VA 参考模式
- **修复：只有静图、无音频的 H3 Ref2VA 曾被错误拒绝** → 旧 build 上的 Ref2VA 消融结果需复核
- **Pika H3 Flex 6 步蒸馏权重**、**Open-H3-Regenerate-2K 2560×1440**、**MiniMax H3 L2VA（FL2VA 分区）**
- **LFM3-VL 可作为带视觉的语言模型**（我们用它做第三方复核，是官方支持的用法）
- **更广 LoRA 支持**：`.safetensors` 可直装 LoRA 槽（**FP8 暂不支持**）；ComfyUI int8 ConvRot × pruned 权重格式
- **上游文档扩到 27 个 md**；**英文版 `docs/MINIMAX-H3.md`（249 KB）比中文版多 73 KB** → 长视频指南的权威出处是英文版

---

## 12. 第 2 轮（2026-11-18）：YUV 口径归因收口 + 版本落差订正 + 适配器全量盘点

> 来源：`vpipe-lab/report/vpipe-H3-部署与测试报告.md` §18.2、`vpipe-lab/report/vpipe-daily-knowledge.md` 第 2 轮、
> 脚本 `vpipe-lab/scripts/p11_caliper.py`（原始数据 `vpipe-lab/p11-caliper.json`）。
> **本节是对第 11.5 节的实测修订 —— 第 11.5 节的直觉方向对，归因对象错。**

### 12.1 ★★ SSIM 口径：那个 0.03 是「比较域」造成的伪影，不是编码开销

第 11.5 节说「4:4:4 下这 0.03 应显著变小」。**实测：能变小，但真凶不是像素格式，是比较域。**

**三个口径（务必分清）**

| 口径 | 命令形态 | 比较域 | 与视频像素格式的关系 |
|---|---|---|---|
| **A**（我们长期用的） | `-i vid -i ref.png -lavfi "[0:v][1:v]ssim"` | **YUV 域** | **强依赖** —— ffmpeg 会把参考图 auto_scale 到视频格式 |
| **B**（PNG 落盘再比） | 两边都落 PNG 再比 | **RGB 域**（gbrp） | **无关** |
| **C**（判别用） | `-lavfi "[0:v]format=gbrp[a];[1:v]format=gbrp[b];[a][b]ssim"` | **RGB 域**（gbrp） | **无关** |

**★ 关键事实 1：B ≡ C**（实测 `|B − C| = 0.000000`，两个视频、四种格式全部成立）
→ 「PNG 落盘再比」和「强制 gbrp 域直比」**是同一个度量**，别当成两件事。

**★ 关键事实 2：口径 A 的读数随被测视频像素格式漂移，B/C 不漂移**

| 变体 | 口径 A | 口径 B | 口径 C |
|---|---:|---:|---:|
| yuv420p/limited/bt601 + h264 | **0.5796** | 0.3900 | 0.3900 |
| yuv422p/full/bt709 + ffv1 | **0.6191** | 0.3902 | 0.3902 |
| yuv444p/full/bt709 + ffv1 | **0.7244** | 0.3902 | 0.3902 |
| yuv444p/limited/bt709 + ffv1 | **0.7549** | 0.3901 | 0.3901 |

口径 A 极差 **0.1752**；口径 B/C 极差 **0.0003**。

**机制（`ffmpeg -v verbose` 直接读到，不是推测）**：口径 A 下**参考图被 auto_scale 到视频的像素格式**才参与比较：

```
4:2:0 视频：rgb24/gbr/pc  →  yuv420p/smpte170m/tv    ← 参考图被 4:2:0 抽样 + 压到 limited
4:4:4 视频：rgb24/gbr/pc  →  yuv444p/bt709/pc         ← 无抽样、范围无损
```

⇒ **口径 A 的分数里混进了「参考图被降采样的程度」**，它不是纯粹的相似度度量。

**★ 关键事实 3：4:2:0 真丢色度，但只丢 0.0046**
真值基准（从无损 4:4:4/ffv1 解出 RGB 帧，各变体**全用 ffv1 无损编码器**，差值只可能来自色度抽样）：

| 变体 | SSIM vs 真值逐帧 | PSNR |
|---|---:|---:|
| 自检（真值自比） | 1.000000 | inf |
| 4:4:4 | **0.999977** | 82.31 dB |
| 4:2:2 | 0.997014 | 48.63 dB |
| 4:2:0 | 0.995417 | 46.67 dB |
| 4:2:0 + limited + bt601 + h264（默认全链） | 0.984282 | 41.58 dB |

⇒ **真正吃掉 0.015 的是 `limited range` + `bt601` + `h264 有损压缩` 三条叠加，不是色度抽样。**

**★ 关键事实 4：方向 —— 口径 A 恒高于口径 B**（+0.17~0.19）
实测 `pika-i2va-shop.mp4 vs ref-cat-832.png`：A=0.5774 / B=0.3895 → **A−B = +0.1879**。
`p4-i2va-preview-fast.mp4 vs 锚定图`：A=0.3453 / B=0.1735 → **+0.1718**。
⇒ 报告第 17.3 / 18.1 节「PNG 再比偏低」**正确**；第 15.4.2 节括号「PNG 再比**会高**」**写反了**。

**★ 历史表安全性**：抽查第 16/17 节全部关键表被测文件，
像素格式**全部一致**（`h264 / yuv420p(tv, smpte170m)`）→ **历史结论不受影响**。

### 12.2 ★ 纪律：跨像素格式比较必须换口径

> **口径 A 的读数依赖被测视频的像素格式。**
> **今后凡跨格式比较（如 4:2:0 vs 4:4:4），必须用口径 B/C，或在比较前把双方统一转码到同一格式。**
> 同格式组间比较（当前所有历史表）不受此影响。

**生产链建议**：交付片用 `yuv444p + full + bt709 + ffv1`（或至少 `full + bt709`），
相对默认链（`yuv420p + limited + bt601 + h264`）**可回收约 0.011 SSIM**。
LFM3-VL 第三方复核也判不出 4:2:0 与 4:4:4 的肉眼差别（`vpipe-lab/scripts/vqa-p11.sh`）。

### 12.3 ★ 版本落差订正：「落后 12 个 commit」只对已装 App 成立

| 对象 | 实测版本 | 与上游 `main @ 4dc36b7` 的差距 |
|---|---|---|
| 已安装 App 的 `vpipe` helper | `0.1 (9db5dd7*0)` | **落后 12 个 commit** |
| 本地源码树 `vpipe-lab/repo/vpipe` | `33cda00`（2026-11-13，depth-1 shallow clone） | **只落后 2 个 commit** |
| 本地已编译 build | `build/apps/vpipe/vpipe` → `0.1 (33cda00*0)` | 可运行 |

⇒ **P12 的成本远低于原设想**：只需把源码树从 `33cda00` 再拉 2 个 commit，不必重编译整条链。

**本地 build 的坑**：直接跑会 `dlopen failed for libavutil.dylib` →
需 `DYLD_LIBRARY_PATH="/Applications/Vpipe Manager.app/Contents/Frameworks"`。
但这样会加载 App 的 `libvpipe`（9db5dd7），**版本串会从 `33cda00*0` 变成 `9db5dd7*0`**
→ 用版本串判断「跑的是哪个 build」时必须知道这一点。

### 12.4 ★ YUV 4:4:4 / BT.709 / FFV1：**已装 App 就支持**，不必等升级

第 11.1 / 11.5 节把这一组能力记作「上游新增，需升级才能拿到」。**实测证伪**：

- **行为探针**：非法 `pix_fmt="yuv999p"` 被拒并打印
  `pix_fmt 'yuv999p' is not yuv420p, yuv422p, yuv444p or rgb24`；`yuv444p` 被接受
- **实跑探针**：`load-video → video-to-rgb → rgb-to-video(yuv444p/full/bt709) → save-video(ffv1)`
  在**已装 App** 上跑通（797 ms），产出经 ffmpeg 确认为 `ffv1, yuv444p(pc, bt709), 832x480`
- **源码佐证**：`stages/rgb-to-video-stage.cc:34-40` 三个选项数组早已存在

⇒ **缺的不是能力，是「测量」。** 第 16 节的续接流水线（`p3-ext-part1.vpipeline`）**早就在用官方 lossless 配方**。

### 12.5 ModelScope `lightx2v/Minimax-h3-Turbo` 全量盘点（28 文件）

本机现有 4 个（`models/lightx2v/`，5.7 GB）：
`fl2v 4step v1.2 768p bf16`、`fl2v 8step v1.0 768p bf16`、`fl2v 8step v1.0 768p comfyui_bf16`、`ref2v 8step v1.0 768p bf16`。

**从未测过的新变体**（下载即用，各 1.38 GB）：

| 变体 | 文件 | CommitDate |
|---|---|---|
| Ref2VA 4-step 768p | `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors` | 2026-10-20 |
| Ref2VA 8-step v1.1 768p | `minimax_h3_ref2v_turbo_8step_v1.1_768p_bf16.safetensors` | 2026-10-20 |
| FL2VA 4-step v1.3 768p | `minimax_h3_fl2v_turbo_4step_v1.3_768p_bf16.safetensors` | 2026-10-20 |
| FL2VA 8-step v1.2 768p | `minimax_h3_fl2v_turbo_8step_v1.2_768p_bf16.safetensors` | 2026-11-12 |

**`_comfyui_bf16` 变体更大**（1.96–2.12 GB），两者都在。

### 12.6 ★ shift 规则再补一条线索：4-step 家族可能是 6.0

- `lightx2v/Minimax-h3-Turbo-SLA` 的 `minimax_h3_fl2v_turbo_4step_v0.1_768p_sla_bf16.safetensors`
  （1.29 GB）元数据写 **`video_flow_shift 6.0 / audio_flow_shift 3.0`**
- 而第 9.2 节实测：**Ref2VA 768p 是 12.0 更锐**（FL2VA 768p 是 6.0 更锐）
- ⇒ **4-step 家族的 shift 可能与 8-step 不同**；**在拿到 Ref2VA 4-step 768p 实测前，不改第 9.2 节任何结论**

### 12.7 4 步「固定时间步嵌入」机制（独立佐证第 9 节结论）

adapter 元数据带 `pdd_config`（`nfe=4, grid_size=256`）→ 调度器建 257 点 σ 网格切 4 段，
每段蒸馏头权重除以该段 σ 跨度；`num_inference_steps = steps + 1` 个 σ 点使 transformer 恰好被调用 `steps` 次；
`_FusedProjection` 存 4 组输出投影、`_FourStepController` 是按步切头的 forward hook、
`validate_four_step_call()` 断言恰好 4 次前向。

⇒ **从机制层面印证「4 步适配器必须同时把 pipeline `steps` 改成 4」，不是巧合。**

### 12.8 本轮新增的坑

1. **`ffprobe` 不在 PATH**（本机 `~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/` 只有 `ffmpeg`）
   → 用 `ffmpeg -hide_banner -i <file>` 读 `Stream #0:0 ... Video:` 行代替
2. **二进制字符串探测对本机 vpipe 无效**：`grep -a "yuv444p"` 0 命中
   （helper 只有 107 KB，真正代码在 `Contents/Frameworks/libvpipe*.dylib`）
   → 用**行为探针**（非法值被拒 + 实跑 + ffmpeg 验产物）
3. **ffv1 不接受 rgb24**：`avcodec_open2 failed: the frames are rgb24 and 'ffv1' may not accept it`
   → 零损失基准只能取「真值 PNG 序列自比」
4. **`ssim` stats 在 RGB 域输出 R/G/B 而非 Y/U/V** → 正则要兼容两种，否则整批测量**静默返回 None**
5. **PSNR 不能复用 SSIM 的滤镜串** → 必须把 `ssim` 换成 `psnr`
6. **Bash 工具 cwd 会在多次调用间漂移** → 写文件一律用绝对路径

---

## 13. ★★ 上游权威 shift 规则表（2026-11-18 第 3 轮核对，本节优先于第 9/12 节的经验结论）

> 来源：`vpipe-lab/repo/vpipe/docs/MINIMAX-H3.md`（上游官方文档，本地源码树 `33cda00` 自带）
> 行号：1946–1977、1508–1513、444–450；核对日期 2026-11-18
> **本节是上游自己写的适配器→shift 对照表，权威性高于任何社区表格与本实验室的经验对照。**

### 13.1 官方表（逐字转录）

| entry | partition | steps | shifts (v/a) | trained at |
|---|---|---|---|---|
| `Turbo few-step v4-600 EMA` (larryvrh) | FL2VA | 4–8 | 12 / 3 | — |
| `Turbo few-step v1-850 EMA` (larryvrh) | FL2VA | 4 | 12 / 3 | — |
| `Turbo 4-step v1.0 768p` (lightx2v) | FL2VA | 4 | **6** / 3 | 1344×768 |
| `Turbo 4-step v1.2 768p` (lightx2v) | FL2VA | 4 | **6** / 3 | 1344×768 |
| `Turbo 8-step v1.0 544p` (lightx2v) | FL2VA | 8 or 4 | 12 / 3 | 544p |
| `Turbo 8-step v1.0 768p` (lightx2v) | FL2VA | 8 | **6** / 3 | 1344×768 |
| `Turbo 4-step v0.1` (lightx2v) | **Ref2VA** | 4 | **12** / 3 | 544p |
| `Turbo 8-step v1.0 768p` (lightx2v) | **Ref2VA** | 8 | **6** / 3 | 1344×768 |

### 13.2 三条必须记住的规则

1. **「The shifts are part of the adapter, not a preference.」**
   lightx2v 的 768p 检查点是**在 video shift = 6 上蒸馏的**，而模型默认（以及所有非 768p 训练的适配器）是 12。
   蒸馏是拟合到它训练时的 σ 网格上的，**跑在错的网格上不是风格差异，是另一条 schedule，而且没有任何东西会报告它**。
2. **Ref2VA + 768p 必须用 `video_shift: 6.0`** —— 上游原话：
   「The Ref2VA adapter is the only one here that needs `video_shift: 6.0`.」
   上游官方长视频链（`docs/MINIMAX-H3.md:1511`）的 parts 2–4 也明确写 `video_shift: 6.0`。
3. **Ref2VA + 4 步 v0.1 是 544p 的变体，用 12 / 3**（不是 6）——「the one on the checkpoint's own shifts」。

### 13.3 ★ 「换 shift = 换场景」：shift 对照实验的方法学陷阱（新增，第 3 轮实测）

- 社区实测（AICU，2026-08-18）：「The same seed does not give you the same shot. The sigma shift changes the path
  from noise to image, so the same seed and the same prompt produce a **different scene** — not a lower-quality version
  of the same scene.」
- **本实验室第 3 轮独立验证**：只改 `video_shift`（其余全同：参考图、提示词、seed 42、8 步、1344×768）
  → **首帧 SSIM 仅 0.46–0.58**（Ref2VA A(6.0) vs B(12.0) = **0.5213**；FL2VA 768p shift6 vs shift12 = **0.4618**）。
- 即使换成「静态参考图 + 完全静止提示词」，首帧 SSIM 仍只有 **0.5062** →
  **vpipe 里无法用「同一场景」来对照 shift**，因为 σ 网格决定了整条去噪轨迹。
- ⇒ **纪律：跨 shift 比较时，结论只能表述为「两条不同 σ 网格的对比」，不能表述为「同一模型渲染得更锐/更好」。**
  要控制场景，只能用**首帧锚定（FL2VA）**把第 0 帧钉死。
- 社区 5090 实测同样强调：「把 8 步配方硬拉到 768p，或者把 shift 交叉用，就是在跟自己较劲」。

### 13.4 ★★ `sigmas` 字段：可以手写 ComfyUI 的 σ 网格（上游 issue #55 的请求已被满足）

`minimax-h3-model-config` 阶段有 `sigmas` 字段（源码 `stages/minimax-h3-model-config-stage.cc:69`）：

- 「the VIDEO's sigmas **AS RUN**, in place of the grid `steps` and the shifts make -- comma-separated, terminal 0
  included, strictly falling from at most 1」
- **上游文档给的示例串正是 ComfyUI `er_sde` 的 σ 表**：
  `"1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"`
  （与上游 issue #55 正文里贴的 `ComfyUI er_sde sigmas 1, .9844, .9627, .9304, .878, .7579, .5527, .2369, 0` **逐位相同**）
- 「One forward per sigma but the last, so the list sets the step count and `generate-video`'s `steps` is not used.」
  （9 个 σ → 8 次前向；`steps` 与之不一致时**阶段会告警**）
- 「Wins over an adapter's own grid (a flow map, a sampling contract)」——对普通 LoRA 适配器直接生效。
- 音频的 σ 由 `video_shift` / `audio_shift` 映射得出（`video_shift` 仍然决定音频落在哪）。
- ⚠️ 「A distillation was fitted to the grid it was trained on, so a few-step adapter on another grid is **off its training**.」
  → 用 `sigmas` 换网格会让 Turbo 适配器离开它的训练网格，**画质变化不能全部归因于网格**。

### 13.5 `-split` 优于 `-comfyui`（上游明确推荐）

- 上游：「**`-split` is the diffusers copy, and it is the better file.** … Prefer the split one」
  理由：「a published fusion is **silently wrong on one of the two weight releases** and a split file is right on both」。
- 完整 `model_variant` 名（上游 `docs/MINIMAX-H3.md:2005-2016`）：

| variant | what |
|---|---|
| `lightx2v/Minimax-h3-Turbo-4step-768p` | FL2VA 4-step, shift 6 |
| `lightx2v/Minimax-h3-Turbo-8step` | FL2VA 8-step, 544p, shift 12 |
| `lightx2v/Minimax-h3-Turbo-8step-768p` | FL2VA 8-step, shift 6 |
| `lightx2v/Minimax-h3-Turbo-8step-768p-split` | the same, **split** — prefer this |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2` | FL2VA 4-step **v1.2**, shift 6, **split** — prefer this |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2-comfyui` | the same, fused |
| `lightx2v/Minimax-h3-Turbo-ref2va-4step` | Ref2VA 4-step, 544p, shift 12 |
| `lightx2v/Minimax-h3-Turbo-ref2va-4step-split` | the same, **split** — prefer this |
| `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` | Ref2VA 8-step, shift 6, **split** — prefer this |
| `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p-comfyui` | the same, fused |

- 本机装的是 `minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16.safetensors`（1.38 GB，**bf16 即 split 版**）→ **选对了**。

---

## 14. lightx2v 官方 Model Specs 表（2026-11-18 读 `github.com/ModelTC/Minimax-H3-Turbo`）

> 这是**厂商自己的表**，与上游 vpipe 文档的适配器→shift 对照表**逐行一致** → 可交叉印证。

| Model | partition | 训练分辨率 | 训练 shift (v/a) | 蒸馏 NFE | 推荐推理 NFE |
|---|---|---|---|---|---|
| FL2VA Turbo 4-step v0.1 | FL2VA/T2VA | 544p 混合 | 12/3 | 4 | 4 |
| FL2VA Turbo 8-step v1.0 | FL2VA/T2VA | 544p 混合 | 12/3 | 8 | 8 / 4 |
| FL2VA Turbo 4-step v1.0 768p | FL2VA/T2VA | 1344×768 | **6/3** | 4 | 4 |
| FL2VA Turbo 8-step v1.0 768p | FL2VA/T2VA | 1344×768 | **6/3** | 8 | 8 |
| Ref2VA Turbo 4-step v0.1 | Ref2VA | 544p 混合 | **12/3** | 4 | 4 |

- **官方表里没有 Ref2VA 8-step 768p 这一行** → 上游 vpipe 给它的 `video_shift: 6.0`
  是**从 768p 家族继承的推断**（上游自己也这么标注）→ 引用时要写成「推断」。
- 官方 Studio 用的是 **FL2VA Turbo 8-step v1.0 768p**，推荐 **8 NFE / video shift 6 / audio shift 3**。
- 官方 README 把 **v1.2（8 步 FL2VA）** 标为 ⭐ 新推荐（比 v1.1 更好，更接近 29 步 base）。

## 15. ModelScope 上的新变体（上游 catalog 尚未收录）

ModelScope `lightx2v/Minimax-h3-Turbo` 现有 **31 个文件 / 27 个 safetensors**，
而上游 vpipe catalog 只注册了 **12 个**。差集（**上游未收录 = 可上报的实质增量**）：

| 文件名 | 大小 | 备注 |
|---|---|---|
| `minimax_h3_fl2v_turbo_4step_v1.3_768p_bf16.safetensors` | 1.32 GB | ★ **v1.3 是最新一代 4 步 768p** |
| `minimax_h3_fl2v_turbo_4step_v1.3_768p_comfyui_bf16.safetensors` | 1.87 GB | 同上，ComfyUI 融合版 |
| `minimax_h3_fl2v_turbo_8step_v1.2_768p_bf16.safetensors` | 1.47 GB | 官方 README 的 ⭐ 推荐 |
| `minimax_h3_fl2v_turbo_8step_v1.2_768p_comfyui_bf16.safetensors` | 2.02 GB | 同上，融合版 |
| `minimax_h3_fl2v_turbo_8step_v1.1_768p_bf16.safetensors` | 1.32 GB | 8 步 v1.1 |
| `minimax_h3_ref2v_turbo_4step_v1.0_768p_bf16.safetensors` | 1.32 GB | ★ **Ref2VA 4 步 768p**（第 3 轮 P11b 想测的） |
| `minimax_h3_ref2v_turbo_8step_v1.1_768p_bf16.safetensors` | 1.32 GB | Ref2VA 8 步 v1.1 |
| `minimax_h3_fl2v_turbo_4step_v1.1_768p_fp8.safetensors` | **32.4 GB** | fp8 版（异常大，注意磁盘） |

- lightx2v 每个适配器**发布两次**：ComfyUI 融合版 + split（`to_q`/`to_k`/`to_v`）版
  → **优先 split**（上游文档：融合版在其中一个权重发布上会静默出错）。
- 本机已装：`minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16`（1.38 GB，bf16 即 split 版）。

## 16. 参考图缩放：官方三策略 + vpipe 的 `fit` 枚举

**lightx2v 官方**（`--reference-resize-mode`，蒸馏训练用 `match`，推理也推荐 `match`）：

| 模式 | 行为 | 缩放系数 |
|---|---|---|
| `match`（**推荐**） | 面积对齐目标画布、保比例、**不上采样** | `min(1, sqrt(target_area / ref_area))` |
| `max` | 保比例，只把短边 > 2048 的缩小 | `min(1, 2048 / ref_short_edge)` |
| `diffusers` | 保比例，短边强制 2048 | `2048 / ref_short_edge` |

**vpipe 侧对应物**：`image-resample` 的 `fit` 枚举为
`pad`（保长边+填充）/ `crop`（保短边+中心裁）/ **`stretch`（改长宽比）** / `manual` /
`pad_to_grid` / `crop_to_grid` / `crop_to_area`。

> ⚠️ **`stretch` 是唯一破坏长宽比的模式**。参考图非正方形时不要用。
> `pad` ≈ 官方 `match` 的保比例版本（本实验室的 `minimax-h3-reference-subject.jpg` 是 1024×1024 正方形，
> 所以 `stretch` 在那个夹具上零形变 —— **不能推广到其他参考图**）。

`reference_image_short_edge` 默认值：**2048（Ref2VA）/ 768（FL2VA）**。
2048 → 单张静图 **121 个 VAE tile**（最多 9 张）；1024 → **25 个**。
上游自己的示例用 `image-resample` + `reference_image_short_edge: 1024`。

## 2026-11-20 00:30 更新（第 12 轮）

### LightX2V Turbo v1.2 参数映射
- **来源**: LightX2V v1.2 Release Notes
- **适用**: `lightx2v/Minimax-h3-Turbo` (v1.2)
- **参数**:
  - `infer_steps`: 8 或 4
  - `video_flow_shift`: 12.0 (★ v1.1 为 6.0)
  - `audio_flow_shift`: 3.0
- **注意事项**: 
  - 修复了音频噪点问题；
  - 提升了对 Prompt 语义的还原；
  - **不兼容** Pruned 型基座（报 AdaLN shape 错误）。

## 2026-11-23 23:20 更新（第 13 轮 · 04:30 槽故障诊断后补跑）

**来源**：GitHub `tgo-app-dev/vpipe` commit `a6a1f53`（2026-11-23 09:54Z，85 文件 +17617/−509 行）。**注意：release 仍 v0.1.110（11-01），此增量仅在 main，本机 build 需更新后才能用。**

### pi-H3 2/4 步适配器原生进主仓（K128）
- 跑 ComfyUI **剪枝版** MiniMax-H3 checkpoint；每个 partition 入口带**精确 handle**（fl2va 可在多个剪枝副本中精确指向）。
- 适配器结构 = 部分投影低秩对 + 整块替换（每 block 调制 / 输出调制+norm / 双 head）；strength 非 0 时应用、0 时撤销；**step grid 来自适配器文件**。
- 被拒绝场景（按名字）：发布版 ckpt / split rank / 作为训练基座。

### DWD — Decoding Without a Decoder（K129）
- 适配器最后一步把 video rows 特征**直接交给 vae-decode 代替 latent**，vae-decode 跑适配器自己的 pixel head 而非 video VAE → **解码器不加载**，decode 阶段只记 head。
- 精度：对 restatement 读 f32 **0.0053**，参考自身 bf16 **0.0052**（上游口径，非本机 Apple Silicon 实测）。
- 意义：印证 K117 的 DWD 定义，首次给出 vpipe 内可复现路径（此前只能走外部 LakonLab v0.3）。

### train-lora 与内存关键（K130/K131/K133）
- `train-lora` 训练 MiniMax-H3 自身 DiT（两 partition）+ Qwen-Image 家族；样本=静帧或带音轨 clip 窗口，锚定首/末/双/无；Ref2VA 用 sidecar 命名参考。
- **调制表折叠 26 GB → 174 MB**（压到剪枝 ckpt 携带的 8 维曲线）；每 block 保留激活不重算、梯度逐位相同；AdamW/8bit/Adafactor/B 因子独立 lr → **24GB 机器跑 LoRA 的内存关键**。
- 三处内存记账修正（影响峰值显存口径，关联 K91，需重测）：video-ref-encoder 补 VAE encode+prefill 并在 prefill 前归还；prefill dequant scratch 按权重路线记账（此前 dense 按 quantized 收费）；fast decoder 每次 decode 后归还工作集。

### 新增流水线（K134）—— 流水线手册待补 8 条
- 4 条 LoRA：`minimax-h3-train-lora` / `-clips` / `-ref2va` / `-image-train-lora-edit`
- 3 条 pi-H3：`pi-h3-text-to-video` / `pi-h3-first-frame-to-video` / `pi-h3-first-last-to-video`
- 1 条准备：`prepare-pi-h3`
- 文档：`docs/LORA-TRAINING.md` +262、`docs/MINIMAX-H3.md` +246

### 版本口径警示（K135）
- main 已 +17617 行但 release 仍 v0.1.110 → **release 落后 main**，引用上游能力时必须注明 commit（`a6a1f53`），禁止以 release 号推断功能有无。

## 2026-11-24 00:06 更新（第 25 轮 · 社区增量，⚠️ 二手来源待复现，非本机实测）

**来源**：社区博客/教程（studio.aifilms.ai、lpqz.cn、mindpattern.ai），非上游 commit。**禁止并入已验证能力区，须本机复现后才采信。**

### FlashGen 4-step LoRA（K140，待复现）
- VSD（无数据分布匹配蒸馏），rank 64 BF16；攻击 qkv_proj/out_proj/fc1/fc2/**adaln_proj.linear**——时间步条件层是 4 步跨大噪声间隔保运动/音频同步的关键。
- 随附 `merge_lora_ckpt.py` 把适配器永久融合进 FL2VA 基座，并写入 base_schedule `[1.0,0.7,0.4,0.15,0.0]` 到 checkpoint config（**勿用通用线性 sigma 覆盖，否则边缘发软/瞬态浑浊**）。
- 目标 1344×768 / 5.2 s；FP8/INT8 ≈16–24 GB。与 K128（vpipe 原生 pi-H3 2/4 步）并列，属外部 4 步蒸馏路线。

### Turbo 三档耗时 + 双 shift 印证（K142，口径警示）
- ComfyUI-NPU 平台 768p/15s：50 步 Euler≈35.0 min / 21 步 res_multistep≈15.0 min / 8 步 Turbo≈6.9 min。
- **video shift 12 / audio shift 3** 双 flow schedule——印证 K106；旧版 ComfyUI 4 步音频会过度采样失真。
- `silu(t_emb)` 网格注入 pruned/curve 基座 → 单 LoRA 覆盖 bf16/int8/pruned（印证 K128 pruned）。
- ⚠️ NPU/15s 口径，**不可与本机 M5 768p/124f 29:34 直接比**。

### Character Swap LoRA V1.5（K141，待复现）
- akatz-ai，Ref2VA 上的 video-to-video 换角色；推荐配方 Int8 base + V1.5@1.0 + 8step Turbo@1.0，8 步 CFG=1.0 er_sde；原音 passthrough 非重生成。

### vLLM PR #52023（K143，本机不采信）
- `--model-variant fl2va+ref2va` 共享编码器省一半 encoder 内存；需 181.7 GiB 两 DiT 常驻，<120 GiB 启动失败 → 服务器大显存场景，与本机 24 GB 单 token 路线无关。

## 2026-11-24 06:30 更新（第 26 轮 · 权重仓库级指标 + 字节同构 + 社区步数口径）

### 仓库级指标（K150，HF `/api/models/lightx2v/Minimax-h3-Turbo`，2026-11-24 取）
- **downloads 1,793,937 / likes 1,235 / 存储 75.80 GB（70.6 GiB）/ 30 文件（26 safetensors + .gitattributes/LICENSE/NOTICE/README）**。
- **lastModified = 2026-11-16T09:19:46Z** → 自 11-16 起 **8 天无新权重**；结合文件清单**最高版本是 v1.3（4 步）/ v1.2（8 步）** ⇒ **不存在 v1.4**，v1.3 即当前 4 步终版。
- ModelScope 镜像侧 Downloads 64,476、LastUpdated 同为 2026-11-16 —— 两站同步。

### 4 步家族字节级同构（K151，★ 工程可用）
`minimax_h3_fl2v_turbo_4step` 的 768p bf16 各版本 **LFS size 全部相同**：

| 文件 | size (B) | 备注 |
|---|---|---|
| `..._4step_v1.0_768p_bf16` | 1,383,677,808 | |
| `..._4step_v1.1_768p_bf16` | 1,383,677,808 | |
| `..._4step_v1.2_768p_bf16` | 1,383,677,808 | 本机已装 |
| `..._4step_v1.3_768p_bf16` | 1,383,677,808 | **本机未装** |
| `..._4step_v1.1_768p_fp8` | 34,023,114,720 | = 31.69 GiB（ModelScope 报 32.4 GB，勾稽一致） |

（各文件 sha256 **互不相同** → 同构但非同文件。）

**结论**：v1.0→v1.3 的迭代**只换权重值、不改张量结构与 rank** ⇒ **v1.3 可直接占 v1.2 的槽位做 A/B，无需修改任何 shape / rank / 配方假设**。这条把「换版本」从「改管线」降级为「换路径」。
- 8 步家族不满足该规律：v1.2 = **1,543,291,302 B**（比 v1.0/v1.1 的 1,383,677,808 大 11.5%），`_comfyui_bf16` 版 = 2,115,772,012 B ⇒ 8 步 v1.2 是**结构性变更**，不可直接换槽。
- Ref2VA 4 步只有 v0.1 与 v1.0 两个 768p 版（均 1,383,677,808 / 1,956,193,000）；8 步有 v1.0 / v1.1。

### 社区「4 步不够」口径（K152，⚠️ 二手待复现，非上游 commit、非本机实测）
- 来源：minimax3.com/blog/minimax-h3-turbo-steps（2026-08-15，**明示非官方**）。
- 断言：两位 LoRA 作者**均推荐 >4 步**；larryvrh card 称 6–8「明显优于 4」，**>8 无增益反过锐**；**ModelTC 官方示例工作流默认挂 8 步 checkpoint 而非 4 步**。
- 唯一基准（RTX 5080 / 15 s / ~0.5 MP，作者自述「一个人的机器、非受控」）：标准 **1035 s** → 仅 SageAttention **487 s** → Turbo+Sage **193 s**。
- 核心指标是 **time-per-usable-clip**：5× 采样缩减在「算上弃片重跑」后端到端只兑现约 **2×**。
- 已知短板：快/大运动在低步数下拖影；Ref2VA 参考遵循是最不成熟环节（仍 v0.1）。
- **与本机冲突**：18.21 用静态/慢速夹具测得 4 步细节能量 170.6 > 8 步 167.7。**不矛盾——适用场景不同**；本机口径应加限定「静态或慢运动」。待用运动夹具复现（P40）。

---

## 2026-11-25 追加（第 27 轮 · 官方迭代方向 + 8 步家族结构性变更）

### K156 ★★ 官方两条线的迭代投入不对称（ModelScope + HF 交叉，2026-11-25 取）
- **4 步线最后更新 = 2026-10-20（v1.3）**，此后 36 天无新版本；**8 步线最后更新 = 2026-11-12（v1.2）**，且 v1.2 相对 v1.1 是**结构性变更**（bf16 1,383,677,808 → **1,543,291,302 B，+11.5%**；comfyui 版 1,956,193,000 → **2,115,772,012 B**）。
- 推论（**这是从日期+字节推的，非官方声明**）：官方把新增投入放在 **8 步线**，4 步线自 v1.3 起进入冻结。⇒ 本机若把 4 步当唯一主力，等于押在一条**已停止迭代**的分支上。
- 官方 README 在 **2026-11-24 14:36** 更新过（唯一变更文件，权重 0 变更），内容仍是「**⭐ v1.2（8 步）** 优于 v1.1（8 步）/ Pika LoRA / 29 步 base」。⚠️ 该对比**只比 8 步 v1.1 vs 8 步 v1.2，不涉及 4 步** —— 不能拿它给「4 步不够」背书，只能证明「8 步线还在被维护」。
- 8 步 v1.2 **本机未安装**（本机 8 步只有 v1.0）。因是结构性变更，**不可**按 K151 的字节同构直接换槽（换了会 shape/rank 不匹配）。

### K150 指标复核（2026-11-25，HF 页面口径）
- downloads **1,793,803** / likes **1.24k** / discussions **63** / Spaces **100** / collection `MiniMax-H3-LightX2V`（11 项）。相对 11-24 的 1,793,937 基本**持平**（-134，噪声级）。
- ModelScope 镜像：**31 文件 / 26 safetensors / 75,804,462,395 B（75.80 GB）**，非权重文件 5 个（`.gitattributes` / `LICENSE` / `NOTICE` / `README.md` / `configuration.json`）。

## 2026-11-25 追加（第 28 轮 · H3-Tiny 三步采样契约 + 第四日静默 + RelayVSR 显式画布）

### K166 ★ H3-Tiny 的采样契约与 vpipe 现有 4/8 步家族**不同族**
- H3-Tiny 17B/14B OKD **没有少数步蒸馏**，走 **50 步 + `simple` scheduler + 无 CFG（BasicGuider）**，且**不叠加 turbo LoRA**（README 明写）。few-step 版则用自家节点给出的 sigma 网格：`linspace(1, 0, steps+1)` @ **video shift 12**，默认 **6 步（≥4）**。
- ⇒ 与本机现状的差异是**两层**：① 步数 50（本机 4/8 步配方不适用）；② **video shift 12**（本机 4 步/8 步配方不是 12）。
- ⇒ **不要拿 H3-Tiny 的「不训练可用」当成「可以直接套本机 4 步加速」**。它的质量前提是 50 步全采样；若强行 6 步，必须用它的 few-step 权重，不是 17B pruned。
- 参考生成参数（README）：文本编码器与 VAE 用 `Comfy-Org/MiniMax-H3`，DiT 放 `models/diffusion_models/`。

### K160 ★ 上游第 4 日静默（快照，须逐日复查）
- HEAD 仍 **a6a1f53**（`pushed_at 2026-11-23T11:20:51Z`，**满 2 天未动**）；release 最新仍 **v0.1.110（2026-11-01）→ 落后 main 24 天**；issue **14 条全开**（最新仍 #59 / 11-16 / 0 评论）；**PR = 0**；仓库 269 star / 27 fork / 36,920 KB（与上轮完全一致）。
- 官方 `docs/` 目录 2026-11-25 复查仍**无任何 H3-Tiny 相关文档**（`grep -li "h3-tiny" docs/` 空），MINIMAX-H3.md 的 pruned 段落只描述 **[1025, 8]** 曲线形式。
- 上游代码里 `pruned` 仅作为「ComfyUI 曲线形式」的识别标志（`adaln_t_table` 存在即 pruned），**不区分 50 块原版与 42 块剪枝版** → 这正是 K163 的 gate 成因。

### K167 ★ LightX2V RelayVSR x4 支持显式输出画布（#1735，2026-11-19）
- `8bbaabd`「feat(relayvsr): accept an explicit output size for x4」：此前 x4 的输出尺寸只能由 `sr_ratio` 推（两轴同倍），新增可直接指定画布。动机原文举的例子正是 **MiniMax-H3 的 16:9 768P = 1344×768（area cap 768×1344）**，两轴倍率不同。
- 与本机关系：vpipe 的 `video-to-rgb` 有 `output_width/output_height` 成对参数（`stages/audio-video/video-to-rgb-stage.cc:326-350`），但 **relayvsr-upscale 本身无显式画布参数** → 若要「先超分再压回固定画布」，需在流水线里串一个 video-to-rgb 或 resize 步骤。属**生态印证**，非本机新能力。
- LightX2V 近 8 条 commit（11-19 ~ 11-23）中与 H3 相关仅 2 条：#1749（causal 音频 9 chunk，K158）与 #1743（`minimax_h3_image` 推理复用 DiT conditioning + tiled VAE 加速，+89/−18，**图像侧非视频侧**）。

## 2026-11-25 追加（第 29 轮 · Turbo Fusion 与采样契约冲突 + 第 5 日静默）

### K169 ★★★ LightX2V「Turbo Fusion」三源融合适配器（2026-11-24 18:50 UTC）
- 融合配方（4 步与 8 步**共用**，只换基座 ckpt）：**LightX2V cm2200 蒸馏 ckpt ×1.0 + Pika Ref2VA Flex ×0.4 + Larry Turbo v4 step-600 EMA ×0.4**。
- **推理期不再叠三个适配器**（模型卡原话：Download one variant, do not add the component LoRAs on top）。
- 变体（HF = ModelScope，逐位同字节）：
  | 变体 | 4 步 | 8 步 |
  |---|---|---|
  | Full | 3,778,242,236 | 3,778,245,950 |
  | Full `_comfyui` | 5,209,509,820 | 5,209,509,820 |
  | Lite r32 | 665,148,804 | 665,148,812 |
  | Lite r32 `_comfyui` | 808,241,732 | 808,241,732 |
  | `pruned/…_pruned_comfyui` | 5,220,193,444 | 5,220,193,444 |
  | `pruned/…_lite_r32_pruned_comfyui` | **818,925,468** | 818,925,468 |
- **采样契约：Euler + video flow shift 12 + audio flow shift 3**。
- ⚠️ **与本机现役配方冲突**：`scripts/dance-woman-768p.vpipeline` 是 lightx2v ref2va-8step-768p + `video_shift 6.0 / audio_shift 3.0`。**直接换槽不改 shift = 用错轨迹**，结论不可归因。
- 8 步与 4 步的 Full 差 3,714 B 却**不是同一文件**（基座 ckpt 不同）→ `ls -l` 不可判同，须比 `__metadata__.recipe` / `source_sha256`。

### K168 ★ 上游第 5 日静默（快照，须逐日复查；口径已改）
- HEAD `a6a1f53`：`commit.author.date 2026-11-23T09:54:27Z` / `pushed_at 11-23T11:20:51Z` → 至 2026-11-25 04:30 为 **1.77 天 / 1.73 天**。
- **口径修正**：上轮记「满 2 天」偏早。此后统一写「距 HEAD commit `<date>` 已 N.NN 天」，不再用「第 N 日」。
- release 最新 **v0.1.110（11-01）→ 落后 main 24 天**；issue 14 全开（无一条 updated 晚于创建日）；PR=0；269 star / 27 fork / 36,920 KB。

### K176 ★ 社区「自建融合」成惯例（非官方，待复现）
- HF 11-24 六小时内新增 ~15 个 H3 仓库；`ibyteohdear/MiniMax-H3-Pruned-DMD-FL2VA-Turbo-Fused`（434 dl）与 `-Pruned-LightX8-hybrid-Fused`（452 dl）**都是 pruned + 融合**形态。
- ⇒ 社区默认按 **pruned 基座**发布融合适配器。本机若跟进，pruned 通路是主干道。
- ⚠️ 二手来源，**待复现**，不并入已验证能力。

### 新迹象（非 H3，与本机量化路线同族）
- **stable-diffusion.cpp #2403**「support immediate LoRA merges for INT8 weights」（2026-11-23，改 `src/core/metal/int8.metal`）：**在 Metal 上把 LoRA 直接合并进 int8 权重**。本机 `lora-fuse` 只走 `fp8::decode_bf16` → f32，**int8 基座 + LoRA 融合是缺口**，与 P44（pruned_int8 + Fusion LoRA）同一个工程问题。

## 2026-11-25 追加（第 30 轮 · Kijai 混合量化包 + W4A8 实装确认）

### K179 ★★★ `Kijai/MiniMax-H3-experimental` 的 pruned W4A8 档比 Comfy-Org int8 小 44%
- 仓库 31 文件，`2026-11-24T07:43` 更新，likes 715。两个 DiT 主文件（零下载读头实测）：

| 文件 | 字节 | GiB | 结构 |
|---|---|---|---|
| `minimax_h3_ref2va_pruned_w4a8_mixed` | 11,770,657,048 | **10.96** | 50 块、`adaln_t_table [1025,8]` F32、208 量化层（**200 w4a8 + 8 int8_tensorwise**）、AdaLN `F16 [96768,8]` |
| `minimax_h3_fl2va_pruned_w4a8_mixed` | 12,540,858,008 | **11.68** | 同上，量化记录放 **header `_quantization_metadata`**（200 层），**无** `.comfy_quant` 旁挂 tensor |

- 对照 Comfy-Org `ref2va_pruned_int8_convrot` = **19.53 GiB（20,970,379,616 B）** ⇒ W4A8 档少下 **9.20 GB / 8.57 GiB**，37 GiB 磁盘下从「勉强」变「宽裕」。
- 8 个 int8 层 = `token_refiner.blocks.0.{attn.out_proj,attn.qkv_proj,mlp.fc1,mlp.fc2}` ×2 → **「mixed」= 两套格式混在一个文件里**，不是单一格式。
- 采样契约同 LightX2V 线：Euler + **video shift 12** + audio 3（改槽必须连 shift 一起改，见 K169）。

### K180 ★★ 同一家族的两种量化记录布局（新坑，第三次「同名不同构」）
| 布局 | 记录位置 | 本机读取路径 |
|---|---|---|
| ref2va 版 | 每层旁挂 `<layer>.comfy_quant`（U8 tensor，89 B JSON） | `declared_format_` 第一分支（读 tensor 文本） |
| fl2va 版 | header `__metadata__._quantization_metadata.layers[<layer>]` | `declared_format_` 第二分支（读 metadata） |
- 两分支都在 `generative-models/shared/fp8-layout.cc:79-121`，**都能读**；但**只看文件里有没有 `.comfy_quant` 会误判** fl2va 版「无量化记录」。
- ⇒ 纪律：判量化格式必须**同时**看 tensor 旁挂 + header metadata 两处。

### K178 ★★★ 本机已装 App（0.1 / `9db5dd7*0`，2026-11-14 构建）二进制里已含完整 pruned + W4A8 路径
- `strings "/Applications/Vpipe Manager.app/Contents/Frameworks/libvpipe.0.dylib"` 实测命中：
  - `w4a8_to_i8` / `w4a8_convrot_dequant`（W4A8 展宽 kernel）、`asym_w4a8_int8`
  - `h3_adaln_pruned_f16` / `h3_adaln_pruned_res_f16`（pruned 8 宽曲线 kernel）
  - `'{}' carries AdaLN curve branches but no curve table…`（缺表报错）
  - `a pruned AdaLN of {} x {} (adaln_t_table) is not the 8-wide curve this model reads`（**16 宽拒绝的原文**）
  - `carries ComfyUI weight diffs on the AdaLN (adaln_proj.linear.diff / .diff_b)`（`.diff_b` 支持）
- 上游侧对应 commit = `41d2789`（2026-11-12，W4A8 + pruned kernel 引入），**早于本机 build 日期** → 已编译进去。
- ⇒ **P44 不需要重编译源码**，直接手工 `hf_dir` 指目录即可试（K174 的 catalog 缺失仍成立）。

### K185–K188 ★★★ LightX2V 官方 H3 蒸馏 best practices（2026-11-25 `7fc25cd` / PR #1730）+ 4 步家族 alpha 变迁

> 来源：GitHub `ModelTC/lightx2v` commit `7fc25cddd61ffbace4e9be98e64618822468ba4a`（`lightx2v_train/docs/minimax_h3_distill.md` 全文 + 6 个 yaml 全量）；权重头取自 HF `resolve/main` + HTTP Range（0 下载）。

**1）官方改成了「双任务 × 两阶段」**

| 阶段 | 任务 | iters | LoRA | shift (video/audio) | LR |
|---|---|---|---|---|---|
| dCM | FL2AV | 1500 | rank/alpha **128/128**，AdaLN 与 norm_out 覆盖 **16/16** | **6.0 / 3.0** | student **2e-5**（AdamW 0.0/0.999，wd 0.01） |
| dCM | Ref2AV | 1500 | 同上 | **12.0 / 3.0** | 同上 |
| PDMD+GAN | FL2AV | 3000 | 同上 | rollout 6.0，**1500 步后切 12.0** | student 5e-5 / fake 4e-6 |
| PDMD+GAN | Ref2AV | 3000 | 同上 | rollout **12.0 / 3.0**（无调度） | 同上 |

- dCM 细节：`total_steps 48` / `skip_steps 1` / `loss_scale 100.0` / `ema_decay 0.999` / video·audio loss weight **0.8/0.8** / 32 GPU FSDP2 / 每 500 存 2 个。
- PDMD 细节：`fake_update_ratio 5`（→ **2500 fake : 500 student**）/ GAN `generator 0.005 / discriminator 0.01` / `feature_block 49` / `head_hidden_dim 1024` / `head_temporal_bins 4` / `critic_video_threshold 0.95` / `critic_audio_floor 0.85` / 每 100 存 2 个。
- 数据契约：`cache_dataset` + `meta.json`，**124 帧 @ 24 fps**，FL2AV **768×1344** / Ref2AV **1344×768**。

**2）结论（对本机直接可用）**

- **shift 6 vs 12 不是画质偏好，是任务分家**：FL2AV 线 6/3、Ref2AV 线 12/3。本机任何 **ref2va** 配方用 `video_shift 6.0` 都偏离官方 Ref2AV 蒸馏分布。
- **AdaLN 的 LoRA rank 是 16**（不是 128）→ 与本机 `pruned` 8 宽曲线 + `[96768,8]` 的形状家族一致，说明官方也在「主 rank 128 + AdaLN 低秩」这条路上。

**3）4 步 768p 家族：形状同构、强度变了 16 倍（K188）**

| 文件 | header | tensors | `__metadata__.alpha` | `lora_B` mean\|w\| | max |
|---|---|---|---|---|---|
| `fl2v_turbo_4step_v1.0_768p_bf16` | 81,768 B | 624 | **128** | 0.002028 | 0.0347 |
| `fl2v_turbo_4step_v1.1_768p_bf16` | 81,768 B | 624 | **128** | — | — |
| `fl2v_turbo_4step_v1.2_768p_bf16` | 81,768 B | 624 | **8** | 0.001995 | 0.0277 |
| `fl2v_turbo_4step_v1.3_768p_bf16` | 81,768 B | 624 | **8** | 0.001913 | 0.0173 |

- **key 集与 shape/offsets 四者完全一致**（逐键比对 True），rank 恒 128；**只有 `__metadata__.alpha` 变了**。
- 本机 `generative-models/shared/runtime-lora.cc:324-333` 读 `__metadata__.alpha`，`:445-452` 折成 `mul = alpha / rank`。
- ⇒ **换 LoRA 槽前必读三件：`__metadata__.alpha`、`lora_A` 第 0 维（rank）、是否带 per-module `.alpha`**。只看体积/形状会把 v1.3 当 v1.0 用，等效强度掉到 1/16。

**4）Fusion pruned 的 4 步 / 8 步 lite_r32（K191）**：828 tensors / header 100,232 B / key 与 shape 全同，**权重体抽样 sha 全不同**；`pruned_table_sha256` 两者相同（同基座同 AdaLN 表）。选档时按「步数」取文件，不能按体积判同。

### 第 31 轮（2026-11-26 04:30）：2K refine 的本机通路 / int8 适配器盲区 / alpha 两种语义

#### 1）本机 2K latent-upscale 是「一等能力」，社区件只是官方权重的 F16 转存（K198）

- **本机实现**：`stages/latent-upscale-stage.cc`（`type_name = "latent-upscale"`，参数 `scale` / `width` / `height` / `align`）+ `generative-models/minimax-h3/metal-minimax-h3-latent-upscaler.{h,cc}`。
- **网络结构**：`conv_in 24→512 (3×3×3)` → in stack 12 个 ResBlock（输入尺寸）+ 6 个 TemporalConv（dwconv kernel 5）→ 三线性 resize（**帧数不变**）→ out stack 同构 → `GroupNorm → SiLU → 3×3×3`。GroupNorm **按整条片统计**，所以必须**一次跑完整片**（不能切片）。
- **归一化**：默认 `Normalize::kRelease`（**双重归一**）——因为 ComfyUI 节点是拿原始 latent 调它，而 Open-H3 的 latent 已经是白化的。`kOnce` 才是节点本意。
- **精度**：默认 **F16**（残差峰约 8e3，f16 够用且精度是 bf16 的 4 倍）；`VPIPE_H3UP_BF16=1` 切 bf16；**f16 出非有限值会自动回退 bf16 重跑**（`upscale()` 内建 fallback）。
- **catalog 两条条目**：`Open-H3-Regenerate-2K` 与 `-IC`，`files = {"latent_upsampler/minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors", ...}`，`model_type = "minimax-h3-latent-upscaler"`。
- **社区对照（2026-11-26 读头）**：`SOLRICKS/MiniMax-H3-Upscaler:minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors`（690,592,672 B）与官方 `Efficient-Large-Model/Open-H3-Regenerate-2K:latent_upsampler/…_bf16.safetensors`（690,592,992 B）**322 tensors、key 集、shape 逐一致（onlyA 0 / onlyB 0），唯一差异 dtype BF16 → F16**（header 32,552 → 32,232 B）。
- **⇒ 纪律**：看到社区「新」upscaler 先做双读头比对，**同 key 同 shape 就是同一份权重的转存**，不必当新能力。2K 的真正缺口是 **refiner LoRA**（Open-H3 r256/576 或 SOLRICKS 的 int8 打包）。

#### 2）int8 **适配器因子**是第二条量化盲区，且是静默的（K199/K200/K201）

- **基座 vs 适配器是两条独立通路**：基座 int8/W4A8 走 `shared/fp8-layout.cc`（`int8_tensorwise` / `asym_w4a8_int8`，K178 的 `w4a8_to_i8`）；**LoRA 因子走 `shared/runtime-lora.cc`**，`take_()` / `take_f32_()` **只分支 BF16 / F16 / F32**（`:502-517`、`:537-546`）。
- `fp8::format_of()`（`shared/fp8.h:76-88`）对 `"I8"` **显式返回 `kNone`**（注释原文：`kNone for any other dtype (I8 among them)`）⇒ I8 因子取空 → `++_skipped` → **该模块静默不生效**，日志无错。
- **样本**：`SOLRICKS/MiniMax-H3-Upscaler:h3_upscale_refiner_int8.safetensors`（1,884,199,184 B / **624 tensors = 208 模块 × (lora_A I8 + lora_B I8 + alpha F32)**，50 块 + token_refiner 2 块）。
- **`.alpha` 语义第二例（K200）**：该件 metadata 写 `quantization: "int8_per_tensor_scales_in_lora_alpha_v1"`，`alpha` 是**量化 scale**（实测 `blocks.48.mlp.fc2 = 3.956e-4`、`blocks.15.attn.out_proj = 1.800e-4`），与 K188 的**整数倍率**（128 / 8）**语义相反**。且 rank **逐模块不同**（159 / 185 / 200 / 258 / 338 / 513）。
- **⇒ 换槽体检三件升级为四件**：① `__metadata__.alpha` 或 per-module `.alpha`；② **先判语义（整数倍率 vs 量化 scale，看量级 + metadata 的 `quantization` 键）**；③ rank（`lora_A` 第 0 维，**可能逐模块不同**）；④ 因子 dtype（**I8 会被静默跳过**）。
- **量化代价（K201，引用必带）**：`manifest.json` 自报 `converted_pairs 208`、相对 Frobenius median **0.0824** / mean 0.0875 / p95 **0.1432** / max **0.2841**，作者标 `visual_quality_metric: false`、`additional_training: false`。

#### 3）「融合进基座」的全量 diffusers 仓本机打不开（K204/K205）

- `ibyteohdear/MiniMax-H3-Pruned-{DMD-FL2VA-Turbo,LigthX8-hybrid}-Fused`：各 4 分片 ≈ **40.2 GB**，基座 `multimodalart/MiniMax-H3-Pruned/transformer`，方法 `load_lora_adapter → pin scaling → fuse_lora → strip peft → sharded save`。
  - `DMD-FL2VA-Turbo`：`LoRA alpha 15.156 / rank 16 / Fusion scale 0.897 / 363 层`；`LightX8-hybrid`：`alpha 48 / rank 48 / scale 1 / 312 层`。
  - 分片头实测：**176 tensors/片、无 `adaln_t_table`**，AdaLN 已烘进 `norm_out.folded_bias [10752]`；`config.json`：`adaln_rank 8 / hidden_size 5376 / num_layers 50 / text_dim 5120`。
- **本机判据**：`stages/model-catalog.cc:2502` 原文「`pruned` DiTs (a different model, not a different packing of this one)」；`WeightSet::open()` → `MetalLlamaWeights::open_model(dir)` 走单文件 / GGUF，**无 diffusers 分片目录（`diffusion_pytorch_model-0000K-of-0000N` + `index.json`）读取路径** ⇒ **看着像 H3、本机打不开**（第 4 类缺口，前三类：16 宽 Tiny / VSA `gate_compress` / GGUF）。
- **旁挂件缺口（K205）**：官方 pruned 基座 `transformer/adaln_affine.safetensors` = `adaln_basis F32 [8,2688]` + `adaln_mean F32 [2688]`（header 仅 184 B），本机全树 `grep -ri "adaln_affine|adaln_basis|adaln_mean"` = **0**。⇒ 8 宽曲线的**基与均值是旁挂的**，此前只比 `adaln_t_table [1025,8]` 会漏。

### 第 32 轮（2026-11-26 06:30）：**Fusion pruned 的 alpha 判决 = 按原样 1.0** / w6a8 双拒 / VAE int8 第三盲区

#### 1）★★★ Fusion pruned 适配器：alpha == rank，`mul ≡ 1.0`（P44 第③前置关闭）

- **文件**：`lightx2v/MiniMax-H3-Turbo-Fusion:pruned/minimax_h3_ref2v_turbo_fusion_4step_v1.0_pruned_comfyui.safetensors`（**5,220,193,444 B / 828 tensors**，BF16 467 + F32 361；`lite_r32` 版 **818,925,468 B**，HF 与 ModelScope 逐字节同）。
- **逐模块 alpha / rank 实测（4 步 full 档）**：

| 模块 | alpha | rank (`lora_A` 第 0 维) | mul = alpha/rank |
|---|---:|---:|---:|
| `blocks.N.adaln_proj.linear` | 32.0 | 32 | **1.00** |
| `blocks.N.attn.out_proj` | 320.0 | 320 | **1.00** |
| `blocks.N.mlp.fc1` | 320.0 | 320 | **1.00** |
| `blocks.N.mlp.fc2` | 320.0 | 320 | **1.00** |
| `blocks.N.attn.qkv_proj` | 960.0 | 960 | **1.00**（= 320 × 3，metadata `qkv_fusion: "…alpha multiplied by 3"`） |

- `__metadata__.output_alpha_counts = {"32.0":51,"320.0":156,"960.0":52}`、`default_training_alpha = 320.0`、`default_training_rank = 320`、`alpha_policy = "per-module alpha tensors take precedence over CLI default"`。
- **⇒ 结论**：这属 **K188 的「倍率」语义**，乘数**恰好 1.0**，**不需要任何折算**。P44 从「3 条前置」降为「2 条」。
- **⚠️ 反例警示**：rank 是**逐模块三档**（32 / 320 / 960，极差 30×）。任何「整个适配器一个 rank」的记账方式都会算错——`sibling_alpha()` 那条「多 rank 逐模块」的路径在这里是必须的。
- **`lite_r32` 档不同**：`output_rank_counts = {"32":207,"96":52}`、`output_alpha_counts = {"32.0":207,"96.0":52}`（同样 mul = 1.0），rank 只有 32 / 96 两档。**选档时不要拿 full 档的 alpha 表套 lite 档。**

#### 2）★★ Fusion pruned 的 AdaLN 修正：`diff_b` + LoRA 因子分工，无 `.diff`

- 51 个 `diff_b`（50 块 + `final_layer`），`F32 [96768]` / `F32 [10752]`；**`.diff` 权重补丁 = 0 个**。
- 同层并存 `lora_A [r,8]` + `lora_B [D,r]` + `.alpha`（F32）。
- metadata：`adaln_conversion: "A'=A@P; diff_b=(alpha/r)*B@A@mean; original B and alpha preserved"`、`adaln_precision: "FP32 A and diff_b; all other tensors retain source dtype"`。
- **本机契约吻合**：`bind_pruned_adaln_` 的 needle 用 `find`（命中 `diff_b`），后缀判定 `ends(".diff")` 对 `diff_b` 为假 → 走 is_b 分支**只写 bias 半区**（`dst += D*8`）；weight 半区由普通 LoRA 因子承担，**两半不重叠**。

#### 3）★★★ `pruned_w6a8` 是双重拒绝（不是一条门）

- `Comfy-Org/MiniMax-H3:diffusion_models/minimax_h3_ref2va_pruned_w6a8.safetensors` = **15,983,746,636 B / 1151 tensors**。
- `comfy_quant = {"format":"w6a8_int8","group_size":32,"convrot":true,"convrot_groupsize":256}`；权重 `I8 [21504,4032]`（6 bit 打包），旁挂 `weight_s_rel F8_E4M3 [21504,168]`（= K/32）+ `weight_s_channel F32 [21504]`。
- **两道门**：① `fp8-layout.cc:326` 按名拒绝 `w6a8_int8`；② 即便去掉名字门，I8 路径的 scale 校验（`:438-448`）只接受「1 个」或「每行 1 个」，**K/32 块 scale 会被「BLOCK-scaled encoding」拒**。
- **⇒ 「换个文件名试试」这条路彻底没有价值**。

#### 4）★★ 校准：CoFFmeteor 融合 int8 基座（契约全符合，但是真人素材）

- `Coffmeteor/MiniMaxH3-Realism-Turbo-Remix:int8/minimaxh3RealismTurbo_v10INT8.safetensors`，**20,967,649,144 B / 932 tensors**。
- `model.diffusion_model.` 全前缀 + `adaln_t_table F32 [1025,8]` + `qkv_proj I8 [21504,5376]` + `weight_scale F32 [21504,1]`（逐行）+ `comfy_quant {"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}` + 50 块 + `audio_patch_proj`/`audio_out` 齐 + **无 `time_embedder`**（pruned 形态）⇒ 本机四条判据全过。
- **⚠️ 只记存在性，不进能力表**：Singularity + Turbo + Realism + Motion 融合 + **真人 YouTube 微调**（`source.json` 明写），属真人素材；`__metadata__.required_prompt_prefix = "r34l1sm"`（**本机不读此键，触发词须手动加进 prompt**）。作者默认设置：960×544 → 1632×928、8+3 步、24 fps。

#### 5）★★★ 第三条量化盲区：VAE int8_convrot（比 K199 更危险）

- 社区件（Kijai `wip/` + 根目录）：`lightvae_lite` **1,036,943,392 B**、`lynnreal_light` **2,137,493,384 B**、`mt_video` **2,811,065,896 B**、官方 `video_vae_int8_convrot` **3,171,670,912 B**。README 自报 **decode ~2×**（需 ComfyUI 0.36.0）。
- 头实测：**I8/U8 各 48**、标量 `weight_scale`、`comfy_quant {"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}`。
- **本机 VAE 契约**：`linear_()` 读 **`.scales` + `.biases`**（仿射量化；`_quant_bits` 4/8、`_quant_group` 默认 64，来自 config 的 `quantization.{bits,group_size}`），**不认** ComfyUI 的 `weight_scale` / `comfy_quant`。
- **⇒ 失效形态**：`_quant_bits == 0` 时直接走 dense 路径拿 I8 张量 → **把整数码当像素值 → 画质崩塌且无错误日志**。比 K199（LoRA 因子静默 `_skipped`）更危险。
- **P48**：① `linear_()` 加 comfy 命名分支；② 转换脚本解成 BF16（lite VAE 只 1.04 GB → 解出约 4 GB，本机可接受）。
