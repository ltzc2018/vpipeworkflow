#!/usr/bin/env python3
"""P9 主体裁切对照图：把 A/B/C 在**同一裁切区**（主体胸像）放大并排

为什么需要它
------------
p9_sharpness.py 给出量化结论：Ref2VA 768p 上 shift 12.0 组的「纹理 ÷ 噪点」比
shift 6.0 组高 11.5%，与第 8 轮 FL2VA 的结论**方向相反**。
但「拉普拉斯方差高」可能只是噪点，必须有**同区域、同帧号、同样放大倍率**的
肉眼对照才能定性。本脚本固定取第 80 帧（画面中段，主体最清晰的一拍），
裁 420x420 的胸像区，放大 2 倍并排贴标签。

用法: p9_crop_compare.py [out.png]
"""
import os
import subprocess
import sys

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{LAB}/deliverables/images/p9-crop-compare.png"

FRAME = 80
CROP = "crop=420:420:462:150"
SCALE = "840:840"

ITEMS = [
    ("p9-ref2va-768p-a.mp4", "P9-A · Ref2VA 768p · shift 6.0 · 1图"),
    ("p9-ref2va-768p-d-shift8.mp4", "P9-D · Ref2VA 768p · shift 8.0 · 1图"),
    ("p9-ref2va-768p-b-shift12.mp4", "P9-B · Ref2VA 768p · shift 12.0 · 1图"),
    ("p9-ref2va-768p-c-multiref.mp4", "P9-C · Ref2VA 768p · shift 6.0 · 1图+动作视频+音轨"),
    ("p3-768p-shift6.mp4", "参照 · 第8轮 FL2VA 768p · shift 6.0"),
    ("p3-768p-shift12.mp4", "参照 · 第8轮 FL2VA 768p · shift 12.0"),
]


def main():
    tmp = "/tmp/p9-crop-compare"
    os.makedirs(tmp, exist_ok=True)
    inputs = []
    labels = []
    for i, (name, label) in enumerate(ITEMS):
        src = f"{WS}/out/{name}"
        if not os.path.exists(src):
            print(f"跳过（无产物）{name}")
            continue
        dst = f"{tmp}/c{i}.png"
        subprocess.run(
            [FF, "-y", "-v", "error", "-i", src,
             "-vf", f"select=eq(n\\,{FRAME}),{CROP},scale={SCALE}:flags=lanczos",
             "-fps_mode", "passthrough", "-frames:v", "1", dst],
            check=True)
        inputs.append(dst)
        labels.append(label)

    if not inputs:
        print("没有可用产物")
        return 1

    args = []
    for p in inputs:
        args += ["-i", p]
    fc = []
    stack = ""
    for i in range(len(inputs)):
        fc.append(f"[{i}:v]drawbox=x=0:y=0:w=840:h=40:color=black@0.75:t=fill,"
                  f"drawtext=fontfile='{FONT}':text='{labels[i]}':x=10:y=9:fontsize=22:fontcolor=white[s{i}]")
        stack += f"[s{i}]"
    fc.append(f"{stack}hstack=inputs={len(inputs)}[row]")
    subprocess.run([FF, "-y", "-v", "error"] + args + ["-filter_complex", ";".join(fc),
                    "-map", "[row]", "-frames:v", "1", OUT], check=True)
    print(f"写出 {OUT}（第 {FRAME} 帧 · 裁切 {CROP} · 放大 2 倍 · {len(inputs)} 列）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
