# 提示词写法与消融方法论

## H3 提示词的基本结构

H3 的编码器**逐字读取提示词，中间没有任何改写步骤**。提示词结构要照模型训练时的格式写。

### 基础格式（文生视频）

三个字段：
- `integrated_multimodal_description` —— 画面描述
- `overall_soundscape` —— 环境音
- `non_diegetic_music` —— 配乐

镜头标记为 `[Shot N] At MM:SS.mmm`，说话人有稳定 ID，台词写作 `<d>[English] Just one more turn.</d>`。

### 参考格式（Ref2VA）

六个小节，其中：
- `subject_definitions` 把主体命名为 `<Video 1>` 的 `<Subject 1..3>`，音频为 `<Audio 1>`
- `summary` 以 **`[video continuation + audio reference]`** 开头（表示这段是续接、声音被延续而非复制）
- `retention_analysis` + 逐镜头 `detailed_description`

## Pika H3 Flex 的提示词范式

Pika adapter 有自己的 manifest 契约（`pika-flex-ref2va-v1`），提示词要照它的范式写：

```
References: @Image1 is the subject sheet. Make a new video of the subject from @Image1.
[动作、场景、镜头描述]
Audio: [环境音/音效/配乐]
Normal real-time speed, no slow motion. No text, no captions, no logos.
```

要点：
- **`References: @Image1 is the subject sheet`** —— 声明参考图的**角色**
- 官方范式还要求写 *"Keep the character exactly as designed in @Image1 — same face, proportions, **outfit**, colours"* —— 因为服装丢失是已知问题
- **`Normal real-time speed, no slow motion.`** 抑制慢动作
- **`No text, no captions, no logos.`** 抑制水印和字幕（实测有效）

## 消融实验方法论（本轮最值钱的部分）

### 为什么要做消融

"参考图看起来生效了"是自说自话。要证明参考图真的参与了生成，必须做对照实验。

### 第一层：像素级 SSIM/PSNR

回答"输出与参考图**逐像素**一致吗？"

```bash
ffmpeg -i f000.png -i ref-crop.png -lavfi "[0:v][1:v]ssim;[0:v][1:v]psnr" -f null -
```

实测结果：

| 路线 | 首帧 SSIM | 全片平均 |
|---|---|---|
| 首帧锚定 | 0.9505 | 0.5774 |
| 首尾帧锚定 | 0.9500 | 0.6657 |
| 参考生视频（有参考） | 0.5245 | 0.5120 |
| 参考生视频（**无参考对照**） | 0.5805 | **0.5718** |

**反直觉的关键发现**：参考生视频"有参考"的 SSIM **低于**"无参考对照"。

这说明参考图**不是把输出往参考图拉**，而是**改写主体本身**。所以：
- 参考生视频的 SSIM 低，**不是模型没生效**
- 恰恰相反，它证明参考图在做的是语义替换而非像素重建

### 第二层：第三方模型复核

回答"输出的**语义**真的被参考图改写了吗？"

用**独立于生成链路**的模型（LFM3-VL-2B、Qwen3.5-4B）问输出抽帧。

实测：提示词里**没有"熊猫"二字**，但两个独立模型都把 D 组判成"黑白熊猫"，LFM3-VL 还描述出"坐在窗台上、伸舌头舔爪子"。

结论从"我自己看着像"升级为**被独立复核**。

多模态 chat 的媒体行标记协议：
```
<|__vpipe_fs_im_start__|/abs/path.png<|__vpipe_fs_im_end__|>
```
需要 `text-input` 开 `media: true`。单发测试从 **stdin 管道喂一行**即可，不需要 Web UI。

### 第三层：先验不可达主体消融（最容易忽略的一条）

回答"我的消融设计**有区分度**吗？"

**A/B 消融必须先问"对照组能不能产生不同结果"。**

失败案例：第一版实验用"姜黄猫"做参考图，无参考对照组 B 组**也出姜黄虎斑猫** —— 场景先验太强，两组输出无法区分。这样的消融**不可证伪**，再多的行数指标、SSIM 数字都是自说自话。

**解法**：换一个模型先验**不可能产出**的参考主体。比如水彩插画风格的**黑白熊猫** —— 场景先验只会出猫，出不了熊猫，立刻可区分。

> **换一个模型先验不可能产出的参考主体，比换任何指标都管用。**

### 内部量化证据

参考行数差异也是证据。A 组（有参考）16,999 行 / B 组（无参考）14,943 行 —— 参考行占一个 rotary slot、按各自噪声水平保持。

但要注意：**参考行数只由图片尺寸决定，与内容无关**。所以 A 组和 D 组行数相同（都是 16,999）。行数差异只证明"参考被打包进序列"，不证明"内容被采用"——内容证据必须靠第一、二层。

## 提示词对照表

| 想要的效果 | 提示词写法 |
|---|---|
| 抑制水印 | `No text, no captions, no logos.` |
| 抑制慢动作 | `Normal real-time speed, no slow motion.` |
| 保留服装 | `Keep the character exactly as designed in @Image1 — same face, proportions, outfit, colours.` |
| 指定镜头 | `The camera slowly pushes in.` / `The camera pulls back.` / `A slow orbit around the subject.` |
| 环境音 | `Audio: soft rhythmic purring, a faint breeze through the open window, distant birdsong outside.` |
| 动作描述 | `blinks slowly and gently licks its paw` —— 动词短语，具体的微动作比大动作更稳 |
