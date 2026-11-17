# MiniMax-H3 纹理沸腾（temporal texture boiling）量化与复现

> 建立日期：2026-11-18（第 3 轮夜间自动知识同步）
> 依据：上游 issue `tgo-app-dev/vpipe#55`（shduanqin-byte，2026-10-21）
> 脚本：`vpipe-lab/scripts/p13_hf_jitter.py`、`make_p13_pipelines.py`、`p13_runner.sh`、`p13_contact.sh`、`vqa-p13.sh`

---

## 1. 现象

MiniMax-H3 生成的视频里，**静止表面上的高频纹理会逐帧重绘**（"沸腾"）。
上游 issue #55 把它定位为采样器问题：ComfyUI 的 `er_sde` 每步结尾有一次**受控重注噪**
（Langevin 修正），误差被重新随机化；而 vpipe 的 `FlowMatchEuler` 是确定性的，误差单调累积，
读起来就是纹理漂移。

**本实验室第 3 轮在 M5 Pro / 24 GB 上独立复现了该现象**，方法学与上游一致。

---

## 2. 度量公式（严格照抄 issue #55，不要自创改写）

在 **384 宽的灰度解码**上：

```
HF(t)      = gray(t) − GaussianBlur(gray(t), σ=2.0)
HF jitter  = mean_t |HF(t+1) − HF(t)| / mean_t |HF(t)|      ← 沸腾指标
frame diff = mean_t |gray(t+1) − gray(t)| / 255
sharpness  = mean_t Var(Laplacian(gray(t)))
```

- 高斯核：σ=2.0，半径 `ceil(3σ)=6`，可分离卷积，边缘 `reflect` 填充。
- Laplacian：4 邻域离散核 `[[0,1,0],[1,-4,1],[0,1,0]]`。
- `sharpness` 是**逐帧方差再对帧求均值**（不是整段方差）。
- 上游原值：静态参考片 **HF jitter 0.0000 / frame diff 0.00000 / sharpness 272.4**；
  8 步输出 **0.0502 / 0.00232 / 948.1**；16 步 **0.0437 / 0.00214 / 1210.1**；
  4 步 LoRA **0.0914**（作者称 unusable）。

### 2.1 本实验室加的一个补充指标（不替代上面三个）

```
static_hf_jitter —— 只在「时序静止像素」上统计的 HF jitter
```

做法：先用 σ=2.0 模糊帧的逐像素帧间差 `|blur(t+1) − blur(t)|` 判定静止性（阈值 2.0/255），
再只在静止像素上算 HF jitter。

**为什么要加**：#55 之所以要造「静墙夹具」，就是为了把运动这一项消掉。
真实视频里场景在动，`HF jitter` 混着运动；用这个补充指标可以直接问
「**静止表面上**有多少高频抖动」。

---

## 3. 复现方法（关键：必须造静态夹具）

上游 #55 的夹具逻辑：

> 「The reference is a 22-frame clip made from **one still image**, so it is mathematically static.
> Measured on the reference itself: HF jitter 0.0000 … Every bit of jitter in the output is
> therefore model-generated.」

本实验室的等价做法（更省事，且效果相同）：

1. **参考地板**：把一张静图编码成 22 帧的静止片，编码参数与出片完全一致
   （`h264 High / yuv420p(tv, smpte170m) / 24 fps`）→ 测得的 HF jitter 就是
   **编码器 + 度量口径的地板值**。
2. **静态提示词**：明确写「完全静止 / 锁定机位 / 无运动 / 无眨眼 / 无呼吸」。
3. **同帧数**：出片帧数取 **22 = 17×1+5**，与上游夹具一致 → 数值可与上游直接对表。
4. **对照臂**：同一参考图 + 同一提示词 + 同一 seed，**只改一个变量**。

### 3.1 为什么「静态参考图」比「静态参考视频」更省事

上游夹具把「一张静图做成 22 帧片」当**视频参考**喂进去。本实验室改成把它当**图片参考**：

- 官方限制「单段参考视频 2–15 秒」→ 22 帧 = 0.92 秒 **低于下限**，视频参考路线有被拒风险；
- 图片参考没有这个下限；
- 且「静态参考图 + 完全静止提示词」已能把场景压到 **94–95% 像素静止**（见第 4 节 `static_px`），
  运动残留对沸腾读数的影响可忽略。

---

## 4. 本实验室第 3 轮实测结果（M5 Pro / 24 GB / Ref2VA 768p / 8 步 / seed 42 / 22 帧 / 1344×768）

| 变体 | HF jitter | frame diff | sharpness | static_hf_jitter | 静止像素占比 |
|---|---:|---:|---:|---:|---:|
| **静态参考（编码地板）** | **0.0010** | 0.000010 | 353.66 | 0.0010 | 1.000 |
| shift 6.0（上游文档指定值） | **0.1293** | 0.004595 | 610.45 | 0.1156 | 0.955 |
| shift 12.0 | **0.1182** | 0.004662 | 683.39 | 0.1045 | 0.941 |
| ComfyUI `er_sde` σ 网格（`sigmas`） | 见报告 18.3 | | | | |

- **沸腾量级 = 地板的 118–129 倍**，且 94–95% 的像素是静止的 → 沸腾是真的，不是运动假象。
- 两臂的 `frame_diff` 只差 1.5%（0.004595 vs 0.004662）→ 运动量可比。
- 上游 8 步墙片是 **0.0502**，本实验室静态场景 8 步是 **0.1293**。绝对值不可直接比
  （分辨率 1344×768 vs 1024×576、检查点是 stock `Ref2VA-8bit` vs Singularity v1.3、
  画面内容也不同），但**「远高于地板」这个结论独立复现**。

### 4.1 与上游 #55 的方向性对照

| 变量 | 上游 #55 实测 | 本实验室实测 | 方向 |
|---|---|---|---|
| 步数 8 → 16 | 0.0502 → 0.0437（变好） | — | — |
| 步数 8 → 4（4 步 LoRA） | 0.0502 → **0.0914**（变差） | 4 步片 HF jitter **0.3493** vs 8 步 **0.3272**（FL2VA 768p，方向一致） | ✅ 一致 |
| `video_shift` 12 → 6 | 0.0512 → 0.0436（**降 shift 更好**） | shift 6.0 = 0.1293 / shift 12.0 = 0.1182（**升 shift 更好**） | ❌ **方向相反** |
| 参考图数量 | 3 张 → 1 张：0.4749 → 0.3620（少参考更稳） | 多参考 C 静态抖动 0.1740 > 单参考 A 0.1307（**多参考更不稳**） | ✅ 一致 |

**shift 那一行方向相反，但两边都有「换场景」混淆项**（见下节），不能直接互证。

---

## 5. ★ 两个必须记住的方法学陷阱

### 5.1 换 shift = 换场景（无法用同一场景对照 shift）

只改 `video_shift`（其余全同：参考图、提示词、seed、步数、画布）时：

| 对照 | 首帧 SSIM |
|---|---|
| Ref2VA 768p shift 6.0 vs 12.0 | **0.5213** |
| FL2VA 768p shift 6.0 vs 12.0 | **0.4618** |
| 静态参考图 + 静止提示词，shift 6.0 vs 12.0 | **0.5062** |

社区实测同样如此（AICU，2026-08-18）：「The same seed does not give you the same shot …
the same seed and the same prompt produce a **different scene**」。

⇒ **vpipe 里没有「同一场景的 shift 对照」这回事**：σ 网格决定整条去噪轨迹。
跨 shift 的结论只能表述为「两条不同 σ 网格的对比」。
真要控制场景，只能用**首帧锚定（FL2VA）**把第 0 帧钉死。

### 5.2 ★★ 已装 App **不是** seed 可复现的（跨运行会漂）

同一个流水线、同一个 seed、同一台机器，**连跑两次的结果完全不同**：

- 22 帧里 **0/22 帧逐位相同**；
- 整段 SSIM 只有 **0.750072**；
- 输出文件大小都不同（245 549 B vs 244 535 B）。

**原因**：上游 commit `e6972ac`（2026-11-06）"A generation that repeats bit for bit" **在已装 App
（`9db5dd7`，2026-11-01）之后**，App 里没有这个修复。本地源码树 `33cda00`（2026-11-13）已包含。

⇒ **纪律**：本实验室（乃至任何用 9db5dd7 App 的）所有「同 seed 对照」都带运行间漂移，
**组间差异必须大于这个漂移基线才能算数**。测漂移基线的做法：同一流水线跑两次比逐帧哈希。

---

## 6. ★ 用 `sigmas` 直接喂 ComfyUI 的 σ 网格（上游 issue #55 的请求已被满足）

### 6.1 上游已有这个字段

`minimax-h3-model-config` 阶段有 `sigmas` 键（源码 `stages/minimax-h3-model-config-stage.cc:69`）：

- 「the VIDEO's sigmas **AS RUN**, in place of the grid `steps` and the shifts make — comma-separated,
  terminal 0 included, strictly falling from at most 1」
- **上游文档给的示例串正是 ComfyUI `er_sde` 的 σ 表**：
  `"1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"`
  （与 issue #55 正文里贴的 ComfyUI 那一行**逐位相同**）
- 「One forward per sigma but the last, so the list sets the step count and `generate-video`'s
  `steps` is not used.」（9 个 σ → 8 次前向；`steps` 与之不符时阶段会告警）
- 「Wins over an adapter's own grid (a flow map, a sampling contract)」→ 对普通 LoRA 适配器直接生效。
- 音频的 σ 由 `video_shift` / `audio_shift` 映射得出（`video_shift` 仍决定音频落点）。
- ⚠️「A distillation was fitted to the grid it was trained on, so a few-step adapter on another grid
  is **off its training**.」→ 换网格后画质变化不能全部归因于网格。

### 6.2 ⚠️ 已装 App 会**静默忽略**这个字段

| build | 是否支持 `sigmas` | 证据 |
|---|---|---|
| 已装 App `9db5dd7*0` | ❌ **静默忽略** | 日志里 `MiniMaxH3ModelConfigStage(...)` 行**没有** `, the video's N steps on sigmas [...]`；输出与不写该字段**逐位相同**（视频帧 framemd5 一致、音频 md5 一致） |
| 本地 build `33cda00*0` | ✅ 生效 | 日志出现 `shifts 6.0/3.0, the video's 8 steps on sigmas [1, 0.9844, ...]` |

⇒ **新的坑（比「shift 写错完全静默」更隐蔽）：在旧 build 上写新字段名，字段被静默丢弃 ——
零报错、零告警、零日志、输出逐位相同。**
写完新字段务必去日志里找它自己的回显。

### 6.3 ★ 不用碰已装 App 也能跑本地 build（symlink farm 法）

已装 App 的 helper 只依赖 `@rpath/libvpipe.0.dylib`，rpath 是 `@executable_path/../Frameworks`。
`DYLD_LIBRARY_PATH` **对 `@rpath` 无效**，所以第 2 轮「用 `DYLD_LIBRARY_PATH` 换库」的做法是错的。

正确做法（**不改动已装 App**）：

```bash
APP="/Applications/Vpipe Manager.app/Contents"
BLD=<本地源码树>/build
rm -rf /tmp/vp13 && mkdir -p /tmp/vp13/Helpers /tmp/vp13/Frameworks
cp "$APP/Helpers/vpipe" /tmp/vp13/Helpers/vpipe
for f in "$APP/Frameworks/"*; do ln -sf "$f" "/tmp/vp13/Frameworks/$(basename "$f")"; done
ln -sf "$BLD/libvpipe.0.dylib" /tmp/vp13/Frameworks/libvpipe.0.dylib   # ← 换成本地框架
chmod +x /tmp/vp13/Helpers/vpipe
DYLD_LIBRARY_PATH="$APP/Frameworks" /tmp/vp13/Helpers/vpipe --version
# → 0.1 (33cda00*0)   ← 本地 build 生效
```

之后所有生成都用 `VPIPE_BIN=/tmp/vp13/Helpers/vpipe` 跑（`p13_runner.sh` 已支持该环境变量）。
**注意**：本机 `ffprobe` 不在 PATH，尺寸探测用 `ffmpeg -i` 的 `Stream #0:0 ... WxH`。

---

## 7. 本节新增的坑（2026-11-18 第 3 轮）

1. **在旧 build 上写未知 config 键 → 静默丢弃**（零报错、零日志、输出逐位相同）。见 6.2。
2. **`DYLD_LIBRARY_PATH` 管不了 `@rpath`** → 第 2 轮那条「用 DYLD_LIBRARY_PATH 换 libvpipe」的结论要改：
   真正能换的是 symlink farm（6.3）。
3. **已装 App 不是 seed 可复现的**（跨运行 SSIM 0.75）→ 所有同 seed 对照都要先测漂移基线。见 5.2。
4. **不能用 mp4 文件哈希判断两次生成是否一致**（容器含时间戳，字节必不同）→
   要比 **`framemd5`**（逐帧）或**音频轨 md5**。
5. **编辑正在运行的 bash 脚本会破坏它的执行**：bash 按文件偏移增量读取脚本，
   中途改文件 → 脚本从错位处继续读 → 本轮把 `p13_runner.sh` 的 `case` 读成了 `*)` 分支 → `exit 2`。
   → **改调度脚本前先停掉正在跑的实例**。
6. **`generate-video` 的 iport 数量必须与模板逐项一致**：多一个空 iport 会把
   `minimax-h3-model-config` 挤到下一个槽位，报
   `payload type mismatch on edge video-ref-encoder[2] -> generate-video[9]`。
   → 改流水线时**照抄模板的 iports 列表，不要凭印象重排**。
7. **`setsid` 在 macOS 上不存在** → 本机的脱离进程组由 `scripts/detach_run.py`
   （`os.setsid()`）完成，调度脚本本身用 Bash 工具的 `run_in_background` 托管即可。

---

## 8. ★★★ 可复现性（2026-11-18 03:07 P15 实测，修订第 3 轮的归因）

### 8.1 开关不是「版本」，是 `autotune: false`

上游 `e6972ac` 原文：`autotune` false asks for a repeatable generation. A kernel tuner chooses
between candidates that agree to rounding but not to the bit, and it chooses by racing them…
**pin it (`ane_rows`) too and a generation repeats exactly.**

`docs/PLUGINS.md`：two runs whose races land differently produce different pictures from the same seed.

**本机实测（4 臂，各 22 帧 / 1344×768 / 8 步 / seed 42 / shift 6.0）**：

| 对照 | 逐帧 md5 | 音频 md5 | SSIM(整段) | PSNR | 字节 |
|---|---|---|---|---|---|
| App(9db5dd7) vs 本地 build(33cda00) | ★ 同 | ★ 同 | **1.000000** | inf | 244535 = 244535 |
| 竞速开，第 1 次 vs 第 2 次 | 不同 | 不同 | **0.750072** | 19.14 | 244535 / 245549 |
| ★ **竞速关，第 1 次 vs 第 2 次** | ★ **同** | ★ **同** | ★ **1.000000** | ★ **inf** | 244535 = 244535 |

**结论**：
1. **`autotune: false` → bit-for-bit 可复现**；
2. **不可复现与 vpipe 版本新旧无关**（第 3 轮「App 旧所以不可复现」的归因**错误**）；
3. **关竞速更快**：220 s vs 225 s（**−2.2%**）——
   日志 `gemm autotune 4635`（首帧前向 4710 ms 的 98.4%）就是那笔钱。

### 8.2 怎么关（三个 stage 都要）

```json
"generate-video":      { "config": { "autotune": false, ... } },
"vae-decode":          { "config": { "autotune": false } },
"video-ref-encoder":   { "config": { "autotune": false } }
```

- `video-ref-encoder` 一处同时管住**文本编码器(LM)**与**视频条件器**，漏了它文本侧仍可能竞速；
- `ane_rows` 在 **M5** 上是惰性的（`ane_ffn` 默认 false）；**M4 Pro 上必须钉**。

### 8.3 漂移基线（竞速开时的噪声幅度，可跨 build 复用）

| 指标 | 本地 build(33cda00) | 已装 App(9db5dd7) |
|---|---:|---:|
| sharpness | **+9.1%** | 8.7% |
| HF jitter | **+20.3%** | 18.4% |
| frame diff | **+25.2%** | 22.4% |
| static_hf_jitter | **+14.5%** | 13.5% |

→ **漂移是本机硬件/模型的属性，与二进制版本无关。**

### 8.4 竞速漂移 = 纯细节噪声（与「换 shift = 换场景」是两种机制）

只差竞速的两次运行：**同一场景、同一语义**（人工目检：同一姿态、同一窗框、同一光斑），
只有像素细节不同。→ **做 shift 对照前先关竞速**，否则两个混淆项混在一起。

### 8.5 逐位判据的完整组合

`framemd5`（**必须 `-map 0:v`**，全流会混进音频包）+ 音频轨解码后 md5 + SSIM 双口径 + PSNR。
**绝不能用 mp4 文件哈希**（容器含时间戳）。

### 8.6 纹理沸腾的本机候选解法：`dmd` sampler（零下载）

上游 #55 说 ComfyUI 的 `er_sde` 每步重注噪 → 误差重新随机化 → 沸腾被压制。
**H3 内置的 `dmd` 就是这个机制**（见 `sampler-spec.md`）：
`x0 = x + σ·v` → `x_next = (1−σ')·x0 + σ'·n`，噪声取自 clip 自己的 seed。
接法：`diffusion-sampler-select{method: dmd}` → `generate-video` 的 **iport 3**。

> ⚠️ `dpmpp_sde` 对 H3 **不被支持**（上游明确排除）→ 这是 #55 的第 1 条请求至今未满足的部分。

### 8.7 σ 网格

见同目录 `sigma-grid.md`（闭式公式，已与上游文档 + ModelTC 官方表逐位互验 33 个数值）。

---

## 9. ★★ 第 4 轮（P18）判决：`dmd` 采样器把纹理沸腾压低约 13%，并更锐

**这是本实验室对上游 issue #55 的第一次「有解」实测。**

| 项 | 值 |
|---|---|
| 实验 | P18 · `vpipe-lab/scripts/{make_p18_pipelines.py,p18_runner.sh,p18_analysis.py}` |
| 夹具 | 静态（静止提示词 + 静图参考）/ 22 帧 / 1344×768 / 8 步 / seed 42 / Ref2VA 8-step 768p / shift 6.0-3.0 |
| 关键前提 | **三处 `autotune: false`** → 漂移 = 0 → **差异 100% 归因于采样器** |
| 臂 | A `euler`（接 sampler 端口）/ B `dmd` / B2 `dmd` 重复 / 参照 `p15-repro-af1`（不接端口） |

### 9.1 主结果

| 指标 | euler | **dmd** | 效应 |
|---|---:|---:|---:|
| **HF jitter**（#55 主指标） | 0.1075 | **0.0937** | **−12.82%** |
| **frame diff** | 0.003669 | 0.003324 | **−9.40%** |
| **sharpness** | 559.73 | **617.19** | **+10.27%** |
| **static_hf_jitter** | 0.1010 | 0.0892 | **−11.68%** |
| 用时 | 219 s | **219 s** | **0%** |

**结论**：`dmd`（每步取 x0 再重注噪到下一个 σ）**降低沸腾 12.8%、同时锐度 +10.3%、不花额外时间**。

### 9.2 ⚠️ 但不是根治（别夸大）

- 第 3 轮的**静态夹具地板 = 0.0010**；本轮 `dmd` 的 0.0937 → **仍是地板的 94×**。
- ⇒ 正确表述：**「把沸腾压低约 13%」**，不是「解决」。
- 上一轮 P13 测的 `er_sde` σ 网格是 **−16%**，但**落在 18.4% 的漂移带里 → 当时不可下结论**。
  **现在漂移 = 0，若重跑 `er_sde`（P13b）那个 −16% 就能直接采信** → **P13b 优先级要提到 P18 之上**。

### 9.3 ★ 社区互证（同一机制，不同生态）

HF `Comfy-Org/MiniMax-H3-Image` 讨论区：
> ComfyUI 的 **`lcm`** 采样器「每步取端点预测**再重注噪到下一个 σ**」，
> **euler** 则「把陈旧的高频噪声每步带着走」「步数越多越累积」，
> 并断言「**病理在采样器侧，不在权重侧**」。

**`lcm`（ComfyUI）≡ `dmd`（vpipe）= 同一个重注噪机制** ⇒ **本轮独立验证该社区结论成立。**

### 9.4 三条配套的确定性判决

1. **A（接端口 + euler）vs 参照（不接端口）**：★ 逐位完全相同（framemd5 同 / 音频 md5 同 /
   SSIM 1.000000 / PSNR inf / 字节 244 535 = 244 535）
   → **sampler 端口在 method=euler 时完全透明**；且这是**跨轮次**的 bit-for-bit 复现。
2. **B vs B2（`dmd` 跑两次）**：★ 逐位完全相同 → **`dmd` 的重注噪路径也是确定性的**
   （噪声取自 clip 自己的 seed → 重注噪不引入随机性）。
3. **A vs B**：首帧 SSIM **0.440051** → **「换采样器 = 换场景」**（与「换 shift = 换场景」同族，
   且 0.44 比 shift 的 0.46–0.56 还低）。

### 9.5 ⚠️ LFM3-VL 复核**再次**给出与量化相反的答案（已知缺陷的又一实例）

| 提问 | LFM3-VL 的回答 | 量化真值 |
|---|---|---|
| 「哪一行平坦区域噪点更细碎？」 | **第 3 行（dmd）更多** | **dmd 更少（−12.8%）** |
| 「两首帧是否同一场景？」 | 「场景基本相同，只有细微差异」 | **首帧 SSIM 0.440051 → 不是同一场景** |
| 「首末帧纹理有没有变多？」 | 读成 4 段独立视频，答案不可用 | — |

⇒ **再次印证已知缺陷 ②（分不清细微锐度/纹理差）与 ④（场景同一性只能靠 SSIM / 相位相关）**。
**纪律：纹理与锐度只信量化，LFM3-VL 只用它能可靠回答的「有没有运动」这类粗判。**
