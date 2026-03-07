[English](README.md) | [中文](README_zh.md)

# llama-cpp-python-sycl-windows

为 Windows 平台预编译的 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) 安装包，支持 **Intel Arc GPU (SYCL)** 加速。

基于 [JamePeng 的 SYCL 分支](https://github.com/JamePeng/llama-cpp-python) 编译，为 Intel Arc GPU 提供 SYCL 加速支持。

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 x64 |
| 显卡 | Intel Arc（炼金师 / 战法师架构） |
| Python | 3.13.x |
| 驱动 | Intel Arc 显卡驱动（建议使用最新版） |
| oneAPI | ❌ 无需安装（运行时 DLL 已内置） |

---

## 可用安装包

| 版本 | 文件 | 大小 |
|------|------|------|
| 0.3.31 | `llama_cpp_python-0.3.31+sycl-cp313-cp313-win_amd64.whl` | ~174 MB |
| 0.3.30 | `llama_cpp_python-0.3.30+sycl-cp313-cp313-win_amd64.whl` | ~180 MB |

从 [Releases](../../releases) 页面下载。

---

## 安装方法

### 方法一：pip 安装（推荐）

```bat
pip install llama_cpp_python-0.3.31+sycl-cp313-cp313-win_amd64.whl
```

### 方法二：手动安装（适用于 ComfyUI 等嵌入式 Python 环境）

1. 将 whl 文件重命名为 `.zip` 后解压
2. 将 `llama_cpp` 文件夹复制到 `site-packages` 目录：

```
your_python\Lib\site-packages\llama_cpp\
```

---

## 验证 SYCL 是否正常工作

将以下内容保存为 `check_sycl.py` 并运行：

```python
import ctypes, os

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

预期输出：
```
OK ggml-base.dll
OK dnnl.dll
OK sycl8.dll
OK mkl_sycl_blas.5.dll
OK ggml-sycl.dll
handlers OK
```

---

## 在 ComfyUI 中使用

为所有基于 llama-cpp-python 的 ComfyUI 节点启用 SYCL GPU 加速，需要创建一个专用的预加载插件。

### 第一步：创建插件目录

```bat
mkdir "your_comfyui\custom_nodes\sycl-preloader"
```

### 第二步：创建空的 `__init__.py`

```bat
echo. > "your_comfyui\custom_nodes\sycl-preloader\__init__.py"
```

### 第三步：创建 `prestartup_script.py`

```python
import os
import ctypes
import importlib.util

if os.name == "nt":
    try:
        # 如果安装了 oneAPI，添加其 DLL 搜索路径
        for d in [
            r"C:\Program Files (x86)\Intel\oneAPI\compiler\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\mkl\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\dnnl\latest\bin",
            r"C:\Program Files (x86)\Intel\oneAPI\tbb\latest\bin\intel64\vc_mt",
        ]:
            if os.path.exists(d):
                os.add_dll_directory(d)

        # 从 llama_cpp 目录加载 SYCL DLL
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

### 为什么使用 prestartup_script.py？

Python 3.8+ 在 Windows 上出于安全考虑，加载 DLL 时完全忽略 `PATH` 环境变量，必须通过 `os.add_dll_directory()` 显式指定路径。

ComfyUI 的 `prestartup_script.py` 机制在所有插件节点被 import 之前执行，是唯一能在 `llama_cpp` 加载前运行 Python 代码的可靠时机。

预加载效果是**进程级别**的，所有基于 llama-cpp-python 的插件（ComfyUI-QwenVL、comfyui-sg-llama-cpp 等）都会自动受益于 SYCL 加速，无需每个插件单独配置。

---

## ComfyUI 推荐参数

| 参数 | 推荐值 |
|------|--------|
| `n_gpu_layers` | `-1`（所有层卸载到 GPU） |
| `n_ctx` | `4096` |
| `n_threads` | `4` |
| `n_threads_batch` | `4` |
| `vision_image_min_tokens` | `-1` |
| `vision_image_max_tokens` | `-1` |

---

## 已知限制

- Intel Arc（SYCL0）不支持 Flash Attention，显存占用会高于 CUDA 方案
- 部分 CLIP 图计算算子会回退到 CPU，视觉编码性能受限
- Qwen3.5-2B（混合/循环架构）可能导致不稳定，建议改用 Qwen3-2B

---

## 测试环境

| 项目 | 版本 |
|------|------|
| 显卡 | Intel Arc B580（战法师架构） |
| 驱动 | 最新版 |
| 操作系统 | Windows 11 x64 |
| Python | 3.13.11 |
| oneAPI | 2025.3.2 |
| ComfyUI | 0.16.3 |

---

## 致谢

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [JamePeng 的 SYCL 分支](https://github.com/JamePeng/llama-cpp-python)
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
