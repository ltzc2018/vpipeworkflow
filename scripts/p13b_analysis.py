#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P13b · `sigmas`（ComfyUI `er_sde` σ 表）网格对照 —— 判决脚本

## 要回答的问题

第 3 轮（报告 18.3）测得「`er_sde` σ 网格让 HF jitter 下降 **16.0%**」，
但当时本机漂移基线是 **18.4%** → **效应落在噪声带内，当时正确地没有下结论**。

第 4 轮（报告 18.4）定位到漂移的真源 = Metal 内核竞速（`autotune`），
在 `generate-video` + `vae-decode` + `video-ref-encoder` 三处关掉 → 漂移 = 0。

⇒ 本轮在漂移 = 0 下重测，**≥3 次**，看那个 −16% 是否成立。

## 实验设计

| 臂 | `minimax-h3-model-config.sigmas` | 视频 σ 网格 | 次数 |
|---|---|---|---|
| **A** | `1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0` | ComfyUI `er_sde` 表 | **3**（r1/r2/r3） |
| **B** | 不写该字段 | 默认网格（shift 6.0） | **2**（r1/r2） |
| 跨轮锚点 | 第 4 轮 `p18-euler.mp4` | 默认网格（shift 6.0） | 1（历史） |

两臂其余配置逐字相同（`make_p13b_pipelines.py` 里有差异自检）。

## 口径纪律（继承 P11 / P15 / P18）

* 逐帧判据用 `framemd5` **必须 `-map 0:v`**（全流会混进音频包：22 帧片的全流清单是 51 行）；
* 音频轨另用解码后 md5 判；
* **绝不用 mp4 文件哈希**判断两次生成是否一致（容器含时间戳）；
* SSIM **口径 A（视频流直接比）与口径 B（首帧落盘 PNG 再比）分开写**（两者差约 0.03~0.18，不混用）；
* 效应量必须同时给出**地板值与倍数**（第 4 轮坑 12.4）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
sys.path.insert(0, os.path.join(LAB, "scripts"))


# ------------------------------------------------------------------ 基础判据
def framemd5_video(path):
    """★ 只取视频流的逐帧 md5 清单（-map 0:v）→ (行数, 清单整体 md5)。"""
    p = subprocess.run([FF, "-v", "error", "-i", path, "-map", "0:v",
                        "-f", "framemd5", "-"], capture_output=True, text=True)
    if p.returncode != 0:
        return None, None, p.stderr[:200]
    lines = [l for l in p.stdout.splitlines() if l and not l.startswith("#")]
    body = "\n".join(lines) + "\n"
    return len(lines), hashlib.md5(body.encode()).hexdigest(), None


def framemd5_all(path):
    p = subprocess.run([FF, "-v", "error", "-i", path, "-f", "framemd5", "-"],
                       capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l and not l.startswith("#")]
    return len(lines)


def audio_md5(path):
    p = subprocess.run([FF, "-v", "error", "-i", path, "-map", "0:a:0",
                        "-f", "md5", "-"], capture_output=True, text=True)
    m = re.search(r"MD5=([0-9a-f]+)", p.stdout)
    return m.group(1) if m else None


def ssim_stream(a, b):
    """口径 A：视频流直接比。"""
    p = subprocess.run([FF, "-v", "info", "-i", a, "-i", b, "-lavfi",
                        "[0:v][1:v]ssim", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else float("nan")


def psnr_stream(a, b):
    p = subprocess.run([FF, "-v", "info", "-i", a, "-i", b, "-lavfi",
                        "[0:v][1:v]psnr", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"average:([0-9.]+|inf)", p.stderr)
    return m.group(1) if m else "nan"


def first_frame_png(src, tag):
    tmp = "/tmp/p13b_ssim"
    os.makedirs(tmp, exist_ok=True)
    png = os.path.join(tmp, "%s.png" % tag)
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf",
                    "select=eq(n\\,0)", "-frames:v", "1", png], check=True)
    return png


def ssim_png(a, b):
    """口径 B：两段各抽首帧落盘 PNG 再比。"""
    pa = first_frame_png(a, "a")
    pb = first_frame_png(b, "b")
    p = subprocess.run([FF, "-v", "info", "-i", pa, "-i", pb, "-lavfi",
                        "[0:v][1:v]ssim", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else float("nan")


def pair_report(a, b, label):
    fa, ha, ea = framemd5_video(a)
    fb, hb, eb = framemd5_video(b)
    aa = audio_md5(a)
    ab = audio_md5(b)
    return {
        "pair": label,
        "a": os.path.basename(a), "b": os.path.basename(b),
        "frames_a": fa, "frames_b": fb,
        "framemd5_a": ha, "framemd5_b": hb,
        "framemd5_identical": (ha is not None and ha == hb),
        "audio_md5_a": aa, "audio_md5_b": ab,
        "audio_identical": (aa is not None and aa == ab),
        "ssim_stream_口径A": round(ssim_stream(a, b), 6),
        "psnr_stream": psnr_stream(a, b),
        "ssim_png_口径B": round(ssim_png(a, b), 6),
        "bytes_a": os.path.getsize(a), "bytes_b": os.path.getsize(b),
    }


def seconds_for(name):
    p = os.path.join(LAB, "logs", "%s.seconds" % name)
    if os.path.exists(p):
        return int(open(p).read().strip())
    return None


# ---------------------------------------------------------------------- main
def main():
    out_json = sys.argv[1] if len(sys.argv) > 1 else None
    O = os.path.join(WS, "out")
    arms = {
        "A1": os.path.join(O, "p13b-ersde-r1.mp4"),     # A 臂 er_sde σ 网格
        "A2": os.path.join(O, "p13b-ersde-r2.mp4"),
        "A3": os.path.join(O, "p13b-ersde-r3.mp4"),
        "B1": os.path.join(O, "p13b-default-r1.mp4"),   # B 臂 默认网格
        "B2": os.path.join(O, "p13b-default-r2.mp4"),
        "anchor": os.path.join(O, "p18-euler.mp4"),    # 第 4 轮跨轮锚点
    }
    present = {k: v for k, v in arms.items() if os.path.exists(v)}
    if not present:
        print("没有产物，先跑 p13b_runner.sh")
        return 1

    import p13_hf_jitter as P

    print("=" * 100)
    print("P13b · `sigmas`（ComfyUI er_sde σ 表）网格对照 —— 第 3 轮 −16% 的重测")
    print("=" * 100)

    # ---------------------------------------------------------- 1 逐位判据
    print("\n【1】逐位判据（framemd5 只取视频流 -map 0:v；音频另算 md5）")
    rows = []
    combos = [
        ("A1", "A2", "★ A1 vs A2：同臂同配置重复运行 → 漂移是否为 0"),
        ("A2", "A3", "★ A2 vs A3：同上"),
        ("B1", "B2", "★ B1 vs B2：默认网格臂同配置重复运行"),
        ("B1", "anchor", "★★ B1 vs 第 4 轮 p18-euler：跨轮次锚点（漂移=0 的跨轮证据）"),
        ("A1", "B1", "★ A vs B：唯一变量 = 视频 σ 串（处理组对照）"),
    ]
    for ka, kb, label in combos:
        if ka in present and kb in present:
            r = pair_report(present[ka], present[kb], label)
            rows.append(r)
            print("\n--- %s" % r["pair"])
            print("    %s  vs  %s" % (r["a"], r["b"]))
            print("    视频帧数        : %s / %s   （全流清单行数 %s / %s）"
                  % (r["frames_a"], r["frames_b"],
                     framemd5_all(present[ka]), framemd5_all(present[kb])))
            print("    framemd5(视频流): %s" % ("★ 逐位相同" if r["framemd5_identical"] else "不同"))
            print("      A = %s" % r["framemd5_a"])
            print("      B = %s" % r["framemd5_b"])
            print("    音频轨 md5      : %s" % ("★ 逐位相同" if r["audio_identical"] else "不同"))
            print("      A = %s" % r["audio_md5_a"])
            print("      B = %s" % r["audio_md5_b"])
            print("    SSIM 口径A(整段): %s      PSNR: %s" % (r["ssim_stream_口径A"], r["psnr_stream"]))
            print("    SSIM 口径B(首帧): %s" % r["ssim_png_口径B"])
            print("    字节            : %s / %s" % (r["bytes_a"], r["bytes_b"]))

    # ---------------------------------------------------------- 2 #55 三指标
    print("\n\n【2】issue #55 三指标 + 本实验室补充指标（384 宽灰度解码域）")
    print("%-24s %9s %11s %10s %12s %10s"
          % ("文件", "HF jitter", "frame diff", "sharpness", "static_jitter", "静止像素比"))
    metrics = []
    for k in ("A1", "A2", "A3", "B1", "B2", "anchor"):
        if k not in present:
            continue
        m = P.measure(present[k])
        metrics.append({"arm": k, **{x: m[x] for x in
                        ("file", "hf_jitter", "frame_diff", "sharpness",
                         "static_hf_jitter", "static_pixel_ratio")}})
        print("%-24s %9.4f %11.6f %10.2f %12.4f %10.3f"
              % (os.path.basename(present[k]), m["hf_jitter"], m["frame_diff"],
                 m["sharpness"], m["static_hf_jitter"], m["static_pixel_ratio"]))

    # ---------------------------------------------------------- 3 首帧 SSIM
    print("\n\n【3】首帧 SSIM（口径 B：落盘 PNG 再比）与耗时")
    pair_ssim = []
    for ka, kb, label in [("A1", "B1", "A(er_sde) vs B(默认)"),
                          ("B1", "anchor", "B1 vs 第4轮锚点")]:
        if ka in present and kb in present:
            s = P.frame0_ssim(present[ka], present[kb])
            pair_ssim.append({"pair": label, "frame0_ssim": round(s, 6)})
            print("    %-28s 首帧 SSIM = %.6f" % (label, s))
    for k in ("A1", "A2", "A3", "B1", "B2"):
        s = seconds_for("p13b-%s-r%s" % (("ersde" if k.startswith("A") else "default"),
                                         k[-1]))
        if s:
            print("    %-28s 用时 %d s（%.1f 分）" % (k, s, s / 60.0))

    # ---------------------------------------------------------- 4 效应量
    print("\n\n【4】效应量：A(er_sde σ 网格) 相对 B(默认网格)；漂移基线 = 0")
    base = next((m for m in metrics if m["arm"] == "B1"), None)
    effects = []
    if base:
        for m in metrics:
            if m["arm"] in ("B1",):
                continue
            e = {"arm": m["arm"]}
            for key in ("hf_jitter", "frame_diff", "sharpness", "static_hf_jitter"):
                b = base[key]
                e[key + "_pct"] = round((m[key] - b) / b * 100.0, 2) if b else None
            effects.append(e)
            print("    %-6s HF jitter %+7.2f%%   frame diff %+7.2f%%   "
                  "sharpness %+7.2f%%   static_jitter %+7.2f%%"
                  % (m["arm"], e["hf_jitter_pct"], e["frame_diff_pct"],
                     e["sharpness_pct"], e["static_hf_jitter_pct"]))

    # ---------------------------------------------------------- 5 与第 3 轮对比
    print("\n\n【5】与第 3 轮（18.3）对照 —— 那个 −16% 当时落在 18.4% 漂移带内")
    r3 = {
        "shift6_run1_hf": 0.1293, "shift6_run2_hf": 0.1075,
        "ersde_hf": 0.0995, "ersde_frame_diff": 0.003433,
        "ersde_sharpness": 544.30, "ersde_static": 0.0944,
        "ersde_static_ratio": 0.981, "floor": 0.0010,
        "ersde_effect_pct": -16.0, "drift_pct": 18.4,
    }
    a1 = next((m for m in metrics if m["arm"] == "A1"), None)
    b1 = next((m for m in metrics if m["arm"] == "B1"), None)
    print("    第 3 轮：er_sde HF jitter %.4f vs shift6 %.4f → %+.1f%%（漂移带 %.1f%%）→ 不可下结论"
          % (r3["ersde_hf"], r3["shift6_run2_hf"], r3["ersde_effect_pct"], r3["drift_pct"]))
    if a1 and b1:
        eff = (a1["hf_jitter"] - b1["hf_jitter"]) / b1["hf_jitter"] * 100.0
        print("    第 5 轮：er_sde HF jitter %.4f vs 默认 %.4f → %+.2f%%（漂移 = 0）"
              % (a1["hf_jitter"], b1["hf_jitter"], eff))
        print("    地板倍数：第3轮 %.0f×  vs  第5轮 %.0f×（地板 %.4f）"
              % (r3["ersde_hf"] / r3["floor"], a1["hf_jitter"] / r3["floor"], r3["floor"]))

    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"pairs": rows, "metrics": metrics,
                       "frame0_ssim": pair_ssim, "effects": effects,
                       "round3_reference": r3},
                      f, indent=2, ensure_ascii=False)
        print("\n[JSON] %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
