#!/usr/bin/env python3
"""修复 P4 预览流：把「两个 init 段」拼成的畸形 MP4 拆回合法的分片。

根因
----
vpipe 的 preview stage 通过 WebSocket 推的是 **fMP4**：一段 init(=ftyp+moov)
加若干 fragment(=moof+mdat)。当预览解码器的输出分辨率/编码参数变化时，服务端会
**再推一段 init**。本机抓流脚本曾把「init1 + frag* + init2 + frag*」直接顺序拼成
一个 .mp4 —— 于是文件里出现了 **两个 moov**，中间还嵌了一个 ftyp。

MP4 规范里 moov 只能有一个。解码器走到第二个 moov 时会重置参数集（SPS/PPS），
后续 fragment 就用错误的配置去解，于是整段出现
「top block unavailable for requested intra mode」与大面积花屏。

修法
----
1. 按 box 结构把原文切成若干段：segN = ftyp+moov_N + frag*
2. 每段各自用 ffmpeg 重封装成合法 MP4（part-N.mp4）
3. 可选把各段统一到第一段的画布后拼成一个**可播**的单文件

两种输入：
  --raw  <file>        旧的畸形单文件，内部按 moov 切段
  --parts <f1> <f2>…  抓流时已经按段落盘的合法 fMP4

用法:
  python3 p4_fix_preview.py --raw <preview-stream.mp4> --outdir <dir> [--tag i2va-fast] [--concat]
  python3 p4_fix_preview.py --parts seg1.fmp4 seg2.fmp4 --outdir <dir> --tag x --concat
"""
import argparse
import json
import os
import struct
import subprocess
import sys

FF = "/Users/minichen/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"


def top_boxes(data):
    """返回顶层 box 列表 [(type, pos, size)]。"""
    out = []
    pos = 0
    n = len(data)
    while pos + 8 <= n:
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = n - pos
        if size < hdr or pos + size > n:
            break
        out.append((typ, pos, size))
        pos += size
    return out


def track_size(data, moov_pos, moov_size):
    """从 moov 里读 tkhd 的宽高。"""
    pos = moov_pos + 8
    end = moov_pos + moov_size
    while pos + 8 <= end:
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr:
            break
        if typ == b"trak":
            p2, e2 = pos + hdr, pos + size
            while p2 + 8 <= e2:
                s2 = struct.unpack(">I", data[p2:p2 + 4])[0]
                t2 = data[p2 + 4:p2 + 8]
                if s2 < 8:
                    break
                if t2 == b"tkhd":
                    v = data[p2 + 8:p2 + s2]
                    w = struct.unpack(">I", v[-8:-4])[0] >> 16
                    h = struct.unpack(">I", v[-4:])[0] >> 16
                    return w, h
                p2 += s2
        pos += size
    return None


def split_segments(data):
    """按 moov 的出现把畸形文件切成若干段，每段 = ftyp+moov+fragment。"""
    boxes = top_boxes(data)
    moovs = [b for b in boxes if b[0] == b"moov"]
    if not moovs:
        return [{"start": 0, "end": len(data), "size": None, "moof": 0}]
    starts = []
    for m in moovs:
        s = m[1]
        for j in range(boxes.index(m) - 1, -1, -1):
            if boxes[j][0] == b"ftyp":
                s = boxes[j][1]
                break
        starts.append(s)
    segs = []
    for idx, m in enumerate(moovs):
        e = starts[idx + 1] if idx + 1 < len(starts) else len(data)
        segs.append({
            "start": starts[idx], "end": e,
            "size": track_size(data, m[1], m[2]),
            "moof": sum(1 for t, p, _ in boxes if t == b"moof" and starts[idx] <= p < e),
        })
    return segs


def remux(src, dst, scale_to=None, crf="18"):
    cmd = [FF, "-y", "-v", "error", "-i", src]
    if scale_to:
        w, h = scale_to
        cmd += ["-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stderr or "")[-600:]


def decode_errors(path):
    r = subprocess.run([FF, "-v", "error", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    errs = [l for l in (r.stderr or "").splitlines() if l.strip()]
    return len(errs), errs[:6]


def probe(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    txt = (r.stderr or "")
    dur = ""
    for line in txt.splitlines():
        if "Duration:" in line:
            dur = line.split("Duration:")[1].split(",")[0].strip()
    size = ""
    for line in txt.splitlines():
        if "Stream #0:0" in line:
            if "x" in line.split("Video:")[-1]:
                size = line.split("Video:")[-1].split(",")[-2].strip()
    return dur, size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--parts", nargs="+")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tag", default="preview")
    ap.add_argument("--concat", action="store_true")
    ap.add_argument("--concat-name", default=None)
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    report = {"outdir": args.outdir, "segments": []}

    # ---- 1. 切段 ----
    parts = []
    if args.raw:
        data = open(args.raw, "rb").read()
        segs = split_segments(data)
        print(f"== {args.raw}  ({len(data)} bytes) ==")
        for i, s in enumerate(segs):
            print(f"  段{i+1}: @{s['start']}..{s['end']}  画布={s['size']}  moof={s['moof']}")
            part = os.path.join(args.outdir, f"{args.tag}-part{i+1}.fmp4")
            with open(part, "wb") as f:
                f.write(data[s["start"]:s["end"]])
            parts.append((part, s))
        report["raw"] = args.raw
        report["raw_bytes"] = len(data)
    elif args.parts:
        for i, p in enumerate(args.parts):
            data = open(p, "rb").read()
            boxes = top_boxes(data)
            moovs = [b for b in boxes if b[0] == b"moov"]
            size = track_size(data, moovs[0][1], moovs[0][2]) if moovs else None
            n_moof = sum(1 for t, _, _ in boxes if t == b"moof")
            print(f"  段{i+1}: {os.path.basename(p)}  画布={size}  moof={n_moof}")
            parts.append((p, {"size": size, "moof": n_moof}))
    else:
        ap.error("需要 --raw 或 --parts")

    # ---- 2. 每段重封装成合法 MP4 ----
    fixed = []
    for i, (part, s) in enumerate(parts):
        dst = os.path.join(args.outdir, f"{args.tag}-part{i+1}.mp4")
        rc, err = remux(part, dst)
        if rc != 0:
            print(f"  !! 段{i+1} 重封装失败: {err}")
            continue
        n_err, sample = decode_errors(dst)
        dur, res = probe(dst)
        print(f"  段{i+1} -> {os.path.basename(dst)}  {res} {dur}  解码错误 {n_err} 处"
              f"{'  ' + str(sample) if n_err else ''}")
        report["segments"].append({
            "index": i + 1, "part": part, "fixed": dst,
            "canvas": list(s["size"]) if s["size"] else None,
            "moof": s["moof"], "decode_errors": n_err,
            "bytes": os.path.getsize(dst), "duration": dur, "resolution": res,
        })
        fixed.append(dst)
        if not args.keep_raw and args.raw and part != dst:
            os.remove(part)

    # ---- 3. 拼成可播单文件 ----
    if args.concat and len(fixed) >= 1:
        canvas = report["segments"][0]["canvas"]
        cname = args.concat_name or f"{args.tag}-preview-stream.mp4"
        out = os.path.join(args.outdir, cname)
        inputs = []
        for f in fixed:
            inputs += ["-i", f]
        fc = []
        for i in range(len(fixed)):
            fc.append(f"[{i}:v]scale={canvas[0]}:{canvas[1]}:flags=lanczos,"
                      f"setsar=1,fps=24[v{i}]")
        fc.append("".join(f"[v{i}]" for i in range(len(fixed))) +
                  f"concat=n={len(fixed)}:v=1:a=0[vout]")
        cmd = [FF, "-y", "-v", "error"] + inputs + [
            "-filter_complex", ";".join(fc), "-map", "[vout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            n_err, _ = decode_errors(out)
            dur, res = probe(out)
            print(f"  拼接 -> {os.path.basename(out)}  {res} {dur}  解码错误 {n_err} 处")
            report["concat"] = {"path": out, "decode_errors": n_err,
                                "bytes": os.path.getsize(out), "duration": dur,
                                "resolution": res}
        else:
            print(f"  !! 拼接失败: {(r.stderr or '')[-500:]}")
            report["concat"] = {"error": (r.stderr or "")[-500:]}

    rp = os.path.join(args.outdir, f"{args.tag}-fix-report.json")
    with open(rp, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"报告: {rp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
