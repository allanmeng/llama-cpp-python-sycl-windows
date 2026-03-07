# llama-cpp-python-sycl-windows
Pre-built llama-cpp-python wheels for Windows with Intel GPU (SYCL/oneAPI) support. Optimized for Intel Arc &amp; Data Center GPUs.

Pre-built [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) wheels with **Intel Arc GPU (SYCL)** acceleration for Windows.

Compiled from [JamePeng's fork](https://github.com/JamePeng/llama-cpp-python) which adds SYCL support for Intel Arc GPUs.

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10/11 x64 |
| GPU | Intel Arc (Alchemist / Battlemage) |
| Python | 3.13.x |
| Driver | Intel Arc GPU driver (latest recommended) |
| oneAPI | ❌ Not required (runtime DLLs are bundled) |

---

## Available Wheels

| Version | File | Size |
|---------|------|------|
| 0.3.31 | `llama_cpp_python-0.3.31+sycl-cp313-cp313-win_amd64.whl` | ~174 MB |
| 0.3.30 | `llama_cpp_python-0.3.30+sycl-cp313-cp313-win_amd64.whl` | ~180 MB |

Download from [Releases](../../releases).

---

## Installation

### Method 1: pip install (recommended)

```bat
pip install llama_cpp_python-0.3.31+sycl-cp313-cp313-win_amd64.whl
```

### Method 2: Manual (for embedded Python environments like ComfyUI)

1. Extract the whl file (rename to `.zip` then extract)
2. Copy the `llama_cpp` folder to your `site-packages` directory:

```
your_python\Lib\site-packages\llama_cpp\
```

---

## Verify SYCL is Working

Save the following as `check_sycl.py` and run it:

```python
import ctypes, os

# Add oneAPI DLL search paths if installed, otherwise bundled DLLs will be used
llama_dir = r'your_python\Lib\site-packages\llama_cpp'
os.add_dll_directory(llama_dir)

for dll in ['ggml-base.dll', 'dnnl.dll', 'sycl8.dll', 'mkl_sycl_blas.5.dll', 'ggml-sycl.dll']:
    try:
        ctypes.CDLL(os.path.join(llama_dir, dll))
        print(f'OK {dll}')
    except Exception as e:
        print(f'FAIL {dll}: {e}')

from llama_cpp.llama_chat_format import Qwen25VLChatHandler, Qwen3VLChatHandler
print('handlers OK')
```

Expected output:
```
OK ggml-base.dll
OK dnnl.dll
OK sycl8.dll
OK mkl_sycl_blas.5.dll
OK ggml-sycl.dll
handlers OK
```

---

## Usage with ComfyUI

To enable SYCL GPU acceleration for all llama-cpp-python based nodes in ComfyUI, create a dedicated preloader plugin.

### Step 1: Create plugin directory

```bat
mkdir "your_comfyui\custom_nodes\sycl-preloader"
```

### Step 2: Create `__init__.py` (empty)

```bat
echo. > "your_comfyui\custom_nodes\sycl-preloader\__init__.py"
```

### Step 3: Create `prestartup_script.py`

```python
import os
import ctypes
import importlib.util

if os.name == "nt":
    try:
        # Add oneAPI DLL search paths if installed
        for d in [
            r"C:\Program Files (x86)\Intel\oneAPI\compiler\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\mkl\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\dnnl\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\tbb\latest\bin\intel64\vc_mt",
        ]:
            if os.path.exists(d):
                os.add_dll_directory(d)

        # Load SYCL DLLs from llama_cpp directory
        _spec = importlib.util.find_spec('llama_cpp')
        _llama_dir = os.path.dirname(_spec.origin) if _spec else None
        if _llama_dir and os.path.exists(_llama_dir):
            os.add_dll_directory(_llama_dir)
            for _dll in ['ggml-base.dll', 'dnnl.dll', 'sycl8.dll',
                         'mkl_sycl_blas.5.dll', 'ggml-sycl.dll']:
                _dll_path = os.path.join(_llama_dir, _dll)
                if os.path.exists(_dll_path):
                    ctypes.CDLL(_dll_path)
                    print(f"[SYCL] OK {_dll}")
    except Exception as e:
        print(f"[SYCL] Error: {e}")
```

### Why prestartup_script.py?

Python 3.8+ on Windows ignores `PATH` when loading DLLs for security reasons.
`os.add_dll_directory()` must be called explicitly before `llama_cpp` is imported.
ComfyUI's `prestartup_script.py` mechanism runs before any plugin nodes are imported,
making it the only reliable place to preload SYCL DLLs.

The preload effect is **process-wide**, so all llama-cpp-python based plugins
(ComfyUI-QwenVL, comfyui-sg-llama-cpp, etc.) will automatically benefit from SYCL acceleration.

---

## Recommended Parameters (ComfyUI)

| Parameter | Value |
|-----------|-------|
| `n_gpu_layers` | `-1` (all layers on GPU) |
| `n_ctx` | `4096` |
| `n_threads` | `4` |
| `n_threads_batch` | `4` |
| `vision_image_min_tokens` | `-1` |
| `vision_image_max_tokens` | `-1` |

---

## Known Limitations

- Flash Attention is not supported by SYCL0 (Intel Arc), memory usage will be higher than CUDA
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
| oneAPI | 2025.3.2 |
| ComfyUI | 0.16.3 |

---

## Credits

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [JamePeng's SYCL fork](https://github.com/JamePeng/llama-cpp-python)
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
