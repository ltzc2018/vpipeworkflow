---
name: vpipe-live-preview
description: 使用 vpipe 的 TAE-H3 实时预览解码器，在视频去噪过程中实时看到低分辨率画面，无需等待完整成片。适用于"先看低清预览再决定是否出正片"、"调参时快速迭代构图与运镜"、"商品场景下先确认画面再投入正片成本"等场景。本技能应在本机需要在生成过程中观察中间结果、或想降低试错成本时使用。
agent_created: true
---

# vpipe 实时预览（TAE-H3）

用 TAE-H3 这个轻量 VAE 在**每个去噪步骤之后**解出低分辨率画面，实时推到 Web UI。不用等 6 分钟才知道结果对不对。

## 何时使用

- 调提示词/构图/运镜时快速迭代
- 昂贵的长视频生成前先低成本试错
- 直播式演示

**不适用**：CLI 批处理（本技能在 CLI 下不会自动结束，见下）；最终画质评估（预览是低分辨率的 TAE 解码，与最终 VAE 解码不是一回事）。

## 原理

`preview_vae` 是一个**独立的轻量 VAE**（TAE-H3，9.9M 参数），每 N 步把当前 latent 解一次。

```
generate-video (latent) → preview_vae → preview stage → Web UI
```

配置挂在 `generate-video` 或单独的 `preview` stage 上：

| 键 | 说明 |
|---|---|
| `preview_vae` | TAE-H3 权重路径。**可以是文件、也可以是目录**（三种写法实测均可用） |
| `preview_every` | 每几步解一次。`1` = 每步 |
| `preview_max_edge` | 预览最长边（像素） |
| `preview_frames` | 预览帧数（不填则跟随输出帧数） |

TAE-H3 的规格（从日志读出）：
```
LatentPreviewer('generate-video'): taehv TAE 'models/madebyollin/taehv/taeh3.safetensors'
-- 24 latent channels, 16x spatial, 4x temporal, 9.9M params
```

## 关键前提：这是 Web UI 功能

> **CLI 下接上 `preview` stage 之后，流水线不会自己结束。**

官方文档原话：*"The `preview` stage runs until you stop the pipeline."* `preview` 是一个 **WebSocket sink（0 oports）**，没有下游消费者，流水线就一直等着。

所以：
- **正确用法**：启动 Vpipe Manager Web UI，在浏览器里跑流水线
- **CLI 跑**：需要自行终止进程，或者用 `preview_frames` 限制预览时长

## 快速开始（Web UI 路线）

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

# 1) 准备 TAE-H3（官方文档有专门的 prepare 流水线）
$VPIPE --launch ./pipelines/prepare-minimax-h3-preview.vpipeline
```

然后启动 Web UI：
```bash
open -a "Vpipe Manager"
```
在界面里选择工作目录 → Start Server → 载入 `pipelines/h3-taeh3-preview.vpipeline` → 改提示词 → 开始。

## 完整流水线

```json
{
  "id": "h3-taeh3-preview",
  "stages": [
    { "id": "model-select", "type": "model-select", "iports": [],
      "config": { "hf_dir": "local/MiniMax-H3-FL2VA-8bit" } },
    { "id": "text-prompt", "type": "text-prompt", "iports": [],
      "config": { "text": "..." } },
    { "id": "diffusion-conditioner", "type": "diffusion-conditioner",
      "iports": [ {"src":"text-prompt","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0} ],
      "config": { "unload_when_idle": "always" } },
    { "id": "minimax-h3-model-config", "type": "minimax-h3-model-config", "iports": [],
      "config": { "video_shift": 12.0, "audio_shift": 3.0, "lora": "larryvrh/MiniMax-H3-Turbo-Lora-v4-600-ema" } },
    { "id": "generate-video", "type": "generate-video",
      "iports": [ {"src":"diffusion-conditioner","oport":0}, {"src":"","oport":0},
                  {"src":"model-select","oport":0}, {"src":"","oport":0},
                  {"src":"","oport":0}, {"src":"","oport":0}, {"src":"","oport":0},
                  {"src":"","oport":0}, {"src":"","oport":0},
                  {"src":"minimax-h3-model-config","oport":0} ],
      "config": {
        "width": 512, "height": 288, "frames": 39, "fps": 24, "steps": 4, "seed": 42,
        "preview_vae": "/abs/path/to/models/madebyollin/taehv/taeh3.safetensors",
        "preview_every": 1,
        "preview_max_edge": 512,
        "preview_frames": 39,
        "unload_when_idle": "always"
      } },
    { "id": "preview", "type": "preview", "iports": [ {"src":"generate-video","oport":2} ],
      "config": {} }
  ],
  "subpipelines": []
}
```

> ⚠️ **`preview` 必须接 `generate-video` 的 `oport 2`**（预览通道）。
> 接 `oport 0`（视频 latent）或 `oport 1`（音频 latent）都不对 —— 早期版本的
> 本技能文档里写的是 `oport 0`，已修正。

**预览用的分辨率要低**：512×288 / 39 帧 / 4 步。预览本身就是为了快，不要用成片的 960×544。

## `preview_vae` 的三种路径写法（实测均可用）

| 写法 | 例子 | 说明 |
|---|---|---|
| 绝对文件 | `/Users/.../models/madebyollin/taehv/taeh3.safetensors` | 最明确 |
| 相对文件 | `models/madebyollin/taehv/taeh3.safetensors` | 相对于工作目录 |
| **相对目录** | `models/madebyollin/taehv` | 目录里自己找权重文件（推荐，文件名可能变） |

用目录写法的好处：上游改文件名时不需要改流水线。

## 一个真实的坑：静默失效

**首次运行时 TAE 预览完全没有加载，而且日志里没有任何警告。**

排查过程（值得记录，因为没有任何报错）：
1. 尝试绝对路径 → 无反应
2. 尝试相对文件 → 无反应
3. 尝试相对目录 → 无反应
4. 各种组合 `preview_frames` 有无 → 都无反应
5. 逐字节比对配置文件 → **配置本身没问题**
6. **原版重跑一次 → 正常加载并解码**

结论：这是**紧接另一个 vpipe 进程退出后的偶发时序竞态**，不是配置错误。

**判定原则**：当"配置完全正确 + 三种写法都试过 + 日志无任何错误"时，先**原版重跑一次**再改配置。本例重跑即好。

> 本条未计入上游 issue——**未能稳定复现**。但作为排查经验写在这里。

## 官方 TAE-H3 准备流程的坑

官方 `prepare-minimax-h3-preview.vpipeline` 走 `raw.githubusercontent.com` 拉权重，本机该域名 **SSL 连接失败**（连试 6 次都报错）。

**绕过办法**：改用 GitHub API 的 raw 端点手工下载：
```bash
curl -sL "https://api.github.com/repos/madebyollin/taehv/contents/taeh3.safetensors" \
  -H "Accept: application/vnd.github.raw" -o taeh3.safetensors
```
下载后**校验 sha256** 与官方一致。

同样地，`madebyollin/taeh2_1`（Krea-2 的预览 TAE）在本机也没下到，ModelScope 上不存在这个仓库。

## 预览 vs 最终成片的差异

| | 预览（TAE-H3） | 最终成片（VAE） |
|---|---|---|
| 参数 | 9.9M | H3 的完整双 VAE |
| 质量 | 低分辨率、块感明显 | 完整画质 |
| 用途 | 判断构图/运动/主体在不在 | 交付 |

**预览里看到主体在位，不代表成片里服装细节保真**。最终保真度要看 `vpipe-first-frame-to-video` / `vpipe-first-last-to-video` 里的 SSIM 数据。

## 常见坑

**1. CLI 下流水线不结束**
`preview` 是 WebSocket sink。CLI 跑必须自行终止。

**2. 预览配置写在了错误的 stage**
`preview_vae` 挂在 `generate-video` 的 config 里。写成独立的 `preview` stage 的 config 不生效。

**3. 预览分辨率设太高，失去意义**
预览每步都要解码一次。960×544 每步解一次会明显拖慢去噪。

**4. `preview_every: 1` 在慢机器上开销大**
本机 24GB 可以跑。16GB 机器建议 `preview_every: 2`。

## 参考资料

- `references/preview-setup.md` —— TAE-H3 获取与路径写法
- `references/troubleshooting.md` —— 故障排查表
- `references/i2va-preview-findings.md` —— **i2va 首帧锚定链路的完整实测报告**（2026-11-14）
- `references/cli-capture.md` —— **CLI 下把预览流抓下来做量化**（免 Web UI 手工操作）
- `assets/h3-taeh3-preview.vpipeline` —— 预览流水线（文件路径写法）
- `assets/h3-taeh3-preview-dir.vpipeline` —— 预览流水线（目录路径写法）
- `assets/pika-i2va-preview-fast.vpipeline` —— **i2va 首帧锚定 + 预览（512×288 / 39 帧，实测通过）**
- `assets/pika-i2va-preview-prod.vpipeline` —— 同上，生产规格（832×480 / 124 帧）
- `assets/pika-t2v-preview-fast.vpipeline` —— t2v 对照组（无锚定，用于量化锚定价值）
- `scripts/p4_run.py` —— 编排：起 web-ui → 载流水线 → 启动 → 抓流 → 等成片 → 停
- `scripts/ws_capture.py` —— 极简 RFC6455 客户端 + 分段拼装 fMP4
- `scripts/split_preview.py` —— 按 init 段把预览流切成独立可解码的 mp4
- `scripts/p4_beats.py` —— 切步 + 印相 + SSIM/PSNR 量化
- `scripts/p4_anchor_emergence.py` —— 锚定涌现曲线（每一步主体是否已锁死）
- `scripts/vqa-p4.sh` —— 第三方模型（LFM3-VL）复核

### 路径约定

技能资产里的 `.vpipeline` **路径相对 vpipe 工作目录**（即 `~/AI-Models/vpipe-workspace`）：

```json
"url":         ["refs/minimax-h3-reference-subject.jpg"],
"preview_vae": "models/madebyollin/taehv",
"output_url":  "out/p4-i2va-preview-fast.mp4"
```

`preview_vae` 用**目录**写法（目录里自己找权重文件），上游改文件名也不怕。
换成别的机器时，改这三处（或整体替换成绝对路径）即可。

### 脚本的路径配置

全部脚本支持环境变量覆盖，无需改代码：

| 变量 | 含义 | 默认 |
|---|---|---|
| `VPIPE_FFMPEG` | ffmpeg 可执行文件 | `PATH` 上的 `ffmpeg` → 本机 hermes 路径 |
| `VPIPE_WS` | vpipe 工作目录 | `~/AI-Models/vpipe-workspace` |
| `VPIPE_LAB` | 实验室目录（产物落盘处） | `~/WorkBuddy/vpipe-lab` |
| `VPIPE_WEBUI` | `vpipe-web-ui` 可执行文件 | `/Applications/Vpipe Manager.app/Contents/Helpers/vpipe-web-ui` |
| `VPIPE_WEBUI_PORT` | web-ui 端口 | `9876` |

---

## i2va（首帧锚定）链路：已验证可用

> 完整数据见 `references/i2va-preview-findings.md`。

**接线不用改锚定部分**，只在 `minimax-h3-model-config` 上加预览三件套，
并把 `preview` 接到 **`generate-video` 的 oport 2**：

```json
"preview_vae": "<abs>/models/madebyollin/taehv/taeh3.safetensors",
"preview_every": 1, "preview_max_edge": 512, "preview_frames": 39
```

**实测结论**（M5 Pro / 24 GB）：

| | i2va-fast | t2v 对照 | i2va-prod |
|---|---|---|---|
| 有效预览延迟 | 22.11 s | 20.26 s | **90.33 s**（成片的 24%）|
| 预览最后一拍 vs 成片（相位对齐） | SSIM 0.9338 | 0.9460 | 0.9663 |
| 预览第 1 帧 vs 锚定图 | **0.6102** | 0.1219 | 0.8872 |

**锚定在预览路径上第 1 步就锁死**（step1 SSIM 0.9534）；无锚定时 step1 只有
0.7085，要到 step3 才收敛 —— 这是首帧锚定价值的量化形态。

### 三个最容易踩的坑（另五个见 references）

1. **预览流有两个 init 段**。preview stage 采纳真实原生分辨率时会重新初始化
   fMP4 → 推第二个 init 段。**按到达顺序分段拼装**，否则前 20 秒全是坏帧。
2. **「第一个 fragment 到达」≠「能看见画面」**。头 20 秒是 640×360 / 8 kb/s 的
   **黑画面占位**，不是预览失效。有效延迟以**分辨率被采纳的时刻**为准。
3. **各拍相位不对齐**。预览是同一 clip 循环播放，每拍替换时相位会漂移。
   横向比较必须先做**相位对齐**，否则会把 0.93 误判成 0.13。
   切步用「同相位帧（n 与 n-39）在一个拍内 SSIM 0.978，跨拍骤降」。
