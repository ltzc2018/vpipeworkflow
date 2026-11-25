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
| FlashVSR v1.1（**第 6 轮已实测**） | ✅ | ✅ | ✅ **1280×768 已跑通** | 6.953 GB（原生，ModelScope） | **实测：细节 +1160%，但对真值 SSIM −0.0506 / PSNR −4.05 dB** |
| **MiniMax-H3 Turbo-SLA** | ✅ | ❌ | ❌ | 1.4-1.9 GB (LoRA) | **85% 稀疏注意力 (SLA) 加速，需 vpipe 内置算子支持**（2026-11-19 第 9 轮） |
| **LTX-2.5**（22B 视频/音频模型） | ✅ | ✅（插件） | ⚠️ 22B | **ABI 8 独立插件** | **支持 T2V/I2V/音频参考，支持潜空间 2× 超分** |
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

## 1b. SLA (Sparse-Linear Attention) —— DMD 后的第二加速赛道（2026-11-19）

### 1.1 是什么

- **`lightx2v/Minimax-h3-Turbo-SLA`**：针对 MiniMax-H3 的 **4步 768p 蒸馏 LoRA**。
- **核心机制**：
  - **SLA (Sparse-Linear Attention)**：针对扩散 Transformer 的高效注意力实现。
  - 使用了 **85% 的注意力稀疏率**，跳过 85% 的计算量。
  - 与 DMD 不同，SLA 侧重于**每步内部运算逻辑的优化**，而 DMD 侧重于**更新式（Re-noising）**。
- **效果**：RTX 5090 上实测可实现 **2.5x 提速**。

### 1.2 vpipe 支持状态：❌ 暂不支持算子

- 扫描源码 `33cda00` 确认目前没有 `dynamic_sparse_attn` 或 `SLA` 相关算子。
- 这是一个重大的功能缺口，建议关注上游适配进度。

---

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

---

## 补充（2026-11-22 第 21 轮追加）

- **h3.c（antirez）官方承认位**：vpipe README 在 d347808 版本新增「Flagship workloads / performance」主章节，h3.c 从 docs 内小注**升级为 README 门面对比项**（含 YouTube 对比视频）。同 workload 三机全胜（快 21–24%）。生态图谱中 h3.c 的定位更新：**从「社区另类实现」变为「官方认证的主要竞品」**。
- **d347808（2026-11-21）**：上游重心移向 LLM/VLM 侧（DeepSeek-V4.1 GGUF vision tower）。H3 视频线自 d72c22f 后无新动作——与本实验室「核心 ABI 冻结、扩张在模型面」的第 19 轮判断一致。
- **社区口径提醒（第 1 轮已知，本轮复验）**：HyperFlow H3 Flash（Video Rebirth，13.7B/13.9B 剪枝版）是**压缩权重**路线，与 vpipe 的「全量 33B + 蒸馏适配器」路线不同族；对比任何 Flash 数据时先问「是权重压缩还是步数蒸馏」。

## 2026-11-22 追加（第 22 轮 · K120）：H3 生态规模首次量化 + Suno H3Move

- **Suno Visuals / H3Move**（2026-11-20 报道，新浪财经/和讯）：基于开源 H3 的音乐视频垂直应用（呼应歌曲结构、演唱口型同步、最长 15s、独立 Visual credits 计费、生成前嵌水印）。
- **H3 开源 100 天：社区衍生 1400+ 模型，HF 累计下载 1.4 亿次**（官方口径，MiniMax 港股公告转引）。
- 官方合作矩阵更新一览：RunningHub（H3 480P）、fal（H3Max 实时优化）、NVIDIA×MIT（Open-H3-Regenerate-2K）、Pika（H3 Flex）、**Suno（H3Move 音乐视频）**、斯坦福 LakonLab（**pi-H3** 2/4 步免 VAE，见同目录 ecosystem-tracking.md）。
- 对本实验室结论的影响：无技术路线变更；「生态有但只有托管形态」（14.11）之外新增第四形态实例——**垂直应用套壳**（H3Move：基座权重不变，场景数据后训练）。

## 2026-11-24 追加（第 26 轮 · DWD 学术出处 + 全生态零增量快照）

### DWD 原论文（K153，学术侧正式出处）
- **《Decoding Without a Decoder: Direct Pixel Prediction from Diffusion Transformers》**，arXiv **2611.22287**（cs.CV），v1 **2026-11-17** / v2 11-18。
- 作者：Hansheng Chen、Shengqu Cai、Jan Ackermann、Rayhan Zirvi、**Gordon Wetzstein**、Xinchen Yan、**Leonidas Guibas**（Stanford 系）。
- 方法：**原 denoising head 保持冻结**以锚定采样轨迹；只微调**最后几个 transformer block** + 新增线性 DWD head，用像素质量损失训练；DWD head 只在最后一步预测像素。
- 定量：Wan 视频 **warping error −23%**（细节失真与闪烁下降）；ImageNet **FID 1.55 → 1.43**（作者称为 pixel flow 模型新 SOTA）。
- 与本实验室的关系：
  - 印证 K117（pi-H3 权重发布的 DWD 定义）与 K129（vpipe 内实现：末步交 video rows 给 `vae-decode`、video VAE 不加载）。
  - ⚠️ **数值不可直接比**：论文的 −23% warping / 1.43 FID 是质量指标；本机 0.0053/0.0052 是**张量差值**。
  - **为 P36/P37 提供降本依据**：训练侧只需末几 block，比全量微调轻得多——24 GB 上的 LoRA/DWD 实验可行性因此上调。

### 2026-11-24 零增量快照（明日须复查；K121 教训：「零迹象」寿命可能只有 1 天）
| 生态位 | 端点 | 观察 |
|---|---|---|
| vpipe 主仓 | commits / releases / issues / pulls | HEAD 仍 **a6a1f53**；release 仍 **v0.1.110（11-01）落后 22 天**；issue **14 全开**；**PR=0** |
| ComfyUI 上游 | `/commits?per_page=10` | 近 10 条**无 MiniMax / H3 / audio-video / Turbo** |
| ComfyUI 官方博客 | blog.comfy.org | 无 H3 条目（仅有订阅墙，无正文可取证 → 记为「未取到」而非「无」） |
| stable-diffusion.cpp | `/commits?per_page=5` + releases | 最新 3b12781「idle TTLs for model weights」；**5 条全无 H3**；release `master-1122-3b12781` |
| ModelTC/Minimax-H3-Turbo 代码仓 | `/commits?per_page=5` | 最新 commit 仍 **02e26d5（2026-08-27）**，代码侧 3 个月未动 |
| lightx2v 权重仓 | HF `/api/models` + `/tree/main` | lastModified **2026-11-16**，**无 v1.4**；1.79M 下载 |
| Lakonik/pi-H3 | HF `/api/models` | lastModified **2026-11-21**，12 文件无新增；32,375 下载 |
| 社区中文面 | B站 / 知乎 / CSDN | 有大量「4 步 vs 8 步画质」内容，**均无日期、无 vpipe 关键词** → 仅记关注点，不采信 |

> 快照意义：本周生态动作集中在**上游代码**（已消化）而非权重/竞品；下游社区则集中在**步数选择的经验讨论**上——这与 K151/K152 指向同一件事：**版本已稳定，剩下的是怎么用**。

## 2026-11-25 追加（第 27 轮 · H3-Tiny 剪枝家族首次进图谱 + 因果流式 9 chunk + MPS 侧修复）

### K155 ★★ H3-Tiny（第三方结构化剪枝，首次进本图谱）
- 来源：GitHub `fuyi25/MiniMax-H3-Tiny`（仓库 2026-11-19 建，2026-11-24 11:51 最新 commit = 加 INT8 ComfyUI ckpt），44 star；HF 权重 `H3-Tiny/MiniMax-H3-Tiny-*`。
- **方法三件套**（README 明写）：① **AdaLN 低秩**——每 block 的 AdaLN 投影占 33.1B 中的 **13.0B**，其输入是 timestep 的固定函数，故**无数据**地在该输入上拟合 **rank-8** 近似；② **结构性删块**——按各 block 对 video/audio token 的改变量排序，保护音频最依赖的块，**删掉 50 块中的 8 块（6–11、13、15）** → 17B；③ **FFN 收窄**——每层 FFN 保留 14,336 通道中的 **9,792**，输出投影重拟合，再用 **OKD**（从 33B teacher 蒸馏）短训恢复 → 14B。
- **关键事实**：17B **剪完不训练即可用**（50 步）；few-step 版默认 **6 步（4 步也可，4–8 之间）**。
- ComfyUI 单文件（`H3-Tiny/MiniMax-H3-Tiny-ComfyUI`）：bf16 17B = **34.2 GB**、14B OKD = **28.1 GB**；INT8 ConvRot = **18.1 GB / 15.1 GB**（H200 / 1344×768 / 243 帧：DiT 占 **~17 GB VRAM** 而非 33 GB，速度与 bf16 齐平）。仓库总 **200 GB**。
- ⚠️ **与本机的关系**：本机 24 GB / 37 GiB 剩余磁盘 → **bf16 全部不可行**；INT8 17B 18.1 GB **单文件即可塞进 37 GiB 磁盘**，但需确认 vpipe 是否认这套剪枝结构（**vpipe catalog 无 h3_tiny 变体**，见下一条）。**登记 P42（待验证）**。
- ⚠️ **方法论提醒**：这是「**权重压缩**」路线（与 HyperFlow 13.7B、pi-H3 pruned 同族），**与 vpipe 的「全量 33B + 蒸馏适配器」不同族**。任何「和 Turbo 比速度」的比较必须先问「跑的是几 B」。

### K157 ★★ vpipe 本机 build 对剪枝/因果两条新路线均无 catalog 条目
- 本地树 HEAD `d72c22f`（落后基准 `a6a1f53` 1 个 commit）的 `stages/model-catalog.cc` 中，`tiny` 的所有出现都是 **TAE 预览解码器**（`2D tiny preview decoder`），**没有任何 H3-Tiny / h3_tiny 剪枝 checkpoint 条目**；`causal` 只出现在 Qwen-Image / Z-Image 的注释里（`causal_condition`），**无 MiniMax-H3 causal 流式条目**。
- ⇒ **两条社区/上游新路线本机目前都无法用 vpipe 直接跑**：Tiny 需等上游采纳或改源码；因果流式（K158）只存在于 LightX2V 侧。
- 定位纪律：**「社区有」≠「vpipe 能用」**。本报告一切「可用」判断以本机 catalog 为准。

### K158 ★ LightX2V 因果流式（RefA2AV 实时）扩到 9 chunk 音频历史
- `ModelTC/LightX2V` **#1749**（commit `e5744932`，2026-11-23 11:17，merged）：`CleanAttentionPolicy` 新增 `audio_latest_chunk_num = 9`（原 video 侧 `latest_chunk_num` 保 2），`kv_cache_max_t_rope` 7 → **9**；约束改为 `1 <= latest <= audio_latest <= kv_cache_max_t_rope`（原为「sink 与 recent 槽不相交」）。
- 语义：**视频历史只留 2 chunk、音频历史留到 9 chunk** → 音频的长期连贯性靠更长 KV 换，视频靠短窗换算力。`kv_cache.py` 的 workspace capacity 相应按 `AUDIO_CHANNELS * audio_rows * (audio_latest - latest)` 扩容。
- 影响面：**只影响 `configs/minimax_h3_causal/{5090,h100}/*refa2a{v,}*_realtime_768p*` 这 6 个实时流式配置**；离线 FL2VA/Ref2VA 不受影响。
- 与本机：**无关能力**（vpipe 无 causal 条目，K157），仅作「上游把音频历史当第一优先级」的生态信号记录。

### K159 ★ ComfyUI 侧 MPS 修复（对 Apple Silicon 派系有普适参考价值）
- `Comfy-Org/ComfyUI` **#17940**（merged 2026-11-23 22:36）：`comfy_extras/nodes_video_deflicker.py` 的 `warp()` 在 **MPS** 上报 `RuntimeError: MPS: Unsupported Border padding mode`。修法：MPS 分支把归一化采样坐标 **clamp 到 [−1, 1]** 并改用 `padding_mode="zeros"`（对 `mode="bilinear" + align_corners=True` 与 `border` 数学等价），非 MPS 保持 `border`。附单测验证数值等价。
- 与本机：**vpipe 不用 ComfyUI 节点**，无直接影响；但这是「MPS 缺 border padding → 用 clamp+zeros 等价替换」的**可复用绕法**，本机若在自研 MPS 算子（超分 warp / 光流采样）遇到同类报错可直接套用。

## 2026-11-25 追加（第 28 轮 · H3-Tiny 权重头零下载实测 → 本机 AdaLN 宽度硬 gate）

### K161 H3-Tiny INT8 ComfyUI 权重正式发布（K155 的量化细节补全）
- 发布 commit：`fuyi25/MiniMax-H3-Tiny@408d92a`「Add INT8 ComfyUI checkpoints」，**2026-11-24 11:51**，+198/−0 行（README +9、`comfyui/__init__.py` +68、新增 `scripts/quantize_comfyui_int8.py` 121 行）。
- 4 个 INT8 文件（HF `H3-Tiny/MiniMax-H3-Tiny-ComfyUI`）：17B Ref2VA **18.1 GB**、17B FL2VA **18.1 GB**、14B OKD Ref2VA **15.1 GB**、17B FewStep Ref2VA **18.1 GB**；对应 bf16 为 34.2 / 34.2 / 28.1 / 34.2 GB。
- 格式：**W8A8 + Hadamard rotation（ConvRot），group size 256**；文件内嵌 `__metadata__.h3tiny` JSON（`weights: int8_convrot`、`convrot_groupsize: 256`、`int8_linears: 168`、`adaln: curve|lowrank`、`params`）。
- 官方口径（README，H200 / 1344×768 / 243 帧）：DiT 占 **~17 GB VRAM**（bf16 33 GB），**采样速度与 bf16 齐平**，构图与运动保持。
- ⚠️ **Triton 后端陷阱**：`comfy-kitchen` 的 INT8 kernel 用 **int32 算元素偏移**，`rows × width > 2^31` 会**越界读出噪声帧**（10 s @1344×768 ≈ 246k token 就会触发，发生在 FFN）。作者的 `patch_triton_int8()` 按行分块（`max(256, (INT32_MAX // width - 512) // 256 * 256)` 行/次）绕开。**这是「量化正确但 kernel 索引溢出」类故障**，与精度无关。
- 月下载量 14,156 / 22 likes（HF 页面口径，2026-11-25 取）。

### K162 ★★★ H3-Tiny 权重头零下载实测（Range 读 8 字节 + JSON header，未下任何权重）
用 HTTP Range 只取 safetensors 头（81496 字节 JSON），得到四个文件的真实结构：

| 文件 | tensors | 主块数 | `adaln_t_table` | `blocks.0.adaln_proj` | `blocks.0.mlp.fc1/fc2` |
|---|---|---|---|---|---|
| 17B Ref2VA (int8) | 788 | **42**（0–41，即删 8 块） | **[1025, 16]** F32 | `.linear.weight [96768,16]` F32 | [28672,5376] I8 / [5376,14336] I8 |
| 17B FL2VA (int8) | 788 | 42 | [1025, 16] F32 | [96768,16] F32 | 同上 |
| 14B OKD Ref2VA (int8) | 788 | 42 | [1025, 16] F32 | [96768,16] F32 | **[19968,5376] / [5376,9984]** |
| 17B FewStep Ref2VA (int8) | 879 | 42 | **无**（`adaln: lowrank`） | **`.linear_1 [8,2688]` + `.linear_2 [96768,8]`** | 同上 17B |
| 14B OKD Ref2VA (bf16) | — | 42 | [1025, 16] F32 | [96768,16] F32 | [19584,5376] / [5376,**9792**] |

- 三个 Ref2VA/FL2VA/14B 文件的 `token_refiner` 仍是 2 块、`ffn` 仍是 14336（只有主块 FFN 收窄），`condition_proj [5376,5120]` BF16、`video_patch_proj [5376,96]`、`audio_patch_proj [5376,32]` 与原版一致。
- **17B 与 14B 的 INT8 文件张量数完全相同（788）**，区别只在 FFN 宽度 → 不能用 tensor 数区分。

### K163 ★★★ 本机 vpipe 对 H3-Tiny 是「硬 gate 拒绝」，不是「缺 catalog 条目」（修正 K157 的层次）
- `generative-models/minimax-h3/metal-minimax-h3-transformer.cc:830` 的校验：`if (out.pruned() && (out.time_dim != 8 || out.curve_grid < 2)) return fail("a pruned AdaLN of {} x {} (adaln_t_table) is not the 8-wide curve this model reads")`。而 `time_dim` 在 pruned 文件里直接取自 `adaln_t_table` 的第 2 维（同文件 :692 `tdim = grid > 0 ? dim("adaln_t_table", 1) : ...`）。
- H3-Tiny 三个 curve 文件的 `adaln_t_table` 是 **[1025, 16]** → `time_dim = 16 ≠ 8` → **加载即 fail**。Metal kernel `h3_adaln_pruned_f16` 内部同样硬编码 `for k < 8` 与 `coords + t*8`（`gpu-kernels/metal/ops/minimax_h3_regenerate.metal:183-201`），即便绕过校验也会读错。
- FewStep 版更进一步：它没有 `adaln_t_table`（`adaln: lowrank`），而是**双段低秩** `adaln_proj.linear_1 [8,2688]` → `linear_2 [96768,8]`，且恢复了 `time_embedder`。本机只认单段 `adaln_proj.linear`（`metal-minimax-h3-transformer.cc:2838/2905/4873`），**命名与结构双不匹配**。
- ⇒ **结论升级**：K157 说「catalog 无 h3_tiny 条目」是表层；真正的阻塞是 **AdaLN 曲线宽度（8 vs 16）与低秩分段方式**。P42 的可行性评估不必等上游「是否采纳」——**先要上游把 pruned AdaLN 从 8 宽泛化到任意宽**，这是一次 kernel + 校验的双改。
- 反例（说明泛化成本不高）：本机已有 `curve_grid` 变量与 `[curve_grid, time_dim]` 注释（`.h:138-142`），结构上只差把常量 8 改成参数。

### K164 ★ 14B OKD 的 INT8 与 bf16 **不同构**——ConvRot group=256 对齐 padding
- bf16 14B：`fc1 [19584,5376]`（=9792×2）、`fc2 [5376,9792]`；INT8 14B：`fc1 [19968,5376]`（=9984×2）、`fc2 [5376,9984]`。
- 差 **192 列**（9792 → 9984）。9792 不是 256 的倍数（9792/256=38.25），ConvRot group 256 要求列数对齐 → pad 到 9984（=39×256）。
- ⇒ **纪律**：**「INT8 版 = bf16 版量化」这个假设是错的**。凡是要按 shape 判等价、或做 INT8↔bf16 张量对拷的地方，必须先比对实际 shape，不能套用 bf16 的宽度。这也解释了 15.1 GB 与「28.1 GB bf16」并非恰好 1/2 关系之外的小额外开销。

### K165 ★ 官方 pruned（Comfy-Org）与 H3-Tiny 17B 的非 AdaLN 张量逐形状一致
- `Comfy-Org/MiniMax-H3` 的 `minimax_h3_{fl2va,ref2va}_pruned_int8_convrot`：932 tensors、**50 块**、`adaln_t_table [1025,8]`、`blocks.0.adaln_proj.linear.weight [96768,8]` F16、`qkv [21504,5376]` I8、`fc1 [28672,5376]`、`fc2 [5376,14336]`。
- 与 H3-Tiny 17B 相比：**qkv / out_proj[5376,7168] / fc1 / fc2 全部同形状**；差异只有两处 —— ① 块数 50 vs 42；② AdaLN 曲线 8 vs 16 宽。
- ⇒ H3-Tiny 的「结构化剪枝」对 vpipe 而言 = **「官方 pruned 形式少 8 块 + AdaLN 换宽」**，任何「支持 pruned 文件」的 loader 理论上只差这两点。这为上游若采纳时的改动量提供了精确边界。

## 2026-11-25 追加（第 29 轮 · pruned 家族分层 + Turbo Fusion 融合适配器）

### K173 ★★ 本机文档把 pruned 形式写成**一等支持路径**（此前误判为「本机不认」）
- `docs/MINIMAX-H3.md:2529-2600`：pruned = 时间步 MLP 换成 `adaln_t_table (1025×8)`，每块 AdaLN 投影 `[96768,8]`（发布形式是 `[96768,2688]`）。读法：t 夹到 0..1 → 表两行 lerp → 无 SiLU 直接投 → f32 求和 → 一次 bf16 舍入。投影全程驻留（bf16 约 77 MB），**不跑 AdaLN bake**。
- 文档明确列出三类 LoRA 的处理：① **为 pruned 转换的** → 直接应用（含 `.diff`/`.diff_b`）；② **在全模型上训练的** → 经 2688×8 基 U 与均值 m 搬上曲线（残差 ~2e-5），**需模型根下有未剪枝 ckpt**，否则 warn 并跳过；③ **改时间嵌入本身的**（`time_embedder` / flow-map 如 HyperFlow）→ 走 released ckpt 的 MLP，剩差再经 released AdaLN 投影补回（每 run 一次）。
- `…_pruned_w6a8`（6-bit codes）**按文件名拒绝**。

### K171 ★★ 8 宽 pruned + ComfyUI `.diff_b` 在本机是可读通路（源码级三道门）
1. **入口**：`metal-minimax-h3-transformer.cc:4834`（diffusers 布局）/ `:4897`（ComfyUI 布局），两处都只在 `c.pruned()` 时调 `bind_pruned_adaln_`。
2. **`.diff_b` 触发**：`bind_pruned_adaln_` 用 `lora::Adapter::file_touches(path,"adaln_proj.linear.diff")`，而 `runtime-lora.cc:890` 是 **`n.find(needle) != npos` 子串匹配** → `.diff_b` 命中。形状校验 `is_w ? [D,8] : [D]`（`.cc:4537`）→ `[96768] == D` 通过。
3. **每模块 `alpha`**：Fusion 的 `.alpha` 是 `[]` F32 标量张量；本机 `lora-fusion.cc:292` 读 `module + ".alpha"`，`runtime-lora.cc:445` 同款。**不是** `__metadata__.ss_alpha`。

⇒ 唯一硬条件 = **DiT 必须是 pruned 形式**。若基座是 released（未剪枝），整段 AdaLN 分支被 warn 丢弃（`.cc:4666-4675`），LoRA 的其余因子照常绑 → **看起来像「弱一点的适配器」而不报错**。这是最危险的静默降级。

### K170 ★★★ Turbo Fusion 三种布局的权重头（零下载实测）
| 布局 | tensors | 幂名/形状 | 用途 |
|---|---|---|---|
| Full（LightX2V/diffusers） | 1089 | `transformer_blocks.0.adaln_proj.linear.lora_A.default **[32,2688]**` + `lora_B.default **[96768,32]**` BF16 | **2688 宽** = 完整模型 AdaLN，pruned 基座上走「基 U 搬移」路径 |
| ComfyUI | 777 | `blocks.0.attn.qkv_proj.lora_A **[960,5376]**`（3×320 块对角）/ `lora_B **[21504,960]**`；每模块 `.alpha`；`output_rank_counts {"32":207,"96":52}` | 未剪枝基座 |
| **pruned/** | 828 | `adaln_proj.linear.lora_A **[32,8]**` + `lora_B **[96768,32]**` + **`diff_b [96768]` F32**；`default_training_rank 320`、`output_rank_counts {"32":51,"320":156,"960":52}` | **8 宽曲线**，本机可读（K171） |

- metadata 关键键：`adaln_conversion: A'=A@P; diff_b=(alpha/r)*B@A@mean; original B and alpha preserved`、`pruned_table_sha256`、`pruned_base_sha256`、`qkv_fusion: block diagonal B; concat A; alpha multiplied by 3`、`swi_glu_mapping: Diffusers [value;gate] -> ComfyUI [gate;value]`。
- **Lite r32 是 QR-product truncated SVD**：保留谱能量 98.41%（4 步）/ 97.80%（8 步）——模型卡自注「权重空间统计，不是感知质量」。

### K174 ★ catalog 仍无 pruned DiT 条目
- `stages/model-catalog.cc` 全文仅 1 处 `pruned`，是**注释**：「`pruned` DiTs (a different model, not a different packing of this one)」。
- ⇒ 用 pruned **必须手工 `hf_dir` 指向目录**，不能走 catalog 一键 prepare（K157 保留）。

### K172 ★ Comfy-Org pruned 各档体积（2026-11-25 实测）
| 文件 | 字节 | GiB |
|---|---|---|
| `ref2va_pruned_w6a8` | 15,983,746,636 | 14.89（**按名拒绝**） |
| `ref2va_pruned_fp8_scaled` | 20,958,205,608 | 19.52 |
| **`ref2va_pruned_int8_convrot`** | **20,970,379,616** | **19.53** ← 本机候选 |
| `ref2va_pruned_bf16` | 40,225,724,176 | 37.46 |
| 未剪枝 `ref2va_int8_convrot` | 34,038,894,550 | 31.70 |
| 未剪枝 `ref2va_bf16` | 66,280,487,368 | 61.72 |

## 2026-11-25 追加（第 30 轮 · Kijai experimental 全谱 + FastH3-VSA 权重落地 + 官方仓事故）

### K179 ★★★ pruned W4A8 混合档（本机最小 24 GB 可塞候选）
- `Kijai/MiniMax-H3-experimental` 的 `minimax_h3_{ref2va,fl2va}_pruned_w4a8_mixed`：**10.96 / 11.68 GiB**（Comfy-Org int8 pruned 19.53 GiB）。
- 50 块 / `[1025,8]` / AdaLN F16 / 200 层 W4A8 + 8 层 int8_tensorwise（token_refiner）。本机二进制含 `w4a8_to_i8`（K178）。详见 `768p-adapters.md`。

### K181 ★★★ FastH3-Omni（VSA）权重已在社区落地，但本机**仍无法加载**
- `Kijai/…:minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors`（**21.33 GiB**，1082 tensors）：50 块、`[1025,8]`、250 个 `comfy_quant` 全为 `{"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}`、**每块多一个 `attn.to_gate_compress.weight` I8 `[7168,5376]`** + `weight_scale`。
- **本机 `grep -c gate_compress` = 0**（全源码树），且 `untranslatable_tensor()`（`minimax-h3-diffusers-layout.cc:117`）对任何无 native 名的 tensor **整文件拒绝**。
- 这与上游 **issue #56**（`AugustRush/vpipe:omniref-vsa`，2026-10-22，**746 行 15 文件，GitHub 报 Able to merge，0 评论，已挂 34 天**）描述的失败**完全一致** —— 即「社区已有权重 + 现成 PR，上游未合」。
- ⇒ **VSA 是本机 H3 家族里唯一「权重齐、PR 齐、只差合入」的能力缺口**。与 P42（Tiny 16 宽）不同，这条不需要改 kernel，只需一张名字映射 + VSA 压缩逻辑。

### K182 ★ 官方仓 `MiniMaxAI/MiniMax-H3` 11-24 发生「误合 PR #112 → 12 分钟内 revert」
- `ebc970b115`（04:53:34，title 为阿拉伯语「换装…」）→ `12253298ad`（04:56:04，「Revert accidental merge of PR #112」，恢复 `.gitattributes` 并删掉误合图片）。
- 性质：**非技术变更**（误合社区图片 PR），权重与代码**零影响**；但这是官方仓首次出现「非维护者 PR 被误合并」。
- ⇒ 纪律：官方仓 `lastModified` 变动 ≠ 有新权重。判权重更新必须看 `tree` 的文件 sha/体积，不能只看 `lastModified`。

### K183 ★ Comfy-Org 官方 `model_patches/` 已收录 H3 ControlNet Union（本机仍 0 支持）
- `Comfy-Org/MiniMax-H3` 新增 `model_patches/minimax_h3_fun_controlnet_union{,_2.0}_pruned_{bf16,int8_convrot}`（8.38 / 4.53 / 4.22 / 2.30 GB）。
- 本机 `grep -ri controlnet repo/vpipe --include=*.cc` = **0**。（与既有 §1 ControlNet 结论一致，但此前只知道 alibaba-pai 原始仓，现在**Comfy-Org 官方镜像也收了** → 生态地位升级。）

### K184 ★ 社区侧「latent 空间修复」成为一条独立赛道（非官方，待复现）
- `BobMcoy/Minimax-H3-Temporal-Latent-Upscaler`（11-21 建，11-24 更新，v2.1）：不解码到像素，直接在**首轮 sampler 的 latent 输出**上按 17 帧块检测快运动，只对运动块做 2×/3× 时间膨胀后二次采样，再回收原帧数与 Pass-1 音频；另有 1.5× 空间超分。
- 与本机关系：**vpipe 无 latent 时间膨胀 stage**（`grep -ri latent.*upscal` 无命中）。这是「采样后再修」路线，与本机 RelayVSR/FlashVSR 的「像素域超分」是**不同层**。
- ⚠️ 二手来源 + 仅 ComfyUI 节点，**待复现**，不并入已验证能力。

### K189/K190 ★★★ 文本编码器替代赛道：ClipProj（sd.cpp 已实现，本机契约不符）

> 来源：`leejet/stable-diffusion.cpp` commit `5fa203c`（#2410，2026-11-25 16:29，4 文件 +166/−7）；`NicoLab28/ClipProj-MiniMax-H3` README + `mmh3-4b-ClipProj-v3.1` 权重头（HTTP Range）。

**1）它是什么**：一条**线性投影**把 **Qwen3-VL-4B/8B** 的 hidden 映射到 H3 DiT 要的 **5120 维**，替掉 **Qwen3-VL-32B**。显存 **15.7 GB → 4.5 GB**（4B int8）。不改变 DiT / VAE / 采样器。

**2）sd.cpp 侧实现要点**：`ClipProjConnector`（`input_dim 2560` → `output_dim 5120`）；张量 `W / mean_in / std_in / mean_out / std_out / sink_out`；**只读单层 tap 24**（对照：P-H3 读 `{13,19,25,31,37}` 五层，32B 读 50）；`sink_out` 替换首 token；**不支持 `-mlp` 残差变体**（`else if` 排在 P-H3 之后）。

**3）本机为什么装不上（四条全不满足）**：

| 契约项 | 本机要求 | ClipProj 实际 |
|---|---|---|
| 类名 | `_class_name == "PH3ImageTextConnector"`（`p-h3-image.h:46`） | 无 `config.json`，单文件 6 张量 |
| 位置 | `text_encoder/` 旁的 `text_connector/config.json`（`minimax-h3-text-encoder.cc:451`） | 无目录结构 |
| 张量名 | `proj.weight` / `input_mean` / `input_std` / `output_mean` / `output_std` / `sink_embedding`（`:668-690`） | `W / mean_in / std_in / mean_out / std_out / sink_out` |
| dtype/shape | 全 **F32**；`proj.weight` 为 `[taps*hidden × outw]` 展平 | 全 **F16**；`W [2560,5120]` 二维 |

- 结构上也不同：本机是「**N 个 tap 沿 hidden 维拼接 → 一次投影**」，ClipProj 是「**单 tap → 一次投影**」。不是改名能通的差异。
- 权重头实测：`tap 24`、`d_in 2560`、`d_out 5120`、`n_train_prompts 3331`、`n_train_tokens 8,471,247`、`cos_test 0.6874`、`r2_test 0.4755`。

**4）作者的自我限定（引用时必须带上）**：v3.1 图像分数与 v3 **完全重叠**，与 32B 也「无可分辨差异」——**这不等于相同**（余弦对可数属性是盲的）。32B 换 seed 就重读 75 音素里 5.8 个，v3.1 是 6.4–7.0 ⇒「换编码器 ≈ 重掷一次 seed」。多语种音素错误 −29%（西/法/德/意 −60~74%）。

**5）本机可走的路**：① 打包适配（改名 + 转 F32 + 造 `text_connector/config.json`，`hidden_state_indices: [24]`）——**但单 tap 与 N-tap 拼接是否语义等价，必须先读 `connector_config_` 与 `_proj` 的乘法规约**；② 等上游。收益：24 GB 机器腾 ~11 GB。**登记为 P46，未实施。**

### K192/K193 ★★ 社区 11-25 两条「新形态权重」：GGUF 家族（本机无路径）与 graft 调优 int8（键集全同）

- **`Infinity-io/MiniMax-H3-GGUF`**（11-25 02:21 建，83 dl）：`minimax_h3_{fl2va,ref2va}_pruned-{Q2_K 6.7 / Q3_K 8.7 / Q4_K 11.4 / Q5_0 13.9 / Q6_K 16.6 / Q8_0 21.4} GB` + `UD-Q2_K_XL 8.1 / UD-Q3_K_XL 9.6`。
  - **本机 H3 无 GGUF 加载路径**：`repo/vpipe/generative-models/minimax-h3/` 下 `gguf` 命中 **0**（全树 56 处 gguf 均在 LLM/图像侧）⇒ 记为缺口，不并入能力。
- **`yichengup/minimax_h3-tyc-zs05-ltxqnorm-int8-convrot`**（11-25 08:46，1,141 dl，**20.97 GB**，卡面自述「官方 pruned 的调优变体，**未训练**」）：
  - **与 Comfy-Org `ref2va_pruned_int8_convrot` 逐键相同**（932/932，`only in tyc = 0`、`only in base = 0`），`adaln_t_table [1025,8]` F32 → **本机 loader 不会拒**。
  - 但 metadata 声明 5 处 **graft**：`zspatial_graft`（Z-Image-Turbo 的 `q_norm`，块 30–49，dose 0.5）、`qnorm_graft`（LTX-2.5 `attn1.q_norm`，均值归一 ×1.9340，块 30–48，dose 1.0）、`qnorm_pin`（块 49 rms 5.0）、`adaln_splice none (fl2va throughout)`、`quant_format int8_tensorwise convrot groupsize 256`。
  - ⇒ **「同名不同构」第 5 次，且这次 shape 都一样**：判「能不能跑」要看键集+shape，判「是什么东西」**必须读 metadata 的 graft 声明**。画质差异不可归因到「模型名」。
  - 卡面自述的副作用（**待复现**）：「快动作更有爆发力」但「快速动作可能出现撕裂/拖影/物体被带走」。
