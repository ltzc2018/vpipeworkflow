# 准备 Ref2VA 时编码器被无谓地重新量化（多出 27 GB 新字节）

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
<!-- 全部条目均在本机复现，日志与命令可复现 -->

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
