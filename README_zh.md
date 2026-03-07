[English](README.md) | [📖 中文文档点这里](README_zh.md)

# llama-cpp-python-sycl-windows

为 Windows 平台预编译的 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) 安装包，支持 **Intel Arc GPU (SYCL)** 加速。

基于 [JamePeng 的 SYCL 分支](https://github.com/JamePeng/llama-cpp-python) 编译，为 Intel Arc GPU 提供 SYCL 加速支持。

---

## ⚠️ 前置要求

安装前，请确保已完成以下步骤：

### 1. Intel Arc 显卡驱动
从以下地址下载并安装最新的 Intel Arc 显卡驱动：
👉 https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

### 2. Intel oneAPI Base Toolkit（必须安装）
SYCL 运行时依赖 Intel oneAPI，但**无需安装完整工具包**，只需安装以下组件：

| 组件 | 用途 |
|------|------|
| Intel oneAPI DPC++/C++ Compiler | 提供 `sycl8.dll`、`OpenCL.dll` 运行时 |
| Intel oneAPI Math Kernel Library (oneMKL) | 提供 MKL SYCL 运行时 |
| Intel oneAPI Deep Neural Network Library (oneDNN) | 提供 `dnnl.dll` |
| Intel oneAPI Threading Building Blocks (oneTBB) | 提供 `tbb12.dll` |

下载 Intel oneAPI Base Toolkit（安装时选择自定义安装）：
👉 https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **提示：** 安装时选择「自定义安装」，只勾选上表中的 4 个组件，可节省大量磁盘空间。

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 x64 |
| 显卡 | Intel Arc（炼金师 / 战法师架构） |
| 驱动 | Intel Arc 显卡驱动（最新版） |
| oneAPI | ✅ 必须安装 — DPC++ Compiler、oneMKL、oneDNN、oneTBB |

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

## 在 ComfyUI 中使用

### 在启动脚本中加载 oneAPI 环境

安装完 oneAPI 后，在 ComfyUI 的启动 `.bat` 文件里，**Python 启动之前**加入以下一行：

```bat
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
```

启动脚本示例 `start_comfyui.bat`：
```bat
@echo off
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
......
......
"C:\python\python.exe" main.py --listen 0.0.0.0
```
-----

### 创建专用的预加载插件
为所有基于 llama-cpp-python 的 ComfyUI 节点启用 SYCL GPU 加速，需要创建一个专用的预加载插件。

#### 第一步：创建插件目录

```bat
mkdir "your_comfyui\custom_nodes\sycl-preloader"
```

#### 第二步：创建空的 `__init__.py`

```bat
echo. > "your_comfyui\custom_nodes\sycl-preloader\__init__.py"
```

#### 第三步：创建 `prestartup_script.py`

```python
import os
import ctypes
import importlib.util

if os.name == "nt":
    try:
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

#### 为什么使用 prestartup_script.py？

##### 问题背景

编译并安装 SYCL 版本的 llama-cpp-python 之后，直接用 Python 脚本调用时 GPU 可以正常工作。但是，ComfyUI 里基于 llama-cpp-python 的插件（例如提示词反推插件）却无法激活 SYCL，只能回退到 CPU 运行。

根本原因是 **Python 3.8+ 在 Windows 上引入的 DLL 加载限制**：

> 出于安全考虑，Python 3.8+ 在加载 DLL 时完全忽略 `PATH` 环境变量。即使 `setvars.bat` 已经正确地把 oneAPI 路径写入了 `PATH`，Python 也不会通过这个机制找到 SYCL DLL。唯一可靠的方式是在 Python 代码里显式调用 `os.add_dll_directory()`，在需要 DLL 之前提前注册搜索路径。

##### 为什么 bat 启动文件和 main.py 都不行？

- **启动 `.bat` 文件**：可以设置 `PATH` 和环境变量，但无法调用 Python 的 `os.add_dll_directory()`，DLL 加载限制依然存在。
- **ComfyUI 的 `main.py`**：看起来是个选项，但 `main.py` 第一行就开始导入 ComfyUI 核心模块（`import comfy.options` 等），这些 import 会间接触发插件加载链，导致 `llama_cpp` 可能在预加载代码执行之前就已经被导入了。时机太晚，不可靠。

##### 解决方案：利用 ComfyUI 的 prestartup 机制

ComfyUI 内置了一个钩子函数 `execute_prestartup_script()`。启动时，ComfyUI 会扫描 `custom_nodes\` 下每一个子文件夹，找到并执行其中名为 `prestartup_script.py` 的文件。这个过程发生在**所有插件节点被导入之前**，是整个 ComfyUI 进程中最早能可靠运行 Python 代码的时机。

启动顺序如下：
```
main.py 基础初始化
    ↓
execute_prestartup_script()  ← prestartup_script.py 在这里执行
    ↓
加载各插件的 __init__.py / nodes.py
    ↓
启动服务器
```

通过 `os.add_dll_directory()` 和 `ctypes.CDLL()` 加载 SYCL DLL 之后，效果是**进程级别**的。后续所有基于 llama-cpp-python 的插件（ComfyUI-QwenVL、comfyui-sg-llama-cpp 等）都能自动找到已经在内存中的 DLL，无需每个插件单独配置。

##### 为什么要建一个专用的插件文件夹？

如果把 `prestartup_script.py` 放在某个现有插件的文件夹里（例如 comfyui-sg-llama-cpp），风险很高——一旦那个插件被删除或更新，这个文件就消失了。最稳妥的做法是创建一个只包含两个文件的最小专用插件目录：

```
custom_nodes\sycl-preloader\
    __init__.py          （空文件）
    prestartup_script.py （SYCL DLL 预加载器）
```

这个文件夹没有节点、没有依赖，永远不会被 ComfyUI Manager 的更新机制修改。它只有一个职责：在正确的时机为整个 ComfyUI 进程完成 SYCL DLL 的预加载。

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
