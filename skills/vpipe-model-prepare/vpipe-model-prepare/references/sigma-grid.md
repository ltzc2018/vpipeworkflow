# H3 σ 网格 · 公式、换算与工具

> 最后更新：**2026-11-18 03:07**（第 3 轮续作 P15）
> 权威来源：① 上游 vpipe `docs/MINIMAX-H3.md`（源码树自带，`33cda00`）
> ② lightx2v / ModelTC 官方 `ModelTC/Minimax-H3-Turbo` README
> 两者逐位互验（33 个数值全对），本文给出的是**推导后的闭式公式**，不是抄来的表。

---

## 1. 一句话结论

**H3 的 σ 网格由「步数 N」和「两个 shift」完全决定，可以自己算出来，不必抄表。**

```
q_i        = (N - i) / N                       i = 0..N   （N+1 点，末点 q=0）
σ_video(q) = shift_v · q / (1 + (shift_v - 1) · q)
σ_audio(q) = shift_a · q / (1 + (shift_a - 1) · q)
```

- 视频与音频**共用同一个无偏移网格 q**，各自过一次自己的 shift；
- 末点 q = 0 → σ = 0，即「干净端点」，**不算一次前向**；
- `steps: N` = **N 次前向** over **N+1 个 σ**。

---

## 2. 两个一手来源的原文

### A. 上游 vpipe `docs/MINIMAX-H3.md`

> By default a clip runs `steps` forwards over `linspace(1, 0, steps + 1)`,
> pushed through each modality's shift, and every step is an Euler step.

> The **audio's** sigmas follow the way ComfyUI's H3 model derives them:
> each video sigma is taken back to the shared unshifted grid through
> `video_shift`, then out through `audio_shift`. So the two shifts still
> matter with a list of your own: they decide where the audio sits.
> The list for the example above, at shifts 12 / 3, puts the audio at
> 1, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0.

> The 8-step grid at shift 12 starts it at 0.632; at shift 6, 0.462;
> at shift 12, 16 steps start it at 0.444.

### B. lightx2v / ModelTC 官方 README

> For `NFE = N`, define the N transformer evaluation points on the unshifted
> grid as `q_i = (N - i) / N`, where `i = 0, 1, ..., N - 1`.
> For example, with `NFE = 4`, `video shift = 12`, and `audio shift = 3`,
> the shared grid is `q = [1, 0.75, 0.5, 0.25]`, giving video sigma
> `[1, 0.9730, 0.9231, 0.8000] -> 0` and audio sigma
> `[1, 0.9000, 0.7500, 0.5000] -> 0`; each list therefore uses exactly
> four NFEs.

---

## 3. 工具：`scripts/p15_sigma_grid.py`

```bash
# 默认网格：8 步、video_shift 6、audio_shift 3
python3 p15_sigma_grid.py --steps 8 --video-shift 6 --audio-shift 3

# 自定义视频 σ 串（ComfyUI 的 er_sde 表）→ 反解共享网格 q + 音频 σ 串
python3 p15_sigma_grid.py --sigmas "1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0" \
                           --video-shift 12 --audio-shift 3
```

**脚本每次运行都会自检 6 组共 33 个数值**（与 A、B 两个来源逐位比对），任何一条不符即退出码 2。

已核对的锚点：

| 场景 | 结果 | 来源 |
|---|---|---|
| N=4, 12/3 | video `1, 0.9730, 0.9231, 0.8000, 0`；audio `1, 0.9000, 0.7500, 0.5000, 0` | ModelTC |
| N=8, shift 12 | 最后一步起点 **0.632** | vpipe |
| N=8, shift 6 | 最后一步起点 **0.462** | vpipe |
| N=16, shift 12 | 最后一步起点 **0.444** | vpipe |
| er_sde 串 @12/3 | audio `1, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0` | vpipe |

---

## 4. 自定义 σ 串时，音频怎么跟着走

给了自己的**视频** σ 串（如 ComfyUI 的 `er_sde`），音频 σ **不是**直接拿同一串去过 audio_shift，
而是要**先反解 q、再过 audio_shift**：

```
q         = σ_v / (shift_v − σ_v · (shift_v − 1))
σ_audio   = shift_a · q / (1 + (shift_a − 1) · q)
```

例：er_sde 串在 `video_shift 12 / audio_shift 3` 下

```
video : 1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0
q     : 1, 0.840219, 0.682621, 0.526960, 0.374893, 0.206901, 0.093357, 0.025218, 0
audio : 1, 0.940390, 0.865815, 0.769689, 0.642753, 0.439031, 0.236005, 0.072021, 0
```

→ **换 `video_shift` 会连带改变音频落点**，即使视频 σ 串是手写的。

---

## 5. 步数语义（别再混）

| 写法 | 含义 |
|---|---|
| vpipe `steps: N` | **N 次前向**（over N+1 个 σ） |
| diffusers `num_inference_steps: N` | 网格点数（含端点）→ 实际 **N−1 次前向** |
| 换算 | vpipe `steps: N` ≡ diffusers `num_inference_steps: N + 1` |

上游明确选了 ComfyUI/diffusers 这一侧，理由两条：
1. **步数会「旅行」** —— 从 ComfyUI 工作流、模型卡、别人的设置里抄来的步数都是「前向次数」；
   按参考实现的读法抄，每次都会少一次前向（20 步 → 19 步）。
2. **适配器是按前向次数命名的** —— 「4 步」「8 步」蒸馏就是拟合到那个次数、那个网格；
   少一次前向就是另一个网格，而且**没有任何地方会告诉你**。

---

## 6. 三条会让结论翻车的纪律

1. **「最后一步」只有自定义 σ 串才能改变。**
   `steps` + shift 达不到；用 `sigmas` 时，末点 q = 0 那个 σ 之前的**倒数第二个 σ**决定了
   最后一步从多高落到干净（8 步 shift 12 → 0.632；shift 6 → 0.462；16 步 shift 12 → 0.444）。
   → **比较两条不同 σ 网格时，最后一步的落差是混淆项。**

2. **few-step 适配器是拟合在某个特定网格上的。**
   Turbo LoRA 蒸馏在「自己 shift 上的 shifted linspace 网格」；HyperFlow 与 Pika H3 Flex 在各自的网格上。
   换自己的 σ 串 = 让它们脱离训练网格 → 上游原话：「it may look better on one shot and worse on the next」。
   → **用 `sigmas` 测适配器时，结论不能外推到默认网格。**

3. **`sigmas` 与 `steps` 不一致时 stage 会 warn，但 `sigmas` 赢。**
   「One forward runs per sigma but the last, so this list is eight steps, whatever
   `generate-video`'s `steps` says (the stage warns when the two disagree).」

---

## 7. ★★★ 闭式公式已被「运行时真值」验证（2026-11-18 第 5 轮 P13b）

### 7.1 验证的性质升级

| 阶段 | 验证方式 | 证据强度 |
|---|---|---|
| 第 3 轮 | 两个一手来源**互相**对拍（上游 `docs/MINIMAX-H3.md` + ModelTC README），33 个数值 | 文档级一致 |
| **第 5 轮** | **与实际运行时回显逐值对拍** | **★ 运行时真值** |

第 5 轮 P13b 的 A 臂在 `autotune: false` 下跑通，日志回显（`logs/p13b-ersde-r1.log` 第 115 行）：

```
[INFO] h3-denoise: 8 steps by Euler, as the sampler asks,
  on the video's sigmas as given [1.0000, 0.9844, 0.9627, 0.9304, 0.8780, 0.7579, 0.5527, 0.2369, 0.0000],
  the audio's mapped through shifts 6/3 [1.0000, 0.9693, 0.9281, 0.8699, 0.7825, 0.6102, 0.3819, 0.1344, 0.0000]
```

用 `scripts/p15_sigma_grid.py` 的闭式公式复算**同一个 σ 串**（`--video-shift 6 --audio-shift 3`）：

```
audio sigma : 1, 0.969279, 0.928083, 0.869858, 0.782531, 0.610176, 0.381884, 0.134366, 0
反解出的共享无偏移网格 q : 1, 0.913173, 0.811378, 0.690208, 0.545342, 0.342864, 0.170771, 0.049195, 0
```

### 7.2 对拍结果

| # | 运行时回显 | 闭式公式 | 差 |
|---:|---|---|---|
| 1 | 1.0000 | 1.000000 | 0 |
| 2 | 0.9693 | 0.969279 | < 5e-5 |
| 3 | 0.9281 | 0.928083 | < 5e-5 |
| 4 | 0.8699 | 0.869858 | < 5e-5 |
| 5 | 0.7825 | 0.782531 | < 5e-5 |
| 6 | 0.6102 | 0.610176 | < 5e-5 |
| 7 | **0.3819** | **0.381884** | < 5e-5 |
| 8 | **0.1344** | **0.134366** | < 5e-5 |
| 9 | 0.0000 | 0.000000 | 0 |

⇒ **9 个值全部吻合到 4 位小数**（第 7、8 两个非平凡值最关键：
它们是「反解 q 再过 `audio_shift`」才能算出来的，直接从 `shift=3` 的 q 网格推不出来）。

**⇒ 公式 `q = σ_v / (shift_v − σ_v·(shift_v − 1))` 与
`σ_a = shift_a·q / (1 + (shift_a − 1)·q)` 已被运行时逐位证实。**

### 7.3 顺带证实的三件事

1. **`sigmas` 字段在本地 build `33cda00` 里真实生效**（不是被静默丢弃）：
   日志第 70 行回显 `the video's 8 steps on sigmas [1, 0.9844, …]`，
   第 77 行 `8 steps on the model config's sigmas`。
   → 印证第 3 轮坑 10.2 的纪律：**写完新字段必须在日志里找到它自己的回显。**
2. **音频 σ 确实走的是「共享 q 网格」**：给的是 shift 6/3，
   运行时把视频 σ 反解回 q（`[1, 0.913173, …, 0.049195, 0]`）再过 `audio_shift=3`
   → 得到 `[1, 0.9693, …, 0.1344, 0]`。**两模态共用一个 q，不是各自独立网格。**
3. **`autotune: false` 生效的旁证**：`[h3-dit] first forward at 9294 rows: 76 ms before block 0
   (… **gemm autotune 0** …)` —— 竞速开时这一项是 **4635 ms**。

### 7.4 第三方交叉印证（N+1 点网格是 H3 家族通用约定）

FastVideo 的 FastH3（**DMD2 蒸馏模型**，见 `h3-ecosystem-map.md` §3）：
**4 次前向 over 5 点 σ**、**8 次前向 over 9 点 σ**、base **49 次前向**。
⇒ 与我们的「N 次前向 over N+1 点」完全一致。
→ 「N+1 点」不是 vpipe 的怪癖，是 H3 家族的通用约定。
