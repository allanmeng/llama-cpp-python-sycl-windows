[English](README_EN.md) | [中文](README.md)

# llama-cpp-python-sycl-windows

Pre-built [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) wheels with **Intel Arc GPU (SYCL)** acceleration for Windows.

Compiled from [JamePeng's fork](https://github.com/JamePeng/llama-cpp-python) which adds SYCL support for Intel Arc GPUs.

---

## Latest Release Notes (v0.4.7+sycl · 2026-11-13)

**Key highlights: oneAPI 2026.2 build migration + the exclusion list grows to 6 DLLs (now including `mkl_intel_thread.3.dll`) + performance on par with 0.4.6 + upstream MTP device states and multi-GGUF shard support**

- Upgraded to llama-cpp-python **0.4.7** (based on JamePeng `c7c7055`, llama.cpp `2a4daf0e0` = b12345, **171 submodule commits**, zero local patches; **16 commits** since 0.4.6's `1dd04be`, one of which only bumps the version and five only move the submodule pointer)
- **🆕 The exclusion list grows from 5 to 6 DLLs (the change you most need to know about)**: **`mkl_intel_thread.3.dll` (38.95 MiB)** is now excluded too — the `ggml-sycl.dll` built with oneAPI 2026.2 imports it, and shipping it would inflate the wheel from 43 MB to about **84 MB**. Full exclusion list: `dnnl.dll`, `mkl_core.3.dll`, `mkl_sycl_blas.6.dll`, `mkl_tbb_thread.3.dll`, `tbb12.dll`, `mkl_intel_thread.3.dll`, so the **wheel stays at 43 MB (43.13 MiB)**. Upstream landed **`#32005`** doing the very same thing for its Windows SYCL release package — this is a general 2026.2 issue
- **⚠️ `setvars.bat` is mandatory**: every excluded DLL must come from the target machine's oneAPI. **Drop `setvars.bat` from your launcher and `ggml-sycl.dll` fails to load and silently falls back to CPU, with no loud error.** A "no-setvars" variant (bundling 12 extra DLLs and rewiring the `lib/` search path) was tried and rejected: B580 on 2026.2 requires the **Level Zero v2 adapter**, but `ur_adapter_level_zero_v2.dll` fails with **error 127 (missing entry point)**, falling back to `[opencl:gpu:0]`
- **oneAPI 2026.2 build migration**: compiler moves from clang **22 to 23** (`icx` 2026.2.0 Build 20261001) with **no build-flag changes**; the bundled oneDNN is still **3.13.2** (the 2026.2 installer's `dnnl` directory still points at 2026.1) and no runtime DLL was renamed. **This wheel is built and measured with 2026.2. If you are still on 2026.1**, the required runtime DLL names match (2026.1 also ships `mkl_intel_thread.3.dll`), but that combination is **not tested here** — just load it through `setvars.bat` as usual
- **Upstream core highlights** (all backwards compatible for this plugin): **MTP device-side hidden-state transfer** (new `draft_n_ubatch`, `LLAMA_MTP_DEV=0` forces the host path; this plugin uses no speculative decoding, so it does not apply); **`Llama(model_shards=...)` / `SpecConfig.draft_model_shards`** for extra GGUF shards and external PLE tables; **bindings alignment** (NextN device-state, architecture-capability, decision-label, `moe_cache_cpu_share`); **MTMD audio ABI + mono f32 PCM streaming resampler + Kimi K3.1 image placeholders**; **grammar** gains numeric `allOf` intersections and corrected chess / Japanese-rules grammars (`llama_grammar.py` changes for the first time)
- **⚠️ Self-builders must pin vendor to `2a4daf0e0`**: upstream states this revision sits **before** `ggml : prune` (`29dbbad2b`) and `llama : prune` (`8ca5a8008`), and that native libraries **must be rebuilt from it** to match the updated context and audio parameter ABIs. **This build uses exactly that revision — do not rebuild from a later prune commit**
- **None of the 13 SYCL items targets throughput, so performance is flat versus 0.4.6 (expected)**: **`#31285` rejects over-VRAM allocations and adds `GGML_SYCL_BMG_VRAM_CHECK` (default 1)** — applies to **BMG only**, so **it is on by default on B580**; an oversized allocation now logs `cannot allocate ... MiB` and is refused instead of crashing the driver; `#31138` makes the oneDNN FA cache thread-safe; `#31784` fixes `CLAMP` for strided views; `#31896` MUL_MAT src1 precision gating (the F32 path here is unchanged); `#31126`/`#32013` cache the device-id; `#31873` AOT above 4 GB (we run JIT); `#30156` device-side MoE scheduler (dense model, does not apply); `#31574` is **Alchemist / A770 only**, not B580; `#30802` YaRN (not enabled); `#30857` `SWIGLU_OAI` f16 (this build has `F16: no`); `#31465` CPY rounding precision (model has none of those types)
- **⚠️ One easy misread**: `#31084` (CUDA / Metal radix Top-K determinism) **contains no SYCL code changes** (only `ggml-cuda`, `ggml-metal` and tests), so it must not be counted as a SYCL item
- **Plugin compatibility: zero changes needed**: `Llama.__init__` **76 params**, `create_chat_completion` **55 params**, `GenericMTMDChatHandler.__init__` **6 params** — all identical to 0.4.6. [comfyui-sg-llama-cpp](https://github.com/allanmeng/comfyui-sg-llama-cpp) needs no changes
- **New APIs all live in `_internals` (easy trap when writing probe scripts)**: `suppress_tokens` / `classifier_free_guidance` are on `llama_cpp._internals.LlamaModel`, and `supports_embd_row` / `set_embeddings_layer_inp_dev` on `llama_cpp._internals.LlamaContext` — **the top-level `llama_cpp` package does not export `LlamaModel` / `LlamaContext`**, so `hasattr(llama_cpp.LlamaModel, ...)` reports a false negative
- **Memory footprint identical to 0.4.3 / 0.4.5 / 0.4.6**: `SYCL0 compute buffer` **513.02 MiB**, `SYCL_Host` **28.03 MiB**, `matches expectation` on both cold and warm runs — no growth, no leak; the new BMG VRAM check **did not fire** on the 4032-token large image
- **2 new SYCL environment variables**: **`GGML_SYCL_BMG_VRAM_CHECK`** (default `1`, BMG VRAM check, set `0` to disable) and **`GGML_SYCL_MMID_SCHED`** (default `1`, device-side MoE scheduling, MoE models only); nothing was removed, other defaults are unchanged, and `GGML_SYCL_ENABLE_GRAPH` still defaults to `0`
- **Build note**: clean single pass (10 min 28 s); the `-fsycl` device compile **deadlocked a second time** at `fattn-vec-instance-q4_0-f16.cpp` (CPU flat), and a process-tree kill plus a rerun cleared it — same root cause as the 0.4.5 link-stage deadlock, **not a code issue**
- **⚠️ Known integration note (carried over from 0.3.48 / 0.3.49 / 0.4.0 / 0.4.1 / 0.4.2 / 0.4.3 / 0.4.5): hybrid vision model + `ctx_checkpoints=0` first-decode crash**

- Symptom: hybrid vision models with SWA layers (e.g. Qwen3.5), on large images (~4000+ vision tokens), prefill succeeds but **first decode token crashes** (`failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`)
- Root cause: caller passing `ctx_checkpoints=0` forces the hybrid model down a "Bypassing rollback" fast-path that has no slot headroom for the first decode token on large prefills
- **Status in this release: still not re-tested specifically.** 0.4.6 added a round of safety cleanup around context capacity and sampler lifetime (`n_ctx_seq`, early rejection of oversized embedding inputs, samplers retained until context destruction), and 0.4.7 aligns context parameters with `moe_cache_cpu_share`; both hardware runs in this release (cold + warm) kept `ctx_checkpoints=-1` and did not trigger the issue
- Workaround: **keep the default `ctx_checkpoints=-1`**
- **✅ Official recommended plugin fixed**: [comfyui-sg-llama-cpp](https://github.com/allanmeng/comfyui-sg-llama-cpp) changed the default to `-1` in `1f0fc15` with a reactive `n_ctx` hint. No manual handling needed when using this plugin
- **This wheel has no such bug**: pure `llama_cpp.Llama` on the same model + large image at `n_ctx=8192` verified working

**🚀 Measured performance (Qwen3.5-4B vision model + images, 0.4.7, Intel Arc B580):**

> ✅ The test machine is an **Intel Arc B580 Graphics** with the exact same driver as 0.4.6 (SYCL 20.1 / `1.17.39894+4` / 160 CUs / `Reorder=Y`), so the hardware side introduces no variable. **⚠️ However the warm run does not use the same image as the 0.4.6 baseline** (0.4.7: **2336×1760 / 4015 tokens**; 0.4.6: **1792×2304 / 4032 tokens**), so **only rate metrics get a cross-version Δ — image encode time and total time are not compared**.

| Metric | Large image 2336×1760 (warm) | Large image 1792×2304 (cold, reference only) |
|--------|------------------------------|----------------------------------------------|
| Vision tokens | 4015 | 4032 |
| Image encode time | **11233 ms** (clip_encode) | 26731 ms (clip_encode) |
| Image decode time | 1125 ms (1/2) + 1451 ms (2/2) | 3935 ms (1/2) + 3161 ms (2/2) |
| Prompt eval | **1328.76 t/s** (3041.93 ms / 4042 tokens) | 31.59 t/s (128494.43 ms / 4059 tokens) |
| Generation speed | **90.02 t/s** (eval 12897.76 ms / 1161 runs) | 90.53 t/s (eval 13774.83 ms / 1247 runs) |
| Total time | 42.03 s | 191.62 s |
| load time | 131.20 ms | 66111.51 ms |
| SYCL compute buffer | SYCL0 513.02 MiB / SYCL_Host 28.03 MiB | same as left |

**Against 0.4.6 — rate metrics only** (different images):

| Item | 0.4.6 | 0.4.7 | Δ |
|------|-------|-------|---|
| Prompt eval (warm) | 1330.03 t/s | **1328.76 t/s** | **flat (−0.10%)** |
| Generation speed (warm) | 90.66 t/s | **90.02 t/s** | −0.71% (within noise) |
| Generation speed (cold) | 89.89 t/s | **90.53 t/s** | +0.7% (within noise) |
| SYCL compute buffer | 513.02 / 28.03 MiB | same | identical |

> Test scene: Qwen3.5-4B-Uncensored-Q4_K_M + mmproj-BF16, hybrid architecture (with SWA layers), `ctx_checkpoints=-1`, `n_ctx=8192`, `n_batch=2048` (large image fed as `2048 + 1967`).
>
> **Why this release gains nothing — expected, not a failed optimization**: the 13 SYCL items break down as packaging fix (`#32005`), allocation guard (`#31285`), thread safety and failure memoization (`#31138`), `CLAMP` correctness (`#31784`), precision semantics (`#31896`), device-id caching micro-optimizations (`#31126` / `#32013`), AOT (`#31873`), MoE scheduling (`#30156`), an Alchemist-only un-gate (`#31574`), YaRN (`#30802`), CPY rounding precision (`#31465`), and `SWIGLU_OAI` f16 (`#30857`) — **none targets `mul_mat` throughput**. 0.4.6's +5.9% came from the `#31013` / `#31008` / `#31325` MMVQ templating batch, and this release has no comparable commit.
>
> **The two independent generation readings agree closely**: 90.53 cold, 90.02 warm — only **0.57%** apart across two image sizes and two cache states, so the metric is stable and reproducible; the gap to 0.4.6's 90.66 is measurement noise.
>
> **The cold-run figure (191.62 s) cannot be compared**: on a brand-new DLL, `load time` hits 66.1 s, `clip_encode` 26.7 s and prompt eval 31.59 t/s because Level Zero's program cache is fully invalidated and every kernel is re-JITed. **That cost is one-off** — the second run drops `load time` to 131 ms and restores prompt eval to 1328.76 t/s. Generation speed is already normal in the cold run, because the decode kernels finish JITing during encode.

**Community feedback:**

> ✅ **"Qwen 3.8 27B working fine with `llama_multimodal.GenericMTMDChatHandler`"** — vision model compatibility confirmed
> See: https://github.com/JamePeng/llama-cpp-python/discussions/169#discussioncomment-18036209

**Wheel**: `llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl` (**43.13 MiB / 45,220,961 B**, md5 `cbede18e0214fadc5c980d773a9e43ac`, slim build, **requires oneAPI 2026.2** and `setvars.bat` in the launcher)

> 📥 **Download oneAPI 2026.2**
>
> - Official: https://www.intel.com/content/www/us/en/developer/tools/oneapi/oneapi-toolkit-download.html
> - Mirror (Quark): https://pan.quark.cn/s/be61433cc224
>
> The official page is a generic entry point — **pick 2026.2 manually** in the downloader (don't accidentally install a newer or older release); the mirror is a fixed build. Close ComfyUI and any other consumer before installing, **reboot** afterwards, and make sure `call setvars.bat` is still in your launcher — the log must show `GGML_SYCL_SUPPORT_LEVEL_ZERO_API: yes` and `[level_zero:gpu:0]`, otherwise the backend has **silently fallen back to CPU**.

---

## Important Changes in 0.3.39+

### 1. What Changed in llama-cpp-python-sycl-windows After 0.3.39

Starting from version 0.3.39, llama-cpp-python introduced a major **MTMD (Multi-Modal Token Decomposition) rewrite**, restructuring how vision models are supported:

| Change | 0.3.38 and Earlier | 0.3.39+ |
|--------|-------------------|---------|
| Vision model loading | Manual `clip_model_path` handler injected into `Llama()` | `mmproj_path` passed directly to `Llama()`, handler created internally |
| Vision handler class | Model-specific handlers (e.g. `Qwen3VLChatHandler`) | `GenericMTMDChatHandler` handles all vision models |
| Handler parameter passing | Direct to handler constructor | Via `chat_handler_kwargs` dict |
| Hybrid architecture models | No special handling | Use default `ctx_checkpoints=-1` (e.g. Qwen3.5); **do not pass `0`** — 0.3.48+ triggers hybrid fast-path first-decode crash |

### 2. Manual Cleanup Required for Users Upgrading from Pre-0.3.39

> **Important**: Do NOT use `pip install --upgrade` directly. Stale files from the old version may conflict with the new one. Follow these steps instead:

#### Step 1: Completely Uninstall the Old Version

```bat
pip uninstall llama-cpp-python -y
```

#### Step 2: Install the New Wheel

```bat
pip install llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl
```

#### Step 3: Update Your ComfyUI Plugin

If you use this whl in ComfyUI, you must use a plugin version adapted for 0.3.39+ (see section 3 below).

### 3. Adapted ComfyUI Plugin

The original `comfyui-sg-llama-cpp` plugin does not support the 0.3.39+ MTMD rewrite. The following fork has been adapted:

**https://github.com/allanmeng/comfyui-sg-llama-cpp**

Adaptation details:
- **`clip_model_path` → `mmproj_path`**: Passed directly to `Llama()`, no manual handler creation
- **`GenericMTMDChatHandler` parameter filtering**: Takes the union of `GenericMTMDChatHandler` ∪ `MTMDChatHandler` parameters, filtering out `force_reasoning`, `enable_thinking`, and other params not accepted in 0.3.39+
- **Added `ctx_checkpoints` option** (default `-1`): hybrid architecture models (Qwen3.5 etc. Transformer+Mamba) use the default; **do not set `0`** — 0.3.48+ triggers hybrid fast-path first-decode crash
- **`vision_image_min_tokens` default** changed from `-1` to `1024` (Qwen-VL minimum requirement)
- **Removed invalid UI params**: `vision_enable_thinking`, `vision_force_reasoning`, `vision_add_vision_id`

Installation:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/allanmeng/comfyui-sg-llama-cpp
```

---

## 0.3.43+ Build & Deployment Notes (oneAPI 2026 / Python XPU ≥ 2.13)

### 1. Why 0.3.43 builds with oneAPI 2026

Starting from 0.3.43, the build environment was upgraded to **Intel oneAPI Base Toolkit 2026** (corresponding to Intel Deep Learning Essentials 2026.0). Reasons:

- Intel officially recommends installing the latest oneAPI / GPU driver to ensure performance and compatibility on Intel Arc B580 / B70 (Battlemage).
- 0.3.43 must be paired with a **Python XPU runtime (`intel-xpu-backend-for-pytorch` / PyTorch XPU) ≥ 2.13** (i.e. the PyTorch 2.13 stack). oneAPI 2026 matches it at the ABI and runtime level; mixing an older Python XPU backend (e.g. 2.12 + oneAPI 2025) may cause runtime mismatch.

> **Important**: If your ComfyUI / inference environment uses the PyTorch XPU stack, make sure `intel-xpu-backend-for-pytorch` is **≥ 2.13** to stay consistent with the 0.3.43 oneAPI 2026 build.

### 2. Wheel packaging: Option A (slim build, no oneAPI runtime bundled)

Starting from 0.3.45, the published wheels use **Option A (slim)**: oneAPI runtime DLLs are **NOT bundled** (`dnnl.dll`, `mkl_core.3.dll`, `mkl_sycl_blas.6.dll`, `mkl_tbb_thread.3.dll`, `tbb12.dll` are all removed), keeping the wheel at ~36–43 MB.

> **🆕 Since 0.4.7 the exclusion list has 6 entries**: **`mkl_intel_thread.3.dll`** (38.95 MiB) is now excluded as well — the `ggml-sycl.dll` built with oneAPI 2026.2 imports it. Without the exclusion the wheel would grow from 43 MB to about 84 MB. **Like every other excluded item, this DLL is supplied by the target machine's oneAPI**, so `setvars.bat` in your launcher is not optional.

The target machine therefore **MUST have Intel oneAPI pre-installed** (the SYCL core runtime `sycl9.dll` / `OpenCL.dll` and the numeric libraries above are provided by oneAPI).

> **⚠️ Note**: `libomp140.x86_64.dll` **IS kept** in the wheel (the OpenMP preload fix depends on it) — do not delete it.

If oneAPI is not installed on the target machine, the SYCL runtime cannot load and inference will fail. Install the oneAPI Base Toolkit as described in the Prerequisites section below.

### 3. For machines that already have the oneAPI Toolkit (no manual slimming needed)

The Option A wheel contains no redundant oneAPI DLLs by design; once oneAPI is installed on the target machine, those runtimes are provided by oneAPI via `setvars.bat` or the system PATH. The wheel keeps only `libomp140.x86_64.dll` (required).

> If you are upgrading from an older version (0.3.43/0.3.44 self-contained wheels), stale oneAPI DLLs may remain in site-packages — run `pip uninstall` first, then install the new version.

### 4. PR #25880 Patch: Fix SYCL onednn fattn Long-Context Corruption

Version 0.3.43 applies a local patch from [PR #25880](https://github.com/ggml-org/llama.cpp/pull/25880) (ggml-org/llama.cpp), fixing a **use-after-return** bug in the SYCL onednn flash-attention path.

**Symptoms**: Under long contexts (n_kv ≥ ~26k, e.g. the second turn of a multi-turn conversation), the oneDNN fattn output collapses to a repeated token ("GGGGG…" pattern).

**Root cause**: The SDPA scale value is uploaded via async memcpy from a stack-local variable to a GPU device buffer. When the K/V staging kernels complete on the in-order queue before the memcpy runs, the stack frame has been recycled, and the memcpy reads garbage → the subsequent SDPA uses a wrong scale → garbled output.

**Fix**:
- Upload the scale via **synchronous memcpy** (`.wait()`), ensuring the copy completes before returning the buffer pointer
- Use a **per-device device scalar cache** (`static std::unordered_map`), uploading the scale synchronously only once and reusing the cached value on subsequent calls
- New env var `GGML_SYCL_FA_ONEDNN_MAX_KV` (default 0 = unlimited) provides an escape hatch for extremely long sequences — past the ceiling the FA falls back to the native kernel

**Difference from PR #25741**: The earlier #25741 used an unconditional `wait_and_throw()` to mask the symptom (keeping the stack frame alive long enough for the async memcpy to finish), but at the cost of ~6% PP performance per call. `#25880` fixes the root cause and has zero performance penalty on single-device setups.

---

## Prerequisites

Before installing, you must have the following:

### 1. Intel Arc GPU Driver

Download and install the latest Intel Arc GPU driver from:
https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

### 2. Intel oneAPI Base Toolkit (Required)

The SYCL runtime depends on Intel oneAPI. You do **not** need to install the full toolkit — only the following components are required:

| Component | Why needed |
|-----------|-----------|
| Intel oneAPI DPC++/C++ Compiler | Provides the SYCL compiler (icx) and `OpenCL.dll` |
| Intel oneAPI DPC++ Library | Provides `sycl9.dll` runtime (oneAPI 2026.2) |
| Intel oneAPI Math Kernel Library (oneMKL) | Provides `mkl_core.3.dll`, `mkl_sycl_blas.6.dll`, `mkl_tbb_thread.3.dll`, and **`mkl_intel_thread.3.dll` (new dependency as of 0.4.7)** |
| Intel oneAPI Deep Neural Network Library (oneDNN) | Provides `dnnl.dll` |
| Intel oneAPI Threading Building Blocks (oneTBB) | Provides `tbb12.dll` |

Download Intel oneAPI Base Toolkit (select individual components during install):
https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **Tip:** During installation, choose "Custom Installation" and select only the components listed above to save disk space. In oneAPI 2025+, **DPC++ Library** is a component separate from the Compiler and must be ticked individually.

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10/11 x64 |
| GPU | Intel Arc (Alchemist / Battlemage) |
| Driver | Intel Arc GPU driver (latest) |
| oneAPI | Required — DPC++ Compiler, oneMKL, oneDNN, oneTBB |

---

## Available Wheels

| Version | File | Size |
|---------|------|------|
| 0.4.7 | `llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl` | ~43 MB |
| 0.4.6 | `llama_cpp_python-0.4.6+sycl-cp313-cp313-win_amd64.whl` | ~43 MB |
| 0.4.5 | `llama_cpp_python-0.4.5+sycl-cp313-cp313-win_amd64.whl` | ~42 MB |
| 0.4.3 | `llama_cpp_python-0.4.3+sycl-cp313-cp313-win_amd64.whl` | ~39 MB |
| 0.4.2 | `llama_cpp_python-0.4.2+sycl-cp313-cp313-win_amd64.whl` | ~37 MB |
| 0.4.1 | `llama_cpp_python-0.4.1+sycl-cp313-cp313-win_amd64.whl` | ~37 MB |
| 0.4.0 | `llama_cpp_python-0.4.0+sycl-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.49 | `llama_cpp_python-0.3.49+sycl-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.48 | `llama_cpp_python-0.3.48+sycl-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.47 | `llama_cpp_python-0.3.47+sycl-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.46 | `llama_cpp_python-0.3.46+sycl-cp313-cp313-win_amd64.whl` | ~35 MB |
| 0.3.45 | `llama_cpp_python-0.3.45+sycl-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.44 | `llama_cpp_python-0.3.44+sycl+pr25880-cp313-cp313-win_amd64.whl` | ~36 MB |
| 0.3.43 | `llama_cpp_python-0.3.43+sycl+pr25880+oneapi2610-cp313-cp313-win_amd64.whl` | ~109 MB |
| 0.3.41 | `llama_cpp_python-0.3.41+sycl-cp313-cp313-win_amd64.whl` | ~27 MB |
| 0.3.38 | `llama_cpp_python-0.3.38+sycl-cp313-cp313-win_amd64.whl` | ~22 MB |
| 0.3.36 | `llama_cpp_python-0.3.36+sycl-cp313-cp313-win_amd64.whl` | ~20 MB |
| 0.3.35 | `llama_cpp_python-0.3.35+sycl-cp313-cp313-win_amd64.whl` | ~19 MB |
| 0.3.34 | `llama_cpp_python-0.3.34+sycl-cp313-cp313-win_amd64.whl` | ~19 MB |
| 0.3.33 | `llama_cpp_python-0.3.33+sycl-cp313-cp313-win_amd64.whl` | ~18 MB |
| 0.3.32 | `llama_cpp_python-0.3.32+sycl-cp313-cp313-win_amd64.whl` | ~18 MB |
| 0.3.31 | `llama_cpp_python-0.3.31+sycl-cp313-cp313-win_amd64.whl` | ~174 MB |
| 0.3.30 | `llama_cpp_python-0.3.30+sycl-cp313-cp313-win_amd64.whl` | ~180 MB |

Download from [Releases](https://github.com/allanmeng/llama-cpp-python-sycl-windows/releases).

---

## Installation

### Method 1: pip install (recommended)

```bat
pip uninstall llama-cpp-python -y
pip install llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl
```

Uninstalling first ensures a clean state.

### Method 2: Manual (for embedded Python environments like ComfyUI)

1. Extract the whl file (rename to `.zip` then extract)
2. Copy the `llama_cpp` folder to your `site-packages` directory:

```
your_python\Lib\site-packages\llama_cpp\
```

---

## Usage with ComfyUI

### Add oneAPI to your startup script

After installing oneAPI, add the following line to your ComfyUI launch `.bat` file **before** starting Python:

```bat
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
```

Example `start_comfyui.bat`:

```bat
@echo off
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
......
......
"C:\python\python.exe" main.py --listen 0.0.0.0
```

---

### Create a dedicated preloader plugin

> **Note (since 0.3.45)**: The wheel uses Option A (slim) and **no longer bundles** the oneAPI runtime DLLs; it still automatically registers its own `lib/` directory, and the target machine must have oneAPI pre-installed (see "Wheel packaging" above).

To enable SYCL GPU acceleration for all llama-cpp-python based nodes in ComfyUI, create a dedicated preloader plugin.

#### Step 1: Create plugin directory

```bat
mkdir "your_comfyui\custom_nodes\sycl-preloader"
```

#### Step 2: Create `__init__.py` (empty)

```bat
echo. > "your_comfyui\custom_nodes\sycl-preloader\__init__.py"
```

#### Step 3: Create `prestartup_script.py`

```python
import os
import importlib.util
from pathlib import Path

def sycl_preloader():
    if os.name != "nt":
        return
    try:
        _spec = importlib.util.find_spec('llama_cpp')
        if not _spec:
            print("[SYCL] llama_cpp package not found")
            return
        _pkg_dir = Path(_spec.origin).parent
        for _sub in ['', 'lib', 'bin']:
            _d = _pkg_dir / _sub if _sub else _pkg_dir
            if _d.exists():
                os.add_dll_directory(str(_d))
        for _p in os.environ.get("PATH", "").split(os.pathsep):
            if "Intel" in _p and os.path.exists(_p):
                os.add_dll_directory(_p)
        print("[SYCL] DLL search paths registered")
    except Exception as e:
        print(f"[SYCL] Error: {e}")

sycl_preloader()
```

#### Why prestartup_script.py?

##### The Problem

After compiling and installing the SYCL-enabled llama-cpp-python, the GPU works correctly when called directly from a Python script. However, llama-cpp-python based plugins inside ComfyUI (such as image captioning / prompt generation plugins) fail to activate SYCL and fall back to CPU.

The root cause is a **DLL loading restriction introduced in Python 3.8+** on Windows:

> For security reasons, Python 3.8+ completely ignores the `PATH` environment variable when loading DLLs. Even if `setvars.bat` has correctly set up the oneAPI paths in `PATH`, Python will not find the SYCL DLLs through that mechanism. The only reliable way is to call `os.add_dll_directory()` explicitly within Python code before the DLLs are needed.

##### Why not bat or main.py?

- **Launch `.bat` file**: Can set `PATH` and environment variables, but cannot call Python's `os.add_dll_directory()`. The DLL restriction still applies.
- **ComfyUI `main.py`**: Appears to be an option, but `main.py` begins importing ComfyUI core modules (`import comfy.options`, etc.) at the very first line. These imports can indirectly trigger plugin loading chains, meaning `llama_cpp` may already be imported before any preload code in `main.py` has a chance to run. The timing is too late and unreliable.

##### The Solution: ComfyUI's prestartup mechanism

ComfyUI has a built-in hook called `execute_prestartup_script()`. At startup, ComfyUI scans every subfolder under `custom_nodes\` and executes any file named `prestartup_script.py` it finds there. This happens **before any plugin nodes are imported**, making it the earliest reliable point to run Python code in the ComfyUI process.

The startup order is:

```
main.py basic init
    ↓
execute_prestartup_script()  ← prestartup_script.py files run here
    ↓
Load each plugin's __init__.py / nodes.py
    ↓
Start server
```

Once the SYCL DLLs are loaded via `os.add_dll_directory()` and `ctypes.CDLL()`, the effect is **process-wide**. All subsequent llama-cpp-python based plugins (ComfyUI-QwenVL, comfyui-sg-llama-cpp, etc.) will automatically find the DLLs already in memory — no per-plugin configuration needed.

##### Why a dedicated plugin folder?

Placing `prestartup_script.py` inside an existing plugin folder (e.g. comfyui-sg-llama-cpp) is fragile — if that plugin is deleted or updated, the file disappears. The safest approach is to create a minimal dedicated plugin folder containing only two files:

```
custom_nodes\sycl-preloader\
    __init__.py          (empty)
    prestartup_script.py (SYCL DLL preloader)
```

This folder has no nodes, no dependencies, and will never be touched by ComfyUI Manager's update mechanism. It serves one purpose only: ensuring the SYCL DLLs are loaded at the right moment for the entire ComfyUI process.

---

## Recommended Parameters (ComfyUI)

| Parameter | Value |
|-----------|-------|
| `n_gpu_layers` | `-1` (all layers on GPU) |
| `n_ctx` | `4096` |
| `n_threads` | `4` |
| `n_threads_batch` | `4` |
| `ctx_checkpoints` | `-1` (default; hybrid models like Qwen3.5 use default, **do not set `0`** — 0.3.48+ triggers hybrid fast-path first-decode crash) |
| `vision_image_min_tokens` | `1024` (Qwen-VL minimum requirement) |
| `vision_image_max_tokens` | `-1` (use default) |

---

## Known Limitations

- Flash Attention on SYCL0 (Intel Arc) is implemented via the **oneDNN path** (`GGML_SYCL_DNNL`, enabled by default): on B-series (B580/B70, etc.) `GGML_SYCL_ENABLE_FLASH_ATTN` / `GGML_SYCL_FA_ONEDNN` / `GGML_SYCL_ENABLE_MKL_FA` are all enabled in practice; upstream gates oneDNN features off on **A-series (Alchemist)**, where this path is unavailable. Either way, memory usage is higher than with CUDA
- Some CLIP graph operators fall back to CPU, vision encoding performance is suboptimal
- Qwen3.5-2B (Hybrid/Recurrent architecture) may cause instability, use Qwen3-2B instead

---

## Tested Environment

| Item | Version |
|------|---------|
| GPU | Intel Arc B580 Graphics (160 CUs / 12526 MB / `Reorder=Y`) |
| Driver | SYCL 20.1 / driver `1.17.39894+4` |
| OS | Windows 11 x64 |
| Python | 3.13.11 |
| oneAPI | **2026.2.0 Build 20261001** (icx, clang 23) |
| ComfyUI | 0.33.2 |

---

## Credits

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [JamePeng's SYCL fork](https://github.com/JamePeng/llama-cpp-python)
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
