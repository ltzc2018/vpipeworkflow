# vpipe 工作流集

> 本机（Mac mini M5 Pro / 24 GB / macOS 27.2）验证通过的 [vpipe](https://github.com/tgo-app-dev/vpipe) 生成工作流，固化为可复用的技能包。
>
> 上游：`tgo-app-dev/vpipe`（`main` @ `33cda00`，本机源码编译版 `0.1 (9db5dd7*0)`）
> 文档来源：官方 `docs/MINIMAX-H3-zh-cn.md`、26 个 release、30 条 issue，以及 YouTube / 社区实测资料

---

## 目录

| 路径 | 内容 |
|---|---|
| [`skills/`](skills/) | **7 个技能包**，每个含 SKILL.md（中文说明 + 使用教程）、流水线模板、参考资料、脚本 |
| [`pipelines/`](pipelines/) | 全部可运行的 `.vpipeline` 流水线 |
| [`scripts/`](scripts/) | 保真度量化、VQA 批处理、拼图等辅助脚本 |
| [`docs/`](docs/) | 部署与测试报告（760 行）、上游 issue 提案（5 条 + 可提交单文件）、后续计划任务清单 |

---

## 技能一览

| 技能 | 做什么 | 实测耗时 |
|---|---|---|
| [`vpipe-text-to-image`](skills/vpipe-text-to-image/) | 文生图 | Z-Image-Turbo **42.5 秒** / Krea-2-Turbo **49.5 秒** |
| [`vpipe-image-edit`](skills/vpipe-image-edit/) | 图生图、参考图编辑、多参考合成 | — |
| [`vpipe-reference-to-video`](skills/vpipe-reference-to-video/) | 参考图 → 视频（Ref2VA） | **6 分 49 秒** |
| [`vpipe-first-frame-to-video`](skills/vpipe-first-frame-to-video/) | 单图 → 视频（i2va） | **5 分 59 秒** |
| [`vpipe-first-last-to-video`](skills/vpipe-first-last-to-video/) | 双图 → 插值视频 | **8 分 41 秒** |
| [`vpipe-live-preview`](skills/vpipe-live-preview/) | TAE-H3 实时预览 | 每步一次 |
| [`vpipe-model-prepare`](skills/vpipe-model-prepare/) | 下载 / 量化 / 注册 / 磁盘回收 | 硬链接复用省 **27 GB** |

### 安装

```bash
cp -r skills/vpipe-* ~/.workbuddy/skills/     # 用户级
# 或 cp -r skills/vpipe-* <项目>/.workbuddy/skills/   # 项目级
```

---

## 三条最重要的实测结论

### 1. 参考与锚定是两条互斥的路线

| 需求 | 用哪条 | 依据 |
|---|---|---|
| 主体身份保留、换场景换动作 | **参考生视频**（Ref2VA） | 参考图决定主体长什么样 |
| 商品图 → 短视频，开头出现 | **首帧锚定** | 首帧 SSIM 0.9505 |
| **商品要在整段片子里都在** | **首尾帧锚定** | 仅首帧锚定会中途丢商品 |

**实测反证**：仅首帧锚定时，深蓝牛仔外套在第 20–40 帧之间彻底消失、画面整体重构（SSIM 从 0.95 断崖到 0.42）。只有首尾帧锚定才全程保留。

> 官方文档明写：**参考与关键帧互斥** —— Ref2VA 的序列是 `[text | reference blocks | target audio | target video]`，没有任何槽位能把参考绑到输出第 0 帧。

### 2. 参考生视频做的是语义替换，不是像素重建

| 视频 | 首帧 SSIM | 全片平均 |
|---|---|---|
| 参考生视频（有参考） | 0.5245 | 0.5120 |
| 参考生视频（**无参考对照**） | 0.5805 | **0.5718** |

「有参考」的 SSIM **低于**「无参考对照」—— 说明参考图**不是把输出往参考图拉，而是改写主体本身**。

### 3. 消融实验必须先问「对照组能不能产生不同结果」

第一版实验用「姜黄猫」做参考图，**无参考对照组也出姜黄虎斑猫** —— 场景先验太强，实验**不可证伪**。

换成**水彩插画风格的黑白熊猫**后立刻可区分。提示词里没有「熊猫」二字，但 LFM3-VL 与 Qwen3.5 两个独立模型都把输出判成「黑白熊猫」。

> **换一个模型先验不可能产出的参考主体，比换任何指标都管用。**

---

## 快速上手

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope      # 本机 HF 直连不通

VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

# 准备模型
$VPIPE --launch ./pipelines/prepare-minimax-h3-8bit.vpipeline
$VPIPE --launch ./pipelines/prepare-pika-h3-flex.vpipeline

# 出片（参考生视频）
$VPIPE --launch ./pipelines/pika-ref2va-ablation.vpipeline
```

---

## 本机实测数据

| 项 | 值 |
|---|---|
| 机器 | Mac mini M5 Pro / 24 GB 统一内存 / 15 核 / macOS 27.2 |
| 文生视频（4 步 Turbo LoRA） | 5 分 50 秒 · 960×544 / 124 帧 / 5.18 s + AAC |
| 参考生视频（Pika Ref2VA） | 6 分 49 秒 · 832×480 / 124 帧 |
| 首帧图生视频 | 5 分 59 秒 · 首帧 SSIM 0.9505 / PSNR 31.11 dB |
| 首尾帧插值 | 8 分 41 秒 · 全片平均 SSIM 0.6657（四类最高） |
| 文生图 Z-Image-Turbo | 42.5 秒 · 8 步 no-cfg |
| 文生图 Krea-2-Turbo | 49.5 秒 · 8 步 euler+simple |
| LFM3-VL-2B VQA | prefill 5,626 tok/s · decode 50.6 tok/s |
| Qwen3.5-4B-MLX-4bit | prefill 1,568 tok/s · decode 83.0 tok/s |
| 单元测试 | 3464 条通过 3460 条（4 条为上游缺陷 + ffmpeg 构建差异） |

**24 GB 上跑 25–30 GB bf16 权重**靠的是 vpipe 的 residency 流式加载（`plan_streaming`），不换内存、不崩。

---

## 踩坑速查

| 症状 | 根因 | 修法 |
|---|---|---|
| 流水线秒退、无产出 | `save-video` 用了 `path` | 改 **`output_url`** |
| 同上 | `save-video` 只接一路输入 | 补 `audio-vae-decode` → 端口 1 |
| `the layout reserves N rows but the encoder packed 0` | 两个 stage 的 `frames` 不一致 | 让它们**完全相等** |
| `model_variant 'X' matches 0 of the 1 models` | variant 逐字段匹配 | 用 **`model_type`** |
| `rm` 后 `df` 没变 | `rm` 是 safe-delete shim | **`/bin/rm`** |
| 重任务被杀、日志无错消失 | 并行下载的 IO 竞争 | 重任务**串行** |

完整排查表见各技能的 `references/troubleshooting.md`。

---

## 许可与来源

- 工作流、脚本、文档：本仓库（MIT）
- 上游 vpipe：Apache-2.0 — https://github.com/tgo-app-dev/vpipe
- 模型权重各有许可，以各自模型卡为准。本仓库**不含任何模型权重**。
