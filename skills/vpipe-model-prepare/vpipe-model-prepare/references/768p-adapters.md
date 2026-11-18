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
