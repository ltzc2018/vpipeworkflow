#!/usr/bin/env python3
"""P9 锐度量：把「真实纹理」和「颗粒噪点」从拉普拉斯细节能量里拆开

为什么需要这个
--------------
第 8 轮用「逐帧拉普拉斯响应方差」当细节能量，本轮在 Ref2VA 上发现一个反直觉现象：
**shift 12.0 组的细节能量比 shift 6.0 组高 34%**，与第 8 轮 FL2VA 的结论（shift 6 更高）相反。
但目视同一位置的裁切图，shift 6.0 组毛发根根分明，shift 12.0 组表面更平滑。

这说明拉普拉斯方差**把噪点也当成细节**了 —— shift 12.0 组同时有更高的逐帧抖动，
它的高频里混着颗粒，而不是更多纹理。

本脚本用纯 numpy（无 scipy / 无 cv2）做三个可解释的量：

  detail_raw  拉普拉斯方差（原始帧）        —— 第 8 轮的口径：细节 + 噪点
  detail_med  3x3 中值滤波后再算拉普拉斯方差  —— 中值滤波压掉孤立噪点，保留纹理边缘
  grain       |帧 - 中值滤波(帧)| 的均值      —— 颗粒噪点能量
  snr_texture  detail_med / grain           —— 「纹理 ÷ 噪点」，越大越干净

用法: p9_sharpness.py [video.mp4 ...] [--json out.json]
"""
import json
import os
import subprocess
import sys

import numpy as np

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
WS = "/Users/minichen/AI-Models/vpipe-workspace"

DEFAULT = [
    f"{WS}/out/p9-ref2va-768p-a.mp4",
    f"{WS}/out/p9-ref2va-768p-b-shift12.mp4",
    f"{WS}/out/p9-ref2va-768p-c-multiref.mp4",
    f"{WS}/out/p9-ref2va-768p-d-shift8.mp4",
    f"{WS}/out/p3-768p-shift6.mp4",
    f"{WS}/out/p3-768p-shift12.mp4",
]


def gray_frames(path, w=1344, h=768):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0",
         "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    n = w * h
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, n)


def median3(f):
    """3x3 中值滤波（numpy 实现，边界用 edge 复制）"""
    h, w = f.shape
    p = np.pad(f, 1, mode="edge")
    st = np.empty((9, h, w), dtype=np.float32)
    k = 0
    for dy in range(3):
        for dx in range(3):
            st[k] = p[dy:dy + h, dx:dx + w]
            k += 1
    return np.median(st, axis=0)


def lap_var(f):
    """4 邻域拉普拉斯响应的方差"""
    x = f.astype(np.float32)
    lap = (-4.0 * x[1:-1, 1:-1] + x[:-2, 1:-1] + x[2:, 1:-1] + x[1:-1, :-2] + x[1:-1, 2:])
    return float(lap.var())


def analyse(path, crop=None):
    """crop=(x, y, w, h) 时只在该固定区域上测量 —— 用来排除「两组构图不同」的干扰：
    主体在画面中的位置变了，整帧纹理量就不可比；固定中心裁剪能只比同一块内容。"""
    fr = gray_frames(path)
    if len(fr) == 0:
        return None
    raws, meds, grains = [], [], []
    for row in fr:
        f = row.reshape(768, 1344).astype(np.float32)
        if crop:
            x, y, cw, ch = crop
            f = f[y:y + ch, x:x + cw]
        raws.append(lap_var(f))
        m = median3(f)
        meds.append(lap_var(m))
        grains.append(float(np.mean(np.abs(f - m))))
    raw = float(np.mean(raws))
    med = float(np.mean(meds))
    grain = float(np.mean(grains))
    return {
        "path": path,
        "frames": int(len(fr)),
        "crop": list(crop) if crop else None,
        "detail_raw": round(raw, 1),
        "detail_med": round(med, 1),
        "grain": round(grain, 3),
        "snr_texture": round(med / grain, 1) if grain > 1e-6 else None,
        "med_over_raw": round(med / raw, 3) if raw > 1e-6 else None,
    }


def main():
    argv = sys.argv[1:]
    out_json = None
    crop = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = argv[i + 1]
        del argv[i:i + 2]
    if "--crop" in argv:
        i = argv.index("--crop")
        crop = tuple(int(v) for v in argv[i + 1].split(","))
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        args = [p for p in DEFAULT if os.path.exists(p)]
    res = []
    for p in args:
        if not os.path.exists(p):
            print(f"跳过（无产物）{p}")
            continue
        r = analyse(p, crop)
        res.append(r)
        print(f"{os.path.basename(p)}" + (f"  [crop {crop}]" if crop else ""))
        print(f"  帧数        : {r['frames']}")
        print(f"  细节(原始)  : {r['detail_raw']:>8.1f}   ← 第 8 轮口径：细节 + 噪点")
        print(f"  细节(中值后): {r['detail_med']:>8.1f}   ← 压掉孤立噪点后的真实纹理")
        print(f"  颗粒噪点    : {r['grain']:>8.3f}")
        print(f"  纹理/噪点   : {r['snr_texture']:>8.1f}")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"\n写出 {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
