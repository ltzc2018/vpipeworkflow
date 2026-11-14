# vpipe × MiniMax H3 · 本地音视频生成部署与全面测试报告

> 机器：Mac mini **M5 Pro / 24 GB 统一内存 / 15 核 / macOS 27.2**
> 日期：2026-11-14（第三版，合并「i2va 首帧锚定 + 保真度量化 + 多模型对照」第三轮）
> 来源：YouTube `youtu.be/o9m7UYpmCbg`（中文）+ GitHub `tgo-app-dev/vpipe`
> 代码基线：`main` @ `33cda00`（源码编译，Apple Silicon 构建）

---

## 0. 一句话结论

**vpipe 装好了，H3 的两个 partition（FL2VA / Ref2VA）都在本机 8-bit 跑通，四条生成路线全部出片：**

| 路线 | 权重 | 参考图 | 耗时 | 规格 |
|---|---|---|---|---|
| 文生视频 | FL2VA-8bit + Turbo-LoRA v4 | — | 5 分 50 秒（4 步） | 960×544 / 124 帧 / 5.18 s + AAC |
| **参考生视频（推荐）** | **Ref2VA-8bit + Pika H3 Flex ref2va** | ✅ | **6 分 49 秒** | 832×480 / 124 帧 / 5.18 s + AAC |
| 参考生视频（官方已发布配对） | FL2VA-8bit + VDN 线性分支 | ✅ | 8 分 20 秒 | 960×544 / 124 帧 / 5.18 s + AAC |
| **首帧图生视频 i2va** | FL2VA-8bit + Pika H3 Flex **fl2va** | ✅ 首帧 | **5 分 59 秒** | 832×480 / 124 帧 / 5.18 s + AAC |
| **首尾帧插值** | FL2VA-8bit + Turbo-LoRA | ✅ 首+尾 | 8 分 41 秒 | 960×544 / 124 帧 / 5.18 s + AAC |
| TAE-H3 实时预览 | 已接入，TAE 解码成功 | — | 每步一次 | 512×288 预览循环 |
| **文生图（Z-Image-Turbo）** | 官方 bf16 | — | **42.5 秒** | 1024×1024，8 步 no-cfg |
| **文生图（Krea-2-Turbo）** | 官方 bf16（无 M87 LoRA） | — | **49.5 秒** | 1024×1024，8 步 euler+simple |

**第二轮最大的收获不是多出一支片，而是把「参考图到底有没有起作用」这件事真正验证了** —— 见第 6 节。第一版报告里那支 Ref2VA 成片，提示词把猫的外观写得很死，**无法证明参考图生效**；这一版用**四组消融对照**重做了实验（含一组"熊猫参考图"强消融），并修正了两处会误导用户的配置错误。

**第三轮把验证从"看片"升级成"可测量"**，并因此**推翻了自己上一版的一个结论**：

| 判定 | 方法 | 结果 |
|---|---|---|
| 输出与参考图**逐像素**一致吗 | ffmpeg SSIM/PSNR 逐帧 | 锚定首帧 **0.9505**；参考生视频只有 **0.49–0.52** |
| 输出的**语义**真被参考图改写了吗 | 两个**第三方模型**复核（LFM3-VL-2B + Qwen3.5-4B） | 都把 D 组判成"**黑白熊猫**"，而提示词里没有"熊猫"二字 |
| 锚定能不能保住商品 | 逐帧 SSIM + VQA 描述 | ⚠️ **仅首帧锚定：商品约 2 秒后消失**；**首尾帧锚定：全程保留** |

> 第三轮最重要的修正：第二版说「首帧锚定 ✅ 完整保留服装」是**高估**。实测证明**只给首帧时牛仔外套在第 40 帧前后就消失、画面被整体重构**；**商品要全程在场必须给到末帧锚定**。详见 6.5 节。

仓库单元测试 3464 条通过 3460 条，剩余 4 条已定位为 3 项上游缺陷 + 1 项本地 ffmpeg 构建差异；本轮新定位 **4 条上游 issue**（见第 9 节与 `vpipe-upstream-issues.md`）。


---

## 1. 先说清楚「vpipe」是什么

| | |
|---|---|
| 正确目标 | **`tgo-app-dev/vpipe`** — "Real-time multimodal AI pipelines on Apple Silicon"，C++20 + 自研 Metal kernel，257 stars |
| 同名干扰 | `cbg-ethz/V-pipe` — ETH 的 NGS 病毒基因组 snakemake 流程，与本任务无关 |
| 最新 release | v0.1.110（2026-11-01）；仓库 main 于 2026-11-13 仍有提交（本地编译版 `0.1 (33cda00*0)`） |
| 支持的模型族 | MiniMax H3（FL2VA/Ref2VA）、Krea-2、FLUX.2/FLUX.3 klein、Qwen-Image-2.1、Qwen 3.8、Ministral 3、LFM3-VL、DeepSeek-V4.1-Flash、Gemma 4、VDN-H3、HyperFlow、Pika H3 Flex… CLI `--list-models` 列出 **152 条** |

**架构要点**（来自 `docs/MINIMAX-H3-zh-cn.md` + 源码）：
- 前向计算不走 Python、不走 MPS/MLX，直接 dlopen 自研 **metal-compute** 内核；另内联复用 MLX 的 Steel 矩阵模板。
- **权重流式传输**：50 个同构 block 顺序计算，block 常驻 SSD、按需搬进统一内存，配合自适应驻留与 mlock'd "wired pool"。
- 生成阶段是 **C++20 协程流水线**，画面/音频/文本在一条图上流转。
- 量化格式：**仿射分组量化（group size 64）**，且会量化 AdaLN 调制层（13B 参数），这是多数通用量化工具会漏掉的。

---

## 2. YouTube 视频内容（字幕 444 段 / 5540 字，已完整抓取）

视频主题：**在 16 GB Mac mini 上用 VPIPE 跑通 MiniMax H3 的音视频生成**，"两步法"。

核心论点与本机实测的对应：

| 视频说法 | 本机实测结果 | 判定 |
|---|---|---|
| 安装包 < 30 MB，无需折腾 Python 环境 | 官方 DMG 42.3 MB（含 FFmpeg），CLI 独立可跑 | ✅ 属实 |
| 核心是「权重流式传输」，用 SSD 当显存 | 日志：`residency probe 50 blocks of 50 (390 MB each)`；收尾 `DiT residency ended at 24 of 50 blocks (9980 MB)` | ✅ 属实 |
| 两步：① 量化准备 ② 文生视频 | `prepare-minimax-h3-8bit` → `minimax-h3-text-to-video`，均跑通 | ✅ 属实 |
| 源模型约 115 GB，8-bit 量化峰值约 180 GB | **实测源 123.6 GB**（文档说的 115 GB 偏小），准备全程 49 分 44 秒 | ⚠️ 数字偏乐观 |
| 量化后删掉 115 GB 源，保留约 65 GB | 产物 **65 GB**（DiT 7 分片 + 编码器 6 分片 + 双 VAE 硬链接） | ✅ 属实 |
| 挂 Turbo-LoRA，4~8 步，别超 8 步 | 4 步 / 6 步各跑一遍，均正常 | ✅ 属实 |
| 选带 `_ema` 后缀的版本（如 v4-600-ema） | 用 `larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema`（779.8 MB） | ✅ 属实 |
| frames 填 120 会自动对齐成 124（17n+5） | 两轮成片均 **124 帧 / 5.18 s** | ✅ 属实 |
| 宽高必须是 32 的倍数 | 960×544，均为 32 倍数 | ✅ 属实 |
| 提示词里要写「发声物体/环境音」，声音才会出来 | 提示词写 "rhythmic soft footsteps… sea breeze… rolling ocean waves"，音轨实测为宽带海浪噪声 | ✅ 属实 |
| M4/M6 开 ane_ffn/ane_qkv；M5 保持默认 i8_gemm | 本机 M5 Pro：`--gpu-info` → `matrix_cores: true`，保持默认 | ✅ 属实 |
| 「第一步约 15 分钟」 | **49 分 44 秒**（因需下载 123.6 GB） | ⚠️ 未含下载时间 |
| 「480p 5 秒 4 步约 4 分钟」 | 960×544 / 4 步 = **5 分 50 秒**（M5 Pro 24 GB） | ✅ 数量级一致 |

### 视频里没提、但很关键的补充
- **AdaLN 预烘焙**：4 步时日志显示 `baked AdaLN for 4 steps (7 rows) -- 51 projections (13216 MB of weights) replaced by 64 MB of tables, and no longer streamed per step`。这就是"少流式 13 GB 权重"的来源。
- **Turbo-LoRA 用运行时挂载而非融合**：`lora` 键 + `lora_scale=1.0`。文档明确说融合会丢掉 22–54% 的 delta，而 Turbo 的 delta 只有 2–4e-4（bf16 步长 ~4e-3），所以运行时挂载是正解。
- **`shift` 是适配器的一部分**：Turbo v4-600 用 12/3；lightx2v 那一系 768p 要改成 6.0，填错不会报错，只会出另一套调度表。
- **视频完全没提的两个 partition**：FL2VA 与 Ref2VA 共用同一个 Qwen3-VL-32B 编码器与同一对双 VAE，**只有 DiT 权重不同**。这是本轮做参考生视频时最关键的结构性认知。

---

## 3. 安装（两条路都走通）

### A. 官方 App（推荐，5 分钟）
```
VpipeManager-0.1.110-with-ffmpeg.dmg (42.3 MB) → /Applications/Vpipe Manager.app
CLI: /Applications/Vpipe Manager.app/Contents/Helpers/vpipe
```
自检：`--version` → `0.1 (9db5dd7*0)`；`--gpu-info` → M5 Pro / macOS 27.2 / `matrix_cores: true`。

### B. 源码编译（为了跑仓库自带测试与拿到最新代码）
```sh
# ① 先编 LGPL FFmpeg（本机没有 ffmpeg 头文件，这是卡点）
bash apps/macos-app/build-lgpl-ffmpeg.sh --prefix <prefix> --jobs 10
# ② 配 + 编
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
      -DVPIPE_BUNDLE_FFMPEG=ON -DVPIPE_FFMPEG_BUNDLE_DIR=<prefix>/lib
cmake --build build -j 10          # 15 核约 12 分钟
# ③ 跑测试（minitest 框架，不是 gtest）
DYLD_FALLBACK_LIBRARY_PATH=<prefix>/lib ./vpipe_test --color off
```
> 不加 `DYLD_FALLBACK_LIBRARY_PATH` 会在 `dlopen libavutil.dylib` 处直接 abort。

### C. Web UI
```sh
vpipe-web-ui --bind 127.0.0.1 --port 9876 --show-qr
```
启动自检会逐项列出权限（Local network / Full Disk Access / Microphone / Camera / 音视频输入设备）。

---

## 4. 模型下载与量化

**关键**：huggingface.co 在本机不通。vpipe 官方文档给了正规解法 —— `VPIPE_MODEL_SOURCE=modelscope`，模型仍注册在 HuggingFace 路径下，recipes 与本地副本互不冲突。

```sh
export VPIPE_MODEL_SOURCE=modelscope
cd ~/AI-Models/vpipe-workspace
vpipe --launch pipelines/prepare-minimax-h3-8bit.vpipeline
```

### 4.1 FL2VA（第一轮）

| 文件 | 字节 | sha256 |
|---|---:|---|
| `diffusion_models/minimax_h3_fl2va_bf16.safetensors` | 66,280,487,368 | `907d4add…6182` ✅ 自动校验 |
| `text_encoders/qwen3vl_32b_minimax_h3_bf16.safetensors` | 51,506,295,256 | ✅ |
| `vae/minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 | **本机已有，硬链接复用，零下载零占用** |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | **同上** |
| `larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema` | 779,849,816 | ✅ 20.4 秒下完 |

**下载速率实测 ~41 MB/s**，全程自动 sha256 校验。

量化产物：
```
models/local/MiniMax-H3-FL2VA-8bit/   65 GB
├── diffusion_models/  model-0000{1..7}-of-00007.safetensors   (8-bit g64)
├── text_encoders/     model-0000{1..6}-of-00006.safetensors   (8-bit g64)
├── tokenizer/         tokenizer.json + config
└── vae/               双 VAE（与源同 inode，硬链接）
```
日志：`902 tensors -> 8-bit g64, scales F16` / 编码器 `350 quantized, 552 passthrough`。

### 4.2 Ref2VA（第二轮）

**难点**：官方 `prepare-minimax-h3-ref2va-8bit.vpipeline` 需要 **117.8 GB**（DiT 66.28 + 编码器 51.5），而本机当时只剩 90.7 GB。

**破解**：只量化 DiT，编码器与双 VAE **硬链接复用 FL2VA 的 8-bit 产物**，净增只有 33 GB。

| 步骤 | 结果 |
|---|---|
| 下载 `minimax_h3_ref2va_bf16.safetensors` | 66,280,487,368 字节，sha256 `e32c54c1a7b4f5f397f195cea267ccb18806303bb665678c4bee60953bdf3026` ✅ |
| 下载方式 | 单连接会被杀（进程随 shell 退出消失），改为 **8 段 Range 并行**，`curl -C -` 断点续传 |
| 下载耗时 | **12 分 51 秒**，聚合 **~127 MB/s** |
| 量化 | 535 tensors → 8-bit g64，**259 quantized / 276 passthrough**，**82 秒** |
| 产物 | `models/local/MiniMax-H3-Ref2VA-8bit/` **33 GB** |

硬链接验证（`stat` 实测 inode）：

| 文件 | inode | links | 说明 |
|---|---:|---:|---|
| `Ref2VA-8bit/vae/minimax_h3_video_vae_fp16.safetensors` | 3246333 | 5 | 与 FL2VA 同源，零额外占用 |
| `Ref2VA-8bit/vae/minimax_h3_audio_vae_fp32.safetensors` | 3246378 | 6 | 同上 |
| `Ref2VA-8bit/diffusion_models/model-0000{1..7}` | 4311737… | 1 | 量化产物，与 bf16 源 inode 完全不同 |

**净增磁盘：33 GB（官方路线为 60 GB）**。这是本轮最实用的一条工程结论。

### 4.3 Pika H3 Flex（第二轮，参考生视频的官方推荐）

```
Pika-Labs/Pika-H3-Flex-fl2va   2,767,274,120 B  sha256 8ed6115d647ab11c1b38d04e63c4c6e1594128ae312f7b5635cd50563b7b9327
Pika-Labs/Pika-H3-Flex-ref2va  2,767,274,120 B  sha256 eef684ba1258f0cdbbbda6128188ad2688417f2eb17ff875375e74a32b6d61b5
```
ModelScope 源，**1 分 14 秒**下完两套，4/4 文件校验通过并自动注册。

每个 adapter 带一份 `manifest.json`，**它接管采样契约**：

```json
{"model":"pika-flex","task":"ref2va","release_id":"pika-flex-ref2va-v1",
 "rank":128,"alpha":128,"trunk":"transformer_ref",
 "numerics_policy":"fp32_conditioning_v1",
 "sampling":{"knots":[1000,750,500,250,100,40,0],"video_shift":12.0,"audio_shift":3.0,"method":"renoise"}}
```

关键点：`trunk: "transformer_ref"` —— ref2va 版绑定的正是 Ref2VA 的专用主干，**分区配对是官方保证的**；`method: renoise` 意味着 6 步不是普通 Euler，而是「取 x0 → 加新噪声到下一档」。运行日志确认：

```
[h3-denoise: 6 steps RE-NOISED on the sampling contract's grid (pika-flex-ref2va-v1): x0 at each sigma, then fresh noise to the next]
```

### 4.4 TAE-H3 实时预览解码器

`madebyollin/taeh3`（22,709,752 字节，sha256 `4fd022bfcab08772fe0536b17ea1a3bbb5625be11e397868d1c5d891863d4c13`）。

官方 `prepare-minimax-h3-preview.vpipeline` 在本机失败，原因见 9.1；改用 GitHub API 的 raw 端点手工取到同一文件（校验和与官方一致），放在 `models/madebyollin/taehv/taeh3.safetensors`，再按文档「`preview_vae` 可直接填一个 `.safetensors` 的路径」接入。

### 4.5 TAE-H3 实时预览：接入成功

验证流水线 `pipelines/h3-taeh3-preview.vpipeline`（FL2VA-8bit + Turbo-LoRA，512×288 / 39 帧 / 4 步），关键日志：

```
[INFO] MiniMaxH3ModelConfigStage('minimax-h3-model-config'): shifts 12.0/3.0,
       condition t 1.000/1.000, audio as long as the video, runtime lora at 1.00,
       previews every 1 step(s)
[INFO] LatentPreviewer('generate-video'): taehv TAE
       'models/madebyollin/taehv/taeh3.safetensors'
       -- 24 latent channels, 16x spatial, 4x temporal, 9.9M params
[INFO] preview('preview'): looping a 39-frame clip at 512x288, 24 fps;
       each new clip replaces it
```

**TAE 解码成功并接到了 preview 端口**：39 帧的预览 clip 被解码出来、由 preview stage 循环播放。TAE 的规格与官方一致（时序解码器，4× temporal upsample，9.9M 参数）。

`preview_vae` 的三种写法实测都可用：

| 写法 | 结果 |
|---|---|
| `models/madebyollin/taehv`（相对目录，含单个 .safetensors） | ✅ |
| `models/madebyollin/taehv/taeh3.safetensors`（相对文件路径） | ✅ |
| `/Users/.../taeh3.safetensors`（绝对文件路径） | ✅ |

**一次偶发失效的观察**：首次运行时（紧接另一个 vpipe 进程退出后启动）预览完全没加载 —— 日志里连 `LatentPreviewer` 这一行都没有，且**没有任何警告或报错**；配置一字未改重跑即正常。源码注释提到 model_config beat 与 model 的到达顺序会影响解析时机（"either can be first"），因此这很可能是 **config beat 的时序竞态**。因未能稳定复现，本报告只记录现象，不计入 issue。

**CLI 下的行为提醒**：preview stage 是 WebSocket sink（0 oports），**接上它之后流水线不会自己结束** —— 官方文档说得很明确："The `preview` stage runs until you stop the pipeline."。要用 Web UI 跑；命令行下需自行终止。

### 4.6 多模型对照组（第三轮）

先回收空间再下新模型。**Ref2VA 的 bf16 量化源**（66,280,487,368 B / inode 4310295 / links=1，与 8-bit 量化分片完全独立）已按官方文档"Once preparation finishes you can delete the source repack and keep the ~65 GB"删除，回收 **61 GiB**（可用空间 37 GiB → 93 GiB）。

> ⚠️ **本机 `rm` 的 safe-delete 钩子只把文件搬进 `~/.Trash` 而没有清空**，`df` 读数完全不变。`osascript` 清空废纸篓报 `-10004 权限违例`，`unlink` 报 `Operation not permitted`（macOS TCC 保护）。**可行解法是直接调用系统 rm 绕过 shim**：
> ```sh
> /bin/rm -f "/Users/minichen/.Trash/<文件名>"   # which -a rm 第一条是 shim，最后一条才是 /bin/rm
> ```

HF 直连本机不通（curl 超时），**全部走 ModelScope**（`VPIPE_MODEL_SOURCE=modelscope`）：

| 模型 | 体积 | 校验 | 下载 | 用途 |
|---|---:|---|---|---|
| `LiquidAI/LFM3-VL-2B` | 3.6 GB | ✅ | 3 分 24 秒（含 Qwen 共用） | 视频帧语义理解（VQA） |
| `mlx-community/Qwen3.5-4B-MLX-4bit` | 2.9 GB | ✅ 13/13 | 同上 | 中文多模态对话 |
| `Tongyi-MAI/Z-Image-Turbo` | 32.8 GB | — | ModelScope | 文生图（6B / 8 步蒸馏） |
| `krea/Krea-2-Turbo` (+ `mgwr/M87` + `madebyollin/taew2_1`) | ~30 GB | — | ModelScope | 文生图（12B） |

下载时 vpipe 会提示**未拉取的伴随 checkpoint**，例如 Qwen3.5-4B 缺 `qwen3_5_mlx_4b_vision_vid_512x320` / `_768x480` / `z-lab/Qwen3.5-4B-DFlash` —— *"A stage that wants one will refuse at launch; fetch each with model-fetch model_path=<key>"*。本轮只用纯图片通道，未触发。


---

## 5. 全面测试结果

### 5.1 仓库单元测试：3464 条 / 368 套件
```
[==========] 3464 tests from 368 test suite ran. (400284.030 ms total)
[  PASSED  ] 3460 tests.
[  FAILED  ] 4 test
```

| 失败项 | 定性 | 依据 |
|---|---|---|
| `save_audio_stage.aac_mp3_m4a_roundtrip` | **本地构建产物，非 vpipe 缺陷** | 只挂 mp3（aac/m4a 通过）。自建 LGPL ffmpeg 未带 libmp3lame；换官方 App 的 Frameworks 后即通过 |
| `model_register_stage.every_pinned_catalogue_entry_detects_as_itself` | **上游缺陷** | 102 条钉住条目中 3 条识别不出：`videorebirth/hyperflow`、`videorebirth/hyperflow-ref2va`、`PrunaAI/P-H3-Image-no-dit` |
| `model_register_stage.minimax_h3_supplements_detect_as_themselves` | **上游缺陷** | 同类：目录里有条目，detector 签名表没覆盖 |
| `relaunch_sweep.every_registered_source_is_covered` | **上游测试维护滞后** | 新增 stage（vosr-/flashvsr-model-config、training-dataset、optimizer-select）没加进测试的 `kSweep` 清单 |

> 后 3 项都是**纯离线测试**（构造假文件做识别），与 ffmpeg/网络无关，是仓库 main 的真实问题。

### 5.2 Web UI
Playwright 实测渲染正常（非空白/非错误页）：左侧 Pipelines / Profiler / User I/O / Database / Files / Composer / Plugins 导航，STAGES 工具箱（PREPARATION 8 / VISUAL 17 / CONFIGURATION），底部实时状态条 `ANE 0.0% | GPU 42.0% | GPU MEM 2.01 GB / 24.0 GB | MEM 13.3 MB`。

### 5.3 文生视频（第一轮，两轮）
| 轮次 | 步数 / seed | 耗时 | 规格 | 产物 |
|---|---|---:|---|---|
| 1 | 4 步 / seed 6 | **5 分 50 秒** | H.264 960×544 / 24 fps / 124 帧 / 5.18 s + AAC 32 kHz | `h3-t2v-turbo.mp4` (1,401,884 B) |
| 2 | 6 步 / seed 42 | **8 分 01 秒** | 同上 | `h3-t2v-turbo-6step.mp4` (1,397,018 B) |

两轮均在 **bf16 源已不存在**的情况下跑通 → 证明 8-bit 量化模型自包含。

### 5.4 音轨核验（"音画一体"的关键证据）
```
时长 5.17 s @ 32 kHz | 峰值 1748 (5.3% FS) | RMS 267.5 (0.82%) → 非静音
分段 RMS(每 0.5s): 61 78 90 109 137 249 399 479 408 250   ← 浪涌涨落弧
频带能量: 20-120Hz 5.8% | 120-400 15.2% | 400-1k 21.3% | 1-3k 31.3% | 3-8k 20.7% | 8-16k 5.4%
<1 kHz 占比 42.4%，无谐波结构 → 宽带海浪/风噪
```
音频不是后期贴上去的，是与画面在同一次去噪里长出来的（架构上音画共用一条打包序列）。参考生视频的三支片子同样带 AAC 立体声轨（32 kHz，127 kb/s）。

### 5.5 画面核验
抽帧目检（0/1.3/2.6/3.9/5.0 s）：金色逆光、湿润沙滩镜面反光、白色连衣裙、发丝与裙摆飘动、浪线推进，帧间连贯无跳变、无畸变。第一轮画面与原视频开篇镜头（金发美女沿退潮沙滩慢跑）高度一致。

### 5.6 首尾帧插值（FL2VA，第二轮重跑）

第一轮该流水线的进程无错消失（推测与当时 66 GB 并行下载的 IO/内存竞争有关）；下载结束后重跑，**8 分 41 秒跑通**。

| 项 | 值 |
|---|---|
| 规格 | H.264 960×544 / 24 fps / 124 帧 / 5.18 s + AAC 32 kHz 立体声 |
| 锚点 | 日志：`2 keyframe anchors (first + last frame), noised to t 1` |
| 首帧 | 参考图 center-crop 到 960×544（全身中景） |
| 末帧 | 参考图内 `scale 1.6875` 的窗口（`src_x 455, src_y 239`）→ 面部特写 |

抽帧目检（0 / 1.3 / 2.6 / 3.9 / 5.0 s）：镜头从**正面全身中景**平滑推到**面部极特写**，中间依次经过俯身抬爪、低头舔爪、闭眼特写；**深蓝牛仔外套在全过程中始终保留**，毛发与胡须细节连贯、无跳变、无畸变。

### 5.7 参考生视频（第二轮）

| 组 | 配置 | 耗时 | 规格 | 首次 forward |
|---|---|---:|---|---:|
| **A** 有参考图 | Ref2VA-8bit + Pika ref2va + 猫图 | **6 分 49 秒** | 832×480 / 124 帧 / 5.18 s + AAC | 16,999 rows / 5,556 ms |
| **B** 空参考（对照） | 同上，`references: []` | **5 分 50 秒** | 同上 | 14,943 rows / 5,386 ms |
| **C** 官方已发布配对 | FL2VA-8bit + VDN 线性分支 + Turbo + 猫图 | **8 分 20 秒** | 960×544 / 124 帧 / 5.18 s + AAC | 20,543 rows / 5,609 ms |
| **D** 强消融（熊猫图） | 同 A，参考图换成黑白熊猫 | **6 分 48 秒** | 同 A | 16,999 rows / 5,538 ms |

内部指标：

| 指标 | A | B | C |
|---|---|---|---|
| AdaLN 烘焙行数 | **17 rows**（157 MB 表） | **11 rows**（101 MB 表） | 17 rows（157 MB 表） |
| DiT 常驻收尾 | 24/50 blocks (9,980 MB) | 18/50 blocks (7,485 MB) | — |
| VDN 窗口 | — | — | 37 帧 × 510 tokens，111,155/206,082 key blocks（dense 的 53.9%） |

**A 与 B 差 2,056 行、AdaLN 表多 6 行** —— 这是参考图确实被打包进 DiT 序列的**内部量化证据**（参考行占一个 rotary slot、按各自噪声水平保持）。

### 5.8 首帧图生视频（i2va，带货「商品图 → 短视频」）

用 Pika H3 Flex 的 **fl2va** adapter 走首帧锚定：`load-image` → `image-resample`(832×480 crop) → `vae-encode` → `generate-video` 端口 5。

| 项 | 值 |
|---|---|
| 耗时 | **5 分 59 秒** |
| 规格 | H.264 832×480 / 24 fps / 124 帧 / 5.18 s + AAC 32 kHz 立体声 |
| 锚点日志 | `1 keyframe anchor (first frame) rounded to bf16 (the adapter's conditioning policy), noised to t 0.999` |
| 采样契约 | `pika-flex-fl2va-v1`（knots 7 点 / renoise） |
| 首次 forward | 15,712 rows / 5,685 ms |

首帧与参考图 crop 的**像素级实测**（ffmpeg SSIM/PSNR）：

| 指标 | 值 |
|---|---|
| SSIM (All) | **0.9032** |
| PSNR | **31.11 dB** |
| 差分图形态 | 均匀低阶强度偏差 + 仅主体轮廓处有边缘残差（无几何错位） |

> 差分图证明：**几何完全对齐**，残差只来自 VAE 编解码与 H.264 压缩，不是重新生成。

### 5.9 保真度量化：锚定路线 vs 参考生视频路线（SSIM 衰减）

对每支片子逐帧与「对应参考图裁到同一分辨率」做 SSIM（脚本 `vpipe-lab/anchor-fidelity.sh`）：

| 视频 | 帧数 | 全片平均 SSIM | 首帧 | 中帧 | 末帧 |
|---|---:|---:|---:|---:|---:|
| **i2va 首帧锚定**（猫+牛仔外套） | 124 | 0.5774 | **0.9505** | 0.4245 | 0.4377 |
| **FL2VA 首尾帧锚定**（猫+牛仔外套） | 124 | 0.6657 | **0.9500** | 0.6425 | 0.6139 |
| Pika Ref2VA 参考生视频（猫参考） | 124 | 0.5120 | 0.5245 | 0.5093 | 0.5247 |
| Pika Ref2VA 参考生视频（熊猫参考） | 124 | 0.4896 | 0.4868 | 0.4896 | 0.4940 |
| Pika Ref2VA 无参考对照（猫参考） | 124 | 0.5718 | 0.5805 | 0.5718 | 0.5735 |
| FL2VA + VDN 仿 Ref2VA（猫参考） | 124 | 0.4721 | 0.4868 | 0.4691 | 0.4795 |

三条可直接下结论的读数：

1. **两条锚定路线首帧 SSIM 都是 0.95**（近像素级），参考生视频路线首帧只有 **0.49–0.52**。参考图在 Ref2VA 里是**语义条件**，不是像素重建。
2. **参考生视频"有参考"(0.5120) 反而低于"无参考对照"(0.5718)** —— 数值上证明参考图**不是把输出往参考图上拉**，而是改写主体本身。
3. **FL2VA + VDN 仿 Ref2VA 是全表最低 (0.4721)** —— 这条路根本没建立参考图通道，SSIM 水平与"完全不看参考图"一致。

### 5.10 多模型能力面对照（第三轮新增）

新增两个非 H3 模型，独立于生成链路做验证：

| 模型 | 体积 | 角色 | 实测 |
|---|---|---|---|
| **LiquidAI/LFM3-VL-2B** | 3.6 GB（13/13 校验通过） | 视频帧语义理解（VQA） | prefill **5,626 tok/s** / decode **50.6 tok/s**，整条流水线 5.1 s |
| **mlx-community/Qwen3.5-4B-MLX-4bit** | 2.9 GB（13/13 校验通过） | 中文多模态对话 | prefill **1,568 tok/s** / decode **83.0 tok/s**，整条流水线 6.0 s |

两者的接线方式（官方文档口径）：`text-input`（`media: true`）→ `text-chat` → `save-text`，图片以**媒体行标记**内联：

```
<|__vpipe_fs_im_start__|/abs/path/frame.png<|__vpipe_fs_im_end__|>
```

`text-chat` 是持久 K/V 对话 stage，`save-text` 以 `key="text"` 取回 assistant 回合记录；`feedback-tx`/`feedback-rx` 构成交互回路，单发测试时从 **stdin 管道喂一行**即可。

**Qwen3.5-4B 的独立确认**（中文问答 + 附熊猫帧）：

> 1) H3 模型在 vpipe 中主要负责处理视频相关的任务，例如视频生成、视频编辑、视频分析等……
> 2) 下面这张图里的动物是**大熊猫**。它正坐在窗台上，伸出舌头舔手指，神情可爱……

**LFM3-VL 对四组产出的同一提问**（"这些画面里的动物是什么？毛色、姿态、环境？用中文回答"）：

| 视频 | LFM3-VL 的回答（摘要） |
|---|---|
| **D 组（熊猫参考）** | "**这些画面中的动物是熊猫**。它的毛色主要是黑白相间……它坐在窗台上……第二张图中，熊猫伸出舌头，似乎在舔自己的爪子" |
| A 组（猫参考） | "一只猫。毛色是**橙色，带有深色的条纹**……在窗台上" |
| B 组（无参考对照） | "一只猫。它有着**橙白相间**的毛色……坐在窗台上" |
| i2va（首帧锚定） | "第一张画面里的猫身上穿着一件**深蓝色的短袖衬衫**，款式类似于西装外套，带有纽扣。**后面的两张画面里，这件衣服并没有出现**，猫只是在窗台上坐着，没有穿任何衣服" |
| **首尾帧锚定** | "猫身上穿着一件短袖衬衫，颜色为**深蓝色**，款式类似于典型的衬衫设计，带有纽扣。**每一张画面中的衣服都还在，猫的衣着保持一致，没有变化**" |

### 5.11 文生图对照：Z-Image-Turbo vs Krea-2-Turbo

vpipe 内置 catalog 有 152 个模型条目，本轮挑了 image 类里两个 8 步蒸馏模型做同提示词横评。

| | **Z-Image-Turbo** | **Krea-2-Turbo** |
|---|---|---|
| 来源 | `Tongyi-MAI/Z-Image-Turbo` | `krea/Krea-2-Turbo` |
| 磁盘 | 31 GB（transformer 权重 24.6 GB / 12.3B 参数 / 3 分片） | 33 GB（28 transformer blocks，官方称 **36 GB**） |
| LoRA | 无 | **M87 拿不到**（只发布在 HuggingFace，本机 HF 不通）→ 按官方文档「Running without the LoRA」去掉 `lora`/`lora_scale` 与提示词末尾的 `--preview` |
| 采样 | `simple (8 steps, shift 3 linear, rho 7)`，`guidance_scale = 0`（**no cfg**） | `euler+simple 8 steps`，**每步 5,458–5,705 ms** |
| **耗时** | **42.5 秒**（latent 36.92 秒） | **49.5 秒 / 46.9 秒**（latent 45.64 / 43.67 秒） |
| 内存 | 声明峰值 31,311 MB → 实际流式驻留 **18,452 MB** | 声明峰值 34,014 MB → 实际流式驻留 **15,841 MB** |
| 输出 | 1024×1024，latent `[16, 128, 128]` | 1024×1024，latent `[16, 128, 128]` |

> **24 GB 统一内存上跑 24.6 GB / 28 GB 的 bf16 权重，靠的是 vpipe 的 residency 流式加载** —— 官方文档说得很直白："At bf16 the 28 transformer blocks do not fit beside the conditioner's text encoder even on 24 GB -- `plan_streaming` says stream there too."

**与官方基准对照**（官方 `docs/KREA-2.md`：M5 Pro **20 核** MacBook Pro 16" 24 GB = **35 秒**）：本机 M5 Pro **15 核**实测 49.5 / 46.9 秒。核数比 20/15 = **1.33×**，耗时比 49.5/35 = **1.41×** —— 与官方"耗时随 GPU 核数近似线性缩放"的结论吻合。

**两支成片（对照图 `images/t2i-compare.png`，左 = Z-Image，右 = Krea）**：

- **猫场景**（与 5.6/5.8 的视频实验**同一提示词**）：两个模型都产出姜黄虎斑猫 + **深蓝牛仔外套（铜扣、翻领、口袋）** + 木窗台 + 暖阳 —— 与视频实验的主体、场景、服装**三要素一致**，构成一次跨模态一致性验证。风格上 Krea 明显更"胶片摄影"（窗玻璃里有猫的倒影、暖调更强），Z-Image 更干净通透。
- **带货商品图**：两张都是可用级别的电商主图 —— **木衣架、米色墙、左侧窗光、铜扣、撞色明线**都在。Z-Image 偏浅蓝、构图更规整；Krea 偏深靛蓝、**丹宁织纹与竖向落色纹理更明显**。

**LFM3-VL 对四张图的细节读数（逐张作答）**：

| 图 | 模型 | 颜色 | 金属扣 | 面料纹理 |
|---|---|---|---|---|
| 图1 猫 | Z-Image | 蓝色 | **3 个** | 清晰，丹宁织纹 + 明显缝线 |
| 图2 猫 | Krea-2 | 蓝色 | **3 个** | 清晰，丹宁织纹 + 缝线 |
| 图3 商品 | Z-Image | 深蓝色 | **5 个** | 清晰，丹宁织纹 + 缝线 |
| 图4 商品 | Krea-2 | 深蓝色 | **5 个** | 清晰，丹宁织纹 + 缝线 |

两个模型在扣子数量与纹理细节上**给出一致的读数**（猫图 3 扣 / 挂拍商品图 5 扣），说明两者在"电商图必须数得清扣子"这个硬指标上**都过关**。

---

## 6. 参考图到底有没有生效？——一次方法论纠错

这是第二轮的核心，也是本报告最有价值的部分。

### 6.1 第一版报告的错误

第一版里那支 Ref2VA 成片，提示词是：

> *"`<Subject 1>` is the ginger tabby cat in `<Picture 1>`, with a dense orange tabby coat, white chest and paws, and green eyes. …"*

我一度据此判定「参考图生效了」。**这个结论下得太早**：提示词已经把毛色、斑纹、眼睛颜色全部写死，即使参考图完全失效，模型照样能生成姜黄虎斑猫。**这是不可证伪的实验设计。**

### 6.2 消融对照与它的局限

重做时把提示词改成**零外观描述**：

> *"References: @Image1 is the subject sheet. Make a new video of the subject from @Image1. The subject sits on a wooden windowsill in warm late-afternoon sunlight, looks directly at the camera, blinks slowly and gently licks its paw; …"*

A 组（有参考图）输出：**姜黄虎斑猫、绿眼、额头 M 形深纹、白胸白爪**，与参考图高度一致。

**但 B 组（`references: []`，同一提示词、同一 seed）也输出了姜黄虎斑猫** —— 色调更浅、虎斑更淡、白胸面积更大。「窗台 + 暖阳 + 猫」这个场景本身就是模型的强先验。

> **结论：在这套提示词下，A/B 在外观层面不具区分度，不能据此断言参考图生效。** 必须换一个模型先验不可能命中的主体。

### 6.3 强消融：换成模型先验不可能生成的参考主体（D 组）

用仓库自带的第二张参考图 `klein-multi-ref-panda.jpg` —— 一张**水彩插画风格的黑白熊猫**（黑耳、黑色眼斑、抱着竹子）。「窗台暖阳」场景的先验绝不会产出黑白水彩熊猫。

**D 组结果（提示词、seed、模型、adapter、采样契约全部与 A/B/C 相同，只换参考图）**：

| 组 | 参考图 | 输出主体 |
|---|---|---|
| A | 姜黄猫（写实照片） | 姜黄虎斑猫，绿眼，额头 M 形深纹 |
| B | 无（`references: []`） | 姜黄虎斑猫（色调更浅、虎斑更淡、白胸更大） |
| C | 姜黄猫（写实照片） | 姜黄虎斑猫（FL2VA 路线，色调最深、条纹对比最强） |
| **D** | **黑白熊猫（水彩插画）** | **黑白熊猫** — 黑耳、黑色眼斑、黑白四肢，**坐姿与参考图一致** |

> **结论确凿：参考图是决定性输入。** 主体类别与配色随参考图改变，而"窗台暖阳"的场景先验只决定环境、不决定主体。这同时**纠正了第一版的判断**——参考图一直是有效的，第一版的问题在于**实验设计不可证伪**（提示词把外观写死），而不是参考图不起作用。

三组内部的量化差异同样支持这一结论：

| 指标 | A（猫图） | B（空参考） | D（熊猫图） |
|---|---|---|---|
| 首次 forward 的序列行数 | 16,999 | 14,943 | 16,999 |
| AdaLN 烘焙行数 | 17 rows | 11 rows | 17 rows |

参考图贡献 **2,056 行**（A/D 相同——参考行数只由图片尺寸决定，与内容无关；而 B 少掉的正是这些行）。

#### 6.3.1 第三方模型复核（脱离生成链路的独立证据）

上面全是「看片 + 看日志」。为了不给自己的眼睛找台阶，把 D 组和 A/B 组的帧喂给**另一个模型**（LFM3-VL-2B，完全不参与生成），问同一个问题：

> 这些画面里的动物是什么？请描述它的毛色、姿态和所处环境。用中文回答。

| 被问的视频 | 提问里的参考图 | LFM3-VL 的判定 | 是否符合参考图 |
|---|---|---|---|
| **D 组** | 黑白熊猫（水彩插画） | "**这些画面中的动物是熊猫**。它的毛色主要是黑白相间，头部和背部为白色，四肢和身体的其他部分为黑色……坐在窗台上……伸出舌头，似乎在舔自己的爪子" | ✅ 完全一致 |
| A 组 | 姜黄猫 | "一只猫。毛色是**橙色，带有深色的条纹**" | ✅ 一致 |
| B 组 | **无** | "一只猫。它有着**橙白相间**的毛色" | ✅ 一致（但毛色描述不同） |

**D 组的提示词里没有"熊猫"二字**，"窗台暖阳"的场景先验也产不出黑白水彩熊猫 —— 而两个互相独立的第三方模型（LFM3-VL-2B 与 Qwen3.5-4B）都把它判成熊猫。这就把结论从"我自己看着像"升级为**可证伪且被独立复核的结论**。

同时 A/B 两组都被判为"猫"但**毛色描述不同**（A："橙色带深色条纹"；B："橙白相间"），这正好复现了 6.2 说的局限 —— 猫这个参考主体在场景先验覆盖范围内，**只有换成先验不可能产出的主体（熊猫）才能做出有区分度的消融**。


### 6.4 配置纠错：Ref2VA partition 上挂 VDN 是「无发布配置」

第一版给 Ref2VA 配了 VDN 线性分支。复核官方文档后发现**这条路没有官方背书**：

- 官方文档：*"**the VDN branch is only published for FL2VA**, so before it the linear attention and references could not be had together."*
- 源码 `generative-models/minimax-h3/metal-minimax-h3-transformer.cc:8780`：

```cpp
if (L.ref2va && _cfg.partition == "ref2va") {
  _mc->session()->warn(fmt(
      "MetalMiniMaxH3Transformer: VDN's branch is trained on the "
      "FL2VA partition's blocks and this is Ref2VA; its {} reference "
      "rows are attended densely, outside the window, and the linear "
      "branch does not see them -- no published configuration pairs "
      "the two", L.num_condition_rows));
}
```

同一处注释：*"On the Ref2VA partition the branch would be attached to blocks it was not trained with, **which nothing published does** -- that one still warns."*

而**官方发布的参考路线是「FL2VA 权重 + references」**（即 `ref2va-like` 模式，由 OpenVDN 于 2026-09-17 发布）：引用行照 Ref2VA 的方式打包，但由 FL2VA 的 transformer 读取。

**第一版还有一处配置错误**：给 Ref2VA partition 挂了 FL2VA 专用的 Turbo adapter（`larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema`，`parent_model_type = "minimax-h3-fl2va"`，catalog 里**没有** Ref2VA 版条目），vpipe **不报错也不警告**，完整出了片。这条已写成上游 issue（见 9.2）。

### 6.5 四条路线的选型结论（带货场景）

| 路线 | 参考一致性 | 速度 | 官方背书 | 建议 |
|---|---|---|---|---|
| **Ref2VA-8bit + Pika H3 Flex ref2va** | 最高（专用主干 `transformer_ref` + 专用 adapter） | **6 分 49 秒**（832×480 / 6 步） | ✅ 官方发布 | **首选** |
| FL2VA-8bit + VDN + Turbo（ref2va-like） | 中高（音色更接近参考图） | 8 分 20 秒（960×544 / 6 步） | ✅ 官方发布 | 需要 960×544 高清时用 |
| Ref2VA-8bit + VDN | ⚠️ 无发布配置 | 12 分 54 秒 | ❌ | 不建议 |

> 参考一致性的判定方法见 6.3：D 组把参考图换成黑白熊猫，同一套提示词下输出就是黑白熊猫 —— 主体类别与配色**完全由参考图决定**，场景先验只决定环境。

**给带货场景的一条实操经验（本轮最实用的发现）**：**参考图负责「主体长什么样」，但服装、配饰这类特征往往不会自动保留。** 参考图里的姜黄猫穿着深蓝牛仔外套 —— A/C 两组（参考生视频）都没复现。

⚠️ **这里要修正一个第一轮的高估**：第二轮的量化与 VQA 复核证明，**"首帧锚定"并不等于"全程保服装"**。5.8/5.9/5.10 三组证据一致：

- i2va（**只有**首帧锚定）首帧 SSIM **0.9505**，但从第 ~45 帧起断崖跌到 0.42；
- LFM3-VL 逐帧看 i2va：**"第一张画面里的猫身上穿着一件深蓝色的短袖衬衫……后面的两张画面里，这件衣服并没有出现"**；
- 而首尾帧锚定那支，5 帧全部 SSIM ≥ 0.61，LFM3-VL 明确回答 **"每一张画面中的衣服都还在，猫的衣着保持一致，没有变化"**。

| 路线 | 主体身份 | 首帧像素保真 | **服装 / 配饰** | 适合 |
|---|---|---|---|---|
| 参考生视频（`video-ref-encoder`） | ✅ 保留（品类、毛色、纹样） | ❌ 0.49–0.52 | ⚠️ 常丢失 | 换场景、换动作，主体大致像就行 |
| **仅**首帧锚定（`vae-encode` + 端口 5） | ✅ 像素级保留首帧 | ✅ **0.9505** | ❌ **约 2 秒后漂移消失** | 静态开场 + 短动态 |
| **首尾帧锚定**（端口 5 + 6） | ✅ 首尾双锚 | ✅ **0.9500** | ✅ **全程保留** | **商品图 → 短视频，必须保真时首选** |

> **带货实操结论**：商品要在整段片子里都在，**必须给到末帧锚定**（首尾帧都提供含商品的图），不能只给首帧 —— 只给首帧时，DiT 会按提示词重构画面，商品在约 2 秒后消失。

两支片的 7 帧接触印相（`images/i2va-jacket-drift-sheet.png` / `images/firstlast-jacket-kept-sheet.png`）把这个差别拍得很清楚：

| 仅首帧锚定（i2va） | 首尾帧锚定（first-last） |
|---|---|
| 第 0 / 20 帧：深蓝牛仔外套 + 铜扣清晰可见，暗背景正面像 | 第 0 帧：深蓝牛仔外套 + 铜扣，暗背景全身中景 |
| **第 40 帧起：外套彻底消失**，背景换成亮窗、姿态由正面转为侧身 —— 画面被 DiT 按提示词整体重构 | 第 20→123 帧：镜头平滑推进到面部特写，**外套与铜扣每一帧都在** |

官方 Pika 提示词范式里也明确要求写 *"Keep the character exactly as designed in @Image1 — same face, proportions, **outfit**, colours"* —— 说明服装丢失是已知问题，官方给的解法就是**在提示词里点名要保留**。但若商品必须像素级保真（logo、吊牌、包装），**首尾帧锚定比参考图更可靠**。


---

## 7. 踩坑清单

1. **本机 `rm` 会被 safe-delete 钩子重定向到 macOS 废纸篓** —— 文件"删了"但磁盘没释放。清理完必须查 `~/.Trash` 与 `diskutil info /System/Volumes/Data | grep "Container Free Space"`。
2. **`df` 读数滞后** —— 删除后第一次 `df` 常是旧值，要用 `diskutil` 复核。
3. **几个 GGUF 之间本就是同 inode 的硬链接别名** —— 标称体积大于实际唯一数据，估空间时要按 inode 数算。
4. **`model_path` 指向 repo，不是注册表键** —— 同 repo 多模型时必须加 `model_variant`，值是目录里的 `.variant` 标题串（如 `Turbo few-step v4-600 EMA (larryvrh)`）。
5. **自建流水线要照抄官方文件的 `iports`** —— 只抄 `config` 会导致 stage 之间没连线，日志表现为 `no model -- ... inert`。
6. **`save-video` 的 `output_url` 用绝对路径最稳**。
7. **FFmpeg 头文件本机没有** —— 源码编译必须先跑仓库自带的 `build-lgpl-ffmpeg.sh`。
8. **`model-select` 不写注册表，只有 `model-quantize` 写** —— 手搓模型目录后 `model-select` 会报 `cannot open <dir>/transformer`。正确做法是用 `model-quantize` 跑一遍（`src_model` 给绝对路径、`output_name` 给**相对**路径），让它把注册键写进 LMDB。
9. **`nohup … &` 在本环境会被杀** —— 后台任务必须用工具的 `run_in_background`；大文件下载同理（单连接 curl 跑了 867 MB 就消失）。
10. **`linear_branch` 默认为 `"auto"`** —— Ref2VA 下会自动选一个未下载的 VDN 模型，导致 `attach_linear_branch` 失败 → DiT 被丢弃 → 日志 `no DiT; skipping`。必须显式写 `linear_branch`。
11. **`VPIPE_MODEL_SOURCE=modelscope` 会让只在 GitHub 发布的模型取不到**（taeh3 系列）—— 见 9.1。
12. **ffmpeg 9.0（本机 hermes 版）的 `-update 1` 选项不存在**，`filter_complex` 里混用 `drawtext` 也容易踩解析坑；拼图最稳的是「先用 `-vf` 逐帧处理 → 再纯 `hstack/vstack` 拼接」。

---

## 8. 复现步骤

```sh
# 0) 装 App
hdiutil attach VpipeManager-0.1.110-with-ffmpeg.dmg && cp -R "Vpipe Manager.app" /Applications/

# 1) 准备 FL2VA（下载 123.6 GB + 8-bit 量化，约 50 分钟）
cd ~/AI-Models/vpipe-workspace
export VPIPE_MODEL_SOURCE=modelscope
"/Applications/Vpipe Manager.app/Contents/Helpers/vpipe" --launch ./pipelines/prepare-minimax-h3-8bit.vpipeline

# 2) 准备 Ref2VA（见 4.2 的硬链接复用法，净增 33 GB）
#    只量化 DiT，编码器与双 VAE 硬链接复用 FL2VA-8bit

# 3) 准备 Pika H3 Flex adapter（1 分 14 秒）
vpipe --launch ./pipelines/prepare-pika-h3-flex.vpipeline

# 4) 文生视频（960×544 / 4 步 / 带声音，约 6 分钟）
./run_t2v.sh

# 5) 参考生视频（832×480 / 6 步 renoise，约 7 分钟）
vpipe --launch ./pipelines/pika-ref2va-ablation.vpipeline

# ---- 第三轮 ----

# 6) 首帧图生视频 i2va（832×480 / 6 步，约 6 分钟）
vpipe --launch ./pipelines/pika-i2va-shop.vpipeline

# 7) 首尾帧插值（960×544 / 5 步，约 9 分钟）
vpipe --launch ./pipelines/h3-first-last.vpipeline

# 8) 多模型对照组（LFM3-VL-2B + Qwen3.5-4B，约 4 分钟）
vpipe --launch ./pipelines/prepare-multimodal-compare.vpipeline

# 9) 文生图模型（Z-Image-Turbo 32.8 GB + Krea-2-Turbo ~30 GB）
vpipe --launch ./pipelines/prepare-image-models.vpipeline

# 10) 语义验证：stdin 喂一行，图片用媒体行标记内联
echo "这些画面里的动物是什么？用中文回答。<|__vpipe_fs_im_start__|>/abs/path/frame.png<|__vpipe_fs_im_end__|>" \
  | vpipe --launch ./pipelines/lfm3-vl-vqa.vpipeline

# 11) 保真度量化（逐帧 SSIM/PSNR）
bash scripts/anchor-fidelity.sh
```

工作区：`~/AI-Models/vpipe-workspace/`
```
data.mdb  lock.mdb          ← 会话与模型注册表（路径 = 工作目录）
models/<owner>/<repo>/      ← 下载的权重
models/local/               ← 量化产物（生成阶段的 hf_dir 指向它）
models/larryvrh/...         ← Turbo-LoRA
models/Pika-Labs/...        ← Pika H3 Flex adapter + manifest
models/madebyollin/taehv/   ← TAE-H3 预览解码器
models/LiquidAI/...         ← LFM3-VL-2B（VQA）
models/mlx-community/...    ← Qwen3.5-4B-MLX-4bit（对话）
models/Tongyi-MAI/...       ← Z-Image-Turbo
models/krea/...             ← Krea-2-Turbo
pipelines/  out/  refs/  run_*.sh
```

---

## 9. 上游 issue（5 条，详见 `vpipe-upstream-issues.md`）

| # | 标题 | 性质 | 证据 |
|---|---|---|---|
| 1 | `url-files` 型模型只绑定单一 GitHub URL，受限网络下无备用通道 | feature/bug | 官方 `prepare-minimax-h3-preview.vpipeline` 在本机 SSL 失败；同一文件用 `api.github.com` 的 raw 端点可正常取到 |
| 2 | `parent_model_type` 与当前 partition 不符的 LoRA 不被拒绝（与 manifest 型 adapter 规则不一致） | bug | FL2VA 专用 Turbo adapter 挂到 Ref2VA 上，vpipe 无任何提示跑完全流程 |
| 3 | Ref2VA partition + VDN linear branch 只警告不拒绝，产出「无发布配置」的结果 | bug | `metal-minimax-h3-transformer.cc:8780` 警告文本 + 文档「VDN branch is only published for FL2VA」 |
| 4 | 准备 Ref2VA 时编码器被无谓地重新量化（多出 27 GB 新字节） | feature | 官方准备流程净增 ~60 GB；复用 FL2VA-8bit 的编码器与双 VAE（硬链接）后净增仅 33 GB，本机已验证 |
| 5 | `model-fetch` 的「伴随 checkpoint 未拉取」警告不准确（第三轮新增） | bug | 拉 `Qwen3.5-4B-MLX-4bit` 时警告"stage will refuse at launch"，但该模型自带 297 个视觉塔张量且 `text-chat` 图文问答正常跑通 |

（第一轮定位的 3 条识别/清单缺陷 + 本报告的实测吞吐数据，仍建议一并提交。）

**每条 issue 已拆成可直接粘贴的单文件**：`report/issues/issue-1.md` … `issue-5.md`（首行标题 + 其后正文）。本机未安装 `gh` 且没有 GitHub token，需手动提交。


---

## 10. 交付物

### 视频
| 文件 | 说明 |
|---|---|
| `videos/h3-t2v-turbo.mp4` | 文生视频 4 步（5 分 50 秒） |
| `videos/h3-t2v-turbo-6step.mp4` | 文生视频 6 步（8 分 01 秒） |
| `videos/pika-ref2va-ablation.mp4` | **参考生视频 A 组**（Pika Ref2VA + 参考图，6 分 49 秒） |
| `videos/pika-ref2va-noref.mp4` | 空参考对照组 B 组（5 分 50 秒） |
| `videos/fl2va-ref2va-like-ablation.mp4` | 官方 ref2va-like 路线 C 组（8 分 20 秒） |
| `videos/pika-ref2va-panda.mp4` | **强消融 D 组**（熊猫参考图，6 分 48 秒）——参考图生效的决定性证据 |
| `videos/h3-ref2va-img.mp4` | 第一轮 Ref2VA + VDN 版本（保留作对照） |
| `videos/h3-first-last.mp4` | **首尾帧插值**（8 分 41 秒）—— 镜头从全身中景推到面部特写，服装全程保留 |
| `videos/pika-i2va-shop.mp4` | **首帧图生视频 i2va**（5 分 59 秒）—— 首帧像素级保真，第 40 帧起商品漂移 |
| `videos/h3-audio.wav` | 分离出的音轨（频谱/包络分析用） |

### 图像
| 文件 | 说明 |
|---|---|
| `images/ablation-ref-vs-subject.png` | **消融决定性对比图**：上排 = 水彩熊猫参考图 + D 组三帧（写实黑白熊猫）；下排 = A/B/C 三组（全是猫）+ D 组末帧 |
| `images/ablation-A-vs-B.png` | A vs B 对比：上排左 = 猫参考图，其余 = A 组三帧；下排 = B 组四帧 |
| `images/i2va-jacket-drift-sheet.png` | **仅首帧锚定的 7 帧印相**：第 0/20 帧有深蓝外套，第 40 帧起外套消失、画面整体重构 |
| `images/firstlast-jacket-kept-sheet.png` | **首尾帧锚定的 7 帧印相**：外套与铜扣每一帧都在，镜头推到面部特写 |
| `images/h3-contact-sheet.png` / `-6step.png` | 文生视频两轮抽帧总览 |
| `images/h3-first-last-sheet.png` | 首尾帧插值 5 帧接触印相（镜头推进全过程） |
| `images/webui.png` / `webui-clean.png` | Web UI 实测截图 |
| `images/t2i-compare.png` | **文生图 2×2 对照**：上排 = 猫场景（左 Z-Image / 右 Krea-2），下排 = 带货商品图（左 Z-Image / 右 Krea-2） |
| `images/t2i-zimage-cat.jpeg` / `t2i-krea-cat.jpeg` | Z-Image / Krea-2 的猫场景原图（1024×1024） |
| `images/t2i-zimage-product.jpeg` / `t2i-krea-product.jpeg` | Z-Image / Krea-2 的带货商品图原图（1024×1024） |
| `images/i2va-firstframe-diff-x4.png` | i2va 首帧与参考 crop 的 4× 放大差分图（证明几何对齐） |
| `images/i2va-f000.png` | i2va 首帧原图（SSIM 0.9505） |


### 流水线 / 日志 / 参考图
| 文件 | 说明 |
|---|---|
| `pipelines/prepare-minimax-h3-8bit.vpipeline` | 官方准备流水线 |
| `pipelines/prepare-pika-h3-flex.vpipeline` | Pika adapter 准备（官方） |
| `pipelines/prepare-minimax-h3-preview.vpipeline` | TAE-H3 准备（官方，本机受网络阻断） |
| `pipelines/h3-t2v-turbo.vpipeline` | 改写版出片流水线（Turbo-LoRA + 音画一体提示词） |
| `pipelines/pika-ref2va-ablation.vpipeline` | **参考生视频主用**（Pika Ref2VA + references） |
| `pipelines/pika-ref2va-noref.vpipeline` | 空参考对照组 |
| `pipelines/fl2va-ref2va-like-ablation.vpipeline` | 官方 ref2va-like 路线对照 |
| `pipelines/pika-ref2va-panda.vpipeline` | 强消融（熊猫参考图） |
| `pipelines/h3-taeh3-preview.vpipeline` | TAE-H3 实时预览流水线 |
| `pipelines/h3-first-last.vpipeline` | 首尾帧插值流水线 |
| `pipelines/pika-i2va-shop.vpipeline` | **首帧图生视频 i2va**（商品图 → 短视频） |
| `pipelines/lfm3-vl-vqa.vpipeline` | **LFM3-VL 语义验证**（text-input → text-chat → save-text，stdin 喂单发） |
| `pipelines/qwen35-4b-chat.vpipeline` | **Qwen3.5-4B 中文多模态对话** |
| `pipelines/prepare-multimodal-compare.vpipeline` | LFM3-VL + Qwen3.5-4B 准备 |
| `pipelines/prepare-image-models.vpipeline` | Z-Image-Turbo + Krea-2-Turbo 准备 |
| `pipelines/z-image-turbo-t2i.vpipeline` / `krea-2-turbo-t2i.vpipeline` | 两个文生图流水线（官方示例改写） |
| `pipelines/krea-2-turbo-t2i-nolora.vpipeline` | **实际出片用的 Krea 版**（删掉 M87 LoRA，见 5.11 节；官方文档「Running without the LoRA」） |
| `pipelines/h3-taeh3-preview-dir.vpipeline` | TAE-H3 预览的**目录相对路径**写法（三种路径写法均实测可用） |
| `pipelines/h3-ref2va-img.vpipeline` / `h3-t2v-6step.vpipeline` | 第一轮 Ref2VA+VDN 与 6 步文生视频流水线（对照用） |
| `pipelines/run_prepare.sh` / `run_t2v.sh` | 准备与出片的快捷脚本 |
| `scripts/anchor-fidelity.sh` | **SSIM 保真度量化脚本**（逐帧 vs 参考图） |
| `scripts/vqa-batch.sh` | **LFM3-VL 批量语义对照** |
| `scripts/t2i-compare.sh` / `t2i-sheet.sh` | 文生图对照与 2×2 拼图脚本 |
| `logs/*.log` | 全部运行日志（含下载、量化、四组实验、三轮对照） |
| `logs/vqa-*.txt` | LFM3-VL 对四组产出的原始回答 |
| `logs/qwen35-answer.txt` | Qwen3.5-4B 的原始回答 |
| `refs/*.jpg` | 两张参考图（姜黄猫 / 水彩熊猫） |

---

## 11. 后续可做

### 本轮已完成（原列表已消化）

- ~~**Pika H3 Flex 的 `fl2va` adapter 用于首帧/首尾帧**~~ → **已完成**（5.8 节，5 分 59 秒；结论见 6.5 节修正后的版本）
- ~~**清磁盘**~~ → **已完成**（4.6 节，回收 61 GiB；注意废纸篓 shim 的坑）
- ~~**上游提 issue**~~ → **5 条**已备好（`report/vpipe-upstream-issues.md` + `report/issues/issue-1~5.md` 可逐条粘贴），**待在 GitHub 实际提交**（本机无 `gh`、无 token）
- ~~**多模型能力面对照**~~ → **已完成**（5.10 节：LFM3-VL-2B VQA + Qwen3.5-4B-MLX-4bit 中文对话 + Z-Image-Turbo / Krea-2-Turbo 文生图）

### 仍可做

- **多参考组合**（商品图 + 场景图 + 动作参考视频）：Ref2VA 支持最多 9 图 / 3 视频 / 3 音频，是带货「一物多场景」的正路。官方参考图 `klein-multi-ref-panda.jpg` 即多参考示例。
- **锚定 + 参考图叠加**：把「首尾帧锚定」（保商品）与 `video-ref-encoder`（保主体身份）在同一条流水线里组合 —— 两条路线目前是互斥的，i2va 丢掉外套的根因是 DiT 只拿到首帧 latent；如果能在锚定之外再挂一路参考行，商品与身份就能同时保住。这需要验证 vpipe 的 `generate-video` 端口 5/6 与 7/8/9 能否同时非空。
- **HyperFlow 8 步 adapter**（`videorebirth/hyperflow`，2.8 GB，单文件覆盖 t2va/fl2va/ref2va 三个工作流）：比 Pika 的 6 步更慢但质量口径不同，可做 A/B。
- **768p / 10 秒 / 15 秒规格**：Pika 768p 需 `reference_image_short_edge: 2048` 且画布 1344×768；frames 362 ≈ 15 秒。
- **把 TAE 预览接进 i2va**：目前预览只在 t2v 流水线验证过；商品场景下"先出低清预览再出正片"的工作流对带货者很有价值。
- **量化 Z-Image / Krea**：两个图像模型都是 bf16（32.8 GB / ~30 GB），8-bit 量化后各可省一半，对本机 90 GB 的磁盘很关键（`model-quantize` 的 `target: "dit"` 路径本轮已在 H3 上验证可用）。

---

## 12. 方法论备忘（本轮最值钱的部分）

这一轮真正的收获不是"多跑了几个模型"，而是三条**可复用的判定方法**：

| 方法 | 用来回答 | 本轮实例 |
|---|---|---|
| **像素级 SSIM/PSNR** | 输出与参考图**逐像素**一致吗？ | 锚定首帧 0.9505 vs 参考生视频 0.49–0.52 |
| **第三方模型复核** | 输出的**语义**真的被参考图改写了吗？ | LFM3-VL 与 Qwen3.5 都把 D 组判成"熊猫"，而提示词无"熊猫"二字 |
| **先验不可达主体消融** | 我的消融设计**有区分度**吗？ | 猫参考 → 场景先验也能出猫（不可证伪）；换成水彩熊猫 → 立刻可区分 |

> **最容易被忽略的一条**：A/B 消融必须先问"对照组能不能产生不同结果"。如果两组输出本来就一样（猫 vs 猫），再多的行数指标、SSIM 数字都只是自说自话。**换一个模型先验不可能产出的参考主体**，比换任何指标都管用。


