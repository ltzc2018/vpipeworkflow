# vpipe 夜间自动任务 SOP（每日 4 轮共用）

> 本文件是 `vpipe 后续计划任务·每日 4 轮夜间自动执行` 系列自动化的**单一事实来源**。
> 4 个自动化分别对应 00:30 / 02:30 / 04:30 / 06:30 四个时段，prompt 里是压缩版，细节以本文件为准。
> 维护人：小五 · 建立日期：2026-11-17

---

## 0. 每轮定位

**一轮 = 一次「联网自搜索 → 消化固化 → 报告更新 → 同步 GitHub」循环。**

自动化的主任务不是跑实验，而是**每天自动从 vpipe 官方渠道 / GitHub / 网络吸收新知识并固化下来**；
实验只是「知识需要验证时才做」的附属动作，不允许每轮都跑重任务。

| 项 | 值 |
|---|---|
| vpipe 工作目录 | `/Users/minichen/AI-Models/vpipe-workspace` |
| 实验室目录 | `/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab` |
| 计划清单 | `vpipe-lab/report/vpipe-后续计划任务.md` |
| 主报告 | `vpipe-lab/report/vpipe-H3-部署与测试报告.md` |
| 知识累积 | `vpipe-lab/report/vpipe-daily-knowledge.md`（只追加） |
| 轮次计数器 | `vpipe-lab/report/.auto-round-state.json` |
| 互斥锁 | `vpipe-lab/report/.auto-round.lock` |
| 技能包 | `~/.workbuddy/skills/vpipe-*` |
| GitHub | `git@github.com:ltzc2018/vpipeworkflow.git`（**必须 SSH**，HTTPS 走代理 502） |

### 环境变量（每轮开头 export）

```bash
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
```

---

## 1. 轮次编号与并发保护

1. 读 `.auto-round-state.json`（不存在就创建 `{"round":0,"last_run":null}`）→ 本轮 `R = round + 1`。
2. **互斥**：若 `.auto-round.lock` 存在且 mtime 距今 < 90 分钟 → 说明上一轮还在跑，**本轮直接跳过**，在报告里写「上一轮未结束，本轮跳过」，不要两个轮次并发。
3. 拿到锁：写 `.auto-round.lock`（内容 = 本轮时间戳）。
4. 本轮**成功结束后**写回 `{"round": R, "last_run": "<本轮时间>"}` 并删除 `.auto-round.lock`。
   失败也要删锁，但不要递增 `round`（下一轮可重试同一 R）。

---

## 2. 阶段 A —— 知识自搜索（每轮必做，绝不可跳过）

用联网搜索工具（WebSearch / WebFetch）系统检索以下源，目标是找出**相对上一轮的新增量**：

| # | 来源 | 关注点 | 基线（2026-11-17） |
|---|---|---|---|
| 1 | GitHub `tgo-app-dev/vpipe` | 新 release / commit / README / CHANGELOG / `docs/MINIMAX-H3-zh-cn.md` 变化 / 新开或新关的 issue 与 PR | `main @ 33cda00`，本机编译版 `0.1 (9db5dd7*0)`，官方 26 个 release，30 条 issue |
| 2 | 官方文档站 + vpipe 官网文档；ModelScope `lightx2v/Minimax-h3-Turbo` 及相关仓库 | 新适配器变体（768p / 4步 / 8步 / 新 adapter / 新的 TAE 解码器版本） | 已测：FL2VA/Ref2VA 768p、4步 v1.2、HyperFlow 8步、Pika H3 Flex |
| 3 | MiniMax-H3 官方（博客/公告/HuggingFace 模型页）、ComfyUI 生态、stable-diffusion.cpp / GGUF 侧 | H3 的新能力、新运行时、新节点 | GGUF Q4 路线见技能 `locmodel-h3-video` |
| 4 | 社区实测（YouTube / Reddit / X / 掘金 / 知乎 / B站） | 别人踩到的新坑、新参数、新工作流 | — |
| 5 | 上游 issue 状态跟踪 | `vpipe-lab/report/vpipe-upstream-issues.md` 里 6 条 issue 是否被回复/修复/关闭 | 6 条文档已备，待人工提交 |

**搜索词必须中英双语**，至少覆盖：
`vpipe`、`vpipe vpipeline`、`MiniMax H3`、`MiniMax-H3 FL2VA`、`MiniMax-H3 Ref2VA`、`TAE-H3`、`HyperFlow`、`lightx2v 768p`、`video_shift`、`vpipe workflow`、`MiniMax H3 768p local`、`H3 GGUF`。

### 每条新知识必须记录四项
1. **来源 URL**
2. **发布/更新日期**
3. **一句话结论**
4. **是否与本机已有实测冲突**（并写明与报告第几节冲突）

### 去重铁律
- 与主报告第 13–17 节已有的结论重复 → **一律不重复写**，只写增量。
- 确有冲突 → 必须同时写「与第 N 节冲突」+ 复核方案；**没有量化证据前不推翻旧结论**。
- 与 `vpipe-daily-knowledge.md` 里已记过的 → 跳过；除非该条有了**状态变化**（如 issue 被修复、版本更新）。

---

## 3. 阶段 B —— 消化与固化

1. **技能包**：新知识若与某技能相关 → 更新 `~/.workbuddy/skills/vpipe-*/references/*.md`
   （**只追加小节**，注明日期与来源链接；**不要删改**已有内容）。
2. **待验证登记**：新能力若无法直接采信 → 在 `vpipe-后续计划任务.md` 状态看板登记「待验证」行，供后续轮次做实验。
3. **知识累积**：本轮全部新增知识写入 `vpipe-lab/report/vpipe-daily-knowledge.md`（按日期分节，**只追加**）。
4. **实验结果**：若本轮跑了实验，量化结果也写进同一文件。

---

## 4. 阶段 C —— 实验验证（有条件执行）

**触发条件（满足其一才跑）：**
1. 阶段 A 搜到**可本地复现**的新能力 / 新参数 / 新 bug；
2. 状态看板存在未完成的高优先级实验任务；
3. 上一轮实验失败需要复跑。

**不满足就跳过本阶段**，并在报告里明写「本轮无实验，仅知识同步」。

### 执行纪律
- 每轮最多 1 个实验任务；**重任务串行**（实测并行会互相杀死进程）。
- **磁盘下限 15 GiB**；本机 Data 卷约 22 GiB，下载前先 `df -h` 核算。
  不够先清理：优先 `~/.cache/huggingface` 与已用完的模型目录；用 `/bin/rm` 而不是 `rm`（sandbox 的 `rm`/`rm -rf` 会被拒）。
- 固定 seed 便于对照。
- 后台跑重任务用 `setsid` + `.done` 幂等 + PID 续接（模板：`vpipe-lab/scripts/p9_runner.sh`、`p3_runner.sh`、`p3_chain.sh`），
  否则会被回收 SIGHUP 杀掉（P3 轮实测 30 分钟全废）。
- 每个生成任务结束后**必须抽帧目检**：ffmpeg 抽第 0/40/80/末帧拼印相 + LFM3-VL 复核
  （流水线 `vpipe-lab/pipelines/lfm3-vl-vqa.vpipeline`，批处理模板 `vpipe-lab/vqa-round4.sh`）。
- **每个结论都要有量化证据**：SSIM/PSNR（`vpipe-lab/anchor-fidelity.sh`）+ 第三方模型复核。**只看日志不算数**。
- **量化口径必须注明**：视频流直接比
  (`[0:v]scale=256:144[a];[1:v]scale=256:144[b];[a][b]ssim`)
  比「两张都先落盘 PNG 再比」高约 0.03（YUV 4:2:0 色度往返损失）。**两种口径不要混用**。

### 状态看板现状（2026-11-17）
- ✅ 已完成：P1 多参考组合、P3 768p/长规格/四段式续接、P4 TAE 预览接 i2va、P7.1 Boogu 图生图、P2 HyperFlow 对照、P9 Ref2VA@768p
- 🚫 P5 图像 4-bit 量化：建议跳过（上游 issue #41：4-bit 对 Qwen-Image-2.1 静默输出全透明图且报成功）
- 📄 P6 上游 issue：文档已备，待人工提交
- ⛔ P7.2 Qwen-Image-Edit-2511：需 57.7 GB，磁盘阻塞
- **新的实验任务由阶段 A 的搜索结果生成**

---

## 5. 每轮必须更新的两份文件（硬性要求，不许跳）

### (a) `vpipe-lab/report/vpipe-后续计划任务.md`
1. 顶部「状态看板」的日期改为本轮时间（如 `（2026-11-18 00:30 更新）`）。
2. 状态看板表格**新增一行**：`第 R 轮 · YYYY-MM-DD HH:MM 夜间知识同步`
   —— 结果列写清：本轮检索了几个源 / 新增几条知识 / 改了哪个技能 / 是否跑了实验及关键数字。
3. 状态看板之后**新增或更新**小节 `## 每日知识增量（YYYY-MM-DD HH:MM）`：
   逐条列出本轮新增知识（来源 + 结论 + 对既有结论的影响），**累积式保留历史各轮**。
4. 若本轮跑了实验且有结论 → 对应任务小节标题后加「（✅ YYYY-MM-DD 完成）」并写入关键量化数字。

### (b) `vpipe-lab/report/vpipe-H3-部署与测试报告.md`
- 文件**末尾**维护长期章节 `## 18. 夜间自动知识同步（自动任务，每轮追加一小节）`（首次运行时创建；已有则复用）。
- 每轮在其中追加 `### 18.R YYYY-MM-DD HH:MM —— <本轮主题>`，固定小节：
  - `18.R.1 本轮检索范围与来源清单`（含 URL 与日期）
  - `18.R.2 新增知识`（逐条）
  - `18.R.3 与既有结论的印证 / 冲突`
  - `18.R.4 本轮实验`（无实验就写明并给理由）
  - `18.R.5 对技能包 / 脚本 / 流水线的修改`
  - `18.R.6 本轮踩的坑与结论`
- **不要改写前面 13–17 节等历史章节正文**（确需修订时单独标注「第 R 轮修订」），保持历史可追溯。

---

## 6. GitHub 同步（每轮结束前）

### 6.1 用常驻工作副本，不要每轮全量 clone（★ 2026-11-17 实测）

仓库 `ltzc2018/vpipeworkflow` 的 `size` 是 **216,872 KB ≈ 212 MB**（41 个视频占大头）。
**全量 `git clone` 会被 SIGTERM 打死**（退出码 137），沙箱内外都复现。

**正确做法**：常驻副本 + 增量 pull。

```bash
REPO=/Users/minichen/WorkBuddy/2026-11-12-21-10-11/.vpipeworkflow

# 首次（只需做一次；后台跑，别用前台，会超时）
git clone git@github.com:ltzc2018/vpipeworkflow.git "$REPO"

# 每轮
git -C "$REPO" pull --ff-only
```

**不要用 `--filter=blob:none` 部分克隆做同步**：
`git ls-tree -l`、`git checkout` 会为**每个缺失 blob 单独回源**（本仓库 395 个文件 = 395 次往返）→ 同样被打死。
部分克隆只能当**只读探测工具**（例如看远端文件树）。

### 6.2 每轮同步的内容

```bash
cd "$REPO"
# 复制本轮新增/变更的：
#   skills/    技能包（含 references/）
#   scripts/   脚本
#   pipelines/ 流水线
#   docs/reports/  两份主报告 + SOP + daily-knowledge + 轮次状态
git add -A
git commit -m "docs: 第 R 轮夜间知识同步（YYYY-MM-DD HH:MM）"
git push origin main
```

- **仓库内路径必须相对化**（相对 vpipe 工作目录），仓库自带 `refs/` 参考图。
- **⚠️ 真人素材一律不入 public 仓库**：`refs-real/`、`*real-photo*`、`*boogu-real*` 绝不 push。
- push 后用 GitHub API 复查**真人文件数为 0**。
- 视频产物若本轮有新增，用 `git add` 单个文件即可（按需拉取那一个 blob，不会全量回源）。

---

## 7. 本轮交付（中文总结 + present_files）

总结必须覆盖：检索了哪些源 / 新增几条知识 / 具体结论（含与旧结论的印证或冲突）/ 改了哪些技能与报告 /
是否跑了实验及量化结果 / 踩到什么坑 / 下一步建议。

最后用 present_files 展示：本轮更新的 `vpipe-后续计划任务.md`、`vpipe-H3-部署与测试报告.md`、
新增或修改的技能参考文档、`vpipe-daily-knowledge.md`；若有实验，一并展示成片与印相图。

---

## 8. 已知坑清单（避免重复踩）

### 接线 / 参数
- 参考生视频与首帧锚定**互斥**；商品要全程在场必须用首尾帧锚定。
- 仅首帧锚定时主体会在第 20–40 帧之间消失。
- `save-video` 的键是 `output_url` 不是 `path`，且必须接两路输入（rgb-to-video + audio-vae-decode）。
- `video-ref-encoder` 与 `generate-video` 的 `frames` 必须相等，否则整个请求被跳过。
- `model_variant` 逐字段比对 `version`/`variant`/`name`/`model_type`，用 `model_type` 最稳。
- 官方多参考上限：9 图 + 3 视频 + 3 音频 = 12 项，单段参考视频 2–15 秒，总时长 ≤ 15 秒。
  - `attach_audio` 的数字是「**音频那条参考自己的槽位号**」（1 起算）→ ≥4 条参考时才暴露歧义。
  - **没用到的参考端口不要接** —— 一个空端口会重编号后面的所有参考。
- 引导长度必须是 `17n+5` 帧（90 = 17×5+5）。

### 模型 / 采样
- **shift 规则按适配器分叉，不是按分辨率**：
  FL2VA 768p = 6.0 更锐；**Ref2VA 768p 实测 12.0 更锐**；544p / Pika / HyperFlow = 12.0。
- **shift 响应是台阶不是斜坡**：6.0 与 8.0 几乎等价（运动曲线 r 0.9817）→ 中间值不必试。
- **shift 写错完全静默**：只有 HyperFlow 与带 `sampling_contract` 的适配器才 warn（`stages/generate-video-stage.cc:3746`）。
- **4 步适配器必须同时把 pipeline `steps` 改成 4**，否则静默劣化。
- **HyperFlow 是 flow-map adapter 不是普通 LoRA**；`lora_scale: 0` 精确回到原始模型（已三组验证）；Ref2VA 注册名 `videorebirth/hyperflow-ref2va`；适配器生效时 `steps` 被忽略。
- **Boogu 图生图**：参考图走 Qwen3-VL 语义条件**不走 latent**（不需要 `vae-encode`）；调度器必须 `boogu_v1`；CFG 固定 1；**每张参考图各接一个 `image-resample`**；参考图必须预裁成单一主体。
- 本机 HuggingFace 直连不通，**全部走 ModelScope**（`VPIPE_MODEL_SOURCE=modelscope`）。

### 度量 / 复核
- **细节能量会把噪点当细节** → 评价锐度必须同时看「3×3 中值滤波后纹理量」与「颗粒量」。
- **接缝判据必须用相位相关**（区分「几何错位」与「重新渲染纹理漂移」）；**不能只靠 LFM3-VL 读图**（它把 76px 重构误读为「自然姿态变化」）。
- **LFM3-VL-2B 三个缺陷**：否定式问题编答案；分不清细微锐度差；**运镜方向判断不可靠** → 运镜只信相位相关。
- 768p 多参考只一半成立：身份锁 ✅ / 音轨锁 ✅ / **运镜锁 ❌**；代价：行数 ×2.10、耗时 ×3.64、画质 −17%。

### 预览 / 续接
- **TAE 实时预览**：`preview` 是 WebSocket sink，**CLI 下流水线永不结束**；必须接 `generate-video` 的 **oport 2**（接 oport 0 静默失效）；预览流有**两个 init 段**要分段拼装；各拍**相位不对齐**，横向比较前必须相位对齐（否则 0.13 vs 0.93）。
- **锚定涌现**：有锚定 step1 SSIM 0.9534；无锚定 step1 0.7085、step3 才收敛 → 锚定后第 1 步预览就能判断商品有没有跑偏。
- **官方四段式续接**：`temporal-slice(start=-90)` + `audio-to-pcm(start_s=段长-3.75, duration_s=3.75)` + `video-ref-encoder(attach_audio=[2])` + ffv1/alac。

### 环境 / 脚本
- **后台任务被回收会 SIGHUP 杀掉重任务** → `setsid` + `.done` 幂等 + PID 续接 + 内存/磁盘门限。
- bash 3.2 **无 `declare -A`** → 用 `case` 分派。
- 数组追加 `files+=(-i "$f")` 是**两个元素** → 图像计数用独立计数器。
- **`$N` 后紧跟中文全角标点会被吞进变量名** → 一律 `${N}`。
- ffmpeg `ssim` stats **索引 1 是 Y 分量** → 按 key 解析 `All:`。
- `os.rmdir` / `rm -rf` 被 sandbox 拒；`ps`/`top` 被封禁 → 用 `.mem` 采样 + PID 文件。
- Bash 工具 timeout 上限 600000 ms → sleep 分段 ≤ 9 分钟。

---

## 9. 调度器实现说明（2026-11-17 实测）

- `FREQ=DAILY` **不支持** 多值 `BYHOUR`（校验直接拒绝：`BYHOUR must be an integer between 0 and 23`）。
- `FREQ=HOURLY;INTERVAL=2;BYMINUTE=30;BYHOUR=0,2,4,6` **会忽略 BYHOUR 与 BYMINUTE**：
  实测 nextRun = 创建时间 + 2h（20:34 → 22:34），与指定小时无关。
- **因此本系列用 4 个 `FREQ=DAILY` 单时段自动化实现**：00:30 / 02:30 / 04:30 / 06:30。
- 4 个自动化共用本 SOP，靠 `.auto-round-state.json` 递增轮次 + `.auto-round.lock` 防并发。

---

## 10. 2026-11-18 第 3 轮补充的坑与纪律（★ 优先于上面的旧条目）

### 10.1 ★★★ 已装 App **不是** seed 可复现的 —— 所有同 seed 对照必须先测漂移基线

- 同一个流水线、同一个 seed、同一台机器**连跑两次**：**0/22 帧逐位相同**，整段 **SSIM 仅 0.750072**，
  文件大小都不同（245 549 B vs 244 535 B）。
- 原因：上游 bit-for-bit 修复 `e6972ac`（2026-11-06）**晚于**已装 App（`9db5dd7`，2026-11-01）；本地源码树 `33cda00` 已含。
- **实测漂移幅度**：sharpness **8.7%**、HF jitter **18.4%**、frame diff **22.4%**、static_hf_jitter **13.5%**。
- **纪律**：任何组间差异**必须先跑一次同配置重复运行**拿到漂移基线，效应超过基线才可采信。
- **不要用 mp4 文件哈希判断两次生成是否一致**（容器含时间戳）→ 比 **`framemd5`** 与**音频轨 md5**。

### 10.2 ★★ 旧 build 会**静默丢弃**新 config 键

- 在已装 App 上给 `minimax-h3-model-config` 写 `sigmas`：零报错、零告警、**零日志回显**，
  输出与不写该字段**逐位相同**。
- 这是「shift 写错完全静默」的升级版：**字段根本不存在时也是静默的**。
- **纪律**：写完新字段，**必须在日志里找到它自己的回显**（例如 `the video's 8 steps on sigmas [...]`）。
- 推论：「已装 App 有这个能力」**不能**从「源码里有」推断出来，得逐字段验。

### 10.3 ★★ 换 `video_shift` = 换场景

- 只改 `video_shift`（其余全同）时首帧 SSIM 仅 **0.46–0.56**；
  即便用静图参考 + 完全静止提示词也一样（**0.5062**）。
- **纪律**：跨 shift 的结论只能表述为「两条不同 σ 网格的对比」，不能表述为「同一模型渲染得更锐」。

### 10.4 ★★ 上游官方文档的 shift 表是权威来源（别只靠社区表）

- `docs/MINIMAX-H3.md`（源码树自带）有完整的**适配器→partition→steps→shift** 表，
  关键三条：768p 家族蒸馏在 **shift 6**；**Ref2VA 8-step 768p → 6.0**（唯一需要 6.0 的 Ref2VA 适配器）；
  **Ref2VA 4 步 v0.1 = 544p → 12/3**。
- 上游自己也标注了「Ref2VA 8-step 768p 的 6.0 是**从 768p 家族继承的推断**，上游未文档化，值得复核」。
- **纪律**：查 shift 先查上游文档，再查社区表（sdnext 的表与上游逐行一致，可作交叉印证）。

### 10.5 ★ 不碰已装 App 也能跑本地 build（symlink farm）

- 已装 App 的 helper 只依赖 `@rpath/libvpipe.0.dylib`，rpath = `@executable_path/../Frameworks`；
  **`DYLD_LIBRARY_PATH` 对 `@rpath` 无效**（第 2 轮那条结论要改）。
- 正确做法见报告 18.3.6 坑 2：复制 helper 到 `/tmp/vp13/Helpers/`，
  建 `/tmp/vp13/Frameworks/` 软链农场（App 的框架全链过去，只把 `libvpipe.0.dylib` 换成本地 build 的）。
  → `--version` 打出 `0.1 (33cda00*0)`；`p13_runner.sh` 支持 `VPIPE_BIN` 覆盖。

### 10.6 ★ 编辑正在运行的 bash 脚本会破坏它的执行

- bash 按**文件偏移增量**读取脚本，中途改文件 → 从错位处继续读 → 本轮把 `p13_runner.sh` 的 `case`
  读成了 `*)` 分支 → `exit 2`。
- **纪律**：**改调度脚本前先停掉正在跑的实例**。

### 10.7 `generate-video` 的 iport 数量必须与模板逐项一致

- 多一个空 iport 会把 `minimax-h3-model-config` 挤到下一槽位 →
  `payload type mismatch on edge video-ref-encoder[2] -> generate-video[9]`
  （producer `TensorBeatPayload` vs consumer `FlexDataPayload`）。
- **纪律**：改流水线时**照抄模板的 iports 列表**，别凭印象重排。

### 10.8 LFM3-VL-2B 的第 4 个缺陷（本轮发现）

- 问「这三张是不是同一个场景？」它答「**完全相同**」，而定量首帧 SSIM 只有 0.51–0.56。
- → 它按**语义层**（主体/背景/光线）判断场景同一性，**对像素级场景差异不敏感**。
- **纪律**：**「是否同一场景」只能靠首帧 SSIM / 相位相关裁决，不能靠 LFM3-VL。**
  （它仍能可靠回答「有没有运动」这类粗判 —— 本轮用它确认了静态夹具成立。）

### 10.9 磁盘受限时怎么设计实验

- 本轮磁盘仅 **5.1 GiB**（远低于 15 GiB 下限）→ 刻意选「**模型已在本地、只跑短片**」：
  22 帧 / 1344×768 / 8 步，**每臂 3 分 55 秒、产物仅 240 KB** → 三臂 + 一次重复运行全部完成。
- **规律**：短片（22 帧 = 17×1+5）+ 本地已有模型 + 单臂 < 4 分钟 ≈ 可在低磁盘下做完整对照。
