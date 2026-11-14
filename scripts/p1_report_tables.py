#!/usr/bin/env python3
"""P1 汇总：把日志 + 度量结果拼成报告用的 Markdown 表格

用法: p1_report_tables.py [--md out.md]
"""
import json
import os
import re
import subprocess
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"

GROUPS = {
    "a": ("A 组 · 仅主体图", "1 图（写实橘猫）"),
    "b": ("B 组 · 主体图 + 风格图", "2 图（橘猫 + 水彩熊猫）"),
    "c": ("C 组 · 2 图 + 动作视频 + 音轨", "3 图？→ 2 图 + 1 视频 + 1 音轨"),
    "d": ("D 组 · 3 图 + 动作视频 + 音轨", "3 图（橘猫 / 熊猫 / 熊猫特写）+ 1 视频 + 1 音轨"),
}


def parse_log(g):
    p = f"{LAB}/logs/p1-{g}.log"
    if not os.path.exists(p):
        return None
    txt = open(p, errors="ignore").read()
    out = {}
    m = re.search(r"(\d+) reference\(s\) -> (\d+) conditioning rows, (\d+) reference video rows, (\d+) reference audio rows", txt)
    if m:
        out["n_ref"] = int(m.group(1))
        out["cond_rows"] = int(m.group(2))
        out["video_rows"] = int(m.group(3))
        out["audio_rows"] = int(m.group(4))
    m = re.search(r"first forward at (\d+) rows", txt)
    if m:
        out["fwd_rows"] = int(m.group(1))
    m = re.search(r"ran for (\d+) m (\d+) s", txt)
    if m:
        out["sec"] = int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"presentation: (\d+) tokens", txt)
    if m:
        out["tokens"] = int(m.group(1))
    m = re.search(r"reference (\d+) \((image|video|audio) ([^)]*)\)", txt)
    refs = re.findall(r"reference (\d+) \((image|video|audio) ([^)]*)\)", txt)
    out["refs"] = "; ".join(f"{r[0]}:{r[1]}" for r in refs)
    m = re.search(r"fitted -- (.+)", txt)
    if m:
        out["fitted"] = m.group(1).strip()
    return out


def ssim_psnr(vid, ref):
    """口径 A：视频流直接与图片比（ffmpeg lavfi）。

    SSIM 取 **All:** 聚合值（Y/U/V 合并），与历史表格（anchor-fidelity.sh）同口径。
    PSNR 取滤镜汇总行的 average。
    """
    sf = "/tmp/p1_ssim.txt"
    p = subprocess.run([FF, "-hide_banner", "-i", vid, "-i", ref, "-lavfi",
                        f"[0:v][1:v]ssim=stats_file={sf};[0:v][1:v]psnr", "-f", "null", "-"],
                       capture_output=True, text=True)
    err = p.stderr
    ssim_all = psnr_avg = ""
    for line in err.splitlines():
        if "SSIM" in line and "All:" in line:
            ssim_all = line.split("All:")[1].split()[0]
        if "PSNR" in line and "average:" in line:
            psnr_avg = line.split("average:")[1].split()[0]
    xs = []
    if os.path.exists(sf):
        for line in open(sf):
            if line.startswith("n:") and "All:" in line:
                xs.append(float(line.split("All:")[1].split()[0]))
    if not xs:
        return "", psnr_avg
    ssim = (f"{sum(xs)/len(xs):.4f}"
            f"（首 {xs[0]:.4f} / 中 {xs[len(xs)//2]:.4f} / 末 {xs[-1]:.4f}）")
    return ssim, psnr_avg


def prep_ref(src, dst, w=832, h=480):
    subprocess.run([FF, "-y", "-v", "error", "-i", src, "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                    "-pix_fmt", "rgb24", dst], capture_output=True)


def main():
    out_md = None
    if "--md" in sys.argv:
        out_md = sys.argv[sys.argv.index("--md") + 1]

    motion = {}
    mj = f"{LAB}/logs/p1-motion.json"
    if os.path.exists(mj):
        for r in json.load(open(mj)):
            motion[os.path.basename(r["path"])] = r

    lines = []
    lines.append("### 表 15-1　四组的运行与条件规模\n")
    lines.append("| 组 | 参考构成 | 参考条数 | conditioning rows | reference video rows | reference audio rows | 前向行数 | 耗时 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for g, (name, desc) in GROUPS.items():
        lg = parse_log(g)
        vid = f"{WS}/out/p1-{g}-multi-ref.mp4"
        if not lg or not os.path.exists(vid):
            continue
        t = lg.get("sec")
        t = f"{t//60} 分 {t%60} 秒" if t else "—"
        lines.append(f"| {name} | {desc} | {lg.get('n_ref','—')} | {lg.get('cond_rows','—')} | "
                     f"{lg.get('video_rows','—')} | {lg.get('audio_rows','—')} | "
                     f"{lg.get('fwd_rows','—')} | {t} |")

    lines.append("\n### 表 15-2　各组与主体参考图（橘猫）的像素保真度\n")
    lines.append("> 口径 A：视频流直接与图片比（ffmpeg `lavfi ssim/psnr`），YUV 4:2:0 色度往返损失计入。")
    lines.append("> 全部被测对象用同一口径，组间可比。\n")
    lines.append("| 组 | 帧数 | 全片平均 SSIM | 首帧 / 中帧 / 末帧 SSIM | 全片平均 PSNR |")
    lines.append("|---|---:|---|---|---:|")
    ref_png = "/tmp/p1_ref_cat.png"
    prep_ref(f"{WS}/refs/minimax-h3-reference-subject.jpg", ref_png)
    for g in ("a", "b", "c", "d"):
        vid = f"{WS}/out/p1-{g}-multi-ref.mp4"
        if not os.path.exists(vid):
            continue
        ssim, psnr = ssim_psnr(vid, ref_png)
        n = 0
        if os.path.exists("/tmp/p1_ssim.txt"):
            n = sum(1 for l in open("/tmp/p1_ssim.txt") if l.startswith("n:"))
        lines.append(f"| {GROUPS[g][0]} | {n} | {ssim} | {psnr or '—'} dB |")

    if motion:
        lines.append("\n### 表 15-3　运动学：输出 vs 动作参考视频\n")
        lines.append("| 视频 | 帧数 | 全局横移 net dx (px @256 宽) | 全局纵移 net dy | 运动能量 mean | 与动作参考的能量曲线相关 r |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        ref = motion.get("motion-pan-right-124f.mp4")
        for name, r in motion.items():
            if r is None:
                continue
            prof = r.get("energy_profile")
            rr = "—"
            if ref and name != "motion-pan-right-124f.mp4" and prof:
                import numpy as np
                a = np.array(ref["energy_profile"]); b = np.array(prof)
                rr = f"{np.corrcoef(a, b)[0,1]:.4f}" if a.std() > 1e-9 and b.std() > 1e-9 else "n/a"
            lines.append(f"| {name} | {r['frames']} | {r['net_dx']:+.1f} | {r['net_dy']:+.1f} | "
                         f"{r['mean_energy']:.3f} | {rr} |")

    txt = "\n".join(lines)
    print(txt)
    if out_md:
        with open(out_md, "w") as f:
            f.write(txt + "\n")
        print(f"\n写出 {out_md}")


if __name__ == "__main__":
    main()
