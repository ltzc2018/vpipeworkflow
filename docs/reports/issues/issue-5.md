# `model-fetch` 的「伴随 checkpoint 未拉取」警告不准确：明明自带视觉塔，仍警告 stage 会拒绝启动

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
<!-- 全部条目均在本机复现，日志与命令可复现。 -->

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

## 附：复现环境

- 模型：`mlx-community/Qwen3.5-4B-MLX-4bit`（2.9 GB，13/13 文件校验通过）
- 阶段：`model-fetch` → `text-chat`（`hf_dir: mlx-community/Qwen3.5-4B-MLX-4bit`，`compute_dtype: bf16`）
- 输入：stdin 单行，含 `<|__vpipe_fs_im_start__|/abs/path.png<|__vpipe_fs_im_end__|>` 媒体行标记
- 输出：`save-text`（`key: "text"`）
