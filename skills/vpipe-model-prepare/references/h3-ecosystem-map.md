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

### K202/K203 ★★★ 换编码器的第二个社区方案：Qwen3.5-9B + 投影（带 MLP）+ rank32 LoRA —— 但成片 PSNR 只有 14.76 dB

- **仓**：`Alissonerdx/Qwen3.5-9B-Minimax-H3`（2026-11-25 18:54），配套节点 `alisson-anjos/ComfyUI-Qwen3.5-H3`（2026-11-24 建，13 star）。
- **投影（`minimax_h3_qwen3.5_9b_projection.safetensors`，header 1,304 B）**：**9 张量全 F32**
  - `W [4096,5120]`（4096 → 5120）
  - `mean_in/std_in [4096]`、`mean_out/std_out [5120]`
  - **`mlp.0.weight [8192,4096]` + `mlp.0.bias [8192]`、`mlp.2.weight [5120,8192]` + `mlp.2.bias [5120]`** ← **带 MLP 残差**
  - metadata：`tap 20`、`epochs_completed 3`、`n_train_prompts 1138`
- **LoRA（`minimax_h3_qwen3.5_9b_lora.safetensors`，header 65,056 B）**：**530 tensors / rank 32 / 34 个线性模块 / BF16**，全部 `model.language_model.layers.*` 前缀（含 `linear_attn.in_proj_{a,b,qkv,z}`、`o_proj`、`gate/up/down_proj`，另加 `model.visual.merger.linear_fc{1,2}`）。
- **作者自评指标（引用必带全表）**：

| 变体 | text cos | vision cos | overall | 视频 PSNR | FrameCorr |
|---|---|---|---|---|---|
| 仅投影（无 LoRA） | 0.8919 | 0.7873 | 0.8396 | **12.877 dB** | 0.4410 |
| 联合 Epoch1 | 0.9417 | 0.8801 | 0.9109 | — | — |
| 联合 Epoch2 | 0.9492 | 0.8867 | 0.9180 | — | — |
| **联合 Epoch3（当前）** | **0.9507** | **0.8879** | **0.9193** | **14.764 dB** | **0.6310** |

- 差例：case04（4 参考）PSNR **11.104 dB** / corr 0.4808；case03（3 参考）14.743 / 0.3852。
- **⇒ 三条结论**：
  1. **hidden-state 余弦 0.95 只换来成片的 14.8 dB** —— 「编码器对齐 ≠ 成片对齐」。与本机「纹理量 + SSIM + 编造量」三件套同方向：**中间表示不是验收指标**。
  2. **比 ClipProj 离本机更远**：ClipProj 是「**无 mlp**」变体（sd.cpp 的 `ClipProjConnector` 明确写「不支持 `-mlp` 残差变体」），Qwen3.5 是「**带 mlp**」。
  3. 两个方案都要求「**单 tap + 一次性投影**」，本机是「**N 个 tap 沿 hidden 维拼接 → 一次投影**」（K190）——tap 数不同，不是改名能通。
- **状态**：**待复现**。登记 P46，**优先级维持中、期望下调**。

## 2026-11-26 追加（第 32 轮 · 「时调制剪枝」成独立工艺线 + 本机第 5 类不可读形态 + ref LoRA 轻量路线）

### K210 ★★★ WaveCut 风格「时调制剪枝」：把 AdaLN 换成 one-hot 时编码 + 投影

- **方法源**：`iamwavecut/MiniMax-H3-Image-Pruned`（GitHub，2026-11-10，0 star，描述「MiniMax-H3-Image without unused weights（135 → 94 GB, bit-identical images）」）。做法：在**固定采样步**上预先算出时调制，用 **one-hot 时编码器 + 投影**替换整张时调制网络。
- **ComfyUI 参考图路径版**：`Jianqiao1/MiniMax-H3-Image-Lossless-Pruned-ComfyUI`（2026-11-25 18:40）。
  - bf16：`minimax_h3_image_wavecut_style_pruned_reference_bf16.safetensors` **40,234,634,888 B**（66.3 → 40.2 GB）。
  - int8 ConvRot：`…_reference_int8_convrot.safetensors` **20,979,299,938 B**（→ 21.0 GB）。
  - 作者自评（ComfyUI 0.45.0 / RTX 5090 / 4096² / Euler CFG1 / **六步**）：bf16 **5/5 逐像素相同（MAE 0.0000 / PSNR ∞）**；int8 **MAE 9.1674 / PSNR 21.833 dB / 0/5 相同**。对照 Comfy-Org：bf16 22.703 dB、int8 22.178 dB。
  - **关键限制（作者自述）**：只在**参考图路径**上像素等价（含纯黑参考图）；纯 T2I 路径**不等价**，因为原模型在有/无参考时舍入不同。**所有比较用 ComfyUI，不用 diffusers**。
  - **定量风格 sigma 表**：`1.0, 0.9675236940383911, 0.8875485062599182, 0.75, 0.5327739119529724, 0.23200887441635132, 0.0`（写进 `ManualSigmas`）。
- **⚠️ 待复现**（社区二手 + 作者自测，未见第三方复现）。

### K211 ★★★ 本机第 5 类「看着像 H3、打不开」：宽 8 AdaLN + 无前缀 + 无曲线表

| | bf16 件 | int8 件 |
|---|---|---|
| tensors / 字节 | 531 / 40,234,634,888 | 981 / 20,979,299,938 |
| 前缀 | **无** `model.diffusion_model.` | **无** |
| `adaln_t_table` | **无** | **无** |
| AdaLN 投影 | `blocks.N.adaln_proj.linear.weight BF16 [96768, 8]` | 同（BF16） |
| `time_embedder` | **极窄**：`proj_in [16,256]`、`proj_out [8,16]` | 同 |
| 额外 | — | `blocks.N.attn.comfy_attention.config`（`[{"attention":"comfy_kitchen_int8"}]`，本机 grep = 0） |

- **本机判据链**（`metal-minimax-h3-transformer.cc:640-661`）：
  - `comfy_saved` = `is_comfy_saved_dit_file()`（要求有 `model.diffusion_model.` / `diffusion_model.` 全前缀）**或** （`has("adaln_t_table")` 且 `has("blocks.0.attn.qkv_proj.weight")`）。
  - 本件三条都不满足 → 直接 fail **「is neither a Comfy-Org H3 component, an H3 DiT ComfyUI saved, nor one in the diffusers naming」**。
- **第 5 类的命名**：这类是「**one-hot 剪枝形态**」——宽 8 的 AdaLN + 极窄 `time_embedder` + 无曲线表，本机**没有任何识别分支**（既不是 pruned 曲线形态，也不是 full-model 形态）。
- **为何不是「加个 adaln_t_table.bin 就能读」**：本机 pruned 分支要求 `curve_grid >= 2` 且 `time_dim == 8`（`:831`），而 `curve_grid` 只能来自 `adaln_t_table`；本件的 `time_embedder.proj_out [8,16]` 说明它的「8」是**输出维度**不是曲线网格。语义不同，**不能靠补一个旁挂表绕过**。

### K216 ★★ 社区另辟的 FL2VA→Ref2VA 轻量路线：「ref LoRA」

- `Kijai/MiniMax-H3-experimental` README 原文：**「ref lora is the difference between fl2va and ref2va, completely experimental, I don't even know if it has a use case at this point.」**
- `wip/` 下另有 `minimax_h3_ref2va_pruned_w6a8_g32.safetensor`（指向 `Comfy-Org/comfy-kitchen` PR **#191**）。
- **与本机现象的关系**：本机两个 partition 的 transformer config **字节相同**、行为不同（见 `metal-minimax-h3-transformer.cc:434-446` 的注释）。社区用「就差一个 LoRA」解释同一现象。**待复现**——若成立，则 FL2VA 单份下载可覆盖两任务，能省一半磁盘。

### Kajai `wip/` 与根目录的量化 VAE 全谱（K217 的来源）

| 文件 | 字节 | 说明 |
|---|---:|---|
| `minimax_h3_lightvae_lite_encoder_fp16.safetensors` | 203,172,976 | lite VAE 的编码器（fp16） |
| `minimax_h3_lightvae_lite_vae_int8_convrot.safetensors` | 1,036,943,392 | **lite VAE 解码器 int8**（最小候选） |
| `minimax_h3_lynnreal_light_vae_int8_convrot.safetensors` | 2,137,493,384 | LynnReal light VAE（来源 `stdstu123/LynnReal-Onmi-light-vae`，自报 1.3× faster） |
| `minimax_h3_mt_video_vae_int8_convrot.safetensors` | 2,811,065,896 | mt video VAE |
| `minimax_h3_video_vae_int8_convrot.safetensors` | 3,171,670,912 | 官方 VAE 的 int8 版 |

- README：「int8_convrot VAE needs ComfyUI 0.36.0 for maximum speed benefit / It speeds up VAE decode times by ~2x」。
- **本机不认**（K217）：VAE 走 `.scales`/`.biases` 仿射量化，不是 `.weight_scale`/`comfy_quant`。

### 上游与生态快照（第 8 日静默，逐日复查）

- vpipe：HEAD `a6a1f53`（11-23 09:54）、release **v0.1.110**（11-01，落后 **26 天**）、issue 14 全开、PR 0、273 star / 27 fork。
- sd.cpp：`52491bd` #2423 DGL 内联媒体预览 → H3 相关仍只有 11-25 `5fa203c` ClipProj(no mlp)。
- ComfyUI：`f40a4fbb` frontend 1.59.15 / `a2103ae6` Meshy / `b27006af` Recraft，无 H3。
- LightX2V：`83a424a`（README 文案）。
- 社区新仓：`SOLRICKS/3D-Animation-Style-MiniMax-H3`（rank16 step1250 LoRA + 5 份 V3 workflow）、`Coffmeteor/MiniMaxH3-Realism-Turbo-Remix`（908 dl）、`pmczip/MiniMaxH3_RefMod`（1,634 dl）。

## 第 33 轮增补（2026-11-27 00:30）—— 生态快照第 9 日 + 三条新支线

- **上游仍静默第 9 日**：HEAD `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`pushed_at 11-23T11:20:51Z`）、release **v0.1.110**（11-01，落后 **26 天**）、issue **14 全开**（#59/#58/#56/#55 仍 0 评论）、**PR 0**、**274 star（+1）/ 27 fork / 36,920 KB**。
- **LightX2V 单日 3 条但全非 H3**：`1e912006` LongCat-Video-Avatar 1.6（#1762）、`d9b1099d` Seed-VC 原生音频转换（#1758）、`239537fc` YuE2 音频生成（#1755）⇒ H3 主线仍是 `7fc25cd`（#1730，11-25）。
- **sd.cpp 单日 5 条，H3 零**：`e637c7bc` server Web UI（#2437）、**`ea3f6ec7` LTX INT8 ConvRot 载入修复（#2436）**、**`6b51a955` W4A8 复用 INT8 GEMM（#2435）**——两条量化基础设施改动**只服务 LTX/通用路径**，H3 相关仍停在 11-25 `5fa203c` ClipProj(no mlp)。
  - ⚠️ 注意别误读：`#2436 / #2435` 的「INT8 ConvRot / W4A8」**不是** H3 支持，别当成 H3 量化进度。
- **ComfyUI 零 H3**：`8b0f1071` VBAR pins（#17837）、`4a4b3409` Seed/OpenRouter 节点迁移、`ef507153` TextGenerateV2 流式预览。
- **ModelScope**：`lightx2v/Minimax-h3-Turbo` 仍 **31 项**（与上轮同）——本轮镜像直连 `huggingface.co` 全域不可达（见下「踩坑」），ModelScope 侧未再逐项复核。
- **新支线 ①「预烘 AdaLN 表」第三家**：`OpenVDN/vdn-minimax-h3-edge`（`freevideo-fp8-variants-v1`，535 payload 全校验），`adaln-tables-v2-*` 每文件 8 个 `step_N BF16 [6|9, 32256]`。与 K210（宽 8 one-hot）、K205（`adaln_basis [8,2688]`）并列，**三种互不兼容布局**；本机一种都不认。
- **新支线 ②「三件套交付」**：`vantagewithai/MiniMax-H3-comfyUI-GGUF`（11,153 dl / 28 like）= 22 个 GGUF（fl2va/ref2va × 11 档）+ 4 个 8 步 acc LoRA + 7 份 workflow。社区交付单位从「一个权重」变成「权重+LoRA+workflow+注意力补丁」。
- **新支线 ③「像素头」**：`pocis/MiniMax-H3-Video-PixelHead`（92 tensors / 95.9 MB F32，`eval_psnr_db 31.97`，作者自标 `experimental_preview_v0.2.0_not_recommended_for_production`）——DWD 路线的首个推理侧实现，本机无通路。
- **编辑型 LoRA 扩支**：`VoidEclipseAI/MiniMax-H3-ReFrame-VideoInpainting-LoRA`（596 MB，画布内重绘）、`Uhvg856/MiniMax-H3-Person-Remover-LoRA`、`Uhvg856/MiniMax-H3-Character-Swap-LoRA`、`ausboss/MiniMax-H3-Image-Outpaint-LoRA`（13 like）⇒ 「人物/物体级编辑」已成独立品类。
- **检索通路退化（新）**：本轮 `huggingface.co` **全域超时**（DNS 解析到 157.240.13.8，TCP 无响应，`api/models`、`resolve` 均 `000` 25 s 超时）；`hf-mirror.com` 的 **`resolve` + Range 完全可用**（返回 206 与正确首 8 字节）。⇒ 读头可全部走镜像，不再依赖直连。

## 第 34 轮增补（2026-11-27 02:30）—— 生态快照第 10 日 + sd.cpp 换编码器双向推进

### 上游与三条相邻线（逐日复查，本轮为**有增量**的一次）

- **vpipe 上游：第 10 日静默（零增量）**。HEAD 仍 `a6a1f53`（`author.date 2026-11-23T09:54:27Z`、`committer.date 11-23T11:14:45Z`、`pushed_at 11-23T11:20:51Z`）；
  release 最新仍 **v0.1.110**（11-01）⇒ **落后 26 天**；issue **14 全开**（#59/#58/#56/#55 的 `updated_at == created_at`、0 评论）；
  **PR total_count = 0**；**274 star（与上轮同）/ 27 fork / 36,920 KB**。
- ★★ **sd.cpp 出现本轮唯一的实质增量（换编码器线双向推进）**：
  - **`439e77a5` PR #2424「support `-mlp` variants of ClipProj-MiniMax-H3」已于 2026-11-26T13:12:17Z 合入**——补上了 #2410（11-24，no-mlp）的缺口，
    现在 `mmh3-8b-ClipProj` / `-mlp` / `v3.1` / `v3.1-mlp` **四种 connector 全支持**（含 linear+mlp refiner 与纯 mlp）。
    ⇒ **K190/K202 里「sd.cpp 也不支持带 MLP 残差变体」这条前提被上游推翻**；本机 `minimax-h3-text-encoder.cc` 的 connector 契约仍是 6 张量「无 MLP」式（`:655-690`），
    因此 **P46 的对手（sd.cpp）已具备本机没有的能力**，P46 从「跟跑」变成「落后一个变体」。
  - **`2414`（open，未合）「latent continuation」**：`--save-latent` / `--continue-latent` / `--pin-frames`，从上一段**尾 latent** 续接而非尾**像素**帧
    （作者说明：像素帧续接有构图漂移、且音轨每段重启）。本机全树 `save-latent|continue-latent|pin-frames` grep = **0** ⇒ 长视频拼接是**新增缺口**（非 H3 独有，但直接影响 >10 s 交付）。
  - 其余 4 条与前一轮同源、无 H3：`e637c7bc` server Web UI（#2437）、`ea3f6ec7` LTX INT8 ConvRot（#2436）、`6b51a955` W4A8 复用 INT8 GEMM（#2435）、`00a944fd` lingbot rms_affine 融合（#2422）。
- **LightX2V 单日 4 条，仍全非 H3**：`c1e33b28` intel xpu B70（#1763）、`1e912006` LongCat-Video-Avatar 1.6（#1762）、`d9b1099d` Seed-VC（#1758）、`239537fc` YuE2（#1755）。
  ⚠️ 组织名是 **`ModelTC/LightX2V`**；`api.github.com/repos/lightx2v/LightX2V` 返回 **404**（不是改名跳转，别当仓没了）。
- **ComfyUI 零 H3**：`8b0f1071` VBAR pins（#17837）、`4a4b3409` Seed/OpenRouter → Comfy Router（#17960）、`ef507153` TextGenerateV2 流式预览（#17996）。
- **ModelScope `lightx2v/Minimax-h3-Turbo` 仍 31 项**（README 于 2026-11-24 14:36 UTC 改过文案，权重未动）；
  **新增复核 `lightx2v/Minimax-H3-Turbo-Fusion` 共 48 项**（2026-11-24 18:49 UTC 一次性上传）：`pruned/` 6 个 safetensors + 非 pruned 6 个 + `assets/`（case1/2 图 + 对比 mp4）+ `configuration.json`。
- **Comfy-Org/MiniMax-H3**：`lastModified 2026-11-15`、**33,258,212 dl / 2,853 like**（权重仓本身已 12 天未动）。

### 本轮社区面（11-26 单日，与第 33 轮**去重后**的新仓）

> 第 33 轮已记的 `vantagewithai` / `javawock7618` / `pocis` / `OpenVDN` / `MATLOWAI` / `VoidEclipseAI` / `Uhvg856` / `ausboss` / `aevionlabs` / `Infinity-io` / `klassas` / `Jianqiao1` / `Alissonerdx/Qwen3.5-9B` 不再重复。

- `Maximilian228/MiniMax-H3-pi-H3-NVFP4-GPTQ`（**新品类：`pi-H3` 的 NVFP4/GPTQ 落地方案**，含 DiT + DWD 头 + 32B 文本编码器三件，面向 Blackwell）。
- `Alissonerdx/TE-PK-Minimax-H3`（**新品类：零梯度闭式投影换编码器**，8 个 key、20–105 MB；同作者 `ComfyUI-H3-Text-Encoders`）。
- `loom-draft/pytraveler-MiniMax-H3-Prompt-Rewriter-Qwen3.8-27B-{FL2VA,Ref2VA}-loom`（**提示词改写器作为独立仓**、F2VA/Ref2VA 双版本）。
- `ibyteohdear/MiniMax-H3-Pruned-{DMD-FL2VA-Turbo,LightX8-hybrid}-Fused` 更新（497/502 dl；仍是 4 分片 diffusers 目录 + `time_embedder.table`）。
- `haubnh/FrameRush-Minimax-H3`、`Jim507735/Minimax-H3-LongVideo`（均 3 文件、**无 README**）、`nnndite/minimaxh3image`、`mimba/minimax-h3`、
  `bp-5193/MiniMax-H3`、`PYTHAI/MiniMax-H3-fork`、`klassas/minimax-h3-loras`、`RunningHubAI/rh-minimax-h3-image-123-1500-lora`（7 个**空壳/占位仓**，0 dl）。
- ⇒ 与第 33 轮相比，重心从「编辑型 LoRA」转向 **「pi-H3 的量化落地」+「换编码器」** 两条工程线；空壳仓比例明显上升（11-26 单日 30 仓中 ~8 个无内容）。

### 检索通路（本轮复核，含一条新坑）

- `huggingface.co` 仍**全域不可达**：`api/models/Comfy-Org/MiniMax-H3` 与 `api/models?search=` 均 `000`（12.1–12.2 s 恰好等于 `--max-time`）。
- `hf-mirror.com` 同路径 **200 / 0.76 s**；`resolve/main/<file>` + `-r 0-7` 稳定 **206** 且首字节正确。⇒ **镜像优先**的规则本轮继续成立（第 3 日）。
- **新坑：镜像上「不存在的文件」返回 404，但存在性判断不能只看 `resolve`** —— 本轮 `Jim507735/Minimax-H3-LongVideo` 的 `README.md` 与随机文件名**都返回 404**，
  而 `api/models/<id>` 报 3 个 siblings ⇒ 该仓只有 3 个非 README 文件。**判「仓空不空」要看 `api/models` 的 siblings，不要用 `resolve README` 的结果反推**。
- **新坑：`api/models/<id>` 的 `siblings[].size` 依然全 `None`**（第 3 日复现）；体积只能 `curl -sIL | grep -i content-length`（本轮 6 个文件全用此法）。

## 第 35 轮增补（2026-11-27 04:30）—— 生态快照第 11 日 + 「后处理」与「调参 graft」两条线的新形态

### 上游与相邻线（逐日复查）

- **vpipe 静默第 11 日**：HEAD 仍 `a6a1f53`（`author.date 2026-11-23T09:54:27Z`），release 仍 **v0.1.110（2026-11-01）→ 落后 26 天**，
  issue **14 全开**（#59/#58/#56/#55 均 `updated_at == created_at`、0 评论），**PR total_count = 0**，**274 star / 27 fork / 36,920 KB**（与第 34 轮逐位相同）。
- **LightX2V（`ModelTC/LightX2V`）5 条全非 H3**：`c1e33b28`（11-26 17:10）Intel XPU B70 修复 #1763、`1e912006` LongCat-Video-Avatar 1.6 #1762、
  `d9b1099d` Seed-VC #1758、`239537fc` YuE2 #1755、`83a424ac` README 文案 #1757。H3 侧仍停在 **11-25 06:41 的 `7fc25cdc`（#1730 蒸馏 best practices）**。
- **sd.cpp 6 条，H3 只前进半步**：`439e77a5`（11-26 13:12）#2424 `-mlp` 变体（第 34 轮已记）；
  新 **`e637c7bc` 13:48 #2422 lingbot 视频 rms_affine 调制融合**、`fce8619b` 13:36 #2434 FLUX.3 fused QKV、
  `6b51a955` 15:00 #2435 W4A8 复用 INT8 GEMM、`ea3f6ec7` 15:50 #2436 LTX INT8 ConvRot 载入修复、`e637c7bc/e637`… 其余为 server/WebUI。
  ⇒ **#2435/#2436 仍只服务 LTX 与通用路径，不是 H3 量化进度**（K229 的提醒继续成立）。
  另 **PR #2357（open，未合，11-15 起无更新）「MiniMax-H3 2D-conv latent upscaler」**：新增 `minimax_h3_latent_upscaler_2d_conv_v1`（2D conv + 两个共享时间块、无 attention/SE/大核），
  与已合的 **#2249（3D-conv，2026-11-04 关闭合入）** 并列 ⇒ sd.cpp 也只支持 **3D-conv 这一支**，与本机同。
- **ComfyUI**：`2b33af49`（11-26 19:08）#18015 Pruna 定价、`8b0f1071` #17837 VBAR、`4a4b3409` #17960 Seed/OpenRouter、`ef507153` #17996 —— **4 条全无 H3**。
- **ModelScope**：`lightx2v/Minimax-h3-Turbo` 仍 **31 项**（README 11-24 改文案，权重未动）；`Minimax-H3-Turbo-Fusion` **15 项顶层 + `assets/` + `pruned/`**，
  `pruned/` 4 个 safetensors（4/8 步 × lite_r32/全量）**sha 两两不同**（K240 结案，见 768p-adapters 第 35 轮第 6 条）。

### 本轮社区面（11-26 单日，与第 33/34 轮**去重后**）

- 新品类：**latent upscaler v2 重训族**（`George0667/MiniMax_Temporal_Upscaler`，v2 + v2_temporal，478 dl）、
  **跨模型 q_norm graft**（`yichengup/...ltxqnorm-int8-convrot`，1,141 dl / 8 like，20.97 GB）、
  **AMD Loom 打包**（`loom-draft/pytraveler-...-Prompt-Rewriter-Qwen3.8-27B-{FL2VA,Ref2VA}-loom`，`.loom` 程序 + GGUF 卡片，**不是 H3 权重**，只是提示词改写器的部署包）。
- **gated 仓首次出现**：`linkqpsfa/minimax-h3-{i2v,unc-i2v}-weights`（11-26）siblings 可见但 `resolve` 全 403 `GatedRepo` ⇒ 社区开始用「限制访问」分发 H3 权重，检索时不可按体积判断内容。
- 空壳/占位仓比例未见改善（`mimba/minimax-h3`、`nnndite/minimaxh3image`、`PYTHAI/MiniMax-H3-fork` 等仍 0 dl、无权重）。

### 检索通路（第 4 日复核）

- `huggingface.co` 直连**仍未恢复**（本轮未再试，沿用镜像；`api/models` / `resolve` 全走 `hf-mirror.com`，均 200）。
- `hf-mirror.com` 两个新坑：**① 403 GatedRepo 的 `content-length`（183/191）是错误体长度，看着像文件体积**；
  **② `curl -sIL` 不带 `-L` 时 302 目标不展开，`content-length` 直接给 183**——必须 `-sIL`（大 I 大写）才跟跳转，小写 `-i` + `-s` + `-L` 亦可。
- `api/models/<id>` 的 `siblings[].size` **第 4 日仍全 `None`**；体积一律 `curl -sIL | grep -i content-length`。
- ModelScope 的 `repo/files` 顶层会返回 `Type: tree` 的目录项且**不带子项列表**；取子目录要再打一次 `Root=<dir>`，本轮 `pruned/fl2v`、`pruned/ref2v` 均不存在（目录名是 `pruned/` 下平铺）。

## 第 36 轮增补（2026-11-27 06:30）

### 上游（零增量，第 12 日）
- `tgo-app-dev/vpipe` HEAD `a6a1f53`（author 11-23T09:54:27Z / pushed 11-23T11:20:51Z），**274 star 连续第 3 日不动**、27 fork、36,920 KB、issue 14 全开 0 评论、PR 0。
- release **v0.1.110（11-01）** 落后 main **26 天**。引用上游能力必须写 commit。
- sd.cpp 11-26 合入两条与本机相关：**#2435**（W4A8 改走 INT8 GEMM，删独立 matmul，+692/−1496/29 文件）、**#2436**（`convrot_groupsize` 缺省 **256**，与 ComfyUI 对齐）。本机 `Declared` 的默认也是 256 ⇒ **三方一致**（新少见的无分歧项）。

### 新生态线（第 4 次重心迁移）
| 线 | 代表 | 形态 |
|---|---|---|
| 编辑型 LoRA | `Uhvg856/*`、`ausboss/*` | 11-26 前的主流 |
| pi-H3 量化 + 换编码器 | `Maximilian228/*NVFP4-GPTQ`、`Alissonerdx/TE-PK` | 第 33/34 轮 |
| 后处理重训 + 跨模型 graft | `George0667/*Temporal_Upscaler`、`yichengup/*ltxqnorm` | 第 35 轮 |
| **货架仓 + 整模型镜像** | `Enigma4869/h3`（**422 个 .safetensors**，三层目录）、`vml12/Pika-H3-Flex`（96 文件全量镜像 66.28 GB 索引） | **第 36 轮** |

- 空壳继续增：`RunningHubAI/rh-crown-…`（1 文件无权重）、`Lora-Daddy/h3-writer-hauhau`（4 文件无权重）。
- `huggingface12341/zsf-h30` 有 4 分片 `model-0000x-of-00004.safetensors`（疑似整模型再分发，未读头）。

### 官方仓
- `MiniMaxAI/MiniMax-H3`：lastModified **2026-11-24T04:56Z**、**6,012,871 dl / 7,411 like**。
- `lightx2v/Minimax-h3-Turbo` 31 项未动；`Minimax-H3-Turbo-Fusion` 权重 11-24 18:50Z 未动；⚠️ **文件数口径**：`Recursive=false` 15 项 / `true` 48 项（K264）。

### 检索通路
- 镜像优先第 4 日成立；`huggingface.co` 未试（已知 `000`）。
- **`x-linked-size`** 是 302 上唯一可信体积字段（本轮 4 件一次拿全）。
- ComfyUI 的 `search/issues` 本轮返回体缺 `total_count` 且无 `items` ⇒ **接口抖动 ≠ 零结果**（判零须 HTTP200 + 空数组）。

---

## 6. HyperFlow H3 Flash：从「另一族」到 upstream 一等公民（2026-11-28 · 第 37 轮 · K266–K269）

> 来源：上游 `docs/MINIMAX-H3.md`（commit `41a694a2`，271,340 B）新增 120 行专章、`stages/model-catalog.cc` 双条目、
> `tests/unit-tests/hyperflow-h3-flash.cc`（1,093 行）、HF 镜像零下载读头。

**定位变更**：第 1 轮（K12）与第 20 轮（K116）都把它记为「社区另一族、与 vpipe 无关」。**文档层已错**——它是官方文档的一等章节，走 `generate-video` 的 `dit_dir`（不是 LoRA）。但**本机层仍不支持**（见下）。

### 三个文件自述的架构变更

| 变更 | 内容 | 本机（`d72c22f`）状态 |
|---|---|---|
| **块删除 + 重编号** | FL2VA 删 **6 / 21 / 22** ⇒ **47 块**；Ref2VA 删 **9** ⇒ **49 块**。文件从 0 重编号，原编号只存 `__metadata__.hyperflow.dropped_blocks` | `dropped_blocks` grep = **0** |
| **低秩投影对** | 部分投影存成 `up @ down`，rank **pad 到 64**；FL2VA **102 对 / 18 块 / 最宽 3200 / 合计 2.667 GB**；Ref2VA **114 对 / 19 块** | `.up.weight` 只在 vdn-branch 与 quantizer 命中，**DiT 无低秩对通路** |
| **双时间内建** | `endpoint_time_embedder` 是模型的一部分（与 `time_embedder` 形状同构，各 4 张 F32），每次前向给 `(t, r)`；**AdaLN 读 16 维**（官方 pruned 是 8 维）；**无单时间模式** | `endpoint_time_embedder` 只作为 **HyperFlow LoRA 的因子名**出现（`metal-minimax-h3-transformer.cc:5198/5225`），**不是模型自带张量** |

### `curve_dit`：官方化的「跨模型时间调制嫁接」

pi-H3 训在 pruned 形态的时间调制上，Flash 没有。做法：

```json
"dit_dir":  "VideoRebirthAI/hyperflow-h3-flash-fl2va-int8-convrot",
"curve_dit": "Comfy-Org/MiniMax-H3-FL2VA-pruned-int8-convrot"
```

⇒ Flash 的块跑 **stock pruned 曲线 + 其 AdaLN（单时间）**，pi-H3 的 LoRA / 全张量覆写按**原编号**绑定（落在 6/21/22 的跳过并报），`final_layer` / DWD 头 / 4 步采样器照旧。只读 stock 文件的曲线表与 AdaLN（约 **0.15 GB**）。此路径下 **flow-map 适配器被拒、VDN 分支被拒**。

M5 Max 832×480×73 + Sol：**23.4 s / 22.9 GB** vs pi-H3 直接跑 pruned DiT **29.7 s / 27.4 GB**。

> **与 K247 民间 graft 的区别**（重要）：K247 是手工换 `attn.q_norm` 增益（跨 LTX-2.5 / Z-Image，**行为未知**）；`curve_dit` 只换**时间调制的数据来源**（曲线表 + AdaLN 复用），**不改任何权重语义**。P56 的 QC 判据要按这两类分开写。

### 本机判定（K277）

`libvpipe.0.dylib`（`0.1 (9db5dd7*0)`）strings：`hyperflow` **0** / `curve_dit` **0** / `endpoint_time_embedder` **0** / `tensor-parallel-flash` **0**。

⚠️ **但 `pi-H3` strings 也是 0，而本机确实支持 pi-H3** ⇒ **`strings` 只证有、不证无**。判「本机不支持 Flash」的真依据是**源码树三结构键 grep 全 0** + 本地树停在 `d72c22f`（11-20，落后 HEAD 87 个 commit）。

### 派生仓矩阵（2026-11-27 快照）

| 仓 | dl | 说明 |
|---|---|---|
| `VideoRebirthAI/hyperflow-h3-flash`（官方） | 1,019,175 | 8 个目录：`fl2va/ref2va` × `bf16 / gguf / int8_convrot / int8_convrot_comfyui`；**权重停在 2026-11-14** |
| `BennyDaBall/HyperFlow-H3-Flash-INT8-ComfyUI` | 126,064 | 单文件 int8 |
| `BennyDaBall/HyperFlow-H3-Flash-NVFP4-ComfyUI` | 6,435 | NVFP4 |
| `hoidhxd/HyperFlow-H3-Flash-INT8-ComfyUI-Hybrid` | 244 | **`b25-49` 命名 ⇒ 只量化后 24 块，前半 bf16** |
| `moonbox-dev/…-GGUF` / `…-ref2va-GGUF` | 3,248 / 1,663 | GGUF |
| `hancheng-ai/…-MLX-Serve-{8bit,4bit}` × 2 partition | 286 / 275 / 207 / 201 | MLX |

---

### 2026-11-28（第 38 轮）修正与新形态

**⚠️ 体积修正（向后覆盖）**：

| 文件 | 本文档旧值 | **现测（`x-linked-size`）** |
|---|---|---|
| `Comfy-Org/MiniMax-H3:vae/minimax_h3_video_vae_int8_convrot` | 3,171,670,912 | **2,811,065,184** |
| `Comfy-Org/MiniMax-H3:vae/minimax_h3_video_vae_fp16` | — | **5,207,808,496** |
| `Comfy-Org/MiniMax-H3:vae/minimax_h3_sol_vae_fp16` | — | **3,596,335,728** |
| `Comfy-Org/MiniMax-H3:vae/minimax_h3_sol_vae_int8_convrot` | — | **1,988,306,504** |

理由：该文件提交史停在 10-29 之前（`4b53a35191` 仅改 README/模板）⇒ 文件未换过；旧值与社区 `mt_video`（2,811,065,896 B）仅差 712 B ⇒ 旧记录为串位。**int8 相对 fp16 = −46%**（旧口径 −39%）。

**新形态两枚**：

| 仓 | 文件数 | 说明 |
|---|---|---|
| `MistyViolet/MiniMax_H3` | 66 | **整机套装**：`LLM/`（Qwen3.8-27B `UD-IQ3_XXS`/`UD-Q8_K_XL` GGUF + `mmproj-BF16`）、DiT ×2（官方 int8 + K282 hybrid）、text_encoders ×3、vae ×3、`latent_upscale_models/h3_upscaler_lms_v0.1`、`loras/` 11 + `loras/minimaxh3/` 12、`semantic_bridge/t8_compat/`、中文目录 `自動續接長視頻音頻驅動數字人/models/`（12 个 DiT 变体）。**493 dl / 0 like** |
| `AI-KSK/minimax-h3-vbvr-v2-video-reasoning` | 7 | **无权重评测仓**：`workflow.json`(19 节点/22 链) + `CHECKSUMS.txt` + 中英 README，9 场景 18 片段、4 维判据，外链 B 站/YouTube/RunningHub |

**空壳族**：`RunningHubAI/rh-*` 3/3 只有 `.gitattributes`。


---

## AdaLN 的三种形态（2026-11-28 第 39 轮，K294）

| # | 形态 | `time_embedder.proj_out` | 时间表 | 例 |
|---|---|---|---|---|
| 1 | 官方 pruned | **无 t-MLP** | `adaln_t_table [1025,8]` | `Comfy-Org/…pruned_int8_convrot` |
| 2 | 折叠进 t-MLP 输出（WaveCut） | `[8,16]` | 无 | K211 的 WaveCut 件 |
| 3 | **预烘 t-MLP + 8 宽折叠基（QuantFunc / SVDQuant）** | `[2688,5376]` | 无（但有 `adaln_fold_basis [8,2688]`） | `QuantFunc/…int4_r128` |

⇒ 判「像不像 pruned」**不能只看 `adaln_proj.linear.weight` 的宽度**（三者都是 8），要看 `time_embedder.proj_out` 的 **out 维**（无 / 8 / 16 / 2688）。
本机 `comfy_saved` 判据硬性要 `adaln_t_table`（`metal-minimax-h3-transformer.cc:648-652`）⇒ 形态 3 **落在缝里**（fail「is neither a Comfy-Org H3 component…」）。

## 分发形态第 8 种：整仓打包 diffusers 源码（K298）

`ibyteohdear/MiniMax-H3-Pruned-{LightX8-hybrid,DMD-FL2VA-Turbo}-Fused` 各 **1423 文件**，其中 **1412 个在 `diffusers/` 下**
（`diffusers/__init__.py`、`diffusers/commands/*.py`、`diffusers/__pycache__/*.cpython-311.pyc`），
真权重只有根目录 **4 个 `diffusion_pytorch_model-0000{1..4}-of-00004.safetensors`**。

⇒ 与「`siblings ≤ 2` 先当空壳」（K288）互补：**上界也要看**，上千的多半打包了源码/缓存。
统计「有效仓」时先看 `topdir` 分布，`diffusers/` 下 `.py`/`.pyc` 一律不计。

## 换编码器：TE-PK `pk_lora` 方言（K299 补）

`Alissonerdx/TE-PK-Minimax-H3:gemma4/minimax_h3_32b_pk_lora_gemma4_e4b.safetensors` = **520 tensors 全 F16**：
非 `te_lora` 只有 4 个（`scale F32 [1]` / `R F16 [15360,5120]` / `donor_mean [15360]` / `target_mean [5120]`），
余 516 个是 `te_lora.layers.*.{self_attn.{q,k,v,o}_proj, mlp.{gate,up,down}_proj}.lora_{A,B}`，rank 32。

**`grep sink` = 0** ⇒ README 里的 `inject_token0_sink = True` 是**运行时注入 Qwen3-VL-32B 的 20 KB Token-0 向量**（`<0.01 ms`，零训练），
**不是**权重里的 `sink_embedding`。⇒ 判「能否塞进本机 connector」**不能靠 README 功能名对齐，要 dump 张量表**（本机要 6 张量含 `sink_embedding`，K237）。

## 官方 H3-Image 的三件套（2026-11-28 第 40 轮，K304）

`MiniMaxAI/MiniMax-H3-Image` = **100 文件 / 1,084,642 dl / 2,629 like**（`created 11-03`，`lastModified 2026-11-16T10:00Z`）。

| 文件 | 体积 / 结构 | 含义 |
|---|---|---|
| `pdd_fused_heads.safetensors` | **12,388,808 B / 2 tensors 全 F32**：`video_out.weight [6, 96, 5376]` + `video_out.bias [6, 96]` | **6 个 step 专用输出头**（96 = patch `1×2×2` × latents 24）；K94 的 `step_head_of` 从机制变实体 |
| `pdd_config.json` | `num_inference_steps 6`、`sigmas [1.0, 0.9675237, 0.8875485, 0.75, 0.5327739, 0.2320089, 0.0]` | 六步**显式** sigmas（不是 sgm_uniform 网格） |
| `transformer/` | **66,279,032,256 B / 12 分片 / 531 键** | DiT 本体；**同一份权重在 `transformer_diffusers/` 再存一遍**（14 文件） |
| `transformer/config.json` | `_class_name = MiniMaxH3DiTModel`（**不是** `MiniMaxH3Transformer3DModel`）、`audio_enabled false`、`adaln_out_features 96768`、`final_adaln_out_features 10752` | ⚠️ **同一模型两种 `_class_name` 拼写**，引用必须带文件出处 |

**体积口径三档**：DiT 单独 **66.28 GB** / 「图像包」（含 VAE + 文本编码器）**68.65 GB** / 全仓含 `transformer_diffusers` 重复份 **≈ 132 GB**。⇒ 引「H3-Image 多大」必须带口径。

**社区二改的体积对照（待复现）**：MLX-8bit 全量 **42.6 GB**（DiT 22.4 + TE 20.2，README 自报 16 GB Mac / 512×640 / 62 s / 3.25 GB 峰值）；candle `q8` **68.9 GB**（DiT 35.30 + TE 33.71，**因 Q8_0=8.5 bpw 反比官方 fp8 大**）。⇒ 本机可用 **35 GiB**，**最省的 MLX 件仍差 8 GB**。

## 适配形态第 7 种：独立 MLP semantic bridge（2026-11-28 第 40 轮，K305）

`MistyViolet/MiniMax_H3:semantic_bridge/t8_compat/BUNNY_H3_ActionLogic_Bridge_V1_T8_Compat.safetensors`
= **22,046,928 B / 6 tensors 全 F32**：`fc1 [512,5120]` / `fc2 [512,512]` / `fc3 [5120,512]`（**5120 → 512 → 5120 瓶颈 MLP**，≈5.51 M 参数）。

`__metadata__` 要点：`bridge_type BUNNY_H3_ActionLogic_Bridge`、**`target_h3_layer "49"`**、`operation "lossless_metadata_wrap"`、`schema t8_semantic_bridge_v1`、`source {JOKER141/BUNNY_H3_Conditioning_Bridge, rev 658bfbb0}` + `source_sha256`、`activation silu`、`recommended_alpha_start "0.10"`、`recommended_magnitude_match per_token`、`teacher_val_cos 0.350` / `val_rep_cos 0.996` / `val_corr_cos 0.997`、`formal_prompts 2400`。

⇒ **与 LoRA 的本质差别：不是权重增量，而是整层替换**（`lossless_metadata_wrap` 把原网关包进 metadata）。本机 `strings libvpipe` 对 `semantic_bridge` / `actionlogic` / `BUNNY` **全 0 命中**，源码树 `grep semantic_bridge` = 0 ⇒ **没有任何 hook 点，`runtime-lora` 任何路径都绑不上**。`teacher_val_cos 0.350` vs `val_rep_cos 0.996` ⇒ 自报「行为接近本体、但与老师差很远」，价值不明（**待复现，社区单源**）。

## MLX w8a8 全家桶：第三个「Apple 运行时」分支（2026-11-29 第 41 轮，K310/K311）

`Joyboyreturns/MiniMax-H3-Image-MLX-w8a8`（167 文件，`lastModified 2026-11-28T16:23Z`，0 dl / 0 like，**首日**）——与 `SarthakRawool/…-MLX-8bit-LowMem`（K303）**不是同一份**：那份是 MLX affine（`U32` + `scales`/`biases`），这份是 **MLX ConvRot W8A8（`I8` + `F32 [N]` 逐行）**。

| 组件 | 体积 | 结构 |
|---|---|---|
| `dit/blocks/00..49` | 每片 **385,618,778 B** × 50 ≈ **19.28 GB** | 每块 **12 张量**：4 × `I8 weight`（`to_qkv [21504,5376]` / `to_out [5376,7168]` / `ff.0.proj [28672,5376]` / `ff.2 [5376,14336]`）+ 4 × `F32 [N] weight_scale` + 4 × `BF16` norm（`norm1/norm2/norm_q/norm_k [128]`） |
| `dit/core.safetensors` | 190,712,784 B / **23 张量全 BF16/F32** | 含 **`pdd_proj_out.0..5` 各 `[96,5376]`**（= 官方 `pdd_fused_heads` 的展开式，逐个 step 一个 Linear）、`proj_in [5376,96]` **F32**、`time_embedder.linear_1 [5376,256]` / `linear_2 [2688,5376]` |
| `dit/refiner.safetensors` | 1,541,464,152 B | token refiner（2 层） |
| `dit/modulation/` | 52 文件 | **预烘 AdaLN 表**（见 quantization.md §7.2） |
| `te/embed` + `te/layers/00..49` + `te/visual` | 1.56 + 24.39 + 1.19 GB | Qwen3-VL 层 0–49，每层 12 张量（4 × `I8` + 4 × `F32 [N]` + 4 × `BF16`），`qkv_proj [10240,5120]` **已融合**、`gate_up_proj [51200,5120]` **已融合** |
| `vae/` | 2,336,973,400 B | F32 全量 |
| **合计** | **≈ 50.5 GB**（不含 modulation） | vs 官方 66.28 GB DiT、MLX bf16 同构；**本机 3.4 GiB 可用** |

README 自报（**待复现，社区单源**）：16 GB M4 Air / 1024² / 6 步 = **99.80 s**（TE 7.39 + DiT 89.36 + VAE 3.05），峰值 **1.58 GB**（SSD 流式，零 swap）。

**本机判死四条（逐条读代码，未下载）**：
1. **`hadamard: sylvester`** —— 本机 `convrot_unrotate` 只有 regular 基（错基 ⇒ relL2 2.06，见 quantization.md §7.1）。
2. **`is_diffusers_layout()` 三条判据全不满足** —— 缺 `transformer_blocks.0.adaln_proj.linear.weight`（此件**根本没有 `adaln_proj`**，AdaLN 是预烘表）、缺 `token_refiner.refiner_blocks.0.attn.to_q.weight`（refiner 单独成文件且命名未知）、有 `context_embedder.weight` 但前两条已挂 ⇒ `native_()` 不触发，`blocks.0.attn.to_qkv.weight` 无人翻译成 `attn.qkv_proj`。
3. **融合投影无反翻译** —— `minimax-h3-diffusers-layout.cc:246-248` 只有 **拆**（`to_q → to_qkv.q`），**没有 `to_qkv → q/k/v` 的逆**；`assembled_parts()` 只在 `to_q/.k/.v` 存在时才拼。
4. **`fused_gate_up` 同理** —— 本机 `mlp.fc1.ug` 是「up|gate 一文件两半」，此件 `gate_up_proj` 是**单张量融合**，没有拆分支。

⇒ **不是「格式不认」，而是「命名契约 + 旋转基 + AdaLN 形态」三处同时不同**。要读需：写 Sylvester 基分支 + 补 `to_qkv→qkv` 拆解 + 补「预烘表」AdaLN 分支。**工作量 ≈ 一个新的适配形态，且本机磁盘 3.4 GiB 连 50 GB 都放不下 ⇒ 不投入。**

## 第四个「整机套装仓」：diffusers modular + AoTI（2026-11-29 第 41 轮，K313）

`addlabsviral/minimax-h3-combined`（62 文件 / 1,144 dl / 0 like / `11-28T13:20Z`）——为 **HF ZeroGPU Spaces** 打包的部署件，README 自报全仓 **≈112 GB**（Hub 150 GB/Space 配额内）。

| 目录 | 内容 | 体积 |
|---|---|---|
| `transformer/` | 50 块，**BF16 且 Turbo LoRA 已折进权重** | index `total_size` **66,280,430,080 B**（7 分片） |
| `transformer_ref/` | 同结构 ref 分区 | 14 分片 |
| `text_encoder/` | Qwen3-VL **8-bit（bitsandbytes LLM.int8）** | **35,527,751,672 B** 单文件 |
| `vae/` + `audio_vae/` | F32 未量化 | 3 分片 |
| `aoti/.../package.pt2` | **AoTI 编译的 transformer_block 包** | **862,601 B**（仅 862 KB，编译成 torch 归档而非权重） |
| `lora/` | Turbo LoRA 原档（已折入，仅供对照） | — |

**两处新增知识**：
- **`base_model_relation: merge`** —— 首个把「权重融合」写进 metadata 的整机仓（前三个 K285/K287/`MistyViolet` 都是「多件并列」）。⇒ 判「要不要再挂 LoRA」先读这个字段：`merge` 表示**再挂一次等于双倍**。
- **`aoti/` 是第五种「非 safetensors 权重容器」**（前四：GGUF / `.pt2` 在此首次出现 / MLX `safetensors+json` / candle `safetensors` 分片 / `adaln_t_table.bin` 裸 f32）。862 KB 说明**它不含权重**，只是编译产物，本机无任何理由解析。
- **`text_encoder` 是 bnb LLM.int8，`SCB`/`weight_format` 拼写本机不认识**（见 quantization.md §7.3）。

## 社区工作流洪水与空壳的量化（2026-11-29 第 41 轮，K314）

- **`AI-KSK/*` 单组织 139 个仓**，其中 H3 相关 **≥20 个**（`minimax-h3-*-NNN` 系列，编号 288–331），全部 `0 dl / 0–3 like`、`lastModified 11-28T13:18–13:27Z`（**9 分钟内批量上传**）。命名规律 = `<主题>-<流水号>`。
- ⇒ **「H3 生态仓数」不能直接当活跃度**：单日 20+ 仓来自一个组织的批量搬运。**判活跃要看「独立作者数」与「有 dl 的仓数」**。
- **`RunningHubAI/rh-*` 空壳率本轮 2/2**（`rh-minimax-h3-image-123-2250-lora`、`rh-minimax-h3-dmd-8step-turbo.safetensors-lora` 均只有 `.gitattributes`）；累计 K288 的 3/3 ⇒ **总 5/5 = 100% 空壳**。⇒ 见 `rh-` 前缀先查 siblings 数，`==1` 即判空。
- **`Rex38rus/MiniMax-H3-GGUF`、`elismasilva/minimax_h3_video_custom_blocks`** 也只有 `.gitattributes`（`dl=0`）⇒ **空壳不止 `rh-` 一家**。
- **`Harsha001/MiniMax-H3-Image-ROCmFPX`** = **gated**（`api/models` 正常列 8 siblings 含 4 个 GGUF + `sdcpp-rocmfpx.patch`，但 `raw/README.md` 与 `resolve` 全 403）。⇒ 与 K251 同型，**且这次是「连 README 都 403」**（K251 那条 README 可读）⇒ **gated 有两档：只挡权重 / 连 README 一起挡**。

## 混合量化「按块切档」的第三种排布（2026-11-29 第 41 轮，K314）

`chdp207/minimax_h3_ref2va_LightX2V4step_Mystic05_NDE05mlp_W4A8_EdgeFP8` 两件同仓、同一 `converted_by` 流程：

| 件 | 体积 | 块分布 |
|---|---|---|
| `…_W4A8_EdgeFP8.safetensors` | **13,214,260,168 B** / 1300 tensors | 块 **2–47 = W4A8**（`I8 [N,K/2]` + `s_rel E4M3 [N,K/16]` + `s_channel F32 [N]` + `codebook F32 [16]`，`comfy_quant {"asym_w4a8_int8","group_size":16,"convrot":true,"convrot_groupsize":256}`）；块 **0,1,48,49 = FP8**（`F8_E4M3` + `weight_scale F32 []`） |
| `…_W8A8.safetensors` | **20,969,407,312 B** / 932 tensors | 块 **2–47 = int8 ConvRot**（`I8` + `weight_scale F32 []` + `comfy_quant {"int8_tensorwise","convrot":true,"256"}`）；块 **0,1,48,49 = FP8** |

- **命名 `EdgeFP8` 的含义** = **首尾 4 块（0/1/48/49）保 FP8、中间 46 块压到 W4A8**（metadata `quant_recipe` 原话：「blocks 2-47; TensorCoreFP8E4M3Layout blocks 0,1,48,49」）。「Edge」指**块序的两端**，不是图像边缘。
- **第三处「按块切档」证据**（前两处：Kijai `b25-49` 前 25 块 BF16 / 后 24 块 int8 的**误读**（K282 已推翻）、`Fusion hybrid`）。
- **`nvfp4_reference_vessel`** = metadata 里点名**用于对标但不在本件的 NVFP4 件**（`10Eros_Max_h3_8stepTURBO_beta6_pruned_nvfp4`）⇒ **metadata 里可以出现「指向别处的参考件」**，读 metadata 不能假设所有字段都描述自身。
- 两件都是 **pruned 形态**（`adaln_t_table [1025,8]`），`lora_merge` 字段记录了融合公式与两个 LoRA（`4step_v1.0_768p_comfyui_bf16 ×1` 208 模块 + `MysticXXX V5 ref2va ×0.75` 82 模块，`lora_exclude_regex = adaln_proj`）。
- **本机可读性（逐字段核对，两件都过）**：
  - **W8A8 件**：块 2–47 `I8 [21504, 5376]`（**整字节，K = 5376 不翻倍**）+ `weight_scale F32 [21504, 1]`（2-D 列向量，本机 `fp8-layout.cc:436-440` 的 `col` 判定接受 `shape[1]==1`）+ `comfy_quant{"int8_tensorwise",convrot,256}` ⇒ **与本机常规 int8 ConvRot 完全同形，结构上可读**。
  - **W4A8 件**：块 2–47 `I8 [21504, **2688**]`（**半字节，K = 2688×2 = 5376**）+ `weight_s_rel E4M3 [21504, 336]` + `s_channel F32 [21504]` + `codebook F32 [16]`，`resolve_w4a8_` 要求 `s_rel == [N, K/16]`，`5376/16 = 336` ✓、`codebook == 16 F32` ✓ ⇒ **也过全部门**。
  - ⚠️ **唯一分辨点就是 `shape[1]` 是否等于 `K`**：两件的 `comfy_quant` 都是 72/89 B 的小 JSON，**`format` 字段是唯一分清 `int8_tensorwise`（整字节）与 `asym_w4a8_int8`（半字节）的东西**；同为 `I8`、同为 `convrot 256`、同样 4 个块是 FP8。**只看 dtype + 体积判断会错**。
  - ⚠️ 但**两件都要求 `comfy_quant` 记录在**；若某转换器像 K303 那样把它剥掉，两件会同时落入「I8 有 scale 无记录 ⇒ 明确拒载」，而不是静默错值。
  - ⇒ 这两件是**目前唯一「结构上本机直接可读」的 pruned + 混合量化 + LoRA 已融合**件，但体积 13.2 / 21.0 GB，**本机 3.4 GiB 可用 ⇒ 登记不下载**（P67）。
