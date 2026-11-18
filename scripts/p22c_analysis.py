#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P22c —— FlashVSR+ Turbo 原生 Metal 视频超分：判决脚本"""
import json
import os
import subprocess
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
sys.path.insert(0, os.path.join(LAB, "scripts"))

import p13b_analysis as A
import p13_hf_jitter as J

P22 = os.path.join(WS, "out/p22")
# 真值冲击 1920x1152 (1.667 比例)
REF = os.path.join(WS, "out/p22/p22-src-1920x1152-ref.mp4") # 需要生成
ARMC = os.path.join(P22, "p22c-armC-plus-1920x1152.mp4")

def detail_native(path, w=1920, h=1152):
    import numpy as np
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0",
         "-vf", "scale=%d:%d" % (w, h), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    if n < 1: return None
    fr = np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32)
    def median3(f):
        p = np.pad(f, 1, mode="edge")
        st = np.empty((9, h, w), dtype=np.float32)
        k = 0
        for dy in range(3):
            for dx in range(3):
                st[k] = p[dy:dy + h, dx:dx + w]
                k += 1
        return np.median(st, axis=0)
    def lap_var(f):
        x = f.astype(np.float32)
        lap = (-4.0 * x[1:-1, 1:-1] + x[:-2, 1:-1] + x[2:, 1:-1] + x[1:-1, :-2] + x[1:-1, 2:])
        return float(lap.var())
    raws, meds, grains = [], [], []
    for row in fr:
        raws.append(lap_var(row)); m = median3(row); meds.append(lap_var(m))
        grains.append(float(np.mean(np.abs(row - m))))
    return {"detail_med": round(float(np.mean(meds)), 1), "grain": round(float(np.mean(grains)), 3)}

def main():
    res = {"experiment": "P22c FlashVSR+ Turbo 1920x1152 SR", "arms": {}}
    print("P22c · FlashVSR+ Turbo 1920×1152 超分判决")
    
    if os.path.exists(ARMC):
        n, h, _ = A.framemd5_video(ARMC)
        m = J.measure(ARMC)
        d = detail_native(ARMC)
        res["arms"]["C-plus"] = {"framemd5": h, "temporal": m, "detail": d}
        print(f"  Arm C (Plus): HF jitter={m['hf_jitter']:.6f} 纹理量={d['detail_med']:.1f}")

    out_json = os.path.join(LAB, "logs", "p22c-analysis.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
