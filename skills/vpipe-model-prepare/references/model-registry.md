# vpipe 模型注册表与 `model_variant` 匹配规则

> 2026-11-13 ~ 11-14 实测 · 源码：`vpipe-lab/repo/vpipe/stages/model-catalog.cc`、`model-detect.cc`、`model-register-stage.cc`

## 1. 注册表在哪

```
~/AI-Models/vpipe-workspace/
├── data.mdb  lock.mdb    ← LMDB 注册表（路径 = 工作目录）
└── models/                ← 权重目录
```

**注册表按工作目录解析**。换个工作目录 = 一套全新的模型，必须全部重新 prepare。

**只有 `model-quantize` 和 `model-register` 会写注册表**；
`model-select` 只读不写（它只是"选一个"）。

---

## 2. 三种 stage 的分工

| stage | 做什么 | 写注册表？ |
|---|---|---|
| `model-fetch` | 从 HF/ModelScope 下载 + 校验 + 注册 | ✅ |
| `model-quantize` | 量化 + 注册产物 | ✅ |
| `model-register` | 把**已经在磁盘上**的目录注册进表（不下载） | ✅ |
| `model-select` | 在流水线里选一个模型 | ❌ |

### `model-register` 的配置

```json
{
  "id": "register",
  "type": "model-register",
  "iports": [],
  "config": {
    "model_dir": "/abs/path/to/models/videorebirth/hyperflow",
    "key": "videorebirth/hyperflow-ref2va",
    "model_type": "minimax-h3-lora",
    "overwrite_existing": false
  }
}
```

| 键 | 说明 |
|---|---|
| `model_dir` | 磁盘目录（**必填**，绝对路径最稳） |
| `key` | 注册键；留空则取路径最后两段拼成 `<owner>/<repo>` |
| `model_type` | 覆盖**自动检测**的运行时提示（`minimax-h3-lora` / `boogu-image` / …） |
| `overwrite_existing` | 默认关：**不允许同一个键被另一个目录接管**；重新注册**同一个**目录是幂等的，不用开 |

**实测（注册 HyperFlow 的 Ref2VA 别名）**：

```
[INFO] ModelRegisterStage('register'): registered 'videorebirth/hyperflow-ref2va'
  -> '/Users/minichen/AI-Models/vpipe-workspace/models/videorebirth/hyperflow'
  [minimax-h3-lora, by config-key] - -> -
```

---

## 3. `model_variant` 的匹配规则（踩过两次）

`model-fetch` 的 variant 匹配是**逐字段精确/子串比对**，字段只有四个：

```
version  /  variant  /  name  /  model_type
```

### 错误写法（用的是 catalog 的**显示名**，匹配 0 个）

```json
"model_variant": "Edit-2511 20B [bf16 (Qwen)]"
```
```
[ERROR] model_variant 'Edit-2511 20B [bf16 (Qwen)]' matches 0 of the 1 models
        published from Qwen/Qwen-Image-Edit-2511
```

### 正确写法（用 `model_type`）

```json
"model_variant": "qwen-image-edit"
```

### 为什么显示名不能直接用

源码 `stages/model-catalog.cc:3546` `catalog_pick_variant` 的匹配是逐字段进行的，
**没有任何一个字段等于那个显示串** —— 显示串是这四项的拼接。
`model_type` 是其中唯一稳定、唯一可用的字段。

> **这本身是一条可提交给上游的 issue**（已写进 `report/issues/issue-6.md`）：
> 错误提示应该列出**可直接使用的取值**（四个字段各自的值），而不是拼接后的显示名。

### `variant` 留空的前提

`variant` 留空时，要求该仓库**只有一个**候选，否则报 `matches 0 of the N models published from ...`。

---

## 4. 同一份权重注册成多个键（HyperFlow 的做法）

HyperFlow 官方**一个文件覆盖两个 partition**（`transformer` 与 `transformer_ref`），
catalog 里因此登记了两次：

```cpp
{.hf_path = "videorebirth/hyperflow", .parent_model_type = "minimax-h3-fl2va",
 .name = "videorebirth/hyperflow"},
{.hf_path = "videorebirth/hyperflow", .parent_model_type = "minimax-h3-ref2va",
 .name = "videorebirth/hyperflow-ref2va"},
```

权重头里的元数据自证：

```
tasks = ["t2va", "fl2va", "ref2va"]
compatible_subfolders = ["transformer", "transformer_ref"]
hyperflow_sigmas = [1.0, 0.931506, 0.839236, 0.703462, 0.5, 0.296538, 0.160764, 0.068494, 0.0]
hyperflow_gate = 0.25
hyperflow_video_shift = 12.0   hyperflow_audio_shift = 3.0
```

**运行时不需要真的注册第二个键**：`lora` 字段接受
「注册键 / 含单个 .safetensors 的目录 / 文件直路径」三种写法，
直路径也能走 flow-map 逻辑（实测 `lora_scale: 1.0` 与 `0.0` 都正常）。
但注册别名后**选择器里能直接选**，体验更好。

---

## 5. 已知缺陷

| # | 内容 | 表现 |
|---|---|---|
| **#15** | 官方 `prepare-minimax-h3-8bit.vpipeline` 的 `quant-dit` 写 `src_model: "Comfy-Org/MiniMax-H3"`，而 `fetch` 注册名是 `Comfy-Org/MiniMax-H3-FL2VA` | **源永远找不到，流水线静默 drain**（当前 main 已修） |
| **#49** | 非 Comfy-Org 来源的权重无法写 config | 量化只完成一半 |
| 上游单测 | 102 条钉住条目里 **3 条识别不出**：`videorebirth/hyperflow`、`videorebirth/hyperflow-ref2va`、`PrunaAI/P-H3-Image-no-dit` | 目录里有条目，**detector 签名表没覆盖** |
| 上游单测 | `relaunch_sweep.every_registered_source_is_covered` | 新增 stage 没加进测试清单（测试维护滞后） |

**对策**：给 `model-register` 显式写 `model_type`（见 §2）即可绕开 detector 的签名表缺口。

---

## 6. 自查命令

```bash
cd ~/AI-Models/vpipe-workspace
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"

$VPIPE --list-models | head -50          # 列出注册表
$VPIPE --list-pipelines | head -50        # 列出可用流水线
```

运行日志里每一次 `model registry: '<key>' -> '<path>'` 都说明这次查表命中了。
**如果日志里出现 `matches 0 of the N models published from ...`，就是 `model_variant` 写错了**
（见 §3）。
