# vpipe 量化机制与已知缺陷

> 2026-11-13 ~ 11-14 实测 · 源码：`vpipe-lab/repo/vpipe/generative-models/quantize/model-quantizer.cc`

## 1. `model-quantize` 的关键字段

```json
{
  "id": "quant-dit",
  "type": "model-quantize",
  "iports": [ { "src": "fetch", "oport": 0 } ],
  "config": {
    "src_model": "Comfy-Org/MiniMax-H3-Ref2VA",
    "output_name": "local/MiniMax-H3-Ref2VA-8bit-dit",
    "target": "dit",
    "bits": 8,
    "group_size": 64,
    "quant_modulation": true,
    "skip_existing": false
  }
}
```

| 键 | 说明 | 坑 |
|---|---|---|
| `src_model` | **必须是注册表里的键**，不是磁盘路径 | 官方 `prepare-minimax-h3-8bit.vpipeline` 写的是 `Comfy-Org/MiniMax-H3`，而 fetch 注册名是 `Comfy-Org/MiniMax-H3-FL2VA` → **静默 drain**（issue #15，main 已修） |
| `output_name` | **相对路径**（`local/...`），不是绝对路径 | 给绝对路径会写到别处 |
| `target` | `dit` / `text_encoder` | **`linear_branch` 留空时在 Ref2VA 下会选到未下载的模型 → `no DiT; skipping`** |
| `bits` | 4 / 8 | 4-bit 对图像模型高危，见 §4 |
| `group_size` | 64 | |
| `quant_modulation` | 量化调制层 | 建议开 |
| `skip_existing` | 已存在是否跳过 | 省时间用 `true` |

---

## 2. 8-bit 的机制

- **仿射分组量化**，group size 64
- **AdaLN 调制层（13B / 33B）强制 8-bit** —— 这些层对精度敏感，不能降到 4-bit
- **AdaLN 按步数预烘焙成表**：日志里

  ```
  baked AdaLN for 4 steps (7 rows) -- 51 projections (13216 MB of weights)
      replaced by 64 MB of tables, and no longer streamed per step
  ```
  这是**巨大的空间节省来源**：13216 MB 的投影权重换成 64 MB 的查表。
  步数不同，烘焙出的行数不同（HyperFlow 8 步 → 24 rows → 221 MB 表）。

**本机实测**：Ref2VA DiT 535 tensors → 8-bit g64，**259 量化 / 276 直通，82 秒**。
FL2VA 编码器 902 tensors（350 量化 / 552 直通）。

---

## 3. AdaLN 烘焙与「步数」的关系（容易搞错）

| 场景 | 烘焙行数 |
|---|---|
| Pika H3 Flex 4 步 | 7 rows |
| Pika H3 Flex 6 步 | 11 rows |
| Ref2VA 6 步 | 17 rows |
| HyperFlow 8 步 | 24 rows |

**行数不是步数**：AdaLN 每个步要展开成若干行（条件行 + 调制行）。
这行数差就是「参考图进入序列」的内部证据 —— 本轮消融实验就是靠它区分
「有参考」与「无参考」两组。

---

## 4. 🔴 图像模型的 4-bit 量化：高危，建议跳过

上游 **issue #41**（v0.1.68，M4 16GB）实测：

| 模型 | 4-bit 结果 |
|---|---|
| **Z-Image-Turbo** | 1024×1024 跑 28 秒后 **GPU command buffer 错误**；更小尺寸直接硬挂 |
| **Qwen-Image-2.1** | **静默输出全透明图** |
| FLUX.2 klein | 正常（说明 4-bit 路径本身没坏，是特定模型族的问题） |

**最危险的地方**：量化**报成功、日志零警告** —— 极易误发布。

### 建议

1. **不量化图像模型**（Z-Image 31 GB + Krea 33 GB 都是官方公开权重，可随时重下）
2. 真要省空间，**优先删整个模型目录**，而不是量化
3. 如果确实要量化图像模型：**只用 8-bit，且必须目检输出**（检查是不是空白/全透明）
4. **4-bit 一律不做**

**8-bit 在 Z-Image / Krea 上没有被上游验证过** —— 本机这两家跑的是 bf16 原始权重。

---

## 5. 量化产物的目录结构（8-bit）

```
models/local/MiniMax-H3-FL2VA-8bit/
├── diffusion_models/       ← DiT（7 分片 + index.json）
├── text_encoders/          ← 编码器（6 分片 + config.json + tokenizer）
├── tokenizer/
└── vae/
    ├── minimax_h3_audio_vae_fp32.safetensors
    └── minimax_h3_video_vae_fp16.safetensors
```

**Ref2VA 与 FL2VA 共用同一个编码器和同一对双 VAE，只有 DiT 不同。**
所以量化 Ref2VA 时**只需要量化 DiT**，其余硬链接复用（见
`assets/prepare-ref2va-8bit-hardlink.vpipeline`）。

**实测省空间效果**：
- 官方全量流程需要 **117.8 GB**（66.28 GB bf16 + 重新量化 33 B 编码器 + 双 VAE）
- 硬链接复用后**净增 33 GB**
- 校验：`stat -f "%i %l"` 两边的 inode 相同（links=2/5）即为硬链接成功

---

## 6. 量化后怎么确认成功

```bash
# 1) tensor 数量合理吗？
grep -iE "quantized|tensors|passthrough" prepare-*.log

# 2) 产物在位吗？
du -sh models/local/MiniMax-H3-*-8bit

# 3) 能加载吗？（这才是真正的判据）
#    直接跑一次生成，看日志有没有 "residency probe" / "DiT residency ended at N of 50 blocks"
```

**判据**：日志出现
```
DiT residency ended at 24 of 50 blocks (9717 MB)
```
说明是**流式驻留**（不是全量常驻），24 GB 机器上正常。

---

## 7. 量化不会自动写 `model_index.json`

**量化只产权重，不产配置**。非 Comfy-Org 来源的权重无法写 config，
量化只完成一半（issue #49）。所以：

- 只量化官方 Comfy-Org 权重；
- 硬链接复用时，记得把 `config.json` / `index.json` 一起链过去；
- 量化后**一定要跑一次真实生成**验证能加载，不能只看日志说"量化完成"。
