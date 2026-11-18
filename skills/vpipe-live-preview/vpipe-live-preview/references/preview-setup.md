# TAE-H3 预览解码器：获取、接线与路径写法

> 2026-11-14 本机实测 · 模型：`madebyollin/taehv` · `taeh3.safetensors`

## 1. 它是什么

TAE-H3 是一个**独立的轻量 VAE**（9.9M 参数），在每个去噪步骤之后把当前 latent
解成低分辨率画面，推给 Web UI。

规格（从日志读出）：

```
LatentPreviewer('generate-video'): taehv TAE
  'models/madebyollin/taehv/taeh3.safetensors'
  -- 24 latent channels, 16x spatial, 4x temporal, 9.9M params
```

**它不是 H3 的 VAE**，两者参数与输出质量都不一样（见 SKILL.md 的对照表）。

---

## 2. 获取（官方 prepare 流水线在本机会失败）

官方 `prepare-minimax-h3-preview.vpipeline` 走 `raw.githubusercontent.com` 拉权重，
本机该域名 **SSL 连接失败**（连试 6 次都报错）。

### 绕过：GitHub API 的 raw 端点

```bash
cd ~/AI-Models/vpipe-workspace/models/madebyollin/taehv
curl -sL "https://api.github.com/repos/madebyollin/taehv/contents/taeh3.safetensors" \
  -H "Accept: application/vnd.github.raw" -o taeh3.safetensors

# 必须校验 sha256
shasum -a 256 taeh3.safetensors
```

下载完**自己把目录写进注册表**，或者让 vpipe 的 `model-select` 用目录路径直接指过去。

### 同样的坑还有一处

`madebyollin/taeh2_1`（Krea-2 的预览 TAE）在本机**也没下到**，
ModelScope 上不存在这个仓库 → Krea-2 的 `krea-2-preview.vpipeline` 在本机不可用。

---

## 3. `preview_vae` 的三种路径写法（**实测均可用**）

| 写法 | 例子 | 说明 |
|---|---|---|
| 绝对文件 | `/Users/<user>/AI-Models/vpipe-workspace/models/madebyollin/taehv/taeh3.safetensors` | 最明确 |
| 相对文件 | `models/madebyollin/taehv/taeh3.safetensors` | 相对于工作目录 |
| **相对目录** | `models/madebyollin/taehv` | 目录里自己找权重文件（**推荐**） |

**推荐目录写法**：上游改文件名时不需要改流水线。
本机两种都跑过：
`assets/h3-taeh3-preview.vpipeline`（文件路径写法）、
`assets/h3-taeh3-preview-dir.vpipeline`（目录路径写法）。

---

## 4. 接线：配置挂在 `generate-video` 上

```json
{
  "id": "generate-video",
  "type": "generate-video",
  "iports": [ /* ... */ ],
  "config": {
    "width": 512, "height": 288, "frames": 39, "fps": 24, "steps": 4, "seed": 42,
    "preview_vae": "models/madebyollin/taehv",
    "preview_every": 1,
    "preview_max_edge": 512,
    "preview_frames": 39,
    "unload_when_idle": "always"
  }
}
```

| 键 | 说明 |
|---|---|
| `preview_vae` | TAE-H3 权重路径（文件或目录） |
| `preview_every` | 每几步解一次。`1` = 每步 |
| `preview_max_edge` | 预览最长边（像素） |
| `preview_frames` | 预览帧数（不填则跟随输出帧数） |

下游接一个 `preview` stage：

```json
{ "id": "preview", "type": "preview",
  "iports": [ { "src": "generate-video", "oport": 0 } ], "config": {} }
```

**坑**：把这些键写在独立的 `preview` stage 的 config 里**不生效** ——
它们必须在 `generate-video` 的 config 里。

---

## 5. 为什么必须用 Web UI

官方文档原话：*"The `preview` stage runs until you stop the pipeline."*

`preview` 是 **WebSocket sink（0 oports）**，没有下游消费者 → 流水线一直等。

- **正确用法**：启动 Vpipe Manager Web UI，在浏览器里跑
- **CLI 跑**：需要自行终止进程，或用 `preview_frames` 限制预览时长

```bash
cd ~/AI-Models/vpipe-workspace
export VPIPE_DISABLE_TELEMETRY=1 VPIPE_MODEL_SOURCE=modelscope
vpipe-web-ui --bind 127.0.0.1 --port 9876
```

启动会打印 8 位访问密钥（本机 localhost 免密钥）。
启动自检项：Local network / Full Disk Access / Microphone / Camera 权限状态。

---

## 6. 预览参数怎么选

| 用途 | width × height | frames | steps | preview_every |
|---|---|---|---|---|
| **构图/运镜试错** | 512 × 288 | 39 | 4 | 1 |
| 快速看主体在不在 | 512 × 288 | 39 | 4 | 2 |
| 半成品预览 | 832 × 480 | 39 | 6 | 2 |

**预览分辨率要低**：预览每步都要解码一次，960×544 每步解一次会明显拖慢去噪。
24 GB 机器 `preview_every: 1` 可以跑；16 GB 建议 `preview_every: 2`。

**帧数对齐**：官方 H3 的帧数必须整除到 `17n + 5`。
`frames: 39` = 17×2+5 ✔；`frames: 48`（2 秒 @24fps）会被截成 **39**。

---

## 7. 静默失效（踩过，没有报错）

**首次运行时 TAE 预览完全没有加载，日志里没有任何警告。**

排查过程（记录在案，因为**没有任何报错**）：

1. 绝对路径 → 无反应
2. 相对文件 → 无反应
3. 相对目录 → 无反应
4. `preview_frames` 有无的各种组合 → 都无反应
5. 逐字节比对配置文件 → **配置本身没问题**
6. **原版重跑一次 → 正常加载并解码**

结论：这是**紧接另一个 vpipe 进程退出后的偶发时序竞态**，不是配置错误。

**判定原则**：当「配置完全正确 + 三种写法都试过 + 日志无任何错误」时，
先**原版重跑一次**再改配置。

> 本条未计入上游 issue —— **未能稳定复现**。但作为排查经验保留。

---

## 8. 已验证的四种路径写法（流水线资产）

本机把 `preview_vae` 的四种写法各跑了一条流水线，全部能加载并解码：

| 资产 | 写法 |
|---|---|
| `assets/h3-taeh3-preview.vpipeline` | 相对文件 `models/madebyollin/taehv/taeh3.safetensors` |
| `assets/h3-taeh3-preview-dir.vpipeline` | 相对目录 `models/madebyollin/taehv` |
| `assets/h3-taeh3-preview-abs.vpipeline` | 绝对文件路径 |
| `assets/h3-taeh3-preview-relfile.vpipeline` | 相对文件（另一种相对写法） |

**四个都跑通** —— 说明 vpipe 对 `preview_vae` 的路径解析是宽松的。

---

## 9. 预览 ≠ 成片

| | 预览（TAE-H3） | 最终成片（VAE） |
|---|---|---|
| 参数 | 9.9M | H3 的完整双 VAE |
| 质量 | 低分辨率、块感明显 | 完整画质 |
| 能回答的问题 | 构图对不对？主体在不在？运镜动没动？ | 服装细节保不保真？ |

**预览里主体在位，不代表成片里服装细节保真**。
最终保真度要看 `vpipe-first-frame-to-video` / `vpipe-first-last-to-video` 里的 SSIM 数据
（首帧锚定 0.9505 / 首尾帧锚定 0.9500 / 参考生视频只有 0.49–0.52）。
