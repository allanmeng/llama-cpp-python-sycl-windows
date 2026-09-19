[English](README_EN.md) | [中文](README.md)

# llama-cpp-python-sycl-windows

Pre-built [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) wheels with **Intel Arc GPU (SYCL)** acceleration for Windows.

Compiled from [JamePeng's fork](https://github.com/JamePeng/llama-cpp-python) which adds SYCL support for Intel Arc GPUs.

---

## Latest Release Notes (v0.4.0+sycl · 2026-09-19)

**Key highlights: MTMD text-to-speech (TTS) + grammar improvements and speedups + runtime state reliability**

- Upgraded to llama-cpp-python **0.4.0** (based on JamePeng release commit `5c83af7`, llama.cpp `60081bb` = b11046, **335 submodule commits**, zero local patches)
- **MTMD text-to-speech (TTS)**: new `MTMDAudioGenerator` (with a new `MTMDBaseHandler` base class) supporting **Qwen3-TTS** and **Pocket TTS**; speaker reference audio plus model-specific language and sampling options; ships a CLI TTS demo and a Streamlit playground
- **Grammar improvements**: `LlamaGrammar` now supports custom start rules and lazy triggers; JSON Schema conversion fixes (reference resolution, empty schemas, integer bounds, tool-parameter handling); conversion up to **16.2x faster** (200 optional properties 21.689 → 1.339 ms)
- **Runtime state reliability**: `LlamaState` snapshots now carry token/score/logits data and validate model/context compatibility; hybrid checkpoint lifetime aligned with native state changes; `Llama.abort()` wired to native cancellation (returns `finish_reason="abort"`)
- **SYCL backend gains** (335 llama.cpp commits): TOP_K now uses radix select (**supports k>32**), `rms_norm+mul+add` and residual-chain fusion, `ssm_conv` SiLU epilogue fusion, Q4_K multi-column MMVQ deduplication, oneDNN scratchpad pool-free ordering fix

**⚠️ Known integration note (carried over from 0.3.48 / 0.3.49): hybrid vision model + `ctx_checkpoints=0` first-decode crash**

- Symptom: hybrid vision models with SWA layers (e.g. Qwen3.5), on large images (~4000+ vision tokens), prefill succeeds but **first decode token crashes** (`failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`)
- Root cause: caller passing `ctx_checkpoints=0` forces the hybrid model down a "Bypassing rollback" fast-path that has no slot headroom for the first decode token on large prefills. Verified against the source: this fast-path **still exists** in 0.4.0
- Workaround: use default `ctx_checkpoints=-1` (enables checkpoint cache, avoids the broken branch)
- **✅ Official recommended plugin fixed**: [comfyui-sg-llama-cpp](https://github.com/allanmeng/comfyui-sg-llama-cpp) changed the default to `-1` in `1f0fc15` with a reactive `n_ctx` hint; large-image vision inference now works normally. No manual handling needed when using this plugin
- **This wheel has no such bug**: pure `llama_cpp.Llama` on the same model + large image at `n_ctx=8192` verified working (double-checked)

**🚀 Measured performance on B580 (Qwen3.5-4B vision model + images, 0.4.0):**

| Metric | Small image 1088×1440 | Large image 2336×1760 |
|--------|-----------------------|-----------------------|
| Vision tokens | 1530 | 4015 |
| Image encode time | 1771 ms (clip_encode) | 25899 ms (clip_encode) |
| Image decode time | 759 ms (batch 1/1) | 3627 ms (batch 1/2) + 2850 ms (batch 2/2) |
| Prompt eval | **1194.33 t/s** (1304.50 ms / 1558 tokens) | **57.70 t/s** (70067.12 ms / 4043 tokens) |
| Generation speed | **86.27 t/s** (eval 18197.69 ms / 1570 runs) | **46.37 t/s** (eval 30798.45 ms / 1428 runs) |
| Total time | 30.05 s | 143.40 s |
| Hybrid checkpoint | 2 host checkpoints (50.25 MiB each), rollback hit 73 prefix | 2 host checkpoints (50.25 MiB each), rollback hit 101 prefix |
| SYCL compute buffer | SYCL0 495.00 MiB / SYCL_Host 18.02 MiB | same as left |

> Test scene: Qwen3.5-4B-Uncensored + mmproj-BF16, hybrid architecture (with SWA layers), `ctx_checkpoints=-1`, `n_ctx=8192`. Versus the equivalent 0.3.49 measurements: small-image generation 84.88 → **86.27 t/s**, prompt eval 1173.60 → **1194.33 t/s**; large-image generation 44.61 → **46.37 t/s**, prompt eval 54.91 → **57.70 t/s**. No regression in either scene, with a modest gain on both. Vision inference normal, no first-decode crash.

**Community feedback:**

> ✅ **"Qwen 3.8 27B working fine with `llama_multimodal.GenericMTMDChatHandler`"** — vision model compatibility confirmed
> See: https://github.com/JamePeng/llama-cpp-python/discussions/169#discussioncomment-18036209

**Wheel**: `llama_cpp_python-0.4.0+sycl-cp313-cp313-win_amd64.whl` (~36 MB, slim build, requires oneAPI 2026.1)

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
pip install llama_cpp_python-0.4.0+sycl-cp313-cp313-win_amd64.whl
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

- Intel officially recommends installing the latest oneAPI / GPU driver to ensure performance and compatibility on Intel Arc B580 (Battlemage).
- 0.3.43 must be paired with a **Python XPU runtime (`intel-xpu-backend-for-pytorch` / PyTorch XPU) ≥ 2.13** (i.e. the PyTorch 2.13 stack). oneAPI 2026 matches it at the ABI and runtime level; mixing an older Python XPU backend (e.g. 2.12 + oneAPI 2025) may cause runtime mismatch.

> **Important**: If your ComfyUI / inference environment uses the PyTorch XPU stack, make sure `intel-xpu-backend-for-pytorch` is **≥ 2.13** to stay consistent with the 0.3.43 oneAPI 2026 build.

### 2. Wheel packaging: Option A (slim build, no oneAPI runtime bundled)

Starting from 0.3.45, the published wheels use **Option A (slim)**: oneAPI runtime DLLs are **NOT bundled** (`dnnl.dll`, `mkl_core.3.dll`, `mkl_sycl_blas.6.dll`, `mkl_tbb_thread.3.dll`, `tbb12.dll` are all removed), keeping the wheel at ~36 MB. The target machine therefore **MUST have Intel oneAPI pre-installed** (the SYCL core runtime `sycl9.dll` / `OpenCL.dll` and the numeric libraries above are provided by oneAPI).

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
| Intel oneAPI DPC++ Library | Provides `sycl9.dll` runtime (oneAPI 2026.1) |
| Intel oneAPI Math Kernel Library (oneMKL) | Provides MKL SYCL runtime |
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
pip install llama_cpp_python-0.4.0+sycl-cp313-cp313-win_amd64.whl
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
| GPU | Intel Arc B580 (Battlemage) |
| Driver | Latest |
| OS | Windows 11 x64 |
| Python | 3.13.11 |
| oneAPI | 2026.1 |
| ComfyUI | 0.16.3 |

---

## Credits

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [JamePeng's SYCL fork](https://github.com/JamePeng/llama-cpp-python)
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
