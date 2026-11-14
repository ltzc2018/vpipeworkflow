#!/usr/bin/env python3
"""把预览流按 init 段切成若干独立可解码的 mp4。

preview stage 在「采纳真实原生分辨率」时会重新初始化 fMP4，推第二个 init 段。
两个段的分辨率不同（如 640x360 → 512x288），塞进同一个 mp4 会让 ffmpeg 用
第一段的 SPS 去解第二段 → 满屏 decode error。必须按段切开。

用法： split_preview.py <stream.mp4> <ws-capture.log> <out_dir>
"""
import os
import re
import sys

FRAG_RE = re.compile(r"^\[\s*([\d.]+)s\] FRAG (\d+)B")


def main():
    stream, log_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)

    # 从抓取日志还原每个分段的 fragment 字节数
    segs = [[]]          # 每段一个 fragment 长度列表
    init_sizes = []
    for line in open(log_path):
        m = FRAG_RE.match(line.strip())
        if m:
            segs[-1].append(int(m.group(2)))
            continue
        if "INIT #" in line:
            n = int(re.search(r"INIT #(\d+)", line).group(1))
            init_sizes.append(int(re.search(r"(\d+)B", line).group(1)))
            if n > 1:
                segs.append([])   # 新 init 开启新分段

    data = open(stream, "rb").read()
    pos = 0
    out = []
    for i, frags in enumerate(segs):
        init_len = init_sizes[i] if i < len(init_sizes) else 0
        chunk = data[pos:pos + init_len]
        pos += init_len
        for fl in frags:
            chunk += data[pos:pos + fl]
            pos += fl
        path = os.path.join(out_dir, f"segment-{i + 1}.mp4")
        with open(path, "wb") as f:
            f.write(chunk)
        out.append({"segment": i + 1, "path": path, "bytes": len(chunk),
                    "init_bytes": init_len, "frag_count": len(frags)})
        print(f"segment-{i + 1}: init={init_len}B frags={len(frags)} "
              f"total={len(chunk)}B -> {path}")
    print(f"消耗 {pos} / {len(data)} 字节")
    for o in out:
        print(o)


if __name__ == "__main__":
    main()
