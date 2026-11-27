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

---

## 量化 × `__metadata__` 自由 JSON（2026-11-28 · 第 37 轮）

> 来源：HF 镜像 Range 读头（Flash FL2VA/Ref2VA、8step v1.2）+ 本机源码树 grep。

**新一类盲区：结构参数不再写在张量形状里，而写在 `__metadata__` 的自由文本里。** 它**不影响加载成功**，只影响结果对不对——比 int8 盲区更难发现。

| 文件 | metadata 键 | 内容 | 本机 |
|---|---|---|---|
| HyperFlow H3 Flash | `hyperflow` | `{"format":1,"variant":"fl2va","weights":"int8_convrot","blocks":47,"dropped_blocks":[6,21,22],"rank_multiple":64,"convrot_groupsize":256,"source":"fl2va_int8_convrot","source_revision":"9e9ed14b…"}` | 无解析（grep `dropped_blocks` = 0、`rank_multiple` = 0）|
| lightx2v 8step v1.2 | `alpha` / `floating_dtype` / `key_format` | `"128"` / `bfloat16` / `minimax-h3-diffusers` | `_meta_alpha` 读它，但**与逐模块 `.alpha`（16/128）冲突** |
| Pika comfy 版（K257） | `conversion` | 自然语言「preserves unit scaling and omits explicit alpha」 | 只用于人工判读 |
| Fusion pruned（K212） | （逐模块 `alpha` 张量） | `alpha == rank` 全体成立 | 按模块读 |

**三条纪律**：

1. **读头后第一件事：dump `__metadata__` 全部键**（不是只看 `format`）。结构化参数（块数、删块表、rank 倍数、组大小）大概率在里面。
2. **`alpha == rank` 有两种语义**：Fusion（倍率惯例）与 8step v1.2（训练惯例）——行为都是 `mul = 1.0`，但**来源不同**，靠数值分不开，要看 metadata 里有没有 `conversion` / `floating_dtype` 之类的说明。
3. **data 区偏移计算**：`绝对偏移 = 8（长度前缀）+ header_json_len + data_offsets[0]`。漏掉 8 字节会读出任意 bf16 位模式（如 `1.836e+37`）**且不报错**。

---

## `alpha` 的四义（2026-11-28 第 38 轮新增，含第 3 态）

同一个键名 `alpha`，在不同 publisher 手里是四种完全不同的东西，**张量名 / shape / dtype 全都无异样**，只能靠 `__metadata__` 区分：

| # | 语义 | 判据 | 例 | `mul` |
|---|---|---|---|---|
| 1 | **强度倍率** | `alpha == rank`，metadata 有 `conversion` 说明 | Fusion pruned（K212） | 1.0 |
| 2 | **训练惯例** | `alpha == rank`，逐模块标量 | 8step v1.2（K270）、4 步 v1.1（α128） | 1.0 |
| 3 | **per-tensor 反量化 scale** | `alpha ≈ 1e-5 ~ 1e-3` 且**与 rank 无关**；metadata `quantization: "int8_per_tensor_scales_in_lora_alpha_v1"` | SOLRICKS int8 refiner（K283） | 当强度算 ≈ 1.5e-6（**错**） |
| 4 | **空模板 / 用途说明** | 多数键为空串；有意义的键是 `positive_phrase` / `negative_phrase` / `image_effect` | `H3_speed_slider_1.1`（K286） | 恒 1.0（α==rank） |

**本机读取顺序（`runtime-lora.cc:446`）**：**逐模块 `.alpha` 张量优先** → 缺失才回落 `_meta_alpha`（`__metadata__.alpha` / `lora_alpha` / `lora_adapter_metadata`）。`scalar_f32`（`:48-82`）收 **F32 / F16 / BF16 / I64 / I32**。

⇒ **P61 结案**：8step v1.2 的 51 个 rank-16 模块 **`mul = 16/16 = 1.0`**，**不会**因 metadata `alpha="128"` 变成 8。

### 两条硬纪律

1. **补 I8 因子读取时必须加负向断言**：`alpha < 1e-2 && alpha != rank` ⇒ **拒该模块并告警**，否则 SOLRICKS 类件会从「静默跳过」变成「静默乘 1e-6」（比现在更隐蔽）。
2. **读 bf16 标量后必须自检**：`u16 << 16 → f32` 才对；按 IEEE half（`<e`）解会得到 29.0 → `2.96875` 这种「看起来合理」的小数**且不报错**。**自检断言：`alpha == rank` 应成立**（对 1/2/4 三态都成立），不成立先怀疑解码。


---

## 第 5 个量化家族：SVDQuant W4A4（2026-11-28 第 39 轮，K292）

`QuantFunc/Minimax-H3-Quantfunc-4bit:minimax_h3_fl2va_4step_quantfunc_int4_r128.safetensors`
`x-linked-size` **12,368,339,576 B / 2608 tensors / 274,992 B header**；BF16 1151 + I8 832 + F32 625。
50 块 + token_refiner 2 块 + `final_layer`，**208 个线性 × 9 键**：

| 键 | dtype | 形状（`blocks.0.attn.out_proj`） | 含义 |
|---|---|---|---|
| `qweight` | I8 | `[5376, 3584]` | 4 bit 码，**2 nibble / 字节** |
| `wscales` | BF16 | `[112, 5376]` | **group 64 沿 INPUT**（7168/64=112） |
| `wgsums` | BF16 | `[112, 5376]` | 与 `wscales` 同形（zero-point 侧） |
| `proj_down(_scale)` | I8 / F32 | `[7168,128]` / `[8]` | **SVD 下投影，秩 128**（r64 档 64） |
| `proj_up(_scale)` | I8 / F32 | `[5376,128]` / `[5376]` | SVD 上投影 |
| `resq_vr(_scale)` | I8 / F32 | `[7168,128]` / `[7168]` | **残余低秩分支** |
| `smooth_factor(_orig)` | BF16 | `[7168]` | 平滑因子（208 / 200 个） |

**四组算术核验**（全对）：`qkv [21504,2688] & wscales[84,21504]`（5376/64=84）、`fc1 [28672,2688] & [84,28672]`、`fc2 [5376,7168] & [224,5376]`（14336/64=224）、`out [5376,3584] & [112,5376]`。

⚠️ **`resq_vr` ≠ NVFP4 的 `weight_scale_2`**：前者是**低秩残余分支**（I8 `[·,rank]` + F32 行 scale），后者是**张量级二级 scale**（F32 标量/向量）。两者都叫「残余/二级」，**判「是不是同一族」不能看键名有 `res` 或 `scale_2`**。

**本机结论（K293）**：`strings` 对 `qweight`/`wgsums`/`wscales`/`proj_down`/`proj_up`/`resq_vr`/`smooth_factor` **七键全 0 命中**（`qweight` 只在 `qwen3` / `drama3` 两条 LLM 通路）⇒ **不支持，且失败在判据层不是解码层**（无 `adaln_t_table`、无 `blocks.N.attn.qkv_proj.weight` ⇒ `metal-minimax-h3-transformer.cc:657-661` 直接 fail）。

**社区自报（待复现）**：PSNR 23.7 dB（vs bf16 同 prompt 同 seed）、RTX 4090 768² 124 帧 3.2 s/步、SM75/86/89/120。

## 量化家族现在有 5 个（能力矩阵要 5 列）

| # | 家族 | 代表件 | 本机 |
|---|---|---|---|
| 1 | Fusion（LoRA 融合进 pruned） | `lightx2v/Minimax-H3-Turbo-Fusion` | 支持（K212/K250） |
| 2 | Kijai W4A8 混合 | `minimax_h3_ref2va_pruned_w4a8_mixed` 11.77 GB | 支持（K178/K179） |
| 3 | int8 TensorWise + ConvRot | `Comfy-Org …pruned_int8_convrot` 19.53 GiB | 支持（K180/K215） |
| 4 | NVFP4 | `KalponicStudio/MiniMax-H3-Image-Ojon` | **部分**：已装二进制缺 `nvfp4_dequant`（K269 前身） |
| 5 | **SVDQuant W4A4 int4** | `QuantFunc/…int4_r128` 12.37 GB | **不支持（判据层）** |

## 判「409 / 404 / 000」的三类假信号（2026-11-28 补第三类）

| 现象 | 真因 | 判据 |
|---|---|---|
| `http_code=000` 且 `time_total == timeout` | 网络不通 / DNS 无响应 | **不是 404**，换镜像重打 |
| `http_code=403` 且 `content-length` 约 183 / 191 | gated 仓的**错误体长度** | 不是文件体积；先读 `README.md`（200 可读 ⇒ 仓在） |
| **`http_code=404` 且响应体约 55 KB** | **URL 漏写 `/resolve/main/`** | **先用一个已知好件做对照**，对照不通就是 URL 形态错 |

⇒ 批测体积前**必跑一次对照**（如 `Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot`）。
