#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P32 —— RelayVSR 2× 真值对照（P22 源 320×192 → 640×384）

要回答的问题（P29 遗留）：
  Q1 编造量：RelayVSR 2× 输出对 640×384 lanczos 真值的 SSIM/PSNR，
     相对纯 lanczos 插值臂（320×192 → 640×384 lanczos）是高是低？
     —— P22 判决 FlashVSR 4× 的 SSIM 比插值**低** 0.05 / PSNR 低 4 dB（编造）。
  Q2 细节：2× 档的纹理量/颗粒量是「结构化」还是「噪点」？（纹理/噪点比）
     相对真值倍数 = 编造量的直接度量（P22 判据：真值 1.76× 就是编造量）。
  Q3 确定性：同 config 复跑（r1 vs r2）是否逐位相同（P29 K103）？
  Q4 时序：HF jitter / frame_diff 相对插值臂与真值的偏移。
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
from p22_analysis import detail_native   # noqa: E402
from p29_analysis import hf_series, periodicity_score  # noqa: E402

P32 = os.path.join(WS, "out/p32")
REF = os.path.join(P32, "p32-ref-640x384.mkv")            # 真值（768p→lanczos→640×384）
ARMA = os.path.join(P32, "p32-armA-lanczos-640x384.mp4")  # 基线：lanczos 插值（待生成）
ARMB = os.path.join(P32, "p32-relayvsr-x2-640x384.mp4")
ARMB2 = os.path.join(P32, "p32-relayvsr-x2-r2-640x384.mp4")

W, H = 640, 384


def make_lanczos_arm():
    """A 臂：320×192 → 640×384 lanczos 插值（带音频，与 B 臂同容器口径）"""
    if os.path.exists(ARMA):
        return
    cmd = [FF, "-y", "-v", "error", "-i", os.path.join(WS, "p22-src-320x192.mp4"),
           "-vf", "scale=%d:%d:flags=lanczos" % (W, H),
           "-c:v", "libx264", "-preset", "slow", "-crf", "14",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           ARMA]
    subprocess.run(cmd, check=True)
    print("A 臂（lanczos）已生成")


def main():
    make_lanczos_arm()
    res = {"experiment": "P32 RelayVSR-x2 ground-truth comparison (320x192 -> 640x384, 25f)",
           "arms": {}, "pairs": []}
    print("=" * 74)
    print("P32 · RelayVSR 2× 真值对照（P22 同源 320×192 → 640×384）—— 判决")
    print("=" * 74)

    # ---------------- 逐位判据 ----------------
    print("\n【逐位判据】framemd5(-map 0:v) + 音频 md5")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB), ("B-r2", ARMB2), ("真值", REF)):
        n, h, err = A.framemd5_video(path)
        au = A.audio_md5(path)
        print("  %-12s 帧数=%-4s framemd5=%s audio=%s" %
              (tag, n, (h or "")[:16], (au or "-")[:16]))
        res["arms"][tag] = {"framemd5": h, "audio_md5": au, "frames": n}

    if "B-relayvsr" in res["arms"] and "B-r2" in res["arms"]:
        same = (res["arms"]["B-relayvsr"]["framemd5"] == res["arms"]["B-r2"]["framemd5"])
        res["determinism_framemd5_identical"] = same
        print("  ★ 复跑 framemd5 逐位相同: %s" % same)

    # ---------------- Q1 保真（真值对照，本轮核心） ----------------
    print("\n【Q1 保真】同分辨率 640×384 vs lanczos 真值")
    print("  口径 A = 视频流直接比；口径 B = 首帧落盘 PNG 再比")
    for a, b, label in ((ARMA, REF, "A-lanczos vs 真值"),
                        (ARMB, REF, "B-relayvsr vs 真值"),
                        (ARMA, ARMB, "A vs B")):
        r = A.pair_report(a, b, label)
        res["pairs"].append(r)
        print("  %-22s SSIM(A)=%s  PSNR=%s  SSIM(B)=%s" %
              (label, r["ssim_stream_口径A"], r["psnr_stream"], r["ssim_png_口径B"]))

    # ---------------- Q2 细节 ----------------
    print("\n【Q2 细节】纹理量 / 颗粒量（原生 640×384 双口径）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB), ("真值", REF)):
        d = detail_native(path, w=W, h=H)
        res["arms"][tag]["detail"] = d
        print("  %-12s 纹理量(raw/med)=%s/%s 颗粒=%s 纹理噪点比=%s" %
              (tag, d["detail_raw"], d["detail_med"], d["grain"], d["snr_texture"]))

    # ---------------- Q4 时序 ----------------
    print("\n【Q4 时序】HF jitter 族（384 宽统一口径）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB), ("真值", REF)):
        m = J.measure(path)
        res["arms"][tag]["hf"] = m
        print("  %-12s hf_jitter=%s frame_diff=%s sharpness=%s static=%s" %
              (tag, m["hf_jitter"], m["frame_diff"], m["sharpness"], m["static_hf_jitter"]))

    # ---------------- 15 帧周期检验（P33 判据定标数据点） ----------------
    print("\n【15 帧周期检验】（keyframe 每 15 帧；window=16）")
    for tag, path in (("A-lanczos", ARMA), ("B-relayvsr", ARMB)):
        series, _ = hf_series(path)
        p = periodicity_score(series, 15)
        res["arms"][tag]["period15"] = p
        print("  %-12s peak_excess=%s f_ratio=%s" % (tag, p["peak_excess"], p["f_ratio"]))

    # ---------------- 效应量汇总 ----------------
    print("\n【效应量】B(relayvsr) 相对 A(lanczos) / 相对真值")
    try:
        a_d = res["arms"]["A-lanczos"]["detail"]
        b_d = res["arms"]["B-relayvsr"]["detail"]
        r_d = res["arms"]["真值"]["detail"]
        e = {}
        for k in ("detail_med", "grain", "snr_texture"):
            e["B_vs_A_" + k + "_pct"] = round((b_d[k] - a_d[k]) / a_d[k] * 100.0, 2)
            e["B_over_REF_" + k] = round(b_d[k] / r_d[k], 3)
        a_t = res["arms"]["A-lanczos"]["hf"]
        b_t = res["arms"]["B-relayvsr"]["hf"]
        for k in ("hf_jitter", "frame_diff", "sharpness"):
            e["B_vs_A_" + k + "_pct"] = round((b_t[k] - a_t[k]) / a_t[k] * 100.0, 2)
        res["effect"] = e
        for k, v in e.items():
            print("  %-30s %s" % (k, v))
    except Exception as ex:
        print("  汇总失败：%s" % ex)

    out = os.path.join(LAB, "report", "p32_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print("\nsaved:", out)


if __name__ == "__main__":
    main()
