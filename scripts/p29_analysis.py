#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P29 —— RelayVSR 2× (int8 token) 判决脚本

问题：
  Q1 确定性：autotune:false 下同 seed 复跑是否逐位相同（对照 P22 FlashVSR 的
     「framemd5 不同但指标漂移≈0」—— RelayVSR stage 真有 autotune 键）
  Q2 细节：RelayVSR 2× 是否生成插值给不出的细节（纹理量/颗粒量双口径，对照 P22
     「细节生成器」判决在 2× 档是否成立）
  Q3 保真：本素材无更高真值 → 用「A vs B 直接对比 + HF jitter 15 帧周期性」
     判据（社区 fervorcreativeai 预言：接缝以 window-1=15 帧为周期脉动）
"""
import os, sys, json
import numpy as np

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
sys.path.insert(0, os.path.join(LAB, "scripts"))

import p13b_analysis as A
import p13_hf_jitter as J
from p22_analysis import detail_native

SRC  = os.path.join(WS, "out/dance-woman-5s.mp4")
ARMA = os.path.join(WS, "out/p29/p29-armA-lanczos-1664x960.mp4")
ARMB = os.path.join(WS, "out/p29-relayvsr-x2.mp4")
ARMB2 = os.path.join(WS, "out/p29-relayvsr-x2-r2.mp4")

W, H = 1664, 960

def decode_gray_native(path):
    """原生 1664x960 解码灰度帧（不缩放），供周期性分析"""
    cmd = [FF, "-v", "error", "-i", path, "-map", "0:v:0",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess_run(cmd)
    n = len(raw) // (W * H)
    return np.frombuffer(raw[:n*W*H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)

def subprocess_run(cmd):
    import subprocess
    return subprocess.run(cmd, capture_output=True, check=True).stdout

def hf_series(path):
    """返回每帧 HF 能量序列（高频带能量），用于 15 帧周期检验"""
    g = decode_gray_native(path)
    blur = J.gaussian_blur(g)
    hf = g - blur
    return np.array([float(np.abs(f).mean()) for f in hf]), hf

def periodicity_score(series, period=15):
    """检验序列是否有 period 帧周期脉动：
    比较相邻帧差分（lag-1）与 lag-period 差分的相关性；
    若有周期性接缝，|diff lag=period| 应显著大于 lag-1 或呈现周期峰。"""
    s = np.asarray(series)
    n = len(s)
    # 直接对帧间 HF 变化率做周期折叠：第 k 帧的 |hf[k]-hf[k-1]| 按 (k mod period) 分组
    d1 = np.abs(np.diff(s))
    groups = [[] for _ in range(period)]
    for i, v in enumerate(d1):
        groups[(i + 1) % period].append(v)
    means = [float(np.mean(g)) for g in groups if len(g) > 0]
    grand = float(np.mean(d1))
    # 周期峰显著度：最大组均值 / 总均值 - 1
    peak = max(means) / grand - 1.0 if grand > 1e-12 else 0.0
    # 与随机对照：组间方差 / 总方差（F 比近似）
    between = float(np.var(means))
    within = float(np.mean([np.var(g) for g in groups if len(g) > 0]))
    f_ratio = between / within if within > 1e-15 else 0.0
    return {"period": period, "grand": grand, "peak_excess": round(peak, 4),
            "f_ratio": round(f_ratio, 4), "group_means": [round(m, 5) for m in means]}

def main():
    res = {"experiment": "P29 RelayVSR-x2 int8 token 2x (832x480 -> 1664x960, 124f)", "arms": {}, "pairs": []}
    print("=" * 74)
    print("P29 · RelayVSR 2× (Comfy-Org int8 repack, i8_gemm token) —— 判决")
    print("=" * 74)

    print("\n【逐位判据】framemd5(-map 0:v) + 音频 md5")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB), ("B-r2", ARMB2)):
        n, h, _ = A.framemd5_video(path)
        au = A.audio_md5(path)
        print("  %-12s 帧数=%-4s framemd5=%s audio=%s" % (tag, n, (h or "")[:16], (au or "-")[:16]))
        res["arms"][tag] = {"framemd5": h, "audio_md5": au, "frames": n}

    if os.path.exists(ARMB2):
        a, b = res["arms"]["B-relayvsr"], res["arms"]["B-r2"]
        same = (a["framemd5"] == b["framemd5"])
        res["determinism_framemd5_identical"] = same
        print("  ★ 复跑 framemd5 逐位相同: %s" % same)

    print("\n【Q2 细节】双口径（原生分辨率 1664×960）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB)):
        d = detail_native(path, w=W, h=H)
        res["arms"][tag]["detail"] = d
        print("  %-12s 纹理量(raw/med)=%s/%s 颗粒=%s 纹理噪点比=%s" %
              (tag, d["detail_raw"], d["detail_med"], d["grain"], d["snr_texture"]))

    print("\n【时序指标】HF jitter 族（384 宽统一口径）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB), ("B-r2", ARMB2)):
        m = J.measure(path)
        res["arms"][tag]["hf"] = m
        print("  %-12s hf_jitter=%s frame_diff=%s sharpness=%s static=%s" %
              (tag, m["hf_jitter"], m["frame_diff"], m["sharpness"], m["static_hf_jitter"]))

    print("\n【Q3 保真】A vs B 口径 A 流直比")
    r = A.pair_report(ARMA, ARMB, "A-lanczos vs B-relayvsr")
    res["pairs"].append(r)
    print("  SSIM(A)=%s PSNR=%s dB SSIM(B首帧)=%s" %
          (r["ssim_stream_口径A"], r["psnr_stream"], r["ssim_png_口径B"]))

    print("\n【15 帧周期检验】（window=16 → 关键帧每 15 帧；若接缝则周期峰显著）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB)):
        series, _ = hf_series(path)
        p = periodicity_score(series, 15)
        res["arms"][tag]["period15"] = p
        print("  %-12s peak_excess=%s f_ratio=%s" % (tag, p["peak_excess"], p["f_ratio"]))
        print("    组均值: %s" % p["group_means"])

    out = os.path.join(LAB, "report", "p29_results.json")
    with open(out, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print("\nsaved:", out)

if __name__ == "__main__":
    main()
