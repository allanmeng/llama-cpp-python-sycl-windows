# Changelog
## [0.3.41+sycl] - 2026-07-11

### Changed from JamePeng

升级至 llama-cpp-python 0.3.41，包含 0.3.39 引入的 MTMD 重写及 0.3.41 的多项新特性。

---

#### 模板驱动的 MTMD（Template-Driven MTMD）

为 MTMD chat handler 新增 `extra_template_arguments` 参数，传递到 Jinja chat template 渲染调用中。这使得通用模型模板可以接收运行时选项，如 `enable_thinking`、`add_vision_id` 等模型特定的 Jinja 变量。

将 MTMD prompt 渲染逻辑拆分为独立 helper：

- `_render_mtmd_prompt()`：纯 chat template 渲染
- `_replace_media_placeholders()`：将渲染后的 media tag 规范化为 MTMD runtime marker
- `_render_and_replace_media()`：组合渲染与规范化

将 `mtmd_tokenize` 拆分为独立的 `_mtmd_tokenize()` helper，将混合 tokenization 逻辑与 `_process_mtmd_prompt` 解耦，改善 prompt 构建与 C++ binding 之间的关注点分离。

---

#### 更广泛的多模态输入（Broader Multimodal Inputs）

扩展 MTMD media extraction，支持模型 chat template 中常见的多种多模态内容格式。除了 OpenAI 风格的 `image_url`/`audio_url`/`video_url` chunk 之外，现在还接受 `image`/`audio`/`video` 类型的 chunk 以及直接的 media key，如 `{"image": "..."}`、`{"audio": "..."}`、`{"video": "..."}`。

新增 `video_url` 输入支持：`MTMDChatHandler` 现在可以处理视频输入。会检测加载的 libmtmd 是否支持 video helper，在不支持时提前拒绝视频输入。

---

#### GenericMTMDChatHandler 增强

增强 `GenericMTMDChatHandler` 对模型自带 chat template 的支持：

- 接受可选的命名 chat template
- 通过 `llama_model_chat_template()` 在调用时从模型加载
- 回退到模型默认 chat template
- 最终使用内置 `MTMD CHAT_FORMAT` 作为兜底

扩展通用 media placeholder 列表以适配常见多模态模板。

---

#### 更智能的 N-Gram 投机解码（Smarter N-Gram Drafting）

改进投机解码的 n-gram draft 选择和 accept 反馈机制：

- 按 key/value 存储已接受的 draft 长度，并相应截断未来的 draft
- key-only 模式下在任何 key 匹配时即进行 draft，不再要求 `min_hits`
- k4v continuation 按频率选择而非最近出现
- 当 top continuation 不占主导时跳过有歧义的 k4v draft
- 跟踪固定大小的 k4v continuation 以保持频率统计的可比性

---

#### 模块重构：多模态 handler 迁移至 llama_multimodal

将 `MTMDChatHandler`、`GenericMTMDChatHandler` 及模型特定的多模态 chat handler 从 `llama_chat_format.py` 迁移至独立的 `llama_multimodal.py` 模块。

`llama_chat_format.py` 随着多模态支持扩展已变得过于庞大。拆分后 chat formatting 层更精简，media loading、MTMD tokenization、KV-cache 管理和 handler 实现集中在专用模块中。

保留 `llama_chat_format.py` 的向后兼容 re-export，现有 import 不受影响。

将 `clip_model_path` 保留为 `mmproj_path` 的废弃初始化别名。

---

#### 其他改进

- llama.cpp 同步至 `ggml-org/llama.cpp` commit [`3899b39`](https://github.com/ggml-org/llama.cpp/commit/3899b39ce2acc2e019f149b7107f24b6ca297390)
- 改进 Windows LLVM OpenMP 运行时 `libomp140.x86_64.dll` 的发现逻辑，优先使用 VS 2022 VC143 OpenMP redist
- `load_shared_library` 失败时的错误信息现在包含搜索目录的内容列表，便于诊断缺失或错误命名的库文件
- `LlamaModel.model_chat_template()` 返回 `Optional[str]`，正确处理模型无 chat template 的情况
- 新增 `MTMDChatHandler` chunk type helper（`_is_text_chunk`/`_is_image_chunk`/`_is_audio_chunk`）

---

### Changed

- Upgraded to llama-cpp-python 0.3.41
- Removed `bin/` directory from whl package during post-compile cleanup
  - `bin/` 目录由 llama.cpp 构建系统自动生成，仅包含 7 个核心 DLL（`lib/` 目录 14 个 DLL 的子集）
  - `llama_cpp` 的 `load_shared_library` 会将 `[lib/, bin/]` 依次 prepend 到 PATH，导致 `find_library` 优先命中 `bin/` 下的 DLL
  - 7 个核心 DLL 从 `bin/` 加载，5 个 oneAPI DLL 从 `lib/` 加载，Windows DLL loader 对不同路径的同名模块视为不同实例，引发 SYCL 运行时初始化冲突（access violation 崩溃）
  - 打包前删除 `bin/` 后，所有 DLL 统一从 `lib/` 加载，问题消除
- Continued to remove bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size ~22 MB

### Notes

- This version includes MTMD rewrite (since 0.3.39), which breaks API compatibility with 0.3.38 and earlier for vision model usage
- Key API changes from 0.3.39+:
  - `clip_model_path` removed → use `mmproj_path` passed to `Llama()`
  - Model-specific vision handlers deprecated → `GenericMTMDChatHandler` handles all vision models
  - Handler parameters passed via `chat_handler_kwargs` dict
  - Hybrid architecture models (e.g. Qwen3.5) require `ctx_checkpoints=0`
- If you use vision models (Qwen-VL, etc.) in ComfyUI, you must use the adapted plugin: https://github.com/allanmeng/comfyui-sg-llama-cpp
- Installation still requires Intel oneAPI runtime to be installed on the target machine

### Environment

| Item | Version |
|------|---------|
| Python | 3.13.11 |
| Intel oneAPI | 2025.3.2 |
| GPU | Intel Arc B580 (Battlemage) verified |

### Upgrade from 0.3.38 or earlier

> **Do NOT use `pip install --upgrade` directly.** Residual files from the old version may conflict with the new one. Follow these steps:

**Step 1: Uninstall the old version**

```bat
pip uninstall llama-cpp-python -y
```

**Step 2: Install the new version**

```bat
pip install llama_cpp_python-0.3.41+sycl-cp313-cp313-win_amd64.whl
```

**Step 3: Update your ComfyUI plugin to the adapted version**

If you use `comfyui-sg-llama-cpp`, switch to the adapted fork:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/allanmeng/comfyui-sg-llama-cpp
```

---

## [0.3.38+sycl] 优化 CJK 解码回绕、同步语法解析器，并修复 CUDA Graph 日志 - 2026-05-01
Changed from JamePeng

### 主要新特性
#### 性能优化：针对 CJK 高频输出的解码缓冲区大小优化

- 将初始的解码回绕（detokenize）缓冲区估算值从原来的“token 数 x1”增大为“token 数 x5 + 32 字节”。性能分析显示，CJK 高频输出场景中每个 token 往往需要约 4.0 至 5.04 字节，处理极小 token 的边缘情况甚至需要约 6.0 字节。旧的估算值经常导致 llama_detokenize 调用失败，进而需要重新调整缓冲区大小并重试，这使得 llama_detokenize 的调用次数几乎翻倍。
- 本次优化减少了不必要的解码重试，降低了 CJK 场景下的调用开销，实测推理性能提升了约 3%–5%。

#### 补丁（日志）：过滤掉冗长且杂乱的 CUDA Graph 调试日志

- 在 ggml_log_callback 中添加了临时补丁，用于抑制底层 C++ 后端生成的、类似 CUDA Graph id %zu reused 这类嘈杂日志。未来计划对日志系统进行全面重构，以实现更好的日志控制。

#### 功能（语法）：与上游同步更新 JSON Schema 到 GBNF 转换器

- 允许 LlamaGrammar.from_json_schema 和 json_schema_to_gbnf 同时接受字符串和字典格式的 schema 输入。

- 将 allow_fetch、dotall 和 raw_pattern 参数暴露给公共 API，与上游脚本保持一致。

- 修复了处理空/无约束 schema 对象（例如 {"description": "..."}）时缺失的逻辑，现在此类情况会正确默认为接受任意值。

- 修复了当变量为零时 has_min 和 has_max 计算错误的问题。将 != None 替换为 is not None 以生成最小/最大整数。

- 更新了内部常量与正则表达式（INVALID_RULE_CHARS_RE、GRAMMAR_LITERAL_ESCAPE_RE、GRAMMAR_RANGE_LITERAL_ESCAPE_RE），解决了字符转义问题。

- 更新了参考链接，指向新的 ggml-org 组织。

### Changed
- Upgraded to llama-cpp-python 0.3.38
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~22MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.36+sycl] - 2026-04-17

### Changed from JamePeng
 Gemma-4 全模态和工具调用功能改进，支持 Qwen3.6 / Step3-VL，编译工作流程优化
  #### feat: 增强 Qwen35ChatHandler，支持 preserve_thinking 并兼容 Qwen3.6
  - 新增 `preserve_thinking` 参数，可选择性地在历史对话中保留 `<think>` 推理块（默认 `False` 以节省 Token）。
  - 在 Jinja 模板中为 `enable_thinking` 添加 `is defined` 安全检查。
  - 简化了模板中工具调用参数的 JSON 序列化逻辑。
  - 更新类文档，明确支持 Qwen 3.5 和 Qwen 3.6 模型。
  - 在详细日志中包含 `preserve_thinking` 状态。
  
  #### docs: 为 Gemma-4 添加全能多模态 (Omni Multimodal) 示例
  - 将 Qwen3-VL 示例移至 `<details>` 折叠块以优化 README 布局。
  - 新增生产级示例，展示使用 `Gemma4ChatHandler` 同时处理视觉与音频。
  - 引入通用 `build_media_payload` 助手函数，支持本地文件到 OpenAI 格式的动态编码。
  - 澄清 Gemma-4 各变体的多模态差异：E2B/E4B（全能型）对比 31B/26BA4B（仅视觉）。
  
  #### docs: 为 Gemma4ChatHandler 添加音频处理建议
  - 推荐针对 Gemma4 E2B/E4B 使用 BF16 精度的 `mmproj`。
  - 标注了其他量化版本中已知的音频性能退化问题。
  - 关联了相关 `llama.cpp` 的 PR/Issue 讨论链接。
  
  #### refactor: 同步 Gemma4ChatHandler 聊天模板
  - 对齐 HuggingFace 最新 `google/gemma-4-31B-it` 模板，引入 `format_tool_response_block` 和前向扫描工具解析。
  - 更新针对 OpenVINO/Metal/Vulkan/SYCL 的 README 说明。
  
  #### feat: 实现 Step3-VL-10B 专用 Step3VLChatHandler
  
  #### feat(types): 对齐最新 OpenAI API 规范
  - 扩展 `CompletionUsage`，支持 `PromptTokensDetails` 等细粒度 Token 追踪。
  - 为流式响应添加 `usage` 字段支持。
  - 修复 `CreateCompletionResponse` 中的字段重复问题。
  - 更新 `ChatCompletionRequestAssistantMessage` 支持 `None` 内容及 `refusal` 字段。
  - 优化 `ChatCompletionToolChoiceOption` 以支持 `allowed_tools` 自定义行为。
  
  #### feat(ci): 优化 CUDA 与 METAL 的 GitHub 构建工作流
  - **Action 版本升级**: 升级 `checkout` (v6), `upload-artifact` (v6) 等核心组件。
  - **构建优化**: 将 `cudaarch` 限制为 Volta-Hopper (7.0-9.0)，解决 CUDA 12.4+ 编译导致的 6 小时超时问题，确保现代 GPU 兼容性的同时缩短构建耗时。
  
  #### feat: 更新 llama.cpp 核心至 commit `9db77a0`
  
  #### feat: 同步 llama.cpp llama/mtmd 20260415 版 API 绑定

### Changed
- Upgraded to llama-cpp-python 0.3.36
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~19MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.35+sycl] - 2026-04-06

### Changed from JamePeng

1. Gemma 4 系列全面支持
- 新增对话处理器 (Gemma4ChatHandler)： 实现了 Gemma 4 特有的 Token 结构（如 <|turn|>、<|channel|> 等），支持多模态输入（图像、音频）和工具/函数调用。
- 停止逻辑优化： 修复了生成停止序列，增加了 GEMMA4_EOS_TOKEN 等识别，防止模型在生成结束或调用工具时出现“过度生成（幻觉复读）”的问题。
- 思维链控制 (Reasoning/Thinking)： 为 Gemma 4 的 31B 和 26BA4B 版本增加了 enable_thinking 开关。注意： 明确指出 E2B（你使用的版本）和 E4B 暂不支持此功能。

2. 新模型适配与修复
- LFM 2.5-VL 支持： 实现了针对 LFM 2.5-VL 视觉模型的对话处理器。
- Qwen 3.5 修复： 修正了 Qwen 3.5 对话模板中的拼写错误。

3. OpenAI API 规范深度对齐
- 结构化输出 (Structured Outputs)： 放弃了 Anyscale 的旧格式，全面采用官方 OpenAI json_schema 响应格式。
- 新增字段支持： 支持音频输入/输出、developer 角色（开发者角色定义）、拒绝回答（refusal）以及内容过滤（content_filter）等字段。

4. 底层架构迁移与重构
- 日志系统迁移： 将日志回调从旧的 llama_log_callback 迁移到了新的 ggml_log_callback，以匹配上游 GGML 的架构调整。
- 核心库同步： 引入了对 ggml-base 共享库的支持，并同步了 llama.cpp 截至 2026年4月2日 的最新 API 绑定。


### Changed
- Upgraded to llama-cpp-python 0.3.35
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~19MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---
## [0.3.34+sycl] - 2026-04-01

### Changed
- Upgraded to llama-cpp-python 0.3.34
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~19MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.33+sycl] - 2026-03-17

### Changed
- Upgraded to llama-cpp-python 0.3.33
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~18MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.32+sycl] - 2026-03-09

### Changed
- Upgraded to llama-cpp-python 0.3.32
- Removed bundled oneAPI runtime DLLs from whl (`dnnl.dll`, `mkl_core.2.dll`, `mkl_sycl_blas.5.dll`, `mkl_tbb_thread.2.dll`, `tbb12.dll`)
- WHL size reduced from ~130MB+ to ~18MB
- oneAPI runtime DLLs are now expected to be provided by the user's local oneAPI installation via `setvars.bat`

### Notes
- oneAPI upgrades no longer require repackaging the whl
- Installation now requires Intel oneAPI runtime to be installed on the target machine

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.31+sycl] - 2026-03-07

### Added
- Upgraded to llama-cpp-python 0.3.31
- Bundled full oneAPI runtime DLLs for standalone deployment (no oneAPI installation required)
- Added `ur_loader.dll`, `ur_adapter_level_zero.dll`, `ur_adapter_level_zero_v2.dll`, `ur_win_proxy_loader.dll`
- Added `ur_adapter_opencl.dll`, `libiomp5md.dll`, `libhwloc-15.dll`
- Added `umf.dll`, `tcm.dll`, `ggml-rpc.dll`, `svml_dispmd.dll`
- Support for `Qwen25VLChatHandler` and `Qwen3VLChatHandler`

### Fixed
- Removed duplicate DLLs from `bin/` and `lib/` subdirectories

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.30+sycl] - 2026-03-07

### Added
- Initial release
- llama-cpp-python 0.3.30 compiled with SYCL support
- Intel Arc GPU acceleration via Intel oneAPI
- Verified working on Intel Arc B580 (Battlemage)
- Full oneAPI runtime DLLs bundled

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified
