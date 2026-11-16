#!/usr/bin/env python3
"""P9 量化分析：Ref2VA @ 768p 多参考组合

复用第 8 轮的 p3_analysis.py 全部口径，保证跨轮可比：
  * 细节能量（拉普拉斯高通方差）：native（原生分辨率绝对锐度）+ canvas（统一 1344x768 交付尺寸）
  * 饱和度 / 对比度（暴露「采样网格用错 → 色彩漂移」）
  * 抖动（相邻帧平均绝对差）/ 冻结帧对 / 近黑帧
  * 亮度收敛（y_first / y_last / y_mean）
  * 音频：RMS / 峰值 / 静默 / 谱质心 / 低频占比
  * 组间 SSIM/PSNR —— **视频流直接比**（不落盘 PNG，避免 YUV 4:2:0 色度往返偏低约 0.03）

分析对象：
  A  p9-ref2va-768p-a          Ref2VA 768p · 1 图参考 · shift 6.0
  B  p9-ref2va-768p-b-shift12  Ref2VA 768p · 1 图参考 · shift 12.0   ← 只差 A 一个 shift 数字
  C  p9-ref2va-768p-c-multiref Ref2VA 768p · 1 图 + 动作视频 + 音轨 · shift 6.0
  -- 跨轮参照 --
  p3-768p-shift6   第 8 轮 FL2VA 768p shift 6.0（同一画布/步数，跨轮同口径对照）
  p3-768p-shift12  第 8 轮 FL2VA 768p shift 12.0
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_analysis as pa  # noqa: E402

WS = "/Users/minichen/AI-Models/vpipe-workspace"

FILES = {
    "A": f"{WS}/out/p9-ref2va-768p-a.mp4",
    "B": f"{WS}/out/p9-ref2va-768p-b-shift12.mp4",
    "C": f"{WS}/out/p9-ref2va-768p-c-multiref.mp4",
    "D": f"{WS}/out/p9-ref2va-768p-d-shift8.mp4",
    "p3fl_shift6": f"{WS}/out/p3-768p-shift6.mp4",
    "p3fl_shift12": f"{WS}/out/p3-768p-shift12.mp4",
}

PAIRS = [
    ("A", "B", "Ref2VA 768p：shift 6.0 vs 12.0"),
    ("A", "D", "Ref2VA 768p：shift 6.0 vs 8.0（中间档）"),
    ("D", "B", "Ref2VA 768p：shift 8.0 vs 12.0"),
    ("A", "C", "Ref2VA 768p：单图参考 vs 单图+动作视频参考"),
    ("A", "p3fl_shift6", "跨轮：Ref2VA 768p vs FL2VA 768p（同 shift 6.0）"),
    ("p3fl_shift6", "p3fl_shift12", "参照：FL2VA 768p 的 shift 6 vs 12（第 8 轮基线）"),
]


def main():
    out_json = sys.argv[1] if len(sys.argv) > 1 else "/tmp/p9-analysis.json"
    exist = {k: v for k, v in FILES.items() if os.path.exists(v)}
    res = {"overview": {}, "pairs": {}, "_files": exist}

    print("== 产物概览 ==")
    for k, v in exist.items():
        a = pa.analyse_video(v)
        a["path"] = v
        res["overview"][k] = a
        au = a.get("audio", {})
        print(f"  {k:12s} {a.get('resolution','?'):>9s} {a.get('duration','?'):>9s} "
              f"帧={a.get('frames','?'):>4d} 音频={a.get('has_audio','无'):>3s} "
              f"细节={a['detail_native']:>6.1f} 饱和={a.get('sat_mean','?'):>7} "
              f"对比={a.get('contrast','?'):>6} 抖动={a['jitter']:>5} 冻结={a['frozen_pairs']:>3d} "
              f"近黑={a['near_black_frames']:>3d} "
              f"谱质心={au.get('centroid_hz','—')}Hz 低频={au.get('low_ratio','—')}")

    print("\n== 组间 SSIM/PSNR（视频流直接比） ==")
    for a, b, desc in PAIRS:
        fa, fb = exist.get(a), exist.get(b)
        if not (fa and fb):
            continue
        s, ps = pa.ssim_psnr_stream(fa, fb)
        res["pairs"][f"{a} vs {b}"] = {"desc": desc, "ssim": s, "psnr": ps}
        print(f"  {a:12s} vs {b:12s} SSIM={s:.4f}  PSNR={ps if ps != '' else '—'}   ({desc})")

    with open(out_json, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n写出 {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
