# vpipe 后续计划任务清单

> 基于 GitHub `tgo-app-dev/vpipe`（`main` @ `4dc36b7`，**2026-11-16**；**已装 App `0.1 (9db5dd7*0)` 落后 12 个 commit，但本地源码树 `33cda00` 只落后 2 个** —— 见第 2 轮修订）、官方 `docs/MINIMAX-H3-zh-cn.md`（+ 英文版 `docs/MINIMAX-H3.md` 249 KB）、官方 release、issue（**至少 59 条**），以及 YouTube/社区实测资料整理
> 生成时间：2026-11-14 · **最近更新：2026-11-26 02:30（第 30 轮 · 官方 H3 蒸馏 best practices 落地 + 4 步适配器 alpha 从 128 掉到 8 + ClipProj 文本编码器路线与本机 connector 契约不符）**
> 机器：Mac mini M5 Pro / 24 GB / 15 核 / macOS 27.2

---

## 状态看板（2026-11-26 02:30 更新）

| 轮次 | 状态 | 摘要 |
|---|---|---|
| **第 30 轮 · 2026-11-26 02:30 夜间知识同步（官方蒸馏配方 + alpha 语义换槽陷阱 + ClipProj 契约判定）** | ✅ **完成（P39 无头 CLI 第 7 次完整链路：02:30 槽准时触发，守卫 R=30）** | 上游静默第 6 日（HEAD a6a1f53 = 距 commit **2.36 天**；release v0.1.110 落后 **24 天**；issue 14 全开；**PR=0**；**273 star** +3）。**★★★ K186/K187 LightX2V 官方发布 H3 蒸馏 best practices**（`7fc25cd` / PR #1730，双任务双阶段，**FL2AV shift 6/3、Ref2AV shift 12/3**，dCM 1500 iters LR 2e-5 → PDMD+GAN 3000 iters）；**★★★ K188 4 步家族 v1.2/v1.3 的 `__metadata__.alpha` 从 128 → 8**（形状全同、强度 1/16）→ **K151 收窄**；**★★★ K189/K190 ClipProj**（sd.cpp 已实现，4B 编码器替 32B，15.7→4.5 GB）但**本机 connector 四条契约全不符** → 新增 **P46**；**K191 Fusion pruned 4/8 步同头不同体**；K192 社区 GGUF 家族（本机无路径）；K193 tuned int8 键集全同但 5 处 graft；**K195 P45 措辞修正**（fork 停在 10-21，需 rebase 而非「点 Merge」）；K196 sd.cpp RelayVSR KV graph-cut。详见报告 18.39 节 |
| **第 29 轮 · 2026-11-25 06:30 夜间知识同步（本机二进制实装确认 + W4A8 混合档 + VSA 缺口分级）** | ✅ **完成（P39 无头 CLI 第 6 次链路：06:30 槽准时触发；04:30 段未 sync 未推进，本轮补完闭环）** | 上游零增量（HEAD a6a1f53 = 距 commit **2.81 天**；release v0.1.110 落后 **24 天**；issue 14 全开 0 回复；PR=0；**270 star** +1）。**★★★ K178 本机 11-14 构建的 `libvpipe.0.dylib` 早已含 `h3_adaln_pruned_f16` / `w4a8_to_i8`** → 「本机不支持 pruned/W4A8」注销；**★★★ K179 Kijai `pruned_w4a8_mixed` 仅 10.96 GiB**（vs Comfy-Org int8 19.53 GiB）→ P44 下载量砍 47%；K180 同家族两种量化记录布局；**★★★ K181 FastH3-VSA 权重 21.33 GiB 已落地，但 issue #56（Able to merge 34 天）未合 → 本机整文件拒绝**；K182 官方仓误合/revert；K183 Comfy-Org 收 ControlNet Union；K184 社区 latent 域时间修复（待复现）。**新增 P45（VSA 跟踪）**；**修技能包分叉坑**（18.38.6 坑①）。详见报告 18.38 节 |

| **第 29 轮 · 2026-11-25 04:30 夜间知识同步（Turbo Fusion 融合适配器 + 本机 pruned 通路分层）** | ✅ **完成（P39 无头 CLI 第 5 次完整链路：04:30 槽准时触发、检索→固化→报告→sync→release 闭环）** | 上游静默第 5 日（HEAD a6a1f53 = 距 commit 1.77 天 / release v0.1.110 落后 **24 天** / issue 14 全开 / PR=0 / 269 star）。**★★★ K169「Turbo Fusion」**：LightX2V + Pika Flex + Larry v4 合成单 LoRA，4/8 步共用配方，**video shift 12**（与本机现役 6.0 冲突）；**★★★ K170/K171「pruned 通路分层」**：设 8 宽 + `.diff_b` 在本机可读（源码三道门逐一核对），只有 16 宽（H3-Tiny）被拒 → **K163 收窄**；K172 pruned_int8 19.53 GiB；K173 文档已把 pruned 写成一等支持；K174 catalog 仍无条目；K175 Lite r32 谱能量≠画质；K176 社区自建融合成惯例。**新增 P44（Fusion-pruned 本机实测，下轮首选）**。详见报告 18.38 节 |
| **第 28 轮 · 2026-11-25 02:30 夜间知识同步（H3-Tiny INT8 权重头零下载实测 + 上游第 4 日静默）** | ✅ **完成（P39 无头 CLI 第 4 次完整链路：02:30 槽准时触发、检索→固化→报告→sync→release 闭环）** | 上游静默第 4 日（HEAD a6a1f53 满 2 天未动、release v0.1.110 落后 **24 天**、issue 14 全开、PR=0、269 star 逐位同上轮）。**★★★ 本轮方法突破：用 HTTP Range 只读 safetensors header（0 下载）**——K162（H3-Tiny 四个 INT8 文件的 42 块 / `adaln_t_table [1025,16]` / 14B INT8 FFN 9984 / FewStep 双段低秩全量结构）；**K163（本机 pruned AdaLN 硬 gate：`time_dim != 8` 即 fail，非「缺 catalog」而是「loader 不认」）**；K164（14B INT8 9984 ≠ bf16 9792，ConvRot group 256 对齐）；K165（Tiny17B 与官方 pruned 50 块仅差「块数+曲线宽」两处）；K166（H3-Tiny 走 50 步/shift12，与本机 4/8 步不同赛道）；K167（LightX2V #1735 RelayVSR x4 显式画布）。P42 前置重写。详见报告 18.37 节 |
| **第 27 轮 · 2026-11-25 00:30 夜间知识同步（上游第 3 日静默 + 官方迭代方向量化）** | ✅ **完成（P39 无头 CLI 第 3 次完整链路：00:30 槽准时触发、守卫 RUN/R=27、检索→固化→报告→sync→release 闭环）** | 上游静默第 3 日（HEAD a6a1f53 两天未动、release v0.1.110 落后 **24 天**、issue 14 全开 0 回复 0 处理、PR=0、269 star）。K155（★★H3-Tiny 剪枝家族：AdaLN rank8 + 删 8/50 块 + FFN 9792，17B 不训练可用，INT8 18.1 GB）；K156（★★**官方 4 步线 10-20 后 36 天冻结、8 步线 v1.2 结构性变更不可换槽**）；K157（★★**本机 catalog 无 Tiny/causal 条目**）；K158（★LightX2V 因果流式音频历史 9 chunk）；K159（★ComfyUI MPS warp 绕法可迁移）。新增 **P42**。详见报告 18.36 节 |
| **第 27 轮 · 2026-11-25 00:30 夜间知识同步（上游第 3 日静默 + 官方迭代方向量化）** | ✅ **完成（P39 无头 CLI 第 3 次完整链路：00:30 槽准时触发、守卫 RUN/R=27、检索→固化→报告→sync→release 闭环）** | 上游静默第 3 日（HEAD a6a1f53 两天未动、release v0.1.110 落后 **24 天**、issue 14 全开 0 回复 0 处理、PR=0、269 star）。K155（★★H3-Tiny 剪枝家族：AdaLN rank8 + 删 8/50 块 + FFN 9792，17B 不训练可用，INT8 18.1 GB）；K156（★★**官方 4 步线 10-20 后 36 天冻结、8 步线 v1.2 结构性变更不可换槽**）；K157（★★**本机 catalog 无 Tiny/causal 条目**）；K158（★LightX2V 因果流式音频历史 9 chunk）；K159（★ComfyUI MPS warp 绕法可迁移）。新增 **P42**。详见报告 18.36 节 |
| **第 26 轮 · 2026-11-24 06:30 夜间知识同步（P39 无头 CLI 首次跑完整链路）** | ✅ **完成（P39 实测第 5 次成功：检索→固化→报告→sync→release 全链路在无头 CLI 内闭环；04:30 槽第 4 次实测因流中断失败，兜底正确不推进）** | 上游第 2 日静默（HEAD a6a1f53、release v0.1.110 落后 22 天、issue 14 全开、PR=0）。K148（静默复核）；K149（★a6a1f53 行数口径冲突 19494 vs 17617）；K150（权重仓 1.79M 下载/75.8 GB/8 天未更新→无 v1.4）；K151（★★4 步全版本字节同构→v1.3 可原槽 A/B）；K152（★★社区「4 步不够」口径，与本机静态夹具冲突）；K153（★★DWD 原论文 arXiv 2611.22287：warping −23%、FID 1.55→1.43）；K154（★★★P39 04:30 失败/06:30 成功的对照实证）。详见报告 18.35 节 |
| **第 25 轮 · 2026-11-24 00:06（用户手动触发 00:30 槽失败 → 主对话代跑）** | ✅ **完成（★★★ 首次 daemon.log 级坐实「会话空壳/unknown_interrupted」根因：非配置/非脚本错，是自动化会话被主对话抢占中断；force→检索→固化→sync→release 全链路代跑闭环）** | 上游静默约 14h（HEAD a6a1f53、release v0.1.110、issue 14 全开零回复、PR=0）。K139（会话空壳日志实证）；K140 FlashGen 4-step LoRA（VSD rank64+base_schedule）；K141 Character Swap LoRA V1.5；K142 Turbo 三档耗时+双 shift 印证；K143 vLLM 双分区（本机不采信）。K140–143 社区二手待复现。详见报告 18.29 节 |
| **第 24 轮 · 2026-11-23 23:55（4 槽立即运行/自动运行可执行化 + 逐个测试 + 用户修正去重）** | ✅ **完成（★★★ nightly_guard.sh：判断逻辑从 prompt 文本升级为可执行+可测；4 槽 × 4 场景测试全通过；★ 23:55 按用户要求去掉「今天已跑跳过」，点击/到点均执行）** | 上游静默约 6h（HEAD a6a1f53）、release v0.1.110。K136/K137（issue #59 RelayVSR_X2 原生 2× 未合入）、K138（守卫脚本）。**修正后语义**：4 槽独立执行，仅并发锁(exit=11)拒绝，否则 check/force 都 RUN(0)；last_run 仅审计。修两处 bash 坑。详见报告 18.27 + 18.28 节 |
| **第 23 轮 · 2026-11-23 23:20（04:30 槽故障诊断后手动补跑）** | ✅ **完成（★★★ 上游 a6a1f53 重大增量 +17617 行：vpipe 原生 pi-H3 2/4 步适配器 + DWD 免解码 + LoRA 训练）** | 04:30/00:30 槽今天未触发（会话空壳/无文件，非配置错误=本机调度架构限制）→ 手动补跑。增量 K127–K135：HEAD d347808→a6a1f53（11-23 17:54）；pi-H3 适配器原生进主仓（K128）；DWD 落地 f32 0.0053（K129）；train-lora + 调制表折叠 26GB→174MB（K130/K131）；Dials（K132）；三处内存记账修正（K133）；8 条新流水线（K134）；release 仍 v0.1.110 差距扩大（K135）。**★★★ 推翻 K121**（「上游零迹象」寿命仅 1 天）。详见报告 18.26 节 |
| **2026-11-23 21:23 续作（768p Negative + RelayVSR 保真重制）** | ✅ **完成** | 768p 重生成换场景且同尺度清晰度 −32.6%（K123，不交付）→ RelayVSR 2× 保真重制 960p（16.6s，锐度×2.7，同场景，K124，交付）→ ★★★ P33 判据重大修订：周期脉动源片固有非超分引入（K125/K126），绝对阈值作废改比值判据。详见报告 18.25 节 |


| 任务 | 状态 | 结果 |
|---|---|---|
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
| **第 8 轮 · 2026-11-18 23:50 夜间知识同步** | ✅ **完成（★★★ P22 判决：FlashVSR 原生 Metal 4× 超分真机跑通 + 「它是细节生成器，不是保真放大器」）** | 检索 **18 类源**（GitHub API × 5：commits/releases/**issues+PR**/**branches**/**owner 全部仓库** + ModelScope API × 2 + **本地源码 × 5**：`flashvsr-model-config-stage.cc` / `flashvsr-src-encoder-stage.cc` / `flashvsr-family.h` / `model-registry.cc` / `flashvsr-src-encoder` + 上游官方文档 × 2（`platform.minimax.io` 模型页 + self-host 指南）+ SiliconFlow 公告 + 社区 × 10）。**上游仍零增量**（HEAD `4dc36b7` / release v0.1.110 / 31 issue / **0 PR** / **1 branch** / #55 开放 30 天 0 评论）；ModelScope `lightx2v/Minimax-h3-Turbo` 仍 31 文件 / 26 safetensors。**★ 四个关键增量**：① **★ P22 判决（见下）**；② **★ MiniMax H3 Max = fal.ai 托管、权重未开源**（官方模型页 + 3 源印证）→ 「生态有」但只有托管形态；③ **★ SiliconFlow 2026-11-10 上线 MiniMax-H3 官方 API**（`duration` 5–15 s / `resolution` 480p|768p / `images` 用 `role`），且 **`negative_prompt` / `image_size` 传入不报错但被忽略** → **跨生态印证「静默失效」是通病，不是 vpipe 专利**；④ **★ 官方 self-host 指南明写 H3 部署基线「excludes H3-Context-IR and the complete 2K Workflow」** → **第 1 轮「2K 未开源」是官方口径，不是本实验室的悲观**。**实验（P22 · FlashVSR v1.1，25 帧 / 1280×768 / 45.5 s）**：**★ 本实验室第一次真机跑通上游自带原生 Metal 视频超分**（拖了 3 轮，本轮磁盘回升到 32 GiB 才解锁）。**★ 三条量化判决**：**① 它确实生成了插值给不出的细节**（纹理量 13.00 → 163.80 = **12.6×** / +1160%，且纹理/噪点比 153.7 **高于**真值 144.3 → 是结构化毛发纹理不是噪点）；**② 但它不是「还原」而是「编造」**（对原始 768p 的 SSIM **比纯插值低 0.0506**、PSNR **低 4.05 dB**；真值纹理量的 **1.76×** 就是编造量）；**③ 代价是时序不稳**（frame diff **+37.4%**，HF jitter 0.3066→0.3410，**比真值本身还高 6.1%**）。**★ 复现性判决**：`framemd5` **不同**（不逐位相同）但**指标漂移 ≈ 0**（+0.02%/0.00%/+0.01%/−0.00%）—— 原因：**flashvsr 家族的 sampler/scheduler/negative 全部惰性** → **`autotune` 无可调对象、日志无回显** → **修订第 3 轮 11.1 的适用范围**。**★ LFM3-VL 复核**：Q1场景 ✅ / Q2 纹理粗判 **❌ 说反了**（已知缺陷 ② 再现）/ Q3 1:1 判读 ✅ **正确指出「原图里没有的、像 AI 编造的纹理」** / Q4 运动漏检。详见报告第 **18.6** 节 |

### 待验证登记（第 30 轮 · 2026-11-26 02:30 更新）

| 任务 | 优先级 | 前置 | 说明 |
|---|---|---|---|
| **P46 ★ ClipProj 文本编码器替代（4B 替 32B）** | 中 | **本机契约四条全不符（K190）**：类名限 `PH3ImageTextConnector`、位置限 `text_encoder/../text_connector/config.json`、张量名限 `proj.weight/input_mean/input_std/output_mean/output_std/sink_embedding`、全 F32；ClipProj 是「单文件 6 张量 / F16 / `W [2560,5120]` / 单 tap 24」。且结构不同：本机 **N-tap 拼接 → 一次投影**，ClipProj **单 tap → 一次投影** | **K189**：sd.cpp `5fa203c`（#2410，11-25）已实现 `ClipProjConnector`；**K194** 作者自述「图像分数与 32B 无可分辨差异 ≠ 相同」。收益：24 GB 机器文本编码器 15.7→4.5 GB（腾 ~11 GB）。两条路：① 打包适配（改名+转 F32+造 config，**须先确认单 tap 语义等价**）；② 等上游。成本：<1 GB 下载 + 代码核对，**不改 kernel** |
| **P44 ★ Fusion-pruned 本机实测（W4A8 档）· 前置 4 条** | **高（下轮首选）** | ① 清 `minimax_h3_fl2va_bf16.safetensors.part`（18.3 GB 半成品）→ 余 55 GiB；② 下 `Kijai/MiniMax-H3-experimental:minimax_h3_ref2va_pruned_w4a8_mixed`（**10.96 GiB**）+ `lightx2v/Minimax-H3-Turbo-Fusion:pruned/…_4step_lite_r32_pruned_comfyui`（818,925,468 B，**K191 取 4 步档**）；③ **`video_shift` 6.0 → 12.0**（K187 **官方 Ref2AV 训练分布**，非单纯卡面）；④ **核 Fusion LoRA 的 alpha 语义**（K191：`default_training_alpha 32.0`、`output_alpha_counts {"32.0":207,"96.0":52}`，与本机 `alpha/rank` 折算式对齐） | **K178** dylib 已含 `w4a8_to_i8` + `h3_adaln_pruned_f16` → **无需重编译**；**K179** 比 Comfy-Org int8（19.53 GiB）少下 9.20 GB；**K180** 两套记录布局本机都能读；**K174** catalog 无条目 → 手工 `hf_dir`；**K171** 唯一硬条件是 DiT 为 pruned。**K188 新增纪律**：三变量（LoRA/基座/shift）同时动会不可归因 → 建议先跑「只换 shift」对照臂。**成本**：下载 15–25 min + 生成 29 min ≈ 55–60 min |
| **P45 ★ FastH3-VSA（gate_compress）缺口跟踪** | 低 | **K195 修正**：无（只盯 fork 分支，且合入前需 rebase 一个月演进） | **K181**：`Kijai/…:minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot`（21.33 GiB / 1082 tensors / 250 层 int8_tensorwise）已落地社区，但本机 `grep gate_compress` = **0**，`untranslatable_tensor()` 对无 native 名 tensor **整文件拒绝**。上游 **issue #56**（`AugustRush/vpipe:omniref-vsa`，15 文件 746 行，GitHub 报 **Able to merge**，2026-10-22，**0 评论 / 已 34 天**）的失败原因与实测逐字一致。⇒ 与 P42 不同类：**不需改 kernel，只需名字映射合入**。合入后本机需更新 build 才能跑 |
| **P42 H3-Tiny 剪枝家族本机可行性** | 中 | ⛔ **阻塞（K163 重写）**：不只是「catalog 无 h3_tiny 条目」，而是 **loader 硬 gate** ——`metal-minimax-h3-transformer.cc:830` 要求 `pruned() && time_dim == 8`，而 `time_dim` 取自 `adaln_t_table` 第 2 维；H3-Tiny 是 **[1025,16]** → 加载即 fail。Metal kernel `h3_adaln_pruned_f16` 亦硬编码 `k<8` | **K162 权重头实测**：42 块（0–41）、`[1025,16]` F32、`adaln_proj.linear.weight [96768,16]`；14B INT8 FFN **9984**（bf16 是 9792，ConvRot group 256 对齐）；FewStep 版无 `adaln_t_table`，改双段 `.linear_1 [8,2688] + .linear_2 [96768,8]`。**K165**：与官方 pruned（50 块 / [1025,8]）在 qkv/out_proj/fc1/fc2 上逐形状一致 → **只差「块数自适应 + AdaLN 宽度参数化」**。**下一步不需要下载**：① 向上游提 issue/PR 支持任意宽 pruned 曲线；② 或本机打补丁把常量 8 改参数（kernel + 校验双改，`.h:138-142` 已有 `curve_grid` 变量可复用）。**不建议自行改源码**（会与上游 a6a1f53 冲突） |
| **P39 定时任务会话空壳根治** | 高 | ✅ **实质闭环（2026-11-25 02:30，第 28 轮第 4 次完整链路）**：launchd + 无头 CLI 连跑 4 轮（R=26 / R=27 / R=28）。04:30 槽曾实测因 `Upstream response stream was interrupted` 失败、兜底正确删锁不推进（K154） | 方案=launchd + codebuddy 无头 CLI 独立进程绕开会话层。已破四关：K145(bundle 分派)/K146(模型 ID 别名)/K147(CLI 僵死占锁+看门狗)/K154(流中断兜底)。**残留风险：上游长连接偶发中断，无重试机制** → 见 P41。详见报告 18.30–18.37 |
| **P40 4 步适配器「运动场景」验证 + v1.3 换槽 A/B** | 中 | 待验证（合并两项）。**K156 限定**：4 步线自 10-20（v1.3）后冻结 36 天，换槽 A/B 价值下降；8 步 v1.2 是结构性变更、**不可**换槽。**K166**：H3-Tiny 的 50 步/shift12 与本路线不同赛道，不可混比。**K188 新增前置**：换槽前必读 `__metadata__.alpha`——v1.0/v1.1=**128**、v1.2/v1.3=**8**，形状全同但等效强度差 16 倍；不核 alpha 会把 v1.3 误判为「效果变差」 | ①**K152**：社区称 4 步在快/大运动会糊成拖影（二手待复现）；本机 18.21 的「4 步细节能量 170.6 > 8 步」是**静态/慢速夹具**，需运动夹具复测定稿。②**K151/K156**：v1.3 与 v1.2 字节级同构可换槽，但 4 步线已冻结 → **优先做运动夹具复测，换槽降为可选**。**成本**：+1.38 GB 下载 + ~29 min 生成 |
| **P41 P39 上游流中断重试** | 中 | 待办（K154） | 04:30 槽 `Upstream response stream was interrupted` 导致空跑 4 min 54 s；`cb_exit=0` 掩盖失败。建议：runner 在「cb_exit=0 但 round 未推进」时**自动重试 1 次**，而非直接删锁等下个槽 |
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
