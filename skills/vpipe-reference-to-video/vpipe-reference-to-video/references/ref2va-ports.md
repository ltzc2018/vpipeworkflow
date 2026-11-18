# Ref2VA 端口与序列布局

## 序列对比

| partition | 序列布局 |
|---|---|
| **FL2VA** | `[text | keyframe conditions | target audio | target video]` |
| **Ref2VA** | `[text | reference blocks | target audio | target video]` |

**没有任何槽位能把参考绑定到输出的第 0 帧。** Ref2VA 无法钉住某一帧。

## video-ref-encoder 的端口

| 端口 | 方向 | 内容 |
|---|---|---|
| 0 | in | 提示词 |
| 1 | in | 可选的 `model-select` |
| 2–7 | in | 可选的 `ref1`..`ref6`——以张量形式给出的参考 |
| 0 | out | 条件信息 → `generate-video` 的 **0 号端口** |
| 1 | out | 参考视频行 → `generate-video` 的 **7 号端口** |
| 2 | out | 参考音频行 → `generate-video` 的 **8 号端口** |

## generate-video 的端口

| 端口 | 用途 |
|---|---|
| 0 | 条件（Ref2VA 的条件信息在这里） |
| 1 | — |
| 2 | 模型选择 |
| 3 | 文本/多模态条件（FL2VA 的文本条件在这里） |
| 4 | — |
| 5 | **首帧 keyframe**（FL2VA） |
| 6 | **末帧 keyframe**（FL2VA） |
| 7 | 参考视频行（Ref2VA） |
| 8 | 参考音频行（Ref2VA） |
| 9 | — |
| 10 | 模型配置（`minimax-h3-model-config`） |

## 两种交付参考的方式

### 方式一：文件列表（写在 `references` 配置里）

```json
"references": ["subject.png", "motion.mp4", "voice.wav"]
```

由编码器自己打开文件。**视频和它的音轨必须从同一个容器出来**，这样同步关系才成立。

### 方式二：张量端口（ref1..ref6）

给文件列表无法指称的参考：刚生成的静帧、裁剪的画面、从未落盘的视频。**也能自己决定几何尺寸。**

两者可自由混用：端口参考的编号排在列表**之后**，上限（9 图 / 3 视频 / 3 音频 / 共 12）作用于两者的并集。

## 端口路线的完整例子

```
load-image → image-resample(1024×1024)                              → ref1
load-video ┬→ video-to-rgb → image-resample(1344×768) → temporal-stack → ref2
           └→ audio-to-pcm(32000, stereo) → temporal-stack             → ref3
```

四个承重细节：

1. **一个 `load-video` 同时喂两条流** —— 视频和音轨从同一容器一起出来，同步论证被保留
2. **`attach_audio: [3]`** —— 让 ref3 的音频成为它前一个参考的音轨，保持 `<Video 1>` + `<Audio 1>` 配对。注意这个数字是**参考编号**（1..6），不是输入端口索引：ref1 是 2 号输入端口
3. **`channels: 2`** —— 承载真正的立体声
4. **`max_mb: 384`** —— 124 帧 @ 1344×768 是 366 MiB，超过默认 256 MiB，否则会被截到 86 帧并告警

## 张量的类型由维数决定

| 你发送什么 | 维数 | sideband |
|---|---|---|
| 音频 | `[N]` 或 `[channels, N]` f32 | `sr` / `sample_rate` —— **必需** |
| 一张图片 | `[3, H, W]` u8 | — |
| 一段视频 | `[frames, 3, H, W]` u8 | `fps` —— **必需** |

单帧视频是 `[1, 3, H, W]`，静帧是 `[3, H, W]` —— 这是**不同的请求**，不用猜。

**速率是必需的、从不取默认值。** 音频用 **32000 Hz**（音频 VAE 的采样率）。一段未被统一的 44.1 kHz 音轨会被当成 32 kHz 编码 —— 快 1.38 倍、音高升高四度，**所有形状依然合法**，不会有任何东西报错。

可选 sideband：`short_edge` 设定这一个参考的画布。

## 画布默认值

| 键 | 默认 | 作用对象 |
|---|---|---|
| `reference_image_short_edge` | **2048** | 静帧按自己短边编码，无总像素上限 |
| `reference_video_short_edge` | **768** | 参考视频画布 |
| `reference_video_max_pixels` | 1032192 | 参考视频像素上限 |

**2048 下单张静帧就是 121 个 VAE 图块，而允许九张。** 任何通过 `references` 列表喂入的静帧都应该调低到 1024。

这两个键是**按种类的默认值，只作用于 `references` 列表** —— 从端口到达的参考已自带 `short_edge`，永远到不了它们。

## 编码器的裁剪日志

编码器每改动一个参考的形状都会输出文字警告，三种削减**特意分开计数**：

```
reference 1 fitted -- rescaled 1920x1080 -> 1344x736 (48% of the pixels),
  resampled 30 -> 24 fps (18 frame(s) dropped),
  truncated 72 -> 39 frames (54% of the clip)
```

- 帧率重采样：无论视频是否同时太长都会丢整帧
- 截断：靠 `frames` 解决
- 缩放：靠画布相关的键解决

一个什么都不需要改的参考会以 debug 级别记为 *taken as given* —— 自己把尺寸设好之后，这就是应该追求的结果。
