# llama-cpp-python-sycl-windows Build Guide

> **Last updated**: 2026-08-09

## Chapter 1: Overview

### What is this

This document records the complete process, pitfalls, and notes for **manually building the SYCL backend of llama-cpp-python on Windows**.

The default PyPI version of llama-cpp-python does not include SYCL support; you need to build it yourself to let your Intel Arc GPU accelerate LLM inference. The prebuilt wheels in this repository are produced by the exact same process.

### Why use it

- If you don't want to use the prebuilt wheel and prefer to build a customized version yourself
- If you hit wheel version incompatibilities (Python version, llama.cpp version, etc.)
- If you want to understand the meaning and impact of each SYCL build option
- If you need to troubleshoot build or runtime issues

### Who is it for

- Intel Arc GPU users (Arc A-series / B-series)
- ComfyUI / LM Studio / other llama.cpp downstream users on Windows
- Users with some hands-on experience building llama-cpp-python with SYCL who want a reference document

---

## Chapter 2: Environment Preparation

Before building, make sure the following steps are complete:

### 2.1 Intel Arc GPU Driver

Download and install the latest Intel Arc GPU driver:
👉 https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

### 2.2 Intel oneAPI Base Toolkit (oneAPI 2026.1 recommended)

The SYCL runtime depends on Intel oneAPI, but you don't need the full toolkit — only the following components:

| Component | Purpose |
|-----------|---------|
| Intel® oneAPI DPC++/C++ Compiler | Provides the SYCL compiler (icx) |
| Intel® oneAPI DPC++ Library | Provides the sycl9.dll runtime (2026.1) |
| Intel oneAPI Math Kernel Library (oneMKL) | Provides the MKL SYCL runtime |
| Intel oneAPI Deep Neural Network Library (oneDNN) | Provides dnnl.dll |
| Intel oneAPI Threading Building Blocks (oneTBB) | Provides tbb12.dll |

Download Intel oneAPI Base Toolkit (choose "Custom Installation" during setup):
👉 https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **Tips:**
> - During installation, choose "Custom Installation" and select only the components listed above to save a lot of disk space
> - In oneAPI 2025+, the **DPC++ Library** is a separate component from the Compiler and must be checked individually

**Why oneAPI 2026.1 is recommended?**

- **Better Arc B-series (Battlemage) support**: This repository targets B-series GPUs such as the Intel Arc B580. Battlemage is a new architecture that requires a newer oneAPI for full SYCL kernel support and performance tuning; older versions (e.g., 2024.x) have incomplete B-series support.
- **Annual alignment with PyTorch XPU 2.13**: oneAPI 2026 ↔ Intel Deep Learning Essentials 2026.0 ↔ PyTorch XPU 2.13 is the official yearly pairing with aligned ABI. Mismatched oneAPI and PyTorch XPU versions can cause runtime incompatibilities.
- **Intel official recommendation**: Intel recommends using the latest oneAPI and drivers for best performance and compatibility.

> ⚠️ **Note**: The prebuilt wheels in this repository (0.3.43 and later) are compiled with oneAPI 2026.1; the target machine must also have oneAPI 2026.1 installed (aligned with the build version). If you only need **pure captioning/inference** (no PyTorch XPU image generation), there is no hard Python version constraint; but if you also use PyTorch XPU for image generation, ensure PyTorch XPU ≥ 2.13.

### 2.3 Visual Studio Build Tools (Required)

Building llama-cpp-python requires the MSVC compiler and Windows SDK.

**Download**: 👉 https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

**Select the following workloads during installation:**

| Workload | Description |
|----------|-------------|
| Desktop development with C++ | Includes MSVC compiler, Windows SDK, CMake support |
| C++ CMake tools for Windows | Provides Ninja and other build tools |

**Tips:**
- The full Visual Studio IDE is not required; the **Build Tools** edition is sufficient
- After installation, note the install path — you'll need it later (e.g., `D:\Microsoft Visual Studio\2022\BuildTools`)
- Make sure the installed **Windows SDK version** is compatible with your OS version (the installer picks a matching version by default)

### 2.4 CMake (Required)

CMake configures the build system for the llama-cpp-python build process.

**Download**: 👉 https://cmake.org/download/

**Requirements:**
- Version >= 3.22 (latest stable recommended)
- Check **Add CMake to system PATH** during installation, or manually add CMake's `bin` directory to your environment variables

**Verify installation:**

```cmd
cmake --version
```

Expected output similar to:

```
cmake version 4.2.0
```

---

## Chapter 3: Build Steps

### 3.1 Verify tools are ready

Open cmd and run:

```cmd
git --version
cmake --version
ninja --version
```

Continue only if all print version numbers.

### 3.2 Verify Python version

```cmd
F:\ComfyUI-aki-v3\python\python.exe -V
```

Confirm the output is `Python 3.13.x`.

### 3.3 Pin scikit-build-core

Newer scikit-build-core versions have a known bug in this environment; pin to 0.10.7:

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip install scikit-build-core==0.10.7
```

### 3.4 Get the source code (choose one)

**Method A: Update existing source**

```cmd
cd D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
git fetch
git reset --hard origin/main
git submodule update --init --recursive
```

> ⚠️ Use your actual source path (this repo's test environment uses `D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python`). After `git reset --hard`, run `git status` to confirm the working tree actually has files — `submodule update` sometimes only updates the index/HEAD without writing files to disk (many files show as "deleted"). In that case, `cd vendor\llama.cpp` and run `git reset --hard HEAD` to restore them.

**Method B: Fresh clone**

```cmd
git clone https://github.com/JamePeng/llama-cpp-python D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
cd D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
git submodule update --init --recursive
```

`submodule update` downloads the underlying llama.cpp source and takes a few minutes; please be patient.

### 3.5 Clean old site-packages

```cmd
rd /s /q "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp"
rd /s /q "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp_python-0.3.32.dist-info"
```

⚠️ Change the version number on the second line to the currently installed version.

### 3.6 Set up the build environment

```cmd
set VS2022INSTALLDIR=D:\Microsoft Visual Studio\2022\BuildTools
"F:\Intel-oneAPI\setvars.bat" --force
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=on -DGGML_ONEDNN=off -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_TARGET=INTEL -Wno-dev
```

> `-DGGML_ONEDNN=off` only disables oneDNN optimization for the generic CPU backend (see 5.2); it does not affect the SYCL backend's oneDNN flash-attention (enabled by default).

### 3.7 Build and install

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

### 3.8 Verify the installation

**Verify the version number:**

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip show llama_cpp_python
```

> ⚠️ Use `pip show` instead of `import llama_cpp` to print the version: in a bare CLI, `import llama_cpp` may fail with `Failed to load 'ggml-base'` (misleading) because the SYCL runtime DLLs are not loaded. `pip show` reads package metadata directly and is unaffected by DLL loading.

**Verify the vision modules (JamePeng fork specific):**

```cmd
F:\ComfyUI-aki-v3\python\python.exe -c "from llama_cpp.llama_chat_format import Qwen3VLChatHandler, Qwen25VLChatHandler; print('handlers OK')"
```

Installation succeeded when both commands output normally.

> **Note: Why verify QwenVL?**
> - The llama-cpp-python source built by the author comes from the JamePeng fork
> - This fork includes vision-specific handlers: `Qwen3VLChatHandler` and `Qwen25VLChatHandler`
> - llama-cpp-python from other sources does not have these two classes
> - These classes are the foundation for ComfyUI loading Qwen-series models for image/video captioning

### 3.9 Remove oneAPI runtime DLLs (optional)

First confirm the file names:

```cmd
dir "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\"
```

Then delete the Intel runtimes (mkl/dnnl/tbb), keeping the build artifacts (ggml/llama/mtmd) and `libomp140.x86_64.dll` (required by the OpenMP preload fix — **do NOT delete**):

```cmd
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\dnnl.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_core.3.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_sycl_blas.6.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_tbb_thread.3.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\tbb12.dll"
```

⚠️ File names may change after oneAPI upgrades (e.g., `mkl_core.2` → `mkl_core.3`); always use the actual `dir` output.

> **Note**: After deletion, the DLLs are provided by the installed oneAPI, so you **must run inside a process where the oneAPI environment (setvars.bat) is loaded**; otherwise you will get `Failed to load 'ggml-base'`.

### 3.10 Verify normal operation

Start ComfyUI / Python and run an inference; confirm the log output:

- `using device SYCL0` ✅
- `clip_ctx: CLIP using SYCL0 backend` ✅
- Normal token speed (~70 t/s measured on Qwen3-VL vision model; higher for pure text) ✅

---

## Chapter 4: Enabling SYCL in ComfyUI

### 4.1 Load the oneAPI environment in the startup script

After installing oneAPI, add the following line to ComfyUI's startup `.bat` file, before Python starts:

```bat
call "F:\Intel-oneAPI\setvars.bat" --force
```

> ⚠️ The actual path of `setvars.bat` depends on where you installed oneAPI (e.g., `C:\Program Files\Intel\oneAPI\setvars.bat`); if unsure, search with `dir /s setvars.bat`.

**Example startup script `start_comfyui.bat`:**

```bat
@echo off
call "F:\Intel-oneAPI\setvars.bat" --force
......
......
"F:\ComfyUI-aki-v3\python\python.exe" main.py --listen 0.0.0.0
```

> **Note**: Since 0.3.42, `llama_cpp` automatically registers the package's `lib/` and `bin/` directories in the DLL search path at import time, so **creating a `sycl-preloader` plugin is no longer needed** (sections 4.2–4.4 of older versions of this document have been removed). As long as the oneAPI environment is loaded in the startup script, llama-cpp-python-based plugins (e.g., comfyui-sg-llama-cpp) will use SYCL GPU acceleration normally.

---

## Chapter 5: Known Issues and Notes

### 5.1 scikit-build-core version pinning

The build environment needs `scikit-build-core` pinned to **0.10.7**; newer versions have compatibility issues in this environment:

```cmd
pip install scikit-build-core==0.10.7
```

Without pinning, CMake configuration failures or abnormal wheel builds may occur.

### 5.2 GGML_ONEDNN parameter notes

The build sets `-DGGML_ONEDNN=off`; explanation:

- `GGML_ONEDNN` controls **oneDNN optimization for the generic CPU backend** (only affects pure-CPU inference), unrelated to the SYCL backend
- **The SYCL backend's oneDNN flash-attention** is controlled by a separate option `GGML_SYCL_DNN` (enabled by default); if oneAPI's oneDNN is found at build time, `GGML_SYCL_DNNL` is enabled automatically — this is the optimal performance path for SYCL inference
- Therefore, do **not** change `GGML_ONEDNN` to "enable onednn" — it has no effect on SYCL inference; keep it `off`

### 5.3 Build generator selection

**Ninja** is recommended:

```cmd
set CMAKE_GENERATOR=Ninja
```

Ninja builds much faster than MSBuild, especially for incremental builds. If Ninja is not installed, add the "C++ CMake tools for Windows" component via the Visual Studio Installer, or download it separately.

If Ninja is unavailable, CMake falls back to MSBuild and build time increases significantly.

### 5.4 oneAPI version compatibility

Different Intel oneAPI versions have different SYCL backend support. If you hit build failures or runtime errors, consider:

- Use **oneAPI 2026.1 or later** (all prebuilt wheels from 0.3.43 onward are compiled with oneAPI 2026.1; the runtime must align with the build version; older versions may lack some SYCL kernel support and have incomplete B-series GPU support)
- After oneAPI upgrades, runtime DLL file names in `lib/` may change (e.g., `mkl_core.2.dll` → `mkl_core.3.dll`, `sycl8.dll` → `sycl9.dll`); always check with `dir` before deleting runtime DLLs
- `setvars.bat` paths may differ between oneAPI major versions; always use your actual install path (this repo's test environment uses `F:\Intel-oneAPI\setvars.bat`):

| oneAPI version | Common path |
|----------------|-------------|
| 2025+ (tested in this repo) | `F:\Intel-oneAPI\setvars.bat` (custom install path) |
| 2024+ (default install) | `C:\Program Files\Intel\oneAPI\setvars.bat` |
| Older versions | `C:\Program Files (x86)\Intel\oneAPI\setvars.bat` |

### 5.5 Quick way to verify a successful build

After building, run the following in cmd (requires the `setvars.bat` environment first):

```cmd
F:\ComfyUI-aki-v3\python\python.exe -c "import llama_cpp; print(llama_cpp.__version__)"
```

If it prints the version without DLL load errors, the build succeeded.

To confirm the SYCL backend works, run an inference and check the log for:

```
using device SYCL0 (Intel(R) Arc(TM) B580 Graphics)
clip_ctx: CLIP using SYCL0 backend
```

### 5.6 Building the pure CPU version

If you don't need SYCL GPU acceleration (e.g., for testing or comparison), build the pure CPU version:

```cmd
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=off -Wno-dev
pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

The pure CPU version needs no oneAPI and no `setvars.bat`, but inference is 5–10× slower.

### 5.7 Building the Vulkan version

If the SYCL backend has compatibility issues, consider the Vulkan backend instead. Intel Arc GPUs have good Vulkan support, and llama.cpp's Vulkan backend is more actively maintained.

**Requirements:**

- Install the **Vulkan SDK**: 👉 https://vulkan.lunarg.com/sdk/home
- Make sure the **Vulkan SDK components** are checked during installation (default is fine)
- **Visual Studio Build Tools** required (same as SYCL, see Chapter 2)

**Build commands:**

```cmd
set VS2022INSTALLDIR=D:\Microsoft Visual Studio\2022\BuildTools
call "D:\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=on -Wno-dev
pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

**Notes:**

- Vulkan builds **don't need oneAPI**, a lighter environment
- Build artifacts do not depend on Intel runtime DLLs (no runtime-file deletion step)
- Performance-wise, Vulkan is about **90–95% of SYCL** on Intel Arc; the difference is not noticeable in most scenarios
- If a CUDA backend is also installed, force it off with `-DGGML_CUDA=off`

**Verify operation:**

Start ComfyUI and check the log to confirm the Vulkan backend is active:

```
using device Vulkan0 (Intel(R) Arc(TM) B580 Graphics)
```

---

## Known Limitations

- **Flash Attention on Intel Arc (SYCL0) depends on oneDNN**: FA on the SYCL backend is implemented via the oneDNN flash-attention path (`GGML_SYCL_DNNL`, enabled by default). This path previously had a multi-turn dialog garbling issue (llama.cpp PR #25741 / #25880), natively fixed upstream since 0.3.45.
- **Some CLIP graph compute ops fall back to CPU**, limiting vision-encoding performance
- **Qwen3.5-2B (hybrid/recurrent architecture) may be unstable**; consider Qwen3-2B instead

---

## Test Environment

| Item | Version |
|------|---------|
| GPU | Intel Arc B580 (Battlemage) |
| Driver | Latest |
| OS | Windows 11 x64 |
| Python | 3.13.11 |
| oneAPI | 2026.1 |
| llama-cpp-python | 0.3.46+sycl |
| ComfyUI | 0.16.3 |

---

## Related Projects

- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [llama-cpp-python](https://github.com/JamePeng/llama-cpp-python) by JamePeng
- [llama-cpp-python-sycl-windows](https://github.com/allanmeng/llama-cpp-python-sycl-windows) by allanmeng
