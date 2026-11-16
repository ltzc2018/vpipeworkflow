#!/usr/bin/env python3
"""P9 汇总：把日志 + 度量结果拼成报告用的 Markdown 表格

用法: p9_report_tables.py [--md out.md]
数据来源：
  logs/p9-{a-768p,b-768p-shift12,c-768p-multiref}.log   解析参考条数 / 行数 / 耗时
  logs/p9-analysis.json                                 p9_analysis.py 产物（画质 + 组间 SSIM）
  logs/p9-motion.json                                   p1_motion.py 产物（运镜量化）
  logs/p9-audio.json                                    p1_audio.py 产物（音频谱形）
"""
import json
import os
import re
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"

GROUPS = {
    "A": ("p9-a-768p", "A 组 · Ref2VA 768p · 1 图参考 · shift 6.0", "1 图（写实橘猫）"),
    "B": ("p9-b-768p-shift12", "B 组 · Ref2VA 768p · 1 图参考 · shift 12.0", "1 图（写实橘猫）"),
    "C": ("p9-c-768p-multiref", "C 组 · Ref2VA 768p · 1 图 + 动作视频 + 音轨 · shift 6.0",
          "1 图（橘猫）+ 1 视频（横移摇摄）+ 1 音轨"),
    "D": ("p9-d-768p-shift8", "D 组 · Ref2VA 768p · 1 图参考 · shift 8.0", "1 图（写实橘猫）"),
}


def parse_log(tag):
    p = f"{LAB}/logs/{tag}.log"
    if not os.path.exists(p):
        return None
    txt = open(p, errors="ignore").read()
    out = {}
    m = re.search(r"(\d+) reference\(s\) -> (\d+) conditioning rows, (\d+) reference video rows, "
                  r"(\d+) reference audio rows", txt)
    if m:
        out["n_ref"] = int(m.group(1))
        out["cond_rows"] = int(m.group(2))
        out["video_rows"] = int(m.group(3))
        out["audio_rows"] = int(m.group(4))
    m = re.search(r"first forward at (\d+) rows", txt)
    if m:
        out["fwd_rows"] = int(m.group(1))
    m = re.search(r"ran for (\d+) h (\d+) m(?: (\d+) s)?", txt)
    if m:
        out["sec"] = (int(m.group(1)) * 3600 + int(m.group(2)) * 60
                      + (int(m.group(3)) if m.group(3) else 0))
    else:
        m = re.search(r"ran for (\d+) m(?: (\d+) s)?", txt)
        if m:
            out["sec"] = int(m.group(1)) * 60 + (int(m.group(2)) if m.group(2) else 0)
    m = re.search(r"presentation: (\d+) tokens", txt)
    if m:
        out["tokens"] = int(m.group(1))
    m = re.search(r"baked AdaLN for (\d+) steps", txt)
    if m:
        out["adaln_steps"] = int(m.group(1))
    refs = re.findall(r"reference (\d+) \((image|video|audio) ([^)]*)\)", txt)
    out["refs"] = "; ".join(f"#{r[0]} {r[1]}" for r in refs)
    m = re.search(r"fitted -- (.+)", txt)
    if m:
        out["fitted"] = m.group(1).strip()
    m = re.search(r"runtime LoRA '([^']+)'", txt)
    if m:
        out["lora"] = os.path.basename(m.group(1))
    return out


def fmt_sec(s):
    if s is None:
        return "—"
    return f"{s // 60} 分 {s % 60} 秒"


def main():
    md = None
    argv = sys.argv[1:]
    if "--md" in argv:
        md = argv[argv.index("--md") + 1]

    logs = {k: parse_log(v[0]) for k, v in GROUPS.items()}
    ana = {}
    if os.path.exists(f"{LAB}/logs/p9-analysis.json"):
        ana = json.load(open(f"{LAB}/logs/p9-analysis.json"))
    mot = []
    if os.path.exists(f"{LAB}/logs/p9-motion.json"):
        mot = json.load(open(f"{LAB}/logs/p9-motion.json"))
    aud = []
    if os.path.exists(f"{LAB}/logs/p9-audio.json"):
        aud = json.load(open(f"{LAB}/logs/p9-audio.json"))

    L = []
    L.append("### 17.3.1 四组实测概览\n")
    L.append("| 组 | 参考构成 | 参考条数 | conditioning rows | reference video rows | "
             "reference audio rows | 前向行数 | 耗时 |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for k in ("A", "D", "B", "C"):
        if k not in GROUPS:
            continue
        tag, label, refs_desc = GROUPS[k]
        d = logs.get(k)
        if not d:
            L.append(f"| {label} | {refs_desc} | — | — | — | — | — | — |")
            continue
        L.append(f"| {label} | {refs_desc} | {d.get('n_ref','—')} | {d.get('cond_rows','—')} | "
                 f"{d.get('video_rows','—')} | {d.get('audio_rows','—')} | {d.get('fwd_rows','—')} | "
                 f"{fmt_sec(d.get('sec'))} |")

    ov = ana.get("overview", {})
    if ov:
        L.append("\n### 17.3.2 画质与稳定性（与第 8 轮 FL2VA 768p 同口径）\n")
        L.append("| 组 | 分辨率 | 帧数 | 细节能量 | 饱和度 | 对比度 | 抖动 | 冻结帧对 | 近黑帧 | "
                 "亮度 首→末 | 音频 RMS | 谱质心 |")
        L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
        order = ["A", "D", "B", "C", "p3fl_shift6", "p3fl_shift12"]
        for k in order:
            a = ov.get(k)
            if not a:
                continue
            au = a.get("audio", {})
            L.append(f"| {k} | {a.get('resolution','?')} | {a.get('frames','?')} | "
                     f"{a.get('detail_canvas','?')} | {a.get('sat_mean','?')} | "
                     f"{a.get('contrast','?')} | {a.get('jitter','?')} | {a.get('frozen_pairs','?')} | "
                     f"{a.get('near_black_frames','?')} | {a.get('y_first','?')}→{a.get('y_last','?')} | "
                     f"{au.get('rms','—')} | {au.get('centroid_hz','—')} |")

    pairs = ana.get("pairs", {})
    if pairs:
        L.append("\n### 17.3.3 组间 SSIM / PSNR（视频流直接比）\n")
        L.append("| 对比 | 说明 | SSIM | PSNR (dB) |")
        L.append("|---|---|---:|---:|")
        for k, v in pairs.items():
            ps = v.get("psnr")
            ps = f"{ps:.2f}" if isinstance(ps, (int, float)) else "—"
            L.append(f"| {k} | {v.get('desc','')} | {v.get('ssim',0):.4f} | {ps} |")

    if mot:
        L.append("\n### 17.3.4 运镜量化（相位相关，256×144 口径）\n")
        L.append("| 视频 | 帧数 | net dx (px) | mean\\|dx\\| | net dy (px) | 净变焦 | 运动能量 mean |")
        L.append("|---|---:|---:|---:|---:|---:|---:|")
        for r in mot:
            nm = os.path.basename(r.get("path", ""))
            L.append(f"| {nm} | {r.get('frames','?')} | {r.get('net_dx',0):+.2f} | "
                     f"{r.get('mean_abs_dx',0):.3f} | {r.get('net_dy',0):+.2f} | "
                     f"{r.get('net_zoom_pct',0):+.2f}% | {r.get('mean_energy',0):.3f} |")

    if aud:
        import numpy as np
        L.append("\n### 17.3.5 音频谱形（与动作参考音轨对照）\n")
        L.append("| 音频 | RMS | 谱质心 (Hz) | 低频占比 | 中频 | 高频 | 与参考的包络相关 r |")
        L.append("|---|---:|---:|---:|---:|---:|---:|")
        ref_env = np.array(aud[0]["envelope"])
        for i, r in enumerate(aud):
            nm = os.path.basename(r.get("path", ""))
            env = np.array(r.get("envelope", []))
            if i == 0 or len(env) == 0 or env.std() < 1e-9 or ref_env.std() < 1e-9:
                rr = "—"
            else:
                rr = f"{np.corrcoef(ref_env, env)[0, 1]:+.3f}"
            L.append(f"| {nm} | {r.get('rms',0):.5f} | {r.get('centroid_hz',0):.0f} | "
                     f"{r.get('low_ratio',0):.3f} | {r.get('mid_ratio',0):.3f} | "
                     f"{r.get('high_ratio',0):.3f} | {rr} |")

    text = "\n".join(L)
    print(text)
    if md:
        with open(md, "w") as f:
            f.write(text + "\n")
        print(f"\n写出 {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
