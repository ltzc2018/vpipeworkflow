# CLI 下把实时预览抓下来做量化

> 2026-11-14 实测通过。本文是一份**可直接照着跑**的端到端手册：
> 起服务 → 抓流 → 切段 → 切步 → 量化 → 第三方复核。
> 原理与结论见 `i2va-preview-findings.md`。

---

## 0. 为什么需要这些脚本

`preview` stage 是一个 **WebSocket sink（0 oports）**：

- CLI 下流水线**永远不会自己结束**（官方文档原话：*"The `preview` stage runs until you stop the pipeline."*）
- 浏览器里能看见画面，但你**拿不到文件**，也没法量化

所以需要自己起 web-ui、用脚本连 WebSocket 把 fMP4 落盘、再用 ffmpeg 做量化。

---

## 1. 一条命令跑完

```bash
export VPIPE_LAB=~/WorkBuddy/vpipe-lab
export VPIPE_WS=~/AI-Models/vpipe-workspace
export VPIPE_FFMPEG=$(command -v ffmpeg)

cd "$VPIPE_WS"
python3 "$VPIPE_LAB/scripts/p4_run.py" \
    --pipeline pika-i2va-preview-fast \
    --tag i2va-fast \
    --timeout 900
```

`p4_run.py` 做的事，按时间顺序：

| 步骤 | 动作 | 产物 |
|---|---|---|
| 1 | 起 `vpipe-web-ui --bind 127.0.0.1 --port 9876 --expose-native-file-system` | `logs/p4-webui-<tag>.log` |
| 2 | 轮询 `/api/health` 直到就绪（最多 90 s）| — |
| 3 | `PUT /api/log/level` → **debug** | 见下方「日志级别」小节 |
| 4 | `POST /api/pipelines/load`（路径来自 `--pipeline`）| 拿到流水线 id |
| 5 | **先**连 WebSocket 并 `watch`，**再** launch | — |
| 6 | `POST /api/pipelines/<id>/launch` | 开始生成 |
| 7 | 后台线程抓预览流 | `deliverables/p4-preview/<tag>/preview-stream.mp4` |
| 8 | 等成片文件大小连续 8 秒不变 | `out/<成片名>.mp4` |
| 9 | `POST /api/pipelines/<id>/stop` + 停线程（保证 init 段一定拼上）| — |
| 10 | 增量落盘控制台日志 | `logs/p4-pipeline-<tag>.log` |

> **顺序很重要**：WebSocket 的 `watch` 必须**早于** `launch`。
> 后端每 500 ms 轮询一次预览通道，晚 1.5 秒注册就会丢掉最前面的帧。

### 成片文件名从流水线里读

```python
for st in doc["stages"]:
    if st["type"] == "save-video":
        out_name = os.path.basename(st["config"]["output_url"])
```

**不要自己猜文件名** —— 第一版就栽在这：runner 按 `<tag>.mp4` 猜，
流水线实际写的是 `p4-i2va-preview-fast.mp4`，白等 15 分钟超时。

### 日志级别必须调到 debug

preview stage 会打 `clip #N (39 frames)` —— 这是**预览到达次数**
（= 渲染了预览的去噪步数）的精确计数，默认的 normal 级别看不到。

```
PUT /api/log/level   {"level": "debug"}
```

---

## 2. 抓下来的流长什么样

`deliverables/p4-preview/<tag>/` 里的文件：

| 文件 | 内容 |
|---|---|
| `preview-stream.mp4` | **按到达顺序拼装**的完整流（init1 + frags1 + init2 + frags2…）|
| `init-1.mp4` | 第 1 个 init 段留档（**766 B，不能单独解码**）|
| `init-2.mp4` | 第 2 个 init 段留档（同上）|
| `ws-capture.log` | 分片时间线 + 每条消息的字节数 |

### 为什么有两个 init 段

源码 `stages/audio-video/preview-stage.cc`：

- `handle_video_frame_`：第一个**真实**帧到达时采纳它的**原生分辨率**，
  与「预输入黑画面」的尺寸不同就 `build_pipeline_(W, H)` **重新初始化 fMP4**
  → 推第二个 init 段
- `handle_clip_`：`each new clip replaces it` —— 每个去噪步的 clip 替换上一个，
  然后从头循环播放

实测（i2va-fast）：

| 分段 | 触发时刻 | 分辨率 | 时长 | 码率 | 内容 |
|---|---|---|---|---|---|
| segment-1 | launch + 1.76 s | 640×360 | 20.24 s | **8 kb/s** | **纯黑占位** |
| segment-2 | launch + 22.11 s | **512×288** | 41.79 s | 2011 kb/s | 真实内容 |

**关键判据**：8 kb/s 的 640×360 只能是纯色。
所以「第一个 fragment 到达（2.24 s）」**不等于**「能看见画面（22.11 s）」。

---

## 3. 按 init 段切开

```bash
python3 "$VPIPE_LAB/scripts/split_preview.py" \
    "$VPIPE_LAB/deliverables/p4-preview/i2va-fast/preview-stream.mp4" \
    "$VPIPE_LAB/deliverables/p4-preview/i2va-fast/ws-capture.log" \
    /tmp/p4seg
```

输出：

```
segment-1: init=767B frags=39  total=31551B     -> /tmp/p4seg/segment-1.mp4
segment-2: init=766B frags=84  total=10527324B  -> /tmp/p4seg/segment-2.mp4
消耗 10558875 / 10558875 字节
```

**不切会怎样**：把两个 init 段塞进同一个 mp4，ffmpeg 会用第一段的 SPS 去解
第二段 → 满屏 `error while decoding MB`，**前 20 秒全是坏帧**。

> ⚠️ `init-1.mp4` / `init-2.mp4` 只有 766 字节，**它们是 fMP4 的初始化段，
> 不是可播放视频**。喂给 ffmpeg 会得到「0 帧」。
> **要喂给下一步的是 `segment-2.mp4`**（init + fragments 拼出来的那段）。

---

## 4. 切步：每一拍 = 一个去噪步

预览把**同一个 clip 循环播放**。切步原理：

> **同相位帧（n 与 n-39）在一个拍内几乎逐像素相同**（SSIM ≈ 0.98），
> 跨拍时同相位帧内容变了（SSIM 骤降）。

```bash
python3 "$VPIPE_LAB/scripts/p4_beats.py" \
    i2va-fast \
    /tmp/p4seg/segment-2.mp4 \
    "$VPIPE_WS/out/p4-i2va-preview-fast.mp4" \
    "$VPIPE_WS/refs/minimax-h3-reference-subject.jpg" \
    39
```

参数：`<tag> <segment2.mp4> <final.mp4> <anchor.jpg> [clip_frames]`

产出：

- `deliverables/p4-preview/<tag>/contact-sheet-beats.png` —— 每拍首帧的印相
- `logs/p4-quant-<tag>.json` —— 切步结果 + 全部量化数据

实测三次运行**都精确切出 6 个 beat = 6 个去噪步**。

---

## 5. 相位对齐（不做这一步，结论会完全错）

各拍之间**相位不对齐** —— 预览是「同一个 clip 循环播放」，每一拍被替换时相位会漂移。

未对齐时，预览 vs 成片的 SSIM 只有 **0.13–0.31**；
对齐后是 **0.93–0.97**。差了一个数量级。

`p4_beats.py` 用**双端点准则**求偏移：同时匹配成片首帧与末帧两条曲线，取联合最优。

```
相位偏移：成片 f0 ↔ 预览 f701（首帧 SSIM 0.9640 / 末帧 SSIM 0.9626）
逐帧 SSIM：均值 0.9338  首 0.9357  中 0.9427  末 0.9373
```

> **不要用「单帧 SSIM argmax」选相位。** 画面同质时所有候选都在 0.93 上下，
> **必错**。用双端点准则 + 目检裁决。

---

## 6. 锚定涌现曲线

```bash
python3 "$VPIPE_LAB/scripts/p4_anchor_emergence.py" i2va-fast 39 /tmp/p4seg/segment-2.mp4
```

原理：在每一拍内定位「相位 0 帧」（= clip 的第 0 帧 = 视频首帧的位置），
量它与**成片首帧**的 SSIM —— 这就是「锚定主体在第几步就已经在预览里可辨认」。

产出 `contact-sheet-anchor-emergence.png`（相位一致的逐拍收敛印相）
+ `logs/p4-emergence-<tag>.json`。

---

## 7. 第三方模型复核

```bash
bash "$VPIPE_LAB/scripts/vqa-p4.sh" i2va-fast
```

用 LFM3-VL-2B（**独立于生成链路**）问三个问题：
主体每步是否在场 / 服装每步是否保留 / 预览首帧是不是参考图那只猫。

---

## 8. 这条链路的实测结论

| 对照 | i2va-fast | t2v-fast（无锚定）| i2va-prod |
|---|---|---|---|
| 有效预览延迟 | 22.11 s | 20.26 s | **90.33 s**（成片的 24%）|
| 成片首帧 vs 锚定图 | **0.9736**（35.95 dB）| 0.4293（10.41 dB）| **0.9361**（30.38 dB）|
| 预览第 1 帧 vs 锚定图 | **0.6102** | 0.1219 | 0.8872 |
| 预览最后一拍 vs 成片（对齐后）| **0.9338** | 0.9460 | **0.9663** |

**锚定涌现曲线**（每一步在「视频首帧位置」上与成片首帧的 SSIM）：

| 步骤 | i2va-fast（有锚定）| t2v-fast（无锚定）|
|---|---|---|
| step1 | **0.9534** | **0.7085** |
| step2 | 0.9563 | 0.7099 |
| step3 | 0.9590 | **0.9238** |
| step4 | 0.9610 | 0.9552 |
| step5 | 0.9636 | 0.9675 |
| step6 | 0.9640 | 0.9678 |

**有锚定：第 1 步就已经正确，后面 5 步只是把细节磨清楚。**
**无锚定：第 1–2 步还在漂移，到第 3 步才收敛。**

带货场景直接对应：商品图锚定后，**第 1 步的预览就能判断商品有没有跑偏**，
不锚定时至少要看第 3 步 —— 省下的正是最贵的那几步。

---

## 9. 什么时候值得用这条链路

| 值得 | 不值得 |
|---|---|
| 生产规格（832×480）成片要 6 分钟，先花 90 秒看个大概 | 只要最终画质，30 秒的小图够了 |
| 要判断锚定有没有生效 | 要判断服装细节/材质保真（TAE 只有 9.9M 参数，测不出来）|
| 要横向比较多个提示词版本 | 批量离线跑（每轮都要开 web-ui，开销大）|

**先看预览再出正片**，本质是**用 24% 的时间砍掉 80% 的无效重跑**。
