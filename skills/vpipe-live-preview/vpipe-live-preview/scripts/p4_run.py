#!/usr/bin/env python3
"""P4 编排器：起 vpipe web-ui → 载入流水线 → 启动 → 抓实时预览流 → 等成片落盘 → 停。

用法：
  python3 p4_run.py --pipeline pika-i2va-preview-fast --tag i2va-fast [--timeout 900]

P4 版改动（相对初版）：
  * 控制台日志用 ?since=N 增量拉取，边跑边存，不再只拿到最后 10 行
  * 预览抓取线程用 stop_event 优雅停止，保证 fMP4 的 init 段一定拼上
  * 记录首帧预览延迟（launch → 第一个 fragment / 第一个 PNG still）
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ws_capture import capture  # noqa: E402

WS = os.environ.get("VPIPE_WS",
                     os.path.join(os.path.expanduser("~"), "AI-Models",
                                  "vpipe-workspace"))
LAB = os.environ.get("VPIPE_LAB",
                     os.path.join(os.path.expanduser("~"), "WorkBuddy",
                                  "vpipe-lab"))
VUI = os.environ.get(
    "VPIPE_WEBUI",
    "/Applications/Vpipe Manager.app/Contents/Helpers/vpipe-web-ui")
PORT = int(os.environ.get("VPIPE_WEBUI_PORT", "9876"))


def wait_http(url, timeout=90):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def file_stable(path, quiet=8.0, timeout=1800, min_size=1024):
    """等文件出现且大小在 quiet 秒内不再变化。"""
    t0 = time.time()
    last = -1
    last_change = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size != last:
                last = size
                last_change = time.time()
            elif size >= min_size and time.time() - last_change >= quiet:
                return size
        time.sleep(1.0)
    return None


class LogPoller(threading.Thread):
    """边跑边增量拉控制台日志。"""

    def __init__(self, base, tag):
        super().__init__(daemon=True)
        self.base = base
        self.tag = tag
        self.stop_event = threading.Event()
        self.lines = []          # (wall_ts, seq, level, text)
        self._since = 0

    def run(self):
        while not self.stop_event.is_set():
            try:
                r = requests.get(f"{self.base}/api/log/console",
                                 params={"since": self._since, "limit": 2048},
                                 timeout=10)
                data = r.json()
                for l in data.get("lines", []):
                    self.lines.append((time.time(), l["seq"], l.get("level", ""),
                                       l.get("text", "")))
                new_latest = int(data.get("latest", self._since))
                self._since = max(self._since, new_latest)
            except Exception:
                pass
            self.stop_event.wait(1.0)

    def dump(self, path):
        with open(path, "w") as f:
            t0 = self.lines[0][0] if self.lines else time.time()
            for wall, seq, level, text in self.lines:
                f.write(f"[{wall - t0:8.2f}s] #{seq:<5} {level:<8} {text}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", required=True, help="流水线 id（= 文件名去掉 .vpipeline）")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=float, default=1200)
    ap.add_argument("--quiet", type=float, default=8.0)
    ap.add_argument("--out-name", default=None, help="成片文件名（默认 <tag>.mp4）")
    ap.add_argument("--port", type=int, default=PORT,
                    help="web-ui 端口（默认 9876，或 $VPIPE_WEBUI_PORT）")
    a = ap.parse_args()
    port = a.port

    pipeline_path = os.path.join(WS, "pipelines", a.pipeline + ".vpipeline")
    # 成片文件名直接从流水线里读 save-video 的 output_url，
    # 避免 runner 猜的名字和流水线写出的名字对不上（第一版就栽在这）。
    out_name = a.out_name
    if out_name is None:
        with open(pipeline_path) as f:
            doc = json.load(f)
        for st in doc.get("stages", []):
            if st.get("type") == "save-video":
                out_name = os.path.basename(st["config"]["output_url"])
                break
    out_name = out_name or f"p4-{a.tag}.mp4"
    final_mp4 = os.path.join(WS, "out", out_name)
    if os.path.exists(final_mp4):
        os.remove(final_mp4)

    out_dir = os.path.join(LAB, "deliverables", "p4-preview", a.tag)
    os.makedirs(out_dir, exist_ok=True)
    server_log = os.path.join(LAB, "logs", f"p4-webui-{a.tag}.log")
    os.makedirs(os.path.dirname(server_log), exist_ok=True)
    env = dict(os.environ)
    env["VPIPE_DISABLE_TELEMETRY"] = "1"
    env["VPIPE_MODEL_SOURCE"] = "modelscope"

    srv_log_fh = open(server_log, "w")
    proc = subprocess.Popen(
        [VUI, "--bind", "127.0.0.1", "--port", str(port),
         "--expose-native-file-system"],
        cwd=WS, env=env, stdout=srv_log_fh, stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    base = f"http://127.0.0.1:{port}"
    stop_event = threading.Event()
    try:
        if not wait_http(base + "/api/health", 90):
            print("!! web-ui 没起来，日志：", server_log)
            return 2
        print(f"[{a.tag}] web-ui 已就绪 pid={proc.pid}", flush=True)

        poller = LogPoller(base, a.tag)
        poller.start()

        # 日志级别调到 debug：preview stage 会打 "clip #N (39 frames)"，
        # 这是预览到达次数（= 渲染了预览的去噪步数）的精确计数，
        # 默认的 normal 级别看不到。
        try:
            rl = requests.put(base + "/api/log/level",
                              json={"level": "debug"}, timeout=10)
            print(f"[{a.tag}] 日志级别 -> {rl.status_code} {rl.text[:120]}",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            print("!! 设置日志级别失败", e)

        # 载入流水线
        r = requests.post(base + "/api/pipelines/load",
                          json={"path": pipeline_path}, timeout=30)
        if r.status_code != 200:
            print(f"!! 载入失败 {r.status_code}: {r.text[:500]}")
            return 3
        info = r.json()
        pid = info["id"]
        print(f"[{a.tag}] 已载入流水线 id={pid}", flush=True)

        # 先连 WS 并 watch，再启动（后端每 500ms 轮询一次，watch 早于 launch 没问题）
        cap = {}

        def _cap():
            try:
                cap["r"] = capture("127.0.0.1", port, pid, "preview", out_dir,
                                   a.timeout, os.path.join(out_dir, "ws-capture.log"),
                                   stop_event)
            except Exception as e:  # noqa: BLE001
                cap["e"] = repr(e)

        t = threading.Thread(target=_cap, daemon=True)
        t.start()
        time.sleep(1.5)

        r = requests.post(f"{base}/api/pipelines/{pid}/launch", timeout=30)
        print(f"[{a.tag}] launch -> {r.status_code} {r.text[:200]}", flush=True)
        t_launch = time.time()

        size = file_stable(final_mp4, quiet=a.quiet, timeout=a.timeout)
        print(f"[{a.tag}] 成片落盘: {final_mp4} size={size} "
              f"耗时={time.time() - t_launch:.1f}s", flush=True)

        # preview 是 WebSocket sink，流水线不会自己结束 → 主动停
        try:
            requests.post(f"{base}/api/pipelines/{pid}/stop", timeout=30)
        except Exception as e:  # noqa: BLE001
            print("!! stop 失败", e)
        time.sleep(2)
        stop_event.set()
        t.join(timeout=60)

        poller.stop_event.set()
        poller.join(timeout=10)
        poller.dump(os.path.join(LAB, "logs", f"p4-pipeline-{a.tag}.log"))

        result = {
            "tag": a.tag,
            "pipeline": pid,
            "final_mp4": final_mp4,
            "final_size": size,
            "wall_seconds": round(time.time() - t_launch, 1),
            "capture": {k: v for k, v in (cap.get("r") or {}).items() if k != "events"},
            "capture_error": cap.get("e"),
            "log_lines": len(poller.lines),
            "out_dir": out_dir,
        }
        with open(os.path.join(LAB, "logs", f"p4-result-{a.tag}.json"), "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        stop_event.set()
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
        time.sleep(1)
        srv_log_fh.close()


if __name__ == "__main__":
    sys.exit(main())
