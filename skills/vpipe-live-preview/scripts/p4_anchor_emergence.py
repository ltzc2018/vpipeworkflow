#!/usr/bin/env python3
"""P4：锚定主体在实时预览里的「涌现曲线」。

每一拍（= 每步的干净估计）都在循环播放同一段 clip，不同拍之间的相位不对齐。
align0.ssim 已经给出「成片首帧 vs 预览每一帧」的 SSIM 曲线，
用它可以在每一拍内定位该拍的相位 0 帧（= clip 的第 0 帧 = 视频首帧位置），
从而：
  1) 给出每一拍在「视频首帧这个位置」上与成片首帧的相似度
     —— 这就是「锚定主体在第几步就已经在预览里可辨认」
  2) 产出真正相位一致的「逐步收敛」印相

用法： p4_anchor_emergence.py <tag> <clip_frames> <segment2.mp4>
"""
import json
import os
import re
import shutil
import subprocess
import sys

# ---- 路径配置：优先环境变量，其次 PATH 上的 ffmpeg，最后本机默认 ----
FF = (os.environ.get("VPIPE_FFMPEG")
      or shutil.which("ffmpeg")
      or "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")
LAB = os.environ.get("VPIPE_LAB",
                     os.path.join(os.path.expanduser("~"), "WorkBuddy",
                                  "vpipe-lab"))
OUTROOT = os.environ.get("VPIPE_P4_OUT",
                         os.path.join(LAB, "deliverables", "p4-preview"))
LOGROOT = os.environ.get("VPIPE_LOG_DIR", os.path.join(LAB, "logs"))
WORKROOT = os.environ.get("VPIPE_P4_WORK", os.path.join(LAB, "frames-p4"))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def read_curve(path):
    c = []
    if not os.path.exists(path):
        return c
    for line in open(path):
        m = re.search(r"All:([0-9.]+)", line)
        if m:
            c.append(float(m.group(1)))
    return c


def main():
    tag = sys.argv[1]
    clipf = int(sys.argv[2])
    seg = sys.argv[3]
    quant = json.load(open(os.path.join(LOGROOT, f"p4-quant-{tag}.json")))
    groups = quant["beats"]
    work = os.path.join(WORKROOT, tag)
    outdir = os.path.join(OUTROOT, tag)

    c0 = read_curve(os.path.join(work, "align0.ssim"))
    if not c0:
        print("缺 align0.ssim，先跑 p4_beats.py")
        return 1

    rows, picks = [], []
    for gi, g in enumerate(groups):
        lo = g[0] * clipf
        hi = min((g[-1] + 1) * clipf, len(c0)) - 1
        if lo >= len(c0):
            continue
        seg_c = c0[lo:hi + 1]
        best = max(seg_c)
        idx = lo + seg_c.index(best)
        picks.append((gi, idx))
        rows.append((gi + 1, g[0], g[-1], idx, best))

    print(f"[{tag}] 每一拍在「视频首帧位置」上与成片首帧的相似度：")
    print("| 步骤 | 预览帧区间(循环) | 相位0帧 | SSIM(成片首帧,该帧) |")
    print("|---|---|---|---|")
    for step, g0, g1, idx, best in rows:
        print(f"| step{step} | {g0}..{g1} | {idx} | **{best:.4f}** |")

    # 相位一致的印相：抽每拍的相位 0 帧
    picks_idx = [p[1] for p in picks]
    tmp = os.path.join(work, "_emerg")
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    expr = "+".join(f"eq(n\\,{i})" for i in picks_idx)
    run(f'{FF} -y -i "{seg}" -vf "select=\'{expr}\',scale=384:216" '
        f'-fps_mode passthrough "{tmp}/e-%05d.png"')
    files = sorted(os.listdir(tmp))
    inputs, filt, k = "", "", 0
    for (gi, idx), fn in zip(picks, files):
        src = os.path.join(tmp, fn)
        inputs += f' -i "{src}"'
        filt += (f"[{k}:v]drawtext=text='step{gi + 1}':x=6:y=6:fontsize=20:"
                 f"fontcolor=white:box=1:boxcolor=black@0.65[vt{k}];")
        k += 1
    stack = "".join(f"[vt{i}]" for i in range(k))
    out = os.path.join(outdir, "contact-sheet-anchor-emergence.png")
    run(f'{FF} -y{inputs} -filter_complex "{filt}{stack}hstack=inputs={k}[v]" '
        f'-map "[v]" -frames:v 1 "{out}"')
    print(f"\n[{tag}] 相位一致印相 -> {out} ({k} 格)")

    os.makedirs(LOGROOT, exist_ok=True)
    with open(os.path.join(LOGROOT, f"p4-emergence-{tag}.json"), "w") as f:
        json.dump({"tag": tag, "rows": rows, "picks": picks}, f,
                  ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
