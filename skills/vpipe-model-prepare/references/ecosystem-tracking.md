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

---

## 2026-11-28（第 38 轮）

- **★★★ `b25-49` 真相反转（推翻 K275 的推测）**：`MistyViolet/MiniMax_H3:diffusion_models/minimax_h3_hybrid_fl2va_ref2va_b25-49-bf16-pruned.safetensors` = **40,225,724,176 B / 532 tensors / 无 metadata / 无前缀**，**块 0–49 全在、逐块签名全同**，**F16 恰好 = 50 块 × 2（AdaLN weight[96768,8]+bias）+ final_layer 2**（与官方 pruned int8 的 F16 AdaLN 一致）；键集是官方 pruned int8（932）的**真子集**（缺 400 个 `comfy_quant`/`weight_scale`）⇒ **`b25-49` 是「块范围拼接」不是「块范围量化」**，本机 pruned 通路结构上能读。
- **★★ 官方 int8 video-VAE 体积修正**：`vae/minimax_h3_video_vae_int8_convrot` = **2,811,065,184 B**（旧记 3,171,670,912 B；文件自 10-29 未动，与社区 `mt_video` 仅差 712 B ⇒ 旧记录串位）。同仓：`fp16` 5,207,808,496 / `sol_vae_fp16` 3,596,335,728 / `sol_vae_int8` 1,988,306,504。
- **★★ 分发形态第 6、7 种**：⑥ **整机套装仓** `MistyViolet/MiniMax_H3`（66 文件：LLM GGUF + DiT + 23 LoRA + VAE + upscaler + 中文工作流目录，493 dl / **0 like**）；⑦ **无权重评测仓** `AI-KSK/minimax-h3-vbvr-v2-video-reasoning`（workflow + CHECKSUMS，9 场景 18 片段，外链 B 站 `BV1Bk1czaEu7` / YouTube `OO9yf4yLgng`）。
- **★ 空壳族**：`RunningHubAI/rh-*` 本轮新仓 **3/3 只有 `.gitattributes`**（`rh-crown-hyperpdmd-hd-3-4-minimax-h3-turbo-lora` / `rh-minimax-h3-turbo-4step-ckpt500-comfyui-lora` / `rh-minimax-h3-lora-2090958230839570433`）。⇒ `siblings ≤ 2` 一律先当空壳。
- **★ 跨平台文件数口径**：MS Turbo **31 项** vs HF **30 项**，差的是 `configuration.json`（非权重）；26 个 safetensors 逐名相同 ⇒ 比文件数先扣非权重项（K264 的兄弟坑）。
- **★ gated 仓判据补充**：`linkqpsfa` 两仓 `README.md` **200 可读**、权重 **403** ⇒ **先读 README，能读到即仓在、只是权重 gated**。


## 2026-11-28（第 39 轮 · K291–K300）

- **★★ 上游第 3 日静默（K291）**：HEAD 仍 `41a694a2`（commits per_page=5 与 37/38 轮逐位相同，已 **58 小时**无后继）；275 star（连续 8 日不动）/ 27 fork / 38,535 KB / 14 open issue / **PR=0**；release v0.1.110（11-01）落后 27 天；**#59/#53/#48/#17/#15 的 `updated_at == created_at`**（从未被碰过）。
- **★★★ SVDQuant int4 H3 首次剖到张量级（K292）**：`QuantFunc/Minimax-H3-Quantfunc-4bit` FL2VA r128 = 12,368,339,576 B / 2608 tensors；208 线性 × 9 键；**group 64 切 INPUT 维**、**2 nibble / 字节**、SVD 秩 128（r64 档 64）、`resq_vr` 残余分支。社区自报 PSNR 23.7 dB、4090 3.2 s/步（**待复现**）。
- **★★★ FP8 单文件 DiT 本机支持（K293）**：CLI 帮助 + `metal-minimax-h3-transformer.cc:160-176` + `diffusers-layout.h` 三处同证；`4step_v1.1_768p_fp8` = 34,023,114,720 B / 988 tensors / 950 个 `transformer_blocks.*` 键 = 全量 DiT。**同族 SVDQuant 却掉在判据层**（`strings` 7 键全 0）⇒ 第 4 类失败位「键名缺失层」。
- **★★★ 推翻 K281 两条（K296/K297）**：① 「丢 `norm_out`」是**跨形态误判**（`norm_out.linear` ↔ `final_layer.adaln_proj.linear` 改名，归一化后 `only_official = 0`）；② 「只是裁秩」实为 **裁秩 + pruned 转换**（`pruned_conversion` 三动作）⇒ 只能挂 pruned 基座。
- **★★ 官方 comfy 8step v1.2 比 diffusers 大 37%（K295）**：2,115,772,012 vs 1,543,291,302 B，全因 block-diagonal B（单块 qkv B 16.5 MB vs 5.5 MB）。
- **★ 其余**：`ibyteohdear` 1423 文件里 1412 个是打包的 `diffusers/` 源码（K298）；TE-PK `pk_lora` 无 sink 权重（K299）；sd.cpp 11-27 Q8_0 运行时 INT8（#2445），H3 面零增量（K300）。


## 2026-11-28（第 40 轮 · K301–K308）

- **★★ 上游第 4 日静默，且首次「`updated_at` 变 / `pushed_at` 不变」（K301）**：HEAD 仍 `41a694a2`（≈82 小时无后继）；`pushed_at` **`2026-11-26T23:20:21Z`** 未动，但 `updated_at` 走到 `11-27T18:01Z`。275 star（第 9 日）/ 27 fork / 38,535 KB / 14 open issue / **PR=0** / release v0.1.110 落后 27 天。⇒ **判上游活动改用 `pushed_at` 或 `commits[0].sha`，`updated_at` 会因 star 单独跳动**。
- **★★★ 第 6 个量化家族：GGML block（K302）**：`SceneWorks/minimax-h3-candle` 每个量化线性是 **3 维 `U8 [out, in/32, block]`**（Q4_1 20 B/32、Q8_0 34 B/32），**无 `.scales`/`.biases`**；`q8/transformer` **35.30 GB / 14 分片**、`q8/text_encoder` **33.71 GB / 1003 键（含 layers 50/51）**。本机拒载位置 = `linear_()` 找 `.scales` 得 nullptr → 回落 `to_bf16_` → 无 `comfy_quant` 记录 → **`not in the checkpoint`**。⚠️ **Q8_0 = 8.5 bpw ⇒ q8 档比 fp8 档（34.02 GB）还大 3.8%**。
- **★★★ MLX affine 件被「缺 config」挡住，补半份 config 反而更糟（K303）**：`SarthakRawool/MiniMax-H3-Image-MLX-8bit-LowMem` DiT **23,327,880,544 B（154 分片 + index）**，`adaln_t_table [1025,8]` + 融合 `qkv_proj` ⇒ **结构上完全合本机判据**，但 `transformer/config.json` **404** ⇒ `config_from_json` 第一步 `fail("cannot open")`。**若补一份只写 `bits:8` 的 config**：默认 `group 64` 把 `K` 翻倍（7168→14336）、`bits` 从 8 算成 **4.0**，**而 `scales` 列数在两种解读下都成立** ⇒ 尺寸校验全过 ⇒ **8 bit 码按 nibble 解（静默错值）**。
- **★★ 官方 H3-Image 三件套（K304）**：`pdd_fused_heads` **12,388,808 B / 2 张量**（`video_out.weight [6,96,5376]` = **6 个 step 专用头**）；`pdd_config.json` 六步显式 sigmas；`transformer/` **66,279,032,256 B / 531 键**，且 `transformer_diffusers/` **再存一遍**。`_class_name` 是 **`MiniMaxH3DiTModel`**（与 candle 的 `MiniMaxH3Transformer3DModel` 双拼写）。
- **★★ 适配形态第 7 种：独立 MLP bridge（K305）**：T8 `BUNNY_H3_ActionLogic_Bridge_V1_T8_Compat` = **22,046,928 B / 6 张量 F32**（5120→512→5120），`operation "lossless_metadata_wrap"`、`target_h3_layer "49"`、`teacher_val_cos 0.350` vs `val_rep_cos 0.996`。本机 `strings` 三关键词 **0 命中**，**无 hook 点**。
- **★★ 体积 vs 磁盘（K306）**：H3-Image 官方 DiT 66.28 GB / MLX 全量 42.6 GB / 本机可用 **35 GiB** ⇒ **最省的仍差 8 GB**；candle q8 68.9 GB（量化没换来收益）。
- **★ 零增量**：ModelScope `lightx2v/Minimax-h3-Turbo` **31 项 / 27 safetensors / LastUpdated 11-24T14:36Z（4 日）**，4 步 v1.0–v1.3 `_768p_bf16` **同为 1,383,677,808 B**（K151 边界维持，K307）；sd.cpp 11-27 仅 `3b0426f7` 显存记账，**H3 面第 3 日零增量**（K308）。官方 `MiniMax-H3-Image-PE` **首次登记**（提示词扩写器，Qwen3.8-27B 基底，fp4/sglang，22 文件 / 5,895 dl / 11-10 未动）。

## 2026-11-29（第 41 轮 · K309–K318）

- **★★ 上游第 5 日静默（K309）**：HEAD 仍 **`41a694a2`**（commits per_page=5 与 37–40 轮逐位相同，≈**106 小时**无后继）；`pushed_at` 仍 **`2026-11-26T23:20:21Z`**；**277 star（+2）/ 28 fork（+1）** / 38,535 KB / **14 open issue** / **PR=0**；release 仍 **v0.1.110（11-01）落后 28 天**；issue 评论合计仍 **9**，`#59/#58/#56/#53/#48/#17/#15` 的 `updated_at == created_at`。⇒ 第 40 轮「用 `pushed_at` 判活动」继续成立（`updated_at` 走到 `11-28T14:25Z` 纯 star/fork）。
- **★★★ 第 7 个量化家族：MLX ConvRot W8A8 / Sylvester 基（K310）**：`Joyboyreturns/MiniMax-H3-Image-MLX-w8a8`，`dit/dit.json` 显式 `{"format":"w8a8_convrot","bits":8,"rot_group":256,"hadamard":"sylvester","fused_qkv":true}`。**「错基反旋转」实测 relL2 2.06 / 余弦 −0.02** ⇒ 静默错值。⇒ 家族表加「旋转基声明位」。
- **★★★ 预烘 AdaLN 表 = 第 5 种 AdaLN 形态（K311）**：`dit/modulation/NN.safetensors` = `table BF16 [7,2,6,5376]` + `timesteps F32 [7]`（`norm_out [7,2,5376]`、`temb [7,2688]`）；`core.safetensors` 23 张量含 `pdd_proj_out.0..5 [96,5376]`。**此件无 `adaln_proj`** ⇒ `is_diffusers_layout()` 三条判据全挂。
- **★★ 融合投影只有「拆」没有「合拢」（K312）**：`minimax-h3-diffusers-layout.cc:246-248` 有 `attn.to_q → attn.to_qkv.q`，**无 `attn.to_qkv → q/k/v` 逆映射**；`gate_up_proj` 同理。MLX w8a8 件正好落在缺口上。
- **★★★ bnb LLM.int8 的第三套 scale 拼写 `SCB` + `weight_format`（K313）**：`addlabsviral/minimax-h3-combined` TE = 1954 tensors（`I8 448` + `F32 SCB 448` + `U8 weight_format 448`），`weight_format` 载荷是 **1 字节 `0x00` 不是 JSON**；本机 `grep SCB` = 0。**「有 I8 + 有逐行 scale」不能自动判成 ConvRot**（bnb 不旋转）。
- **★★ 第四个整机套装仓 + `base_model_relation: merge`（K313）**：`addlabsviral/minimax-h3-combined`（62 文件 / 1,144 dl / 自报 112 GB），`transformer/` index `total_size` **66,280,430,080 B**、TE **35,527,751,672 B**、`aoti/package/.../package.pt2` **仅 862,601 B**（编译产物，不含权重）。
- **★★ 混合量化「按块切档」第三例（K314）**：`chdp207/…W4A8_EdgeFP8` = 块 **2–47** W4A8（`I8 [21504,2688]` + `s_rel [21504,336]` + `codebook 16`）、块 **0/1/48/49** FP8；同仓 `…W8A8` = 同 4 块 FP8 + 中间 `I8 [21504,5376]` 整字节。**唯一分辨点是 `comfy_quant.format` 与 `shape[1]`**。⚠️ metadata 的 `nvfp4_reference_vessel` 指向**别处**的对标件 ⇒ metadata 字段不一定描述自身。
- **★★ sd.cpp 破 H3 静默（K315）**：11-28 共 **6 提交**，**`#2452`/`#2454`（d68f2883 / 51866c1a）把 Q4/Q5/Q2_K–Q8_K 接进 INT8 线性层运行时重量化**（`--linear-type i8`）、**`#2431`（3771ef24）fp8 权重上的 LoRA 按后端能力决定「立即合并 / 运行时应用」**。⇒ **sd.cpp 已有「GGML block → INT8 线性」的自适应桥**，正是 K302 判本机「要自写 GGML 解码器」的现成参考实现。
- **★★ 社区洪水与空壳量化（K316）**：`AI-KSK` 单组织 **139 仓**，H3 相关 **≥20 个在 9 分钟内批量上传**（全部 0 dl）⇒ 「仓数」不能当活跃度；`RunningHubAI/rh-*` 空壳累计 **5/5**；`Rex38rus/…GGUF`、`elismasilva/…custom_blocks` 亦空壳。**`Harsha001/MiniMax-H3-Image-ROCmFPX` 是 gated 第二档：连 README 都 403**（K251 那次 README 可读）。
- **★ 零增量（时效快照，明日复查）**：HF `MiniMaxAI/MiniMax-H3` `11-24T04:56Z` / **5,974,796 dl（+8）** / 7,449 like（+1）；`Comfy-Org/MiniMax-H3` `11-15T09:54Z` / **33,871,716 dl（+320）** / 2,899 like（+10）；`MiniMaxAI/MiniMax-H3-Image` 仍 `11-16T10:00Z` / 1,102,421 dl；`-Image-PE` `11-10T15:16Z` / 6,044 dl（+149）。ModelScope `lightx2v/Minimax-h3-Turbo` 仍 **31 项**、`8step_v1.2_768p_bf16` 仍 **1,543,291,302 B**（K151/K270 边界维持）。
