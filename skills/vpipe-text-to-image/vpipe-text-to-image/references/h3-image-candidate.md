# MiniMax H3-Image —— vpipe 文生图的新候选（2026-11-18 第 5 轮登记）

> 最后更新：**2026-11-18 06:31**（第 5 轮夜间知识同步）
> 状态：**🔴 待验证（磁盘阻塞）** —— 尚未在本机跑过任何一张。
> 本机现有 T2I 模型：**Z-Image-Turbo**（6B 蒸馏，8 步，45–46 s/张）、**Krea-2-Turbo**（8 步）。

---

## 1. 为什么值得登记

H3-Image 是 **H3 视频模型的图像分支**（同一 DiT 去掉音频层），
和本实验室正在做的 H3 视频研究**同源** → 值得单独跟踪。

| 项 | 值 |
|---|---|
| 架构 | H3 DiT 去掉音频分支；33.1B；dense 单流；**50 层**；hidden 5376；56 头 |
| 采样 | **6 步蒸馏**、**CFG 固定 1**（**无负面提示词**）、denoise 1.0 |
| 原生分辨率 | 约 **16 MP**（1:1 = 4096×4096 … 21:9 = 6272×2688）；有效区间约 4–20 MP |
| 参考图 | 最多 **16 张**（同一个 checkpoint 同时做 T2I 与多参考编辑） |
| 文本编码器 | **Qwen3-VL-32B，与 H3 视频完全共用** |
| Image VAE | 16× 空间下采样、24 latent 通道；2×2 patch → 每 token 覆盖 32×32 px |
| 权重（官方） | BF16 **68.65 GB** |
| 许可 | MiniMax-H3-Image Community License：**排除美国 / 欧盟 / 英国 / 韩国**；年营收 >100 万美元或对外托管服务需书面授权；商业产品界面须标注「MiniMax-H3-Image」 |

来源：<https://artrealmai.com/article/minimax-h3-image-open-weights-comfyui-16mp>、
<https://vega.chat/blog/minimax-h3-image>、<https://sloptvnews.com/minimax-h3-image-open-weights-4k>

---

## 2. 落地路径（清盘后按此走）

### 2.1 需要下的文件（Comfy-Org 打包）

| 文件 | 体积 | 去向 |
|---|---:|---|
| `minimax_h3_image_pruned_int8_convrot.safetensors` | **21 GB** | `models/diffusion_models/` |
| `minimax_h3_image_vae_fp16.safetensors` | 1.17 GB | `models/vae/` |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 25.28 GB | `models/text_encoders/`（**若已有 H3 视频的文本编码器则可跳过**） |
| `qwen3.5_9b_w4a8_gptq.safetensors` | 7.34 GB | 提示扩写器（可选） |

- 另有 **w4a8 档 12.6 GB**（显存小的卡用）。
- **最小可跑集**：21 GB + 1.17 GB + （若已有）文本编码器 ≈ **22.2 GB**。

### 2.2 本机当前的阻塞

- Data 卷可用 **5.3 GiB**（第 5 轮实测），**远低于 15 GiB 下限** → 21 GB 模型下不动。
- 本机已有 H3 视频的 Qwen3-VL 文本编码器？**待查**（`models/Comfy-Org/MiniMax-H3/text_encoders`）。
  若有，可省 25.28 GB。
- ⇒ **先清盘到 ≥15 GiB，再按 2.1 下载。**

### 2.3 vpipe 侧的未知（待验证）

| 问题 | 怎么验 |
|---|---|
| vpipe 有没有 H3-Image 的 DiT stage？ | grep 本地源码树 `minimax-h3-image` / `h3-image`（**本轮未验**，第 5 轮只验了 ControlNet = 0 命中） |
| 图像 VAE 的 stage 是否支持 16× 下采样 + 2×2 patch 的 token 布局？ | 跑一张 4 MP 试试 |
| 6 步 / CFG 1 / 无负面提示词在 vpipe 侧怎么配？ | 对照 Comfy 模板的 `euler, simple, 6 steps, CFG 1, denoise 1` |
| 本机内存（24 GB 统一）能不能装下 21 GB INT8 + 文本编码器 + VAE？ | 按第 1 轮 P1 的内存账法估算；**大概率需要 swap allowance 调高** |

---

## 3. ★ 值得抄的社区设置（H3-Image 三条修复）

社区实测（`pixelailabs.com` / `webhill.net`，2026-11）认为默认模板出「crunchy grid」的根因是
**分辨率太低 + 采样器过锐**，给三条：

1. **把原生分辨率拉到接近目标（8–16 MP+）再降采样**，而不是把细节压进低分辨率；
   （作者实测 4 MP → 16 MP 只多约 9 秒采样）
2. **换采样器**：`SamplerLCM` + `simple` scheduler + 6 步 + **`s_noise` 1.10 → 0.90**
   → 「crunchy grid」消失，皮肤出现真实毛孔
3. **弃用标签堆砌**，改写成长而连贯的描述；接 `MiniMaxH3PromptWeight` 节点与单帧解码器
   （不要用基础视频 VAE）

⇒ 第 2 条与本实验室第 4 轮 P18 的 `dmd` 判决**同源**
（见 `vpipe-model-prepare/references/sampler-spec.md` §8.1）。

---

## 4. 官方提示词写法（valtz 里的官方技能）

`valtz` 仓库 `core/resources/skills/minimax-h3-image-t2i.md` 给出 H3-Image 的官方提示词规范，
要点（**官方原文归纳**）：

- 模型只吃**一整段详细英文描述**，短提示词会出「平淡图」；
- **保留用户给的硬事实**（原文、名称、数量、数字、公式、风格、媒介、上下左右位置），
  其余**自己拍板定一个具体方案**，不许给备选、不许模棱两可；
- **不要发明品牌、logo、名人**；
- **画面里要画的每个词都用双引号精确写出**（大小写、标点、字体、位置），换行写 `\n`；
- **一段连续散文**，150–400 词；不要 Markdown、不要标题、不要列表；
- **绝不把尺寸/比例/画幅写进提示词**（"1024x1024"、"square format"、"16:9"、"canvas" 全部禁写）；
- 输出格式：`{"prompt": "...", "title": "2-5 word title"}` 单行 JSON。

> ⚠️ **这条对 vpipe 侧的启示**（第 6 条）：vpipe 的 `text-prompt` stage 接的是普通文本，
> 不是这个 JSON → **若要用 vpipe 跑 H3-Image，需要把 JSON 里的 `prompt` 字段抽出来单独喂进去**，
> 不能整段 JSON 塞进去。

来源：<https://raw.githubusercontent.com/tgo-app-dev/valtz/main/core/resources/skills/minimax-h3-image-t2i.md>

---

## 5. 待验证任务（已登记进计划表）

- **P28 · H3-Image 落地**：清盘 → 下 21 GB INT8 → 4 MP 出图 → 与 Z-Image-Turbo 同提示词对比
  （时间、画质、是否需要换采样器）。
- **P28-b · vpipe 是否支持 H3-Image**：先 grep 源码树 `h3-image` / `minimax-h3-image`；
  若 0 命中 → 与 ControlNet 一样写成上游 issue，不做本地实验。
