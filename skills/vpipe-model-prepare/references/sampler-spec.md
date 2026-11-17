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

## 6. 实测建议（本实验室尚未做，见状态看板 P18）

1. **基线**：静态夹具（22 帧）+ `euler`（默认）。
2. **对照 A**：同一夹具 + sampler spec `dmd`（`seed` 不设 → 用 clip 自己的 seed）。
3. **对照 B**：同一夹具 + `sigmas` = ComfyUI `er_sde` 表（已在 P13 做过一版，需 ≥3 次取方差）。
4. 指标：P13 的 `hf_jitter` / `static_hf_jitter` / `sharpness` / `frame_diff`，
   并按 **P15 测出的漂移基线**判定效应是否超过噪声。
5. **注意**：`dmd` 与 `er_sde` 是**两条不同的 σ 网格 + 不同的更新式**，
   混着比较会同时引入两个混淆项（网格 + 更新式）→ 要拆开测。
