# Changelog

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
