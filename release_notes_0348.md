## [0.3.48+sycl] - 2026-08-22

### Changed from JamePeng (upstream 0.3.48)

升级至 llama-cpp-python 0.3.48（基于 JamePeng release commit `7562297`，tag `v0.3.48-cu128-win-20260821`）。关键改动（来自 JamePeng CHANGELOG）：

- **Stateful MTP 投机解码**：`feat(spec)` 落地 `LlamaSpecEngine` 生命周期管理 + `SpecConfig` / `SpeculativeType`；**BREAKING** 移除旧 `LlamaPromptLookupDecoding`，NGram 走新生命周期。推荐 Qwen3.8 27B 起手 `draft_n_max=2`；MTP 目前仅文本 / 单序列。
- **MTMD ctypes 指针绑定修正**：`fix(mtmd)` 将 `unsigned char *` 从 `c_char_p` 改为 `POINTER(c_uint8)`，修正视觉 / 音频缓冲区绑定（此前需手动 workaround 的坑已由上游修复）。
- **llama.cpp 同步**：同步至 `ggml-org/llama.cpp` commit `bb4caa754`（llama.cpp 0.2.0，2026-08-21）。

### Changed (this build)

- **零本地补丁**：llama.cpp `bb4caa754` 原生包含 PR #25880 修复（SYCL onednn fattn use-after-return 修复），本构建无需任何本地 patch。
- **打包方式为方案 A（精简版）**：whl **不自包含 oneAPI 运行时**，移除了与 oneAPI 重复的 DLL（`dnnl.dll`、`mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`、`tbb12.dll`），whl 体积约 36 MB。**部署目标机需预装 Intel oneAPI**（SYCL 核心运行时 `sycl9.dll` / `OpenCL.dll` 及上述数值库由 oneAPI 提供）。
- **`libomp140.x86_64.dll` 保留在 whl 中**：OpenCL/OpenMP 预加载修复依赖包内自带的该 DLL，不可删除。
- **⚠️ BREAKING：`GenericMTMDChatHandler` 构造签名变更（0.3.48）**：从 0.3.47 的 `GenericMTMDChatHandler(clip_model_path=...)` 变为 `GenericMTMDChatHandler(chat_format, mmproj_path, verbose=True, ...)`（`chat_format` 可为 `None` 自动解析，`mmproj_path` 为必填位置参数）。下游插件 / 自定义脚本作者必须跟进此变更，否则构造期直接报缺位置参数。视觉 handler（`Qwen3VLChatHandler` / `Qwen25VLChatHandler` / `GenericMTMDChatHandler`）及音频 handler（`Qwen3ASRChatHandler`）在本构建下均验证可正常导入。
- **⚠️ 已知集成注意：hybrid 视觉模型 + `ctx_checkpoints=0` 首 decode 崩溃**：Qwen3.5 等带 SWA 层的 hybrid 视觉模型，大图（约 4000+ vision tokens）下 prefill 正常但**首 decode token 崩溃**（`failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`）。根因为调用方传 `ctx_checkpoints=0` 强制 hybrid 走 "Bypassing rollback" fast-path，大 prefill 下无槽余量给首 decode token，此问题在 0.3.48+ 稳定暴露。规避：`ctx_checkpoints` 用默认 `-1`（启用 checkpoint 缓存，避开缺陷分支）。ComfyUI-sg-llama-cpp fork 已在 `1f0fc15` 将默认改为 `-1` 并加响应式 `n_ctx` hint。**本 wheel 本身无此 bug**：纯 `llama_cpp.Llama` 同模型同大图在 `n_ctx=8192` 下已双验证正常。

### Environment

| Item | Version |
|------|---------|
| Python | 3.13.11 |
| Intel oneAPI | 2026.1 |
| GPU | Intel Arc B580 (Battlemage) verified |

---
