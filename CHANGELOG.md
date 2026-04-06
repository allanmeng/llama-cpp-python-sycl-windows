# Changelog

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
