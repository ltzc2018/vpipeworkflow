# 文生图提示词模板库（本机实测）

> 实测模型：Z-Image-Turbo（8 步，42.5 秒）、Krea-2-Turbo（8 步，49.5 秒）
> 两者都吃自然语言描述，**英文效果更稳**。

---

## 1. 通用结构

```
[主体] + [动作/姿态] + [服装/材质细节] + [场景/背景] + [光线] + [画质标签] + --no text, no watermark, no logo
```

**`--no text, no watermark, no logo` 很关键** —— 实测不写会生成水印和假文字。

---

## 2. 电商主图（实测效果最好）

```
E-commerce product photograph of a dark blue denim jacket hanging on a wooden hanger
against a warm beige wall, soft directional window light from the left, crisp visible
denim weave texture, contrast stitching and brass buttons clearly visible, clean minimal
background, studio quality --no text, no watermark, no logo
```

**要点**：**点名要保真的细节**（「纽扣清晰可见」「丹宁织纹可见」），
否则模型会把它们糊掉。

**验证方式**：用 LFM3-VL 数扣子 —— 本机实测两模型都读出 **5 个扣子**，
「电商图要数得清扣子」这个硬指标过关。

---

## 3. 场景/氛围图

```
A ginger tabby cat wearing a dark blue denim jacket with brass buttons, sitting on a
wooden windowsill in warm late-afternoon sunlight, photorealistic, shallow depth of field
```

实测两个模型都独立复核出：橘色虎斑猫、牛仔外套、蓝色、有领子和纽扣、室内窗台。

---

## 4. 跨模态一致性技巧（重要）

**视频实验用的提示词可以原样喂给文生图模型**，得到同主体、同服装、同场景的静帧 ——
可以用来做视频链路的参考图，让画面与之前的视频对得上。

本轮实例：
- 视频提示词主体：「姜黄虎斑猫 + 深蓝牛仔外套 + 木窗台 + 暖阳逆光」
- 同一个提示词喂 Z-Image / Krea → 出来的静帧就是那只猫、那件外套、那个窗台

**反向用法**（给视频准备参考图）：
```
先文生图拿到满意的静帧 → 把它当首帧锚定图喂 vpipe-first-frame-to-video
→ 首帧 SSIM 0.9505，保真度远高于参考生视频（0.49–0.52）
```

---

## 5. 换装 / 保留身份（编辑类）

Boogu-Image-Edit（走 VLM 语义条件）的提示词是**一条编辑指令**，
不是描述句。结构：

```
[对参考图做什么] + [逐项点名要保留什么]
```

实测通过：
```
Keep the same woman, the same face, the same hairstyle and the exact same outfit and colors.
Place her in a clean high-end e-commerce studio with a soft light grey seamless backdrop,
soft even key light, natural skin texture, full body visible, centered.
Commercial fashion product photography, sharp focus.
```

```
Replace the background with a neon-lit rainy cyberpunk alley at night, keep the same cat,
same fur pattern, same pose and framing. Photorealistic, sharp focus,
moody teal and magenta rim light.
```

**要点**：
- **必须逐项点名**要保留的东西（服装、配件、姿态），否则模型会顺手改掉；
- 编辑模型**不要接 negative prompt、不要设 `guidance_scale > 1`**（Turbo 蒸馏版固定 CFG = 1）。

---

## 6. 视频提示词（给文生图做参考图时可直接复用）

```
References: @Image1 is the subject sheet. Make a new video of the subject from @Image1.
The subject sits on a wooden windowsill in warm late-afternoon sunlight, looks directly at
the camera, blinks slowly and gently licks its paw; the camera pushes in very slowly.
Audio: soft rhythmic purring, a faint breeze through the open window, distant birdsong
outside. Normal real-time speed, no slow motion. No text, no captions, no logos.
```

结构：`References: @Image1 …` + 场景 + 动作 + `Audio:` + 速度声明 + 排除项。

---

## 7. 本机模型的提示词差异

| | Z-Image-Turbo | Krea-2-Turbo |
|---|---|---|
| 引导 | **no cfg**（`guidance_scale = 0`） | 常规 CFG |
| 调度 | `simple (8 steps, shift 3 linear, rho 7)` | euler + simple |
| LoRA | 无 | **M87 LoRA 只在 HF**，本机用无 LoRA 版 |
| 提示词长度 | tokenizer 上限 512 token，**超了会被截断并打印警告** | — |

Z-Image 的截断提示（值得注意）：
```
DiffusionConditionerStage('text-prompt'): prompt truncated to N tokens,
which is this model's limit
```

---

## 8. 反面教材：不可证伪的提示词

**做消融/对照实验时，提示词不能写死外观**。

第一版消融实验用了「提示词写死『姜黄虎斑猫』」，结果：
- 空参考对照组**也**出姜黄虎斑猫 → **场景先验太强，实验不可证伪**；
- 重做时提示词**零外观描述**，空参考组出的是另一种东西；
- 再改用**水彩黑白熊猫**参考图（先验不可能命中）才做出有效对照。

**结论**：验证「参考图是否生效」时，**主体必须在模型先验里不可达**。

---

## 9. 自检清单

出图后逐条过：

- [ ] 有没有假文字 / 水印？（没写 `--no` 就会有）
- [ ] 关键细节数得清吗？（扣子、缝线、logo）
- [ ] 有没有多余肢体 / 畸变？
- [ ] 主体有没有跑偏？（尤其写实人像）
- [ ] 用 LFM3-VL 独立复核一遍，别只靠自己的眼睛
