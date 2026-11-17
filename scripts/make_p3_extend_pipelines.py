#!/usr/bin/env python3
"""P3.4 四段式续接流水线生成器

做法：**直接加载官方 `minimax-h3-extend-part1/part2/concat.vpipeline` 再打补丁**，
不重画接线 —— 端口拓扑、temporal-stack 参数、attach_audio 槽位全部沿用官方，
只替换本机特有的东西（本地 8-bit 权重、Pika 适配器、分辨率/步数、输出路径、提示词）。

官方原本的规格是 960x576 / 243 帧 / 20 步 / 基础 bf16 模型。
本机 24 GB 跑不动那个组合，缩到 **832x480 / 124 帧 / 6 步 / Pika 适配器**，
每段 5.17 秒，4 段 = 20.67 秒连续视频。

续接机制（官方结构，逐字沿用）：
  load-video(上一段) → video-to-rgb → temporal-slice(start=-90) → temporal-stack → 参考 1（视频）
  load-audio(上一段, start_s=1.4167, duration_s=3.75) → audio-to-pcm → temporal-stack → 参考 2（音频）
  video-ref-encoder(attach_audio=[2])  ← 音频参考是**第 2 条参考**，槽位 1 起算
"""
import json
import os

TPL = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab/repo/vpipe/docs/pipelines"
OUT = "/Users/minichen/AI-Models/vpipe-workspace/pipelines"

W, H, FRAMES, STEPS, SEED = 832, 480, 124, 6, 42
SEG_SEC = FRAMES / 24.0            # 5.1667
GUIDE_FRAMES = 90                  # 官方取上一段末 90 帧
GUIDE_AUDIO_SEC = 3.75             # 官方取上一段末 3.75 秒音频
GUIDE_AUDIO_START = round(SEG_SEC - GUIDE_AUDIO_SEC, 4)   # 1.4167

SCENE = ("A tabby cat in a light blue denim jacket sits on a worn wooden windowsill in warm "
         "late-afternoon sunlight, slowly licking its paw and blinking, individual fur strands "
         "and the denim weave clearly resolved, shallow depth of field, camera very slowly "
         "pushes in. Audio: soft rhythmic purring, a faint breeze through the open window, "
         "distant birdsong outside. Normal real-time speed, no slow motion. "
         "No text, no captions, no logos.")

SUBJECTS = """subject_definitions:
<Subject 1> is the tabby cat in <Video 1>, with brown-and-black striped fur, a light blue denim jacket, white chest fur and pink paw pads.
<Subject 2> is the worn wooden windowsill in <Video 1>, with flaking varnish, a chipped front edge, and warm sunlight lying across it.
<Subject 3> is the view through the open window in <Video 1>, with a pale blue house wall, a strip of green hedge, and long late-afternoon shadows.
<Video 1> is the source video whose final moment the target video continues from.
<Audio 1> is the synchronized audio track of <Video 1>, providing the purring, the breeze and the distant birdsong to continue."""

RETENTION = """retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - the same individual tabby cat keeps its brown-and-black striped fur, light blue denim jacket, white chest fur and pink paw pads.
<Subject 2> (appears in [Shot 1]): fully_preserved - the same worn windowsill with flaking varnish and the same chipped front edge.
<Subject 3> (appears in [Shot 1]): fully_preserved - the same pale blue house wall, green hedge strip and late-afternoon light direction.
<Video 1> (continuation starting point): fully_preserved - [Shot 1] starts from the final framing, pose and lighting of <Video 1>.
<Audio 1>: reference - the purring timbre, the breeze and the birdsong continue in the same character and tempo without copying the original signal."""

SOUND_2 = """overall_soundscape:
The soft rhythmic purring referenced from <Audio 1> continues from the start without a break, joined by the same faint breeze through the open window and the same distant birdsong. One soft fabric rustle as the cat's shoulder shifts, and a single quiet inhale.

non_diegetic_music:
No musical score. Only the natural ambience referenced from <Audio 1> continues."""

SOUND_3 = """overall_soundscape:
The purring referenced from <Audio 1> continues, slightly slower as the cat relaxes. The breeze through the window keeps the same soft, continuous character, and the distant birdsong continues. A small creak of old wood as the cat settles its weight on the sill.

non_diegetic_music:
No musical score. Only the natural ambience referenced from <Audio 1> continues."""

SOUND_4 = """overall_soundscape:
The purring referenced from <Audio 1> continues at an even, sleepy tempo. The breeze through the window keeps its soft continuous character, and the distant birdsong continues, a little further away as the cat drifts toward sleep. One small tap of a claw on bare wood, then quiet.

non_diegetic_music:
No musical score. Only the natural ambience referenced from <Audio 1> continues."""

CONT = [
    # part2
    ("""summary:
[video continuation + audio reference] The target video continues directly from the end of <Video 1>. In <Subject 2>, <Subject 1> finishes licking its paw, lifts its head, and turns slowly to look out through the window of <Subject 3>; the purring and the outdoor ambience follow <Audio 1> without copying the signal.

detailed_description:
The target video is live-action and cinematic, with warm late-afternoon sunlight, a shallow depth of field, and soft fill light from the open window.
[Shot 1] The shot continues seamlessly from the final moment of <Video 1>, keeping the same medium close-up and the same slow push-in. <Subject 1> completes the lick, draws its paw back onto <Subject 2>, and raises its head. Its ears rotate forward and its gaze travels toward the window. Long warm highlights slide across the brass zipper teeth of the denim jacket and along the individual whiskers. The chipped front edge of <Subject 2> stays in the same place in the frame, and the hedge strip of <Subject 3> stays still in the background light. The camera keeps pushing in slowly and the cat's face grows larger in frame.""",
     SOUND_2),
    # part3
    ("""summary:
[video continuation + audio reference] The target video continues directly from the end of <Video 1>. <Subject 1> looks back from the window, gives a slow wide yawn that shows its tongue and small teeth, then blinks twice and settles lower onto <Subject 2>; the purring and the outdoor ambience follow <Audio 1> without copying the signal.

detailed_description:
The target video is live-action and cinematic, with warm late-afternoon sunlight, a shallow depth of field, and soft fill light from the open window.
[Shot 1] The shot continues seamlessly from the final moment of <Video 1>, keeping the same medium close-up and the same slow push-in. <Subject 1> turns its head back from the window toward the camera, opens its mouth in a long yawn that shows a pink tongue and small pale teeth, then closes it and blinks twice with half-closed lids. It lowers its body and settles its weight on <Subject 2>, the denim jacket folding at the shoulder seams. The chipped front edge of the sill and the hedge strip of <Subject 3> keep the same position in frame, so the change is only in the cat's posture and the slightly closer framing.""",
     SOUND_3),
    # part4
    ("""summary:
[video continuation + audio reference] The target video continues directly from the end of <Video 1>. <Subject 1> is nearly asleep on <Subject 2>; a stronger puff of breeze from the window makes its ear flick and its tail flick once, and it does not fully wake; the purring and the outdoor ambience follow <Audio 1> without copying the signal.

detailed_description:
The target video is live-action and cinematic, with warm late-afternoon sunlight, a shallow depth of field, and soft fill light from the open window.
[Shot 1] The shot continues seamlessly from the final moment of <Video 1>, keeping the same close framing. <Subject 1> lies relaxed on <Subject 2> with its chin close to the varnish, eyes nearly closed. A stronger gust comes through the open window of <Subject 3>, the hedge strip in the background shivers slightly, and the cat's near ear flicks back once while the tip of its tail flicks across the wood. It does not open its eyes. The sunlight on the sill has shifted slightly warmer and lower. The camera holds the close framing to the end of the video.""",
     SOUND_4),
]


def load(name):
    with open(os.path.join(TPL, name)) as f:
        return json.load(f)


def stage(doc, sid):
    for s in doc["stages"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def set_cfg(doc, sid, **kv):
    s = stage(doc, sid)
    s.setdefault("config", {}).update(kv)


def build_part1():
    d = load("minimax-h3-extend-part1.vpipeline")
    d["id"] = "p3-ext-part1"
    set_cfg(d, "model-select", hf_dir="local/MiniMax-H3-FL2VA-8bit")
    set_cfg(d, "minimax-h3-model-config", video_shift=12.0, audio_shift=3.0,
            condition_timestep=1.0, audio_seconds=0.0,
            lora="Pika-Labs/Pika-H3-Flex-fl2va", lora_scale=1.0)
    set_cfg(d, "text-prompt", text=SCENE)
    set_cfg(d, "generate-video", height=H, width=W, frames=FRAMES, fps=24,
            steps=STEPS, seed=SEED)
    set_cfg(d, "save-video", output_url="out/p3-ext-part1.mp4")
    return d


def build_part(n):
    """n = 2..4，参考第 n-1 段"""
    d = load("minimax-h3-extend-part2.vpipeline")
    d["id"] = f"p3-ext-part{n}"
    prev = f"out/p3-ext-part{n-1}.mp4"
    set_cfg(d, "load-guide", input_url=prev, enable_audio=False)
    set_cfg(d, "guide-tail", start=-GUIDE_FRAMES)
    set_cfg(d, "load-guide-audio", input_url=prev,
            start_s=GUIDE_AUDIO_START, duration_s=GUIDE_AUDIO_SEC)
    set_cfg(d, "guide-pcm", output_sample_rate=32000, channels=2,
            chunk_duration_s=GUIDE_AUDIO_SEC, max_chunk_duration_s=60)
    set_cfg(d, "model-select", hf_dir="local/MiniMax-H3-Ref2VA-8bit")
    set_cfg(d, "minimax-h3-model-config", video_shift=12.0, audio_shift=3.0,
            condition_timestep=1.0, audio_seconds=0.0,
            lora="Pika-Labs/Pika-H3-Flex-ref2va", lora_scale=1.0)
    body, sound = CONT[n - 2]
    set_cfg(d, "text-prompt", text=f"{SUBJECTS}\n\n{body}\n\n{RETENTION}\n\n{sound}")
    set_cfg(d, "video-ref-encoder", frames=FRAMES, reference_video_short_edge=0,
            attach_audio=[2], max_prompt_tokens=65536)
    set_cfg(d, "generate-video", height=H, width=W, frames=FRAMES, fps=24,
            steps=STEPS, seed=SEED)
    set_cfg(d, "save-video", output_url=f"out/p3-ext-part{n}.mp4")
    return d


def build_concat(nparts=4, out_name="p3-ext-full.mp4"):
    d = load("minimax-h3-extend-concat.vpipeline")
    d["id"] = f"p3-ext-concat{nparts if nparts != 4 else ''}"
    set_cfg(d, "load-parts", input_url=[f"out/p3-ext-part{n}.mp4" for n in range(1, nparts + 1)],
            enable_video=True, enable_audio=True)
    set_cfg(d, "audio-to-pcm", output_sample_rate=32000, channels=2,
            chunk_duration_s=round(SEG_SEC, 4), max_chunk_duration_s=30)
    set_cfg(d, "save-video", output_url=f"out/{out_name}")
    return d


def main():
    docs = {"p3-ext-part1.vpipeline": build_part1()}
    for n in (2, 3, 4):
        docs[f"p3-ext-part{n}.vpipeline"] = build_part(n)
    docs["p3-ext-concat.vpipeline"] = build_concat(4, "p3-ext-full.mp4")
    # 两段版：先落袋一个可验证的续接结果，再继续跑 3/4 段
    docs["p3-ext-concat2.vpipeline"] = build_concat(2, "p3-ext-full2.mp4")
    for name, doc in docs.items():
        p = os.path.join(OUT, name)
        with open(p, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        print(f"写出 {p}  ({len(doc['stages'])} 个 stage)")


if __name__ == "__main__":
    main()
