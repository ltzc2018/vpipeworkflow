#!/usr/bin/env python3
"""极简 RFC6455 WebSocket 客户端 + vpipe 实时预览抓取器。

vpipe 的 web-ui 把 preview stage 的媒体通过 /api/ui/view/preview/ws 推给浏览器：
  文本帧  -> JSON 控制消息（stages / waiting / playing / config / gone）
  二进制帧 -> 4 字节小端头长度 + JSON 头（{"m":"init"|"fragment"|"image"|"audio"}）+ 负载

本脚本把二进制帧落盘：init 段写 init.mp4，fragment 追加到 frag.mp4（fMP4），
image（PNG）单独存成 png-*.png。

P4 版改动：
  * 支持 stop_event 优雅停止，停止时仍然拼装 init+fragment，绝不留下半截文件
  * 每条消息带时间戳，便于算「首帧预览延迟」与「每步预览间隔」
  * fragment 先写 frag.body，停止时统一拼装成 preview-stream.mp4
"""
import base64
import json
import os
import socket
import struct
import sys
import threading
import time


class WSClient:
    def __init__(self, host, port, path, timeout=15.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("web-ui 在握手过程中关闭了连接")
            buf += chunk
        head, _, rest = buf.partition(b"\r\n\r\n")
        status = head.split(b"\r\n")[0].decode(errors="replace")
        if "101" not in status:
            raise RuntimeError(f"WebSocket 握手失败: {status}")
        self._rx = bytearray(rest)

    def _read(self, n):
        while len(self._rx) < n:
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise ConnectionError("连接已关闭")
            self._rx += chunk
        out = bytes(self._rx[:n])
        del self._rx[:n]
        return out

    def recv(self, timeout=1.0):
        """返回 (opcode, payload)；超时返回 (None, None)。"""
        self.sock.settimeout(timeout)
        try:
            head = self._read(2)
        except socket.timeout:
            return None, None
        opcode = head[0] & 0x0F
        masked = head[1] & 0x80
        length = head[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._read(8))[0]
        mask = self._read(4) if masked else None
        payload = self._read(length) if length else b""
        if mask:
            payload = bytes(b ^ mask[i & 3] for i, b in enumerate(payload))
        return opcode, payload

    def send_text(self, text):
        data = text.encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i & 3] for i, b in enumerate(data))
        header = bytearray([0x81])
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n <= 0xFFFF:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        header += mask
        self.sock.sendall(bytes(header) + masked)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def capture(host, port, pipeline, stage, out_dir, seconds, log_path=None,
            stop_event=None):
    os.makedirs(out_dir, exist_ok=True)
    init_path = os.path.join(out_dir, "init.mp4")
    frag_path = os.path.join(out_dir, "preview-stream.mp4")
    body_path = os.path.join(out_dir, "frag.body")
    log_lines = []
    counts = {"init": 0, "fragment": 0, "image": 0, "audio": 0, "text": 0}
    bytes_out = {"init": 0, "fragment": 0, "image": 0}
    png_index = 0
    events = []  # (t, kind, nbytes)

    ws = WSClient(host, port, "/api/ui/view/preview/ws")
    ws.send_text(json.dumps({"m": "watch", "pipeline": pipeline, "stage": stage}))

    t0 = time.time()
    # 分段：一个 init 段 + 其后的若干 fragment 为一段。
    # preview stage 在「采纳真实原生分辨率」时会重新初始化 fMP4（推第二个 init），
    # 所以流结构是 init1+frags1+init2+frags2……必须按到达顺序拼，不能覆盖。
    segments = []      # [{"init": bytes|None, "frags": [bytes,...]}]
    cur = {"init": None, "frags": []}
    segments.append(cur)
    log_lines = []
    counts = {"init": 0, "fragment": 0, "image": 0, "audio": 0, "text": 0}
    bytes_out = {"init": 0, "fragment": 0, "image": 0}
    png_index = 0
    events = []  # (t, kind, nbytes)

    try:
        while time.time() - t0 < seconds:
            if stop_event is not None and stop_event.is_set():
                log_lines.append(f"[{time.time() - t0:7.2f}s] STOP requested")
                break
            opcode, payload = ws.recv(timeout=0.5)
            if opcode is None:
                continue
            if opcode == 0x1:
                counts["text"] += 1
                line = payload.decode(errors="replace")
                log_lines.append(f"[{time.time() - t0:7.2f}s] TEXT {line}")
                if '"m":"config"' in line.replace(" ", ""):
                    events.append((round(time.time() - t0, 2), "config", 0))
                continue
            if opcode != 0x2:
                continue
            if len(payload) < 4:
                continue
            hlen = struct.unpack("<I", payload[:4])[0]
            hdr = json.loads(payload[4:4 + hlen].decode(errors="replace"))
            kind = hdr.get("m", "")
            data = payload[4 + hlen:]
            counts[kind] = counts.get(kind, 0) + 1
            now = round(time.time() - t0, 2)
            if kind == "init":
                bytes_out["init"] += len(data)
                cur = {"init": data, "frags": []}
                segments.append(cur)
                events.append((now, "init", len(data)))
                # 每个 init 段单独留档：preview stage 会在采纳真实原生分辨率时
                # 重新初始化 fMP4，这是「一段流两个 init」的现场证据
                with open(os.path.join(out_dir,
                                       f"init-{counts['init']}.mp4"), "wb") as f:
                    f.write(data)
                log_lines.append(f"[{now:7.2f}s] INIT #{counts['init']} {len(data)}B "
                                 f"(开启新分段)")
            elif kind == "fragment":
                bytes_out["fragment"] += len(data)
                cur["frags"].append(data)
                events.append((now, "fragment", len(data)))
                log_lines.append(f"[{now:7.2f}s] FRAG {len(data)}B "
                                 f"(total #{counts['fragment']})")
            elif kind == "image":
                bytes_out["image"] += len(data)
                png_index += 1
                events.append((now, "image", len(data)))
                with open(os.path.join(out_dir, f"png-{png_index:03d}.png"), "wb") as f:
                    f.write(data)
                log_lines.append(f"[{now:7.2f}s] IMAGE png-{png_index:03d}.png "
                                 f"{len(data)}B")
            elif kind == "audio":
                log_lines.append(f"[{now:7.2f}s] AUDIO {len(data)}B")
    except Exception as e:  # noqa: BLE001
        log_lines.append(f"[{time.time() - t0:7.2f}s] ERROR {e!r}")
    finally:
        ws.close()

    # 按到达顺序拼装：每段 = 自己的 init + 自己的 fragments
    assembled = 0
    seg_info = []
    with open(frag_path, "wb") as out:
        for i, seg in enumerate(segments):
            n_init = len(seg["init"]) if seg["init"] else 0
            n_frag = sum(len(f) for f in seg["frags"])
            if n_init == 0 and n_frag == 0:
                continue
            if seg["init"]:
                out.write(seg["init"])
                assembled += n_init
            for f in seg["frags"]:
                out.write(f)
            assembled += sum(len(f) for f in seg["frags"])
            seg_info.append({"seg": i, "init_bytes": n_init,
                             "frag_bytes": sum(len(f) for f in seg["frags"]),
                             "frag_count": len(seg["frags"])})

    first_frag = next((e[0] for e in events if e[1] == "fragment"), None)
    first_img = next((e[0] for e in events if e[1] == "image"), None)
    summary = {
        "seconds": round(time.time() - t0, 2),
        "counts": counts,
        "bytes": bytes_out,
        "png_files": png_index,
        "stream": frag_path,
        "stream_bytes": assembled,
        "segments": seg_info,
        "first_fragment_at": first_frag,
        "first_image_at": first_img,
        "events": events,
    }
    if log_path:
        with open(log_path, "w") as f:
            f.write("\n".join(log_lines) + "\n")
            f.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "events"},
                     ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", required=True)
    ap.add_argument("--stage", default="preview")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=300)
    ap.add_argument("--port", type=int, default=9876)
    ap.add_argument("--log")
    a = ap.parse_args()
    capture("127.0.0.1", a.port, a.pipeline, a.stage, a.out, a.seconds, a.log)
