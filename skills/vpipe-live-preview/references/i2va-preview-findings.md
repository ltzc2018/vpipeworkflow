# i2va（首帧锚定）链路接实时预览 —— 实测报告

> 2026-11-14 · Mac mini M5 Pro / 24 GB · vpipe `0.1 (9db5dd7*0)`
> 完整报告见 `vpipe-lab/report/vpipe-H3-部署与测试报告.md` 第 13.8 节

## 一句话结论

**可行，而且是「白拿」的。** 首帧锚定链路接 TAE-H3 实时预览没有降级：
预览延迟只比纯文生多 1.85 秒（多出来的是首帧的 `vae-encode`），
而预览能给出「锚定是否生效」的**第 1 步**判据。

## 关键数字

| | i2va-fast | t2v 对照 | i2va-prod |
|---|---|---|---|
| 规格 | 512×288 / 39帧 / 6步 | 同左 | 832×480 / 124帧 / 6步 |
| 成片耗时 | 64.3 s | 58.7 s | 374.3 s |
| **有效预览延迟** | **22.11 s** | **20.26 s** | **90.33 s**（占成片 24%）|
| 预览最后一拍 vs 成片（相位对齐） | SSIM 0.9338 | SSIM 0.9460 | SSIM 0.9663 |
| 成片首帧 vs 锚定图 | 0.9736 / 35.95 dB | 0.4293 / 10.41 dB | 0.9361 / 30.38 dB |
| **预览第 1 帧 vs 锚定图** | **0.6102** | **0.1219** | **0.8872** |

### 锚定涌现曲线（每一拍在「视频首帧位置」与成片首帧的 SSIM）

| 步骤 | i2va-fast（有锚定）| t2v（无锚定）|
|---|---|---|
| step1 | **0.9534** | **0.7085** |
| step2 | 0.9563 | 0.7099 |
| step3 | 0.9590 | **0.9238** |
| step6 | 0.9640 | 0.9678 |

**这就是首帧锚定价值的量化形态**：有锚定时第 1 步的首帧就已经正确；
没有锚定时第 1–2 步的首帧还在漂移，要到第 3 步才收敛。

## 接线（相对已验证的 i2va 流水线只加这些）

```json
"minimax-h3-model-config": {
  "video_shift": 12.0, "audio_shift": 3.0,
  "lora": "Pika-Labs/Pika-H3-Flex-fl2va", "lora_scale": 1.0,
  "preview_vae": "<abs>/models/madebyollin/taehv/taeh3.safetensors",
  "preview_every": 1, "preview_max_edge": 512, "preview_frames": 39
}
"preview": { "type": "preview", "iports": [ {"src": "generate-video", "oport": 2} ] }
```

`preview` 接的是 **`generate-video` 的 oport 2**（不是 oport 0）。
i2va 的锚定接线（`load-image → image-resample → vae-encode-first`）**完全不用改**。

## 八个坑

### 1. 预览流有**两个 init 段**（最容易踩）

preview stage 在「采纳真实原生分辨率」时会**重新初始化 fMP4**，推第二个 init 段：

| 分段 | 时刻 | 分辨率 | 码率 | 内容 |
|---|---|---|---|---|
| segment-1 | launch+1.76s | 640×360 | **8 kb/s** | **纯黑占位** |
| segment-2 | launch+22.11s | 512×288 | 2011 kb/s | 真实内容 |

把两个 init 段拼进同一个 mp4 → ffmpeg 用第一段的 SPS 解第二段 → 满屏
`error while decoding MB`，**前 20 秒全是坏帧**。
**必须按到达顺序分段拼装**，分析时再按 init 边界切开。

源码：`stages/audio-video/preview-stage.cc` → `handle_video_frame_` →
「First real frame: adopt its native resolution (re-init the fMP4 stream if it
differs from the pre-input black size)」。

### 2. 「第一个 fragment 到达」≠「能看见画面」

第一个 fragment 在 launch+2.24s 到，但那是**黑画面占位**。
**有效预览延迟要以分辨率被采纳的时刻为准**（本机 22.11 s）。
判据：**码率**——8 kb/s 的 640×360 只能是纯色。

### 3. 各拍**相位不对齐**（最隐蔽）

预览把同一个 clip 循环播放，每一拍替换时相位会漂移。
**横向比较各拍必须先做相位对齐**，否则会把「预览与成片不像」当成结论
（未对齐 SSIM 只有 0.13–0.31，对齐后 0.93–0.97）。

切步原理：**同相位帧（n 与 n-39）在一个拍内几乎逐像素相同**（SSIM 0.978），
跨拍骤降 → 用它切分，三次运行都精确切出 6 个 beat = 6 个去噪步。

### 4. `ffmpeg -i a.png … a.png` 会毁掉输入

输入输出同路径 → ffmpeg 先截断输出文件 → 比较到的是坏图。
曾让整条对齐曲线**系统性偏低 0.09**（0.8774 vs 真值 0.9338）。
**输出必须换文件名。**

### 5. `select` 拼上百个 OR 项会 OOM

`select='eq(n,1)+eq(n,2)+…'` 拼 124 项 → `Cannot allocate memory`。
改用单表达式：`not(mod(n,39))`（取所有循环首帧）、`between(n,A,B)`（取连续区间）。

### 6. 每抽一帧都整段解码

71 MB / 6807 帧的 prod 流抽 124 帧 = 124 次全量解码，会被系统 kill。
**一次解码批量抽帧**（`-fps_mode passthrough` + `%05d.png`）。

### 7. 单帧 SSIM argmax 选相位**必错**

画面同质时所有候选都在 0.93 上下，argmax 会选到偶然匹配。
用**双端点准则**（同时匹配成片首帧与末帧两条曲线，取联合最优），
再用目检裁决。相机会骗人，SSIM 单点也会骗人。

### 8. runner 猜的成片名与流水线 `output_url` 不一致

白等 15 分钟超时。**从流水线 JSON 里读 `save-video` 的 `output_url`。**

## 怎么把预览抓下来（CLI 路线）

`preview` 是 WebSocket sink，CLI 下流水线不会结束。Web UI + 自写 RFC6455 客户端：

```bash
"/Applications/Vpipe Manager.app/Contents/Helpers/vpipe-web-ui" \
  --bind 127.0.0.1 --port 9876 --expose-native-file-system
```

WebSocket 路径 `/api/ui/view/preview/ws`，先发
`{"m":"watch","pipeline":"<id>","stage":"preview"}`，然后：
- 文本帧 → JSON 控制消息（`waiting` / `playing` / `config` / `gone`）
- 二进制帧 → 4 字节小端头长度 + JSON 头（`{"m":"init"|"fragment"|"image"}`）+ 负载

`init` 与 `fragment` 是 fMP4 的分段，**按到达顺序拼**（见坑 1）。

完整实现见 `vpipe-lab/scripts/ws_capture.py` 与 `scripts/p4_run.py`。

## 预览能判断什么 / 不能判断什么

| 能判断 | 不能判断 |
|---|---|
| 构图、主体在不在场 | 服装细节保真度（TAE 只有 9.9M 参数）|
| 运动方向、机位变化 | 材质纹理、缝线等高频细节 |
| **锚定是否生效（第 1 步就能看）** | 最终画质（必须看成片）|
| 值不值得重跑 | |

第三方模型（LFM3-VL-2B）独立复核：对 i2va 回答「服装在每一步都保留」
「是同一只猫，服装、外观、姿态与参考图一致」；对 t2v 对照组回答
「是另一只猫，与参考图不一致」「服装并未在每一步都保留」——**反证成立**。
