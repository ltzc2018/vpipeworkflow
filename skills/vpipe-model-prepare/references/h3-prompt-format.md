# 官方 MiniMax H3 提示词结构（`<Picture N>` 六段式）—— 2026-11-18 第 5 轮新建

> 最后更新：**2026-11-18 06:31**（第 5 轮夜间知识同步）
> 来源：**MiniMax 官方** `h3-prompt-writing` 技能（随 `tgo-app-dev/valtz` 的 `3rd-party/minimax-h3/` 分发）
> + 上游 vpipe 官方文档 `docs/MINIMAX-H3.md`（本地 build `33cda00` 自带）
> 用途：本实验室的 H3 流水线提示词**目前用的是 vpipe 自己的 `@ImageN` 简写**，
> 与 MiniMax 官方的 `<Picture N>` + 六段结构**不是同一套**。本文件记录两者关系与影响。

---

## 1. ★ 两套标签体系并存（不是新旧替代关系）

| 体系 | 谁在用 | 长相 | 例 |
|---|---|---|---|
| **vpipe 原生** | vpipe 自己的示例流水线 | `@Image1` / `@Image2` / `@Video1` | `docs/pipelines/pika-h3-flex-reference-to-video.vpipeline` |
| **MiniMax 官方** | H3 官方文档与官方提示词技能 | `<Picture N>` / `<Video N>` / `<Audio N>` | `docs/MINIMAX-H3.md` 第 1145 行等 20 处 |

**实测数据**（本地源码树 `vpipe-lab/repo/vpipe`，2026-11-18）：

| 模式 | 命中文件数 |
|---|---:|
| `@Image1` | **1**（仅 `docs/pipelines/pika-h3-flex-reference-to-video.vpipeline`） |
| `<Picture 1>` | **20** |
| `<Audio 1>` | 31 |
| `<Video 1>` | 41 |

- ⇒ **vpipe 的文档主体已经用官方 `<Picture N>` 体系**，
  只有那一个 Pika 示例流水线还写 `@ImageN`。
- ⇒ **本实验室的 P13/P13b/P18 静态夹具用的 `@Image1`**，严格说是**沿用了那一个旧示例**，
  不是官方推荐写法。**登记为待验证项 P27-b**（见 §5）。

---

## 2. 官方 Ref2VA 六段结构

官方 `h3-prompt-writing` 技能规定：full-reference（Ref2VA）改写输出**恰好六段，顺序固定**：

| 顺序 | 段名 | 作用 |
|---|---|---|
| 1 | `subject_definitions` | 定义被引用的内容与它的标签 |
| 2 | `summary` | 任务类型、目标视频、主要引用关系 |
| 3 | `retention_analysis` | 每个被引用项出现在哪、是完全保留/部分保留/迁移/复用 |
| 4 | `detailed_description` | 视觉、动作、镜头、声音、台词（按播放顺序） |
| 5 | `overall_soundscape` | 环境声与物理音 |
| 6 | `non_diegetic_music` | 只有观众能听到的背景音乐 |

Base 模式（T2VA / I2VA / FL2VA / L2VA）则用**三段**：
`integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music`。

官方输出规则（要点）：
- 改写段落**一律用英文**；只保留对话、歌词、画面里可见文字的**原语言**；
- 每个镜头写清：构图 / 主体 / 环境 / 动作 / 镜头运动 / 声音 / **被引用内容在哪个确切时间点出现**；
- **不要写剧情摘要**，不要留悬空标签，时间轴要与要求时长一致；
- 时长必须对上（4–15 秒）。

来源：<https://raw.githubusercontent.com/tgo-app-dev/valtz/main/3rd-party/minimax-h3/skills/h3-prompt-writing/SKILL.md>
与同目录 `references/base-en.txt` / `references/ref-en.txt`（MPL-2.0 随 valtz 分发）。

---

## 3. 四种标签的语义（官方定义）

| 标签 | 含义 | 什么时候单独开一条 |
|---|---|---|
| `<Subject N>` | 从参考素材里抽象出来、**可复用可改造**的可见内容（人、动物、物体、场景、服装、道具、风格、动作、表情） | 总是 |
| `<Picture N>` | 参考图本身，作为某个镜头的**首帧/关键帧/尾帧/构图锚点** | 仅当它确实充当锚点 |
| `<Video N>` | 参考视频，作为**剪辑源、续接起点、或整段时序结构来源** | 仅当它提供整段关系 |
| `<Audio N>` | 被复制或引用的音频信号 | 总是 |

- 一张图如果只用来定义人物/场景/服装/风格 → **不要**单开 `<Picture N>` 条目，
  应在对应的 `<Subject N>` 定义里引用它。
- 一个 `<Subject N>` 可以来自多个素材；一个素材也可以提供多个 subject。
- 官方例子：
  ```
  <Subject 1> is the young woman in <Picture 1>, with long dark hair, a blue cardigan, and a thin silver necklace.
  <Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.
  <Picture 2> is the first frame of [Shot 1], showing a woman seated beside a café window.
  <Video 1> is the source video for the target video edit.
  ```

---

## 4. ★★★ 标签写错 **完全静默**（本轮新增的坑）

上游 `docs/MINIMAX-H3.md` 原文（本地 build `33cda00` 第 1140 行附近）：

> The number in a tag counts within its KIND, not across the list.
> Each of `<Picture i>`, `<Video k>` and `<Audio j>` has a counter of its own,
> so the third reference overall can perfectly well be `<Audio 1>` — it is the first
> *soundtrack*, whatever sits ahead of it.
> …
> **Getting this backwards writes a prompt that points at a reference which is not there,
> and nothing reports it: an unmatched tag is ordinary text to the model.**

要点拆解：

1. **计数器按类型分开**（`<Picture i>` / `<Video k>` / `<Audio j>` 各从 1 起算）。
   → 三张图 + 一段视频 + 一条音频的顺序里，第 3 个参考**完全可能是 `<Audio 1>`**。
2. ★ **未匹配的标签 = 普通文本**：模型不会报错，stage 不会 warn，
   只会把这段标签当成普通英文读进去 → **参考条件静默失效**。
3. 官方推荐顺序是「所有参考块按列表顺序先出，提示词正文在后」：
   ```
   <Picture 1>: … <Picture 2>: … <Audio 1>: … <your prompt text>
   ```
   正文里在哪儿提标签都自由（标签是回指前面已经读过的块）。

### 与本实验室既有坑的同族关系

| 坑 | 表现 | 是否静默 |
|---|---|---|
| shift 写错 | 采样器照跑，场景变了 | **是** |
| `autotune` 竞速 | 同 seed 两次不一样 | **是** |
| 旧 build 丢新字段 | 零报错零日志，输出逐位相同 | **是** |
| ★ **参考标签写错** | 零报错零告警，参考条件失效 | **是** |

⇒ **凡是「引用了但模型没吃进去」的现象，先怀疑标签，再怀疑模型。**

---

## 5. 待验证（已登记进计划表）

- **P27-b · 提示词结构对纹理沸腾绝对水平的影响**
  - 假设：静态夹具若改用官方 `<Picture 1>` 标签 + 六段结构，
    HF jitter 的**绝对值**可能低于当前的 `@Image1` 简写版。
  - **注意**：这**不影响** P18 / P13b 的**内部对照结论**（两臂用同一份提示词，
    差异只可能来自被测变量）。
  - 只影响：① 绝对值能否与上游 #55 的 0.0502 直接比；② 本实验室夹具的「代表性」。
  - 成本：2 臂 × 22 帧 ≈ 8 分钟（模型全在本地）。

---

## 6. 来源清单

| # | 来源 | 日期 | 一句话 |
|---|---|---|---|
| 1 | `valtz` 仓库 `3rd-party/minimax-h3/skills/h3-prompt-writing/SKILL.md` | 2026-11-16 推送 | 官方提示词技能的入口与五种模式 |
| 2 | 同目录 `references/ref-en.txt` | 2026-11-16 | Ref2VA 六段结构与四种标签的完整定义 |
| 3 | 同目录 `references/base-en.txt` | 2026-11-16 | T2VA/I2VA/FL2VA/L2VA 的三段结构 |
| 4 | vpipe `docs/MINIMAX-H3.md`（本地 `33cda00`，第 1140–1160 行） | 2026-11-16 | 「计数器按类型分开」+「未匹配标签是普通文本」原文 |
| 5 | vpipe `docs/pipelines/pika-h3-flex-reference-to-video.vpipeline` | — | 唯一还用 `@ImageN` 的官方示例 |
