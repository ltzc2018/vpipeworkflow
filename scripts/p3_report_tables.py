#!/usr/bin/env python3
"""P3 报告表格生成：从日志与量化 JSON 直接产出 Markdown 表格。

用法: python3 p3_report_tables.py [--md <输出.md>]
"""
import json
import os
import re
import sys

LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
LOGS = os.path.join(LAB, "logs")

RUNS = [
    ("shift6",  "p3-shift6-124f",  "1344x768 · shift 6.0 · 8 步 v1.0"),
    ("shift12", "p3-shift12-124f", "1344x768 · shift 12.0 · 8 步 v1.0"),
    ("long241", "p3-shift6-241f",  "1344x768 · shift 6.0 · 8 步 v1.0 · 241 帧"),
    ("544p",    "p3-544p-124f",    "960x544 · shift 12.0 · 8 步 v1.0"),
    ("4step",   "p3-4step-124f",   "1344x768 · shift 6.0 · 4 步 v1.2"),
    ("ext-part1", "p3-ext-part1",  "832x480 · shift 12.0 · Pika fl2va · 6 步 · 续接第 1 段"),
    ("ext-part2", "p3-ext-part2",  "832x480 · Ref2VA 续接 · 上一段末 90 帧 + 音轨"),
    ("ext-part3", "p3-ext-part3",  "832x480 · Ref2VA 续接"),
    ("ext-part4", "p3-ext-part4",  "832x480 · Ref2VA 续接"),
]


def parse_log(logname):
    p = os.path.join(LOGS, logname + ".log")
    if not os.path.exists(p):
        return {}
    txt = open(p, errors="replace").read()
    info = {}
    m = re.search(r"at (\d+)x(\d+)x(\d+) frames, (\d+) steps, shifts ([\d.]+)/([\d.]+)", txt)
    if m:
        info["spec"] = f"{m.group(1)}x{m.group(2)}"
        info["frames"] = int(m.group(3))
        info["steps"] = int(m.group(4))
        info["shifts"] = f"{m.group(5)}/{m.group(6)}"
    m = re.search(r"first forward at (\d+) rows", txt)
    if m:
        info["rows"] = int(m.group(1))
    m = re.search(r"states shifts ([\d.]+)/([\d.]+) and this graph runs ([\d.]+)/([\d.]+)", txt)
    if m:
        info["shift_mismatch"] = f"适配器 {m.group(1)}/{m.group(2)} vs 图 {m.group(3)}/{m.group(4)}"
    m = re.search(r"runtime LoRA '([^']+)'", txt)
    if m:
        info["lora"] = m.group(1).split("/")[-1]
    m = re.search(r"residency probe (\d+) blocks of \d+ \(([^)]+)\), (\d+) MB reclaimable, wire budget (\d+) MB", txt)
    if m:
        info["blocks"] = int(m.group(1))
        info["reclaimable_mb"] = int(m.group(3))
        info["wire_budget_mb"] = int(m.group(4))
    m = re.search(r"resident weights are only (\d+)% in RAM \((\d+) of (\d+) sampled pages paged out, (\d+) MB wired\)", txt)
    if m:
        info["resident_pct"] = int(m.group(1))
        info["paged_out"] = f"{m.group(2)}/{m.group(3)}"
        info["wired_mb"] = int(m.group(4))
    m = re.search(r"DiT residency ended at (\d+) of (\d+) blocks \((\d+) MB\)", txt)
    if m:
        info["residency_end"] = f"{m.group(1)}/{m.group(2)} 块 · {m.group(3)} MB"
    sp = os.path.join(LOGS, logname + ".seconds")
    if os.path.exists(sp):
        s = int(open(sp).read().strip())
        info["seconds"] = s
        info["minutes"] = f"{s // 60} 分 {s % 60} 秒"
    mp = os.path.join(LOGS, logname + ".mem")
    if os.path.exists(mp):
        vals = []
        for line in open(mp):
            m = re.search(r"free_pct=(\d+)", line)
            if m:
                vals.append(int(m.group(1)))
        if vals:
            info["min_free_pct"] = min(vals)
            info["max_free_pct"] = max(vals)
    return info


def main():
    md_out = None
    if "--md" in sys.argv:
        md_out = sys.argv[sys.argv.index("--md") + 1]

    # --- 表 1：运行规格与资源 ---
    lines = ["| 组 | 规格 | 前向行数 | 耗时 | 步数 | 最低可用内存 | 换出情况 | 备注 |",
             "|---|---|---|---|---|---|---|---|"]
    for key, logname, desc in RUNS:
        info = parse_log(logname)
        if not info:
            continue
        notes = []
        if info.get("shift_mismatch"):
            notes.append("**shift 不匹配**：" + info["shift_mismatch"])
        if info.get("resident_pct") is not None and info["resident_pct"] <= 5:
            notes.append(f"权重仅 {info['resident_pct']}% 常驻（{info.get('paged_out','?')} 页被换出，wired {info.get('wired_mb','?')} MB）")
        lines.append(
            f"| {key} | {desc} | {info.get('rows','—'):,} | {info.get('minutes','—')} | "
            f"{info.get('steps','—')} | {info.get('min_free_pct','—')}% | "
            f"{info.get('residency_end','—')} | {'；'.join(notes) if notes else '—'} |"
            if info.get("rows") else
            f"| {key} | {desc} | — | {info.get('minutes','—')} | {info.get('steps','—')} | "
            f"{info.get('min_free_pct','—')}% | {info.get('residency_end','—')} | "
            f"{'；'.join(notes) if notes else '—'} |")
    table = "\n".join(lines)

    # --- 表 2/3：量化 JSON ---
    q = os.path.join(LOGS, "p3-analysis.json")
    qtable = ""
    if os.path.exists(q):
        d = json.load(open(q))
        ovl = ["| 组 | 分辨率 | 时长 | 帧数 | 细节能量(原生) | 细节能量(画布) | 饱和度 | 对比度 | 抖动 | 冻结帧对 | 首帧亮度 | 末帧亮度 | 音频 RMS | 音频谱质心 |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, v in d.get("overview", {}).items():
            au = v.get("audio", {})
            rms = f"{au.get('rms', 0):.4f}" if au.get("present") else "无"
            cen = f"{au.get('centroid_hz', 0):.0f} Hz" if au.get("present") else "无"
            ovl.append(
                f"| {k} | {v.get('resolution','—')} | {v.get('duration','—')} | {v.get('frames','—')} | "
                f"{v.get('detail_native',0):.1f} | {v.get('detail_canvas',0):.1f} | "
                f"{v.get('sat_mean',0):.4f} | {v.get('contrast',0):.1f} | "
                f"{v.get('jitter',0):.2f} | {v.get('frozen_pairs','—')} | "
                f"{v.get('y_first',0):.1f} | {v.get('y_last',0):.1f} | {rms} | {cen} |")
        ql = ["| 对照 | SSIM | PSNR |", "|---|---|---|"]
        for k, v in d.get("pairs", {}).items():
            s = v.get("ssim")
            ps = v.get("psnr")
            ql.append(f"| {k} | {s:.4f} | {ps if ps != '' else '—'} |" if s != "" else f"| {k} | — | {ps if ps != '' else '—'} |")
        qtable = ("\n\n### 产物概览（细节能量越大越锐）\n\n" + "\n".join(ovl) +
                  "\n\n### 组间对比（视频流直接比口径）\n\n" + "\n".join(ql))

    # --- 表 4：续接接缝 ---
    e = os.path.join(LOGS, "p3-ext-analysis.json")
    etable = ""
    if os.path.exists(e):
        ed = json.load(open(e))
        el = ["| 接缝 | 接缝 SSIM | 接缝 PSNR | Δ亮度 | 段内基线 p5 | 判定 |", "|---|---|---|---|---|---|"]
        for k, v in ed.get("seams", {}).items():
            el.append(f"| {k} | {v.get('seam_ssim','—')} | {v.get('seam_psnr','—')} | "
                      f"{v.get('seam_dY','—')} | {v.get('inside_p5_baseline','—')} | "
                      f"{v.get('verdict','—')} |")
        pl = ["| 段 | 分辨率 | 时长 | 帧数 | 段内 SSIM p5 / p50 / p95 | 冻结帧对 |", "|---|---|---|---|---|---|"]
        for k, v in ed.get("parts", {}).items():
            pl.append(f"| {k} | {v.get('resolution','—')} | {v.get('duration','—')} | {v.get('frames','—')} | "
                      f"{v.get('inside_ssim_p5','—')} / {v.get('inside_ssim_p50','—')} / {v.get('inside_ssim_p95','—')} | "
                      f"{v.get('frozen_pairs','—')} |")
        fu = ed.get("full", {})
        etable = ("\n\n### 续接接缝（关键判据：接缝 SSIM 是否落在段内正常分布内）\n\n" + "\n".join(el) +
                  "\n\n### 各段内相邻帧基线\n\n" + "\n".join(pl))
        if fu:
            etable += (f"\n\n拼接片：{fu.get('resolution')} · {fu.get('duration')} · {fu.get('frames')} 帧 · "
                       f"段边界帧间差 {fu.get('seam_frame_diffs')}（段内中位数 {fu.get('median_frame_diff')}）· "
                       f"冻结帧对 {fu.get('frozen_pairs')}")

    out = table + qtable + etable
    print(out)
    if md_out:
        with open(md_out, "w") as f:
            f.write(out + "\n")
        print(f"\n写出 {md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
