#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P22 —— FlashVSR 原生 Metal 视频超分：判决脚本

## 要回答的问题

vpipe 上游自带**原生 Metal 视频超分**（FlashVSR v1.1，4×）。
本轮第一次在本机真机跑通它，并回答三个问题：

  Q1 **保真**：同一份 320×192 低清源，FlashVSR 的 4× 输出 vs 纯 lanczos 插值，
     谁更接近**原始 768p 真值**？（降到 1280×768 同分辨率对比）
  Q2 **细节**：FlashVSR 是否真的生成了**插值给不出的高频细节**？
     （3×3 中值滤波后的纹理能量 + 颗粒能量 + 纹理/噪点比）
  Q3 **时序**：生成式超分会不会引入闪烁？（HF jitter / static HF jitter）

## 口径纪律（继承 P11 / P13b / P15 / P18）

* SSIM 口径 A（视频流直接比）与口径 B（首帧落盘 PNG 再比）分开写，不混用；
* 逐帧判据用 `framemd5 -map 0:v`（全流会混进音频包）；**绝不用 mp4 文件哈希**；
* 细节能量会把噪点当细节 → 锐度必须同时看中值滤波后的纹理量与颗粒量（第 3 轮坑）；
* 效应量必须给出**地板值与倍数**（第 4 轮坑 12.4）。
"""
import json
import os
import subprocess
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
FF = os.path.expanduser("~/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
sys.path.insert(0, os.path.join(LAB, "scripts"))

import p13b_analysis as A          # noqa: E402
import p13_hf_jitter as J          # noqa: E402


def detail_native(path, w=1280, h=768):
    """细节量：在**原生分辨率**上测（p9_sharpness.analyse 固定 1344×768，会把本轮的
    1280 宽再插值一次；本轮另写一份原生版，数学与 p9_sharpness 完全一致：
    3×3 中值滤波后的拉普拉斯方差 = 纹理量；|帧-中值| 的均值 = 颗粒量）。"""
    import numpy as np
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0",
         "-vf", "scale=%d:%d" % (w, h), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    if n < 1:
        return None
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
        lap = (-4.0 * x[1:-1, 1:-1] + x[:-2, 1:-1] + x[2:, 1:-1]
               + x[1:-1, :-2] + x[1:-1, 2:])
        return float(lap.var())

    raws, meds, grains = [], [], []
    for row in fr:
        raws.append(lap_var(row))
        m = median3(row)
        meds.append(lap_var(m))
        grains.append(float(np.mean(np.abs(row - m))))
    raw_m = float(np.mean(raws))
    med = float(np.mean(meds))
    grain = float(np.mean(grains))
    return {
        "path": path, "frames": int(n), "size": "%dx%d" % (w, h),
        "detail_raw": round(raw_m, 1),
        "detail_med": round(med, 1),
        "grain": round(grain, 3),
        "snr_texture": round(med / grain, 1) if grain > 1e-6 else None,
        "med_over_raw": round(med / raw_m, 3) if raw_m > 1e-6 else None,
    }

P22 = os.path.join(WS, "out/p22")
REF = os.path.join(P22, "p22-ref-1280x768.mkv")            # 真值（原始 768p → 1280×768 lanczos）
ARMA = os.path.join(P22, "p22-armA-lanczos-1280x768.mp4")  # 基线：lanczos 插值
ARMB = os.path.join(P22, "p22-armB-flashvsr-1280x768.mp4") # 实验臂：FlashVSR
ARMB2 = os.path.join(P22, "p22-armB-flashvsr-r2-1280x768.mp4")  # 复跑（确定性）


def probe(path):
    if not os.path.exists(path):
        return None
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    out = p.stderr
    frames = None
    for l in out.splitlines():
        if "frame=" in l:
            try:
                frames = int(l.split("frame=")[1].split()[0])
            except Exception:
                pass
    return {"bytes": os.path.getsize(path), "frames": frames}


def main():
    res = {"experiment": "P22 FlashVSR v1.1 native Metal 4x SR", "arms": {}, "pairs": []}

    print("=" * 74)
    print("P22 · FlashVSR v1.1 原生 Metal 4× 视频超分 —— 判决")
    print("=" * 74)

    # ---------------- 逐位判据（framemd5 视频流 + 音频 md5） ----------------
    print("\n【逐位判据】framemd5(-map 0:v) + 音频轨 md5")
    for tag, path in (("A-lanczos", ARMA), ("B-flashvsr", ARMB), ("B-flashvsr-r2", ARMB2)):
        if not os.path.exists(path):
            print("  %-16s （无产物）" % tag)
            continue
        n, h, err = A.framemd5_video(path)
        au = A.audio_md5(path)
        print("  %-16s 帧数=%-4s framemd5=%s  音频md5=%s" %
              (tag, n, (h or "")[:16], (au or "-")[:16]))
        res["arms"][tag] = {"framemd5": h, "audio_md5": au, "frames": n,
                             "probe": probe(path)}

    if ARMB2 in res["arms"] and "B-flashvsr" in res["arms"]:
        a = res["arms"]["B-flashvsr"]
        b = res["arms"]["B-flashvsr-r2"]
        same = (a["framemd5"] == b["framemd5"])
        res["determinism_framemd5_identical"] = same
        res["determinism_audio_identical"] = (a["audio_md5"] == b["audio_md5"])
        print("  → 复跑逐位相同：%s（视频流 framemd5） / 音频：%s" %
              (same, res["determinism_audio_identical"]))

    # ---------------- Q1 保真 ----------------
    print("\n【Q1 保真】同分辨率（1280×768）两两对比")
    print("  口径 A = 视频流直接比；口径 B = 首帧落盘 PNG 再比（两者不混用）")
    pairs = [
        (ARMA, REF, "A-lanczos vs 真值"),
        (ARMB, REF, "B-flashvsr vs 真值"),
        (ARMA, ARMB, "A-lanczos vs B-flashvsr"),
        (ARMB, ARMB2, "★B-r1 vs B-r2（漂移基线）"),
    ]
    for a, b, label in pairs:
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        r = A.pair_report(a, b, label)
        res["pairs"].append(r)
        print("  %-26s SSIM(A)=%s  PSNR=%s  SSIM(B)=%s" %
              (label, r["ssim_stream_口径A"], r["psnr_stream"], r["ssim_png_口径B"]))

    # ---------------- Q2 细节 ----------------
    print("\n【Q2 细节】3×3 中值滤波后的纹理量 / 颗粒量（细节能量会把噪点当细节）")
    for tag, path in (("A-lanczos", ARMA), ("B-flashvsr", ARMB), ("真值 ref", REF)):
        if not os.path.exists(path):
            continue
        d = detail_native(path)
        res["arms"].setdefault(tag, {}).update({"detail": d})
        print("  %-14s 纹理量=%8.2f  颗粒=%6.3f  纹理/噪点=%7.1f" %
              (tag, d["detail_med"], d["grain"], d["snr_texture"]))

    # ---------------- Q3 时序 ----------------
    print("\n【Q3 时序】#55 三指标 + 静止区 HF jitter")
    for tag, path in (("A-lanczos", ARMA), ("B-flashvsr", ARMB),
                      ("B-flashvsr-r2", ARMB2), ("真值 ref", REF)):
        if not os.path.exists(path):
            continue
        m = J.measure(path)
        res["arms"].setdefault(tag, {}).update({"temporal": m})
        print("  %-14s HF jitter=%.6f  frame diff=%.6f  sharpness=%.2f  static HF jitter=%.6f" %
              (tag, m["hf_jitter"], m["frame_diff"], m["sharpness"], m["static_hf_jitter"]))

    # ---------------- 漂移基线：FlashVSR 家族自身的同配置复跑差 ----------------
    if "B-flashvsr-r2" in res["arms"] and "B-flashvsr" in res["arms"]:
        try:
            t1 = res["arms"]["B-flashvsr"]["temporal"]
            t2 = res["arms"]["B-flashvsr-r2"]["temporal"]
            d = {}
            for k in ("hf_jitter", "frame_diff", "sharpness", "static_hf_jitter"):
                d[k + "_drift_pct"] = round((t2[k] - t1[k]) / t1[k] * 100.0, 2)
            res["flashvsr_drift_baseline_pct"] = d
            print("\n【漂移基线】FlashVSR 同配置复跑（r1 vs r2）—— 效应量必须超过它才可采信")
            for k, v in d.items():
                print("  %-30s %+8.2f%%" % (k, v))
        except Exception as ex:
            print("  漂移基线计算失败：%s" % ex)

    # ---------------- 汇总效应量 ----------------
    print("\n【效应量】B 相对 A（%s）" % "口径：同分辨率 1280×768")
    try:
        a_detail = res["arms"]["A-lanczos"]["detail"]
        b_detail = res["arms"]["B-flashvsr"]["detail"]
        e = {}
        for k in ("detail_med", "grain", "snr_texture"):
            if a_detail.get(k) and b_detail.get(k):
                e[k + "_pct"] = round((b_detail[k] - a_detail[k]) / a_detail[k] * 100.0, 2)
        a_t = res["arms"]["A-lanczos"]["temporal"]
        b_t = res["arms"]["B-flashvsr"]["temporal"]
        for k in ("hf_jitter", "frame_diff", "sharpness", "static_hf_jitter"):
            e[k + "_pct"] = round((b_t[k] - a_t[k]) / a_t[k] * 100.0, 2)
        res["effect_b_vs_a_pct"] = e
        for k, v in e.items():
            print("  %-26s %+8.2f%%" % (k, v))
    except Exception as ex:
        print("  汇总失败：%s" % ex)

    out = os.path.join(LAB, "logs", "p22-analysis.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print("\n→ %s" % out)


if __name__ == "__main__":
    main()
