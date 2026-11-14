# `url-files` 型模型只绑定单一 GitHub URL，受限网络下无备用通道

<!-- 环境：macOS 27.2 / Apple Silicon M5 Pro / 24 GB 统一内存 -->
<!-- vpipe 版本：main @ 33cda00（源码编译，Apple Silicon 构建） -->
<!-- 全部条目均在本机复现，日志与命令可复现 -->

### 现象

官方文档给出的 TAE-H3 预览解码器准备流程无法完成：

```sh
vpipe --launch docs/pipelines/prepare-minimax-h3-preview.vpipeline
```

实测输出：

```
[INFO] ModelFetchStage('fetch'): fetching 'madebyollin/taehv' from raw.githubusercontent.com -> './models/madebyollin/taehv'
[INFO]   [1/1] taeh3.safetensors ...
[INFO]     taeh3.safetensors: interrupted at 0.0 B (SSL connect error); attempt 2/6 in 2s
...
[ERROR] ModelFetchStage('fetch'): model fetch 'taeh3.safetensors' failed: SSL connect error
```

### 分析

`stages/model-catalog.cc` 中该条目的 `extra` 字段给出**唯一一个** URL：

```cpp
{.family = "MiniMax", .version = "H3-FL2VA", .param_class = "TAE",
 .variant = "taeh3 temporal preview decoder (madebyollin)",
 .hf_path = "madebyollin/taehv",
 .model_type = "minimax-h3-tae",
 .parent_model_type = "minimax-h3-fl2va",
 .files = {"taeh3.safetensors"},
 .extra = catalog_url_files_extra(
     {{"https://raw.githubusercontent.com/madebyollin/taehv/main/"
       "safetensors/taeh3.safetensors",
       "taeh3.safetensors"}}),
 .name = "madebyollin/taeh3"},
```

`stages/model-fetch-stage.cc` 的 3b 分支（「Verbatim URL fetch ... a MODEL published somewhere this stage cannot walk」）按 URL 原样下载，没有候选列表与镜像回退。

问题在于 **`raw.githubusercontent.com` 与 `api.github.com` 的可达性并不相同**：同一文件、同一仓库、同一 commit，通过

```
GET https://api.github.com/repos/madebyollin/taehv/contents/safetensors/taeh3.safetensors
Accept: application/vnd.github.raw
```

可以正常取到（实测 22,709,752 字节，sha256 `4fd022bfcab08772fe0536b17ea1a3bbb5625be11e397868d1c5d891863d4c13`，与官方公布值一致），而 `raw.githubusercontent.com` 在本机被 SSL 阻断。

也就是说：受这一条 URL 影响的用户，**恰恰是文档中明确服务的中国大陆用户**（文档专门用 `modelscope` 源解决 HF 不通的问题），而 `url-files` 这条路径既没有 ModelScope 镜像，也没有备用主机。

### 影响面不止 taeh3

catalog 里凡是走 `catalog_url_files_extra` 的条目都受影响，包括：

- `madebyollin/taeh3`（H3 实时预览解码器）
- `madebyollin/taew2_1`（Krea-2 实时预览解码器）
- `vpipe-supplement` 的 CoreML 补充包

### 建议

1. `catalog_url_files_extra` 支持**候选 URL 列表**，按顺序尝试，第一个失败自动回退；
2. 或为 GitHub 系 URL 增加 `api.github.com` + `Accept: application/vnd.github.raw` 作为内置备选；
3. 至少在失败信息中把「源主机不可达」与「文件损坏」区分开（当前统一报 `SSL connect error`，用户难以判断是网络问题还是校验问题）。

---
