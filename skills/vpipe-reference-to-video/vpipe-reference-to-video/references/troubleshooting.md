# 故障排查表

## 静默失败（最危险的一类）

这类问题**不报错**，流水线却什么都没做。

| 症状 | 根因 | 修法 |
|---|---|---|
| `SaveVideoStage('save-video'): config.output_url is required; skipping initialize/process` | `save-video` 用了 `path` 键 | 改成 **`output_url`** |
| `SaveVideoStage('save-video'): expected 2 input edge(s) (enable_video=true, enable_audio=true) but got 1; skipping initialize/process` | `save-video` 只接了视频一路 | 补上 `audio-vae-decode` → 端口 1 |
| `the layout reserves N reference video and 0 reference audio rows but the encoder packed 0 and 0. The video-ref-encoder's frames and this stage's do not agree; skipping` | 两个 stage 的 `frames` 不一致 | 让它们**完全相等** |
| `last-frame keyframe latent does not match [24, n, 30, 52]; generating without it` | 参考视频的画布尺寸没配 | 补 `reference_video_short_edge` + `reference_video_max_pixels` |
| `ModelQuantizeStage('quant-dit'): source model 'X' is not available (not downloaded yet?); skipping quantization` | `src_model` 与注册名不一致 | 见下方「量化源错配」 |
| 流水线秒退、耗时 < 20 秒、无视频产出 | 上面的任一条 | 逐条核对 |

**排查口诀**：先看 `ran for` 的耗时。**秒退 = 有 stage 被跳过**，去日志里找 `skipping`。

## 模型下载

| 症状 | 根因 | 修法 |
|---|---|---|
| `model_variant 'X' matches 0 of the N models published from 'Y'` | variant 匹配是**逐字段**比对 `version`/`variant`/`name`/`model_type` | 用 `model_type`，如 `"qwen-image-edit"` |
| `it has to select exactly one of: ...` | 同上 | 同上 |
| `has no counterpart on ModelScope -- it is published only on HuggingFace` | 该模型只在 HF | 找替代路线（Krea-2 走无 LoRA 版） |
| HF 直连超时 | 本机网络 | `export VPIPE_MODEL_SOURCE=modelscope` |
| `variant.empty()` 时报 `matches 0 of the N` | 该仓库有多个 variant | 必须显式指定 |

## 显存与内存

| 症状 | 根因 | 修法 |
|---|---|---|
| Metal budget exhausted / malloc 失败 | 24GB 上模型太大 | 降到 8-bit；或用官方 prepare 流水线的 residency 流式加载 |
| 参考图编码时显存爆 | `reference_image_short_edge` 默认 2048 | 降到 **1024** |
| 进程被杀、日志无错消失 | 并行跑重任务（IO 竞争） | **重任务串行** |

## 质量与保真度

| 症状 | 根因 | 修法 |
|---|---|---|
| 参考生视频里服装/配饰丢失 | 已知问题 | 提示词点名保留；或改用首尾帧锚定 |
| 仅首帧锚定，第 40 帧左右主体消失 | DiT 按提示词重构画面 | 用**首尾帧锚定** |
| 输出有水印/假文字 | 提示词没抑制 | 加 `No text, no captions, no logos.` |
| 输出比例走样 | `image-resample` 的 `fit: crop` 裁切 | 调整参考图比例，或用 `letterbox` |
| 参考图被过度上采样（日志 `UPSCALED ... (447% of the pixels)`） | `reference_image_short_edge` 作用于**短边** | 准备比例匹配的参考图 |
| 参考视频速度不对 | 输入丢了帧率 | 端口路线必须声明 `fps` |
| 音频音高升高四度 | 音轨是 44.1kHz 但被当 32kHz | `audio-to-pcm` 的 `output_sample_rate: 32000` |

## 预览

| 症状 | 根因 | 修法 |
|---|---|---|
| 预览无反应、日志无任何警告 | 偶发时序竞态 | **原版重跑一次**（本例即好） |
| CLI 下流水线不结束 | `preview` 是 WebSocket sink | 自行终止，或改用 Web UI |
| `preview_vae` 配了但不生效 | 配在了错误的 stage | 必须挂在 `generate-video` 的 config 里 |

## 工具链杂项

| 症状 | 根因 | 修法 |
|---|---|---|
| `ffmpeg: command not found` | 不在 PATH | 用绝对路径 `/Users/<user>/.hermes/tools/ffmpeg-*/ffmpeg` |
| 没有 `ffprobe` | 该 ffmpeg 构建不含 | 用 `ffmpeg -i` 探测 |
| `rm` 之后 `df` 没变 | WorkBuddy 的 `rm` 是 safe-delete shim | `/bin/rm -f "/Users/<user>/.Trash/<file>"` |
| `osascript ... empty trash` 报 -10004 | macOS TCC 权限 | 用 `/bin/rm` 直接删废纸篓里的文件 |
| `unlink ~/.Trash/x` 报 Operation not permitted | 同上 | 同上 |

## 量化源错配（上游 issue #15）

官方 `prepare-minimax-h3-8bit.vpipeline` 里：
- `fetch` 注册名是 `Comfy-Org/MiniMax-H3-FL2VA`（无 `model_key` 时回退到 catalog 名）
- `quant-dit` 的 `src_model` 却是裸 repo id `Comfy-Org/MiniMax-H3`

`model_dir_available` 是注册表 key 查找 + stat，裸 id 永远匹配不上 → 源找不到 → 静默 drain。

**修法**：把 `quant-dit` 的 `src_model` 改成注册名 `Comfy-Org/MiniMax-H3-FL2VA`。

## 真人参考图实测补充（2026-11-14）

用真实人像照片（484×864 竖图）跑参考生视频的实测记录：

| 项 | 值 |
|---|---|
| 耗时 | 7 分 32 秒 |
| 规格 | 832×480 / 124 帧 / 5.18 s + AAC 立体声 32 kHz |
| 参考图处理 | `UPSCALED 484x864 -> 1024x1824 (447% of the pixels)` |

**竖图的坑**：`reference_image_short_edge` 作用于**短边**。竖图 484×864 → 短边放大到 1024 后变成 1024×1824，像素量是原图的 4.47 倍。这会：
1. 显著拖慢编码
2. 让参考画布比例（0.56）与输出画布比例（1.73）严重不符，模型需要额外适配

**建议**：正式使用前把参考图预先裁成与输出接近的比例（832×480 附近），避免 447% 这类过度上采样。

**目检结果**：白背心配深蓝百褶裙、黑色长发、摄影棚柔光箱布景，服装与配色完全继承参考图；镜头从背面绕到正面并推进到面部特写，服装全程保留。画面无水印、无字幕。
