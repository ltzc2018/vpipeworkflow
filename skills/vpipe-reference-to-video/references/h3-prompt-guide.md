# MiniMax-H3 官方提示词规范指南 (2026-11-20 固化)

## 1. 三字段核心结构 (Three Labeled Fields)
H3 是 CFG 蒸馏模型，**无负向提示词**。必须通过以下三个字段进行结构化控制：

### 1.1 integrated_multimodal_description
- **职责**：描述视觉画面、镜头运动、动作、人物对话及同步音效。
- **分镜切换**：除首镜外，后续分镜以 `At 00:XX.XXX, the camera cuts to...` 引导。
- **对话/歌唱**：使用 `(S1) [English] "Lines..."` 格式，(S1) 为稳定的人物 ID。

### 1.2 overall_soundscape
- **职责**：描述环境音（风、雨、车流）、物理动作音（撞击、脚步）、呼吸音。
- **注意**：不要重复 1.1 中已描述的对话或同步音。

### 1.3 non_diegetic_music
- **职责**：描述仅观众可见的背景音乐、配乐（Instrumentation, speed, rhythm）。

---

## 2. 动作描述「八阶段」法 (The Action Chain)
为了提升动作的连贯性，建议将主行动分解为以下阶段：
1. **Preparation**: 准备动作
2. **Trigger**: 触发点
3. **Acceleration**: 加速过程
4. **Primary action**: 核心动作
5. **Contact**: 物理接触/碰撞
6. **Reaction**: 反应/反馈
7. **Recovery**: 恢复状态
8. **Final state**: 最终状态

---

## 3. 官方镜头运动词典 (14 Motion Types)
描述应融入自然语言句中（如 "The camera pushes in with small amplitude at slow speed..."）：
- **缩放**: Zoom In / Zoom Out
- **推进**: Push In / Pull Out
- **平移**: Pan Left / Pan Right
- **横移**: Truck Left / Truck Right
- **仰俯**: Tilt Up / Tilt Down
- **垂直**: Pedestal Up / Pedestal Down
- **特技**: Arc Shot, Tracking Shot, Static Shot, Shake, POV, Roll.

---

## 4. 参考模式锚定 (Anchor Logic)
| 模式 | 锚定点 | 描述路径建议 |
|---|---|---|
| **I2VA** | 首帧 | 建立风格与构图，描述向后的演化 |
| **FL2VA** | 首帧 + 末帧 | 描述两点之间的合理演化路径 |
| **L2VA** | 末帧 | 描述如何收敛到最终画面的前置动作 |
| **Ref2VA** | 多参考 | 明确不变量 (Subject) 与变化量 (Action) |
