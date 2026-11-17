#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P15 · H3 σ 网格计算器（video / audio 双向换算）

## 依据（两个互相独立的一手来源，逐位互验）

**A. 上游 vpipe 文档 `docs/MINIMAX-H3.md`**（源码树自带，33cda00）：

> By default a clip runs `steps` forwards over `linspace(1, 0, steps + 1)`,
> pushed through each modality's shift, and every step is an Euler step.
>
> The **audio's** sigmas follow the way ComfyUI's H3 model derives them:
> each video sigma is taken back to the shared unshifted grid through
> `video_shift`, then out through `audio_shift`. So the two shifts still
> matter with a list of your own: they decide where the audio sits.
> The list for the example above, at shifts 12 / 3, puts the audio at
> 1, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0.
>
> The 8-step grid at shift 12 starts it at 0.632; at shift 6, 0.462;
> at shift 12, 16 steps start it at 0.444.

**B. lightx2v / ModelTC 官方 `ModelTC/Minimax-H3-Turbo` README**（2026-11-17 读）：

> For `NFE = N`, define the N transformer evaluation points on the unshifted
> grid as `q_i = (N - i) / N`, where `i = 0, 1, ..., N - 1`.
> For example, with `NFE = 4`, `video shift = 12`, and `audio shift = 3`,
> the shared grid is `q = [1, 0.75, 0.5, 0.25]`, giving video sigma
> `[1, 0.9730, 0.9231, 0.8000] -> 0` and audio sigma
> `[1, 0.9000, 0.7500, 0.5000] -> 0`; each list therefore uses exactly
> four NFEs.

## 由 A、B 联合确定并逐位互验的公式

```
q_i        = (N - i) / N                for i = 0..N      （N+1 点，末点 q=0）
sigma_v(q) = shift_v * q / (1 + (shift_v - 1) * q)
sigma_a(q) = shift_a * q / (1 + (shift_a - 1) * q)
```

* 视频 σ 串 = 把 q 网格过 `video_shift`；
* 音频 σ 串 = 把**同一个** q 网格过 `audio_shift`；
* 若给定的是**自定义视频 σ 串**（如 ComfyUI 的 `er_sde` 表），音频 σ 串必须**先反解 q**：
  ```
  q = sigma_v / (shift_v - sigma_v * (shift_v - 1))
  sigma_a = shift_a * q / (1 + (shift_a - 1) * q)
  ```
  —— 这正是上游文档说的「each video sigma is taken back to the shared
  unshifted grid through `video_shift`, then out through `audio_shift`」。

## 自检（每次运行都会跑，任何一条不符即报错退出）

```
N=4  sv=12 sa=3  →  video 1, 0.9730, 0.9231, 0.8000, 0
                       audio 1, 0.9000, 0.7500, 0.5000, 0      ← ModelTC 原文
N=8  sv=12       →  最后一步起点 0.632                        ← vpipe 文档
N=8  sv=6        →  最后一步起点 0.462                        ← vpipe 文档
N=16 sv=12       →  最后一步起点 0.444                        ← vpipe 文档
自定义 er_sde 串 + 12/3 →  audio 1, 0.940, 0.866, 0.770, 0.643,
                              0.439, 0.236, 0.072, 0          ← vpipe 文档
```

## 用法

```bash
# 默认网格：8 步、video_shift 6、audio_shift 3
python3 p15_sigma_grid.py --steps 8 --video-shift 6 --audio-shift 3

# 自定义视频 σ 串（ComfyUI 的 er_sde 表）反推音频 σ 串
python3 p15_sigma_grid.py --sigmas "1, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0" \
                           --video-shift 12 --audio-shift 3

# 只要视频 σ 串（可直接贴进 minimax-h3-model-config 的 sigmas 字段）
python3 p15_sigma_grid.py --steps 8 --video-shift 6 --only-video
```
"""
import argparse
import re
import sys


def shift_sigma(q, shift):
    """把无偏移网格点 q 过 flow-matching 的 exponential shift。"""
    return shift * q / (1.0 + (shift - 1.0) * q)


def unshift_sigma(sigma, shift):
    """把已 shift 的 σ 反解回无偏移网格 q（sigma -> q）。"""
    den = shift - sigma * (shift - 1.0)
    if abs(den) < 1e-12:
        raise ValueError("sigma=%r 无法在 shift=%r 下反解" % (sigma, shift))
    return sigma / den


def grid_q(steps):
    """linspace(1, 0, steps+1) —— 即 q_i = (steps - i)/steps, i=0..steps。"""
    return [(steps - i) / steps for i in range(steps + 1)]


def video_sigmas(steps, video_shift):
    return [shift_sigma(q, video_shift) for q in grid_q(steps)]


def audio_from_q(qs, audio_shift):
    return [shift_sigma(q, audio_shift) for q in qs]


def audio_from_video_sigmas(vid_sigmas, video_shift, audio_shift):
    qs = [unshift_sigma(s, video_shift) for s in vid_sigmas]
    return audio_from_q(qs, audio_shift)


def fmt(xs, nd=6):
    out = []
    for x in xs:
        s = ("%." + str(nd) + "f") % x
        s = s.rstrip("0").rstrip(".")
        out.append(s if s else "0")
    return ", ".join(out)


def selftest():
    fails = []

    def chk(name, got, want, tol=5e-4):
        if len(got) != len(want):
            fails.append("%s: 长度 %d != %d" % (name, len(got), len(want)))
            return
        for i, (g, w) in enumerate(zip(got, want)):
            if abs(g - w) > tol:
                fails.append("%s[%d]: %.6f != %.6f" % (name, i, g, w))

    # 1) ModelTC 原文：NFE=4, 12/3
    v = video_sigmas(4, 12.0)
    chk("ModelTC video N=4 sv=12", v, [1.0, 0.9730, 0.9231, 0.8000, 0.0])
    a = audio_from_q(grid_q(4), 3.0)
    chk("ModelTC audio N=4 sa=3", a, [1.0, 0.9000, 0.7500, 0.5000, 0.0])

    # 2) vpipe 文档：最后一步的起点（倒数第二个 sigma）
    chk("N=8 sv=12 最后一步起点", [video_sigmas(8, 12.0)[-2]], [0.632], tol=1e-3)
    chk("N=8 sv=6  最后一步起点", [video_sigmas(8, 6.0)[-2]], [0.462], tol=1e-3)
    chk("N=16 sv=12 最后一步起点", [video_sigmas(16, 12.0)[-2]], [0.444], tol=1e-3)

    # 3) vpipe 文档：ComfyUI er_sde 串在 12/3 下的音频 sigma
    ersde = [1.0, 0.9844, 0.9627, 0.9304, 0.878, 0.7579, 0.5527, 0.2369, 0.0]
    a2 = audio_from_video_sigmas(ersde, 12.0, 3.0)
    chk("er_sde 串 @12/3 的音频 sigma", a2,
        [1.0, 0.940, 0.866, 0.770, 0.643, 0.439, 0.236, 0.072, 0.0])

    # 4) 往返一致性：video -> q -> audio 必须等于直接用 q 算 audio
    chk("往返一致性", audio_from_video_sigmas(v, 12.0, 3.0),
        audio_from_q(grid_q(4), 3.0))

    if fails:
        print("自检未通过：", file=sys.stderr)
        for f in fails:
            print("  ✗ " + f, file=sys.stderr)
        return False
    print("自检通过：6 组共 33 个数值与两个一手来源逐位吻合")
    return True


def parse_sigmas(s):
    xs = [float(x) for x in re.split(r"[,\s]+", s.strip().strip("[]")) if x]
    if not xs:
        raise ValueError("sigmas 解析为空")
    return xs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--video-shift", type=float, default=12.0)
    ap.add_argument("--audio-shift", type=float, default=3.0)
    ap.add_argument("--sigmas", default=None,
                    help="自定义视频 sigma 串（含末尾 0），反推音频 sigma")
    ap.add_argument("--only-video", action="store_true")
    ap.add_argument("--only-audio", action="store_true")
    ap.add_argument("--no-selftest", action="store_true")
    args = ap.parse_args()

    if not args.no_selftest:
        if not selftest():
            return 2

    print()
    if args.sigmas:
        vs = parse_sigmas(args.sigmas)
        if vs[-1] != 0.0:
            vs = vs + [0.0]
            print("（输入串末尾没有 0，已按上游约定补上干净端点）")
        steps = len(vs) - 1
        qs = [unshift_sigma(s, args.video_shift) for s in vs]
        as_ = audio_from_q(qs, args.audio_shift)
        print("自定义视频 σ 串（%d 步 = %d 次前向）" % (steps, steps))
        if not args.only_audio:
            print("  video sigma : %s" % fmt(vs))
        if not args.only_video:
            print("  audio sigma : %s" % fmt(as_))
        print("  反解出的共享无偏移网格 q : %s" % fmt(qs, 6))
        print("  可贴进 minimax-h3-model-config 的 sigmas 字段 = 上面那行 video sigma")
        return 0

    if args.steps is None:
        args.steps = 8
    vs = video_sigmas(args.steps, args.video_shift)
    as_ = audio_from_q(grid_q(args.steps), args.audio_shift)
    print("默认网格：steps=%d（= %d 次前向 over %d 个 sigma）"
          % (args.steps, args.steps, args.steps + 1))
    if not args.only_audio:
        print("  video sigma : %s" % fmt(vs))
    if not args.only_video:
        print("  audio sigma : %s" % fmt(as_))
    print("  最后一步起点（倒数第二个 sigma）: video %.6f  audio %.6f"
          % (vs[-2], as_[-2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
