#!/usr/bin/env python3
"""解析 MP4/fMP4 的 box 结构，并抽取 moov 里的轨道尺寸与 avcC 参数集摘要。

用法: python3 p4_mp4box.py <file.mp4> [max_boxes]
"""
import json
import struct
import sys

CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"mvex", b"edts", b"dinf"}


def iter_boxes(data, start=0, end=None, depth=0, out=None):
    if end is None:
        end = len(data)
    pos = start
    while pos + 8 <= end:
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr or pos + size > end:
            break
        yield depth, typ, pos, size
        if typ in CONTAINERS:
            yield from iter_boxes(data, pos + hdr, pos + size, depth + 1, out)
        pos += size


def find_avcc(data, trak_start, trak_end):
    """在 trak 内找 avcC，返回 (profile, level, width, height) 摘要。"""
    info = {}
    for d, typ, p, s in iter_boxes(data, trak_start, trak_end):
        if d == 1 and typ == b"tkhd":
            v = data[p + 8:p + s]
            if len(v) >= 84:
                w = struct.unpack(">I", v[-8:-4])[0] >> 16
                h = struct.unpack(">I", v[-4:])[0] >> 16
                info["tkhd_size"] = (w, h)
        if d == 1 and typ == b"avcC":
            info["avcC_len"] = s
            info["avcC_head"] = data[p + 8:p + 8 + 16].hex()
    return info


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    print(f"== {path}  ({len(data)} bytes) ==")
    top = []
    for d, typ, p, s in iter_boxes(data):
        if d == 0:
            top.append((typ.decode("latin1"), p, s))
            print(f"  [{p:>10}] {typ.decode('latin1'):6s} size={s}")
    moovs = [t for t in top if t[0] == "moov"]
    print(f"\nmoov 数量: {len(moovs)}")
    for i, (_, p, s) in enumerate(moovs):
        info = {}
        for d, typ, tp, ts in iter_boxes(data, p, p + s):
            if d == 1 and typ == b"trak":
                info.update(find_avcc(data, tp, tp + ts))
        print(f"  moov#{i+1} @{p} size={s} -> {info}")
    # 顶层 moof 计数与位置，用来切分两段
    moofs = [t for t in top if t[0] == "moof"]
    print(f"moof 数量: {len(moofs)}")
    if len(moovs) == 2:
        print(f"第 2 个 moov 起点 = {moovs[1][1]}，其前有 {sum(1 for m in moofs if m[1] < moovs[1][1])} 个 moof")
    return 0


if __name__ == "__main__":
    sys.exit(main())
