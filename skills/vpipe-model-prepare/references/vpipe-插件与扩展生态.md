# vpipe 插件与扩展生态（2026-11-19 第 11 轮新建）

> 最后更新：**2026-11-19 21:30**（第 11 轮夜间知识同步）
> 本文档记录 vpipe 核心仓库之外的独立插件及第三方扩展能力。

---

## 1. vpipe-ltx-2.5（Lightricks 22B 视频/音频模型）

### 1.1 概览
- **仓库**：`tgo-app-dev/vpipe-ltx-2.5`
- **形态**：独立 C++ 插件（需 `plugin ABI 8` 及 vpipe 0.1.80+）。
- **模型**：LTX-2.5（22B 参数），支持视频与音频同步生成。
- **许可**：LTX-2.x Community License（不同于 vpipe 的 Apache-2.0）。

### 1.2 关键能力
1. **全模式生成**：支持 Text-to-Video (T2V)、Image-to-Video (I2V) 以及音频参考 (Audio-Reference)。
2. **潜空间 2× 超分 (Latent Upscale)**：
   - 机制：在 VAE 解码前直接对 latent 做单卷积前向放大。
   - 保真度：实测 **26.9 dB**（对比 Lanczos 2x 插值）。
   - 规格：支持 960x544 → 1920x1088。
3. **固定步数合约**：
   - 模型为蒸馏版本，固定为 8 步。
   - 行为：若流水线设置 `steps: 6`，插件会 **忽略** 并强制执行 8 步。

### 1.3 性能参考 (64GB M4 Pro)
- 960x544, 121 帧 (5s): 总耗时约 **532s** (≈8.8m)。
- DiT Denoise: 410.9s (约 51.4s/步)。

---

## 2. Valtz (原生 macOS GUI)

### 2.1 概览
- **仓库**：`tgo-app-dev/valtz`
- **形态**：使用 C++ 和 Metal 构建的 macOS 原生桌面应用。
- **定位**：vpipe 的官方图形化前端，替代基于浏览器的 Composer。

### 2.2 特色功能
1. **内置技能卡**：集成了 MiniMax 官方的 H3 提示词六段式编写技能。
2. **多模型支持**：原生支持 H3-Image、FLUX.3 Klein、Qwen-Image、Music3、Moss-TTS。
3. **提示词格式**：全面支持 `<Picture N>`、`<Video N>` 等新型标签格式。

---

## 3. 插件开发纪律
1. **ABI 锁定**：插件必须针对特定版本的 vpipe ABI 编译。
2. **路径加载**：非内置 stage 需通过 `plugins/` 目录或显式加载路径挂载。
