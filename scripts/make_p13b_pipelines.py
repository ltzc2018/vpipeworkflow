#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P13b · `sigmas`（ComfyUI `er_sde` σ 表）网格对照 —— 流水线生成器

## 为什么要重做第 3 轮那个实验

第 3 轮（报告 18.3）三臂结论：

| 臂 | σ 来源 | HF jitter | 相对 shift6 的效应 |
|---|---|---:|---:|
| shift 6.0（第 1 次） | 默认网格 | 0.1293 | — |
| shift 6.0（第 2 次） | 默认网格 | 0.1075 | — |
| shift 12.0 | 默认网格 | 0.1182 | −0.2 %（落在漂移内） |
| **ComfyUI `er_sde` σ 网格** | **自定义 sigmas** | **0.0995** | **−16.0 %（落在 18.4 % 漂移带内）** |

→ 第 3 轮**正确地没有下结论**（「−16 %」落在本机 18.4 % 的漂移带内）。

第 4 轮（报告 18.4）找到了漂移的真正来源：`autotune`（Metal 内核竞速），
在 `generate-video` + `vae-decode` + `video-ref-encoder` 三处关掉它 → **漂移 = 0**
（P18 用逐位判据证明：`dmd` 跑两次逐位相同、`euler` 与不接端口逐位相同）。

→ 所以第 3 轮那个 −16 % 现在**可以重测直采**。这就是 P13b。

## 实验设计（两臂 × 多次，唯一变量 = 视频 σ 串）

| 臂 | `minimax-h3-model-config.sigmas` | 视频 σ 网格 |
|---|---|---|
| **A `p13b-ersde`** | `"1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"` | ComfyUI `er_sde` 表（**与第 3 轮逐字相同**） |
| **B `p13b-default`** | **不写该字段** | 默认网格 = `linspace(1,0,steps+1)` 过 `video_shift=6.0` |

* 两臂其余配置**逐字相同**（含 `video_shift: 6.0` / `audio_shift: 3.0` / 同 seed 42 /
  22 帧 / 1344×768 / 8 步 / 同一 LoRA / 同一张参考图）。
* **注意**：A 臂仍写 `video_shift: 6.0` —— 因为给了自定义视频 σ 串后，
  音频 σ 串要**先按 `video_shift` 反解回共享无偏移网格 q** 再过 `audio_shift`
  （上游文档原话；见 `scripts/p15_sigma_grid.py`）。这与第 3 轮完全一致。
* 两臂都带 `sampler-select{method:euler}` 接在 `generate-video` 的 **iport 3**
  （SOP 12.6：把采样器端口常接、method 用 euler 保持中性 → 端口透明、不引入额外差异）。
* 两臂三处 `autotune: false`。

## 跑几次

* A 臂 **3 次**（A1/A2/A3）→ 证明「网格臂」在漂移=0 下逐位相同。
* B 臂 **2 次**（B1/B2）→ 证明「默认臂」逐位相同，且 B1 ≡ 第 4 轮 `p18-euler.mp4`
  （**跨轮次锚点**：同一配置在第 4 轮与本轮产出逐位相同 → 漂移=0 的跨轮次证据）。

## 用法

```bash
python3 make_p13b_pipelines.py            # 生成到 vpipe-workspace/pipelines/
```
"""
import json
import os
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"
PIPE_DIR = os.path.join(WS, "pipelines")
TEMPLATE = os.path.join(PIPE_DIR, "p18-euler.vpipeline")

# ComfyUI `er_sde` 的 σ 表 —— 与第 3 轮 p13-static-shifter-sde.vpipeline 逐字相同
ER_SDE = "1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0"


def build(arm, out_name, with_sigmas):
    with open(TEMPLATE, encoding="utf-8") as f:
        pipe = json.load(f)

    pipe["id"] = arm

    for st in pipe["stages"]:
        if st["type"] == "minimax-h3-model-config":
            # 唯一变量：自定义视频 σ 串
            if with_sigmas:
                st["config"]["sigmas"] = ER_SDE
            else:
                st["config"].pop("sigmas", None)
        if st["type"] == "save-video":
            st["config"]["output_url"] = "out/%s.mp4" % out_name

    # 自检：三处 autotune:false + sampler 端口在 iport 3
    n_auto = sum(1 for st in pipe["stages"]
                 if st["config"].get("autotune") is False)
    assert n_auto == 3, "autotune:false 应恰好 3 处，实际 %d" % n_auto

    gv = next(st for st in pipe["stages"] if st["id"] == "generate-video")
    # ★ iport 3 = iports 列表的第 4 项（index 3），不是 oport==3
    #   （第 3 轮坑 10.7：iport 数量必须与模板逐项一致，多一个空 iport 会挤走 config 槽位）
    assert gv["iports"][3]["src"] == "sampler-select", \
        "iports[3] 必须接 sampler-select，实际 %r" % (gv["iports"][3]["src"],)
    assert len(gv["iports"]) == 10, "iports 必须 10 项，实际 %d" % len(gv["iports"])
    ss = next(st for st in pipe["stages"] if st["id"] == "sampler-select")
    assert ss["config"]["method"] == "euler", "method 必须 euler（保持中性）"

    path = os.path.join(PIPE_DIR, "%s.vpipeline" % arm)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pipe, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("[OK] %s  sigmas=%s" % (path, "有（er_sde）" if with_sigmas else "无（默认网格）"))
    return path


def main():
    if not os.path.exists(TEMPLATE):
        print("模板不存在：%s" % TEMPLATE)
        return 1
    build("p13b-ersde", "p13b-ersde", True)
    build("p13b-default", "p13b-default", False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
