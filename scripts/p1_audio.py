#!/usr/bin/env python3
"""P1 音频通道量化：参考音轨是否被搬运到输出里

三个指标：
  1) low_ratio   —— 低频（<200 Hz）能量占比。海浪/脚步这类隆隆声偏高，鸟鸣/风声偏低
  2) centroid   —— 谱质心（Hz）。低 = 厚重，宽频环境音（浪+风）会拉高
  3) env_r      —— 对数谱包络与参考音轨的 Pearson 相关（谱形状是否像）

用法: p1_audio.py <ref.wav/mp4> <out1.mp4> [out2.mp4 ...] [--json out.json]
"""
import json
import subprocess
import sys

import numpy as np

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
SR = 16000


def pcm(path):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def envelope(x, nband=32):
    """对数谱包络：nband 个对数间隔频带的中位能量"""
    n = len(x)
    if n < 2048:
        return np.zeros(nband)
    win = 2048
    hop = 1024
    frames = []
    for s in range(0, n - win, hop):
        seg = x[s:s + win] * np.hanning(win)
        mag = np.abs(np.fft.rfft(seg)) ** 2
        frames.append(mag)
    if not frames:
        return np.zeros(nband)
    P = np.array(frames)
    edges = np.unique(np.round(np.geomspace(1, P.shape[1], nband + 1)).astype(int))
    bands = []
    for i in range(len(edges) - 1):
        b = P[:, edges[i]:edges[i + 1]]
        bands.append(np.log10(b.mean() + 1e-12))
    return np.array(bands)


def analyse(path):
    x = pcm(path)
    if len(x) == 0:
        return {"path": path, "samples": 0}
    spec = np.abs(np.fft.rfft(x[: min(len(x), SR * 20)])) ** 2
    freqs = np.fft.rfftfreq(min(len(x), SR * 20), 1.0 / SR)
    tot = spec.sum() + 1e-12
    low = spec[freqs < 200].sum() / tot
    mid = spec[(freqs >= 200) & (freqs < 2000)].sum() / tot
    hi = spec[freqs >= 2000].sum() / tot
    centroid = float((spec * freqs).sum() / tot)
    env = envelope(x)
    return {
        "path": path,
        "duration_s": round(len(x) / SR, 3),
        "rms": float(np.sqrt((x ** 2).mean())),
        "low_ratio": float(low),
        "mid_ratio": float(mid),
        "high_ratio": float(hi),
        "centroid_hz": centroid,
        "envelope": env.tolist(),
    }


def main():
    argv = sys.argv[1:]
    out_json = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = argv[i + 1]
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    res = [analyse(p) for p in args]
    ref = res[0]
    print(f"{'对象':34s} {'时长s':>7s} {'RMS':>8s} {'低频占比':>9s} {'中频':>8s} {'高频':>8s} {'质心Hz':>8s} {'谱形r':>8s}")
    print("-" * 100)
    for r in res:
        if r.get("samples", 1) == 0:
            print(f"{r['path'][-34:]:34s}  (无音轨)")
            continue
        if r is ref:
            rr = "—"
        else:
            a = np.array(ref["envelope"])
            b = np.array(r["envelope"])
            rr = "n/a" if a.std() < 1e-9 or b.std() < 1e-9 else f"{np.corrcoef(a, b)[0, 1]:+.3f}"
        print(f"{r['path'][-34:]:34s} {r['duration_s']:7.2f} {r['rms']:8.4f} "
              f"{r['low_ratio']:9.3f} {r['mid_ratio']:8.3f} {r['high_ratio']:8.3f} "
              f"{r['centroid_hz']:8.0f} {rr:>8s}")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(res, f, indent=2)
        print(f"\n写出 {out_json}")


if __name__ == "__main__":
    main()
