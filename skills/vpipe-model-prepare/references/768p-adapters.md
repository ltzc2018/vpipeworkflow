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


