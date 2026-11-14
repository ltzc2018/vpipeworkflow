#!/usr/bin/env python3
"""P3 量化分析：768p / 长规格 的画质、稳定性、音频证据

口径说明
--------
SSIM/PSNR 一律用 **视频流直接比**（`-lavfi "[0:v][1:v]ssim"`），
不落盘 PNG 再比——后者会额外经过 YUV 4:2:0 色度往返，SSIM 偏低约 0.03。
报告里凡出现 SSIM/PSNR 都注明这一口径。

细节能量 = 逐帧拉普拉斯响应的方差（高通），反映"高频细节有多少"。
给出两种口径，避免分辨率不同导致的不可比：
  * native  —— 各组按**原生分辨率**算（绝对锐度）
  * canvas  —— 各组统一缩放到 1344x768 再算（交付尺寸上的残余锐度）

时序指标：
  * jitter   —— 相邻帧平均绝对差（闪烁/抖动）
  * frozen   —— 几乎零变化的相邻帧对数（卡帧/停滞）
  * detail_first_third / detail_last_third —— 细节能量的前 1/3 与后 1/3 均值
                （回答"长规格尾部会不会劣化"）

音频指标：RMS / 峰值 / 是否静音 / 谱质心 / 低频占比。
"""
import json
import os
import subprocess
import sys

import numpy as np

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
CANVAS_W, CANVAS_H = 1344, 768


def ssim_psnr_stream(a, b, seconds=None):
    """视频流直接比：返回 (ssim_all, psnr_avg)。"""
    sf, pf = "/tmp/p3_ssim.txt", "/tmp/p3_psnr.txt"
    for f in (sf, pf):
        if os.path.exists(f):
            os.remove(f)
    pre = ["-t", str(seconds)] if seconds else []
    subprocess.run([FF, "-hide_banner", "-i", a, "-i", b,
                    "-lavfi", f"[0:v][1:v]ssim=stats_file={sf}"] + pre +
                   ["-f", "null", "-"], capture_output=True)
    subprocess.run([FF, "-hide_banner", "-i", a, "-i", b,
                    "-lavfi", f"[0:v][1:v]psnr=stats_file={pf}"] + pre +
                   ["-f", "null", "-"], capture_output=True)
    ssim, psnr = "", ""
    if os.path.exists(sf):
        # stats_file 每行形如 "n:1 Y:0.575 U:0.5 V:0.5 All:0.98" —— 要按 key 取 All
        xs = []
        for l in open(sf):
            if not l.startswith("n:"):
                continue
            for tok in l.split():
                if tok.startswith("All:"):
                    xs.append(float(tok[4:]))
                    break
        if xs:
            ssim = sum(xs) / len(xs)
    if os.path.exists(pf):
        for line in open(pf):
            if "psnr_avg:" in line:
                psnr = float(line.split("psnr_avg:")[1].split()[0])
                break
    return ssim, psnr


def gray_frames(path, w, h):
    """返回 uint8 帧序列 (N, h*w)。保持 uint8 以控制内存峰值（768p×243 帧 ≈ 250 MB）。"""
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0",
         "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    n = w * h
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, n)


def lap_series(fr, h, w):
    """逐帧拉普拉斯响应方差序列（越大越锐）。逐帧转 float32，避免整段展开。"""
    if len(fr) == 0:
        return np.zeros(0)
    out = np.empty(len(fr), dtype=np.float64)
    for i in range(len(fr)):
        a = fr[i].reshape(h, w).astype(np.float32)
        lap = (-4 * a[1:-1, 1:-1]
               + a[:-2, 1:-1] + a[2:, 1:-1]
               + a[1:-1, :-2] + a[1:-1, 2:])
        out[i] = lap.var()
    return out


def frame_count(path):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0", "-f", "rawvideo",
         "-pix_fmt", "gray", "-s", "16x16", "-"], capture_output=True).stdout
    return len(raw) // 256


def probe(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    txt = out.stderr or ""
    info = {}
    for line in txt.splitlines():
        if "Duration:" in line:
            info["duration"] = line.split("Duration:")[1].split(",")[0].strip()
        if "Stream #0:0" in line:
            seg = line.split("Video:")[-1]
            for tok in seg.split(","):
                tok = tok.strip()
                if "x" in tok and tok.replace("x", "").replace(":", "").isdigit():
                    info["resolution"] = tok
                if tok.endswith("fps"):
                    info["fps"] = tok.split()[0]
        if "Stream #0:1" in line and "Audio" in line:
            info["audio"] = "yes"
    info["bytes"] = os.path.getsize(path)
    info["frames"] = frame_count(path)
    return info


def audio_stats(path):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
         "-f", "s16le", "-"], capture_output=True).stdout
    if len(raw) == 0:
        return {"present": False}
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if len(x) < 1024:
        return {"present": True, "samples": int(len(x)), "silent": True}
    rms = float(np.sqrt((x ** 2).mean()))
    peak = float(np.abs(x).max())
    n = min(len(x), 16000 * 20)
    spec = np.abs(np.fft.rfft(x[:n])) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / 16000)
    tot = spec.sum() + 1e-12
    centroid = float((spec * freqs).sum() / tot)
    low = float(spec[freqs < 200].sum() / tot)
    return {"present": True, "seconds": round(len(x) / 16000.0, 2),
            "rms": round(rms, 5), "peak": round(peak, 5),
            "silent": bool(rms < 1e-4), "centroid_hz": round(centroid, 1),
            "low_ratio": round(low, 4)}


def color_stats(path, w=256, h=144):
    """色彩统计：饱和度 / 对比度。用于暴露「采样网格用错 → 饱和度漂移」这类问题。"""
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-map", "0:v:0", "-vf", f"scale={w}:{h}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) == 0:
        return {}
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w, 3).astype(np.float32)
    mx = rgb.max(axis=3)
    mn = rgb.min(axis=3)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)
    g = rgb.mean(axis=3)
    return {"sat_mean": round(float(s.mean()), 4),
            "sat_max": round(float(s.mean(axis=(1, 2)).max()), 4),
            "contrast": round(float(g.std(axis=(1, 2)).mean()), 2)}


def analyse_video(path):
    p = probe(path)
    w, h = (int(x) for x in p.get("resolution", "640x360").split("x"))
    # 1) 原生分辨率细节能量（绝对锐度）——帧多时抽样到最多 160 帧控制内存
    fr = gray_frames(path, w, h)
    if len(fr) > 160:
        fr = fr[::(len(fr) // 160)][:160]
    series_native = lap_series(fr, h, w)
    # 2) 统一画布口径（交付尺寸上的残余锐度）；原生已等于画布时复用
    if (w, h) == (CANVAS_W, CANVAS_H):
        series_canvas = series_native
    else:
        fc = gray_frames(path, CANVAS_W, CANVAS_H)
        if len(fc) > 160:
            fc = fc[::(len(fc) // 160)][:160]
        series_canvas = lap_series(fc, CANVAS_H, CANVAS_W)
    del fr
    # 3) 时序指标（低分辨率，内存可忽略）
    g = gray_frames(path, 256, 144)
    dif = (np.abs(g[1:].astype(np.int16) - g[:-1].astype(np.int16)).mean(axis=1)
           if len(g) > 1 else np.zeros(0))
    frozen = int((dif < 0.05).sum()) if len(dif) else 0
    bright = g.mean(axis=1) if len(g) else np.zeros(0)
    third = max(1, len(series_canvas) // 3) if len(series_canvas) else 1
    out = {
        "resolution": p.get("resolution"), "duration": p.get("duration"),
        "frames": p.get("frames"), "fps": p.get("fps"), "bytes": p.get("bytes"),
        "has_audio": p.get("audio", "无"),
        "detail_native": round(float(series_native.mean()), 1) if len(series_native) else 0.0,
        "detail_canvas": round(float(series_canvas.mean()), 1) if len(series_canvas) else 0.0,
        "detail_first_third": round(float(series_canvas[:third].mean()), 1) if len(series_canvas) else 0.0,
        "detail_last_third": round(float(series_canvas[-third:].mean()), 1) if len(series_canvas) else 0.0,
        "jitter": round(float(dif.mean()), 3) if len(dif) else 0.0,
        "frozen_pairs": frozen,
        "y_first": round(float(bright[0]), 1) if len(bright) else 0.0,
        "y_last": round(float(bright[-1]), 1) if len(bright) else 0.0,
        "y_mean": round(float(bright.mean()), 1) if len(bright) else 0.0,
        "near_black_frames": int((bright < 8).sum()),
        "audio": audio_stats(path),
    }
    out.update(color_stats(path))
    return out


def upscale_to(src, dst, w, h):
    subprocess.run([FF, "-y", "-v", "error", "-i", src,
                    "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-pix_fmt", "yuv420p", dst], check=True)
    return dst


def main():
    out_json = sys.argv[1] if len(sys.argv) > 1 else "/tmp/p3-analysis.json"
    res = {}

    files = {
        "shift6":  f"{WS}/out/p3-768p-shift6.mp4",
        "shift12": f"{WS}/out/p3-768p-shift12.mp4",
        "544p":    f"{WS}/out/p3-544p-ref.mp4",
        "4step":   f"{WS}/out/p3-768p-4step.mp4",
        "long241": f"{WS}/out/p3-768p-shift6-241f.mp4",
    }
    exist = {k: v for k, v in files.items() if os.path.exists(v)}

    print("== 产物概览 ==")
    res["overview"] = {}
    for k, v in exist.items():
        a = analyse_video(v)
        a["path"] = v
        res["overview"][k] = a
        print(f"  {k:8s} {a.get('resolution','?'):>9s} {a.get('duration','?'):>9s} "
              f"帧={a.get('frames','?'):>4d} 音频={a['has_audio']:>3s} "
              f"细节(native/canvas)={a['detail_native']:>7.1f}/{a['detail_canvas']:>7.1f} "
              f"抖动={a['jitter']:.2f} 冻结={a['frozen_pairs']}")

    # 组间 SSIM/PSNR（视频流直接比）
    print("\n== 组间 SSIM/PSNR（视频流直接比） ==")
    res["pairs"] = {}
    res["_files"] = {}
    if "544p" in exist and "shift6" in exist:
        up = "/tmp/p3-544p-up.mp4"
        upscale_to(files["544p"], up, CANVAS_W, CANVAS_H)
        res["_files"]["544p_up"] = up
    pair_specs = [("shift6", "shift12", None),
                  ("shift6", "4step", None),
                  ("shift6", "long241", None),
                  ("544p_up", "shift6", None)]
    for a, b, sec in pair_specs:
        fa = res["_files"].get(a, files.get(a))
        fb = res["_files"].get(b, files.get(b))
        if not (fa and fb and os.path.exists(fa) and os.path.exists(fb)):
            continue
        s, ps = ssim_psnr_stream(fa, fb, sec)
        res["pairs"][f"{a} vs {b}"] = {"ssim": s, "psnr": ps}
        print(f"  {a:9s} vs {b:9s}  SSIM={s:.4f}  PSNR={ps if ps != '' else '—'}")

    with open(out_json, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n写出 {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
