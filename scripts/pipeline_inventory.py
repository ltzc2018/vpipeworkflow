#!/usr/bin/env python3
"""批量提取 pipelines/*.vpipeline 的关键特征，用于生成说明文档。

输出 TSV：文件名 | id | 阶段类型序列 | 模型目录 | 分辨率 | 步数 | 帧数 | shift | LoRA | 输出
"""
import json
import os
import re
import sys

PIPE_DIR = os.path.expanduser("~/AI-Models/vpipe-workspace/pipelines")

KEY_CFG = {
    "width", "height", "steps", "frames", "video_shift", "audio_shift",
    "lora", "lora_scale", "hf_dir", "seed", "flow_map", "lora_scale",
    "clip_frames", "upscale_factor", "preview_max_edge", "preview_frames",
    "preview_every", "reference_image_short_edge", "reference_video_short_edge",
    "audio_seconds", "condition_timestep", "sampler", "method", "negative_prompt",
}


def walk_stages(obj, out):
    """递归收集 stages（主 + subpipelines）。"""
    if isinstance(obj, dict):
        for k in ("stages", "subpipelines"):
            v = obj.get(k)
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        if "type" in item:
                            out.append(item)
                        walk_stages(item, out)
    elif isinstance(obj, list):
        for item in obj:
            walk_stages(item, out)


def summarize(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    stages = []
    walk_stages(data, stages)

    types = [s.get("type", "?") for s in stages]
    # 去重保序
    seen, uniq = set(), []
    for t in types:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    model_dir = ""
    lora = ""
    lora_scale = ""
    width = height = ""
    steps = frames = ""
    vshift = ashift = ""
    seed = ""
    out_name = ""
    is_image = False
    is_video = False
    preview = False
    upscale = False

    for s in stages:
        t = s.get("type", "")
        cfg = s.get("config", {}) or {}
        if t in ("model-select", "model-registry"):
            model_dir = cfg.get("hf_dir", model_dir)
        if "lora" in cfg and cfg.get("lora"):
            lora = cfg["lora"]
        if "lora_scale" in cfg:
            lora_scale = str(cfg.get("lora_scale"))
        for k in ("width", "height"):
            if k in cfg:
                v = cfg[k]
                if isinstance(v, str) and re.match(r"^\d+$", v):
                    v = int(v)
                if k == "width":
                    width = v
                else:
                    height = v
        if "steps" in cfg:
            steps = cfg["steps"]
        if "frames" in cfg:
            frames = cfg["frames"]
        if "video_shift" in cfg:
            vshift = cfg["video_shift"]
        if "audio_shift" in cfg:
            ashift = cfg["audio_shift"]
        if "seed" in cfg:
            seed = cfg["seed"]
        if "upscale_factor" in cfg:
            upscale = True
        if t == "preview":
            preview = True
        if t == "generate-image":
            is_image = True
        if t == "generate-video":
            is_video = True
        if t in ("save-video", "save-image", "save-audio"):
            for k in ("output_path", "output", "path", "filename", "output_url"):
                if k in cfg and isinstance(cfg[k], str) and cfg[k]:
                    out_name = cfg[k]
                    break
            if not out_name:
                out_name = f"<{t}>"
            # 只取最后一个 save
    return {
        "file": os.path.basename(path),
        "id": data.get("id", ""),
        "types": uniq,
        "model": model_dir,
        "lora": lora,
        "lora_scale": lora_scale,
        "res": f"{width}x{height}" if (width or height) else "",
        "steps": steps,
        "frames": frames,
        "shift": f"{vshift}/{ashift}" if (vshift or ashift) else "",
        "seed": seed,
        "kind": ("IMG+VID" if (is_image and is_video) else "IMG" if is_image else "VID" if is_video else "UTIL"),
        "preview": preview,
        "upscale": upscale,
        "out": out_name,
        "n_stages": len(stages),
    }


def main():
    files = sorted(f for f in os.listdir(PIPE_DIR) if f.endswith(".vpipeline"))
    if len(sys.argv) > 1:
        files = [f for f in files if sys.argv[1] in f]
    rows = [summarize(os.path.join(PIPE_DIR, f)) for f in files]
    print("file\tid\tkind\tres\tsteps\tframes\tshift\tlora\tmodel\tpreview\tupscale\tseed\tout\tnstages")
    for r in rows:
        print("\t".join([
            r["file"], r["id"], r["kind"], str(r["res"]), str(r["steps"]),
            str(r["frames"]), str(r["shift"]), r["lora"] or "-",
            r["model"] or "-", "Y" if r["preview"] else "-",
            "Y" if r["upscale"] else "-", str(r["seed"]), r["out"] or "-",
            str(r["n_stages"]),
        ]))


if __name__ == "__main__":
    main()
