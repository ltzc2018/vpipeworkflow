#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P15 · 判决脚本 —— bit-for-bit 可复现性判定

回答三个问题：
  1. B1 vs B2（autotune 关）：`framemd5` 是否逐帧逐位相同？音频轨 md5 是否相同？
  2. A1 vs A2（autotune 开，默认）：漂移有多大（本地 build 的漂移基线）？
  3. 竞速开关是加速还是减速（耗时对照）？

## 口径说明（与 SOP 第 4 节一致）

* **口径 A（视频流直接比）**：`[0:v][1:v]ssim` 直接比两条视频流。
* **口径 B（落盘 PNG 再比）**：两段各抽首帧 → PNG → 再 ssim。
* 口径 A 比口径 B **高约 0.03**（YUV 4:2:0 色度往返损失）—— **两者不可混用**。
* 本脚本同时给出两种口径，并明确标注。

## 逐位相同的判据（比 mp4 文件哈希更严）

mp4 容器含时间戳 → 同一段生成的两个文件哈希必不同。
真正要比的是**解码后的帧数据**：
  * 视频：`ffmpeg -f framemd5` 逐帧 md5 清单
  * 音频：`ffmpeg -f md5` 对音频流取 md5
"""
import argparse
import json
import os
import re
import subprocess
import sys

FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
WS = "/Users/minichen/AI-Models/vpipe-workspace"


def framemd5(path):
    """逐帧 md5 清单 -> (行数, 整体md5)。整体md5 由清单内容再取一次 md5。"""
    p = subprocess.run([FF, "-v", "error", "-i", path, "-f", "framemd5", "-"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None, None, p.stderr[:200]
    lines = [l for l in p.stdout.splitlines() if l and not l.startswith("#")]
    body = "\n".join(lines) + "\n"
    import hashlib
    return len(lines), hashlib.md5(body.encode()).hexdigest(), None


def audio_md5(path):
    """音频轨 md5（解包成 PCM 后取 md5）。无音轨返回 None。"""
    p = subprocess.run([FF, "-v", "error", "-i", path, "-map", "0:a:0",
                        "-f", "md5", "-"], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    m = re.search(r"MD5=([0-9a-f]+)", p.stdout)
    return m.group(1) if m else None


def ssim_stream(a, b):
    """口径 A：视频流直接比。"""
    cmd = [FF, "-v", "info", "-i", a, "-i", b, "-lavfi", "[0:v][1:v]ssim",
           "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else float("nan")


def psnr_stream(a, b):
    cmd = [FF, "-v", "info", "-i", a, "-i", b, "-lavfi", "[0:v][1:v]psnr",
           "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"average:([0-9.]+|inf)", p.stderr)
    return m.group(1) if m else "nan"


def first_frame_png(src, tag):
    tmp = "/tmp/p15_ssim"
    os.makedirs(tmp, exist_ok=True)
    png = os.path.join(tmp, "%s.png" % tag)
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf",
                    "select=eq(n\\,0)", "-frames:v", "1", png], check=True)
    return png


def ssim_png(a, b):
    """口径 B：两段各抽首帧落盘 PNG 再比。"""
    pa = first_frame_png(a, "a")
    pb = first_frame_png(b, "b")
    cmd = [FF, "-v", "info", "-i", pa, "-i", pb, "-lavfi", "[0:v][1:v]ssim",
           "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else float("nan")


def pair_report(a, b, label):
    fa, ha, _ = framemd5(a)
    fb, hb, _ = framemd5(b)
    aa = audio_md5(a)
    ab = audio_md5(b)
    r = {
        "pair": label,
        "a": os.path.basename(a),
        "b": os.path.basename(b),
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
    return r


def metrics(paths):
    """复用 P13 的三指标 + 补充指标（导入同目录脚本）。"""
    sys.path.insert(0, LAB + "/scripts")
    import p13_hf_jitter as P
    out = []
    for p in paths:
        if os.path.exists(p):
            out.append(P.measure(p))
    return out


def seconds_for(name):
    p = os.path.join(LAB, "logs", "%s.seconds" % name)
    if os.path.exists(p):
        return int(open(p).read().strip())
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    O = os.path.join(WS, "out")
    arms = {k: os.path.join(O, "p15-repro-%s.mp4" % k)
            for k in ("at1", "at2", "af1", "af2")}
    app = os.path.join(O, "p13-static-shift6.mp4")   # 第 3 轮 App 基线

    present = {k: v for k, v in arms.items() if os.path.exists(v)}
    if not present:
        print("没有产物，先跑 p15_runner.sh")
        return 1

    print("=" * 96)
    print("P15 · 可复现性基线（判决）")
    print("=" * 96)

    rows = []
    pairs = [("at1", "at2", "A1 vs A2  autotune 开（默认）· 本地 build"),
             ("af1", "af2", "B1 vs B2  autotune 关 · 本地 build")]
    if "at1" in present and "af1" in present:
        pairs.append(("at1", "af1", "A1 vs B1  同一次 build · 仅 autotune 不同"))
    if app and os.path.exists(app) and "at1" in present:
        rows.append(pair_report(app, present["at1"], "App(9db5dd7) vs 本地 build(33cda00) · autotune 开"))

    for ka, kb, label in pairs:
        if ka in present and kb in present:
            rows.append(pair_report(present[ka], present[kb], label))

    for r in rows:
        print("\n--- %s" % r["pair"])
        print("    %s  vs  %s" % (r["a"], r["b"]))
        print("    帧数            : %s / %s" % (r["frames_a"], r["frames_b"]))
        print("    framemd5        : %s" % ("★ 逐位相同" if r["framemd5_identical"] else "不同"))
        print("      A = %s" % r["framemd5_a"])
        print("      B = %s" % r["framemd5_b"])
        print("    音频轨 md5      : %s" % ("★ 逐位相同" if r["audio_identical"] else "不同"))
        print("      A = %s" % r["audio_md5_a"])
        print("      B = %s" % r["audio_md5_b"])
        print("    SSIM 口径A(流)  : %.6f" % r["ssim_stream_口径A"])
        print("    SSIM 口径B(PNG) : %.6f" % r["ssim_png_口径B"])
        print("    PSNR(流)        : %s" % r["psnr_stream"])
        print("    文件大小        : %d / %d B" % (r["bytes_a"], r["bytes_b"]))

    print("\n" + "=" * 96)
    print("耗时对照（竞速开关是加速还是减速）")
    print("=" * 96)
    times = {}
    for k in ("at1", "at2", "af1", "af2"):
        s = seconds_for("p15-repro-%s" % k)
        if s:
            times[k] = s
            print("  %-4s %4d 秒 (%.1f 分)" % (k, s, s / 60.0))
    if "at1" in times and "af1" in times:
        d = times["af1"] - times["at1"]
        print("  → 关竞速相对开竞速：%+.1f 秒 (%+.1f%%)"
              % (d, 100.0 * d / max(times["at1"], 1)))

    print("\n" + "=" * 96)
    print("纹理/锐度指标（P13 三指标 + 补充）")
    print("=" * 96)
    ms = metrics(list(present.values()) + ([app] if os.path.exists(app) else []))
    for m in ms:
        print("  %-28s hf_jitter %7.4f  frame_diff %8.6f  sharp %8.2f  static_jitter %7.4f"
              % (m["file"], m["hf_jitter"], m["frame_diff"], m["sharpness"],
                 m["static_hf_jitter"]))

    out = {"pairs": rows, "seconds": times, "metrics": ms}
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("\n已写入 %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
