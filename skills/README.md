# vpipe 工作流技能包

把本机验证通过的 vpipe 生成路线固化成 7 个可复用的技能。每个技能包含：SKILL.md（中文说明 + 使用教程）、可运行的流水线模板（`assets/`）、参考资料（`references/`）、辅助脚本（`scripts/`）。

## 技能清单

| 技能 | 做什么 | 核心结论 |
|---|---|---|
| **[vpipe-text-to-image](vpipe-text-to-image/)** | 纯文本生成图片 | Z-Image-Turbo 42.5 秒 / Krea-2-Turbo 49.5 秒，24GB 上靠 residency 流式加载跑动 25–30GB 权重 |
| **[vpipe-image-edit](vpipe-image-edit/)** | 基于已有图片生成/修改 | 参考图以 **latent** 进 DiT，约束语义不约束像素；支持多参考合成 |
| **[vpipe-reference-to-video](vpipe-reference-to-video/)** | 参考图 → 视频（Ref2VA） | 主体/服装/风格从参考图继承，但**无法钉住某一帧** |
| **[vpipe-first-frame-to-video](vpipe-first-frame-to-video/)** | 单图 → 视频（i2va） | 首帧像素级保真（SSIM 0.9505），但**只保第 0 帧** |
| **[vpipe-first-last-to-video](vpipe-first-last-to-video/)** | 双图 → 插值视频 | 两端都钉住，**商品能全程保留**（全片 SSIM 0.6657 最高） |
| **[vpipe-live-preview](vpipe-live-preview/)** | TAE-H3 实时预览 | 去噪过程中实时看低清画面，Web UI 功能 |
| **[vpipe-model-prepare](vpipe-model-prepare/)** | 下载/量化/注册/回收磁盘 | 硬链接复用省 27GB；`rm` 是 shim 要用 `/bin/rm` |

## 快速选型

| 你想要 | 用哪个技能 | 为什么 |
|---|---|---|
| 生成一张商品图 | `vpipe-text-to-image` | 最快，42.5 秒 |
| 把商品图换个背景 | `vpipe-image-edit` | 参考图走 latent |
| 商品图 → 短视频，商品开头出现 | `vpipe-first-frame-to-video` | 像素级保真 |
| **商品图 → 短视频，商品全程在** | `vpipe-first-last-to-video` | **仅首帧锚定会中途丢商品** |
| 同一主体换场景换动作 | `vpipe-reference-to-video` | 主体身份从参考图继承 |
| 试参数，想先看效果 | `vpipe-live-preview` | 省时间 |

## 安装

```bash
# 用户级（所有项目可用）
cp -r vpipe-* ~/.workbuddy/skills/

# 或项目级
cp -r vpipe-* <项目>/.workbuddy/skills/
```

打包分发：
```bash
python3 <skill-creator>/scripts/package_skill.py vpipe-reference-to-video
```

## 前置环境

```bash
export VPIPE_DISABLE_TELEMETRY=1
export VPIPE_MODEL_SOURCE=modelscope   # 本机 HF 直连不通
VPIPE="/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
```

工作目录 `~/AI-Models/vpipe-workspace/`（注册表按工作目录解析，换目录要重新 prepare）。

## 已验证环境

Mac mini M5 Pro / 24 GB 统一内存 / 15 核 / macOS 27.2，vpipe `main` @ `33cda00`（源码编译）。

## 一条贯穿全部技能的经验

**日志正常 ≠ 画面正常。** 每个生成任务结束后都要抽帧目检，并用第三方模型（LFM3-VL / Qwen3.5）独立复核。判断"参考图是否生效"不能靠目视，要做消融对照 —— 而且要先问"对照组能不能产生不同结果"。

详见 `vpipe-reference-to-video/references/prompt-guide.md`。
