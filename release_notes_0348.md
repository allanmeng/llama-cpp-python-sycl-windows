# llama-cpp-python 0.3.48+sycl (Intel Arc SYCL, Windows)

预编译 wheel，面向 **Windows + Intel Arc (SYCL / oneAPI)** 的 llama-cpp-python 0.3.48。

## 上游 0.3.48 关键改动（JamePeng fork, commit `7562297`）

- **Stateful MTP 投机解码（Speculative Decoding）**：`LlamaSpecEngine` 生命周期 + `SpecConfig` / `SpeculativeType` 落地；**BREAKING** 移除旧 `LlamaPromptLookupDecoding`，NGram 走新生命周期。推荐 Qwen3.8 27B 起手 `draft_n_max=2`；MTP 目前仅文本 / 单序列。
- **fix(mtmd) ctypes 指针绑定修正**：`unsigned char *` 从 `c_char_p` 改为 `POINTER(c_uint8)`。
- **llama.cpp 同步**：`ggml-org/llama.cpp` commit `bb4caa754`（llama.cpp 0.2.0，2026-08-21）。

## ⚠️ BREAKING: `GenericMTMDChatHandler` 构造签名变更（0.3.48）

```python
# 0.3.47
GenericMTMDChatHandler(clip_model_path=...)
# 0.3.48
GenericMTMDChatHandler(chat_format, mmproj_path, verbose=True, ...)
```

`chat_format` 可为 `None`（自动解析），`mmproj_path` 为**必填位置参数**。下游插件 / 自定义脚本作者必须跟进此变更。

## ⚠️ 已知集成注意：hybrid 视觉模型 + `ctx_checkpoints=0` 首 decode 崩溃

- 现象：Qwen3.5 等带 SWA 层的 hybrid 视觉模型，大图（约 4000+ vision tokens）下 prefill 正常，但**首 decode token 崩溃**（`failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`）。
- 根因：调用方传 `ctx_checkpoints=0` 会强制 hybrid 模型走 "Bypassing rollback" fast-path，大 prefill 下无槽余量给首 decode token。此问题在 0.3.48+ 稳定暴露。
- 规避：`ctx_checkpoints` 用默认 `-1`（启用 checkpoint 缓存，避开缺陷分支）。ComfyUI-sg-llama-cpp fork 已在 `1f0fc15` 将默认改为 `-1` 并加响应式 `n_ctx` hint。
- **本 wheel 本身无此 bug**：纯 `llama_cpp.Llama` 同模型同大图在 `n_ctx=8192` 下已双验证正常。

## 打包方式：方案 A（精简版）

whl **不自包含 oneAPI 运行时**，移除了与 oneAPI 重复的 DLL（`dnnl.dll`、`mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`、`tbb12.dll`），体积约 36 MB。**部署目标机需预装 Intel oneAPI**（SYCL 核心运行时 `sycl9.dll` / `OpenCL.dll` 及数值库由 oneAPI 提供）。

**`libomp140.x86_64.dll` 保留在 whl 中**（OpenMP 预加载依赖，不可删除）。

## 安装

```bash
pip install llama_cpp_python-0.3.48+sycl-cp313-cp313-win_amd64.whl
```

## 环境

| Item | Version |
|------|---------|
| Python | 3.13.11 |
| Intel oneAPI | 2026.1 |
| GPU | Intel Arc B580 (Battlemage) verified |
| scikit-build-core | 0.10.7 |

## 说明

- 自 0.3.43 起，`llama_cpp` 导入时自动注册自身 `lib/` DLL 搜索路径，ComfyUI 中通常无需 `sycl-preloader` 插件。
- 搭配的 Python XPU 运行时（`intel-xpu-backend-for-pytorch` / PyTorch XPU）必须 **≥ 2.13**，与 oneAPI 2026 ABI 对齐。
