#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P13 · MiniMax-H3 纹理沸腾（temporal texture boiling）量化

严格按上游 issue #55 的公式实现，不做自创改写：

    HF(t)      = gray(t) - GaussianBlur(gray(t), sigma=2.0)
    HF jitter  = mean_t |HF(t+1) - HF(t)| / mean_t |HF(t)|      <- 沸腾指标
    frame diff = mean_t |gray(t+1) - gray(t)| / 255
    sharpness  = mean_t Var(Laplacian(gray(t)))

测量域：384 宽的灰度解码（issue #55 原文 "Three metrics on a 384-wide gray decode"）。

额外补充两个本实验室自创但可辩护的指标（不替代 #55 的三个原指标）：
  * static_hf_jitter —— 只在「时序静止像素」上统计的 HF jitter。
      用 sigma=2.0 模糊帧的逐像素帧间差判定静止性，阈值 static_motion_thresh。
      目的：把「真实运动」与「逐帧重绘的高频噪声」分开 —— #55 的静墙夹具
      之所以要造静墙，就是为了消掉运动这一项。
  * pairwise frame-0 SSIM —— 用来检查「换 shift 是否换场景」这个方法学混淆项
      （社区实测：shift 变了，同 seed 同 prompt 也会生成不同画面）。

用法：
    python3 p13_hf_jitter.py <video.mp4> [...]          # 单个/多个视频
    python3 p13_hf_jitter.py --json out.json <video...> # 结果写 json
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
DECODE_WIDTH = 384
SIGMA = 2.0
STATIC_MOTION_THRESH = 2.0  # 灰阶 0-255，模糊后帧间差低于此值算静止像素


# ---------------------------------------------------------------- ffmpeg I/O
def probe_dims(path):
    """从 ffmpeg -i 的 stderr 里抠出 WxH（本机无 ffprobe）。"""
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    m = re.search(r"Stream #0:0.*?(\d{2,5})x(\d{2,5})", p.stderr, re.S)
    if not m:
        raise RuntimeError("无法解析视频尺寸: %s" % path)
    return int(m.group(1)), int(m.group(2))


def decode_gray(path, width=DECODE_WIDTH):
    """解码为 width 宽、偶数高的 8-bit 灰度帧序列，返回 (n, h, w) 的 uint8 数组。"""
    w0, h0 = probe_dims(path)
    h = max(2, int(round(h0 * width / w0 / 2.0)) * 2)  # 保持比例并取偶
    cmd = [FF, "-v", "error", "-i", path,
           "-vf", "format=gray,scale=%d:%d" % (width, h),
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (width * h)
    if n < 2:
        raise RuntimeError("帧数不足 2，无法算帧间指标: %s" % path)
    return np.frombuffer(raw[: n * width * h], dtype=np.uint8).reshape(n, h, width).astype(np.float64)


# ------------------------------------------------------------------ 滤波核
def gauss_kernel(sigma):
    r = int(np.ceil(3.0 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(x ** 2) / (2.0 * sigma * sigma))
    return k / k.sum(), r


def gaussian_blur(frames, sigma=SIGMA):
    """逐帧可分离高斯模糊，边缘用 reflect 填充。"""
    k, r = gauss_kernel(sigma)
    n, h, w = frames.shape
    # 水平
    pad = np.pad(frames, ((0, 0), (0, 0), (r, r)), mode="reflect")
    out = np.zeros_like(frames)
    for i, kv in enumerate(k):
        out += kv * pad[:, :, i:i + w]
    # 垂直
    pad = np.pad(out, ((0, 0), (r, r), (0, 0)), mode="reflect")
    out2 = np.zeros_like(out)
    for i, kv in enumerate(k):
        out2 += kv * pad[:, i:i + h, :]
    return out2


def laplacian(frames):
    """4 邻域离散 Laplacian。"""
    p = np.pad(frames, ((0, 0), (1, 1), (1, 1)), mode="reflect")
    c = p[:, 1:-1, 1:-1]
    return (p[:, :-2, 1:-1] + p[:, 2:, 1:-1] + p[:, 1:-1, :-2] + p[:, 1:-1, 2:]
            - 4.0 * c)


# ------------------------------------------------------------------ 指标
def measure(path):
    g = decode_gray(path)                    # (n,h,w) 0..255
    n = g.shape[0]
    blur = gaussian_blur(g)
    hf = g - blur                            # HF(t)

    # #55 指标 1：HF jitter
    d_hf = np.abs(hf[1:] - hf[:-1])          # (n-1,h,w)
    hf_jitter = float(d_hf.mean() / max(np.abs(hf).mean(), 1e-9))

    # #55 指标 2：frame diff
    d_g = np.abs(g[1:] - g[:-1])
    frame_diff = float(d_g.mean() / 255.0)

    # #55 指标 3：sharpness
    lap = laplacian(g)
    sharpness = float(lap.reshape(n, -1).var(axis=1).mean())

    # ---- 补充：静止区域上的 HF jitter（分离真实运动与沸腾）
    d_blur = np.abs(blur[1:] - blur[:-1])    # 低频运动图
    static_mask = d_blur < STATIC_MOTION_THRESH
    if static_mask.sum() > 0:
        num = float(d_hf[static_mask].mean())
        den = float(np.abs(hf)[0][static_mask[0]].mean()) if static_mask[0].any() else 0.0
        static_hf_jitter = num / max(den, 1e-9)
        static_ratio = float(static_mask.mean())
    else:
        static_hf_jitter = float("nan")
        static_ratio = 0.0

    return {
        "file": os.path.basename(path),
        "path": path,
        "frames": n,
        "decode_gray": "%dx%d" % (g.shape[2], g.shape[1]),
        "hf_jitter": round(hf_jitter, 6),
        "frame_diff": round(frame_diff, 6),
        "sharpness": round(sharpness, 2),
        "static_hf_jitter": round(static_hf_jitter, 6),
        "static_pixel_ratio": round(static_ratio, 4),
    }


# ------------------------------------------------------- 首帧两两 SSIM（混淆项）
def frame0_ssim(a, b):
    """抽两视频第 0 帧为 PNG，再用 ffmpeg ssim 滤镜比（口径：两张都落盘 PNG 再比 = 口径 B）。"""
    tmp = "/tmp/p13_ssim"
    os.makedirs(tmp, exist_ok=True)
    outs = []
    for src, tag in ((a, "a"), (b, "b")):
        png = os.path.join(tmp, "%s.png" % tag)
        subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf",
                        "select=eq(n\\,0)", "-frames:v", "1", png], check=True)
        outs.append(png)
    cmd = [FF, "-v", "info", "-i", outs[0], "-i", outs[1],
           "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else float("nan")


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--json", default=None)
    ap.add_argument("--pairs", default=None,
                    help="逗号分隔的视频对（basename），做首帧 SSIM 对照")
    args = ap.parse_args()

    results = []
    for v in args.videos:
        if not os.path.exists(v):
            print("跳过（不存在）: %s" % v)
            continue
        r = measure(v)
        results.append(r)
        print("%-34s %6.4f  frame_diff %.6f  sharp %8.2f  static_jitter %7.4f  static_px %.3f"
              % (r["file"], r["hf_jitter"], r["frame_diff"], r["sharpness"],
                 r["static_hf_jitter"], r["static_pixel_ratio"]))

    if args.pairs:
        byname = {r["file"]: r["path"] for r in results}
        for pair in args.pairs.split(","):
            a, b = pair.split("|")
            if a in byname and b in byname:
                s = frame0_ssim(byname[a], byname[b])
                print("首帧SSIM  %s  vs  %s  = %.6f" % (a, b, s))
                results.append({"pair": [a, b], "frame0_ssim": round(s, 6)})

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("已写入 %s" % args.json)


if __name__ == "__main__":
    main()
