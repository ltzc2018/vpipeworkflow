#!/usr/bin/env python3
"""P1 多参考组合 —— 视频运动学量化（相位相关 + 运动能量曲线）

用途：判断「动作参考视频的运镜是否被复现」。
方法：
  1) ffmpeg 解出 256x144 灰度原始帧
  2) 相邻帧做相位相关（FFT cross-power spectrum），得到全局平移 (dx, dy)
  3) 相邻帧绝对差均值 -> 运动能量曲线
  4) 两条曲线都可与参考视频做相关（Pearson r）

用法： python3 p1_motion.py <video.mp4> [more.mp4 ...] [--json out.json]
"""
import json
import subprocess
import sys

import numpy as np

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
W, H = 256, 144


def gray_frames(path):
    """解出 (N, H, W) 的 uint8 灰度帧"""
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (W * H)
    return np.frombuffer(raw[: n * W * H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)


def phase_corr(a, b):
    """求把 b 对齐到 a 所需的全局平移 (dy, dx)，单位像素"""
    wy = np.hanning(a.shape[0])[:, None]
    wx = np.hanning(a.shape[1])[None, :]
    win = wy * wx
    A = np.fft.fft2((a - a.mean()) * win)
    B = np.fft.fft2((b - b.mean()) * win)
    R = A * np.conj(B)
    R /= (np.abs(R) + 1e-9)
    r = np.fft.ifft2(R).real
    idx = np.unravel_index(np.argmax(r), r.shape)
    dy, dx = idx
    if dy > a.shape[0] // 2:
        dy -= a.shape[0]
    if dx > a.shape[1] // 2:
        dx -= a.shape[1]
    return float(dy), float(dx)


def zoom_about_center(img, s):
    """把 img 绕中心缩放 s 倍（s>1 放大），双线性插值"""
    h, w = img.shape
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    yy = np.clip((np.arange(h) - cy) / s + cy, 0, h - 1)
    xx = np.clip((np.arange(w) - cx) / s + cx, 0, w - 1)
    y0 = np.floor(yy).astype(int)
    x0 = np.floor(xx).astype(int)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    fy = (yy - y0)[:, None]
    fx = (xx - x0)[None, :]
    return (img[y0][:, x0] * (1 - fy) * (1 - fx) + img[y0][:, x1] * (1 - fy) * fx +
            img[y1][:, x0] * fy * (1 - fx) + img[y1][:, x1] * fy * fx)


ZOOM_CANDS = [0.97, 0.98, 0.99, 0.995, 1.0, 1.005, 1.01, 1.02, 1.03]


def zoom_rate(a, b, shift=(0.0, 0.0)):
    """估计 b 相对 a 的全局缩放速率（>0 = 推近 / zoom-in）

    先把 b 按全局平移对齐，否则横移会被误判成缩放。
    """
    dy, dx = shift
    if abs(dy) > 0.01 or abs(dx) > 0.01:
        h, w = b.shape
        yy = np.clip(np.arange(h) - dy, 0, h - 1).astype(int)
        xx = np.clip(np.arange(w) - dx, 0, w - 1).astype(int)
        b = b[yy][:, xx]
    best_s, best_c = 1.0, -2.0
    av = a - a.mean()
    av = av / (np.linalg.norm(av) + 1e-9)
    for s in ZOOM_CANDS:
        bb = zoom_about_center(b, s)
        bb = bb - bb.mean()
        bb = bb / (np.linalg.norm(bb) + 1e-9)
        c = float((av * bb).mean())
        if c > best_c:
            best_s, best_c = s, c
    return best_s - 1.0


def analyse(path):
    fr = gray_frames(path)
    n = len(fr)
    dxs, dys, eng, zoom = [], [], [], []
    for i in range(n - 1):
        dy, dx = phase_corr(fr[i], fr[i + 1])
        dys.append(dy)
        dxs.append(dx)
        eng.append(float(np.mean(np.abs(fr[i + 1] - fr[i]))))
        zoom.append(zoom_rate(fr[i], fr[i + 1], (dy, dx)))
    dxs = np.array(dxs)
    dys = np.array(dys)
    eng = np.array(eng)
    zoom = np.array(zoom)
    return {
        "path": path,
        "frames": n,
        "dx": dxs.tolist(),
        "dy": dys.tolist(),
        "energy": eng.tolist(),
        "zoom": zoom.tolist(),
        "mean_abs_dx": float(np.mean(np.abs(dxs))),
        "mean_abs_dy": float(np.mean(np.abs(dys))),
        "net_dx": float(dxs.sum()),
        "net_dy": float(dys.sum()),
        "net_zoom_pct": float(zoom.sum() * 100.0),
        "mean_energy": float(eng.mean()),
        "max_energy": float(eng.max()),
        "std_energy": float(eng.std()),
    }


def curve_profile(energy, k=32):
    """把能量曲线重采样到 k 点并做零均值单位方差化，用于跨视频相关"""
    e = np.asarray(energy, dtype=np.float64)
    if len(e) == 0:
        return np.zeros(k)
    x_old = np.linspace(0, 1, len(e))
    x_new = np.linspace(0, 1, k)
    p = np.interp(x_new, x_old, e)
    s = p.std()
    return (p - p.mean()) / s if s > 1e-9 else p - p.mean()


def pearson(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.std() < 1e-9 or b.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main():
    argv = sys.argv[1:]
    out_json = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = argv[i + 1]
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    results = []
    for p in args:
        r = analyse(p)
        results.append(r)
        print(f"{p}")
        print(f"  帧数        : {r['frames']}")
        print(f"  全局横移 dx : mean|dx|={r['mean_abs_dx']:.3f}  net={r['net_dx']:+.2f} px")
        print(f"  全局纵移 dy : mean|dy|={r['mean_abs_dy']:.3f}  net={r['net_dy']:+.2f} px")
        print(f"  运动能量    : mean={r['mean_energy']:.3f}  max={r['max_energy']:.3f}  std={r['std_energy']:.3f}")
    if len(results) > 1:
        print("\n两两能量曲线相关（Pearson r，32 点重采样）:")
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                r = pearson(curve_profile(results[i]["energy"]), curve_profile(results[j]["energy"]))
                print(f"  {results[i]['path'].split('/')[-1]}  vs  {results[j]['path'].split('/')[-1]} : r = {r:.4f}")
    if out_json:
        for r in results:
            r["energy_profile"] = curve_profile(r["energy"]).tolist()
        with open(out_json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n写出 {out_json}")


if __name__ == "__main__":
    main()
