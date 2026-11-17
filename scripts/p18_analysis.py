#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P18 · `dmd` 采样器对纹理沸腾（上游 issue #55）的作用 —— 判决脚本

## 三臂设计

| 臂 | sampler 端口 | method | 作用 |
|---|---|---|---|
| A `p18-euler` | **接上** | `euler` | ★ 接线对照：证明「接上端口且 method=euler」与「不接端口」逐位相同 ⇒ 端口本身透明 |
| B `p18-dmd` | 接上 | `dmd` | 处理组：每步重注噪（`x0 at each sigma, then fresh noise to the next`） |
| B2 `p18-dmd2` | 接上 | `dmd` | 确定性验证：`dmd` 的重注噪路径是否也 bit-for-bit 复现 |
| 参照 `p15-repro-af1` | **不接** | 缺省=euler | 第 3 轮续作的 B1 臂（跨轮次 + 跨接线双重对照） |

## 口径纪律（继承 P11 / P15）

* 逐帧判据用 `framemd5` **必须 `-map 0:v`**（第 3 轮续作坑 11.3：全流会混进音频包，
  22 帧片的清单会变成 51 行）；
* 音频轨另用解码后 md5 判；
* SSIM **口径 A（视频流直接比）与口径 B（首帧落盘 PNG 再比）分开写，不混用**
  （第 2 轮 P11：口径 A 恒高于 B 约 0.17~0.19）；
* 绝不用 mp4 文件哈希判断两次生成是否一致（容器含时间戳）。
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
    """全流清单行数（对照用：应比视频流行数多出音频包）。"""
    p = subprocess.run([FF, "-v", "error", "-i", path, "-f", "framemd5", "-"],
                       capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l and not l.startswith("#")]
    return len(lines)


def audio_md5(path):
    p = subprocess.run([FF, "-v", "error", "-i", path, "-map", "0:a:0",
                        "-f", "md5", "-"], capture_output=True, text=True)
    if p.returncode != 0:
        return None
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
    tmp = "/tmp/p18_ssim"
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
        "euler": os.path.join(O, "p18-euler.mp4"),       # A：接端口 + euler
        "dmd": os.path.join(O, "p18-dmd.mp4"),           # B：dmd
        "dmd2": os.path.join(O, "p18-dmd2.mp4"),         # B2：dmd 重复
        "af1": os.path.join(O, "p15-repro-af1.mp4"),      # 参照：不接端口（跨轮次）
    }
    present = {k: v for k, v in arms.items() if os.path.exists(v)}
    if not present:
        print("没有产物，先跑 p18_runner.sh")
        return 1

    import p13_hf_jitter as P

    print("=" * 98)
    print("P18 · `dmd` 采样器 vs `euler`：纹理沸腾（issue #55）的本机判决")
    print("=" * 98)

    # ---------------------------------------------------------- 1 逐位判据
    print("\n【1】逐位判据（framemd5 只取视频流 -map 0:v；音频另算 md5）")
    rows = []
    combos = [
        ("euler", "af1", "★ A vs 参照：接端口+euler  vs  不接端口（第 3 轮续作 B1 臂）"),
        ("dmd", "dmd2", "★ B vs B2：`dmd` 重注噪路径的确定性"),
        ("euler", "dmd", "A vs B：`euler` vs `dmd`（处理组对照）"),
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
    for k in ("euler", "dmd", "dmd2", "af1"):
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
    for ka, kb, label in [("euler", "dmd", "A(euler) vs B(dmd)"),
                          ("euler", "af1", "A(euler) vs 参照(不接端口)"),
                          ("dmd", "dmd2", "B(dmd) vs B2(dmd)")]:
        if ka in present and kb in present:
            s = P.frame0_ssim(present[ka], present[kb])
            pair_ssim.append({"pair": label, "frame0_ssim": round(s, 6)})
            print("    %-28s 首帧 SSIM = %.6f" % (label, s))
    for k in ("euler", "dmd", "dmd2"):
        s = seconds_for("p18-%s" % k)
        if s:
            print("    %-28s 用时 %d s（%.1f 分）" % ("p18-%s" % k, s, s / 60.0))

    # ---------------------------------------------------------- 4 效应量
    print("\n\n【4】效应量（相对 A 臂 euler；漂移基线 = 0，因 autotune 已关）")
    base = next((m for m in metrics if m["arm"] == "euler"), None)
    effects = []
    if base:
        for m in metrics:
            if m["arm"] == "euler":
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

    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"pairs": rows, "metrics": metrics,
                       "frame0_ssim": pair_ssim, "effects": effects},
                      f, indent=2, ensure_ascii=False)
        print("\n[JSON] %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
