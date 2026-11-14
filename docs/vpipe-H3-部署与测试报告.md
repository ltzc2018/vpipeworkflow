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
| **图生图（Boogu-Image-0.1-Edit-Turbo）** | 官方 bf16（10B，4 步 DMD） | ✅ **支持多参考** | **17.6–32.6 秒** | 1024×1024，参考图走 Qwen3-VL 语义条件 |
| **参考生视频（HyperFlow 8 步 flow-map）** | Ref2VA-8bit + HyperFlow adapter | ✅ | 8 分 54 秒 | 832×480 / 124 帧 / 5.18 s + AAC |

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



---

## 13. 第四轮：Boogu 图生图链路 + HyperFlow 8 步 flow-map 对照

> 日期 2026-11-14 16:20–16:45 · 承接 `vpipe-后续计划任务.md` 的 **P7.1** 与 **P2**

### 13.1 本轮做了什么

| # | 事项 | 结果 |
|---|---|---|
| 1 | 下载并注册 **Boogu-Image-0.1-Edit-Turbo** | 35.8 GB / 30 个文件全部 sha256 通过 |
| 2 | 搭出 **Boogu 图生图**流水线 | **32.6 秒**出 1024×1024 |
| 3 | **双参考图**同框探针 | 跑通，每张参考图 144 个视觉 token |
| 4 | 真人商业写真参考图实测 | 3 组（影棚 / 海滩 / 单人裁切） |
| 5 | 注册 `videorebirth/hyperflow-ref2va` 别名 | 成功（`model-register` + `model_type: minimax-h3-lora`） |
| 6 | **HyperFlow A/B/C 三组对照** | Pika 6 步 vs HyperFlow 8 步 vs `lora_scale: 0` |

### 13.2 Boogu 的机制：参考图走 VLM，不走 latent

这是它与 klein / Qwen-Image-Edit **最根本**的差别：

| | FLUX.2-klein-9B | Qwen-Image-Edit-2511 | **Boogu-Image-0.1-Edit-Turbo** |
|---|---|---|---|
| 参考图进入方式 | **latent**（`vae-encode` → 端口 5/6） | VLM + latent 双路 | **只有 VLM** |
| 条件器 | CLIP/T5 | Qwen2.5-VL | **Qwen3-VL（`mllm/`，16 GB）** |
| 步数 | 4 步 | 20 步 | **4 步 DMD 蒸馏** |
| CFG | — | 需 negative prompt | **CFG = 1（关闭）** |
| 调度器 | simple / karras | simple | **`boogu_v1`**（sigma 约定是反的） |
| 多参考 | 端口 5/6 | `ref_image` + `ref_image2` | **`ref_image` + `ref_image2`（实测通过）** |

**源码依据**：`generative-models/boogu/metal-boogu-transformer.cc` 里 grep 不到任何
`ref_latent`；`stages/diffusion-conditioner-stage.cc:3506` 的 Boogu 分支只用
Qwen3-VL 的视觉塔把参考图拼进文本序列（`kBooguTi2i` 模板）。

**接线时最容易错的三点**（照抄 klein 的接线会静默出错）：

1. **必须接 `boogu-image-model-config`**，而且**同时**接到 `diffusion-conditioner` 的
   iport5 **和** `generate-image` 的 iport7 —— 前者给 VLM 的 `vl_*` 边界，后者让 DiT
   认出家族（少接会打印 `the model_config beat is for the 'boogu-image' family but ...`）。
2. **调度器必须 `type: "boogu_v1"`** —— Boogu 的 sigma 是**反的**（0 = 噪声，1 = 干净），
   用默认 `simple` 会往反方向采样。
3. **不需要 `vae-encode`**，**不要接 negative prompt**、**不要设 `guidance_scale > 1`**
   （Turbo 蒸馏版固定 CFG = 1，接了会白跑第二次 DiT 前向）。

### 13.3 五组实测

| # | 参考图 | 输出 | 耗时 | 结果 |
|---|---|---|---|---|
| 1 | 橘猫 + 牛仔衬衫 | 1024×1024 | **32.6 s** | ✅ 身份/虎斑纹/绿眼/深蓝衬衫铜扣全保留，背景换成霓虹雨夜巷 |
| 2 | 商业写真（竖版） | 576×1024 | **25.7 s** | ✅ 同一人物、深蓝白拼上衣 + 深蓝百褶裙 + 圆形金扣保留，背景换成浅灰影棚 |
| 3 | **两栏拼图**写真 | 576×1024 | 19.0 s | ⚠️ 服装保留但**脸与体型漂移** |
| 4 | 上图**裁出的单人** | 384×1024 | **17.6 s** | ✅ 姿态、粉色比基尼（含白滚边）、**粉色口罩**、亮片高跟鞋全保留，背景换成金色海滩 |
| 5 | 猫 + 熊猫（**两张**） | 1024×1024 | **26.1 s** | ✅ 两种动物同框，各自毛色花纹保留 |

第 5 组的日志证据：
```
DiffusionConditionerStage('diffusion-conditioner'): reference 0 -> 144 vision tokens (grid 24x24), 3 deepstack
DiffusionConditionerStage('diffusion-conditioner'): reference 1 -> 144 vision tokens (grid 24x24), 3 deepstack
```

**内存画像**（24 GB 机器，声明峰值超过物理内存但实测跑完）：
```
memory-plan (generate-image): peak 23933 MB at 'vae-decode' streaming
GenerateImageStage: freeing the Boogu-Image DiT for the 1024x1024 vae-decode (~3712 MB)
```
即 **DiT 与 VAE 从不同时驻留** —— 这是 vpipe 的 memory-bounded 设计。

**踩到的坑**：`load-image` 的 oport 是 `FlexDataPayload`，而 `ref_image` 要
`TensorBeatPayload`，直连会报
`payload type mismatch ... producer FlexDataPayload vs consumer TensorBeatPayload`。
**每张参考图必须各接一个 `image-resample`。**

### 13.4 最重要的教训：参考图必须先裁成「单一主体」

第 3 组与第 4 组用的是**同一张照片**，一张是整张拼图、一张是预先裁出的单人，
**结果差距是数量级的**：

| | 整张拼图（1440×2560，两栏） | 预裁单人（520×2400） |
|---|---|---|
| 服装 | ✅ 粉色比基尼 | ✅ 粉色比基尼 + 白色滚边 |
| 姿态 | ❌ 变成正面站立 | ✅ 侧身、双手抱拳于胸前 |
| 配件 | ❌ 丢失 | ✅ **粉色口罩**、亮片高跟鞋 |
| 脸 / 体型 | ❌ 明显「美颜化」 | ⚠️ 仍轻微漂移 |

**原因**：VLM 看到的是**两栏拼图**，于是把两个主体理解成「一个人 + 场景」，
输出时必然在两者之间折中并重画体态。

**仍然存在的漂移**：Boogu 会「美化」人像 —— 脸型偏模型审美、体型更纤细、
肤色偏亮、发色从深黑漂到浅棕。**服装颜色/款式/配件/姿态可靠，面部身份不可靠。**
需要脸完全一致时，请走 `vpipe-first-frame-to-video` 的首帧锚定（SSIM 0.9505）。

### 13.5 HyperFlow 8 步 flow-map 对照

**别名注册**（`model_type` 显式指定，绕开上游 detector 的签名表缺口）：

```
[INFO] ModelRegisterStage('register'): registered 'videorebirth/hyperflow-ref2va'
  -> '/Users/minichen/AI-Models/vpipe-workspace/models/videorebirth/hyperflow'
  [minimax-h3-lora, by config-key]
```

**运行时确认**（同一个权重文件覆盖三个 partition）：
```
MetalMiniMaxH3Transformer: ... is a FLOW-MAP adapter (HyperFlow 1.0):
  two-time timestep embedding, gate 0.25, 8-step grid, trained at shifts 12/3
MetalMiniMaxH3Transformer: runtime LoRA ... -- 212 modules at scale 1,
  rank <= 768 (diffusers decomposition, qkv fused HERE for this DiT's flat grouping, 52 of 52 banded)
GenerateVideoStage: HyperFlow 1.0 on lora slot 0 -- 8-step flow-map grid from the adapter
  (`steps: 8` is not used while it is live), two-time embedding at gate 0.25
```

**三组对照**（同一提示词、同一参考图 `klein-multi-ref-panda.jpg`、同 seed 42、832×480 / 124 帧）：

| 组 | 配置 | 前向次数 | AdaLN 行数 | 条件行数 | 耗时 | 全片 SSIM vs 参考图 |
|---|---|---|---|---|---|---|
| **A** | Pika-H3-Flex-ref2va，6 步 RE-NOISED | 6 | 17 | 16999 | **6 分 48 秒** | **0.4896** |
| **B** | HyperFlow 8 步 flow-map（scale 1.0） | 8 | **24** | 16999 | **8 分 54 秒** | **0.4433** |
| **C** | HyperFlow 8 步 flow-map，**`lora_scale: 0`** | 8 | **23** | 16999 | **8 分 23 秒** | **0.4810** |

**关键观察**

1. **三组的条件行数完全相同（16999）** —— 同一提示词 + 同一参考图，
   说明这是**干净的 A/B/C**，变量只有 adapter 与采样网格。
2. **AdaLN 烘焙行数不同**：Pika 6 步 = 17 行，HyperFlow 8 步 = 24 行；
   `lora_scale: 0` 时变成 **23 行** —— 差 1 行，说明 scale=0 时
   有一类行（参考/条件行，文档里 `r == t` 的那种）不再需要双时间嵌入。
3. **C 组是整个实验里最有说服力的一组**：
   **C（0.4810）明显更靠近 A（0.4896），而不是 B（0.4433）**。
   这正是「`lora_scale: 0` 精确回到原始模型」的直接证据 ——
   把 adapter 的 delta 归零，输出就回到原始模型的行为（只是仍在 HyperFlow 的 8 步网格上）。
   于是实验被**干净地拆成两个因子**：

   | 因子 | 对照 | SSIM 差 | 结论 |
   |---|---|---|---|
   | **adapter delta** | B vs C | 0.4433 ↔ 0.4810 | delta 把输出推离参考图 |
   | **采样网格** | A vs C | 0.4896 ↔ 0.4810 | 只换网格影响小得多 |

4. **SSIM 偏低不等于画质差** —— 前几轮已经证明「参考生视频里，
   参考图不是把输出往参考图拉，而是改写主体本身」（有参考 0.5120 < 无参考对照 0.5718）。
   SSIM 在这条链路上测的是「输出有多像参考图」，**不是**画质指标。
5. **目视对照**（`frames-hf/compare-abc.png`，第 40 帧三联）：
   A（Pika）整只熊猫入镜、略柔；B（HyperFlow）毛发、窗框木纹、叶片更锐利；
   C（scale 0）与 B 构图几乎一致（同一 seed + 同一 8 步网格），但细节明显更柔。
   **画面上 C 也更靠近 A。**

**结论**

| 维度 | Pika 6 步 | HyperFlow 8 步 |
|---|---|---|
| 耗时 | **快 27%**（6 分 48 秒 vs 8 分 54 秒） | 慢 |
| 前向次数 | 6 | 8 |
| 画质目视 | 略柔 | **更锐** |
| 步数自由度 | 图里的 `steps` 生效 | **适配器接管，`steps` 被忽略** |
| 官方定位 | 「few-step renoise」 | 「8 次前向完成原始模型要 15 步以上的片段」 |

**取舍**：短片（≤5 秒）优先 Pika（省 2 分钟）；追求画质或要跑长片段，
HyperFlow 的 8 次前向比原始模型 15 步更划算。

### 13.6 本轮新增资产

| 类型 | 文件 |
|---|---|
| 流水线 | `boogu-image-edit.vpipeline`、`boogu-multi-ref-probe.vpipeline`、`boogu-real-photo{1-studio,3-beach,3-single-beach}.vpipeline`、`register-hyperflow-ref2va.vpipeline`、`hyperflow-ref2va-panda.vpipeline`、`hyperflow-ref2va-scale0.vpipeline` |
| 产物 | `boogu-edit-cat.jpeg`、`boogu-real-photo1-studio.jpeg`、`boogu-real-photo3-beach.jpeg`、`boogu-real-photo3-single-beach.jpeg`、`boogu-multi-ref-probe.jpeg`、`hyperflow-ref2va-panda.mp4`、`hyperflow-ref2va-scale0.mp4` |
| 对照图 | `frames-hf/compare-ab.png`（Pika vs HyperFlow 四帧对照）、`frames-hf/compare-abc.png`（三组三联） |
| 技能包 | `vpipe-image-edit` 新增 `references/boogu-edit.md`（完整实测报告）+ 2 个资产 |
| 文档 | `vpipe-后续计划任务.md` 加状态看板；本节 |

### 13.7 第三方模型复核（LFM3-VL-2B，独立于生成链路）

| 问题 | LFM3-VL 的回答（节选） | 判定 |
|---|---|---|
| Boogu 换背景后服装是否与参考图一致？ | "在参考图中，人物穿着白色上衣和深蓝色裙子… 经过图生图编辑后，服装和参考图**基本一致**" | ✅ |
| 预裁单人参考图后，姿态与配件是否保留？ | "人物穿着**粉色连体泳衣**，带白色装饰线条… 姿态在两张图中都保持一致，侧身站立，双手抬起靠近胸部" | ✅ |
| 双参考图是否都生效？ | "结果中出现了猫和熊猫。猫的外观（橙色毛色、白色花纹、**穿蓝色衬衫**）与第一张参考图一致；熊猫的外观（黑白毛色、吃竹子）与第二张参考图一致" | ✅ **多参考得到独立复核** |
| Pika 与 HyperFlow 语义是否一致？ | 两组回答几乎相同："一只熊猫…坐在窗台上，背景是自然景观，光线温暖柔和" | ✅ 一致 |

> ⚠️ **真人照片只在本机测试**：GitHub 仓库 `ltzc2018/vpipeworkflow` 是 **public**，
> **不得**把 `refs-real/` 下的真人照片推上去。

---

### 13.8 P4：TAE-H3 实时预览接进 i2va 首帧锚定链路

> 日期 2026-11-14 17:05–17:30 · 承接 `vpipe-后续计划任务.md` 的 **P4**
> 问题：**首帧锚定模式下，实时预览还能正常工作吗？「先出低清预览再出正片」这条
> 带货工作流在 i2va 链路上到底成不成立？**

#### 13.8.1 三次实测

| 流水线 | 规格 | 成片耗时 | 预览流 | 有效预览延迟 |
|---|---|---|---|---|
| `pika-i2va-preview-fast` | 512×288 / 39 帧 / 6 步 / seed 42 | **64.3 s** | 10.6 MB | **22.11 s**（34% 处）|
| `pika-t2v-preview-fast`（对照）| 512×288 / 39 帧 / 6 步 / seed 42 | **58.7 s** | 9.5 MB | **20.26 s**（35% 处）|
| `pika-i2va-preview-prod` | 832×480 / 124 帧 / 6 步 / seed 42 | **374.3 s** | 71.3 MB | **90.33 s**（24% 处）|

**接线**（相对已验证的 `pika-i2va-shop.vpipeline` 只多了预览三件套）：

```json
"minimax-h3-model-config": { "preview_vae": ".../taeh3.safetensors",
                             "preview_every": 1, "preview_max_edge": 512,
                             "preview_frames": 39 }
"preview": { "iports": [ {"src": "generate-video", "oport": 2} ] }
```

**结论一：可行，而且预览是「白拿」的。** 生产规格下 **1 分 30 秒就出低清预览**，
最终成片 6 分 14 秒——**总时间的 24% 处就已经能判断结果好不好**，省下的 4 分多钟
用来调参重跑，是这套工作流最大的价值。

**结论二：i2va 的预览延迟只比 t2v 多 1.85 秒**（22.11 s vs 20.26 s），
这 1.85 秒是首帧锚定多出来的 `vae-encode`。**锚定没有给预览链路带来任何降级。**

#### 13.8.2 预览流的真实结构（踩到的第一个坑）

预览流**不是**一段连续的视频，而是 **两个 init 段拼起来的 fMP4**：

| 分段 | 触发时刻 | 分辨率 | 时长 | 码率 | 内容 |
|---|---|---|---|---|---|
| segment-1 | launch + 1.76 s | 640×360 | 20.24 s | **8 kb/s** | **纯黑占位** |
| segment-2 | launch + 22.11 s | **512×288** | 41.79 s | 2011 kb/s | 真实内容 |

源码依据（`stages/audio-video/preview-stage.cc`）：

- `handle_video_frame_`：第一个真实帧到达时**采纳它的原生分辨率**，与「预输入黑画面」
  的尺寸不同就 `build_pipeline_(W, H)` **重新初始化 fMP4** → 推第二个 init 段。
- `handle_clip_`：`each new clip replaces it` —— 每个去噪步的 clip 替换上一个，
  然后从头循环播放。

**坑**：把两个 init 段的内容拼进同一个 mp4 会让 ffmpeg 用第一段的 SPS 去解第二段，
满屏 `error while decoding MB`，**前 20 秒全是坏帧**。必须**按到达顺序分段拼装**
（`scripts/ws_capture.py` 的 `segments` 逻辑），再用 `scripts/split_preview.py`
按 init 边界切开分析。

**附带结论**：segment-1 那 20 秒不是「预览失效」，是**黑画面占位**。
判据是码率——8 kb/s 的 640×360 只能是纯色。所以
**「第一个 fragment 到达（2.24 s）」不等于「能看见画面（22.11 s）」**。

#### 13.8.3 量化结果

**（a）切步：预览的每一拍 = 一个去噪步**

预览把同一个 39 帧 clip 循环播放。**同相位帧（n 与 n-39）在一个拍内几乎逐像素相同**
（SSIM 0.978），跨拍骤降。据此切分，三次运行**都精确切出 6 个 beat = 6 个去噪步**：

| | i2va-fast | t2v-fast | i2va-prod |
|---|---|---|---|
| segment-2 总帧数 | 1003（25 个循环）| 903（23 个循环）| 6807（54 个循环）|
| 循环长度 | 39 帧 | 39 帧 | 124 帧 |
| 切出 beat 数 | **6** | **6** | **6** |

**（b）SSIM / PSNR 对照表**

统一口径：两张图都先缩放到 256×144 再比（prod 的预览 416×240 与成片 832×480
必须归一化，否则尺寸不匹配直接跳过）。

| 对照 | i2va-fast | t2v-fast（对照）| i2va-prod |
|---|---|---|---|
| 成片首帧 vs 锚定图 | **0.9736**（35.95 dB）| 0.4293（10.41 dB）| **0.9361**（30.38 dB）|
| 预览第 1 帧 vs 锚定图 | **0.6102**（16.01 dB）| **0.1219**（6.92 dB）| **0.8872**（27.32 dB）|
| **预览最后一拍 vs 成片（相位对齐）** | **0.9338** | **0.9460** | **0.9663** |
| 　└ 首 / 中 / 末帧 | 0.9357 / 0.9427 / 0.9373 | 0.9455 / 0.9485 / 0.9439 | 0.9560 / 0.9694 / 0.9687 |

**（c）锚定涌现曲线 —— 本轮最有价值的发现**

在每一拍内定位「相位 0 帧」（= clip 的第 0 帧 = 视频首帧的位置），
量它与**成片首帧**的 SSIM，得到锚定主体在预览里的**逐步收敛曲线**：

| 步骤 | i2va-fast（有锚定）| t2v-fast（无锚定对照）| i2va-prod（有锚定）|
|---|---|---|---|
| step1 | **0.9534** | **0.7085** | **0.9796** |
| step2 | 0.9563 | 0.7099 | 0.9801 |
| step3 | 0.9590 | **0.9238** | 0.9810 |
| step4 | 0.9610 | 0.9552 | 0.9818 |
| step5 | 0.9636 | 0.9675 | 0.9826 |
| step6 | 0.9640 | 0.9678 | 0.9826 |

**这就是首帧锚定价值的量化形态**：

- **有锚定**：第 1 步的首帧就已经正确（0.9534），后面 5 步只是把细节磨清楚。
- **无锚定**：第 1–2 步的首帧还在漂移（0.7085 / 0.7099），**到第 3 步才收敛**
  （0.9238）。也就是说，没有锚定时，前两步的首帧是**不可信的**。

带货场景直接对应：商品图锚定后，**第 1 步的预览就能判断商品有没有跑偏**，
而不锚定时至少要看第 3 步——省下的正是最贵的那几步。

**（d）第三方模型复核（LFM3-VL-2B，独立于生成链路）**

| 问题 | i2va-fast | t2v-fast（对照）|
|---|---|---|
| 主体每一步都在场吗？ | "主体在每一步都在场" ✅ | "主体在每一步都在场" ✅ |
| 服装每一步都保留吗？ | "一件蓝色牛仔外套，**在每一步都保留**" ✅ | "服装**并未在每一步都保留**" ⚠️ |
| 清晰度逐步提升吗？ | "从左到右逐步提升" ✅ | "从左到右逐步提升" ✅ |
| 预览首帧是参考图那只猫吗？ | "**是同一只猫**，服装、外观、姿态都与参考图一致" ✅ | "是**另一只猫**，服装、外观、姿态与参考图**不一致**" ✅ 反证成立 |
| 预览能代表正片吗？ | "同一个场景、同一动作"，丢失的是毛发纹理与缝线等细节 | 同上 |

#### 13.8.4 结论与适用边界

1. **i2va 链路接 TAE 实时预览完全可行**，接线只需在 `minimax-h3-model-config`
   上加 4 个键、把 `preview` 接到 `generate-video` 的 **oport 2**。
2. **首帧锚定在预览路径上成立**，且**第 1 步就锁死**（SSIM 0.9534 vs 无锚定 0.7085）。
3. **预览最后一拍与正片高度一致**（逐帧 SSIM 0.93–0.97），
   **足以判断构图、主体、运动方向和锚定是否生效**。
4. **但预览不能判断细节保真度**（TAE 只有 9.9M 参数）：预览与锚定图的 SSIM 只有
   0.61–0.89，vs 成片的 0.94–0.97。**要验细节保真仍然只能看成片。**
5. **不同拍之间相位不对齐**。预览是「同一个 clip 循环播放」，每一拍被替换时相位
   会漂移，所以**横向比较各拍必须先做相位对齐**，否则会得出「预览与成片不像」
   的错误结论（未对齐时 SSIM 只有 0.13–0.31，对齐后 0.93–0.97）。
6. **预览是 Web UI 功能**。`preview` 是 WebSocket sink（0 oports），CLI 下流水线
   不会自己结束。本轮用 `vpipe-web-ui --bind 127.0.0.1 --port 9876` + 自写
   RFC6455 客户端抓流（`scripts/ws_capture.py`），全程免密钥。

#### 13.8.5 本节新增的坑清单

| # | 坑 | 后果 | 解法 |
|---|---|---|---|
| 1 | 预览流有**两个 init 段**（分辨率重初始化）| **把两段拼进一个 mp4 = 全片花屏**（不是只有前 20 秒）| 按段切开 + 每段各自重封装（详见 13.8.7）|
| 2 | 「第一个 fragment 到达」≠「能看见画面」| 把 2.24 s 误报成预览延迟 | 以**分辨率被采纳的时刻**为准（22.11 s）|
| 3 | 各拍**相位不对齐** | 误判「预览与成片不像」| 用 `SSIM(n, n-39)` 切步 + 相位对齐 |
| 4 | `ffmpeg -i a.png … a.png` | **输入输出同路径会先截断输入**，比较到坏图 | 输出必须换文件名（曾使曲线整体偏低 0.09）|
| 5 | `select='eq(n,1)+eq(n,2)+…'` 拼上百个 OR 项 | `Cannot allocate memory` | 用单表达式 `not(mod(n,39))` / `between(n,A,B)` |
| 6 | 每抽一帧都整段解码 | 71 MB 的 prod 流抽 124 帧要 124 次全量解码 | 一次解码批量抽帧 |
| 7 | 单帧 SSIM argmax 选相位 | 画面同质时全部候选都在 0.93 上下，**必错** | 用双端点准则 + 目检裁决 |
| 8 | runner 猜的成片文件名与流水线 `output_url` 不一致 | 白等 15 分钟超时 | 从流水线 JSON 里读 `output_url` |

#### 13.8.6 本节新增资产

| 类型 | 文件 |
|---|---|
| 流水线 | `pika-i2va-preview-fast.vpipeline`、`pika-t2v-preview-fast.vpipeline`、`pika-i2va-preview-prod.vpipeline` |
| 脚本 | `scripts/p4_run.py`（web-ui 编排 + 增量日志）、`scripts/ws_capture.py`（RFC6455 抓流 + 分段拼装）、`scripts/split_preview.py`、`scripts/p4_beats.py`（切步 + 相位对齐 + SSIM/PSNR）、`scripts/p4_anchor_emergence.py`、`scripts/vqa-p4.sh` |
| 成片 | `p4-i2va-preview-fast.mp4`、`p4-t2v-preview-fast.mp4`、`p4-i2va-preview-prod.mp4` |
| 预览流 | `p4-preview-stream-i2va-fast.mp4`（10.6 MB，Web UI 里看到的原始流）、`init-1.mp4` / `init-2.mp4`（两个 init 段留档）|
| 对照图 | `p4-{i2va-fast,t2v-fast,i2va-prod}-contact-sheet-anchor-emergence.png`（相位一致的逐拍收敛）|
| 日志 | `p4-pipeline-{tag}.log`（带时间戳的流水线日志）、`ws-capture.log`（分片时间线）、`p4-quant-{tag}.json`、`p4-emergence-{tag}.json` |

#### 13.8.7 交付物修正（2026-11-14）：预览流是一份畸形 MP4

用户看交付的 `p4-preview-stream-i2va-fast.mp4` 发现**视频生成有错误**。复查确认：
**不是内容生成错了，是容器坏了**——整片花屏。

##### 症状

```
$ ffmpeg -v error -i p4-preview-stream-i2va-fast.mp4 -f null -
[h264 @ 0x141e5a460] top block unavailable for requested intra mode
[h264 @ 0x141e5a460] error while decoding MB 32 0, bytestream 11979
[h264 @ 0x141e38aa0] cabac decode of qscale diff failed at 13 2
...（贯穿全片）
```

抽帧拼图里几乎全是噪点与竖条，只有中段残留一点轮廓。

##### 根因：文件里有两个 `moov`

写一个 box 解析器把文件结构摊开（`scripts/p4_mp4box.py`）：

```
[         0] ftyp   size=28
[        28] moov   size=739      ← moov#1  轨道 640×360
[       767] moof   size=152
[       919] mdat   size=553
...  39 个 moof/mdat ...
[     31551] ftyp   size=28       ← 第二个 ftyp
[     31579] moov   size=738      ← moov#2  轨道 512×288
...  84 个 moof/mdat ...
```

**MP4 规范里 `moov` 只能有一个。** 抓流脚本把
`init1 + frags1 + init2 + frags2` 顺序拼成单个 `.mp4`，于是文件里出现了两个
`moov`（中间还嵌了一个 `ftyp`）。解码器走到第二个 `moov` 会**重置参数集**
（SPS/PPS），后续 fragment 就用第一段的配置去解第二段的码流 —— 于是从第 1 帧
到最后一帧全是坏块。

> ⚠️ **这个坑本报告 13.8.5 第 1 条早就写了**（「把两个 init 段塞进同一个 mp4，
> ffmpeg 会用第一段的 SPS 去解第二段 → 满屏 error」），
> **但当时的切分只用在分析脚本里，交付的那份文件从没被切过。**
> **教训：诊断脚本切对了 ≠ 交付物是对的。交付前必须对交付文件本身做解码复检。**

##### 量化证据

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 解码错误行数 | **贯穿全片** | **0** |
| 时长 | 41.79 s（错的）| 62.04 s（= 段1 20.24 + 段2 41.79，真实总长）|
| 帧率 | 24.33 fps（容器不一致）| 24 fps 恒定 |
| 画面 | 全片花屏 | 清晰的橘猫，且随 denoise 由模糊变清晰 |
| segment-1 亮度 | — | **506/506 帧亮度 0.00（100% 纯黑占位）** |
| segment-2 亮度 | — | 1003 帧亮度 31.08 → 142.15（收敛曲线），近黑 0 帧 |

三个实验组的「双 init」是**系统性规律**，不是偶发：

| 实验 | segment-1 | segment-2 |
|---|---|---|
| i2va-fast | 640×360 / 39 moof / 20.24 s / 纯黑 | 512×288 / 84 moof / 41.79 s |
| t2v-fast | 640×360 / 35 moof / 18.16 s / 纯黑 | 512×288 / 76 moof / 37.63 s |
| i2va-prod | 640×360 / 170 moof / 88.36 s / 纯黑 | **416×240** / 568 moof / 283.63 s |

##### 修法

新增 `scripts/p4_fix_preview.py`，三步：

1. **按 box 结构切段**（直接解析 `moov` 出现的位置，比按日志字节数切更可靠）
2. **每段各自 ffmpeg 重封装**成合法 MP4（`<tag>-partN.mp4`）
3. **统一到第一段的画布后拼成单文件**（两段分辨率不同，`-c copy` 直拼不行）

抓流脚本 `scripts/ws_capture.py` 同步做了**源头修复**：不再拼畸形文件，
改为每段各写一个 `preview-stream-segN.fmp4`（无损源证据），再调用上面的修复器
产出可播的 `preview-stream.mp4`。

交付物已全部替换并复检：

| 文件 | 规格 | 解码错误 |
|---|---|---|
| `p4-preview-stream-i2va-fast.mp4` | 640×360 / 62.04 s | 0 |
| `p4-preview-stream-i2va-fast-part1.mp4` | 640×360 / 20.24 s（纯黑占位）| 0 |
| `p4-preview-stream-i2va-fast-part2.mp4` | 512×288 / 41.79 s（真实预览）| 0 |
| `p4-preview-stream-t2v-fast.mp4` | 640×360 / 55.79 s | 0 |
| `p4-preview-stream-i2va-prod.mp4` | 640×360 / 372.00 s | 0 |

##### 新增的两条坑

| # | 坑 | 后果 | 解法 |
|---|---|---|---|
| 9 | 诊断脚本把流切对了，**交付物没切** | 交付给用户的是花屏文件 | 交付前对**交付文件本身**跑 `ffmpeg -v error -i X -f null -` |
| 10 | 两段分辨率不同（640×360 vs 512×288）| `-c copy` 直拼会被 ffmpeg 拒绝 | 先 `scale` 到统一画布再 `concat` |

---

## 14. 第六轮：技能固化 + 仓库相对路径化 + GitHub 同步

> 日期 2026-11-14 19:03–19:20 · 承接第 13.8 节（P4）

### 14.1 这一轮做了什么

| # | 事项 | 结果 |
|---|---|---|
| 1 | 6 个 P4 脚本**参数化** | 硬编码路径 → 环境变量覆盖（`VPIPE_FFMPEG` / `VPIPE_WS` / `VPIPE_LAB` / `VPIPE_WEBUI` / `VPIPE_WEBUI_PORT`）|
| 2 | 参数化后**重跑验证** | 用既有 P4 产物复算，相位对齐 SSIM **0.9338**、成片首帧 **0.9736 / 35.95 dB**，与第 13.8 节**逐位一致** |
| 3 | 新增 `references/cli-capture.md` | CLI 下从起服务到量化的**端到端可执行手册** |
| 4 | 新增 `references/anchor-emergence.md` | 锚定涌现曲线（首帧锚定价值的量化形态）|
| 5 | 修正 SKILL.md 的 **preview 接线 oport** | 原文档写 `oport 0`，实测正确是 **`oport 2`** |
| 6 | 仓库 **19 条流水线路径相对化** | 本机绝对路径 → 相对工作目录，并**实测跑通** |
| 7 | 推送到 GitHub | `ltzc2018/vpipeworkflow`（public / main）|

### 14.2 相对路径化：让仓库真的能被别人跑起来

改造前，19 条流水线里有 **37 处**本机绝对路径（`/Users/minichen/...`）。
现在统一为：

```json
"url":         ["refs/minimax-h3-reference-subject.jpg"],
"preview_vae": "models/madebyollin/taehv",
"output_url":  "out/p4-i2va-preview-fast.mp4"
```

**验证方式**：把相对路径版流水线拷进工作区实跑，
日志确认 `refs/minimax-h3-reference-subject.jpg` 与
`models/madebyollin/taehv`（**目录写法**）都被正确解析，
成片正常落盘。

> 附带修掉一个隐蔽问题：**`preview_vae` 用目录写法时，
> 上游改权重文件名也不怕**（目录里自己找），
> 比硬编码 `taeh3.safetensors` 更耐上游变更。

**仓库现在自带 `refs/`**（猫 / 熊猫 / 官方示例图，4 张，共 576 KB），
克隆下来即可跑，不需要自备素材。

### 14.3 一条被文档掩盖的错误

`vpipe-live-preview/SKILL.md` 早期版本的「完整流水线」示例里写的是：

```json
{ "id": "preview", "type": "preview", "iports": [ {"src":"generate-video","oport":0} ] }
```

**这是错的。** 正确接法是 **`oport 2`**（预览通道）：

```json
{ "id": "preview", "type": "preview", "iports": [ {"src":"generate-video","oport":2} ] }
```

`oport 0` 是视频 latent、`oport 1` 是音频 latent —— 接错的表现是
**预览通道没有数据**，但**流水线本身不报错**（静默失效）。
第 13.8 节的实测流水线全部是 `oport 2`，之前只有文档写错。
本次已修正，并在 SKILL.md 里加了显式警告。

> 教训：**流水线 JSON 里的 `oport` 编号必须从跑通的实测文件反查，
> 不能从别的 stage 的文档示例照抄。**

### 14.4 技能包结构（本轮终态）

```
skills/
├── vpipe-text-to-image/          文生图（Z-Image / Krea-2）
├── vpipe-image-edit/             图生图（Boogu，含多参考）
│   └── references/boogu-edit.md  ← 完整实测报告
├── vpipe-reference-to-video/     参考生视频（Ref2VA + HyperFlow）
├── vpipe-first-frame-to-video/   首帧锚定（i2va）
│   └── references/anchor-emergence.md  ← 本轮新增
├── vpipe-first-last-to-video/    首尾帧插值
├── vpipe-live-preview/           实时预览 + CLI 抓流
│   ├── references/cli-capture.md ← 本轮新增
│   └── scripts/  p4_run / ws_capture / split_preview /
│                 p4_beats / p4_anchor_emergence / vqa-p4
└── vpipe-model-prepare/          模型准备（量化 / 注册 / 磁盘）
```

7/7 通过官方 `quick_validate.py`，全部安装到 `~/.workbuddy/skills/`。

### 14.5 仓库同步内容

| 目录 | 内容 | 体积 |
|---|---|---|
| `skills/` | 7 个技能包（含全部 references / assets / scripts）| 524 KB |
| `pipelines/` | 25 条流水线（路径已相对化）| 96 KB |
| `refs/` | 4 张参考图（猫 / 熊猫 / 官方示例）| 576 KB |
| `scripts/` | 保真度 / 预览抓流 / VQA / 拼图脚本 | 68 KB |
| `images/` | 32 张实测产物（印相、对照图、成片抽帧）| 22 MB |
| `videos/` | 18 支实测成片 + 预览原始流 | 29 MB |
| `logs/` | 全部流水线日志与第三方模型复核输出 | 1.7 MB |
| `docs/` | 主报告（1096 行）、后续计划、5 条上游 issue | 192 KB |

**刻意排除**：真人商业写真的原图、衍生图、视频与日志
（`boogu-real-*`、`real-ref2va-*`、含 `refs-real/` 路径的 4 条流水线）。
仓库是 public 的，这类素材一律不上传。README 里写明了这条限制与复现方式。

### 14.6 下一个该做的

优先级不变：**P1（多参考组合的视频）→ P3（768p / 长规格）**。
P1 是 Ref2VA 唯一还没被充分使用的能力，也是带货「一物多场景」的正路。

P1 的关键前置（已在官方 `minimax-h3-reference-to-video.vpipeline` 里验证过端口路线）：
多参考图在 `diffusion-conditioner` 上占 **iport3 / iport4**，
视频参考要先过 `video-to-rgb → image-resample → temporal-stack`，
音频参考走 `audio-to-pcm(32000, stereo) → temporal-stack`。

> **2026-11-14 21:20 更新：P1 已在第 15 节完成**（4 组实测，端口路线位级等价于文件列表路线）。
> 下一个任务改为 **P3（768p / 长规格）**，前置是确认 `lightx2v` 在 ModelScope 可用。
## 15. 第七轮：P1 多参考组合（主体图 + 风格图 + 动作参考视频 + 音轨）

> 日期 2026-11-14 20:00–21:30 · 承接第 14 节 · 计划清单任务 **P1**（清单里优先级最高的一档）
> 模型：`local/MiniMax-H3-Ref2VA-8bit` + `Pika-Labs/Pika-H3-Flex-ref2va`（6 步 renoise）
> 规格：832×480 / 124 帧 / 24 fps / **seed 42** / `i8_gemm: true`
> 路线：**官方端口路线**（不是文件列表路线）

### 15.1 这一轮做了什么

把清单里排在最前面的 **P1 多参考组合** 跑通了。官方规格是单次最多
**9 图 + 3 视频 + 3 音频 = 12 项**，单段参考视频 2–15 秒，总时长 ≤ 15 秒。

四组的**唯一变量是「喂了几条参考、分别是什么角色」**——模型、采样参数、seed、提示词骨架全部固定：

| 组 | 参考构成（按编码器槽位） | 提示词里的角色声明 |
|---|---|---|
| **A** | ① 主体图（写实橘猫） | `@Image1 is the subject sheet` |
| **B** | ① 主体图（橘猫）② 风格图（水彩熊猫） | `+ @Image2 is the style reference` |
| **C** | ① 主体图 ② 风格图 ③ 动作视频（+其音轨折叠成同一条） | `+ @Video1 is the motion reference` |
| **D** | ① 主体图 ② 风格图 ③ 风格图特写裁剪 ④ 动作视频（+音轨） | `+ @Image3 是同一张画的另一个视角` |

**动作参考视频是专门造的。** 官方文档给的动作参考就是一段普通视频，"镜头在动"无法量化。
本轮用 ffmpeg 在已有的跟踪镜头素材上开一个 480×276 的窗口匀速横扫，得到一条
**净横移 +334 px（256 宽尺度）的水平摇摄**——"运镜有没有被复现"于是从主观判断变成一个可测的数字。

### 15.2 端口路线怎么接：官方示例的四个承重细节

官方 `docs/pipelines/minimax-h3-reference-to-video.vpipeline` 的接法：

```
load-image → image-resample(1024×1024)                              → 编码器 iport2
load-video ┬→ video-to-rgb → image-resample(1344×768) → temporal-stack → 编码器 iport3
           └→ audio-to-pcm(32000, stereo) → temporal-stack             → 编码器 iport4
```

编码器 iport 分配：**0 = 提示词，1 = model-select，2–7 = 参考 1–6**。

本轮实测确认的四个承重细节：

1. **`attach_audio` 填的是「音频那条参考自己的槽位号」（1 起算）**，不是图也不是端口号。
   官方示例只有 3 条参考，两种读法数值恰好相同，**只有 ≥4 条参考时才会暴露歧义**。
   本轮 C 组 4 条参考时 `attach_audio: [4]` → 日志打出
   `reference 3 (video 124f 832x480 -> 124f 832x480): … audio VAE 207 latents`，
   **音视频被折叠成了同一条参考**（`3 reference(s)` 而不是 4），配对成功。
   D 组 5 条参考时 `attach_audio: [5]`，同样折叠成 4 条。

2. **`reference_video_short_edge: 0` = 让参考视频保持自己的画布**，不要用出厂的 768。
   官方文档原话：出厂值会把一条 960×544 的参考**上采样到 1344×768**，凭空多 1.98 倍像素；
   官方二参考示例实测 `768 → 0` 让**参考行 13120 → 7144**、**条件行 3115 → 2119**、**耗时 23m07s → 14m17s**。
   端口路线没有这个键，等价做法是**直接用 `image-resample` 把参考视频缩到输出画布尺寸**——本轮用的就是 832×480。

3. **`temporal-stack` 的 `max_mb`**：124 帧 @ 832×480 = 148.6 MiB；官方示例的 124 帧 @ 1344×768 = 366 MiB。
   默认 256 MiB 会把参考**截到 86 帧**并告警。本轮用 `max_mb: 384`。

4. **帧率与采样率必须活下来**：`video-to-rgb` 出来的张量带 `fps` sideband；
   音轨用 `audio-to-pcm` 的 `output_sample_rate: 32000` + `channels: 2`（音频 VAE 的采样率）。

另有一条**从二进制里挖出来、文档没强调**的规则：

> **没用的参考端口干脆不要接。** 一个"空"端口会**重编号后面的所有参考**，悄悄改变整个请求。

所以 A/B/C/D 是**四条独立的流水线**，不是一条加开关。

### 15.3 四组实测

| 组 | 参考构成 | 参考条数 | conditioning rows | reference video rows | reference audio rows | 前向行数 | 耗时 |
|---|---|---:|---:|---:|---:|---:|---:|
| A | 1 图 | 1 | 1131 | 1024 | 0 | 16999 | **6 分 48 秒** |
| B | 2 图 | 2 | 2181 | 2048 | 0 | 19073 | **8 分 01 秒** |
| C | 2 图 + 1 视频 + 1 音轨 | 3 | 4593 | 16478 | 414 | 36329 | **20 分 28 秒** |
| D | 3 图 + 1 视频 + 1 音轨 | 4 | 5636 | 17502 | 414 | 38396 | **19 分 35 秒** |

**参考条数少于喂进去的素材数**，因为视频和它的音轨被折叠成了一条参考。

**代价非常明确**：加一条参考视频，前向行数从 16999 涨到 36329（**2.14 倍**），
耗时从 6 分 48 秒涨到 20 分 28 秒（**3 倍**）。再加一张图只涨 6.5%（38396 行）——
**贵的不是"多一张图"，是"多一段视频"**。

### 15.4 量化证据

#### 15.4.1 端口路线 ≡ 文件列表路线（位级一致）

A 组（端口路线：1 图）与第二轮的历史基线 `pika-ref2va-ablation`（文件列表路线：1 图）
在**每一个可观测量上都完全相同**：

| 量 | 端口路线（A 组） | 文件列表路线（历史基线） |
|---|---|---|
| reference 1 编码 | `image 1f 1024x1024 → 1f 1024x1024`，resize 0 ms | 同 |
| presentation | 1131 tokens | 1131 tokens |
| 条件规模 | 1 reference → 1131 conditioning / 1024 reference video / 0 audio | 同 |
| 前向行数 | 16999 | 16999 |
| 耗时 | 6 m 48 s | 6 m 48 s |
| **成片逐帧像素** | — | — |

最后一行不是"接近"，是**逐帧完全一致**：
`SSIM All:1.000000 (inf)`、`PSNR average:inf`，74 280 960 字节的原始 yuv420p **逐字节相同**（`cmp` 无差异）。

**结论：端口路线是文件列表路线的严格超集，多参考组合不需要牺牲任何保真度。**
这一条同时反向验证了本轮所有对照的可信度——A 组就是历史基线本身。

#### 15.4.2 保真度与画面变化幅度

> 口径 A：**视频流直接与图片比**（ffmpeg `lavfi ssim/psnr`），SSIM 取 **All:** 聚合值，
> 与历史表格（`anchor-fidelity.sh`）同口径；YUV 4:2:0 色度往返损失计入，**组间可比**。
> （另一种口径"两张都先落盘 PNG 再比"会高约 0.03，本报告全程不用那种。）

| 组 | 帧数 | 全片平均 SSIM vs 主体参考图 | 首帧 / 中帧 / 末帧 | 全片平均 PSNR |
|---|---:|---|---|---:|
| A | 124 | **0.5120** | 0.5245 / 0.5093 / 0.5247 | 10.67 dB |
| B | 124 | 0.5030 | 0.5122 / 0.5005 / 0.5102 | 10.75 dB |
| C | 124 | 0.5495 | 0.5913 / 0.5445 / 0.5532 | 11.84 dB |
| D | 124 | 0.5459 | 0.5726 / 0.5452 / 0.5476 | 11.58 dB |

A 组的 0.5120 / 0.5245 与第二轮历史表格里的 "参考生视频（有参考）0.5245 / 0.5120" **完全对上**。

组间两两对比（全片，SSIM All / PSNR average）：

| 对比 | SSIM | PSNR |
|---|---|---|
| A(1 图) vs B(2 图)：加风格参考 | 0.6058 | 16.48 dB |
| A(1 图) vs C(2 图+视频+音轨) | 0.5885 | 13.90 dB |
| B(2 图) vs C(2 图+视频+音轨)：加动作参考 | 0.5818 | 14.13 dB |
| C(4 参) vs D(5 参)：再加一张图 | 0.6224 | 14.99 dB |

**加第二张图让画面变了 39%（SSIM 0.61），但方向不是"风格"。** 见 15.5 的第三方复核。

#### 15.4.3 运镜：动作参考有没有被复现

方法：相邻帧做 **FFT 交叉功率谱相位相关**（256×144 灰度），得到全局平移；
动作参考由 ffmpeg 精确构造，净横移已知，可直接当基准。

**符号约定已用一条反向构造的片子校验过**：`net_dx < 0` = 内容向**右**移动，`net_dx > 0` = 内容向**左**移动。

| 视频 | 全局横移 net dx (px @256 宽) | 全局纵移 net dy | 运动能量 mean | 与动作参考的能量曲线相关 r |
|---|---:|---:|---:|---:|
| 动作参考（构造的横移摇摄） | **+334.0** | -24.0 | 6.775 | — |
| A 组（1 图） | **+0.0** | -1.0 | 1.976 | 0.1546 |
| B 组（2 图） | **+1.0** | -19.0 | 1.629 | 0.2199 |
| C 组（2 图+视频+音轨） | **+160.0** | -11.0 | 8.117 | 0.0126 |
| D 组（3 图+视频+音轨） | **+208.0** | -12.0 | 8.029 | 0.1681 |

**C / D 组是唯一出现横移的组：+160 px / +208 px，是参考视频 +334 px 的 48% / 62%，方向一致（都向左）。**
A / B 组完全没有横移（0 / +1 px）。目检 C、D 组的 4 帧也能直接看出窗框相对画面的位置在持续移动。

但要注意一条**否定结论**：C 组与参考的**运动能量曲线相关只有 0.0126**（A 组 0.1546、B 组 0.2199 反而更高）。

> **被复现的是「镜头往哪个方向、移多快」，不是「每一刻的运动节奏」。**
> 能量曲线（逐帧运动量的时间分布）没有被搬运；全局平移这一项被搬运了。

#### 15.4.4 音频通道

方法：16 kHz 单声道 PCM → 32 个对数间隔频带的对数谱包络 → 与参考音轨做 Pearson 相关；
另给低频(<200 Hz)/中频/高频能量占比与谱质心。

| 视频 | RMS | 低频占比 | 中频 | 高频 | 谱质心 Hz | 谱形 vs 参考 r |
|---|---:|---:|---:|---:|---:|---:|
| 动作参考音轨（海浪+脚步） | 0.0081 | 0.251 | 0.672 | 0.076 | 715 | — |
| A 组（提示词：呼噜/风/鸟鸣） | 0.0020 | 0.241 | 0.036 | **0.723** | **2859** | -0.179 |
| B 组 | 0.0122 | 0.006 | 0.121 | **0.872** | **2220** | -0.442 |
| **C 组（带音轨参考）** | 0.0032 | **0.405** | **0.475** | **0.120** | **992** | **+0.710** |
| **D 组（带音轨参考）** | 0.0029 | **0.467** | 0.172 | 0.361 | **1459** | **+0.646** |

**C / D 组是唯一与参考音轨谱形正相关的组（r = +0.710 / +0.646），而且谱质心从 A 组的 2859 Hz
降到 992 / 1459 Hz，靠近参考的 715 Hz；高频占比从 0.723 压到 0.120 / 0.361。**
也就是说：**参考音轨不仅进了模型，还覆盖了提示词里写死的声景**（提示词要"鸟鸣"，高频大幅减少）。

### 15.5 LFM3-VL-2B 第三方复核

模型：`LiquidAI/LFM3-VL-2B`（独立于生成链路），四关键帧 + 参考图一起问。

**Q1 身份 + 风格**（四组答案**完全一致**）：

> 1) 视频里的主体是一只橘猫，毛色为橙黄色，带有条纹花纹，身上穿着蓝色外套。
> 2) 视频画面的风格是**写实摄影**，更接近第一张参考图。
> 3) 视频里**没有出现熊猫**。

—— 独立模型同时确认了**身份成立（猫）**、**风格没迁移（仍是写实）**、**没有串味成熊猫**。
它还看出猫穿着蓝色外套——这一点肉眼在缩略图上容易漏。

**Q2 串味排查**（海边 / 沙滩 / 奔跑的人 / 女性 / 竹子 / 熊猫）：

| 组 | 海边 | 沙滩 | 奔跑的人 | 女性 | 竹子 | 熊猫 |
|---|---|---|---|---|---|---|
| A | 没有 | 没有 | 没有 | 没有 | 没有 | 没有 |
| B | 没有 | 没有 | 没有 | **（误报）** | 没有 | **（误报）** |
| C | 没有 | 没有 | 没有 | **（误报）** | 没有 | **（误报）** |
| D | 没有 | 没有 | **（误报）** | **（误报）** | 没有 | **（误报）** |

**关键的四项（海边/沙滩/奔跑的人/竹子）在所有组都是「没有」——动作参考视频的内容没有渗进来。**
而"女性/熊猫"这几项是 **LFM3-VL-2B 这个 2B 模型的幻觉**：逐帧原图目检确认
B / C / D 每帧都只有一只橘猫，没有第二只动物、没有人。

> **教训：2B 复核模型在「有没有某个物体」这类否定式问题上会编答案。**
> 它的**肯定式**判断（主体是谁、画面什么风格）可信，**否定式**判断必须人工复核。
> 这也是本轮坚持"目检 + 量化 + 第三方"三道交叉验证的原因。

**Q3 运镜**：

| 视频 | LFM3-VL 的回答 | 相位相关实测 |
|---|---|---|
| A | "镜头似乎是缓慢推近猫的" | net_dx **+0.0**（无横移）|
| B | "镜头似乎是静止不动的" | net_dx **+1.0**（无横移）|
| C | "缓慢推近…画面整体在向右移动" | net_dx **+160.0**（向左）|
| D | "缓慢推近或平移…画面整体在向左移动" | net_dx **+208.0**（向左）|
| 动作参考 | "跟随人物…画面整体在向左移动" | net_dx **+334.0**（向左）|

**模型对 A/B/C/D 的定性判断全部正确**（A 推近、B 静止、C/D 有平移、参考有跟随）。
但它对 C 组的方向说反了（说"向右"，实测是向左），对 D 组和参考又说对了——
**方向这类需要精确定位的判断，2B 模型不可信，仍然以相位相关为准。**

### 15.6 坑

| # | 坑 | 后果 | 解法 |
|---|---|---|---|
| 1 | **`attach_audio` 的数字含义在官方示例里无法判别** | ≥4 条参考时可能把音轨挂错参考上 | 实测确认 = **音频那条参考自己的槽位号（1 起算）**；日志里数 `reference N` 那一行对不对 |
| 2 | **"空"参考端口会重编号后面的参考** | 请求被悄悄改写 | 没用到的端口**不要接**；每组写独立流水线 |
| 3 | **参考视频上采样到 1344×768 会让参考行翻倍** | 官方实测 13120→7144 行、23m07s→14m17s | `image-resample` 直接缩到输出画布（832×480），等价于 `reference_video_short_edge: 0` |
| 4 | **参考视频把前向行数推到 2.14 倍、耗时推到 3 倍** | 124 帧从 6m48s 变 20m28s | 参考视频按 2–15 s 用，别超过输出时长；必要时降帧数 |
| 5 | **2B 复核模型在否定式问题上会编答案** | 会把"画面里有没有熊猫"答成"有" | 否定式结论必须**人工逐帧目检**复核 |
| 6 | **自写的变焦率估计器不可靠** | 横移被误判成缩放（横移参考一度报 +87% 变焦） | 已弃用；只用**相位相关的全局平移**做运镜证据 |
| 7 | **相位相关的 dx 符号需要单独标定** | 方向说反 | 造一条已知方向的片子回测（`scripts/p1_check_sign.sh`）：本实现里 **负值 = 内容向右** |
| 8 | **shell 里 `$G` 紧跟中文字符会被吞** | `bad substitution` | 写 `${G}` |
| 9 | **ffmpeg 的 `ssim`/`psnr` stats 文件格式与直觉不同** | `All:` 在逐帧行里、`psnr_avg:` 在 psnr 行里 | 逐帧 `All:` 求均值 = 全片均值 |
| 10 | **`save-video` 的键仍是 `output_url`** | 整条流水线秒退不报错 | 照旧 |

### 15.7 结论

**P1 的四条成功判据，逐条给证据：**

| 判据 | 结论 | 证据 |
|---|---|---|
| 图锁住主体身份 | ✅ **成立** | 四组主体都是那只橘猫；LFM3-VL 独立确认；A 组与历史基线位级一致 |
| 第二张图锁住风格 | ❌ **不成立** | B/C/D 组画面仍是**写实**，不是水彩；也没有变成熊猫；LFM3-VL 独立确认"写实摄影"。加第二张图确实改了画面（SSIM 0.61），但改的是构图/场景，不是画风 |
| 动作视频的运镜能被复现 | ✅ **成立（幅度约一半）** | C/D 组净横移 +160 / +208 px vs 参考 +334 px（48% / 62%），方向一致；A/B 组为 0 |
| 三者同时给时不互相干扰 | ✅ **成立** | C/D 组没有出现海边、沙滩、竹子、奔跑的人；逐帧目检确认没有熊猫、没有第二只动物 |

**另外三条超出判据的发现：**

1. **参考音轨不仅生效，而且覆盖了提示词里的声景**（谱形 r = +0.710 / +0.646，谱质心 2859 → 992 / 1459 Hz）。
   官方文档说"音轨承载人声或音乐"，实测它**优先级高于提示词的 `Audio:` 段**。
2. **视频只锁"镜头方向与速度"，不锁"运动节奏"**（能量曲线相关仅 0.0126）。
   想复刻一段舞蹈/动作的节奏，参考视频不够。
3. **端口路线与文件列表路线位级等价**，多参考组合零保真度代价——多参考这条路完全走得通，瓶颈不在保真度。

**一句话结论：**

> **Ref2VA 的多参考是"多主体 + 运动 + 声音"的多通道，不是"多风格"的多通道。**
> 图只锁主体（第二张图会被当成另一个主体线索，而不是风格指令）；
> 视频锁镜头方向与速度；音轨锁声景并且压过提示词。
> 想让画面变成另一种风格，应该走**图生图**（Boogu）那条线，不是参考生视频。

**给带货场景的直接建议**：一件商品要出现在多个场景里，别指望在同一段片子里塞多张图分工——
**一次一个主体 + 一段运镜参考 + 一条音轨**是最有效的组合；多个场景请分几次生成再剪。

### 15.8 本节新增资产

| 类型 | 文件 |
|---|---|
| 流水线 | `pipelines/p1-{a,b,c,d}-multi-ref.vpipeline`（四条独立端口路线流水线）|
| 素材 | `refs/motion-pan-right-124f.mp4`（构造的横移摇摄动作参考）、`refs/motion-beach-124f.mp4`（原始跟踪镜头）、`refs/klein-multi-ref-panda-crop.jpg`（熊猫特写裁剪）|
| 成片 | `videos/p1-{a,b,c,d}-multi-ref.mp4`、`videos/p1-motion-ref.mp4` |
| 印相 | `images/p1-{a,b,c,d}-contact.png`、`images/p1-motion-ref-contact.png`、`images/p1-montage.png`（五行对照）|
| 脚本 | `scripts/make_p1_pipelines.py`（四条流水线生成器）、`scripts/p1_motion.py`（相位相关运镜量化）、`scripts/p1_audio.py`（音频谱形量化）、`scripts/p1_fidelity.sh`、`scripts/p1_pairwise.sh`、`scripts/p1_contact.py`、`scripts/p1_frames.sh`、`scripts/p1_montage.sh`、`scripts/p1_report_tables.py`、`scripts/vqa-p1.sh`、`scripts/p1_analyze_all.sh`、`scripts/p1_archive.sh`、`scripts/p1_sync_github.sh`、`scripts/p1_check_sign.sh` |
| 技能包 | `vpipe-reference-to-video/references/multi-ref.md`（端口路线实测手册）+ SKILL.md「多参考能不能分工」对照表 |

---


## 16. 第八轮：P3 —— 768p / 长规格 / 四段式续接

### 16.1 这一轮做了什么

上一轮（P1）把 Ref2VA 的多参考跑通之后，剩下的最大空白是 **「分辨率与时长」**。
MiniMax-H3 的官方文档把 768p 列成一族专门适配器，并明确写着 **shift 必须改成 6.0**，
但官方**没有给出任何"用错 shift 会怎样"的量化证据**，本机 vpipe 也**完全不告警**。

所以这一轮的任务是：**用成对实验把 768p 这件事从"文档说法"变成"可复现的量化结论"**。

| 组 | 规格 | 适配器 | shift | 步数 | 帧数 | 唯一变量 |
|---|---|---|---|---|---|---|
| **R1 shift6** | 1344×768 | `8step-768p-split` | **6.0** | 8 | 124 | 基准（官方推荐配置）|
| **R2 shift12** | 1344×768 | 同上 | **12.0** | 8 | 124 | **只变 shift** |
| **R5 long241** | 1344×768 | 同上 | 6.0 | 8 | **241** | 只变帧数（10.13 秒）|
| **R3 544p** | 960×544 | `8step-544p` | 12.0 | 8 | 124 | 换 544p 推荐配置 |
| **R4 4step** | 1344×768 | `4step-768p-v1.2` | 6.0 | **4** | 124 | 只变步数/蒸馏版本 |
| **P3.4 续接** | 832×480 ×4 段 | Pika fl2va / ref2va | 12.0 | 6 | 124×4 | 官方四段式长视频 |

统一控制：同一段提示词（虎斑猫 + 牛仔外套 + 木质窗台 + 暖色夕照）、**seed 42**、24 fps、音频同开。
每组按自动化约定抽 **第 0 / 40 / 80 / 末帧** 做印相，并做 LFM3-VL-2B 第三方复核。

> **本轮中途踩了一次重坑**：22:29 时 shift12 组被后台任务回收带走了 SIGHUP，
> 30 分钟的 denoise 只跑到 0% 就全废。根因与解法见 16.7 第 1 条。

### 16.2 768p 到底怎么开：适配器家族、注册表与 shift 规则

**第一件事是纠正文档里的一个错觉。** 官方把 768p 适配器列成 5 个"仓库"，
实测注册表里 **11 条 `minimax-h3-lora` 条目全部指向同一个 `hf_path`：`lightx2v/Minimax-h3-Turbo`**。
区分靠的是**注册名（name）+ 变体（variant）**，不是仓库：

| 注册名（写进 `lora`） | variant | 落到哪个文件 | 体积 |
|---|---|---|---|
| `lightx2v/Minimax-h3-Turbo-8step-768p-split` | 8-step v1.0 768p, shift 6, **split qkv** | `minimax_h3_fl2v_turbo_8step_v1.0_768p_bf16.safetensors` | 1.38 GB |
| `lightx2v/Minimax-h3-Turbo-8step-768p` | 8-step v1.0 768p, shift 6 | 同上 | 1.38 GB |
| `lightx2v/Minimax-h3-Turbo-4step-768p-v1.2` | 4-step v1.2 768p, shift 6, split qkv | `minimax_h3_fl2v_turbo_4step_v1.2_768p_bf16.safetensors` | 1.38 GB |
| `lightx2v/Minimax-h3-Turbo-ref2va-8step-768p` | Ref2VA 8-step 768p, shift 6, split qkv | `minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16.safetensors` | 1.38 GB |
| `lightx2v/Minimax-h3-Turbo-8step` | **8-step v1.0 544p** | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1.96 GB（fused qkv）|

每个文件 624 张量。**ModelScope 上 31 个文件全在**，HF 直连依然不通，
所以 `VPIPE_MODEL_SOURCE=modelscope` 是硬前提。

**第二条是 shift 规则。**

| 适配器 | `video_shift` | `audio_shift` |
|---|---|---|
| 768p 系列（全部）| **6.0** | 3.0 |
| 544p / Pika / HyperFlow | 12.0 | 3.0 |

### 16.3 ★ 本轮最重要的发现：**shift 写错是完全静默的**

官方文档说"768p 要把 shift 改成 6.0"，但**没有任何机制会告诉你你改错了**。三层证据：

**第一层 · vpipe 源码。** `stages/generate-video-stage.cc:3746` 确实有一条 shift 不匹配的告警，
但它只在两种情况下触发：HyperFlow，以及**带 `sampling contract` 的适配器**（Pika H3 Flex 这类把
sigma 网格写进权重文件的）。lightx2v 的 Turbo 适配器是**普通 LoRA**，没有 contract —— **一条警告都不会有**。

**第二层 · 权重文件本身也不携带这条信息。** 读四个 safetensors 的 `__metadata__`：

```
minimax_h3_fl2v_turbo_8step_v1.0_768p_bf16.safetensors
    alpha = 8 / format = pt / floating_dtype = bfloat16 / key_format = minimax-h3-diffusers
    （624 张量，没有 shift、没有 sigma 网格、没有训练分辨率）
```

**第三层 · 实测日志。** R2（768p 适配器 + shift 12.0）跑得干干净净：

```
[INFO] MiniMaxH3ModelConfigStage: shifts 12.0/3.0, condition t 1.000/1.000, runtime lora at 1.00
[INFO] GenerateVideoStage: MiniMax-H3 (video+audio) at 1344x768x124 frames, 8 steps, shifts 12.0/3.0
（全文唯一一条 WARN 是 wired pool 分配失败，与 shift 无关）
```

**结论：768p 的 shift 规则是"外部知识"，工具既不校验也不告警。**
不知道这条规则的人会得到一片"看起来正常但明显不对劲"的画面，而且**没有任何线索指向原因**。
这正是本轮要做成对实验的理由。

### 16.4 量化证据

#### 16.4.1 五组运行规格与资源画像

| 组 | 前向行数 | 耗时 | 最低可用内存 | DiT 常驻 | 权重常驻率 |
|---|---:|---|---:|---|---|
| R1 shift6 | 37 804 | **29 分 34 秒** | 8 % | 25 / 50 块 | **0 %**（221/221 页被换出，wired 10 396 MB）|
| R2 shift12 | 37 804 | 28 分 47 秒 | 8 % | — | — |
| R5 long241 | **73 480** | **1 小时 21 分** | **7 %** | — | — |
| R3 544p | 19 378 | **9 分 35 秒** | 10 % | — | — |

**行数模型被两次数值独立验证**：`行数 ≈ 305 × 帧数`
（124 → 37 804 = 304.9/帧；241 → 73 480 = 304.9/帧；544p 因像素数减半 → 19 378 = 156.3/帧）。

**耗时近似线性于行数，但不是严格线性**：
768p 每行 0.0469 s，241 帧时劣化到 0.0669 s/行（**+43 %**，因为 73K 行把 wired pool 压得更紧）。

#### 16.4.2 画质指标

| 组 | 分辨率 | 时长 | 帧数 | 细节能量(原生) | **细节能量(画布)** | 饱和度 | 对比度 | 抖动 | 冻结帧对 | 音频 RMS | 谱质心 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1 shift6 | 1344×768 | 5.18 s | 124 | 167.7 | **167.7** | 0.4714 | 70.62 | 2.53 | 0 | 0.00247 | 3275 Hz |
| R2 shift12 | 1344×768 | 5.18 s | 124 | 158.6 | 158.6 | **0.4854** | **72.93** | 2.735 | 0 | 0.00456 | 3096 Hz |
| R5 long241 | 1344×768 | **10.13 s** | **243** | 173.2 | **173.2** | 0.4979 | 67.92 | **2.295** | 0 | 0.00266 | 2481 Hz |
| R3 544p | 960×544 | 5.18 s | 124 | 175.1 | **50.3** | 0.4113 | 75.80 | 2.61 | 0 | 0.00457 | 3955 Hz |

> **口径**：细节能量 = 逐帧拉普拉斯响应方差（高通），越大越锐。
> **"原生"** = 各组按自己分辨率算（绝对锐度）；**"画布"** = 统一缩放到 1344×768 再算（**交付尺寸上的残余锐度**）。
> 跨分辨率只能比"画布"口径 —— 原生口径下 544p 反而更高（175.1），因为同样的信号摊在更少的像素上，每个像素都拿满了。

#### 16.4.3 shift 6.0 vs 12.0（R1 vs R2，唯一变量是 shift）

| 指标 | R1 shift 6.0 | R2 shift 12.0 | 差异 |
|---|---:|---:|---|
| 细节能量 | 167.7 | 158.6 | **shift12 低 5.4 %** |
| 饱和度 | 0.4714 | 0.4854 | **shift12 高 3.0 %** |
| 对比度 | 70.62 | 72.93 | **shift12 高 3.3 %** |
| 时序抖动 | 2.53 | 2.735 | shift12 高 8.1 % |
| 帧间 SSIM / PSNR | — | **0.6520 / 17.70 dB** | 两组画面已是两支不同的片子 |
| 冻结帧对 | 0 | 0 | 均无 |
| 纯黑帧 | 0 | 0 | 均无 |

**三条信号方向完全一致**：**细节更少、饱和与对比更高、时序更抖** ——
这正是"用错误的 sigma 网格去采样一个为另一个网格蒸馏出来的模型"的典型表现
（过度对比 / 色彩漂移 / 边缘不稳）。目检也印证：R2 的窗框橙更艳、绿更浓。

#### 16.4.4 768p vs 544p 的性价比

| 指标 | R1 768p | R3 544p | 比值 |
|---|---:|---:|---|
| 耗时 | 29 分 34 秒 | 9 分 35 秒 | 768p 贵 **3.09 ×** |
| 交付尺寸细节能量 | **167.7** | **50.3** | 768p 强 **3.33 ×** |
| 饱和度 | 0.4714 | 0.4113 | 544p 低 12.8 % |
| 帧间 SSIM / PSNR（544p 放大后 vs 768p） | — | **0.5688 / 12.64 dB** | 差得不是一点半点 |

**768p 的钱花得值**：贵 3.09 倍，换来交付尺寸上 3.33 倍的细节能量。
而 544p 放大到 1344×768 之后细节能量只剩 **50.3**（768p 的 30 %）—— **模糊是补不回来的**。

#### 16.4.5 长规格（241 帧 / 10.13 秒）会不会尾部劣化

| 指标 | R1（124 帧） | R5（241 帧） |
|---|---:|---:|
| 细节能量 前 1/3 | 159.5 | 190.1 |
| 细节能量 后 1/3 | 176.1 | **156.6** |
| 整体细节能量 | 167.7 | **173.2** |
| 时序抖动 | 2.53 | **2.295**（更稳）|
| 冻结帧对 | 0 | **0** |
| 首帧 → 末帧亮度 | 93.4 → 99.1 | 99.4 → **97.7**（无漂移）|
| 纯黑帧 | 0 | **0** |

**没有尾部劣化。** 末 1/3 的细节能量（156.6）低于首 1/3（190.1），
但这是**镜头在慢慢推近**导致画面里毛发占比下降，而不是画质退化；
逐帧目检末帧（#242）确认毛发、牛仔布织纹、窗框边缘**仍然锐利**，背景稳定不漂。
抖动反而更低、零冻结帧 —— **10 秒单段在 768p 上是稳的**。

#### 16.4.6 音频

四组**全部有声、全部非静音、全部零黑帧**。

| 组 | RMS | 峰值 | 谱质心 | 低频占比(<200 Hz) |
|---|---:|---:|---:|---:|
| R1 shift6 | 0.00247 | 0.116 | 3275 Hz | 0.190 |
| R2 shift12 | 0.00456 | 0.165 | 3096 Hz | 0.131 |
| R5 long241 | 0.00266 | 0.067 | **2481 Hz** | **0.250** |
| R3 544p | 0.00457 | — | 3955 Hz | 0.103 |

10 秒版本的谱质心最低（2481 Hz）、低频占比最高（0.250），
与提示词里的 "soft rhythmic purring, a faint breeze" 在更长时间里建立起来的声景一致。

### 16.5 LFM3-VL-2B 第三方复核（独立于生成链路）

三组问题：**细节解析度 / 画面健康 / 跨组一致性**，每组喂第 0/40/80/末帧四张图。

**Q1 细节解析度 —— 五组全部通过：**

| 组 | 回答 |
|---|---|
| shift6 / shift12 / long241 | 主体是一只猫、穿着牛仔布外套；**毛发一根根清晰可辨**，**牛仔布的织纹能看出经纬结构**，窗玻璃与窗框边缘锐利清晰 |
| 4step | 同上，逐字一致 |
| 544p | 猫、牛仔布外套、毛发一根根可辨、窗框边缘锐利 |

**Q2 画面健康 —— 五组全部"没有任何一项异常"**
（无彩色噪点 / 无马赛克方块 / 无横竖条纹 / 无撕裂错位 / 无大片纯黑纯白 / 无色彩突变块）。
这一问是专门为 **P4 刚修完的预览流花屏**设的，必须由第三方模型独立确认。

**Q3 跨组一致性 —— 独立复现了 shift 的结论：**

> "这些图片展示的是**同一个场景**，主体是**一只穿着牛仔外套的猫**，位于窗台上……核心元素保持一致。"
>
> - **768p 正确设置**：图像清晰，焦点集中在猫身上，窗外景色略显模糊
> - **768p 错误设置**：图像**稍微模糊，细节不如正确设置清晰**
> - **544p**：图像分辨率较低，细节不够锐利
> - **4 步版本**：图像质量看起来最为稳定，细节清晰

**这一条最有价值**：2B 模型在不知道我们量化结论的情况下，
**自己把 shift 12 那组挑出来说"稍微模糊、细节不如正确设置清晰"**，
与我们测到的细节能量 **−5.4 %**（158.6 vs 167.7）方向一致。
第三方模型 + 高通能量两条独立证据指向同一结论 —— **shift 6.0 是必须的**。

（同时再次印证 P1 的教训：LFM3-VL-2B 对"清晰/模糊"这类**相对**判断是可信的，
但对精确方向、帧号等仍不可信，结论仍以量化与逐帧目检为准。）
### 16.6 P3.4 · 四段式续接（官方长视频正路）

官方给的长视频方案是 `minimax-h3-extend-part1..4.vpipeline` + `minimax-h3-extend-concat.vpipeline`
（本机源码树 `docs/pipelines/` 下就有）。官方规格是 960×576 / 243 帧 / 20 步 / 基础 bf16 模型，
**24 GB 机器跑不动**，所以按 P1 的经验缩到 **832×480 / 124 帧 / 6 步 / Pika 适配器**，
每段 5.1667 秒，4 段 = **20.67 秒**。

**做法：不重画接线，直接给官方 JSON 打补丁。** 只替换本机特有的东西
（本地 8-bit 权重、Pika 适配器、分辨率/步数、输出路径、提示词），
端口拓扑、`temporal-stack` 参数、`attach_audio` 槽位全部沿用官方。

#### 16.6.1 官方续接机制（逐字沿用）

```
load-video(上一段) → video-to-rgb → temporal-slice(start=-90) → temporal-stack → 参考1(视频)
load-audio(上一段, start_s=段长-3.75, duration_s=3.75) → audio-to-pcm → temporal-stack → 参考2(音频)
video-ref-encoder(attach_audio=[2], reference_video_short_edge=0, max_mb=384)
save-video(video_codec=ffv1, audio_codec=alac, 无损、色度不折半)
```

- **末 90 帧 = 3.75 秒**，与音频引导的 **3.75 秒刻意对齐**
- `attach_audio: [2]` 里的 2 = **音频那条参考自己的槽位**（与 P1 的结论完全一致）
- 续接提示词以 `[video continuation + audio reference]` 开头，
  并保留 `subject_definitions` / `retention_analysis` / `detailed_description` /
  `overall_soundscape` / `non_diegetic_music` 五个固定段落
- 实测 **ffv1 装进 .mp4 可正常读回**（yuv444p 保留、不折半色度），不必改容器

#### 16.6.2 四段跑批

| 段 | 前向行数 | 耗时 | 说明 |
|---|---:|---|---|
| part1 | 14 935 | **5 分 21 秒** | FL2VA t2v（Pika fl2va，6 步），无参考 |
| part2 | 27 965 | **12 分 23 秒** | Ref2VA 续接（上一段末 90 帧 + 音轨） |
| part3 | 27 970 | 12 分 17 秒 | 同上 |
| part4 | 27 961 | 11 分 53 秒 | 同上 |
| concat | — | 5.8 秒 | `load-video` 数组拼接 → **20.70 秒 / 496 帧** |

**引导视频让前向行数涨了 87 %（14 935 → 27 965），耗时翻倍**（5m21s → 12m）。
这是 P1 结论（参考视频让行数 ×2.14、耗时 ×3）在 Ref2VA 续接链路上的复现。

产物：`p3-ext-part1..4.mp4`（ffv1 无损，各 35 MB）+ `p3-ext-full.mp4`（h264，27 MB，**解码零错误**）。

#### 16.6.3 ★ 接缝跳变量化 —— 漂移是**累积**的

判据：**接缝处相邻帧的 SSIM，是否落在段内相邻帧 SSIM 的正常分布内。**

| 接缝 | 接缝 SSIM | 接缝 PSNR | Δ亮度 | **相位相关位移** | 位移补偿后 SSIM | 段内基线 p5 |
|---|---:|---:|---:|---:|---:|---:|
| part1→part2 | **0.4572** | 14.53 dB | **1.1** | **(0.0, 0.0)** | 0.515 | 0.9562 |
| part2→part3 | **0.3578** | 11.34 dB | **8.59** | (6.03, **+76.02**) | 0.422 | 0.9579 |
| part3→part4 | **0.2812** | 10.11 dB | **13.28** | (1.77, **−86.11**) | 0.332 | 0.9627 |

段内相邻帧基线（各段自身）：

| 段 | 段内 SSIM p5 / p50 / p95 | 冻结帧对 |
|---|---|---:|
| part1 | 0.9562 / 0.9716 / 0.9856 | 0 |
| part2 | 0.9579 / 0.9708 / 0.9831 | 0 |
| part3 | 0.9627 / 0.9784 / 0.9866 | 0 |
| part4 | 0.9815 / 0.9884 / 0.9942 | 0 |

拼接片整体：20.70 秒 / 496 帧 / **冻结帧对 0**，
段边界帧间差 **[27.7, 48.5, 58.4]** vs 段内中位数 **2.42**，
整体亮度 **114.5 → 72.1（净漂移 −42 级）**。

**结论（这是本轮最反直觉的一条）：**

1. **第一处接缝几乎是完美的**：位移 (0, 0)、Δ亮度只有 1.1，视觉上完全连续（见 16.6.5 接缝对照图第一行）。
2. **从第二处接缝起开始明显跳变**：垂直方向 **+76 px** 与 **−86 px** 的重构跳变，
   亮度差涨到 8.6 / 13.3。目检确认：模型在 part3/part4 **重新调度了场景**
   （猫的姿势、景别、光线都变了），而不是从上一段的末帧延续。
3. **位移补偿后 SSIM 仍然只有 0.33–0.42**（基线 0.96）→ 这不是几何错位，
   是**重新渲染导致的像素级纹理漂移**。相位相关测出 (0,0) 的那一处也印证了这一点：
   语义/构图/身份/光线都连贯，但细节不逐像素延续。
4. **漂移是累积的**：SSIM 0.457 → 0.358 → 0.281 单调下降。

> **所以「末帧续接 = 无缝长视频」这个官方说法，在本机 832×480 / Pika 6 步的配置下不成立。**
> 第一段接得上，后面每接一次，模型就会重新想一个构图。
> 想真正无缝，要么把段数减到 2 段（第一处接缝确实是好的），
> 要么提高单段分辨率/步数让引导更强 —— 本轮没有验证后一条。

#### 16.6.4 LFM3-VL-2B 复核（这里它"看漏了"）

| 问题 | 回答 |
|---|---|
| **Q1 跨段一致性** | "四张图中都是**同一只猫**，毛色棕白相间，脸型特征相同，脖子上都穿着**蓝色的牛仔外套**，款式一致"；背景"窗户、木质窗台、窗外的房子和树"一致；"**光线方向和色温保持一致**，阳光从右侧照射进来，呈现暖色调"；姿态变化"自然连贯" |
| **Q2 画面健康** | 没有 ×6（无噪点/马赛克/条纹/撕裂/纯黑白块/色彩突变）|
| **Q3 接缝跳变** | "接缝处**没有出现任何突发的构图跳变、主体变形、光线突变或色彩跳变**"，后两处接缝被描述成"姿势和环境**略有不同**""更加放松，身体蜷缩" |

**Q1/Q2 完全正确**，但 **Q3 漏判了**：76 px 与 86 px 的垂直重构跳变、Δ亮度 8.6/13.3 的色调突变，
2B 模型全部读成了"自然的姿态变化"。

> **方法论结论（与 P1 的教训一致）：**
> **"是不是跳变"这种空间连续性问题，2B 复核模型不可信，必须靠相位相关的位移分解 + 逐帧目检。**
> LFM3-VL 能可靠回答的仍然是"是不是同一只猫""有没有编码异常""光线方向"这类**语义/属性**问题。

#### 16.6.5 接缝目检对照

三处接缝的前后帧并排（第一行 = 接缝1，第二行 = 接缝2，第三行 = 接缝3）：

- **接缝 1**：左右几乎完全一致（同姿态、同框、同光），肉眼无缝。
- **接缝 2**：左＝抬爪低头，右＝抬头侧望、爪子放下、景别与光感都变了 —— **明显跳变**。
- **接缝 3**：左＝低头近景，右＝蜷缩起来、整体更暗更远 —— **明显跳变**。

### 16.7 坑

| # | 坑 | 后果 | 解法 |
|---|---|---|---|
| 1 | **后台任务被回收会杀死正在跑的重任务** | 22:29 shift12 组被 SIGHUP 带走，30 分钟 denoise 只跑到 0% 全废 | `setsid` 让子进程脱离进程组 + `.done` 标记幂等续跑 + PID 续接（发现该组还有活进程就等它）+ 内存/磁盘门限 |
| 2 | **lightx2v 适配器不带 sampling contract** | 4 步适配器配 8 步图**静默跑偏**，AdaLN 会按 8 步烘焙 | **步数必须手动对齐适配器**；lightx2v 的网格信息不在权重里，也不在注册表里，只能查官方表 |
| 3 | **768p 用错 shift 完全静默** | 画面细节 −5.4%、饱和 +3.0%，无任何日志线索 | 只能靠成对实验（见 16.3）|
| 4 | **macOS 自带 bash 3.2 没有 `declare -A`** | 关联数组直接报 `unbound variable` | 用 `case` 分派 |
| 5 | **数组追加 `+=(-i "$f")` 会拆成两个元素** | `${#files[@]}` 是图数的 2 倍，filter 索引与 `hstack=inputs` 全错 | 图像数量**单独计数**；`-i` 与路径保持两个 argv |
| 6 | **中文全角标点紧跟 `$VAR` 会被吞进变量名** | `unbound variable` | 写 `${VAR}` |
| 7 | **sandbox 里 `os.rmdir` / `rm -rf` 会被拒** | 清理抛异常中断脚本 | 清理包 try/except |
| 8 | **ffmpeg 的 `ssim` 滤镜需要两路输入** | 算"段内相邻帧 SSIM"时单路输入静默无输出 | `split` + `trim=start_frame=1` 做"本片 vs 自己错一帧" |
| 9 | **ffmpeg 的 ssim stats 文件第 2 列不是 All** | `float(l.split(" ")[1])` 取到 Y 分量，解析崩 | 按 key 解析 `All:` |
| 10 | **`load-video` 的 `input_url` 可以是数组** | 不知道官方 concat 能一次拼多段 | 官方 `minimax-h3-extend-concat.vpipeline` 就是这么用的 |
| 11 | **请求 241 帧实际输出 243 帧** | 对不上预期的 10.04 秒 | 243 帧 @24fps = **10.125 秒**，正好是官方 extend 段的时长（`chunk_duration_s: 10.125`）|

### 16.8 结论

**P3 的四条成功判据，逐条给证据：**

| 判据 | 结论 | 证据 |
|---|---|---|
| 768p 能不能跑 | ✅ **能，而且很稳** | 1344×768 / 124 帧 / 8 步 = **29 分 34 秒**；241 帧（10.125 秒）= **1 小时 21 分**；零冻结帧、零纯黑帧、尾部不劣化 |
| shift 6.0 是不是必需的 | ✅ **必需，且工具不会告诉你** | 同 seed 同适配器只改 shift：细节能量 **−5.4%**、饱和 **+3.0%**、对比 **+3.3%**、抖动 **+8.1%**；**vpipe 源码 + safetensors 元数据 + 实测日志三层都证明零告警**；LFM3-VL 独立看出"shift12 那组稍微模糊" |
| 768p 比 544p 值不值 | ✅ **值，3.09× 换 3.33×** | 29m34s vs 9m35s；交付尺寸细节能量 167.7 vs **50.3**；放大后 SSIM 0.5688 / PSNR 12.64 |
| 四段式续接能不能无缝 | ❌ **只能接住第一处** | 接缝 SSIM 0.457 → 0.358 → 0.281 单调下降；第 2/3 处出现 **+76 px / −86 px 垂直重构跳变**；Δ亮度 1.1 → 8.6 → 13.3；位移补偿后仍只有 0.33–0.42 |

**四条超出判据的发现：**

1. **lightx2v 适配器"不带网格"**。权重文件的 `__metadata__` 里没有 shift、没有 sigma 网格、
   没有训练分辨率；注册表里也只有一个人类可读的 variant 字符串。
   **适配器与采样图之间的约定，是纯外部知识**，vpipe 既不校验也不告警。
2. **行数模型可以直接用来预测预算**：`行数 ≈ 305 × 帧数`（124 → 37 804，241 → 73 480，两次独立验证）。
   耗时近似线性于行数，但**每行成本会随行数上升**（0.0469 → 0.0669 s/行，+43 %）——
   24 GB 上越长的片段越不划算。
3. **241 帧不是"多一倍时间"，是"多一倍注意力"**：请求 241 帧实际产出 243 帧（10.125 秒），
   与官方 extend 段的 `chunk_duration_s: 10.125` 严丝合缝 —— 说明官方本来就是按 243 帧设计的。
4. **4 步适配器是 768p 上最划算的选项**：4 步 v1.2 = **13 分 26 秒**（8 步的 **45.5 %**），
   细节能量 **170.6 略高于 8 步的 167.7**。但**必须把 `steps` 也改成 4**，否则会静默跑偏。

**给实际生产的直接建议：**

> - **要 768p**：`lora: lightx2v/Minimax-h3-Turbo-8step-768p-split` + `video_shift: 6.0` +
>   `steps: 8`；**要快**就用 `4step-768p-v1.2` + `steps: 4`（省一半时间，画质不降）。
> - **不要在 24 GB 上拉 362 帧（15 秒）单段**。10 秒可以，15 秒风险过高。
> - **要 20 秒以上**：走四段式续接，但**别指望无缝**——每接一次模型就会重新构图。
>   商业用途更稳的做法是**分段生成 + 剪辑**，或者把接缝放在镜头切换点上（用一个硬切盖住跳变）。
> - **接缝判据要靠相位相关**，不要靠 2B 模型判"是不是跳变"，它会把 76 px 的重构读成"自然的姿态变化"。

### 16.9 本节新增资产

| 类型 | 文件 |
|---|---|
| 流水线 | `pipelines/p3-768p-{shift6,shift12,544p,4step}.vpipeline`（四条 768p 对照）<br>`pipelines/p3-ext-part1..4.vpipeline` + `p3-ext-concat{,2}.vpipeline`（官方 extend 打补丁版，5 条） |
| 成片 | `videos/p3-768p-{shift6,shift12,4step}.mp4`、`videos/p3-544p-ref.mp4`、`videos/p3-768p-shift6-241f.mp4`（10.13 秒）<br>`videos/p3-ext-part1..4.mp4`（ffv1 无损）、`videos/p3-ext-full.mp4`（20.70 秒拼接成片）、`videos/p3-ext-full2.mp4` |
| 印相 | `images/p3-{shift6,shift12,544p,4step,long241}-contact.png`、`images/p3-ext-part{1..4}-contact.png`、`images/p3-ext-full{,-2}-contact.png`、`images/p3-montage.png`（**9 行汇总对照**）|
| 脚本 | `scripts/make_p3_pipelines.py`、`scripts/make_p3_extend_pipelines.py`（官方 extend 打补丁生成器）<br>`scripts/p3_runner.sh` / `p3_runner_ext.sh` / `p3_chain.sh`（**setsid + 幂等续跑 + PID 续接 + 内存磁盘门限**）<br>`scripts/detach_run.py`（脱离进程组启动器）<br>`scripts/p3_frames.sh` / `p3_frames_ext.sh` / `p3_montage.sh` / `p3_contact.py`<br>`scripts/p3_analysis.py`（细节能量双口径 + 饱和度 + 时序 + 音频）、`scripts/p3_extend_analysis.py`（**接缝 SSIM + 相位相关位移分解 + numpy SSIM 自检**）<br>`scripts/p3_report_tables.py`、`scripts/vqa-p3.sh`、`scripts/vqa-p3-ext.sh`、`scripts/p3_archive.sh`、`scripts/p3_sync_github.sh` |
| 技能包 | `vpipe-model-prepare/references/768p-adapters.md`（**768p / 长规格手册**：适配器家族、shift 6 规则、24 GB 资源画像、帧数↔成本模型、四段式续接机制、7 条坑）<br>`vpipe-model-prepare/assets/prepare-minimax-h3-768p.vpipeline`、`assets/p3-768p-shift6.vpipeline` |

---
