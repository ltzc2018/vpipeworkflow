#!/usr/bin/env python3
"""P4：预览流切步 + 印相 + SSIM/PSNR 量化。

预览 stage 把每个去噪步的「干净估计」解成一个 39 帧 clip，然后循环播放，
新 clip 替换旧 clip。所以一整条预览流 = 若干个 39 帧的 beat 循环。

切步原理：同相位帧（n 与 n-39）在一个 beat 内几乎逐像素相同（SSIM≈0.98），
跨 beat 时同相位帧内容变了（SSIM 骤降）。据此切出每个 beat。

用法： p4_beats.py <tag> <segment2.mp4> <final.mp4> <anchor.jpg> <clip_frames>
"""
import json
import os
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


def total_frames(path):
    # 注意：ffmpeg 的 frame= 统计写在 stderr，不能再 2>&1 重定向到 stdout
    res = run(f'{FF} -hide_banner -i "{path}" -map 0:v:0 -f null -')
    import re
    m = re.findall(r"frame=\s*(\d+)", res.stderr)
    return int(m[-1]) if m else 0


def extract(path, n, out):
    run(f'{FF} -y -i "{path}" -vf "select=eq(n\\,{n})" -vframes 1 "{out}"')
    return os.path.exists(out) and os.path.getsize(out) > 0


def extract_sel(path, expr, indices, prefix, scale="256:144"):
    """一次解码、按单个 select 表达式批量抽帧。

    注意：不能用 `select='eq(n,1)+eq(n,2)+...'` 拼上百个 OR 项——
    124 项就会让 ffmpeg 滤镜图 "Cannot allocate memory"。
    这里一律用单表达式：
      * 循环首帧 → not(mod(n,CLIPF))
      * 连续区间 → between(n,A,B)
    """
    if not indices:
        return {}
    tmp = os.path.join(os.path.dirname(prefix), "_batch")
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    run(f'{FF} -y -i "{path}" -vf "select=\'{expr}\',scale={scale}" '
        f'-fps_mode passthrough "{tmp}/b-%05d.png"')
    files = sorted(os.listdir(tmp))
    out = {}
    for i, fn in zip(indices, files):
        dst = f"{prefix}{i:05d}.png"
        run(f'/bin/mv "{os.path.join(tmp, fn)}" "{dst}"')
        out[i] = dst
    if len(out) != len(indices):
        print(f"   ⚠ 批量抽帧数量不符：期望 {len(indices)} 实得 {len(out)}")
    return out


def ssim(a, b):
    res = run(f'{FF} -i "{a}" -i "{b}" -lavfi "[0:v][1:v]ssim" -f null -')
    import re
    m = re.search(r"All:([0-9.]+)", res.stderr)
    return float(m.group(1)) if m else 0.0


def psnr(a, b):
    res = run(f'{FF} -i "{a}" -i "{b}" -lavfi "[0:v][1:v]psnr" -f null -')
    import re
    m = re.search(r"average:([0-9.]+)", res.stderr)
    return float(m.group(1)) if m else 0.0


def main():
    tag, seg, final, anchor = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    clipf = int(sys.argv[5]) if len(sys.argv) > 5 else 39
    outdir = os.path.join(OUTROOT, tag)
    work = os.path.join(WORKROOT, tag)
    os.makedirs(work, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    n = total_frames(seg)
    print(f"[{tag}] segment-2 共 {n} 帧，循环长度 {clipf} → "
          f"{n // clipf} 个完整循环")

    # --- 切步：比较相邻循环的同相位首帧（一次解码批量抽帧）---
    starts = [k * clipf for k in range(n // clipf)]
    batch = extract_sel(seg, f"not(mod(n\\,{clipf}))", starts,
                        os.path.join(work, "beatprobe-"))
    loops = [(k, s, batch[s]) for k, s in enumerate(starts) if s in batch]

    groups = []          # [[loop_index, ...], ...]
    scores = []
    for i in range(1, len(loops)):
        s = ssim(loops[i - 1][2], loops[i][2])
        scores.append((loops[i][0], round(s, 4)))
    thr = 0.95
    groups.append([loops[0][0]])
    for idx, s in scores:
        if s < thr:
            groups.append([idx])
        else:
            groups[-1].append(idx)
    print(f"[{tag}] 切步结果（SSIM 阈值 {thr}）：{len(groups)} 个 beat")
    score_of = dict(scores)
    for g in groups:
        print(f"   beat {g[0]:>3}..{g[-1]:<3} 循环数={len(g):<2} "
              f"首帧SSIM={score_of.get(g[0])}")

    # --- 每个 beat 取「该 beat 的第 1 帧」（相位一致，可横向比较收敛过程）---
    beat_frames = []
    for g in groups:
        p = batch.get(g[0] * clipf)
        if p:
            beat_frames.append((g[0], p))
    print(f"[{tag}] 取出 {len(beat_frames)} 张 beat 首帧（相位一致）")

    # --- 印相 ---
    if beat_frames:
        inputs, filt, k = "", "", 0
        for _, p in beat_frames:
            if not os.path.exists(p):
                continue
            inputs += f' -i "{p}"'
            filt += (f"[{k}:v]scale=384:216,drawtext=text='beat {k}':"
                     f"x=6:y=6:fontsize=20:fontcolor=white:box=1:"
                     f"boxcolor=black@0.65[vt{k}];")
            k += 1
        stack = "".join(f"[vt{i}]" for i in range(k))
        out = os.path.join(outdir, "contact-sheet-beats.png")
        run(f'{FF} -y{inputs} -filter_complex "{filt}{stack}hstack=inputs={k}[v]" '
            f'-map "[v]" -frames:v 1 "{out}"')
        print(f"[{tag}] 印相 -> {out} ({k} 格)")

    # --- 量化 ---
    anchor_png = os.path.join(work, "anchor-512.png")
    run(f'{FF} -y -i "{anchor}" -vf '
        f'"scale=512:288:force_original_aspect_ratio=increase,crop=512:288" '
        f'"{anchor_png}"')
    rows = []

    def measure(vid, ref, label):
        # 两边统一缩到 256×144 再比，否则 prod（416×240 vs 832×480）
        # 这类分辨率不一致的组合会因为尺寸不匹配直接跳过
        ss = os.path.join(work, "m.ssim")
        ps = os.path.join(work, "m.psnr")
        filt = ("[0:v]scale=256:144[a];[1:v]scale=256:144[b];"
                "[a][b]ssim=stats_file=" + ss)
        run(f'{FF} -i "{vid}" -i "{ref}" -lavfi "{filt}" -f null -')
        filt = ("[0:v]scale=256:144[a];[1:v]scale=256:144[b];"
                "[a][b]psnr=stats_file=" + ps)
        run(f'{FF} -i "{vid}" -i "{ref}" -lavfi "{filt}" -f null -')
        if not os.path.exists(ss) or os.path.getsize(ss) == 0:
            rows.append((label, "尺寸不匹配", "", "", "", "", "", ""))
            return
        import re
        sv = []
        for line in open(ss):
            m = re.search(r"All:([0-9.]+)", line)
            if m:
                sv.append(float(m.group(1)))
        pv = []
        for line in open(ps):
            m = re.search(r"psnr_avg:([0-9.]+)", line)
            if m:
                pv.append(float(m.group(1)))
        if not sv:
            rows.append((label, "无数据", "", "", "", "", "", ""))
            return
        rows.append((label, str(len(sv)),
                     f"{sum(sv)/len(sv):.4f}", f"{sv[0]:.4f}", f"{sv[-1]:.4f}",
                     f"{sum(pv)/len(pv):.2f}" if pv else "",
                     f"{pv[0]:.2f}" if pv else "",
                     f"{pv[-1]:.2f}" if pv else ""))

    measure(final, anchor_png, "成片 vs 锚定图")
    measure(seg, final, "预览流(seg2) vs 成片")
    pf = os.path.join(work, "preview-first.png")
    extract(seg, 0, pf)
    measure(pf, anchor_png, "预览第1帧 vs 锚定图")
    pl = os.path.join(work, "preview-last.png")
    fl = os.path.join(work, "final-last.png")
    extract(seg, n - 1, pl)
    extract(final, total_frames(final) - 1, fl)
    measure(pl, fl, "预览末帧(非对齐) vs 成片末帧")
    if beat_frames:
        measure(beat_frames[-1][1], fl, "预览最后beat末帧 vs 成片末帧(未对齐)")

    # --- 相位对齐测量：预览最后一个 beat 与成片逐帧对应 ---
    # 预览流是循环播放的，同相位帧相隔 clip_frames 帧。
    # 单帧 argmax 不可靠（画面同质，所有候选 SSIM 都在 0.93 上下），
    # 改用「双端点准则」：同时匹配成片首帧与末帧两条曲线，取联合最优偏移。
    print()
    print("--- 相位对齐：预览最后 beat vs 成片 ---")

    def endpoint_curve(target_frame):
        """一次 ffmpeg 调用，得到「成片 target_frame vs 全部预览帧」的 SSIM 曲线。"""
        t = os.path.join(work, f"tgt{target_frame}.png")
        t2 = os.path.join(work, f"tgt{target_frame}_s.png")
        extract(final, target_frame, t)
        run(f'{FF} -y -i "{t}" -vf "scale=256:144" -frames:v 1 "{t2}"')
        f = os.path.join(work, f"align{target_frame}.ssim")
        run(f'{FF} -i "{seg}" -i "{t2}" -lavfi '
            f'"[0:v]scale=256:144[a];[1:v]scale=256:144[b];[a][b]ssim=stats_file={f}" '
            f'-f null -')
        import re
        c = []
        if os.path.exists(f):
            for line in open(f):
                m = re.search(r"All:([0-9.]+)", line)
                if m:
                    c.append(float(m.group(1)))
        return c

    nfin = total_frames(final)
    c0 = endpoint_curve(0)
    cN = endpoint_curve(nfin - 1)
    off, best = None, -1.0
    if c0:
        for o in range(len(c0) - (nfin - 1)):
            if o + nfin - 1 >= len(cN):
                break
            s = c0[o] + cN[o + nfin - 1]
            if s > best:
                best, off = s, o
    if off is not None:
        print(f"   相位偏移：成片 f0 ↔ 预览 f{off}"
              f"（首帧 SSIM {c0[off]:.4f} / 末帧 SSIM {cN[off + nfin - 1]:.4f}）")
        cur = []
        nf = min(nfin, n - off)
        # 一次解码批量抽：预览的 [off, off+nf) 与成片的 [0, nf)
        ab = extract_sel(seg, f"between(n\\,{off}\\,{off + nf - 1})",
                         list(range(off, off + nf)), os.path.join(work, "pa-"))
        bb = extract_sel(final, f"between(n\\,0\\,{nf - 1})",
                         list(range(nf)), os.path.join(work, "pb-"))
        for p in range(nf):
            a2 = ab.get(off + p)
            b2 = bb.get(p)
            if not a2 or not b2:
                continue
            cur.append(ssim(a2, b2))
        if cur:
            print(f"   逐帧 SSIM：均值 {sum(cur)/len(cur):.4f}  "
                  f"首 {cur[0]:.4f}  中 {cur[len(cur)//2]:.4f}  末 {cur[-1]:.4f}")
            rows.append(("**预览最后beat vs 成片（相位对齐）**", str(len(cur)),
                         f"{sum(cur)/len(cur):.4f}", f"{cur[0]:.4f}",
                         f"{cur[-1]:.4f}", "", "", ""))
            with open(os.path.join(work, "phase-aligned-ssim.txt"), "w") as f:
                for i, v in enumerate(cur):
                    f.write(f"{i}\t{v:.4f}\n")

    print()
    print("| 对照 | 帧数 | SSIM 均值 | SSIM 首 | SSIM 末 | PSNR 均值 | PSNR 首 | PSNR 末 |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")

    os.makedirs(LOGROOT, exist_ok=True)
    with open(os.path.join(LOGROOT, f"p4-quant-{tag}.json"), "w") as f:
        json.dump({"tag": tag, "frames": n, "clip_frames": clipf,
                   "beats": groups, "beat_boundary_ssim": scores,
                   "rows": rows}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
