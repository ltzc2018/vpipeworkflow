#!/usr/bin/env python3
"""P11 —— YUV 口径消融（唯一权威脚本）

════ 问题 ════
本报告第 15.4.2 / 17.3 / 18.1 节反复引用同一件事：
    「视频流直接比 ≈ 0.9736，PNG 落盘再比 ≈ 0.9445，差 0.03 来自 YUV 4:2:0 色度往返」
第 18.1 轮据此立项 P11：「既然上游已支持 4:4:4，这 0.03 就不该被当成固有开销」。

════ 本实验要回答的三个问题 ════
Q1  那 0.03 的差，方向到底是哪边高？差在「编码」还是在「比较域」？
Q2  换成 4:4:4 能不能消解这个差？
Q3  4:2:0 到底是不是**真的**丢色度（不是测量伪影）？

════ 三个口径 ════
A（历史口径 A）视频流直接比，`-i vid -i ref`，**不指定格式** → ffmpeg 自动协商：
        参考 PNG 被 auto_scale 降到视频的像素格式才参与比较
        （4:2:0 视频 → 参考被降成 yuv420p/csp:smpte170m/range:tv；4:4:4 → yuv444p/bt709/pc）
B（历史口径 B）视频抽帧落盘 PNG，再 PNG vs PNG → 两边都是 RGB，比较域 = gbrp
C（判别口径）视频流直接比，但两端强制 `format=gbrp` → 比较域也 = gbrp
        —— C 是人为造的，用来验证 B ≡ C

════ 第一段：口径 A/B/C 的关系（源 = pika-i2va-shop.mp4）════
    同一份 RGB 内容，编成 4 种落盘格式，各测 A/B/C。
    预测：若「0.03 来自编码」，则 B/C 应随格式变化、A 应不变；
          若「0.03 来自比较域」，则 A 随格式变化、B/C 不变。

════ 第二段：真值基准（判别 4:2:0 是否真丢色度）════
    真值 = 无损 4:4:4/ffv1 基准解码出的 RGB 帧；
    从真值分别编出 4:2:0 / 4:2:2 / 4:4:4（**同用 ffv1 无损编码器**，
    这样差值只可能来自色度抽样，不可能来自有损压缩），再在 RGB 域比真值。
    预测：4:4:4 ≈ 1.0（只剩 RGB↔YUV 矩阵舍入），4:2:0 明显低 → 4:2:0 真丢色度。

════ 第三段：历史那对数字复现 ════
    用 anchor-fidelity.sh 的历史对（pika-i2va-shop.mp4 vs ref-cat-832.png），
    复算口径 A 与口径 B，定出那 0.03 的方向与量级，并核对报告 §1405 与 §2264 谁写反了。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
WS = "/Users/minichen/AI-Models/vpipe-workspace"
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"
VPIPE = "/Applications/Vpipe Manager.app/Contents/Helpers/vpipe"
TMP = os.path.join(LAB, "frames-p11")
OUT = os.path.join(WS, "out")
REPORT_JSON = os.path.join(LAB, "p11-caliper.json")
REF_CAT = os.path.join(LAB, "frames-fid", "ref-cat-832.png")
BASE_444 = os.path.join(OUT, "p11-V444.mkv")   # 无损基准（第一段产出）

# 第一段：同一 RGB 内容 → 4 种落盘格式
STAGE1 = [
    ("V420-def", "yuv420p", "limited",  "bt601", "h264_videotoolbox", "4:2:0 + limited + bt601（历史默认）"),
    ("V422",     "yuv422p", "full",     "bt709", "ffv1",             "4:2:2 + full + bt709"),
    ("V444",     "yuv444p", "full",     "bt709", "ffv1",             "4:4:4 + full + bt709（官方 lossless 配方）"),
    ("V444-lim", "yuv444p", "limited",  "bt709", "ffv1",             "4:4:4 + limited + bt709（隔离 range 贡献）"),
]

# 第二段：从真值编码，**全部用 ffv1 无损编码器**，差值只可能来自色度抽样
STAGE2 = [
    ("T444",  "yuv444p", "full",    "bt709", "ffv1", "4:4:4（无色度抽样）"),
    ("T422",  "yuv422p", "full",    "bt709", "ffv1", "4:2:2（半抽样）"),
    ("T420",  "yuv420p", "full",    "bt709", "ffv1", "4:2:0（1/4 抽样）"),
    ("T420h", "yuv420p", "limited", "bt601", "h264_videotoolbox", "4:2:0 + limited + bt601 + h264（历史默认全链）"),
]

STAT_RE = re.compile(r"n:(\d+) (?:Y|R):([\d.]+) (?:U|G):([\d.]+) (?:V|B):([\d.]+) All:([\d.]+)")


def log(m):
    print(m, flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def make_pipeline(key, pf, cr, cs, codec, out_name, src):
    path = os.path.join("/tmp", f"p11-{key}.json")
    pipeline = {
        "id": f"p11-{key}",
        "stages": [
            {"id": "load", "type": "load-video", "iports": [],
             "config": {"input_url": src, "enable_audio": False}},
            {"id": "dec", "type": "video-to-rgb", "iports": [{"src": "load", "oport": 0}],
             "config": {"output_dtype": "u8"}},
            {"id": "enc", "type": "rgb-to-video", "iports": [{"src": "dec", "oport": 0}],
             "config": {"fps": 24, "pix_fmt": pf, "color_range": cr, "colorspace": cs}},
            {"id": "save", "type": "save-video", "iports": [{"src": "enc", "oport": 0}],
             "config": {"output_url": f"out/{out_name}", "enable_video": True,
                        "enable_audio": False, "video_codec": codec}},
        ],
    }
    with open(path, "w") as f:
        json.dump(pipeline, f, indent=2)
    return path


def transcode(key, pf, cr, cs, codec, src_rel):
    ext = "mp4" if codec.startswith("h264") else "mkv"
    out_name = f"p11-{key}.{ext}"
    out_path = os.path.join(OUT, out_name)
    if os.path.exists(out_path):
        os.remove(out_path)
    p = make_pipeline(key, pf, cr, cs, codec, out_name, src_rel)
    env = dict(os.environ, VPIPE_DISABLE_TELEMETRY="1")
    r = run([VPIPE, "--launch", p], cwd=WS, env=env)
    if not os.path.exists(out_path):
        raise RuntimeError(f"转码失败 {key}: {r.stdout[-1500:]} {r.stderr[-1500:]}")
    return out_path


def probe(path):
    r = run([FF, "-hide_banner", "-i", path])
    for line in r.stderr.splitlines():
        if "Video:" in line and "Stream #" in line:
            return line.strip()
    return "(none)"


def parse_stats(sf):
    vals = []
    with open(sf) as f:
        for line in f:
            m = STAT_RE.match(line)
            if m:
                vals.append((float(m.group(5)), float(m.group(2))))
    return vals


def _run_ssim(sf, lavfi):
    if os.path.exists(sf):
        os.remove(sf)
    run([FF, "-hide_banner", "-lavfi", f"{lavfi}=stats_file={sf}", "-f", "null", "-"])
    if not os.path.exists(sf):
        return None
    vals = parse_stats(sf)
    if not vals:
        return None
    allv = [v[0] for v in vals]
    return {"n": len(allv), "avg": sum(allv) / len(allv), "first": allv[0],
            "mid": allv[len(allv) // 2], "last": allv[-1]}


def measure_pair(in0, in1, mode):
    """mode: A=默认协商 / C=强制 gbrp；in0/in1 为输入路径（可含 %04d 序列）"""
    sf = os.path.join(TMP, "s.ssim")
    if mode == "C":
        lavfi = "[0:v]format=gbrp[a];[1:v]format=gbrp[b];[a][b]ssim"
    else:
        lavfi = "[0:v][1:v]ssim"
    if os.path.exists(sf):
        os.remove(sf)
    run([FF, "-hide_banner", "-i", in0, "-i", in1, "-lavfi", f"{lavfi}=stats_file={sf}",
         "-f", "null", "-"])
    if not os.path.exists(sf):
        return None
    vals = parse_stats(sf)
    if not vals:
        return None
    allv = [v[0] for v in vals]
    psnr = "n/a"
    pv = run([FF, "-hide_banner", "-i", in0, "-i", in1, "-lavfi", lavfi.replace("ssim", "psnr"),
              "-f", "null", "-"])
    pm = re.search(r"average:([\d.]+|inf)", pv.stderr)
    if pm:
        psnr = pm.group(1)
    return {"n": len(allv), "avg": sum(allv) / len(allv), "first": allv[0],
            "mid": allv[len(allv) // 2], "last": allv[-1], "psnr": psnr}


def to_png_seq(vid, d):
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    run([FF, "-y", "-v", "error", "-i", vid, "-pix_fmt", "rgb24", os.path.join(d, "%04d.png")])
    return len([x for x in os.listdir(d) if x.endswith(".png")])


def main():
    os.makedirs(TMP, exist_ok=True)
    t0 = time.time()
    res = {"_stages": {}}

    log("=" * 80)
    log("P11 · YUV 口径消融")
    log("=" * 80)

    # ═══════════ 第一段：口径 A/B/C 的关系 ═══════════
    log("")
    log("【第一段】同一 RGB 内容 → 4 种落盘格式，各测 A/B/C")
    log("  源: out/pika-i2va-shop.mp4   参考: frames-fid/ref-cat-832.png")
    log("")
    s1 = {}
    for key, pf, cr, cs, codec, desc in STAGE1:
        log(f"  [转码] {key:9s} {pf}/{cr}/{cs} + {codec}")
        path = transcode(key, pf, cr, cs, codec, "out/pika-i2va-shop.mp4")
        d = os.path.join(TMP, f"png-{key}")
        n = to_png_seq(path, d)
        a = measure_pair(path, REF_CAT, "A")
        c = measure_pair(path, REF_CAT, "C")
        b = measure_pair(os.path.join(d, "%04d.png"), REF_CAT, "C")
        s1[key] = {"desc": desc, "pix_fmt": pf, "color_range": cr, "colorspace": cs,
                   "codec": codec, "path": path, "size": os.path.getsize(path),
                   "probe": probe(path), "frames": n, "A": a, "B": b, "C": c}
        log(f"           A={a['avg']:.4f} (PSNR {a['psnr']:>9s}) | "
            f"B={b['avg']:.4f} (PSNR {b['psnr']:>9s}) | "
            f"C={c['avg']:.4f} (PSNR {c['psnr']:>9s}) | "
            f"Δ(A−C)={a['avg']-c['avg']:+.4f} Δ(B−C)={b['avg']-c['avg']:+.4f}")
        shutil.rmtree(d, ignore_errors=True)
    res["_stages"]["stage1"] = s1

    log("")
    log("  ▶ 第一段判读")
    a_rng = max(v["A"]["avg"] for v in s1.values()) - min(v["A"]["avg"] for v in s1.values())
    bc_rng = max(v["B"]["avg"] for v in s1.values()) - min(v["B"]["avg"] for v in s1.values())
    b_c_diff = max(abs(v["B"]["avg"] - v["C"]["avg"]) for v in s1.values())
    log(f"    口径 A 随落盘格式的极差 = {a_rng:.4f}")
    log(f"    口径 B/C 随落盘格式的极差 = {bc_rng:.4f}")
    log(f"    |B − C| 最大值 = {b_c_diff:.6f}  → {'B ≡ C 成立' if b_c_diff < 1e-6 else 'B ≠ C'}")
    res["_stages"]["stage1_verdict"] = {
        "A_range": round(a_rng, 6), "BC_range": round(bc_rng, 6),
        "B_equals_C": bool(b_c_diff < 1e-6),
    }

    # ═══════════ 第二段：真值基准 ═══════════
    log("")
    log("【第二段】真值基准：4:2:0 是否真丢色度")
    truth_dir = os.path.join(TMP, "truth")
    if os.path.exists(truth_dir):
        shutil.rmtree(truth_dir, ignore_errors=True)
    os.makedirs(truth_dir, exist_ok=True)
    log(f"  [真值] 从无损基准 {os.path.basename(BASE_444)} 解出 RGB 帧")
    n_truth = to_png_seq(BASE_444, truth_dir)
    log(f"         真值帧 {n_truth} 张")
    truth_seq = os.path.join(truth_dir, "%04d.png")

    log("")
    s2 = {}
    for key, pf, cr, cs, codec, desc in STAGE2:
        log(f"  [转码] {key:6s} {pf}/{cr}/{cs} + {codec}   （源 = 无损基准）")
        path = transcode(key, pf, cr, cs, codec, "out/p11-V444.mkv")
        d = os.path.join(TMP, f"png-{key}")
        n = to_png_seq(path, d)
        b = measure_pair(os.path.join(d, "%04d.png"), truth_seq, "C")
        a = measure_pair(path, os.path.join(truth_dir, "0001.png"), "A")
        s2[key] = {"desc": desc, "pix_fmt": pf, "color_range": cr, "colorspace": cs,
                   "codec": codec, "path": path, "size": os.path.getsize(path),
                   "probe": probe(path), "frames": n, "A": a, "B": b}
        log(f"         口径B(RGB域, vs 真值逐帧) = {b['avg']:.6f}  "
            f"首={b['first']:.6f} 末={b['last']:.6f}  PSNR={b['psnr']}")
        shutil.rmtree(d, ignore_errors=True)
    # 真值自比（测量系统自检，应恒为 1.0 / inf）
    sc = measure_pair(truth_seq, truth_seq, "C")
    s2["_selfcheck"] = {"desc": "真值序列自比（测量系统自检）", "B": sc}
    log(f"  [自检] 真值自比 = {sc['avg']:.6f}  PSNR={sc['psnr']}  "
        f"→ {'系统正常' if sc['avg'] > 0.9999 else '系统异常!'}")
    res["_stages"]["stage2"] = s2

    # ═══════════ 第三段：历史那对数字复现 ═══════════
    log("")
    log("【第三段】复现历史那对：pika-i2va-shop.mp4 vs ref-cat-832.png")
    hist_vid = os.path.join(OUT, "pika-i2va-shop.mp4")
    hd = os.path.join(TMP, "png-hist")
    to_png_seq(hist_vid, hd)
    hist_a = measure_pair(hist_vid, REF_CAT, "A")
    hist_b = measure_pair(os.path.join(hd, "%04d.png"), REF_CAT, "C")
    hist_c = measure_pair(hist_vid, REF_CAT, "C")
    res["_stages"]["stage3_historical"] = {
        "pair": "pika-i2va-shop.mp4 vs ref-cat-832.png",
        "A": hist_a, "B": hist_b, "C": hist_c,
        "A_minus_B": round(hist_a["avg"] - hist_b["avg"], 6),
        "A_minus_C": round(hist_a["avg"] - hist_c["avg"], 6),
    }
    log(f"  口径 A（流直比）   All均值={hist_a['avg']:.4f}  首={hist_a['first']:.4f}  PSNR={hist_a['psnr']}")
    log(f"  口径 B（落盘PNG）  All均值={hist_b['avg']:.4f}  首={hist_b['first']:.4f}  PSNR={hist_b['psnr']}")
    log(f"  口径 C（强制gbrp） All均值={hist_c['avg']:.4f}  首={hist_c['first']:.4f}  PSNR={hist_c['psnr']}")
    log(f"  ▶ A − B = {hist_a['avg']-hist_b['avg']:+.4f}   A − C = {hist_a['avg']-hist_c['avg']:+.4f}")
    shutil.rmtree(hd, ignore_errors=True)

    # ═══════════ 第四段：印相 ═══════════
    log("")
    log("【印相】各变体第 0/40/80/末帧 + 变体并排对照")
    sheet_dir = os.path.join(LAB, "p11-sheets")
    os.makedirs(sheet_dir, exist_ok=True)
    picks = [0, 40, 80, 123]
    allv = {}
    for grp in (s1, s2):
        for key, v in grp.items():
            if key.startswith("_") or "path" not in v:
                continue
            allv[key] = v
    for key, v in allv.items():
        parts = os.path.join(TMP, f"sheet-{key}")
        os.makedirs(parts, exist_ok=True)
        got = []
        for p in picks:
            fp = os.path.join(parts, f"f_{p:04d}.png")
            run([FF, "-y", "-v", "error", "-i", v["path"], "-vf", f"select=eq(n\\,{p}),scale=480:-1",
                 "-fps_mode", "passthrough", "-frames:v", "1", fp])
            if os.path.exists(fp):
                got.append(fp)
        sheet = os.path.join(sheet_dir, f"p11-{key}-contact-sheet.png")
        run([FF, "-y", "-v", "error", "-pattern_type", "glob", "-i", os.path.join(parts, "f_*.png"),
             "-filter_complex", f"tile={len(got)}x1:padding=6:color=0x1a1a1a",
             "-frames:v", "1", sheet])
        v["contact_sheet"] = sheet
    log(f"  → {sheet_dir}/  共 {len(allv)} 张印相")

    # 变体并排（同一时刻）
    cmp_dir = os.path.join(TMP, "cmp")
    os.makedirs(cmp_dir, exist_ok=True)
    for key, v in allv.items():
        run([FF, "-y", "-v", "error", "-i", v["path"], "-vf", "select=eq(n\\,0),scale=416:-1",
             "-fps_mode", "passthrough", "-frames:v", "1", os.path.join(cmp_dir, f"{key}.png")])
    cf = sorted(os.listdir(cmp_dir))
    run([FF, "-y", "-v", "error", "-pattern_type", "glob", "-i", os.path.join(cmp_dir, "*.png"),
         "-filter_complex", f"tile={len(cf)}x1:padding=6:color=0x1a1a1a",
         "-frames:v", "1", os.path.join(sheet_dir, "p11-variants-frame0.png")])
    log(f"  → p11-variants-frame0.png（{len(cf)} 变体: {', '.join(x[:-4] for x in cf)}）")

    res["_meta"] = {"elapsed_sec": round(time.time() - t0, 1),
                    "ffmpeg": FF, "vpipe": VPIPE}
    with open(REPORT_JSON, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    log("")
    log(f"结果写入 {REPORT_JSON}（耗时 {res['_meta']['elapsed_sec']}s）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
