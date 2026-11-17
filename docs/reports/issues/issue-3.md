# Ref2VA partition + VDN linear branch 只警告不拒绝，产出「无发布配置」的结果

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
<!-- 全部条目均在本机复现，日志与命令可复现 -->

### 现象

在 Ref2VA partition 上挂 VDN 线性分支：

```json
"linear_branch": "OpenVDN/vdn-minimax-h3-stage-dmd"
```

运行时报一条 warning 后**继续跑完全流程并出片**（本机 12 分 54 秒）。

源码位置 `generative-models/minimax-h3/metal-minimax-h3-transformer.cc:8780`：

```cpp
if (L.ref2va && _cfg.partition == "ref2va") {
  _mc->session()->warn(fmt(
      "MetalMiniMaxH3Transformer: VDN's branch is trained on the "
      "FL2VA partition's blocks and this is Ref2VA; its {} reference "
      "rows are attended densely, outside the window, and the linear "
      "branch does not see them -- no published configuration pairs "
      "the two", L.num_condition_rows));
}
```

同一处的设计注释写得很清楚：

> *"On the Ref2VA partition the branch would be attached to blocks it was not trained with, **which nothing published does** -- that one still warns."*

文档同样说明：

> *"**the VDN branch is only published for FL2VA**, so before it the linear attention and references could not be had together."*

上游的官方组合是「FL2VA 权重 + references」（即 `ref2va-like` 模式）：引用行照 Ref2VA 的方式打包，但由 FL2VA 的 transformer 读取。

### 影响

- 系统明知该组合「没有发布配置」，却只给一条 warning 并照常出片；
- warning 淹没在数十行 `[INFO]/[PROGRESS]` 之后，实践中极易被忽略；
- 结果是**用户拿到一段看似成功、实则无参考支撑的视频**，可用于带货等对外场景，误用成本高。

### 建议

把这一组合从 `warn` 提升为**显式拒绝**（`error`），或提供明确的 opt-in 开关（例如 `allow_unpublished_partition_pair: true`），并在开关生效时于日志中打印醒目的横幅；文档中给出「Ref2VA 想要参考一致性应该用哪条路线」的指引（FL2VA + `ref2va-like`，或 Pika H3 Flex 的 `ref2va` adapter）。

---
