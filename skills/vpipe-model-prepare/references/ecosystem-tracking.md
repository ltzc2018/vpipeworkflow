# 生态跟踪备忘（自动任务追加，只追加不删改）

## 2026-11-22 · pi-H3 权重发布（第 22 轮 · K117–K119）

- **HF `Lakonik/pi-H3`**（2026-11-21）：MiniMax H3 的 2/4 步蒸馏适配器，**DWD 档免 VAE 解码器**（最后一步直接出像素）。4 个适配器 + INT8 ConvRot 版（仅 ComfyUI）。许可 = H3 社区协议（衍生品，地域限制同源）。
- 帧数约束 **17n+5**（768×1344/243f 官方示例）；条件支持 text / 首帧 / 尾帧。
- 推理栈：**LakonLab v0.3**（diffusers，FP8 W8A8 + Sol 稀疏注意力）或 ComfyUI-piFlow v1.4.0。**作者警示 Comfy 路线质量劣于 diffusers**。
- 3090 基准（2 步 INT8 免 VAE）：768p 5s=38.5s / 10s=97.6s / 15s=186s；480p 5s=15.5s（NVIDIA 口径，勿与 Metal 直接比）。
- 与 vpipe 关系：**vpipe 无对应 stage、无接入迹象**（上游 repo 搜 pi-H3 = 0）。本机评估登记为看板 P34（低优先级）。
- 来源：huggingface.co/Lakonik/pi-H3 · github.com/Lakonik/LakonLab（c08dad1）· ComfyUI-piFlow changelog v1.4.0

## 2026-11-28 · 第 37 轮（K265–K278）

- **上游破静默**：`41a694a2`（11-26，122 文件 **+28,663/−418**）。H3 本体 `metal-minimax-h3-transformer.cc` **+1104/−113**；`train-lora-split.cc` **+1664**（双机 TP/DP）；`hyperflow-h3-flash.cc` 单测 **1093**。release 仍 v0.1.110 ⇒ 落后 **27 天**。
- **HyperFlow H3 Flash 收编**为一等公民（`dit_dir`）：见 `h3-ecosystem-map.md` §6。
- **lightx2v 8 步 v1.2**：混 rank + 逐模块 alpha：见 `768p-adapters.md` §5。上游 catalog 768p 条目 **10 → 17**。
- **新量化家族**：`QuantFunc/Minimax-H3-Quantfunc-4bit` = **SVDQuant 4-bit 首现**（`…int4_r128` 12,368,339,576 B / `…int4_r64_base` 11,950,870,730 B，FL2VA/Ref2VA 各两份）。
- **H3-Image 双档**：`KalponicStudio/MiniMax-H3-Image-Ojon`（GGUF Q4/Q5 + **W4A8 / W6A8** safetensors + 2 workflow）。
- **运行时尚**：`SarthakRawool/…-Image-MLX-8bit-LowMem`（270 文件）、`SceneWorks/minimax-h3-candle`（110 文件，Rust candle，`q4/` GGUF blocks）。
- **SageAttention sink 注意力（契约 311）**：缺 311 时**算错但不报错** ⇒ 必须查 `sage_sinks_marker` 探针，不可用就保持 dense。
- **sd.cpp H3 面零增量**（11-26 之后只有 LTX/FLUX/server 四条）。
- 口径：以上社区仓均为**存在性记录**，未核实画质；SVDQuant / W4A8-Image / hybrid 三档**待复现**。
