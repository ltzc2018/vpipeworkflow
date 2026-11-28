# vpipe 上游 Issue 提案（5 条）

> 提交目标：`https://github.com/tgo-app-dev/vpipe/issues`
> 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存
> vpipe 版本：`main` @ `33cda00`（源码编译，Apple Silicon 构建）
> 全部条目均在本机复现，日志与命令可复现。
>
> **可直接提交的单条文件在 `issues/` 目录**：`issue-1.md` … `issue-5.md`，每条一个文件，
> 首行是标题（可直接作为 issue title），其后是正文。本机未安装 `gh` 且无 GitHub token，
> 故由使用者手动提交；正文已按可粘贴格式排好。
>
> | # | 标题 | 性质 |
> |---|---|---|
> | 1 | `url-files` 型模型只绑定单一 GitHub URL，受限网络下无备用通道 | feature/bug |
> | 2 | `parent_model_type` 与当前 partition 不符的 LoRA 不被拒绝 | bug |
> | 3 | Ref2VA partition + VDN linear branch 只警告不拒绝 | bug |
> | 4 | 准备 Ref2VA 时编码器被无谓地重新量化（多出 27 GB） | feature |
> | 5 | `model-fetch` 的「伴随 checkpoint 未拉取」警告不准确（第三轮新增） | bug |

---

## Issue 1 — `url-files` 型模型只绑定单一 GitHub URL，受限网络下无备用通道

### 现象

官方文档给出的 TAE-H3 预览解码器准备流程无法完成：

```sh
vpipe --launch docs/pipelines/prepare-minimax-h3-preview.vpipeline
```

实测输出：

```
[INFO] ModelFetchStage('fetch'): fetching 'madebyollin/taehv' from raw.githubusercontent.com -> './models/madebyollin/taehv'
[INFO]   [1/1] taeh3.safetensors ...
[INFO]     taeh3.safetensors: interrupted at 0.0 B (SSL connect error); attempt 2/6 in 2s
...
[ERROR] ModelFetchStage('fetch'): model fetch 'taeh3.safetensors' failed: SSL connect error
```

### 分析

`stages/model-catalog.cc` 中该条目的 `extra` 字段给出**唯一一个** URL：

```cpp
{.family = "MiniMax", .version = "H3-FL2VA", .param_class = "TAE",
 .variant = "taeh3 temporal preview decoder (madebyollin)",
 .hf_path = "madebyollin/taehv",
 .model_type = "minimax-h3-tae",
 .parent_model_type = "minimax-h3-fl2va",
 .files = {"taeh3.safetensors"},
 .extra = catalog_url_files_extra(
     {{"https://raw.githubusercontent.com/madebyollin/taehv/main/"
       "safetensors/taeh3.safetensors",
       "taeh3.safetensors"}}),
 .name = "madebyollin/taeh3"},
```

`stages/model-fetch-stage.cc` 的 3b 分支（「Verbatim URL fetch ... a MODEL published somewhere this stage cannot walk」）按 URL 原样下载，没有候选列表与镜像回退。

问题在于 **`raw.githubusercontent.com` 与 `api.github.com` 的可达性并不相同**：同一文件、同一仓库、同一 commit，通过

```
GET https://api.github.com/repos/madebyollin/taehv/contents/safetensors/taeh3.safetensors
Accept: application/vnd.github.raw
```

可以正常取到（实测 22,709,752 字节，sha256 `4fd022bfcab08772fe0536b17ea1a3bbb5625be11e397868d1c5d891863d4c13`，与官方公布值一致），而 `raw.githubusercontent.com` 在本机被 SSL 阻断。

也就是说：受这一条 URL 影响的用户，**恰恰是文档中明确服务的中国大陆用户**（文档专门用 `modelscope` 源解决 HF 不通的问题），而 `url-files` 这条路径既没有 ModelScope 镜像，也没有备用主机。

### 影响面不止 taeh3

catalog 里凡是走 `catalog_url_files_extra` 的条目都受影响，包括：

- `madebyollin/taeh3`（H3 实时预览解码器）
- `madebyollin/taew2_1`（Krea-2 实时预览解码器）
- `vpipe-supplement` 的 CoreML 补充包

### 建议

1. `catalog_url_files_extra` 支持**候选 URL 列表**，按顺序尝试，第一个失败自动回退；
2. 或为 GitHub 系 URL 增加 `api.github.com` + `Accept: application/vnd.github.raw` 作为内置备选；
3. 至少在失败信息中把「源主机不可达」与「文件损坏」区分开（当前统一报 `SSL connect error`，用户难以判断是网络问题还是校验问题）。

---

## Issue 2 — `parent_model_type` 与当前 partition 不符的 LoRA 不被拒绝（与 manifest 型 adapter 规则不一致）

### 现象

`larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema` 的 catalog 条目是：

```cpp
{.family = "MiniMax", .version = "H3-FL2VA", .param_class = "LoRA",
 .variant = "Turbo few-step v4-600 EMA (larryvrh)",
 .hf_path = "larryvrh/MiniMax-H3-Turbo-Lora",
 .model_type = "minimax-h3-lora",
 .parent_model_type = "minimax-h3-fl2va",     // ← FL2VA 专用
 .files = {"minimax_h3_turbo_v4_step600_ema.safetensors"},
 .name = "larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema"},
```

**catalog 中没有该 adapter 的 Ref2VA 版本。** 把这个 FL2VA 专用 adapter 挂到 Ref2VA partition 上运行：

```json
{ "id": "minimax-h3-model-config", "type": "minimax-h3-model-config",
  "config": { "lora": "larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema",
              "lora_scale": 1.0 } }
```

vpipe **不报错、不警告**，完整出片（本机 12 分 54 秒，960×544 / 124 帧 + 音轨）。

### 与文档/其它 adapter 的行为对比

`docs/MINIMAX-H3.md` 明确写道：

> *"Keep `video_shift` / `audio_shift` at 12 / 3, **each partition takes ITS OWN**, since an adapter is distilled for one task and **the catalogue's parent link refuses the other partition's**"*

并且对 Pika H3 Flex：

> *"The FL2VA adapter is **refused** on the Ref2VA weights and the Ref2VA adapter on the FL2VA weights — each was trained on one"*

实测确认：**Pika-Flex 型（带 `manifest.json`）的 adapter 确实会被拒绝**；而传统 LoRA（无 manifest）这条 `parent_model_type` 约束**完全不被执行**。

### 影响

规则不一致导致：

- 用户可以在 Ref2VA 上静默使用 FL2VA 蒸馏的 adapter，得到次优结果且毫无提示；
- 文档描述的行为与实现不一致，容易误导；
- 这类错误很难自查——出片正常、只是质量偏弱。

### 建议

在 `generate-video` 装载 adapter 时比对 `parent_model_type` 与当前 partition：

- 不匹配时至少 `warn`（写明是哪个 adapter、期望哪个 partition）；
- 或按文档措辞改为 `error`，并提供显式的 `force: true` 之类的豁免开关；
- 与 manifest 型 adapter 的拒绝规则统一。

---

## Issue 3 — Ref2VA partition + VDN linear branch 只警告不拒绝，产出「无发布配置」的结果

### 现象

在 Ref2VA partition 上挂 VDN 线性分支：

```json
"linear_branch": "OpenVDN/vdn-minimax-h3-stage-dmd"
```

运行时报一条 warning 后**继续跑完全流程并出片**（本机 12 分 54 秒）。

源码位置 `generative-models/minimax-h3/metal-minimax-h3-transformer.cc:8780`：

```cpp
if (L.ref2va && _cfg.partition == "ref2va") {
  _mc->session()->warn(fmt(
      "MetalMiniMaxH3Transformer: VDN's branch is trained on the "
      "FL2VA partition's blocks and this is Ref2VA; its {} reference "
      "rows are attended densely, outside the window, and the linear "
      "branch does not see them -- no published configuration pairs "
      "the two", L.num_condition_rows));
}
```

同一处的设计注释写得很清楚：

> *"On the Ref2VA partition the branch would be attached to blocks it was not trained with, **which nothing published does** -- that one still warns."*

文档同样说明：

> *"**the VDN branch is only published for FL2VA**, so before it the linear attention and references could not be had together."*

上游的官方组合是「FL2VA 权重 + references」（即 `ref2va-like` 模式）：引用行照 Ref2VA 的方式打包，但由 FL2VA 的 transformer 读取。

### 影响

- 系统明知该组合「没有发布配置」，却只给一条 warning 并照常出片；
- warning 淹没在数十行 `[INFO]/[PROGRESS]` 之后，实践中极易被忽略；
- 结果是**用户拿到一段看似成功、实则无参考支撑的视频**，可用于带货等对外场景，误用成本高。

### 建议

把这一组合从 `warn` 提升为**显式拒绝**（`error`），或提供明确的 opt-in 开关（例如 `allow_unpublished_partition_pair: true`），并在开关生效时于日志中打印醒目的横幅；文档中给出「Ref2VA 想要参考一致性应该用哪条路线」的指引（FL2VA + `ref2va-like`，或 Pika H3 Flex 的 `ref2va` adapter）。

---

## Issue 4 — 准备 Ref2VA 时编码器被无谓地重新量化（多出 27 GB 新字节）

### 现象

文档把磁盘占用写得明明白白：

> *"The two partitions **share one repo and one download**. Ref2VA adds only its own 66 GB transformer; the 51 GB prompt encoder and both VAEs are already on disk from step 1 and are skipped."*

但同一篇文档的磁盘小节又承认：

> *"The *download* really does add only the 66 GB transformer — the prompt encoder and both VAEs are already on disk and are skipped. But the pipeline that prepares it **quantizes the encoder too**, into an output of its own, so what you end up holding is a second complete model: ~33 GB of transformer plus ~27 GB of encoder at 8-bit. Only the components quantization leaves alone are hard-linked, and **a re-quantized encoder is new bytes**."*

### 为什么这是个真问题

两个 partition 的**编码器是同一个权重**（Qwen3-VL-32B），量化到 8-bit group-64 的结果也应当逐字节相同 —— 但 `model-quantize` 无条件重新量化一遍，于是：

| | 官方准备流程 | 复用已有 8-bit 编码器 |
|---|---:|---:|
| Ref2VA 8-bit 净增磁盘 | **~60 GB** | **~33 GB** |
| 额外耗时 | 再量化一次编码器 | 0（本机实测 DiT 量化 82 秒） |

在磁盘紧张的机器上，这 27 GB 是「做参考生视频」与「做不了」的分界线。本机当时只剩 90.7 GB，官方流程需要 117.8 GB，直接卡死。

### 本机绕过方式（已验证可用）

只量化 Ref2VA 的 DiT，编码器与双 VAE 用**硬链接**复用 FL2VA-8bit 的产物：

```
models/local/MiniMax-H3-Ref2VA-8bit/
├── diffusion_models/  ← 新量化产物（33 GB），inode 与 FL2VA 完全不同
├── text_encoders/     ← 硬链接到 FL2VA-8bit 的编码器分片，零额外占用
├── tokenizer/         ← 硬链接
└── vae/               ← 硬链接（video VAE inode 3246333 links=5，audio VAE 3246378 links=6）
```

注意 `model-quantize` 的 `src_model` 要给**绝对路径**、`output_name` 要给**相对路径**（`local/MiniMax-H3-Ref2VA-8bit`），否则不会写注册表，后续 `model-select` 会报 `cannot open local/MiniMax-H3-Ref2VA-8bit/transformer`。

### 建议

给 `model-quantize` 增加一个「复用同族已有产物」的选项（例如 `reuse_text_encoder_from: local/MiniMax-H3-FL2VA-8bit`），或者至少在 `prepare-minimax-h3-ref2va-8bit.vpipeline` 里检测同工作目录已存在的 FL2VA 8-bit 产物并直接硬链接 —— 两个 partition 的编码器本来就是同一个权重，重量化一次没有信息增益，只增加 27 GB 与一次量化耗时。

---

## Issue 5 — `model-fetch` 的「伴随 checkpoint 未拉取」警告不准确

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
### 现象

拉取一个**自带视觉塔**的多模态模型后，`model-fetch` 打印了一条警告，说有 3 个「伴随 checkpoint」没有一起拉取，并且断言：

> A stage that wants one will refuse at launch; fetch each with `model-fetch model_path=<key>`

但**实际上没有任何 stage 拒绝启动** —— `text-chat` 用这个模型正常加载、正常跑完了**图文**问答。

复现：

```sh
vpipe --launch ./pipelines/prepare-multimodal-compare.vpipeline
```

日志（原文）：

```
[INFO] ModelFetchStage('fetch-qwen35-4b'): 13 file(s) (13 downloaded, 0 already present), 2.9 GB total
[INFO] ModelFetchStage('fetch-qwen35-4b'): 13 of 13 downloaded file(s) matched the checksum 'mlx-community/Qwen3.5-4B-MLX-4bit' publishes
[INFO] ModelFetchStage('fetch-qwen35-4b'): registered 'mlx-community/Qwen3.5-4B-MLX-4bit' in the model registry
[WARN] ModelFetchStage('fetch-qwen35-4b'): the catalogue lists 3 companion checkpoint(s) for this model that are NOT fetched:
      'z-lab/Qwen3.5-4B-DFlash', 'qwen3_5_mlx_4b_vision_vid_512x320', 'qwen3_5_mlx_4b_vision_vid_768x480'.
      A stage that wants one will refuse at launch; fetch each with model-fetch model_path=<key>
```

紧接着用同一个 `hf_dir` 起 `text-chat`，**一切正常**：

```
[INFO] TextChatStage('chat'): loading model from 'mlx-community/Qwen3.5-4B-MLX-4bit' (dtype=bf16, page_tokens=1024, max_pages=64)
[INFO] TextChatStage('chat'): model ready (24 layers, vocab=128000, thinking=off)
[INFO] TextChatStage('chat'): prefill 437 tok in 0.279 s = 1567.9 tok/s, decode 87 tok in 1.049 s = 83.0 tok/s, ctx_pos 525
```

而且这次对话**带了图片附件**（媒体行标记内联一张 PNG），模型正确描述了图片内容 —— 说明视觉塔被正常用上了。

### 分析

被点名的三个「伴随 checkpoint」其实**根本不是同一个模型的组件**：

- `z-lab/Qwen3.5-4B-DFlash` 是一个**独立的蒸馏模型**（DFlash2 变体），不是 4B-MLX-4bit 的附件；
- `qwen3_5_mlx_4b_vision_vid_512x320` / `_768x480` 是**另一套预训练好的视觉视频投影头**（catalog 里单列的 `qwen3.5` family 条目，param_class 写作 `4B`，但 checkpoint 名里带 `vision_vid`），是**替代方案**而不是**必配件**。

而本次拉取的 `mlx-community/Qwen3.5-4B-MLX-4bit` 自己就带齐了视觉侧：

```
model.safetensors.index.json   1221 tensors，其中 297 个是视觉塔张量
  vision_tower.blocks.0.attn.qkv.weight
  vision_tower.blocks.0.mlp.linear_fc1.weight
  ...
preprocessor_config.json        图像预处理
video_preprocessor_config.json  视频预处理
```

所以这条警告把「catalog 里同 family 的其它条目」误当成了「当前模型的必需附件」，并给出了一个**错误的失败预测**。

### 影响

1. **误导用户去多下 3 个模型**（`z-lab/Qwen3.5-4B-DFlash` + 两个 `vision_vid`），白白多占磁盘与时间 —— 在本机这种磁盘紧张的场景尤其痛；
2. **给出错误的失败预测**（"will refuse at launch"），让人以为配置有问题而去排查错误的方向；
3. 真正需要 `vision_vid` 的 stage（例如把视频帧喂给 Qwen 的视频通道）确实会拒绝启动，但那时应该由**那个 stage 本身**报错，而不是由 `model-fetch` 提前用一条笼统的警告把话说死。

### 建议

1. `model-fetch` 的伴随 checkpoint 警告区分两类：
   - **同一 checkpoint 的必需组件**（缺了必然起不来）→ 应该用 ERROR 或直接失败；
   - **catalog 里的其它可选变体**（DFlash、vision_vid 等）→ 改成 INFO 级别，或加一句「这些是替代变体，不是本模型的组件」。
2. 警告文案不要断言 "will refuse at launch"；改成「以下变体未拉取，若要使用请另行获取」之类不承诺失败的说法。
3. 更彻底的做法：判断「必需」时按 `hf_path` 精确匹配，而不是按 `family` / `param_class` 之类的粗粒度字段做包含关系。

---

### 复现环境

- 模型：`mlx-community/Qwen3.5-4B-MLX-4bit`（2.9 GB，13/13 文件校验通过）
- 阶段：`model-fetch` → `text-chat`（`hf_dir: mlx-community/Qwen3.5-4B-MLX-4bit`，`compute_dtype: bf16`）
- 输入：stdin 单行，含 `<|__vpipe_fs_im_start__|/abs/path.png<|__vpipe_fs_im_end__|>` 媒体行标记
- 输出：`save-text`（`key: "text"`）

---

## 附：本轮实测中确认可用的替代路线

若上游短期内不改动，按下表选型即可（均已在本机跑通）：

| 目标 | 推荐配置 | 本机实测 |
|---|---|---|
| **参考图 → 视频（参考一致性优先）** | `local/MiniMax-H3-Ref2VA-8bit` + `Pika-Labs/Pika-H3-Flex-ref2va` | 832×480 / 124 帧 / 6 步 renoise，**6 分 49 秒**出片 |
| 官方已发布配对 | `local/MiniMax-H3-FL2VA-8bit` + VDN 线性分支 + FL2VA Turbo | `ref2va-like` 模式，960×544，8 分 20 秒 |
| 首帧图 → 视频（商品图转短视频） | `local/MiniMax-H3-FL2VA-8bit` + `Pika-Labs/Pika-H3-Flex-fl2va` | 官方 `pika-h3-flex-first-frame-to-video.vpipeline` 图形 |
| 文生视频 | `local/MiniMax-H3-FL2VA-8bit` + `larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema` | 4 / 6 步均可 |

其中 Pika H3 Flex 的 `manifest.json` 会接管采样契约（日志：`6 steps RE-NOISED on the sampling contract's grid (pika-flex-ref2va-v1)`），并按 `trunk: "transformer_ref"` 绑定到 Ref2VA 的专用主干。

### 附：验证「参考图是否真的生效」的正确做法

第一版报告曾用「提示词里写死主体外观」的方式做参考生视频，结论不可证伪。正确的做法是**消融对照**，且参考图必须选一个**模型先验不可能命中**的主体：

| 组 | 参考图 | 提示词 | 输出 |
|---|---|---|---|
| A | 姜黄猫（写实照片） | 零外观描述 | 姜黄虎斑猫 |
| B | 无（`references: []`） | 同上 | 姜黄虎斑猫（更浅、虎斑更淡） |
| C | 姜黄猫 | 同上（FL2VA 路线） | 姜黄虎斑猫（条纹对比最强） |
| **D** | **黑白熊猫（水彩插画）** | 同上 | **黑白熊猫** ← 决定性证据 |

A/B 在外观层面不具区分度（"窗台 + 暖阳 + 猫"本身就是模型的强先验）；只有换掉先验不可能命中的主体，结论才成立。

**内部量化佐证**：参考图让 DiT 的打包序列多出 2,056 行（16,999 vs 14,943），AdaLN 烘焙表多 6 行（17 vs 11 rows）。


---

## 上游 issue 状态快照（2026-11-29 02:45 抓取 · 第 41 轮）

`api.github.com/repos/tgo-app-dev/vpipe/issues?state=open&per_page=100` ⇒ **14 条全开、0 条关闭、无 label / milestone / assignee**，评论合计 **9**（#52/#45/#34 各 2，#49/#41/#31 各 1）。`pulls?state=open` ⇒ **0**。与第 39/40 轮**逐字相同**，第 5 日无变化。

`updated_at == created_at`（**从未被维护者碰过**）共 **7 条**：#59、#58、#56、#53、#48、#17、#15。

**与本机相关的三条仍无回应**：

| # | 标题 | 创建 | 与本机实测的关系 |
|---|---|---|---|
| 59 | RelayVSR: support the native 2x checkpoint | 11-16 | 与本机 P29/P32 的 2× 档结论一致（欠估增强）；上游未收 |
| 56 | FastH3-Omni: the VSA compression gate and its routing budget | 10-22 | 与 K181/P45 的 `gate_compress` 缺口逐字一致；**已 38 天无回应** |
| 55 | MiniMax-H3 persistent temporal texture "boiling" | 10-21 | 与 K96/K122 的纹理沸腾结论同源；`updated_at` 比 `created_at` 晚 10 min（仅自动标签） |

⇒ **本轮不新增提案**：本轮 8 条知识里没有一条是「本机发现的上游缺陷」——K310–K315 全是**社区件的可读性判据**，属本机能力矩阵，不是上游 bug。P68 的 `hadamard` 声明位若要提给上游，**应等上游真的开始读 Sylvester 件再说**（当前 `41a694a2` 连 `dit.json` 都不读，提了也无从验证）。
