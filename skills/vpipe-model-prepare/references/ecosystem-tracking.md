# 生态跟踪备忘（自动任务追加，只追加不删改）

## 2026-11-22 · pi-H3 权重发布（第 22 轮 · K117–K119）

- **HF `Lakonik/pi-H3`**（2026-11-21）：MiniMax H3 的 2/4 步蒸馏适配器，**DWD 档免 VAE 解码器**（最后一步直接出像素）。4 个适配器 + INT8 ConvRot 版（仅 ComfyUI）。许可 = H3 社区协议（衍生品，地域限制同源）。
- 帧数约束 **17n+5**（768×1344/243f 官方示例）；条件支持 text / 首帧 / 尾帧。
- 推理栈：**LakonLab v0.3**（diffusers，FP8 W8A8 + Sol 稀疏注意力）或 ComfyUI-piFlow v1.4.0。**作者警示 Comfy 路线质量劣于 diffusers**。
- 3090 基准（2 步 INT8 免 VAE）：768p 5s=38.5s / 10s=97.6s / 15s=186s；480p 5s=15.5s（NVIDIA 口径，勿与 Metal 直接比）。
- 与 vpipe 关系：**vpipe 无对应 stage、无接入迹象**（上游 repo 搜 pi-H3 = 0）。本机评估登记为看板 P34（低优先级）。
- 来源：huggingface.co/Lakonik/pi-H3 · github.com/Lakonik/LakonLab（c08dad1）· ComfyUI-piFlow changelog v1.4.0
