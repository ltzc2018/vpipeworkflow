# `parent_model_type` 与当前 partition 不符的 LoRA 不被拒绝（与 manifest 型 adapter 规则不一致）

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
<!-- 全部条目均在本机复现，日志与命令可复现 -->

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
