# 多参考组合（端口路线）

> 实测日期：2026-11-14 · 机器：Mac mini M5 Pro / 24 GB · 模型：`local/MiniMax-H3-Ref2VA-8bit`
> 配套流水线：`pipelines/p1-{a,b,c}-multi-ref.vpipeline`

## 官方规格

| 项 | 上限 |
|---|---|
| 单次请求的参考总数 | **12**（9 图 + 3 视频 + 3 音频，且音频不能是唯一种类）|
| 单段参考视频 | 2–15 秒 |
| 总时长 | ≤ 15 秒 |
| 本地生成时长 | 4–15 秒 |
| 端口参考槽位 | 6 个（编码器 iport 2–7）|

## 两条路线

| | 路径 A：`references` 文件列表 | 路径 B：**端口路线**（官方示例用这个）|
|---|---|---|
| 写法 | `"references": ["a.jpg", "b.mp4"]` | `load-image` / `load-video` → 各自的 stage → 编码器 iport |
| 几何尺寸 | 由编码器按种类决定 | **你自己决定**（每个参考独立）|
| 混合 | 可以（端口参考排在列表之后）| 可以 |

### 端口路线的完整接线

```
load-image  → image-resample(WxH)                                  → 编码器 iport2+   （图）
load-video  ┬→ video-to-rgb → image-resample(WxH) → temporal-stack   → 编码器 iport2+   （视频）
            └→ audio-to-pcm(32000, stereo) → temporal-stack          → 编码器 iport2+   （音轨）
```

编码器 iport 分配：**0 = 提示词，1 = model-select，2–7 = 参考 1–6**。

## 四个承重细节

1. **`attach_audio` 填的是「音频那条参考自己的槽位号」（1 起算），不是图/端口号**
   - 音频必须**排在**它要归属的片段后面（紧邻即可）
   - 槽位号 = 该参考在「参考序列」中的序号（文件列表的在前，端口的在后）
   - 官方示例只有 3 条参考时两种读法数值恰好相同，所以**只有 ≥4 条参考时才会暴露歧义**
   - 日志里会打 `reference N (video 124f ...): ... audio VAE 65 latents` —— 音视频被折叠成一条参考就是配对了

2. **`reference_video_short_edge: 0` = 让参考视频保持自己的画布**
   - 官方二参考示例实测：`768 → 0` 让**参考行 13120 → 7144**、**条件行 3115 → 2119**、**耗时 23m07s → 14m17s**
   - 原因：`768`（出厂值）会把一条 960×544 的参考**上采样到 1344×768**，凭空多 1.98 倍像素
   - 端口路线里没有这个键，直接**用 `image-resample` 把参考视频缩到输出画布尺寸**即可达到同样效果

3. **`temporal-stack` 的 `max_mb`**
   - 124 帧 @ 832×480 = **148.6 MiB**；124 帧 @ 1344×768 = **366 MiB**
   - 默认 256 MiB 会把参考**截到 86 帧**并告警 → 用 `max_mb: 384`

4. **参考视频的帧率必须活下来**
   - `video-to-rgb` 出来的张量带 `fps` sideband；`load-video` 走同容器出视频与音轨，同步关系才成立
   - 音轨用 `audio-to-pcm` 的 `output_sample_rate: 32000` + `channels: 2`（音频 VAE 的采样率）

## 参考编号不能被"空端口"打乱

> A WIRED port must beat every request —— 空张量才是"这次没有"，**静默的端口会重编号后面的所有参考**。

所以：**没用的参考端口干脆不要接**，不要接一个"空"stage。三组对照要写三条流水线，不要写一条加开关。

## 端口路线的 stage 配置速查

| stage | 必填 config | 说明 |
|---|---|---|
| `load-image` | `url`（字符串或数组）| |
| `load-video` | `input_url` | 同时出视频（oport0）与音轨（oport1）|
| `video-to-rgb` | `output_dtype: "u8"` | 出 `[frames,3,H,W]` u8 |
| `image-resample` | `width` / `height` / `fit` / `algorithm` | `fit` ∈ pad / crop / stretch / manual；`algorithm` ∈ bilinear / lanczos / bicubic |
| `temporal-stack` | `mode`（video/audio）/ `group_size: 0` / `max_mb` | 帧或 PCM 堆成一个参考 |
| `audio-to-pcm` | `output_sample_rate: 32000` / `channels: 2` / `chunk_duration_s` / `max_chunk_duration_s` | |
| `video-ref-encoder` | `frames`（必须等于 `generate-video.frames`）/ `reference_image_short_edge` / `attach_audio` | |
| `save-video` | `output_url`（**不是 `path`**）| 必须接两路：rgb-to-video + audio-vae-decode |

## 已知坑

1. **`frames` 必须两处一致**（编码器 / generate-video），否则整个请求被跳过
2. **`attach_audio` 的槽位号**：≥4 条参考时容易搞错，见上
3. **参考视频过长会被截断，而且先缩放全部帧再截断**（低效）
4. **FL2VA 分区下静帧短边不同**：Ref2VA 用 2048（9 张会爆显存），FL2VA 用 768 —— 端口路线的图自带尺寸，不受这两个键影响
5. **图的短边会被上采样**：竖图按短边放大可能变成 447% 像素，单独准备成方图或匹配输出比例
