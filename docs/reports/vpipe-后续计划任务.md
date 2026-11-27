# vpipe 后续计划任务清单

> 基于 GitHub `tgo-app-dev/vpipe`（**当前基线 `main` @ `a6a1f53`，2026-11-23 17:54，85 文件 +17617 行**；已装 App `0.1 (9db5dd7*0)` 与本地源码树均落后于此；上游自 11-23 起持续静默，详见第 36 轮）；早期基线 `4dc36b7`（11-16）/ `33cda00` 见历史轮次。官方 `docs/MINIMAX-H3-zh-cn.md`（+ 英文版 `docs/MINIMAX-H3.md` 249 KB）、官方 release、issue（**至少 59 条**），以及 YouTube/社区实测资料整理
> 生成时间：2026-11-14 · **最近更新：2026-11-27 06:30（第 36 轮 · H3 VAE 侧首个 int8 ConvRot（组 64 不是 256）+ 本机 fast-VAE `float_dtype_` gate 结构性拒载 + Pika Flex 融合 QKV 混 rank 128/384 且 comfy 版丢 alpha）**
> 机器：Mac mini M5 Pro / 24 GB / 15 核 / macOS 27.2

---

## 状态看板（2026-11-27 06:30 更新）

| 轮次 | 状态 | 摘要 |
|---|---|---|
| **第 36 轮 · 2026-11-27 06:30 夜间知识同步（VAE 侧 int8 ConvRot + fast-VAE dtype gate + Pika 融合投影混 rank）** | ✅ **完成（P39 无头 CLI 第 13 次完整链路：06:30 槽准时触发，守卫 R=36）** | 上游静默**第 12 日**（HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star 连续第 3 日不动**）。**★★★ K254 首个 H3 VAE 侧 int8 ConvRot 件**：`cjbrigato/fast_h3_vae_v2_24l-INT8-CONVROT` = **1,623,016,374 B / 493 tensors**（I8 98 / U8 98 / F32 297），98 个量化层（96 块投影 + `x_embedder` + `proj_out`），**`convrot_groupsize = 64`（DiT 侧全是 256）**，`x_embedder` 唯一不旋转（`K=24`）；**★★★ K255 本机 fast-VAE 结构性读不了**：`with_tensor_`（`metal-minimax-h3-fast-vae.cc:96`）的 `float_dtype_` gate 只收 F32/F16/BF16 ⇒ **I8 在读之前即拒**，`proj_` 的 int8 分支是「bf16→int8 转换」而非「读 I8 码字」— 与 video-VAE（走到 `to_bf16_` 才失败）**同一族两个失败位**；**★★★ K256/K257 Pika H3 Flex 的 diffusers 版（624 tensors / 全 F32 / 2.58 GiB / 全 rank 128 / `.default.` 中缀）与 comfy 版（416 tensors / 全 BF16 / 1.82 GiB）是两种 rank 契约**——comfy 版 **`qkv_proj` rank 384 = 3×128 融合投影**，且 README 明写 **`omits explicit alpha tensors`** ⇒ 本机 `_meta_alpha=0` ⇒ `mul≡1`，**推断实际强度只有 1/3**（alpha 第六态）；**★★ K260/K261 两个判据**：`x-linked-etag` 是内容哈希（跨仓相同即同份，官方 `Pika-Labs` 与镜像 `vml12` 实为同份）、**`x-linked-size` 是 302 上唯一可信体积字段**（根治第 35 轮 ``-L`` 坑）；**★★ K262** `_quantization_metadata` 与 `comfy_quant` 层内可写法不同（`x_embedder`），本机优先 `comfy_quant`；**★★ K259** sd.cpp PR #2436 把 `convrot_groupsize` 缺省定 256「matching ComfyUI」，与本机 `Declared` 默认三方一致；**★★ K258** sd.cpp PR #2435 删掉独立 W4A8 matmul 而本机 `w4a8_to_i8` kernel 仍在（「同名 kernel ≠ 同功能」第 2 例）；**★ K264** ModelScope `Recursive` 真假让 Fusion 文件数 15 vs 48。**本轮无生成实验**（0 下载，9 次 Range/HEAD，23 min） |
| **第 35 轮 · 2026-11-27 04:30 夜间知识同步（latent upscaler v2 重训 + 跨模型 q_norm graft + `comfy_quant` U8 载荷）** | ✅ **完成（P39 无头 CLI 第 12 次完整链路：04:30 槽准时触发，守卫 R=35）** | 上游静默**第 11 日**（HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star 连续第 2 日不动**，四项与第 34 轮逐位相同）。**★★★ K245 社区 latent upscaler v2 是「同架构重训、非转存」**：`George0667/MiniMax_Temporal_Upscaler:…_v2_fp16` = **690,592,736 B / 322 tensors / 全 F16**，与 v1（SOLRICKS F16 转存 690,592,672 B）**key 集与 shape 逐名相同、数据区 sha 不同**（`6307f49c` vs `d1e3cbc7`）⇒ 本机 `config_from_weights` 四条自检全过、`dwconv [512,1,5,1,1]` 亦过 ⇒ **零改动可加载**，是**唯一「社区新权重 + 本机零适配」的后处理件**；⚠️ `v2/config.json` 写 `in_blocks 12` 而头里 18 ⇒ **结构只认 header**；**★★ K246 `v2_temporal` 多 4 个 `t_embed` 张量本机无分支且不报错** ⇒ 推断静默忽略（「加载成功≠全生效」第 3 例）；**★★★ K247 第四条调参工艺「跨模型 q_norm graft」**：`yichengup/…ltxqnorm-int8-convrot`（**19.53 GiB / 932 tensors**，1,141 dl）`__metadata__` 自述 `zspatial_graft = donor=Z-Image-Turbo blocks=30-49 dose=0.5`、`qnorm_graft = donor=LTX-2.5 blocks=30-48 dose=1.0`、`qnorm_pin = block 49 rms=5.0`、`adaln_splice = none (fl2va throughout)` ⇒ 格式全对但**语义跨模型、行为未知**；**★★★ K248** I8 refiner 的 rank 实为 **48–946 逐模块变化**（「r256」是标称值）；**★★ K249 `comfy_quant` 是 U8 的 72 B JSON**，且**同一 linear 的 weight(BF16)/bias(F16) 精度可不同**；**★★★ K250 Fusion pruned 4/8 步同字节但 sha 全异 ⇒ 不可原槽互换（K240 结案）**；**★★ K251 gated 仓首现**（siblings 可见、`resolve` 403，**183 B 的 content-length 是错误体**）；K244 sd.cpp 的 2D-conv upscaler #2357 仍 open ⇒ 后处理线与本机同档；K252 社区三条新线 + `jh27kim` 仓已删。新增 **P55（v2 真机复跑）/ P56（graft QC 方法）**。详见报告 18.44 节 |
| **第 34 轮 · 2026-11-27 02:30 夜间知识同步（逐投影混合量化 + DWD 第二份实现 + sd.cpp `-mlp` 反超 + 闭式投影换编码器）** | ✅ **完成（P39 无头 CLI 第 11 次完整链路：02:30 槽准时触发，守卫 R=34）** | 上游静默**第 10 日**（HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star 停涨**）。**★★★ K234 首个「NVFP4 W4A4 + INT8 ConvRot」逐投影混合 H3 DiT**：`Maximilian228/MiniMax-H3-pi-H3-NVFP4-GPTQ` 的 DiT = **14,302,909,922 B / 1,082 tensors**（U8 350 / F32 312 / BF16 220 / F8_E4M3 150 / I8 50），`qkv/out/fc1` 走 NVFP4（`weight_scale` swizzled `[N,336]` + F32 `weight_scale_2`）、`fc2` 走 INT8 ConvRot 逐行（`weight_scale [5376,1]`）、`comfy_quant` 两种原文、命名是**原生名 + `adaln_t_table [1025,8]`**；**★★★ K235 本机判定分两层**：源码 `scan(nvfp4=true)`+`resolve_nvfp4_(comfy=true)`+int8 `per_row` **都认**，但已装 `libvpipe.0.dylib`（`0.1 (9db5dd7*0)`）**`nvfp4_dequant` 命中 0**（kernel 源在 `affine_dequant_embed.cc.metal:2408`，通路 commit **41d2789/11-12**）⇒ **拒载形态是「host 无 NVFP4 widening kernel」，不是格式不认**；**★★★ K236 DWD 像素头第二份实现**（`dwd_pixel_refiner` 171 tensors vs K228 `pocis` 92 tensors，拓扑命名全不同，本机 `dwd` grep=0）；**★★★ K233 sd.cpp PR #2424 已合入（`439e77a5`）支持 `-mlp` 变体四种 connector** ⇒ 推翻 K190/K202 前提、本机落后一档；**★★ K237/K238 换编码器第三条路**（`Alissonerdx/TE-PK-Minimax-H3` 零梯度闭式 Ridge，单件 20–105 MB、5 张量）但**README R² 0.9935 vs metrics.json 0.0371 差两个量级** ⇒ 口径不可用；**★★ K239 K204 精确定位**（`is_diffusers_layout` 全满足 → 翻译启动 → 撞 `time_embedder.table` 无映射 → 返回 0，`folded_bias` grep=0）；K240 ModelScope Fusion 48 项（4/8 步 lite_r32 同尺寸未核 sha）；K241 检索坑（`lightx2v` 组织 404、镜像 `resolve` 404 分文件级/仓级）；K242 社区空壳仓 8/30。新增 **P53（kernel 能力矩阵）/ P54（latent 续接）**，P46 优先度上调、P52 改口径。详见报告 18.43 节 |
| **第 33 轮 · 2026-11-27 00:30 夜间知识同步（加速 LoRA 第五形态 + 混合因子拼写 + alpha 第五态 + 预烘 AdaLN 第三家）** | ✅ **完成（P39 无头 CLI 第 10 次完整链路：00:30 槽准时触发，守卫 R=33）** | 上游静默第 9 日（HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star(+1)**）。**★★★ K221 加速 LoRA 第五形态**：`vantagewithai/…:MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy`（**1,725,921,392 B / 578 tensors**）metadata 自述 `PDD head banks as base-relative pad-and-add reshape_weight LoRA`，带 4 个 `I64` `reshape_weight` 元数据张量 + `final_layer.video_out` **满秩 3072** 的 pad-and-add 对；**本机 `reshape_weight` grep = 0** → 该支**静默落空**（不在 `bind()` 枚举路径上，`_skipped` 未必涨）；**★★★ K222 同文件两种因子拼写并存**：`final_layer.*` 用 kohya（`lora_down/up`，4 对），`blocks.*`+`token_refiner.*` 用 peft（`lora_A/B`，258 对），而本机 `index_suffix_()` **取首个因子定整文件拼写**、`tensor_names()` 来自 `unordered_map` ⇒ **绑一半且不确定绑哪半**；**★★ K223 alpha 第五态**：`lora_alpha 64 == rank 64`（mul 1.0）但 `conversion` 明写 `alpha/rank folded into lora_B` ⇒ 体检须读自然语言；**★★ K224 可读对照件**：`MATLOWAI/…Variable-Clock`（**298,261,224 B**，kohya 拼写、rank16、200 模块，`ss_shift_video 12.0`/`shift_audio 3.0` 独立复现 K187 官方分布）；**★★ K225** ReFrame 视频重绘 LoRA（596 MB，kohya、契约内）；**★★★ K226 预烘 AdaLN 表第三家** `OpenVDN/vdn-minimax-h3-edge`（`step_N BF16 [6|9,32256]`，与 WaveCut 宽 8、`adaln_affine [8,2688]` **三种布局互不兼容**）；**★★ K227 交付三件套化**（22 GGUF + 4 加速 LoRA + 7 workflow，11,153 dl）；**★★ K228 像素头首带 PSNR 31.97**（92 tensors，本机无通路）；**K229 三线零 H3**（⚠️ sd.cpp #2435/#2436 带 INT8/W4A8 字样但只服务 LTX/通用）；**★★ K230 检索通路反转**：`huggingface.co` 全域不可达（`000`），**`hf-mirror.com` 的 `resolve`+Range 反而可用（206）** ⇒ 分流规则改「镜像优先」。新增 **P51（混合拼写容错）/ P52（像素头）**。详见报告 18.42 节 |
| **第 32 轮 · 2026-11-26 06:30 夜间知识同步（P44 第③前置判决 + 时调制剪枝两件拒载 + VAE int8 第三盲区）** | ✅ **完成（P39 无头 CLI 第 9 次完整链路：06:30 槽准时触发，守卫 R=32）** | 上游静默第 8 日（HEAD `a6a1f53` 距 commit ≈ **3.4 天**；release v0.1.110 落后 **26 天**；issue 14 全开且 #59/#58/#56/#55 均 0 评论；**PR=0**；**273 star** 不变）。**★★★ K212 P44 第③条前置判死**：Fusion pruned 逐模块 alpha **全体等于 rank**（adaln 32/32、out_proj+fc1+fc2 320/320、qkv 960/960）⇒ **`mul ≡ 1.0`，无需折算** → **P44 降为 2 条前置**（下载 + 改 `video_shift`）；**★★ K213** AdaLN 修正是「`diff_b` + LoRA 因子」分工（51 个 `diff_b`、**0 个 `.diff`**），与本机 `bind_pruned_adaln_` 契约吻合；**★★★ K210 WaveCut 时调制剪枝成独立工艺线**（H3-Image 135→94 GB 逐像素相同；ComfyUI 参考图路径 66.3→40.2 GB，作者 5/5 pixel-identical）；**★★★ K211 但两个 WaveCut 件本机都拒载**——**无前缀 + 无 `adaln_t_table` + AdaLN 宽 8 + 极窄 `time_embedder`**，`comfy_saved` 两条判据全不满足 → 新增「**第 5 类看着像 H3 打不开**」（one-hot 剪枝形态）；**★★★ K214 `pruned_w6a8` 双拒**（`format=w6a8_int8 group_size 32` 按名拒 + K/32 块 scale 按布局拒）；**★★★ K215 社区融合 int8 基座首次契约全符合**（Coffmeteor 932 tensors / 全前缀 / `adaln_t_table` / 逐行 `weight_scale` / ConvRot 256）**但属真人素材，只记存在性**；**★★★ K217 VAE int8 是本机第三条量化盲区**（VAE 走 `.scales`/`.biases` 仿射量化，不认 ComfyUI `.weight_scale`/`comfy_quant`，失效形态是**把 I8 码当值**，比 K199 静默跳过更危险）→ 新增 **P48**；K216 ref LoRA 路线、K218/K219 生态快照。详见报告 18.41 节 |
| **第 31 轮 · 2026-11-26 04:30 夜间知识同步（2K 后处理通路 + int8 适配器盲区 + 换编码器期望下调）** | ✅ **完成（P39 无头 CLI 第 8 次完整链路：04:30 槽准时触发，守卫 R=31）** | 上游静默第 7 日（HEAD a6a1f53 ≈ **2.4 天**；release v0.1.110 落后 **25 天**；issue 14 全开且 #56/#59 `updated_at == created_at` = **零触碰**；**PR=0**；**273 star** 不变）。**★★★ K198 本机 2K latent-upscale 链路早已完整**（`latent-upscale` stage + 3D-conv 网络 + catalog 两条条目），社区 SOLRICKS 件只是官方 bf16 的 **F16 转存（322 tensors / key / shape 全同）** → 「本机不支持 2K」作废；**★★★ K199 int8 适配器因子零支持且静默**（`runtime-lora.cc` 只认 BF16/F16/F32，`format_of("I8")=kNone` → `_skipped`）→ 新增 **P47**；**★★ K200 `alpha` 有两种互斥语义**（K188 整数倍率 128/8 vs SOLRICKS 量化 scale 3.96e-4）；**K201** SOLRICKS 量化代价 median 0.0824 / max 0.2841；**★★★ K202/K203 第二个换编码器方案 Qwen3.5-9B**（投影带 MLP 残差 + rank32 LoRA）但作者自评**成片 PSNR 仅 14.764 dB** → P46 期望下调；**K204** 两个 Fused 全量 pruned diffusers 仓（分片、无 `adaln_t_table`、AdaLN 烘进 `folded_bias`）本机打不开；**K205** 官方 pruned 基座旁挂 `adaln_affine`（`adaln_basis [8,2688]`）本机 grep=0；K206/K207/K208。**冲突①：P44 前置①（清 18.3 GB 半成品）作废**（磁盘 37 GiB、无 `.part`）→ P44 降为 3 条前置。详见报告 18.40 节 |
| **第 30 轮 · 2026-11-26 02:30 夜间知识同步（官方蒸馏配方 + alpha 语义换槽陷阱 + ClipProj 契约判定）** | ✅ **完成（P39 无头 CLI 第 7 次完整链路：02:30 槽准时触发，守卫 R=30）** | 上游静默第 6 日（HEAD a6a1f53 = 距 commit **2.36 天**；release v0.1.110 落后 **24 天**；issue 14 全开；**PR=0**；**273 star** +3）。**★★★ K186/K187 LightX2V 官方发布 H3 蒸馏 best practices**（`7fc25cd` / PR #1730，双任务双阶段，**FL2AV shift 6/3、Ref2AV shift 12/3**，dCM 1500 iters LR 2e-5 → PDMD+GAN 3000 iters）；**★★★ K188 4 步家族 v1.2/v1.3 的 `__metadata__.alpha` 从 128 → 8**（形状全同、强度 1/16）→ **K151 收窄**；**★★★ K189/K190 ClipProj**（sd.cpp 已实现，4B 编码器替 32B，15.7→4.5 GB）但**本机 connector 四条契约全不符** → 新增 **P46**；**K191 Fusion pruned 4/8 步同头不同体**；K192 社区 GGUF 家族（本机无路径）；K193 tuned int8 键集全同但 5 处 graft；**K195 P45 措辞修正**（fork 停在 10-21，需 rebase 而非「点 Merge」）；K196 sd.cpp RelayVSR KV graph-cut。详见报告 18.39 节 |
| **第 29 轮 · 2026-11-25 06:30 夜间知识同步（本机二进制实装确认 + W4A8 混合档 + VSA 缺口分级）** | ✅ **完成（P39 无头 CLI 第 6 次链路：06:30 槽准时触发；04:30 段未 sync 未推进，本轮补完闭环）** | 上游零增量（HEAD a6a1f53 = 距 commit **2.81 天**；release v0.1.110 落后 **24 天**；issue 14 全开 0 回复；PR=0；**270 star** +1）。**★★★ K178 本机 11-14 构建的 `libvpipe.0.dylib` 早已含 `h3_adaln_pruned_f16` / `w4a8_to_i8`** → 「本机不支持 pruned/W4A8」注销；**★★★ K179 Kijai `pruned_w4a8_mixed` 仅 10.96 GiB**（vs Comfy-Org int8 19.53 GiB）→ P44 下载量砍 47%；K180 同家族两种量化记录布局；**★★★ K181 FastH3-VSA 权重 21.33 GiB 已落地，但 issue #56（Able to merge 34 天）未合 → 本机整文件拒绝**；K182 官方仓误合/revert；K183 Comfy-Org 收 ControlNet Union；K184 社区 latent 域时间修复（待复现）。**新增 P45（VSA 跟踪）**；**修技能包分叉坑**（18.38.6 坑①）。详见报告 18.38 节 |
| **第 29 轮 · 2026-11-25 04:30 夜间知识同步（Turbo Fusion 融合适配器 + 本机 pruned 通路分层）** | ⚠️ **知识已并入、该槽未闭环**（04:30 槽准时触发但 `Upstream response stream was interrupted`，cb_exit=0 假成功、round 未推进、未 sync；K168–K177 由当日 06:30 补跑一并同步） | 上游静默第 5 日（HEAD a6a1f53 = 距 commit 1.77 天 / release v0.1.110 落后 **24 天** / issue 14 全开 / PR=0 / 269 star）。**★★★ K169「Turbo Fusion」**：LightX2V + Pika Flex + Larry v4 合成单 LoRA，4/8 步共用配方，**video shift 12**（与本机现役 6.0 冲突）；**★★★ K170/K171「pruned 通路分层」**：设 8 宽 + `.diff_b` 在本机可读（源码三道门逐一核对），只有 16 宽（H3-Tiny）被拒 → **K163 收窄**；K172 pruned_int8 19.53 GiB；K173 文档已把 pruned 写成一等支持；K174 catalog 仍无条目；K175 Lite r32 谱能量≠画质；K176 社区自建融合成惯例。**新增 P44（Fusion-pruned 本机实测，下轮首选）**。详见报告 18.38 节 |
| **第 28 轮 · 2026-11-25 02:30 夜间知识同步（H3-Tiny INT8 权重头零下载实测 + 上游第 4 日静默）** | ✅ **完成（P39 无头 CLI 第 4 次完整链路：02:30 槽准时触发、检索→固化→报告→sync→release 闭环）** | 上游静默第 4 日（HEAD a6a1f53 满 2 天未动、release v0.1.110 落后 **24 天**、issue 14 全开、PR=0、269 star 逐位同上轮）。**★★★ 本轮方法突破：用 HTTP Range 只读 safetensors header（0 下载）**——K162（H3-Tiny 四个 INT8 文件的 42 块 / `adaln_t_table [1025,16]` / 14B INT8 FFN 9984 / FewStep 双段低秩全量结构）；**K163（本机 pruned AdaLN 硬 gate：`time_dim != 8` 即 fail，非「缺 catalog」而是「loader 不认」）**；K164（14B INT8 9984 ≠ bf16 9792，ConvRot group 256 对齐）；K165（Tiny17B 与官方 pruned 50 块仅差「块数+曲线宽」两处）；K166（H3-Tiny 走 50 步/shift12，与本机 4/8 步不同赛道）；K167（LightX2V #1735 RelayVSR x4 显式画布）。P42 前置重写。详见报告 18.37 节 |
| **第 27 轮 · 2026-11-25 00:30 夜间知识同步（上游第 3 日静默 + 官方迭代方向量化）** | ✅ **完成（P39 无头 CLI 第 3 次完整链路：00:30 槽准时触发、守卫 RUN/R=27、检索→固化→报告→sync→release 闭环）** | 上游静默第 3 日（HEAD a6a1f53 两天未动、release v0.1.110 落后 **24 天**、issue 14 全开 0 回复 0 处理、PR=0、269 star）。K155（★★H3-Tiny 剪枝家族：AdaLN rank8 + 删 8/50 块 + FFN 9792，17B 不训练可用，INT8 18.1 GB）；K156（★★**官方 4 步线 10-20 后 36 天冻结、8 步线 v1.2 结构性变更不可换槽**）；K157（★★**本机 catalog 无 Tiny/causal 条目**）；K158（★LightX2V 因果流式音频历史 9 chunk）；K159（★ComfyUI MPS warp 绕法可迁移）。新增 **P42**。详见报告 18.36 节 |
| **第 26 轮 · 2026-11-24 06:30 夜间知识同步（P39 无头 CLI 首次跑完整链路）** | ✅ **完成（P39 实测第 5 次成功：检索→固化→报告→sync→release 全链路在无头 CLI 内闭环；04:30 槽第 4 次实测因流中断失败，兜底正确不推进）** | 上游第 2 日静默（HEAD a6a1f53、release v0.1.110 落后 22 天、issue 14 全开、PR=0）。K148（静默复核）；K149（★a6a1f53 行数口径冲突 19494 vs 17617）；K150（权重仓 1.79M 下载/75.8 GB/8 天未更新→无 v1.4）；K151（★★4 步全版本字节同构→v1.3 可原槽 A/B）；K152（★★社区「4 步不够」口径，与本机静态夹具冲突）；K153（★★DWD 原论文 arXiv 2611.22287：warping −23%、FID 1.55→1.43）；K154（★★★P39 04:30 失败/06:30 成功的对照实证）。详见报告 18.35 节 |
| **第 25 轮 · 2026-11-24 00:06（用户手动触发 00:30 槽失败 → 主对话代跑）** | ✅ **完成（★★★ 首次 daemon.log 级坐实「会话空壳/unknown_interrupted」根因：非配置/非脚本错，是自动化会话被主对话抢占中断；force→检索→固化→sync→release 全链路代跑闭环）** | 上游静默约 14h（HEAD a6a1f53、release v0.1.110、issue 14 全开零回复、PR=0）。K139（会话空壳日志实证）；K140 FlashGen 4-step LoRA（VSD rank64+base_schedule）；K141 Character Swap LoRA V1.5；K142 Turbo 三档耗时+双 shift 印证；K143 vLLM 双分区（本机不采信）。K140–143 社区二手待复现。详见报告 18.29 节 |
| **第 24 轮 · 2026-11-23 23:55（4 槽立即运行/自动运行可执行化 + 逐个测试 + 用户修正去重）** | ✅ **完成（★★★ nightly_guard.sh：判断逻辑从 prompt 文本升级为可执行+可测；4 槽 × 4 场景测试全通过；★ 23:55 按用户要求去掉「今天已跑跳过」，点击/到点均执行）** | 上游静默约 6h（HEAD a6a1f53）、release v0.1.110。K136/K137（issue #59 RelayVSR_X2 原生 2× 未合入）、K138（守卫脚本）。**修正后语义**：4 槽独立执行，仅并发锁(exit=11)拒绝，否则 check/force 都 RUN(0)；last_run 仅审计。修两处 bash 坑。详见报告 18.27 + 18.28 节 |
| **第 23 轮 · 2026-11-23 23:20（04:30 槽故障诊断后手动补跑）** | ✅ **完成（★★★ 上游 a6a1f53 重大增量 +17617 行：vpipe 原生 pi-H3 2/4 步适配器 + DWD 免解码 + LoRA 训练）** | 04:30/00:30 槽今天未触发（会话空壳/无文件，非配置错误=本机调度架构限制）→ 手动补跑。增量 K127–K135：HEAD d347808→a6a1f53（11-23 17:54）；pi-H3 适配器原生进主仓（K128）；DWD 落地 f32 0.0053（K129）；train-lora + 调制表折叠 26GB→174MB（K130/K131）；Dials（K132）；三处内存记账修正（K133）；8 条新流水线（K134）；release 仍 v0.1.110 差距扩大（K135）。**★★★ 推翻 K121**（「上游零迹象」寿命仅 1 天）。详见报告 18.26 节 |
| **2026-11-23 21:23 续作（768p Negative + RelayVSR 保真重制）** | ✅ **完成** | 768p 重生成换场景且同尺度清晰度 −32.6%（K123，不交付）→ RelayVSR 2× 保真重制 960p（16.6s，锐度×2.7，同场景，K124，交付）→ ★★★ P33 判据重大修订：周期脉动源片固有非超分引入（K125/K126），绝对阈值作废改比值判据。详见报告 18.25 节 |
| **第 22 轮 · 2026-11-22 10:38 夜间知识同步（手动触发·双槽位精简后验证轮）** | ✅ **完成（★★★ pi-H3 权重按承诺窗口发布：2/4 步 + 免 VAE 解码器 DWD；上游 vpipe 完全静默）** | 检索 6 类源（GitHub API ×5 含 PR search 复核 + HF 模型页全文 + ComfyUI-piFlow changelog + ModelScope API + WebSearch ×4）。**增量**：① **K117 pi-H3 已开源**（Lakonik/pi-H3，11-21，4 适配器 + INT8 ConvRot，继承 H3 社区许可）；② K118 ComfyUI-piFlow v1.4.0 支持 + 作者警示 Comfy 路线质量劣于 diffusers；③ K119 LakonLab v0.3.0 + 3090 实测基准（768p 5s=38.5s@2步INT8）；④ K120 Suno H3Move 上线 + H3 生态规模量化（100 天 1400+ 衍生 / 1.4 亿次下载）；⑤ K121 上游零增量（HEAD d347808 / PR=0）；⑥ K122 ModelScope 基线维持。**实验**：无（pi-H3 复现需 LakonLab 栈，登记待验证）。详见报告第 **18.24** 节 |
| **第 21 轮 · 2026-11-22 01:00 夜间知识同步** | ✅ **完成（上游 d347808 + h3.c 对比表进 README 门面，本机同档官方口径 5m29s 首次落表）** | 检索 10 类源。**增量**：① HEAD→`d347808`（LLM/VLM 侧，视频线零变化）；② h3.c 对比表进 README 门面：M5 Pro 24GB VPIPE 5m29s vs h3.c 7m11s（快 24%，本机同档）；③ 该表历史上有过口径刷新（引用必须带 commit/日期）；④ #59 已实现但未关 issue。**实验**：无（P30 留待 02:30/04:30 时段）。详见报告第 **18.23** 节 |
| **第 19 轮 · 2026-11-21 06:30 夜间知识同步** | ✅ **完成（ABI 8 契约确认 + SenseNova/Ming 插件特性盘点 + 上游静默 4 日）** | 检索 6 类源。**增量**：① 确认 SenseNova/Ming 插件需 ABI 8；② 发现 i8_gemm 加速投影层 1.46x 但受限于 I/O；③ 确认 Ming-Image 通过 prompt 触发 RGBA 通道。**实验**：无。详见报告第 **18.19** 节 |
| **第 20 轮续作 2 · 2026-11-21 21:15 P32 RelayVSR 2× 真值对照判决** | ✅ **完成（P32：2× 档 =「向真值收敛的欠估增强」纹理量 = 真值 0.785×，与 4× 的 1.76× 编造方向相反）** | P22 同源猫片三臂 640×384 对比；SSIM(B vs 真值)=0.9015 / 锐度 = 真值 91%；逐位确定性第二素材复证；15 帧周期检验 25 帧素材统计功效不足 → P33 改 ≥45 帧。详见报告第 **18.22** 节 |
| **第 20 轮续作 · 2026-11-21 19:10 P29 RelayVSR 2× 真机判决** | ✅ **完成（P29：2× 跑通 0.12s/帧 + 逐位确定性 + 细节 +184% 但 frame diff +18.3%）** | 权重 5.29 GB 下载（ModelScope Comfy-Org/RelayVSR 子目录）；124 帧超分 14.6s，峰值 7153 MB；纹理量 33.0→93.6 (+184%)、纹理/噪点比 130.2；**autotune:false 逐位复现成立**（修订 13.5）；15 帧周期脉动疑似（peak 1.43 未过线）。详见报告第 **18.21** 节 |
| **第 20 轮 · 2026-11-21 17:26 夜间知识同步（02:30 时段补跑）** | ✅ **完成（上游静默被打破：d72c22f 三大变更 + P28 调度器端口判决）** | 检索 8 类源。**增量**：① 上游新 commit `d72c22f`（114 文件 +50265 行）：RelayVSR 原生 2×（#59 落实，int8 档 4.3 GB）、H3 接入 ComfyUI 四种 flow 调度器（iport 4 真读）、`lcm`≡`dmd`（印证 P18）；② **P28 实验**：scheduler 端口生效，sgm_uniform HF jitter −3.77%（不作为沸腾解法），σ 网格细扰同场景（首帧 SSIM 0.952）；③ **跨 build 锚点作废**：d72c22f 上历史锚点逐位不同（首帧 SSIM 0.344=换场景），新 build 自身确定性成立。详见报告第 **18.20** 节 |
| **第 18 轮 · 2026-11-21 04:30 夜间知识同步** | ✅ **完成（P13b 终审判决 + 核心仓库 5 日静默确认 + 磁盘空间回归）** | 检索 21 源。**增量**：① 确认 `er_sde` 对 H3 视频稳定性有负面效应 (+12.09% jitter)；② 确认主仓库核心 ABI 已锁死，功能外溢至插件。**实验**：P13b (5 臂)。详见报告第 **18.18** 节 |
| **第 17 轮 · 2026-11-21 02:30 夜间知识同步** | ✅ **完成（上游 5 天代码静默确认 + 插件解耦架构定论 + P17 补偿预研）** | 检索 5 源。**增量**：① 主库连续 5 天零提交，架构进入插件扩张期；② P17 Gain/Bias 补偿路径确立。**实验**：无。详见报告第 **18.17** 节 |
| **第 15 轮 · 2026-11-20 19:15 夜间知识同步** | ✅ **完成（LTX-2.5 插件发布 + 潜空间 2x 超分路径确认 + 官方性能 5分00秒 判决）** | 检索 5 源。**增量**：① vpipe-ltx-2.5 插件正式支持 22B 模型；② 确认潜空间 2× 超分 (26.9 dB) 高保真路径；③ 官方 M5 Pro 实测 H3 124帧 仅 5分00秒。**实验**：无。详见报告第 **18.15** 节 |
| **第 14 轮 · 2026-11-20 04:30 夜间知识同步** | ✅ **完成（VPIPE 基准对账 + SLA 机制拆解 + 磁盘红线触发）** | 检索 12 源。**增量**：① 确认 VPIPE 胜 h3.c 21-25% 旗舰性能；② SLA 稀疏注意力提速 2.5x 机制拆解；③ 确认磁盘 4.2G 触发红线。**实验**：无。详见报告第 **18.14** 节 |
|---|---|---|
| **第 10 轮 · 2026-11-19 21:00 夜间知识同步** | ✅ **完成（M5 加速开关发现 + 上游静默期确认 + 性能基准刷新）** | 检索 5 源。**增量**：① 发现 i8_gemm/sage_attn/sol_attn 等 M5 专项优化；② 确认 M5 Pro 性能基准 5m00s (124f)；③ 上游 3.5 天零提交。**实验**：无。详见报告第 **18.11** 节 |
| **第 9 轮 · 2026-11-19 20:55 夜间知识同步** | ✅ **完成（SLA 生态发现 + vpipe 适配缺口确认 + 上游静默期确认）** | 检索 8 源。**增量**：① 发现 SLA (Sparse-Linear Attention) 4步 768p 路线；② 确认 vpipe 暂无 SLA 算子；③ SiliconFlow API 确认忽略 negative_prompt。**实验**：无。详见报告第 **18.9** 节 |
| **第 8 轮 · 2026-11-18 23:50 夜间知识同步** | ✅ **完成（vpipe 支持 DiT 分布式运行 + H3 索引修复 + PDD 规约固化）** | 检索 5 源。**增量**：① vpipe 支持多 Mac 拆分 DiT 推理；② 修复 150k+ 行长序列索引溢出；③ PDD 采样器必须固定 euler/CFG 1.0；④ lightx2v 768p 官方 shift 修正为 6.0/3.0。**实验**：无。详见报告第 **18.8** 节 |
| **第 6 轮 · 2026-11-18 12:56 夜间知识同步（P22 判决，原误标为第 8 轮 23:50，2026-11-27 校正）** | ✅ **完成（★★★ P22 判决：FlashVSR 原生 Metal 4× 超分真机跑通 + 「它是细节生成器，不是保真放大器」）** | 检索 **18 类源**（GitHub API × 5：commits/releases/**issues+PR**/**branches**/**owner 全部仓库** + ModelScope API × 2 + **本地源码 × 5**：`flashvsr-model-config-stage.cc` / `flashvsr-src-encoder-stage.cc` / `flashvsr-family.h` / `model-registry.cc` / `flashvsr-src-encoder` + 上游官方文档 × 2（`platform.minimax.io` 模型页 + self-host 指南）+ SiliconFlow 公告 + 社区 × 10）。**上游仍零增量**（HEAD `4dc36b7` / release v0.1.110 / 31 issue / **0 PR** / **1 branch** / #55 开放 30 天 0 评论）；ModelScope `lightx2v/Minimax-h3-Turbo` 仍 31 文件 / 26 safetensors。**★ 四个关键增量**：① **★ P22 判决（见下）**；② **★ MiniMax H3 Max = fal.ai 托管、权重未开源**（官方模型页 + 3 源印证）→ 「生态有」但只有托管形态；③ **★ SiliconFlow 2026-11-10 上线 MiniMax-H3 官方 API**（`duration` 5–15 s / `resolution` 480p|768p / `images` 用 `role`），且 **`negative_prompt` / `image_size` 传入不报错但被忽略** → **跨生态印证「静默失效」是通病，不是 vpipe 专利**；④ **★ 官方 self-host 指南明写 H3 部署基线「excludes H3-Context-IR and the complete 2K Workflow」** → **第 1 轮「2K 未开源」是官方口径，不是本实验室的悲观**。**实验（P22 · FlashVSR v1.1，25 帧 / 1280×768 / 45.5 s）**：**★ 本实验室第一次真机跑通上游自带原生 Metal 视频超分**（拖了 3 轮，本轮磁盘回升到 32 GiB 才解锁）。**★ 三条量化判决**：**① 它确实生成了插值给不出的细节**（纹理量 13.00 → 163.80 = **12.6×** / +1160%，且纹理/噪点比 153.7 **高于**真值 144.3 → 是结构化毛发纹理不是噪点）；**② 但它不是「还原」而是「编造」**（对原始 768p 的 SSIM **比纯插值低 0.0506**、PSNR **低 4.05 dB**；真值纹理量的 **1.76×** 就是编造量）；**③ 代价是时序不稳**（frame diff **+37.4%**，HF jitter 0.3066→0.3410，**比真值本身还高 6.1%**）。**★ 复现性判决**：`framemd5` **不同**（不逐位相同）但**指标漂移 ≈ 0**（+0.02%/0.00%/+0.01%/−0.00%）—— 原因：**flashvsr 家族的 sampler/scheduler/negative 全部惰性** → **`autotune` 无可调对象、日志无回显** → **修订第 3 轮 11.1 的适用范围**。**★ LFM3-VL 复核**：Q1场景 ✅ / Q2 纹理粗判 **❌ 说反了**（已知缺陷 ② 再现）/ Q3 1:1 判读 ✅ **正确指出「原图里没有的、像 AI 编造的纹理」** / Q4 运动漏检。详见报告第 **18.6** 节 |

### 待验证登记（第 36 轮 · 2026-11-27 06:30 更新）

| 任务 | 优先级 | 前置 | 说明 |
|---|---|---|---|
| **P57 ★★★ fast-VAE 的 int8 通路（新）** | **高（体积减半的唯一路径）** | 需改 `metal-minimax-h3-fast-vae.cc`（`with_tensor_` 的 `float_dtype_` gate + `proj_` 的 I8 分支） | **K254/K255**：`cjbrigato/fast_h3_vae_v2_24l-INT8-CONVROT` = **1,623,016,374 B**（原 fast-VAE bf16 ≈ 3 GB）⇒ **磁盘/显存减半**。但本机 `with_tensor_`（`:96`）在**读之前**就按 dtype 拒（`:73-76` 只收 F32/F16/BF16），`proj_` 的「int8 分支」是 **bf16→int8 转换**而非读 I8 码字。**移植点**：`convrot_row_scales_`（transformer 侧）+ I8 码字读 + `convrot_group_ok(64)`（已验证合法）。**先做可行性判断**：确认 `to_bf16_` 在 fast-VAE 只被 `proj_` 用 |
| **P58 ★★ 融合投影的 alpha 语义（新）** | 中（低成本、结论确定） | `comfy/loras/pika_h3_flex_fl2va_comfy_bf16`（1.82 GiB）+ `fl2va/adapter.safetensors`（2.58 GiB），**本机两个都认** | **K256/K257**：comfy 版 `qkv_proj` rank **384 = 3×128**，且 README 明写 **omits explicit alpha** ⇒ 本机 `mul≡1`，推断**实际强度只有 1/3**。验证：同 seed 两臂各跑一次，比 frame diff / 首帧 SSIM。若 comfy 明显弱 ⇒ 坐实；若相同 ⇒ 说明 Pika 训练时融合投影本就是 384（**则 K257 应撤回**） |
| **P55 ★★★ latent upscaler v2 真机复跑（新）** | **高（成本最低的一条新能力）** | 下 `George0667/MiniMax_Temporal_Upscaler:…_v2_fp16`（**690,592,736 B**）+ 可选 `…_v2_temporal_fp16`（690,601,656 B） | **K245**：v2 与 v1 **key/shape 逐名相同、数据区 sha 不同** ⇒ 同架构重训；本机 `latent-upscale` stage 四条自检全过，**零改动可加载**。做法：取上轮同源 768p 片（或现成 mp4 的 latent），`scale 2` 跑 v1 / v2 两臂，比锐度、纹理量、首帧 SSIM。**第二臂（必做）**：另跑 `v2_temporal`，与 v2 逐位比对 —— 若**逐位相同**即坐实 K246 的「`t_embed` 静默忽略、时间插帧不发生」。成本约 690 MB 下载 + 2×3 min 后处理 |
| **P56 ★ 跨模型 graft 件的 QC 方法（新）** | 中（方法先于结论） | 无（先定判据，不必下载 19.53 GiB） | **K247**：`attn.q_norm.weight` 是普通逐通道增益，本机按名加载**不会拒**，但 graft 来源（LTX-2.5 / Z-Image）与 H3 的 norm 语义不同 ⇒ **格式全对、行为未知**。判据不能沿用 SSIM（它衡量的是「像不像原片」），要**运动一致性 + 撕裂/拖影检测**：快动作段的 frame diff 方差、边缘断裂计数、与 K224 的 `Variable-Clock` 对照。**先写判据脚本再决定是否花 19.53 GiB** |
| **P53 ★★★ 「已装二进制的 kernel 能力矩阵」（新）** | **高（每轮都用到，零成本）** | 无（只读 `strings`） | **K235**：`libvpipe.0.dylib`（`0.1 (9db5dd7*0)`）里 **`nvfp4_dequant` 命中 0**、`w4a8_to_i8` / `h3_adaln_pruned_f16` 命中；而源码树三条通路全在（NVFP4 自 **41d2789 / 2026-11-12**）。⇒ 判「新量化件能不能跑」的**第一个动作应是 `strings` 查 kernel 名，而不是读 README 或 grep 源码**。**做法**：`strings -a "$APP/Contents/Frameworks/libvpipe.0.dylib" \| grep -E "^(nvfp4_dequant\|w4a8_to_i8\|h3_adaln_pruned_f16\|affine_dequant_.*\|int8_.*)$"` 出一张表，与 `fp8-expand.cc` / `fp8-layout.cc` 的 `_lib.function("…")` 列表比差。**收益**：本轮若先查表，K234 那件 10 分钟就有结论 |
| **P54 ★ 长视频 latent 续接（新，低）** | 低（通用缺口，不阻塞 H3 主线） | 无（只记格式） | **K233**：sd.cpp **PR #2414（open，未合）** `--save-latent` / `--continue-latent` / `--pin-frames`，格式 `int32 magic "43LT"` + `version` + `ndim` + `shape[ndim]` + 原始 float（打包布局 24 视频通道在前 + 1 音频通道）。动机：像素帧续接有构图漂移且**每段音轨重启**。本机 `save-latent\|continue-latent\|pin-frames` grep = **0**。⇒ >10 s 交付都会撞到，但要等上游合入或自研打包格式 |
| **P51 ★★ 混合因子拼写容错（新，中）** | **中（挡住「社区最新 8 步 LoRA」的评估）** | 无（纯源码改动，零下载） | **K222**：`vantagewithai` 的 `Acc-8Step_pruned_comfy` 在同一文件里并存两种拼写——`final_layer.*` 用 kohya（`lora_down/up`，4 对）、`blocks.*`+`token_refiner.*` 用 peft（`lora_A/B`，258 对）。本机 `Adapter::index_suffix_()`（`runtime-lora.cc:308-330`）**取扫到的第一个因子张量**决定整文件后缀，而 `tensor_names()` 源自 `std::unordered_map`（`metal-llama-weights.h:296`）⇒ **迭代序不定**。两种结局：扫到 `lora_A` → 258 对绑定、4 对落空；扫到 `lora_down` → `lora_B` 被算成 `lora_up`、**258 对全失配**。**修法**：① `resolve_()` 对 A/B 各自试两种后缀（而非全文件唯一）；② 或 `index_suffix_()` 统计各拼写出现次数取多数。改动小、风险低。**验收**：同一 build 连跑两次，`modules` 计数必须一致且 ≈262 |
| **P52 ★ 像素头（DWD 推理侧）通路（新，低）** | 低 | 无（只记存在性） |  **K228**：`pocis/MiniMax-H3-Video-PixelHead`（**95,858,352 B / 92 tensors / 全 F32**，bf16 版 49 MB）metadata `arch minimax_h3_video_pixel_head_v2`、`d_feat 5376`、`d_lat 96`、`depth_s4/s8/s16/s32 1/2/2/2`、`frame_per_token "1,4,4,4,4"`、`latent_input "x0_hat_vid_1x2x2"`、**`eval_psnr_db 31.97`**、作者自标 `experimental_preview_v0.2.0_not_recommended_for_production`。本机 `pixel_head` grep = **0**，且需 `x0_hat_vid_1x2x2` 这类内部张量 hook 点 ⇒ **不做私改**，等上游或第二个独立实现 <br><br>**【第 34 轮 K236 改口径】** 已出现**第二份互不兼容实现**：`Maximilian228/MiniMax-H3-pi-H3-NVFP4-GPTQ:loras/pi_h3_4step_dwd_head_gptq_int8`（**171 tensors**，全 `dwd_pixel_refiner.*` + `dwd_norm_out.*`，`feature_expand` / `first_frame_proj_out` / `register_tokens`；无 `lora_*`）。两家**张量名与拓扑都不同** ⇒ P52 从「等一个实现」改为「**两家不收敛，等上游统一，不私接**」；本机 `dwd` grep = **0**，`_step_out` 只是多步输出 Linear 数组，不是像素 refiner。 |
| **P48 ★★ VAE int8_convrot 通路（新）** | **中（首个「静默错值」级缺口）** | 无（**解成 BF16 是最省事的验证路径**） | **K217**：社区 4 个 int8 VAE（lite **1.04 GB** / lynnreal 2.14 GB / mt 2.81 GB / 官方 3.17 GB，README 自报 decode **~2×**）带 `I8+U8 各 48` + 标量 `weight_scale` + `comfy_quant {"format":"int8_tensorwise","convrot":true,"convrot_groupsize":256}`；但本机 `metal-minimax-h3-video-vae.cc:852-870` 只认 **`.scales` + `.biases`**（`_quant_bits` 4/8、`_quant_group` 默认 64，来自 config 的 `quantization.{bits,group_size}`）。**失效形态**：`_quant_bits == 0` → 直接 dense 路径拿 I8 张量 → **把整数码当像素值 → 画质崩塌、日志无错**。三条路：① `linear_()` 加 comfy 分支；② **转换脚本解成 BF16**（lite VAE 1.04 → 约 4 GB，本机可接受，且能先验「lite VAE 画质是否可接受」）；③ 等上游 |
| **P47 ★ int8 适配器因子通路（扩写为「三处盲区」）** | 低→**中**（因 P48 同族且更危险） | 无（只影响社区 int8 LoRA / int8 基座 / int8 VAE） | **K199**（适配器）：`runtime-lora.cc` 的 `take_()` / `take_f32_()` 只分支 BF16/F16/F32，`format_of("I8")=kNone` → `_skipped` → 静默不生效。**K200**：SOLRICKS 那种 `.alpha` 是量化 scale（3.96e-4），`alpha/rank` 折出约 1e-6。**K214**（基座 w6a8）：名字门 + K/32 块 scale 布局门双拒。**K217**（VAE）：命名契约不同，失效是**错值**而非跳过。最低成本仍先加 warning（`_skipped > 0` 时 `session()->warn`），**但 VAE 那条必须优先修** |
| **P46 ★★ 换文本编码器（优先度上调，必须先定方言）** | **中→中高**（sd.cpp 已反超） | **K233**：sd.cpp **PR #2424 已合入**（`439e77a5`，11-26T13:12:17Z），`mmh3-8b-ClipProj{,-mlp,-v3.1,-v3.1-mlp}` **四种全支持**；本机 `minimax-h3-text-encoder.cc:655-690` 仍只有 **6 张量、无 MLP** 单一方言。**K237/K238** 出现第三方言（闭式 Ridge，4 张量、无 std/sink），但同仓 README R² 0.99 与 metrics.json 0.037 矛盾 ⇒ **数据不可用**。 | **先选方言再实现**，三候选：① 现有 6 张量（`input_mean/input_std/proj.weight/output_mean/output_std/sink_embedding`，首行被 `sink` 顶替）② ClipProj（no-mlp / mlp）③ 闭式投影（4 张量）。**建议路线**：做 ②→① 的转换器——ClipProj 的线性投影 + 常数 `std`/`sink` 即可构出 6 张量，**改动最小且不碰 kernel**。验收：同 prompt 的 text conditioning 余弦 ≥0.99 + 成片 PSNR 对照（K203 的 14.8 dB 是下限参照） |
| **P44 ★ Fusion-pruned 本机实测（W4A8 档）· 前置 3 条（第 33 轮加「避开混合拼写」）** | **高（首选；选件须避开 K221/K222）** | ① 下 `Kijai/MiniMax-H3-experimental:minimax_h3_ref2va_pruned_w4a8_mixed`（**11,770,657,048 B = 10.96 GiB**）+ `lightx2v/Minimax-H3-Turbo-Fusion:pruned/…_4step_v1.0_lite_r32_pruned_comfyui`（**818,925,468 B**，HF 与 ModelScope 逐字节同；取 4 步档）；② **`video_shift` 6.0 → 12.0**（K187 官方 Ref2AV 训练分布）；③ **【K221/K222 新增】选件避开 `vantagewithai` 的 `Acc-8Step_pruned_comfy`**（同文件 kohya+peft 双拼写 + `reshape_weight` 补丁支 → 绑一半且不确定），仍用 Kijai W4A8 + Fusion `lite_r32`（纯 peft、alpha==rank） | **K212 关闭第③条前置**：Fusion pruned 逐模块 alpha **全体 == rank**（adaln **32/32**、out_proj+fc1+fc2 **320/320**、qkv **960/960** = 320×3）⇒ **`mul ≡ 1.0`，按原样绑定，无需折算**；属 K188 的「倍率」语义而非 K200 的量化 scale。**⚠️ rank 三档极差 30×**（32/320/960），`lite_r32` 档是另一套（32/96）——**不要用 full 档 alpha 表套 lite 档**。**K213**：AdaLN 修正是 **51 个 `diff_b` + LoRA 因子**（**0 个 `.diff`**），本机 `bind_pruned_adaln_` 走 is_b 分支只写 bias 半区，与 LoRA 因子不重叠。**K178** dylib 已含 `w4a8_to_i8` + `h3_adaln_pruned_f16`；**K179** 少下 9.20 GB；**K174** catalog 无条目 → 手工 `hf_dir`。**第二臂（可选）**：K198 的 `latent-upscale` 做 refiner 前后对照 **【第 34 轮 K240】** ModelScope 复核 `lightx2v/Minimax-H3-Turbo-Fusion` 共 **48 项**：`pruned/…_4step_v1.0_lite_r32_pruned_comfyui` 与 `…_8step_v1.0_lite_r32_pruned_comfyui` **同为 818,925,468 B**。**【第 35 轮 K250 结案】sha 全异**（`4step_lite_r32 = fc088567…` / `8step_lite_r32 = 425d1c1c…`；全量档 `86449d1d…` / `8208de8c…`）⇒ **4/8 步不可原槽互换，只取 4 步档**；另根目录 8 个非 pruned 件（3,778,242,236 / 5,209,509,820 / 808,241,732）与 `pruned/` **不是同一批**，别混引。 |
| **P49 ★ WaveCut/one-hot 时调制剪枝形态的可读性（新）** | 低 | 无（需改 A/B 判据，非下载） | **K211**：`Jianqiao1/MiniMax-H3-Image-Lossless-Pruned-ComfyUI` 的 bf16（40.2 GB）与 int8（21.0 GB）**本机皆拒载**——无 `model.diffusion_model.` 前缀、无 `adaln_t_table`、AdaLN 宽 8、`time_embedder` 极窄（`proj_in [16,256]`/`proj_out [8,16]`）⇒ `comfy_saved` 两条判据全不满足，fail 在 `metal-minimax-h3-transformer.cc:657-661`。**为何不能靠补旁挂表绕过**：本机 pruned 分支要求 `curve_grid >= 2 且 time_dim == 8`，而本件的「8」是 `proj_out` 输出维度，语义不同。⇒ 若要读，需在上游加「one-hot 时编码」识别分支（属新架构变体，**不建议本机私改**；与 P42 同类：等上游） |
| **P50 ★ 「ref LoRA」＝ FL2VA→Ref2VA 差分（新，跟踪）** | 低 | 无（只记存在性） | **K216**：Kijai README 原文「ref lora is the difference between fl2va and ref2va, completely experimental」；`wip/minimax_h3_ref2va_pruned_w6a8_g32` 指向 `Comfy-Org/comfy-kitchen` PR #191。若成立，则**一份 FL2VA 权重可覆盖两任务**（省一半磁盘）。与本机「两 partition config 字节相同、行为不同」并存。**待复现** |
| **P45 ★ FastH3-VSA（gate_compress）缺口跟踪** | 低 | **K195 修正**：无（只盯 fork 分支，且合入前需 rebase 一个月演进） | **K181**：`Kijai/…:minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot`（21.33 GiB / 1082 tensors / 250 层 int8_tensorwise）已落地社区，但本机 `grep gate_compress` = **0**，`untranslatable_tensor()` 对无 native 名 tensor **整文件拒绝**。上游 **issue #56**（`AugustRush/vpipe:omniref-vsa`，15 文件 746 行，GitHub 报 **Able to merge**，2026-10-22，**0 评论 / 已 34 天**）的失败原因与实测逐字一致。⇒ 与 P42 不同类：**不需改 kernel，只需名字映射合入**。合入后本机需更新 build 才能跑 |
| **P42 H3-Tiny 剪枝家族本机可行性** | 中 | ⛔ **阻塞（K163 重写）**：不只是「catalog 无 h3_tiny 条目」，而是 **loader 硬 gate** ——`metal-minimax-h3-transformer.cc:830` 要求 `pruned() && time_dim == 8`，而 `time_dim` 取自 `adaln_t_table` 第 2 维；H3-Tiny 是 **[1025,16]** → 加载即 fail。Metal kernel `h3_adaln_pruned_f16` 亦硬编码 `k<8` | **K162 权重头实测**：42 块（0–41）、`[1025,16]` F32、`adaln_proj.linear.weight [96768,16]`；14B INT8 FFN **9984**（bf16 是 9792，ConvRot group 256 对齐）；FewStep 版无 `adaln_t_table`，改双段 `.linear_1 [8,2688] + .linear_2 [96768,8]`。**K165**：与官方 pruned（50 块 / [1025,8]）在 qkv/out_proj/fc1/fc2 上逐形状一致 → **只差「块数自适应 + AdaLN 宽度参数化」**。**下一步不需要下载**：① 向上游提 issue/PR 支持任意宽 pruned 曲线；② 或本机打补丁把常量 8 改参数（kernel + 校验双改，`.h:138-142` 已有 `curve_grid` 变量可复用）。**不建议自行改源码**（会与上游 a6a1f53 冲突） |
| **P39 定时任务会话空壳根治** | 高 | ✅ **实质闭环（2026-11-25 02:30，第 28 轮第 4 次完整链路）**：launchd + 无头 CLI 连跑 4 轮（R=26 / R=27 / R=28）。04:30 槽曾实测因 `Upstream response stream was interrupted` 失败、兜底正确删锁不推进（K154） | 方案=launchd + codebuddy 无头 CLI 独立进程绕开会话层。已破四关：K145(bundle 分派)/K146(模型 ID 别名)/K147(CLI 僵死占锁+看门狗)/K154(流中断兜底)。**残留风险：上游长连接偶发中断，无重试机制** → 见 P41。详见报告 18.30–18.37 |
| **P40 4 步适配器「运动场景」验证 + v1.3 换槽 A/B** | 中 | 待验证（合并两项）。**K156 限定**：4 步线自 10-20（v1.3）后冻结 36 天，换槽 A/B 价值下降；8 步 v1.2 是结构性变更、**不可**换槽。**K166**：H3-Tiny 的 50 步/shift12 与本路线不同赛道，不可混比。**K188 新增前置**：换槽前必读 `__metadata__.alpha`——v1.0/v1.1=**128**、v1.2/v1.3=**8**，形状全同但等效强度差 16 倍；不核 alpha 会把 v1.3 误判为「效果变差」 | ①**K152**：社区称 4 步在快/大运动会糊成拖影（二手待复现）；本机 18.21 的「4 步细节能量 170.6 > 8 步」是**静态/慢速夹具**，需运动夹具复测定稿。②**K151/K156**：v1.3 与 v1.2 字节级同构可换槽，但 4 步线已冻结 → **优先做运动夹具复测，换槽降为可选**。**成本**：+1.38 GB 下载 + ~29 min 生成 |
| ~~**P41 P39 上游流中断重试**~~ → **已完成（2026-11-27，本轮）** | — | — | 04:30 槽 `Upstream response stream was interrupted` 导致空跑 4 min 54 s；`cb_exit=0` 掩盖失败（K154）。**已实现**：runner 把 CLI 执行抽成 `run_cli()`，`cb_exit=0` 但 round 未推进时自动重试 1 次（新 session-id 避免看门狗误 kill、重建并发锁、间隔 30s）；真失败（如 timeout 124）不重试。4 场景隔离测试全过（success 1 次 / 假成功→重试成功 2 次 / 两次假成功失败 / 真失败不重试） |
| **P43 零下载权重头核验纳入常规检索（新）** | 低 | 无（<2 min/模型） | **K162 方法论**：`Range: bytes=0-7` 取 u64 长度 → `Range: bytes=8-(7+len)` 取 JSON header，可得全部张量名/shape/dtype/内嵌 metadata。对任何候选新权重，**先读头判定「本机 loader 会不会 fail」，再决定是否下载**。已证明可用于：H3-Tiny（判出 16 宽被拒）、Comfy-Org pruned（判出 8 宽可读）。建议固化为 `scripts/safetensors-peek.py`（**未建，待用户确认**） |
| **P36 pi-H3 原生适配器本机复现** | 中 | 待验证（前置：build 更新到 a6a1f53 + prepare-pi-h3 权重账）。**K153 依据**：DWD 原论文证明只微调末几 block + 线性 head → P36/P37 前置可合并 | K128/K129：适配器自带 step grid + 精确 handle；DWD 免 VAE 解码（f32 0.0053 / 参考自身 bf16 0.0052）。vpipe 原生第三路线，优先于外部 LakonLab 栈复现 |
| **P37 LoRA 训练 24GB 显存账** | 中 | 待验证（K131 调制表折叠 + K133 记账修正后重测峰值）。**K153 补强**：DWD 论文「仅末几 block 微调」可作 24 GB 降本备选 | K130：train-lora 训练 H3 DiT 两 partition；本机首次涉及「训练」能力族。需确认 24 GB 能否承载 |
| ~~**P38 定时任务调度加固**~~ → **已完成（18.26.7，用户选方案①）** | — | — | 恢复 4 槽制（重建 02:30 id c17d1b23 / 06:30 id 94c4eadb，四槽均 ACTIVE + prompt 统一新基线）；防休眠核查通过（AC sleep 0 + autostart 已配，无需 caffeinate）；三级兜底机制生效。残留风险：应用手动退出不自愈（已知限制，需 launchd 守护才彻底解决） |
| ~~**P32 RelayVSR 2× 真值对照**~~ → **已完成（18.22）**：2× 档 =「向真值收敛的欠估增强」（纹理量 = 真值 0.785×，与 4× 的 1.76× 编造方向相反）；双超分档定位修订为分工（FlashVSR 4× 风格化 / RelayVSR 2× 保真） | — | — |
| ~~**P29 RelayVSR 2× 实测**~~ → **已完成（18.21）**：832×480→1664×960 跑通 | — | — |
| **P30 d72c22f 漂移基线重测** | 高 | 无（零下载） | 新 build 同 seed 复跑对照（历史漂移基线只适用 33cda00）；顺带验证长提示词 band 化对短 prompt 是否零影响 |
| **P31 sgm_uniform/beta 网格 vs 默认 5s 片实测** | 中 | 无 | P28 只测了静态夹具；动态场景的 σ 细扰是否同场景待验 |
| ~~**P33 RelayVSR 接缝周期判据定标**~~ → **已完成（18.25）：判据重大修订** | — | — | ★★★ 124 帧原片本身 peak_excess 1.970/f_ratio 4.331 **强于**超分片 1.921/3.562（同 peak_k=11）→ 脉动是源片固有非超分接缝，推翻 K104 归因。绝对阈值作废，判据改为超分/原片比值（强制加原片对照臂）；本轮比值 0.82<1 无超分脉动。 |
| **P35 768p 重生成高清化 Negative 复盘** | 低 | 无 | K123 已定论「重生成高分辨率 + 恒定码率 = 更糊且换场景」；高清化统一走 RelayVSR 2×（K124）。本项仅条目留存，无需实验 |

## 每日知识增量（2026-11-27 06:30 · 第 36 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 36 轮；主报告对应第 **18.45** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 13 次链路）。知识编号 **K253–K264**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K253** | ★ 上游静默**第 12 日**（五项与第 35 轮**逐位相同**）：HEAD `a6a1f53`（author 11-23T09:54:27Z / pushed 11-23T11:20:51Z）、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR total=0、**274 star / 27 fork / 36,920 KB** | GitHub API ×5 | 2026-11-27 | 零增量；**star 连续第 3 日不动** |
| **K254** | ★★★ **H3 VAE 侧首个 int8 ConvRot**：`cjbrigato/fast_h3_vae_v2_24l-INT8-CONVROT:fast_h3_vae_v2_24l_int8_convrot.safetensors` = **1,623,016,374 B / 493 tensors**（I8 98 / U8 98 / F32 297）。fast-VAE 结构：24 层 / dim 2048 / ffn 16384 / z 24 / `register_tokens [1,4,2048]` / `post_quant_conv [24,24,1,1,1]` / `proj_out [3072,2048]`。98 量化层 = 96 块投影 + `x_embedder` + `proj_out`，每层 `I8 weight` + `F32 weight_scale [N,1]`（逐行）+ `U8 comfy_quant`（120 B）。**`convrot_groupsize = 64`（DiT 侧全是 256）**；`x_embedder` 唯一不旋转（`comfy_quant` 无 `convrot` 键，`K=24`） | HF 镜像 Range 读头（全 header）+ 3 次 `comfy_quant` 载荷切片 | 2026-11-26（仓）/ 2026-11-27（读头） | **量化面从 DiT 扩到 VAE**；⚠️ **组 64 ≠ 256**，任何按 256 硬编码的反旋转在 VAE 上必错 |
| **K255** | ★★★ **本机 fast-VAE 对 I8 是硬拒绝**：`metal-minimax-h3-fast-vae.cc:96` `with_tensor_` 判 `!float_dtype_(info->dtype)` 即返回 false（`:73-76` 只收 F32/F16/BF16）⇒ `proj_` 取不到 `.weight` → `:566` `cannot read <name>` → `load_` 报 `cannot read block 0's ...`。旁证：`proj_` 的 int8 分支（`:533-559`）是「bf16→int8 转换」，**无读 I8 码字路径** | 本机源码逐行 + 张量契约 | 2026-11-27 | **K254 在本机不可用**（结构性，非体积/性能问题）；与 video-VAE（走到 `to_bf16_` 才空）**同一族两个失败位** |
| **K256** | ★★★ **同一份 Pika Flex LoRA 两种 rank 契约**：diffusers 版 `fl2va/adapter.safetensors` = **624 tensors / 全 F32 / 2,767,274,120 B**，`<module>.lora_A.default.weight`（**带 `.default.`**、无 `diffusion_model.` 前缀），**全 rank 128**；comfy 版 `comfy/loras/…_fl2va_comfy_bf16.safetensors` = **416 tensors / 全 BF16 / 1,956,172,176 B**，`diffusion_model.<module>.lora_A.weight`，**普通模块 128、`attn.qkv_proj` 384**（A `[384,5376]` / B `[21504,384]`）。README：「fuses Q/K/V LoRA projections and reorders the SwiGLU halves」 | HF 镜像读头 ×2（官方 `Pika-Labs` 与镜像 `vml12` 同份）+ `comfy/README.md` | 2026-11-26 / 2026-11-27 | **推翻「一个 LoRA 一个 rank」**（K248 是「标称≠实际」，此处是**逐模块合法不同**）；本机 `factor_meta_` 按模块读 rank，结构上支持 |
| **K257** | ★★★ **comfy 版「omits explicit alpha tensors」⇒ 本机 `mul≡1.0`，`qkv` 实际强度只有 1/3**：header 无 `alpha`/`lora_alpha`/`lora_adapter_metadata`（仅 `modified_by/license*/copyright/format=pt/base_model/base_revision/converted_for/source_adapter`）⇒ `index_suffix_`（`:326-358`）三处全未命中 ⇒ `_meta_alpha=0` ⇒ `factor_meta_` `*mul=1.0f`。而 `qkv_proj` rank 384 = 3×128 | 同仓 header + `comfy/README.md` + 本机 `runtime-lora.cc:420-460` | 2026-11-27 | **alpha 第六态：融合后语义被刻意取消**（推断，未实测）；前五态都是「偏强或跳过」，**这一态是「偏弱」** |
| **K258** | ★★ sd.cpp **PR #2435**「reuse INT8 GEMM for W4A8」**11-26T15:00:12Z 合入**（`6b51a955`，**+692/−1496 / 29 文件**）：「Remove the dedicated W4A8 matmul implementations」。本机 `affine_dequant_embed.cc.metal:2372` 仍有 `w4a8_to_i8`、`:2320` 有 `w4a8_convrot_dequant`，`kernel-contract.h:273` 仍登记 | GitHub PR API + 本机 metal 源 | 2026-11-26 | 「同名 kernel ≠ 同功能」**第 2 例**（K235 第 1 例）；sd.cpp 删的是 matmul 不是 kernel，**无直接冲突** |
| **K259** | ★★ sd.cpp **PR #2436**（`ea3f6ec703`，11-26T15:50:54Z）：「Default an omitted `convrot_groupsize` to **256** when ConvRot is enabled, **matching ComfyUI**」；本机 `fp8-layout.cc:47` `int group = 256;` + `:59` `as_int(256)` 同值 ⇒ **三方一致** | GitHub PR API + 本机源码 | 2026-11-26 | **印证**（近期少见的无分歧项）；但意味着 **K254 的 64 必须显式声明**，不写就会被按 256 解释 = 对 VAE 是错值 |
| **K260** | ★★ **第三方镜像仓可逐字节判等**：`vml12/Pika-H3-Flex`（11-26T18:02Z 建、0 dl / 0 like）与官方 `Pika-Labs/Pika-H3-Flex`（10-29 建、**197,060 dl / 712 like**、lastModified **11-07**）的 `fl2va/adapter.safetensors` **`x-linked-etag` 相同（`8ed6115d…`）、`x-linked-size` 相同（2,767,274,120）**，`x-repo-commit` 不同 ⇒ 同份文件不同仓 | HF 镜像 `resolve` 响应头 ×2 + `manifest.json`（`sha256` 亦为 `8ed6115d…`） | 2026-11-27 | **新判据**：判「同一份权重」看 `x-linked-etag` + `x-linked-size`，**不看仓名、不看 `x-repo-commit`** |
| **K261** | ★★ **`x-linked-size` 是 302 上唯一可信体积字段**：本轮 4 件一次拿全（2,767,274,120 / 1,956,172,176 / 9,920,387,264 / …）；而 `curl -sIL` 加 `grep content-length` 给出 **1050 / 1048 / 1102 / 1110**（跳转体长度） | HF 镜像 `resolve` 响应头 | 2026-11-27 | **根治第 35 轮坑②**（缺 `-L` 得 183）；`content-length` 只在 200/206 后有意义 |
| **K262** | ★★ **`_quantization_metadata` 与 `comfy_quant` 层内可写法不同**：K254 的 `x_embedder` 在 `_quantization_metadata` 只有 `{format, orig_dtype}`（**无 convrot 键**），`comfy_quant` 写 `{"format":"int8_tensorwise","orig_dtype":"torch.bfloat16","per_row":true}` —— 两者**一致地都不旋转**；本机 `declared_format_`（`fp8-layout.cc:74-125`）**先 `comfy_quant`、后 `_quantization_metadata`** | 本机源码 + 3 次载荷切片 | 2026-11-27 | 印证解析顺序；新见「细长投影（K=24）作者显式关旋转」是合理设计而非漏写 |
| **K263** | ★ **11-26 社区面（去重后，仅新品类）**：① **`Enigma4869/h3` = 422 个 `.safetensors` 的三层目录集合仓**（首个「个人 LoRA 货架」型）；② `huggingface12341/zsf-h30` 4 分片（疑似整模型再分发，未读头）；③ 空壳续增 `RunningHubAI/rh-crown-true-first-person-…`（1 文件无权重）、`Lora-Daddy/h3-writer-hauhau`（4 文件无权重）、`BrickMomen/bvfinish-h3-image-lora`（1 件 + 8 图）；④ `vml12/Pika-H3-Flex` 是全量镜像（96 文件，DiT 索引 66.28 GB + 双 text_encoder + 双 VAE） | HF 搜索 ×3 拼写 + `api/models` ×5 | 2026-11-26 | 重心**第 4 次迁移**：→ **「货架仓 + 整模型镜像」**。⚠️ `Enigma4869/h3` 名称与内容无关（成人内容命名），只记「存在一个 422 件集合仓」 |
| **K264** | ★★ **ModelScope `Recursive` 口径让 Fusion 文件数 15 ↔ 48**：`Recursive=false` 得 **15 项**（`assets` / `pruned` / 6 根权重 + 元数据）；第 35 轮 K240 的「48 项」是 `Recursive=true`。`LastUpdatedTime 1795546202` = **2026-11-24 18:50Z**（权重未动，与 K169 一致） | ModelScope `repo/files` ×2 口径 | 2026-11-27 | **口径纪律**：引用「N 项」必须写 `Recursive` 真假，否则 15 vs 48 会被误读成「新增 33 文件」 |

## 每日知识增量（2026-11-27 04:30 · 第 35 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 35 轮；主报告对应第 **18.44** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 12 次链路）。知识编号 **K243–K252**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K243** | ★ 上游静默第 11 日（四项与第 34 轮**逐位相同**）：HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star / 27 fork / 36,920 KB** | GitHub API ×5 | 2026-11-27 | 零增量；**star 连续第 2 日不动** |
| **K244** | ★★ sd.cpp 的 latent upscaler 也只有 3D-conv 一支：`#2249` 已于 **11-04 合入**；`#2357`「2D-conv upscaler」**11-14 开、11-15 后未更新、仍 open**（改 866 行 hpp + 13 行 video.cpp）。本机 `2d_conv` grep = **0** | GitHub PR API ×2 + 本机源码 | 2026-11-26 | 后处理线**与本机同档**，没落后（与换编码器线相反） |
| **K245** | ★★★ 社区 latent upscaler **v2 是同架构重训**：`George0667/MiniMax_Temporal_Upscaler:…_v2_fp16` = **690,592,736 B / 322 tensors / 全 F16**，与 v1（SOLRICKS 转存 690,592,672 B / 322）**key 与 shape 逐名相同**但**数据区 sha 不同**（`6307f49c` vs `d1e3cbc7`）⇒ 非转存。本机 `config_from_weights` 四条自检全过、`dwconv [512,1,5,1,1]` ⇒ **零改动可加载** | HF 镜像读头 ×2 + 本机源码 | 2026-11-24 | **唯一「社区新权重 + 本机零适配」的后处理件**；⚠️ `config.json` 写 `in_blocks 12`，**头里是 18** ⇒ 结构只认 header |
| **K246** | ★★ `v2_temporal`（690,601,656 B / **326** tensors）只多 4 个 `t_embed.{0,2}.{weight,bias}`；本机无任何分支且**不报未识别张量** ⇒ 推断**静默忽略**，后果是「空间放大照做、时间插帧静默不发生」（未实测） | HF 读头 + 源码路径核对 | 2026-11-26 | 「加载成功 ≠ 全生效」**第 3 例**（K221/K199/K246） |
| **K247** | ★★★ 第四条调参工艺「跨模型 q_norm graft」：`yichengup/…ltxqnorm-int8-convrot`（1,141 dl / 8 like，**20,970,382,496 B = 19.53 GiB**，932 tensors）`__metadata__`：`rebuild = own-hybrid from official Comfy-Org pruned bf16`、`adaln_splice = none (fl2va throughout)`、**`zspatial_graft = donor=Z-Image-Turbo …blocks=30-49 dose=0.5`**、**`qnorm_graft = donor=LTX-2.5 …blocks=30-48 dose=1.0`**、**`qnorm_pin = block 49 rms=5.0`** | HF 镜像 Range 读头 + README | 2026-11-25 | 新工艺类：不量化/不剪枝/不蒸馏，**改写末段 20 块的 `attn.q_norm` 增益**；格式全对但**语义跨模型 ⇒ 行为未知** |
| **K248** | ★★★ I8 refiner 的 rank **不是固定 256**：624 tensors（I8 416 + F32 208 = 208 对），rank 横跨 **48～946**（out_proj 48–267 / qkv 252–866 / fc1 195–382 / fc2 72–400）；`.alpha` 仍 1e-4～1e-3（最大 `blocks.29.qkv 1.112e-3`） | HF 全 header + 4 次 alpha 切片 | 2026-11-26 | 修正 K199「r256」= **打包标称值**；按固定 rank 反推体积/强度不成立 |
| **K249** | ★★ `comfy_quant` 是 **U8 的 72 B JSON 载荷**：`Coffmeteor` 932 tensors = I8 200 + **U8 200（全 `*.comfy_quant`）** + F32 206（`weight_scale` 200 + `adaln_t_table` + `rope.inv_freq` + 4 bias）+ BF16 275 + **F16 51（全 `adaln_proj.linear.bias`）** ⇒ 同一 linear 的 weight(BF16)/bias(F16) **精度不同** | HF 读头 + 2 次载荷切片 | 2026-11-27 | 统计陷阱：按 dtype 数权重会**翻倍**；须过滤 `is_aux_name` |
| **K250** | ★★★ Fusion pruned 4/8 步**不同构**（K240 结案）：`4step_lite_r32 = fc088567…` / `8step_lite_r32 = 425d1c1c…`（都 818,925,468 B）；`4step_pruned = 86449d1d…` / `8step_pruned = 8208de8c…`（都 5,220,193,444 B） | ModelScope `repo/files`（含 `Sha256`） | 2026-11-26 | **不可原槽 A/B 互换**；根目录另 8 件（3,778,242,236 / 5,209,509,820 / 808,241,732）**与 `pruned/` 非同一批** |
| **K251** | ★★ 新分发形态 **gated 仓**：`linkqpsfa/minimax-h3-{i2v,unc-i2v}-weights` 的 siblings 可见（8 文件 / 单件），`resolve` 一律 **403 `GatedRepo`**；**`content-length: 183`（191）是错误体长度，不是体积** | HF API + `curl -sIL` | 2026-11-26 | 体积判据须「先 status 2xx 再 content-length」；第二类「假体积」（第一类是 `000` 超时） |
| **K252** | ★★ 11-26 社区（去重后）三条新线：**latent upscaler v2 重训族**（478 dl）、**跨模型 graft**（1,141 dl）、**AMD Loom 部署包**（`loom-draft/…-loom`，`.loom` 程序 + `REPORT.md`，**非 H3 权重**，是 27B 提示词改写器打包）；另 `jh27kim/MiniMax-H3-Ref2VA-4step` **已删（`Repository not found`，200 体内的错误）** | HF 搜索 ×2 + `api/models` ×3 | 2026-11-26 | 重心第 3 次迁移：编辑型 LoRA → 量化/换编码器 → **后处理重训 + 增益移植**；「搜到过」≠「还在」 |

## 每日知识增量（2026-11-27 02:30 · 第 34 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 34 轮；主报告对应第 **18.43** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 11 次链路）。知识编号 **K232–K242**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K232** | ★ 上游静默第 10 日：HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star（停涨）** | GitHub API ×5 | 2026-11-27 | 零增量 |
| **K233** | ★★ sd.cpp **PR #2424 已合**（`439e77a5`，11-26T13:12:17Z）：`-mlp` 变体四种 connector 全支持；**PR #2414（open）latent continuation**（尾 latent 续接）；本机仍 6 张量无 MLP、`save-latent\|continue-latent\|pin-frames` grep=0 | GitHub PR API + 本机源码 | 2026-11-26 | **推翻 K190/K202「sd.cpp 也不支持 MLP」** |
| **K234** | ★★★ 首个 **NVFP4 W4A4 + INT8 ConvRot 逐投影混合** H3 DiT：`Maximilian228/…pi-H3-NVFP4-GPTQ` DiT = **14,302,909,922 B / 1,082 tensors**；`qkv/out/fc1` NVFP4（`weight_scale F8_E4M3 [N,336]` swizzled + `weight_scale_2`）、`fc2` INT8 逐行；原生名 + `adaln_t_table [1025,8]` | HF 镜像 Range 读头 | 2026-11-26 | **量化形态第三档：逐投影混合** |
| **K235** | ★★★ 本机判定分两层：源码 `scan(nvfp4=true)` + `resolve_nvfp4_(comfy=true)` + int8 `per_row` **都认**；但已装 `libvpipe.0.dylib`（`0.1 (9db5dd7*0)`）**`nvfp4_dequant` 命中 0**（kernel 源在 `affine_dequant_embed.cc.metal:2408`，通路 commit **41d2789/11-12**）⇒ **拒载是「host 无 NVFP4 widening kernel」，非格式不认** | 源码 grep + `strings` + `git log -S` | 2026-11-27 | **修正「本机不认 NVFP4」单层口径** |
| **K236** | ★★★ DWD 像素头第二份实现：`pi_h3_4step_dwd_head_gptq_int8` = **171 tensors** 全 `dwd_pixel_refiner.*`+`dwd_norm_out.*`（vs K228 `pocis` 92 tensors），**拓扑命名全不同** | HF 镜像 Range 读头 | 2026-11-26 | **P52 改为「两家不收敛，不私接」** |
| **K237** | ★★★ 换编码器第三条路：`Alissonerdx/TE-PK-Minimax-H3` 零梯度闭式 Ridge/Procrustes → 5,120 维，**无 LoRA 无 MLP**，单件 20–105 MB，5 张量 `R [4096,5120]`+donor/target mean+scale | HF 镜像读头 + README | 2026-11-26 | 本机 6 张量方言（含 std/sink）不兼容 |
| **K238** | ★★★ TE-PK 自相矛盾：README/header 9B **cosine 0.9626 / R² 0.9935**，同仓 `metrics.json` **0.890825 / 0.037135**；8 key `val_r2` 全 0.033–0.112 | 三方对照 | 2026-11-26 | **R² 差两个量级 ⇒ 口径不可用，不并入能力** |
| **K239** | ★★ 「LoRA 并进基座」pruned 件 **637 tensors/50 块**，顶层 `time_embedder.table [1025,8]`；`is_diffusers_layout` 全满足 → 翻译启动 → 撞无映射名 → 返回 0 | HF 4 分片读头 + 源码 | 2026-11-26 | **K204 精确定位：翻译映射层是第三处失败位** |
| **K240** | ★★ ModelScope：Turbo 31 项（仅 README 改动）；Fusion **48 项**，4/8 步 lite_r32 pruned **同 818,925,468 B（未核 sha）** | ModelScope API ×2 | 2026-11-26 | P44 仍取 4 步档 |
| **K241** | ★★ 检索坑：`lightx2v/LightX2V` **404**（正确 `ModelTC`）；镜像 `resolve` 对仓内不存在文件也 404 ⇒ 判仓内容看 siblings；`siblings[].size` 仍全 None | curl + GitHub API | 2026-11-27 | 镜像优先第 3 日成立 |
| **K242** | ★ 11-26 社区（去重后）：新品类 2 个（pi-H3 量化落地 / 闭式投影换编码器）+ 提示词改写器双版本仓 + **8/30 空壳仓** | HF 镜像搜索 ×3 | 2026-11-26 | 重心转向工程落地方向 |

## 每日知识增量（2026-11-27 00:30 · 第 33 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 33 轮；主报告对应第 **18.42** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 10 次链路）。知识编号 **K220–K231**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K220** | ★ 上游静默第 9 日：HEAD `a6a1f53`、release v0.1.110 落后 **26 天**、issue 14 全开 0 评论、PR=0、**274 star(+1)** | GitHub API ×5 | 2026-11-27 | 零增量 |
| **K221** | ★★★ **加速 LoRA 第五形态**：`vantagewithai/…Ref2VA-Acc-8Step_pruned_comfy`（**1,725,921,392 B / 578 tensors**）metadata `PDD head banks as base-relative pad-and-add reshape_weight LoRA`；4 个 `I64` `reshape_weight`（`[1]`/`[2]`）=元数据；`final_layer.video_out` **lora_down [3072,5376] + lora_up [3072,3072]（rank=满秩 3072）**；本机 `reshape_weight` grep=**0** ⇒ **部分静默** | HF 镜像 Range 读头 + 本机源码 | 2026-11-26 | 新增「部分静默」失效形态（不在 `bind()` 枚举路径，`_skipped` 未必涨） |
| **K222** | ★★★ **同文件两种因子拼写并存**：`final_layer.*` kohya（4 对）+ `blocks.*`/`token_refiner.*` peft（258 对）；本机「首个因子定整文件拼写」+ `unordered_map` 序 ⇒ **绑一半且不确定绑哪半** | HF 读头（原始字节序）+ `runtime-lora.cc:308-330` / `metal-llama-weights.h:296` | 2026-11-27 | 判据改为「可能只绑一半」；新 **P51** |
| **K223** | ★★ **alpha 第五态**：`lora_alpha 64 == rank 64`（mul 1.0）但 `conversion` 明写 `alpha/rank folded into lora_B` ⇒ **体检须读自然语言 metadata** | 读头 `__metadata__` | 2026-11-26 | 换槽体检加第 5 项（读 `conversion`），否则 alpha≠rank 时会**双倍施加** |
| **K224** | ★★ **可读对照件**：`MATLOWAI/…Variable-Clock` = **298,261,224 B / 600 tensors / 全 F32**，kohya、200 模块、rank16；`ss_shift_video 12.0`/`shift_audio 3.0`/`task t2va`/`base_family fl2va`/`motion_clock …`/`native_anchor weight 30.0`；同仓 `_lateattn`/`_noblock49` + `clock_maps/` | HF 镜像 Range 读头 | 2026-11-25 | 本机可读；**独立复现 K187 的 shift 12/3** ⇒ P44 之后最便宜的对照件 |
| **K225** | ★★ **视频重绘 LoRA 首次进清单**：`VoidEclipseAI/…ReFrame-VideoInpainting` = **596,446,800 B / 600 tensors / 全 F32**、kohya、200 模块、200 个 `.alpha` | HF 镜像 Range 读头 | 2026-11-26 | 契约内、理论可绑；**待复现** |
| **K226** | ★★★ **预烘 AdaLN 表第三家**：`OpenVDN/vdn-minimax-h3-edge`（9,804 文件 / 535 payload 全校验 / `freevideo-fp8-variants-v1`），`adaln-tables-v2-*` = `step_0 BF16 [6,32256]` + `step_1..7 [9,32256]`，契约名 `minimax-h3-adaln-silu-linear-3x6-v1` | HF 镜像 API + `bundle.json`/`READY.json` + 表头 | 2026-11-26 | **三种布局互不兼容**（K210 宽 8 / K205 `[8,2688]` / 本件每步向量）⇒ 本机一种都不认 |
| **K227** | ★★ **交付三件套化**：`vantagewithai` 仓 = 22 GGUF（fl2va/ref2va × 11 档）+ 4 个 8 步 acc LoRA + 7 份 workflow，**11,153 dl / 28 like**；默认 `pruned_int8_convrot` 或 GGUF + `simple/20 步` + `euler` + Sage/Sol/Spectrum 三补丁 | HF 镜像 API + workflow JSON | 2026-11-26 | 评估口径改为「这套三件套能拼出几条」 |
| **K228** | ★★ **像素头（DWD 推理侧）首带 PSNR**：`pocis/…Video-PixelHead` = **95,858,352 B / 92 tensors / F32**，`eval_psnr_db 31.97`、`d_feat 5376`、`d_lat 96`、`latent_input x0_hat_vid_1x2x2`、作者自标 `not_recommended_for_production` | HF 镜像 Range 读头 | 2026-11-26 | 本机 grep=0；31.97 dB 可作「免 VAE 解码」参照线；新 **P52** |
| **K229** | ★ 三线零 H3：LightX2V 3 条全非 H3（LongCat-Avatar / Seed-VC / YuE2）；sd.cpp `#2436` LTX INT8 ConvRot + `#2435` W4A8 GEMM **只服务 LTX/通用**，H3 仍 `5fa203c`；ComfyUI 3 条无 H3 | GitHub API ×3 | 2026-11-26 | **⚠️ 勿把 `#2435/#2436` 当 H3 量化进度** |
| **K230** | ★★ **检索通路反转**：`huggingface.co` 全域 `000`（DNS→157.240.13.8、TCP 无响应），**`hf-mirror.com` 的 `resolve`+Range 可用（206，首字节正确）**、`api/models?search=` 200/2.2 s | curl 实测 | 2026-11-27 | 分流规则改「**镜像优先，直连作 fallback**」（推翻上轮结论） |
| **K231** | ★ 社区续增：Person-Remover / Character-Swap / Image-Outpaint LoRA、`javawock7618/comfy-MiniMax-H3-workflows`（**175 like** 纯 workflow 仓）、`klassas/minimax-h3-image-slim`、`aevionlabs/*` 4 仓、`Infinity-io` GGUF | HF 镜像搜索 API ×3 | 2026-11-26 | 「人物级编辑」成独立品类；workflow 仓独立成类 |

## 每日知识增量（2026-11-26 06:30 · 第 32 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 32 轮；主报告对应第 **18.41** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 9 次链路）。知识编号 **K209–K219**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K209** | ★ 上游静默第 8 日：HEAD `a6a1f53`（≈3.4 天）、release v0.1.110 落后 **26 天**、issue 14 全开、PR=0、273 star 逐位同上轮 | GitHub API | 2026-11-26 | 零增量 |
| **K210** | ★★★ **WaveCut 风格「时调制剪枝」成独立工艺线**：AdaLN 在固定采样步上预计算，换成 one-hot 时编码 + 投影。H3-Image **135 → 94 GB** 逐像素相同；ComfyUI 参考图路径版 **66.3 → 40.2 GB**，作者 5/5 pixel-identical（MAE 0 / PSNR ∞），int8 版 21.0 GB 但 PSNR 21.833 dB | GitHub `iamwavecut/MiniMax-H3-Image-Pruned` + `Jianqiao1/…-ComfyUI` README | 2026-11-25 | **待复现**（ComfyUI 0.45.0 / RTX 5090 / 4096² / 六步）；「剪枝代价可为零、量化代价不能」与 K172/K201 同向 |
| **K211** | ★★★ **两个 WaveCut 件本机皆拒载**：**无 `model.diffusion_model.` 前缀 + 无 `adaln_t_table` + AdaLN 宽 8（`[96768,8]`）+ `time_embedder` 极窄（`proj_in [16,256]`/`proj_out [8,16]`）** ⇒ `comfy_saved` 两条判据全不满足，fail 在 `metal-minimax-h3-transformer.cc:657-661`；int8 件另带本机 grep=0 的 `comfy_attention.config` | HF Range 读头 ×2 + 本地源码 | 2026-11-26 | **新增「第 5 类看着像 H3 打不开」**（one-hot 剪枝形态）；**不可靠补 `adaln_t_table.bin` 绕过**（那个 8 是 `proj_out` 输出维，非曲线网格）→ 新 **P49** |
| **K212** | ★★★ **P44 第③前置判死**：Fusion pruned 逐模块 alpha **全体 == rank**——adaln **32/32**、out_proj+fc1+fc2 **320/320**、qkv **960/960**（=320×3，metadata `qkv_fusion: "…alpha multiplied by 3"`）⇒ **`mul ≡ 1.0`** | 逐模块 `.alpha`/`lora_A` 切片 + `__metadata__` | 2026-11-26 | **K188/K200 第三态落定**（倍率≠rank / 倍率==rank / 量化 scale）；**rank 三档极差 30×**，`lite_r32` 是另一套（32/96） |
| **K213** | ★★ Fusion pruned 的 AdaLN 修正是「**51 个 `diff_b` + LoRA 因子**」分工，**`.diff` 补丁 = 0**；metadata `adaln_conversion: "A'=A@P; diff_b=(alpha/r)*B@A@mean"`。本机 `bind_pruned_adaln_` 命中 `diff_b` 走 is_b 分支只写 bias 半区，weight 半区由 LoRA 承担，两者不重叠 | Range 读头 + 本地 `:4501-4560` | 2026-11-26 | 印证并扩写 K170/K171 |
| **K214** | ★★★ **`pruned_w6a8` 双拒**：`comfy_quant {"format":"w6a8_int8","group_size":32,"convrot":true}`、`I8 [21504,4032]` + `weight_s_rel F8_E4M3 [21504,168]`（K/32）⇒ ① `fp8-layout.cc:326` 按名拒；② 即便去掉名字门，I8 scale 校验（`:438-448`）只接受「1 个或每行 1 个」，**K/32 块 scale 被拒** | Range 读头 + 本地源码 | 2026-11-26 | **K172「按名拒绝」升级为「名 + 布局双拒」**：改名无捷径 |
| **K215** | ★★★ **社区融合 int8 基座首次契约全符合**：`Coffmeteor/MiniMaxH3-Realism-Turbo-Remix` 932 tensors / 全前缀 / `adaln_t_table [1025,8]` / `qkv I8 [21504,5376]` + **逐行** `weight_scale [21504,1]` / ConvRot 256 / 50 块 / 无 `time_embedder` | HF Range 读头 + `catalog.json`/`source.json` | 2026-11-26 | **证明「社区自融 pruned base + int8_convrot」在本机契约上可行**；**但属真人 YouTube 微调素材 → 只记存在性、不进能力表、不交付**；触发词 `r34l1sm` **本机不读该键**，须手加进 prompt |
| **K216** | ★★ 社区「ref LoRA」＝ FL2VA→Ref2VA 差分（Kijai 原文「completely experimental, I don't even know if it has a use case」），`wip/…_ref2va_pruned_w6a8_g32` 指向 `comfy-kitchen` PR #191 | HF README raw | 2026-11-26 | 与本机「两 partition config 字节同、行为不同」并存；**待复现**；若成立可省一半磁盘 → 新 **P50** |
| **K217** | ★★★ **VAE int8_convrot 是本机第三条量化盲区，且是「错值」不是「跳过」**：社区 4 个 int8 VAE（lite **1.04 GB** / lynnreal 2.14 / mt 2.81 / 官方 3.17，自报 decode **~2×**）用 `weight_scale` + `comfy_quant`；本机 VAE 只认 **`.scales`+`.biases`**（`_quant_bits` 4/8、`_quant_group` 64）⇒ I8 码被当值 → **画质崩塌、日志无错** | HF Range 读头 + 本地 `metal-minimax-h3-video-vae.cc:852-870 / 1362` | 2026-11-26 | 量化账本应为**四栏**（基座 FP8 / 基座 int8-W4A8 / 适配器 / VAE）→ 新 **P48（优先级中，须优先修）** |
| **K218** | ★ 社区续增：`SOLRICKS/3D-Animation-Style-MiniMax-H3`（rank16 step1250 + 5 份 V3 workflow）、`Coffmeteor/…Remix` 908 dl、`pmczip/MiniMaxH3_RefMod` 1,634 dl、`SOLRICKS/MiniMax-H3-Upscaler` 5,706 dl 居首 | HF 搜索 API ×2 | 2026-11-26 | 生态重心未变，新增「风格化 LoRA 集」一支 |
| **K219** | ★ sd.cpp / ComfyUI / LightX2V 三线零增量：sd.cpp `52491bd`（#2423 DGL 预览，H3 仍只有 11-25 `5fa203c` ClipProj）；ComfyUI `f40a4fbb` frontend bump / Meshy / Recraft，**无 H3**；LightX2V `83a424a`。ModelScope Turbo 31 项、Fusion 48 项（`lite_r32_pruned_comfyui` 818,925,468 B 与 HF 同） | GitHub API ×3 + ModelScope API ×2 | 2026-11-26 | 零增量（明日复查） |

## 每日知识增量（2026-11-26 04:30 · 第 31 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 31 轮；主报告对应第 **18.40** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 8 次链路）。知识编号 **K197–K208**。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K197** | ★ 上游静默第 7 日：HEAD `a6a1f53`（约 2.4 天）、release v0.1.110 落后 **25 天**、issue 14 全开、PR=0、273 star 逐位同上轮 | GitHub API | 2026-11-25 | 零增量 |
| **K198** | ★★★ **本机 2K latent-upscale 链路早已完整**（`latent-upscale` stage + 3D-conv 网络 + catalog 两条条目）；社区 SOLRICKS 件是官方 bf16 的 **F16 转存**（322 tensors / key / shape 全同、onlyA 0 / onlyB 0，头 32,552 → 32,232 B） | 本机源码 + HF 双读头 | 2026-11-26 | 「本机不支持 2K」**作废**；缺口只在 refiner LoRA |
| **K199** | ★★★ **int8 适配器因子零支持且静默**：`runtime-lora.cc` 只分支 BF16/F16/F32，`fp8::format_of("I8")=kNone` → `++_skipped`、日志无错 | 本地源码 + HF 读头 | 2026-11-26 | **新增 P47**；基座 int8 ≠ 适配器 int8 |
| **K200** | ★★ **`alpha` 两种互斥语义**：K188 的整数倍率（128/8）vs SOLRICKS 的**量化 scale**（3.96e-4），rank 逐模块不同（159–513） | HF Range 读 208 个 `.alpha` | 2026-11-26 | K188 纪律扩写：先判量级与 `quantization` 键 |
| **K201** | ★★ SOLRICKS 自报量化代价：相对 Frobenius median **0.0824** / p95 0.1432 / max **0.2841**，`visual_quality_metric: false` | `manifest.json` | 2026-11-26 | 纪律：社区量化件体积与误差同引 |
| **K202** | ★★★ 第二个换编码器方案 **Qwen3.5-9B**：投影 9 张量全 F32 且**带 MLP 残差**，tap 20；LoRA 530 张量 / rank32 / 34 模块 | HF 读头 + GitHub | 2026-11-26 | 本机契约四条全不符，且比 ClipProj 更远 |
| **K203** | ★★★ **编码器对齐 ≠ 成片对齐**：text cos 0.9507 / overall 0.9193，但成片 **PSNR 12.877 → 14.764 dB** | 该仓 README | 2026-11-26 | **待复现**；P46 期望下调 |
| **K204** | ★★ 两个 Fused 全量 pruned diffusers 仓（各 ≈40.2 GB）：176 tensors/片、无 `adaln_t_table`、AdaLN 烘进 `norm_out.folded_bias [10752]` | HF 读头 + metadata | 2026-11-26 | `WeightSet::open` 无分片目录读取 → 打不开的第 4 类 |
| **K205** | ★★ 官方 pruned 基座旁挂 `transformer/adaln_affine.safetensors`（`adaln_basis [8,2688]` + `adaln_mean [2688]`），本机 grep = 0 | HF 读头 + grep | 2026-11-26 | 新缺口，影响 P44 若用 diffusers 基座 |
| **K206** | ★ `jh27kim/MiniMax-H3-Ref2VA-4step` gated 但目录可读：`ref2va_lora_r256_iter1500` 2.77 GB，与官方 dCM 1500 iters 对齐 | HF tree | 2026-11-25 | 只记存在性 |
| **K207** | ★ 11-25 单日 H3 衍生新仓 ≥20 个；重心转向「后处理 / 换编码器 / 融合进基座」 | HF 搜索 API | 2026-11-26 | 本机两条空白 |
| **K208** | ★ issue #59 / #56 `updated_at == created_at` → 「**零触碰**」而非「零回复」 | GitHub issue API | 2026-11-26 | 比「没人回」更冷 |

**本轮实验**：无（时间预算优先最小闭环；且 K200 刚证明 alpha 语义未定，此时跑 P44 会有四变量不可归因）。零下载实测 14 次 Range（约 8 min，磁盘 0）。

**关键冲突**：P44 上轮的前置①（清 18.3 GB 半成品）**本轮实测不存在**（磁盘 37 GiB、无 `.part`）⇒ 前置降为 3 条。**前置条件本身也会过期，需每轮复核。**

**本轮踩坑（新增）**：① `repos/<owner>/<name>/commits` 对转移/改名仓返回 301 JSON（须走 `repositories/<id>`）；② HF 镜像对个别仓 commit 端点返回 `Invalid username or password`（≠ gated）；③ 家目录无界 `find` 会被 SIGTERM；④ `.alpha` 可能是 F32 小标量，按 `int()` 解会得 0 → LoRA 静默失效；⑤ Python 3.9 heredoc 中文脚本需 UTF-8 声明。

## 每日知识增量（2026-11-26 02:30 · 第 30 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 30 轮；主报告对应第 **18.39** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 7 次链路）。知识编号 **K185–K196**。

### 本轮三条主线

1. **官方给了 H3 蒸馏的超参账本**：LightX2V `7fc25cd`（PR #1730，11-25）把训练改成 FL2AV + Ref2AV 双任务、dCM → PDMD+GAN 两阶段，**shift 6/3 与 12/3 是任务分家而不是画质偏好**。
2. **「字节同构可换槽」的最后一颗雷**：4 步家族 v1.2/v1.3 与 v1.0 **形状逐键全同**，但 `__metadata__.alpha` **128 → 8**，等效强度掉到 1/16。
3. **文本编码器替代赛道被开源，但本机装不上**：ClipProj（4B 替 32B，15.7→4.5 GB）在 sd.cpp 已实现，本机 connector 四条契约全不符。

### 逐条新增知识

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K185** | ★ 上游静默第 6 日（HEAD a6a1f53 = 距 commit 2.36 天 / pushed_at 2.30 天）；release v0.1.110 落后 24 天；issue 14 全开；**PR=0**；**273 star**（+3） | GitHub API ×5 | 2026-11-25 | 零增量，star 是唯一变动 |
| **K186** | ★★★ **LightX2V 官方 H3 蒸馏 best practices**（`7fc25cd` / #1730，+2629/−202）：dCM 1500 iters（LoRA 128/128，AdaLN 16/16，LR 2e-5，48 steps，loss_scale 100）→ PDMD+GAN 3000 iters（2500 fake : 500 student，student LR 5e-5 / fake 4e-6，GAN 0.005/0.01） | commit detail（`minimax_h3_distill.md` 128 行 + 6 yaml） | 2026-11-25 | 官方首次公开超参账本 |
| **K187** | ★★★ **官方 shift 契约：FL2AV 6/3、Ref2AV 12/3**；FL2AV 的 PDMD 在 1500 步处 6.0→12.0 | 6 个训练 yaml | 2026-11-25 | **K169 从「卡面」升级为「训练分布」**；本机 ref2va 用 6.0 不符官方线 |
| **K188** | ★★★ **4 步 v1.0/v1.1 alpha=128，v1.2/v1.3 alpha=8**（rank 恒 128；624 tensors、header 81,768 B、key/shape/offsets 四者全同；`lora_B` max 0.0347→0.0173） | HF Range 读头 ×4 + 权重切片 ×6 | 2026-11-25 | ★★★ **K151 收窄**：形状同构 ≠ 可直接换槽，必核 alpha |
| **K189** | ★★ sd.cpp `5fa203c`（#2410）实现 **ClipProj**：线性投影把 Qwen3-VL-4B/8B 映射到 5120 维，替 32B；显存 15.7→4.5 GB；单 tap 24 | commit detail | 2026-11-25 | 文本编码器替代成独立赛道 |
| **K190** | ★★★ **本机 connector 四条契约全不符**：类名限 `PH3ImageTextConnector`、路径限 `text_connector/config.json`、6 个固定张量名且全 F32、`proj.weight` 一维展平；ClipProj 是单文件/F16/`W [2560,5120]`。且本机 N-tap 拼接 vs ClipProj 单 tap | 本机源码 + 权重头 | 2026-11-25 | 新增 **P46**；「有 connector 通路」≠「能加载任意 connector」 |
| **K191** | ★★ Fusion pruned 4 步/8 步 lite_r32：828 tensors、header 100,232 B、key/shape 全同，权重体 sha 全不同；`pruned_table_sha256` 相同 | HF Range ×6 | 2026-11-25 | 「字节同构」家族第 4 次 |
| **K192** | ★★ 社区 GGUF 家族（`Infinity-io`，Q2_K 6.7 → Q8_0 21.4 GB + UD 两档）；**本机 H3 无 GGUF 路径**（h3 目录 `gguf` 命中 0） | HF 搜索 + tree | 2026-11-25 | 缺口，不并入能力 |
| **K193** | ★★ `yichengup` tuned int8 与官方 pruned_int8 **逐键相同（932/932）**，但 metadata 声明 5 处 graft（Z-Image q_norm / LTX-2.5 q_norm / qnorm_pin / adaln none / int8 convrot 256） | HF Range + 键集比对 | 2026-11-25 | 「同名不同构」第 5 次，**连 shape 都一样** |
| **K194** | ★ ClipProj 自评边界：图像分数与 32B 无可分辨差异 ≠ 相同（余弦对可数属性盲）；32B 换 seed 重读 5.8/75 音素，v3.1 是 6.4–7.0 | ClipProj README + 头 | 2026-11-25 | 单指标不可作保真结论 |
| **K195** | ★★ **issue #56 不是「只差合入」**：fork `AugustRush/vpipe:omniref-vsa` 最新 commit `fd0b0e2`（**2026-10-21**），fork `pushed_at 10-22` → **35 天未推送**；upstream PR 数 = 0 | GitHub API ×4 | 2026-11-25 | **P45 措辞修正**：需 rebase 一个月演进 |
| **K196** | ★ sd.cpp `f296cb0`（#2419）修 RelayVSR KV graph-cut 命名（cache 名缺 `relayvsr.` 前缀致末段重算）+ DGL OOM 上抛 | commit detail | 2026-11-25 | 不可迁移（本机 RelayVSR 无 graph-cut 概念） |

## 每日知识增量（2026-11-25 06:30 · 第 29 轮 · 06:30 段）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 29 轮续；主报告对应第 **18.38** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 6 次链路）。知识编号 **K178–K184**（接 04:30 段的 K168–K177）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K178** | ★★★ **本机已装 App 二进制早已含 pruned + W4A8 通路**：`libvpipe.0.dylib`（`0.1 / 9db5dd7*0`，11-14 构建）`strings` 命中 `w4a8_to_i8` / `w4a8_convrot_dequant` / `asym_w4a8_int8` / `h3_adaln_pruned_f16` / `h3_adaln_pruned_res_f16` / 拒绝 16 宽原文；上游对应 commit `41d2789`（11-12）早于 build 日 → **已编译进去，P44 无需重编译** | `strings` + `git log -S` | 2026-11-25 | **K171 升级为「发布二进制也通」**；「本机不支持 pruned/W4A8」注销 |
| **K179** | ★★★ **Kijai `pruned_w4a8_mixed` 是本机最小可塞候选**：ref2va **11,770,657,048 B（10.96 GiB）** / fl2va 12,540,858,008 B；50 块、`[1025,8]`、AdaLN F16、**200 w4a8 + 8 int8_tensorwise**（token_refiner）。vs Comfy-Org int8 pruned 19.53 GiB → **少下 9.20 GB** | HF Range + tree | 2026-11-25 | **P44 下载量砍 47%**；磁盘余量 16 GiB → 25 GiB |
| **K180** | ★★ **同家族两种量化记录布局**：ref2va 每层旁挂 `.comfy_quant`（U8 tensor）；fl2va **只在 header `_quantization_metadata`**；本机两路都能读（`fp8-layout.cc:79-121`） | 两头对照 + 源码 | 2026-11-25 | 「同名不同构」**第三次**；判格式须双处并查 |
| **K181** | ★★★ **FastH3-VSA 权重已落地（21.33 GiB／1082 tensors，250 层 int8，每块 +`to_gate_compress` `[7168,5376]`）但本机整文件拒绝**：`grep gate_compress`=0，`untranslatable_tensor()` 全拒；上游 **issue #56**（15 文件 746 行，**Able to merge 34 天**，0 评论）失败原因逐字一致 | HF 头 + 源码 + issue #56 | 2026-11-25 | **缺口分级**：VSA = 权重齐 + PR 齐 + 只差合入（**不需改 kernel**） |
| **K182** | ★ 官方仓 11-24「误合 PR #112 → **12 分钟** revert」；非技术变更，权重零影响 | HF commits | 2026-11-24 | 纪律：`lastModified` ≠ 新权重，须看 tree sha/体积 |
| **K183** | ★ Comfy-Org 官方镜像 `model_patches/` 已收 H3 ControlNet Union 四档（8.38/4.53/4.22/2.30 GB）；本机支持仍 **0** | tree + grep | 2026-11-25 | 生态地位升级（此前仅 alibaba-pai 原始仓） |
| **K184** | ★ 社区「latent 域时间修复」独立赛道（17 帧块运动检测 + 局部 2×/3× 膨胀后二次采样，不解码到像素）；本机无对应 stage | HF README | 2026-11-24 | **待复现**；与像素域超分不同层 |

**更正**：上轮「ModelScope 的 `pruned/` 是空目录」**作废** —— `repo/files` 不递归，按 `Root=pruned` 查四个文件全在（含 818,925,468 B），与 HF 同字节。

**本轮实验**：无（生成测试与零下载实测均无新增；读头结果直接并入 K179/K181）。P44 需 60+ min 连续窗，本轮 90 min 内无法安全跑完 sync + release。

## 每日知识增量（2026-11-25 04:30 · 第 29 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 29 轮；主报告对应第 **18.38** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 5 次完整链路闭环）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K168** | ★ 上游第 5 日静默（**口径修正**）：HEAD a6a1f53，距 `commit.author.date 11-23T09:54:27Z` **1.77 天**（上轮「满 2 天」偏早）；release **v0.1.110 落后 24 天**；issue 14 全开（无一条 updated 晚于创建日）；PR=0；269 star / 36,920 KB | GitHub API 全套 | 2026-11-25 | 零增量；时间口径改为「距 HEAD commit N.NN 天」 |
| **K169** | ★★★ **LightX2V「Turbo Fusion」融合适配器**：LightX2V cm2200 ×1.0 + Pika Ref2VA Flex ×0.4 + Larry v4 step-600 EMA ×0.4 → **单个 LoRA**，4/8 步共用配方；8 变体（Full 3.78 GB / ComfyUI 5.21 GB / Lite-r32 665 MB / pruned-lite 818 MB）；**Euler + video shift 12 + audio shift 3** | HF 模型卡 + tree API + ModelScope | 2026-11-24 | **★ 与本机现役冲突**：`dance-woman-768p` 用 shift **6.0** → 不可原样换槽（P44） |
| **K170** | ★★★ **Fusion 三布局权重头零下载实测**：Full=`[32,2688]` AdaLN（完整模型）+ `[96768,32]`；ComfyUI 777 tensors（qkv `[960,5376]` 块对角 + 每模块 alpha）；**pruned = `[32,8]` + `diff_b [96768]` F32** | HF Range | 2026-11-25 | pruned 恰好是**本机支持的 8 宽** |
| **K171** | ★★★ **本机加载 Fusion-pruned 的三道门均通**：① `bind_pruned_adaln_` 仅 `c.pruned()` 时调（`.cc:4834/4897`）；② `.diff_b` 靠 `file_touches` **子串匹配**命中 `.diff`（`runtime-lora.cc:890`），`[96768]==D` 过校验（`:4537`）；③ `.alpha` 是每模块标量。**唯一硬条件 = DiT 必须 pruned**（released 基座会静默丢弃 AdaLN 分支） | 本地源码 + K170 头 | 2026-11-25 | **K163 收窄**：拒的是 16 宽，不是 pruned |
| **K172** | ★★ Comfy-Org pruned 体积：`ref2va_pruned_int8_convrot` **19.53 GiB** / fp8 19.52 / bf16 37.46 / w6a8 14.89（按名拒绝）；对照未剪枝 int8 31.70 GiB、bf16 61.72 GiB | HF tree API | 2026-11-25 | P44 的确定下载量 |
| **K173** | ★★ 本机 `docs/MINIMAX-H3.md:2529-2600` 已把 pruned 写成**一等支持**（`adaln_t_table 1025×8`、`[96768,8]`、无 SiLU、f32 求和）并规定三类 LoRA 处理（转换过/全模型训练经基 U 搬移/改时间嵌入走 released MLP） | 本地 docs（d72c22f） | 2026-11-25 | **推翻 K157 的一半**：不是「不认 pruned」 |
| **K174** | ★ `model-catalog.cc` 仍无 pruned DiT 条目（全文仅 1 处 `pruned`，是注释）→ pruned 只能手工 `hf_dir` | 本地源码 `:2502` | 2026-11-25 | K157 保留（catalog 层） |
| **K175** | ★ Fusion Lite r32 = QR-product truncated SVD，保留谱能量 98.41%/97.80%，**卡面自注「权重空间统计，非感知质量」** | HF 模型卡 | 2026-11-24 | 单指标不可作结论（与本机双判纪律一致） |
| **K176** | ★ 社区自建融合成惯例（11-24 六小时 ~15 个 H3 仓库，两个 pruned+fused 各 400+ 下载）→ **默认按 pruned 基座发布** | HF 搜索 API | 2026-11-24 | 二手，待复现；生态信号 |
| **K177** | ★ H3-Tiny 仓现状：HF 12 文件 / 14,156 下载 / 22 likes / lastModified 11-24T11:53；**ModelScope 无此仓**（record not found） | HF + ModelScope API | 2026-11-25 | K150 的 HF↔MS 逐位比对不适用 Tiny（单源） |

**本轮实验**：无生成实验；有零下载文件级实测（K170/K171，3 个头 + ~230 KB JSON，<3 min / 0 磁盘）。P44 需 20.97 GB + 0.52 GB 下载 + 29 min 生成 → 超预算，登记下轮首选。新增 **P44**。

## 每日知识增量（2026-11-25 02:30 · 第 28 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 28 轮；主报告对应第 **18.37** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 4 次完整链路闭环）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K160** | ★ 上游第 4 日静默：HEAD a6a1f53（pushed_at 11-23T11:20:51Z，**满 2 天未动**）；release **v0.1.110 落后 24 天**；issue 14 全开；PR=0；269 star / 36,920 KB（逐位同上轮）；docs/ 无 H3-Tiny | GitHub API 全套 + 本地 docs grep | 2026-11-25 | 零增量；并首次确认上游 `pruned` 标志**不区分** 50 块/42 块 |
| **K161** | ★★ H3-Tiny INT8 ComfyUI 权重正式发布（`408d92a`，11-24 11:51，+198）：17B Ref2VA/FL2VA/FewStep **各 18.1 GB**、14B OKD **15.1 GB**；W8A8+ConvRot group 256；H200 1344×768×243f DiT **~17 GB** 且速度≈bf16 | GitHub commit + HF 页 | 2026-11-24 | 补全 K155，给出确定下载体积 |
| **K162** | ★★★ **权重头零下载实测**（Range 只读 81496B header）：42 主块（0–41）、`adaln_t_table **[1025,16]**`、`adaln_proj.linear.weight [96768,16]` F32；14B INT8 FFN **[5376,9984]**（bf16 为 9792）；FewStep **无 t_table**，改双段 `.linear_1 [8,2688] + .linear_2 [96768,8]` | HF resolve + HTTP Range | 2026-11-25 | 首次拿到候选权重真实结构；方法可复用（P43） |
| **K163** | ★★★ **本机 pruned AdaLN 硬 gate**（不是缺 catalog）：`.cc:830` 要求 `time_dim == 8`，而 `time_dim` 取自 `adaln_t_table` 第 2 维（:692）→ **[1025,16] 加载即 fail**；Metal kernel `h3_adaln_pruned_f16` 亦硬编 `k<8`/`t*8` | 本地源码 + K162 头 | 2026-11-25 | **升级 K157**：根因是曲线宽度与低秩分段，P42 前置重写 |
| **K164** | ★ 14B INT8 与 bf16 **不同构**：9984 vs 9792（9792 非 256 倍数 → ConvRot 对齐 pad） | K162 头对照 | 2026-11-25 | 「INT8 = bf16 量化」假设失效，shape 比对纪律 |
| **K165** | ★★ 官方 pruned（50 块 / `[1025,8]`）与 Tiny17B 在 qkv/out_proj/fc1/fc2 **逐形状一致**，仅差「块数 50→42 + 曲线 8→16」 | HF 头对照 | 2026-11-25 | 给出上游采纳时的精确改动边界 |
| **K166** | ★ H3-Tiny 走 **50 步 + simple + 无 CFG + 不叠 turbo LoRA**；few-step 用 `linspace(1,0,steps+1)` @ **video shift 12**、默认 6 步 | README + comfyui/__init__.py | 2026-11-24 | 与本机 4/8 步不同赛道，禁止跨赛道比速度 |
| **K167** | ★ LightX2V `8bbaabd`（#1735，11-19）：RelayVSR x4 支持显式输出画布，动机即「H3 16:9 768P = 1344×768 两轴倍率不同」 | LightX2V commit | 2026-11-19 | 生态印证；本机 relayvsr-upscale 无此参数，需串 resize |

**本轮实验**：无生成实验；但有**零下载文件级实测**（K162/K164/K165，HTTP Range 读权重头，<2 min / 0 磁盘）。因 K163 已判定即使下 18.1 GB 也无法加载，下载无意义。新增 **P43**（零下载权重头核验常规化）。

## 每日知识增量（2026-11-25 00:30 · 第 27 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 27 轮；主报告对应第 **18.36** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 执行（第 3 次完整链路闭环）。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K155** | ★★ H3-Tiny 剪枝家族：AdaLN rank-8（13.0B/33.1B）+ 删 8/50 块（6–11/13/15）+ FFN 14336→9792 + OKD → 17B/14B；**17B 不训练可用**，few-step 默认 6 步；INT8 ConvRot **18.1 GB**（H200 DiT ~17 GB VRAM） | GitHub/HF `H3-Tiny` | 2026-11-24 | 权重压缩再添一族；本机仅 INT8 有磁盘可行性 → **P42** |
| **K156** | ★★ 官方投入不对称：4 步线 **v1.3（10-20）后 36 天冻结**；8 步线 **v1.2（11-12）结构性变更**（1,383,677,808→1,543,291,302 B，+11.5%）；README 11-24 单独更新仍 ⭐ 推 8 步 v1.2 | ModelScope 文件 API + HF 卡 | 2026-11-25 | 修正 K150「v1.3 即终版」→ 仅对 4 步成立；**8 步 v1.2 不可换槽** |
| **K157** | ★★ 本机 `model-catalog.cc` 无 H3-Tiny / 无 H3 causal 条目（`tiny` 全是 TAE 预览解码器） | 本地源码 | 2026-11-25 | **「社区有」≠「vpipe 能用」**（第 28 轮 K163 升级为 loader 硬 gate） |
| **K158** | ★ LightX2V #1749：causal 流式 `audio_latest_chunk_num=9`（视频仍 2），`kv_cache_max_t_rope` 7→9；仅影响 6 个 realtime_768p 配置 | PR diff | 2026-11-23 | 音频长期连贯性优先；本机无 causal 能力 |
| **K159** | ★ ComfyUI #17940：MPS 不支持 `padding_mode="border"` → clamp[−1,1] + `zeros`（bilinear+align_corners 下等价） | PR | 2026-11-23 | **可迁移的 MPS 绕法**（自研 warp/光流算子可套用） |

**本轮实验**：无（时间预算优先最小闭环）。P42/P40 均超预算或受阻。

## 每日知识增量（2026-11-24 06:30 · 第 26 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 26 轮；主报告对应第 **18.35** 节。
> ★ 本轮由 **P39 launchd + 无头 CLI** 实际执行（非主对话代跑），是 P39 方案的首次完整链路闭环。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K148** | ★ 上游第 2 日静默：HEAD 仍 a6a1f53；release **v0.1.110 落后 main 22 天**；issue 14 全开；**PR=0**；266 star | GitHub API 全套 | 2026-11-24 | 零增量，K135/K115 延续 |
| **K149** | ★★ a6a1f53 统计口径冲突：上轮记「85 文件 +17617」，本轮 detail API = **total 20003 / +19494 / −509** | commits detail API | 2026-11-24 | 不改历史正文，统一改引 detail 口径 |
| **K150** | ★ 权重仓量化：**1,793,937 下载 / 1,235 likes / 75.8 GB / 30 文件**；lastModified **11-16** → **无 v1.4** | HF api | 2026-11-24 | 印证「v1.3 为终版」，8 天无更新 |
| **K151** | ★★ 4 步 v1.0–v1.3 的 768p bf16 **LFS size 全部 = 1,383,677,808 B**（sha 各异）→ 字节同构，**可原槽 A/B 不改配方**；fp8 精确 34,023,114,720 B | HF tree API | 2026-11-24 | P40 前置成立；解释 18.21 互换可行 |
| **K152** | ★★ 社区「4 步不够」（非官方）：作者推荐 >4，larryvrh 称 6–8 更佳、ModelTC 示例默认 8 步；5080 单机 1035→487→193 s；核心指标 time-per-usable-clip（5× 只兑现 2×） | minimax3.com | 2026-08-15 | **与本机 18.21 静态结论冲突** → 「4 步画质不降」须限定「静态/慢运动」，待复现 |
| **K153** | ★★ DWD 原论文 arXiv **2611.22287**（Stanford，11-17）：Wan **warping error −23%**；ImageNet **FID 1.55→1.43**；仅微调末几 block + 线性 head | arXiv abs | 2026-11-17 | 印证 K117/K129；为 P36/P37 提供降本依据 |
| **K154** | ★★★ P39 对照实证：**04:30 槽流中断失败（cb_exit=0 假成功，兜底正确）/ 06:30 槽全链路成功**；`ps` 中同命令行子进程是**看门狗 shell** 非双开 | 本机 logs | 2026-11-24 | K147 防御有效；新增 P41（流中断自动重试） |

**本轮实验**：无（时间预算优先最小闭环）。**唯一可复现项 K151 已登记 P40**（需 1.38 GB + 29 min，超预算）。

## 每日知识增量（2026-11-22 01:00 · 第 21 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 21 轮；主报告对应第 **18.23** 节。

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K111** | ★★ 上游 HEAD → `d347808`（2026-11-21）：DeepSeek-V4.1 GGUF 视觉输入 + Pillow 精确 bicubic。纯 LLM/VLM 侧，视频线零变化 | GitHub API | 2026-11-21 | 本机 build 落后基准更新为 d347808 |
| **K112** | ★★★ h3.c 对比表进 README 门面：960×544/124f/6 步 bf16 三机全胜，**M5 Pro 24GB：5m29s vs 7m11s（快 24%，本机同档）** | 上游 README @ d347808 | 2026-11-21 | 印证+扩展第 14 轮 K57；本机 6m38s 实测同量级 |
| **K113** | ★★ h3.c 表历史上有过口径刷新（7703614，2026-08-19 旧值无 M5 Pro 行）→ 引用必须带 commit/日期 | commit 考古 | 2026-08-19 | 上游性能数字是活的，禁止无版本引用 |
| **K114** | ★★ h3.c 在 16/24GB 机需 `--ssd-streaming`（bf16），int8 需全驻留 → 与 vpipe 统一内存流式是两种架构 | 上游 README | 2026-11-21 | 跨运行时只能比 bf16 口径 |
| **K115** | ★ #59 上游已实现（d72c22f）但未关 issue（open/0 评论）→ issue 状态维护滞后于代码 | GitHub API issues | 2026-11-22 | #55–59 零回复维持；新增「关闭滞后」观察 |
| **K116** | ★ HyperFlow H3 Flash 社区面复验（13.7B 剪枝权重路线，与 vpipe 全量 33B+适配器不同族），无新事实 | webdiga 等 4 源 | 2026-11 | 固化「权重压缩 vs 步数蒸馏」区分纪律 |

## 每日知识增量（2026-11-21 17:26 · 第 20 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 20 轮；主报告对应第 **18.20** 节。

### 本轮三条主线

1. **上游静默被打破**：`d72c22f`（2026-11-20，114 文件 +50265 行）——RelayVSR 2×、H3 调度器栈大改、PDD 自定义采样。K84「短期无官方补丁」作废。
2. **P28 实验**：scheduler 端口（iport 4）对 H3 生效判决 + 跨 build 锚点陷阱。
3. **本地树快进 + 重编译**：33cda00 → d72c22f（`0.1 (d72c22f*0)`，软链农场 /tmp/vp28）。

### 逐条新增知识

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K90** | ★★★ 上游新 commit `d72c22f`，静默期结束 | GitHub API | 2026-11-20 | 重心回到「核心追更 + 插件」双线 |
| **K91** | ★★★ RelayVSR 原生 2×（issue #59 落实）；ComfyUI int8 档 4.3 GB；2× working set 按「输出」计 → 960×540→1080p 仅 7.8 GB | RELAYVSR.md + diff | 2026-11-20 | **2×→1080p 在 24 GB 舒适** → P29 候选实验 |
| **K92** | ★★★ scheduler-select 新增 normal/sgm_uniform/beta/linear_quadratic；H3 真读 iport 4；shift 由 model config 的 `schedule_shift` 决定 | scheduler-select diff | 2026-11-20 | σ 轨迹第三入口成型 |
| **K93** | ★★ `lcm` ≡ `dmd`（上游官方确认） | minimax-h3-denoise diff | 2026-11-20 | ✅ 印证 P18 |
| **K94** | ★★ PDD 开放 sigmas/scheduler/sampler + `step_head_of` | MINIMAX-H3.md | 2026-11-20 | H3-Image 对照入口打开（磁盘仍阻塞） |
| **K95** | ★★ TaoMate-H3 适配器进 TP rank（当普通 LoRA 切分） | transformer.cc diff | 2026-11-20 | 跨机 TP + adapter 可行 |
| **K96** | ★ top-p 部分排序（~10ms → 前缀） | sampler.cc | 2026-11-20 | 文本侧提速 |
| **K97** | ★ 长提示词 band 化（4dc36b7）进本机 build | commit msg | 2026-11-16 | P28 换轨迹的可能原因之一 |
| **K98** | ★★★ **跨 build 锚点作废**：33cda00 配方跑 d72c22f 与历史锚点逐位不同（首帧 SSIM 0.344 = 换场景）；d72c22f 自身确定性成立（复跑逐位相同） | P28 实验 | 2026-11-21 | **修订 13.2**：锚点只在同 build 内跨轮次有效 |
| **K99** | ★★ **P28 判决**：scheduler 端口生效；sgm_uniform HF jitter −3.77%（vs dmd −12.8%，不作为沸腾解法）；σ 细扰同场景（首帧 SSIM 0.952） | P28 实验 | 2026-11-21 | **修订 13.9**：σ 网格差是连续谱 |
| **K100** | ★★ d72c22f 默认 denoise 不再打 echo 行（接端口才打） | 日志对照 | 2026-11-21 | 回显核对要按版本 |
| **K101** | ★ 社区实测面：16GB mini 流式跑通 / M5 Ultra 1m35s@960×544 / Mac 比 4090 慢一个量级 / H3 License 排除美欧英韩（大陆合规） | 4 源 | 2026-11 | 印证本机 24 GB 定位 |

## 每日知识增量（2026-11-20 20:30 · 第 19 轮）

> 本节由夜间自动任务累积写入（**只追加**）。完整版见 `vpipe-daily-knowledge.md` 第 19 轮；主报告对应第 **18.19** 节。

### 本轮三条主线

1. **上游静默期延续**：主仓库 `4dc36b7` (2026-11-16) 至今已维持 4 天零增量，证明核心逻辑已进入极其稳定的 ABI 冻结期。
2. **插件生态深度盘点**：针对 `vpipe-sensenova-u1.5` 与 `vpipe-ming-image` 进行 ABI 兼容性与加速特性对账。
3. **M5 性能上限确证**：从官方插件测试中提取了 M5 Pro 的 `i8_gemm` 理论收益（1.46x 投影层加速）。

### 逐条新增知识

| # | 知识 | 来源 | 日期 | 对既有结论的影响 |
|---|---|---|---|---|
| **K84** | ★★★ **上游 HEAD 4 日未动**：维持在 `4dc36b7`。实验室应假定短期内无官方 Bit-for-bit 补丁，继续维持 `autotune:false` 纪律。 | GitHub API | 2026-11-20 | **战略建议**：重心全面转向「插件适配」而非「核心追更」。 |
| **K85** | ★★ **ABI 8 契约锁死**：SenseNova 与 Ming 插件均要求 **ABI 8**。旧版主机（ABI 2/4/5）将因 `ABI mismatch` 拒绝加载。 | 插件 README | 2026-11-20 | **环境核验**：实验室本地 build `33cda00` 需确认其 ABI 槽位（推测为 8）。 |
| **K86** | ★★ **i8_gemm 的 I/O 隐身效应**：M5 上投影层加速 1.46x，但端到端不显示（55s vs 56s），因 33GB 权重流播受限于磁盘/内存吞吐。 | `vpipe-sensenova-u1.5` | 2026-11-20 | ✅ **印证 §18.14**：纯算力优化在 24GB 机器上的边际收益有限。 |
| **K87** | ★★ **Ming-Image 透明通道契约**：该插件通过 prompt 固定前缀（如 `RGBA, 4-channel`）触发 VAE 4 通道逻辑。 | `vpipe-ming-image` | 2026-11-20 | **新增能力**：为实验室开启「设计类/透明背景」生成路径。 |
| **K88** | ★ **Issue #55 零回复确认**：开放 32 天，依然无官方人员介入。 | GitHub Issues | 2026-11-20 | ✅ **确认**：实验室自建的 σ 网格公式与 `dmd` 判决是目前唯一的定量依据。 |

## 通用注意事项（每次任务都要遵守）

1. **重任务串行**。本轮实测：并行下载 66 GB 模型时，同期跑的生成流水线被杀掉（日志一切正常后无错消失）。下载结束后重跑即通过。
2. **磁盘下限 15 GiB**。低于这个数就要先清理。本轮实测下载到 14 GiB 时已很紧张。
3. **每个生成任务结束后立刻抽帧目检**，不要只看日志。日志正常 ≠ 画面正常。
4. **固定 seed**，便于对照。
5. **改完配置先核对四个必写项**：`save-video` 的 `output_url`、两路输入边、两个 stage 的 `frames` 一致、`i8_gemm: true`。
6. **每个结论都要有量化证据**（SSIM/PSNR + 第三方模型复核），不要只靠目视。
