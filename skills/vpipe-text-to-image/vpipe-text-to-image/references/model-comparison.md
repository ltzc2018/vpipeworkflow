# Z-Image-Turbo vs Krea-2-Turbo 详细对照

## 规格

| 项 | Z-Image-Turbo | Krea-2-Turbo |
|---|---|---|
| 仓库 | `Tongyi-MAI/Z-Image-Turbo` | `krea/Krea-2-Turbo` |
| transformer 权重 | 24.6 GB（12.3B 参数 / 3 分片） | ~28 GB（12B / 28 blocks） |
| 整仓占用 | 31 GB | 33 GB |
| 参数量级 | 6B（Z-Image 家族） | 12B |
| 步数 | 8 步蒸馏 | 8 步（euler + simple） |
| **实测总耗时** | **42.5 秒** | **49.5 秒**（猫）/ 46.9 秒（商品图） |
| latent 生成耗时 | 36.92 秒 | 45.64 / 43.67 秒 |
| 每步耗时 | — | 5,458–5,705 ms |
| 引导方式 | **no cfg**（`guidance_scale = 0`） | 有引导 |
| 调度 | `simple (8 steps, shift 3 linear, rho 7)` | euler + simple |
| 输出 | 1024×1024，latent `[16, 128, 128]` | 1024×1024 |
| 声明峰值内存 | 31,311 MB | 34,014 MB |
| **实际流式驻留峰值** | **18,452 MB**（`vae-decode` 阶段） | **15,841 MB** |
| LoRA 依赖 | 无 | `mgwr/M87`（**只在 HuggingFace**）|

## 官方基准对照（Krea-2）

官方 `docs/KREA-2.md` 给 M5 Pro **20 核** 24 GB = **35 秒**。
本机 M5 Pro **15 核** = 49.5 秒。

核数比 1.33×、耗时比 1.41×，与官方「随 GPU 核数近似线性缩放」吻合。

## 24GB 上跑 25–30GB 权重的原理

官方文档原话：

> the 28 transformer blocks do not fit beside the conditioner's text encoder even on 24 GB — `plan_streaming` says stream there too

vpipe 的 **residency 流式加载**把权重按块流式换入换出。日志里能看到：
```
[INFO] memory landscape at launch: 24576 MB RAM -- ...
[INFO] resource-plan: ... MB of model weights declared before init
```

**不需要交换内存，也不会崩。** 这是 vpipe 在 24GB Mac 上跑 33B 视频模型的关键。

## 量化状态（重要）

| 位宽 | Z-Image | Krea-2 | 依据 |
|---|---|---|---|
| bf16 | ✅ | ✅ | 本机实测 |
| 4-bit (w4 g64) | ❌ **不可用** | 未测 | 上游 issue #41：GPU command buffer 错误后硬挂 |
| 8-bit (w8 g64) | ⚠️ **未被上游验证** | ⚠️ 同 | 量化报成功且零警告，但输出可能是坏的 |

**量化后必须目检输出是否正常。** issue #41 里 4-bit 的 Qwen-Image-2.1 会**静默输出全透明图**。

## 许可

| 模型 | 许可 |
|---|---|
| Z-Image-Turbo | Apache-2.0（issue #36 的提交者说明） |
| Krea-2-Turbo | 见官方文档；`mgwr/M87` LoRA 另计 |

## 选型建议

- **只求快、Apache 许可、要给视频链路预生参考图** → Z-Image-Turbo（42.5 秒，无 LoRA 依赖）
- **追求更强的构图与美学** → Krea-2-Turbo（需接受无 LoRA 版，或解决 HF 访问）
- **16GB 机器** → 两个模型的 bf16 都不建议；先量化到 8-bit 但**必须目检**
