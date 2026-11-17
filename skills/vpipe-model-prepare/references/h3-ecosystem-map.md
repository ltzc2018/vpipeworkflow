# MiniMax H3 生态能力地图（2026-11-18 第 5 轮新建）

> 最后更新：**2026-11-18 06:31**（第 5 轮夜间知识同步）
> 用途：判断「生态已经有的能力」与「vpipe 本机能不能跑」的差距，避免重复搜索、避免误判本机缺失能力。
> 方法学纪律见本文件末尾第 5 节 —— **任何「本机跑不了 X」的下结论之前，必须先扫源码树 + 上游树做文件级差分**。

---

## 0. 一句话总览（截至 2026-11-18）

| 能力 | 生态有 | vpipe 支持 | 本机能跑 | 权重体积 | 备注 |
|---|:--:|:--:|:--:|---|---|
| **ControlNet Union**（8 种控制条件） | ✅ | ❌ | ❌ | 2.30 GB（INT8 ConvRot） | **上游源码树 0 命中 → 需上游提需求** |
| FastH3（DMD2 4/8 步蒸馏） | ✅ | ❌ | ❌ | 22.90 GB（INT8） | 只有 T2V，无 FL2VA/Ref2VA |
| Ref2VA Acc-8Step（PDD 8-NFE LoRA） | ✅ | ⚠️ 待验 | ⚠️ | **1.73 GB** | 体积可接受，格式兼容性待验 |
| Singularity v2（Ref2VA LoRA） | ✅ | ⚠️ 待验 | ⚠️ | 3.30 GB | HDR/远景面部/运动模糊优化 |
| **MiniMax H3-Image**（16 MP 文生图） | ✅ | ❌ | ❌ | 21 GB（INT8） | **本实验室 T2I 新候选**，见 §2.2 |
| VDN（Video DeltaNet 线性注意力） | ✅ | ✅ | ✅ | 5.1 GB（本地已有） | 上游 28 个文件，本地已有 |
| FlashVSR / RelayVSR（Metal 超分） | ✅ | ✅ | ⚠️ 磁盘 | 3.27 / 6.48 / 10.58 GB | 见 `relayvsr-flashvsr.md` |
| 官方 H3 提示词结构（六段式） | ✅ | ⚠️ 文档里有 | ✅ | 免费 | 见 `h3-prompt-format.md` |

---

## 1. ControlNet Union（alibaba-pai）—— ★ 本轮最大新发现

### 1.1 是什么

- **`alibaba-pai/MiniMax-H3-Fun-Controlnet-Union`**：一个 checkpoint 同时支持 **8 种控制条件**
  —— Canny / Depth / HED / MLSD / Pose / Scribble / Layout / Gray，外加**视频 inpaint**。
- **2.0 分支**：同上（8 条件），采用 **10 层密集控制注入 + guidance 蒸馏**。
- 原理：把控制视频（边缘图/深度图/骨架）编码后，**通过 10 个控制块注入主 transformer**，
  在采样时直接注入结构 skip connection。
- 关键细节（社区实测原文）：控制 patch 叠在 **Ref2VA** 之上，
  并**在音频 token 上把 control skip 清零** → 运动锁死而音频照常生成。
- 姿态提取用 ComfyUI 内置 **SDPose Video Pose Extractor [Multi-Person]**
  （RT-DETRv4 人检 + 133 关键点）。

来源：
- <https://stable-diffusion-art.com/?p=20050>（2026-11 实测文，含工作流）
- <https://blog.gitcode.com/32bfb29921c15ea5bc469428b47f6739.html>（2.0 八条件速查）
- <https://blog.gitcode.com/4868d3a9a6a7b1b9d27fe567f75e48ea.html>（参数调优：`control_context_scale` 等 5 个关键值）

### 1.2 权重体积（★ ModelScope 实测，2026-11-18）

| 文件 | 体积 |
|---|---:|
| `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors` | **2.30 GB** |
| `minimax_h3_fun_controlnet_union_pruned_bf16.safetensors` | 4.22 GB |
| `minimax_h3_fun_controlnet_union_2.0_pruned_int8_convrot.safetensors` | 4.53 GB |
| `minimax_h3_fun_controlnet_union_2.0_pruned_bf16.safetensors` | 8.38 GB |

仓库：`Comfy-Org/MiniMax-H3` 与 `Kijai/MiniMax-H3-experimental` **两个仓库都有这 4 个文件**。

> ⚠️ **体积冲突记录**：社区博客写「约 13.5 GB」，而 ModelScope 实测是 2.30–8.38 GB。
> 差 3–6 倍 → **博客多半把不同精度/不同分支混算了**。同第 4 轮坑 12.7：
> **盘点模型仓库必须按文件逐个看，不能信聚合数字。**

### 1.3 ★ vpipe 支持：0（本轮实测，三重验证）

| 验证方法 | 结果 |
|---|---|
| 上游树 GitHub API（`git/trees/main?recursive=1`，**1776 条目**）| `controlnet` / `control` 关键词 **0 命中** |
| 本地源码树（`vpipe-lab/repo/vpipe`，**5234 文件**）| `controlnet` / `ControlNet` **0 命中** |
| 上游 issue（31 条）| 无 ControlNet 相关 issue |

**结论**：vpipe **完全没有** ControlNet 通路（不是「需要升级」，是「没有这个 stage」）。
→ 生态有能力、vpipe 没有 → **这是上游功能缺口**，适合写成 issue 提案（接第 6 条 issue）。

### 1.4 待验证（登记在计划表）

- **P27 · ControlNet Union 可行性预判**：先确认 vpipe 的 `generate-video` iport 能否挂一个
  「控制 latent」输入；若连输入口都没有 → 直接写上游 issue，不做本地实验。
- 预判成本：INT8 档 2.30 GB，**磁盘清到 ≥15 GiB 后可试**。

---

## 2. MiniMax H3-Image（2026-11-10/11 发布）—— ★ 本实验室 T2I 的新候选

### 2.1 规格

| 项 | 值 |
|---|---|
| 架构 | MiniMax H3 视频 DiT **去掉音频分支**；33.1B；dense 单流；**50 层**；hidden 5376；56 头 |
| 采样 | **6 步蒸馏**，**CFG 固定 1（无负面提示词）** |
| 原生分辨率 | 约 **16 MP**（4096×4096 = 1:1 … 6272×2688 = 21:9）；有效区间约 4–20 MP |
| 参考图 | 最多 **16 张** |
| 文本编码器 | **与 H3 视频共用 Qwen3-VL-32B**（DiT 读第 50 层） |
| Image VAE | 16× 空间下采样、24 latent 通道；2×2 patch → 每 token 覆盖 32×32 像素 |
| 权重 | BF16 **68.65 GB** |
| Comfy-Org 打包 | `minimax_h3_image_pruned_int8_convrot` **21 GB** / VAE fp16 **1.17 GB** / 提示扩写器 `qwen3.5_9b_w4a8_gptq` **7.34 GB** |
| 许可 | MiniMax-H3-Image Community License：**排除美国 / 欧盟 / 英国 / 韩国**；年营收 >100 万美元或对外托管服务需书面授权；商业产品界面须标注「MiniMax-H3-Image」 |

来源：
- <https://artrealmai.com/article/minimax-h3-image-open-weights-comfyui-16mp>（2026-11-10，含 Comfy 模板细节）
- <https://promptlab.cz/en/tutorial/minimax-h3-image-kresli-16megapixelove-obrazky-na-tvem-pocitaci-za-necelou-minutu>（2026-11-11）
- <https://vega.chat/blog/minimax-h3-image>（规格表）
- <https://sloptvnews.com/minimax-h3-image-open-weights-4k>（许可条款）

### 2.2 对本实验室的意义

- 本机已有的 T2I 模型是 **Z-Image-Turbo**（6B 蒸馏，8 步，45–46 s/张）与 **Krea-2-Turbo**（8 步）。
- **H3-Image 理论上更强**（16 MP 原生 + 1 checkpoint 同时做 T2I 与多参考编辑），
  但本机跑不了：**21 GB 模型 + 25.28 GB 文本编码器**（INT8 档），
  而本机 Data 卷当前只剩 **5.3 GiB** → **磁盘阻塞**。
- ⇒ 登记 **P28 · H3-Image 落地**：清盘后先测 INT8 档 21 GB；
  顺带可复用 H3 视频已有的 Qwen3-VL 文本编码器（若本机已下）。

### 2.3 ★★ H3-Image 的采样器结论 —— **对第 4 轮 P18 的跨模型印证**

社区独立实测（`pixelailabs.com` / `webhill.net`，2026-11）给出的三条修复：

| # | 调整 | 作用 |
|---|---|---|
| 1 | 分辨率拉到接近目标（8–16 MP+）再降采样，而不是把细节压进低分辨率 | 修脸型/皮肤块状 |
| 2 | **`SamplerLCM` 节点 + `simple` scheduler + 6 步 + `s_noise` 从 1.10 降到 0.90** | **修「crunchy grid」（过锐块状纹理）** |
| 3 | 弃用标签堆砌、写连贯长描述；接 `MiniMaxH3PromptWeight` 节点与单帧解码器 | 修质感与「塑料感」 |

**★ 与第 4 轮 P18 的关系（重要）**：

- P18 本机实测：vpipe 的 **`dmd` 采样器**（每步重注噪）把 HF jitter 压低 **−12.82%**、
  sharpness **+10.27%**；社区侧早已断言 ComfyUI 的 **`lcm`** ≡ vpipe 的 `dmd`。
- 本轮 H3-Image 社区实测：**默认 `euler` 过锐出块状纹理 → 换 `SamplerLCM`（≡ `dmd`）就修好了**。
- ⇒ **同一条机理（LCM/DMD 更新式 vs euler）在 H3 视频与 H3 图像两个模型家族上独立复现。**
  这是 P18 判决的**第三方、跨家族印证**，把它从「本机单点观察」升级为「家族级共识」。
- ⚠️ 但仍**不是根治**：P18 实测 `dmd` 的 HF jitter 仍是静态地板的 **94×**。
  H3-Image 那条也没说「完全消除」，只说「明显改善」。

来源：<https://pixelailabs.com/blog/minimax-h3-image-comfyui-realistic-photos>、
<https://webhill.net/en/telegram/post/three-comfyui-settings-to-eliminate-artifacts-in-minimax-h3-image>

---

## 3. FastVideo FastH3（DMD2 少步蒸馏）—— 与我们的 σ 网格工作直接相关

### 3.1 规格

| 项 | Preview v1（v0.1 / v0.2） | V2 |
|---|---|---|
| 前向次数 | **4** | **8** |
| σ 网格点数 | **5**（阶梯 `[999, 749, 500, 250]`） | **9** |
| 稀疏注意力 VSA | 90 % 稀疏（video-to-video 保留约 10 % tile；文本/音频 dense） | 80 % 稀疏 |
| 蒸馏 | **DMD2 data-free**（只用 prompt，不用目标视频 → 绕开版权） | 同（只重训 transformer） |
| 编码器 / VAE | 与 base H3 相同 | 与 v1 相同 |
| 状态 | v0.1 = 第 1400 步，v0.2 = 第 2900/4000 步 | — |
| 模式 | **只有 T2V**（未蒸馏 FL2VA / Ref2VA） | 同 |

### 3.2 ★★ 与我们的 σ 网格公式互相印证

- FastH3 v1 = **4 次前向 over 5 点 σ**；v2 = **8 次前向 over 9 点 σ**；base = 49 次前向。
- 我们的公式：`q_i = (N − i) / N`（**N+1 点**）、**N 次前向**。
  → **FastH3 的「4 步 = 5 点 σ」「8 步 = 9 点 σ」与我们的「N 次前向 over N+1 点」完全一致**。
- ⇒ **第三方实现（FastVideo 的 DMD2 蒸馏）在 N+1 点网格上训练**，
  说明「N+1 点」不是 vpipe 的怪癖，而是 H3 家族的通用约定。

### 3.3 ★★★ 必须区分的两个「DMD」（极易混淆）

| 名称 | 是什么 | 层次 | 本实验室状态 |
|---|---|---|---|
| **`dmd`（vpipe 采样器）** | **采样器**：每步重注噪 `x0 = x + σ·v` → `(1−σ')·x0 + σ'·n`（fresh noise） | 推理期，不改权重 | **第 4 轮 P18 已实测**：HF jitter −12.82% |
| **DMD2（FastH3 蒸馏）** | **蒸馏出的学生模型权重**：DMD2 loss 从冻结的 teacher 学 4/8 步 | 训练期，改权重 | 未测 |

- ⚠️ **两者名字相近但不是一回事**。FastH3 的少步能力来自「模型被蒸馏过」，
  **不是**来自「采样器选了 dmd」。
- ⇒ 读社区帖时看到「DMD2」不要自动映射到我们的 `dmd` 采样器结论。

### 3.4 实用坑

- `Beidouqixing/MiniMax-H3-DMD2-4step`（曾流传的链接）**HF 404** → 规范来源是 FastVideo 仓库。
- FastH3 / Nunchaku / 旋转 NVFP4 都需要**自定义加载器节点**，标准扩散模型加载器读不了。
- ComfyUI 侧 VSA-DataFree 4-step 还额外要 **3.59 GB 的 gate 文件**。

来源：<https://g.itadn.com/repos/wildminder/awesome-minimax-H3>（2026-11-16 快照）、
<https://wiro.ai/models/fastvideo/fast-h3>、<https://wiro.ai/models/fastvideo/fast-h3-v2>、
<https://lininn.cn/page/video-generation-fastest-2026>

---

## 4. 其他新适配器（ModelScope 实测体积，2026-11-18）

仓库：`Kijai/MiniMax-H3-experimental`（34 文件）

| 文件 | 体积 | 说明 |
|---|---:|---|
| `MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy.safetensors` | **1.73 GB** | 阿里 PAI **PDD（Parallel Decoding Distillation）8-NFE Ref2VA LoRA** |
| `MiniMax-H3-FL2VA-Acc-8Step_pruned_comfy.safetensors` | 1.73 GB | 同上，FL2VA |
| `minimax_h3_singularity_v2_lora_avg_rank_351_bf16.safetensors` | 3.30 GB | Singularity v2（Ref2VA 优化：HDR / 运动模糊 / 远景面部） |
| `minimax_h3_ref_lora_rank_256_bf16.safetensors` | 2.58 GB | Ref-Delta LoRA |
| `minimax_h3_open_regenerate_2k_refiner_rank_384_bf16.safetensors` | 5.87 GB | **2K 重生成 refiner**（MiniMax 官方 2K 阶段的社区实现） |
| `minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` | 22.90 GB | FastVideo VSA-DataFree 蒸馏（磁盘阻塞） |
| `minimax_h3_video_vae_int8_convrot.safetensors` | 3.17 GB | 社区 INT8 ConvRot 视频 VAE |

**★ 2K refiner 值得单独记**：MiniMax 官方演示里的「768p → 2K 再生成」阶段**没有开源**，
但社区已做出 refiner LoRA。→ 与第 1 轮「2K 模块未开源」的结论**有增量**（社区侧有补丁了）。

---

## 5. ★ 本文件的通用方法学（写下来是为了下次别再踩）

1. **「本机做不了 X」之前必须三件套**：
   (a) grep 本地源码树；(b) 与上游树做**文件级差分**（GitHub API 一次调用拿全树）；
   (c) 确认**不是「需要升级」而是「没有这个能力」**。
   → 本轮 ControlNet Union 就是这样定性的：**没有 stage，不是版本旧**。
2. **模型体积一律按文件逐个查**（ModelScope API），不信博客聚合数字（§1.2 的 3–6 倍偏差）。
3. **同名不同物**要单独建条目（DMD2 vs `dmd`，§3.3）。
4. **生态有能力 ≠ vpipe 有**；**vpipe 有 ≠ 本机跑得动**（磁盘/内存是独立的三道门）。

---

## 6. 来源清单（2026-11-18 第 5 轮）

| # | 来源 | 日期 | 一句话 |
|---|---|---|---|
| 1 | <https://stable-diffusion-art.com/?p=20050> | 2026-11 | ControlNet Union 工作流实测：8 条件 + 音频 token 清零 skip |
| 2 | <https://blog.gitcode.com/32bfb29921c15ea5bc469428b47f6739.html> | 2026-11 | Union 2.0 八条件速查表 |
| 3 | <https://blog.gitcode.com/4868d3a9a6a7b1b9d27fe567f75e48ea.html> | 2026-11 | `control_context_scale` 等 5 个参数 |
| 4 | <https://g.itadn.com/repos/wildminder/awesome-minimax-H3> | 2026-11-16 快照 | H3 全生态资源索引（本轮最重要的一手清单） |
| 5 | <https://artrealmai.com/article/minimax-h3-image-open-weights-comfyui-16mp> | 2026-11-10 | H3-Image 规格 + Comfy 模板 + 采样器设置 |
| 6 | <https://promptlab.cz/en/tutorial/minimax-h3-image-kresli-16megapixelove-obrazky-na-tvem-pocitaci-za-necelou-minutu> | 2026-11-11 | H3-Image 跑通与体积 |
| 7 | <https://vega.chat/blog/minimax-h3-image> | 2026-11 | H3-Image 规格表 / 许可 |
| 8 | <https://sloptvnews.com/minimax-h3-image-open-weights-4k> | 2026-11-10 | H3-Image 许可条款细节 |
| 9 | <https://pixelailabs.com/blog/minimax-h3-image-comfyui-realistic-photos> | 2026-11 | **SamplerLCM 修 crunchy grid**（P18 跨家族印证） |
| 10 | <https://webhill.net/en/telegram/post/three-comfyui-settings-to-eliminate-artifacts-in-minimax-h3-image> | 2026-11 | 同上（三条设置） |
| 11 | <https://wiro.ai/models/fastvideo/fast-h3> | 2026-11 | FastH3 v1 规格（4 前向 / 5 点 σ / 90 % VSA） |
| 12 | <https://wiro.ai/models/fastvideo/fast-h3-v2> | 2026-11-07 | FastH3 v2 规格（8 前向 / 9 点 σ / 80 % VSA） |
| 13 | <https://lininn.cn/page/video-generation-fastest-2026> | 2026-11 | FastH3 vs base H3 加速比（14.38×，B200） |
| 14 | ModelScope API `Comfy-Org/MiniMax-H3`（48 文件）/ `Kijai/MiniMax-H3-experimental`（34 文件）| 2026-11-18 实测 | 权重逐文件体积 |
