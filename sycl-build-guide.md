# llama-cpp-python-sycl-windows 编译指南

## 第一章：概述

### 这是什么

本文档记录了在 **Windows 环境下手动编译 llama-cpp-python SYCL 后端** 的完整流程、踩坑记录和注意事项。

llama-cpp-python 默认的 PyPI 版本不包含 SYCL 支持，需要自行编译才能让 Intel Arc 显卡参与 LLM 推理加速。这个仓库提供的预编译 wheel 也是基于同样的流程产出的。

### 有什么用

- 如果你不想用预编译 wheel，想自己编译定制版本
- 如果你遇到 wheel 版本不兼容（Python 版本、llama.cpp 版本等）
- 如果你想了解 SYCL 编译各参数的含义和影响
- 如果你想排查编译或运行时遇到的问题

### 给谁用

- Intel Arc 显卡用户（Arc A 系列 / B 系列）
- Windows 环境下的 ComfyUI / LM Studio / 其他 llama.cpp 下游用户
- 对 llama-cpp-python SYCL 编译有一定动手能力，但需要一份参考文档的用户

---

## 第二章：环境准备

编译前，请确保已完成以下步骤：

### 2.1 Intel Arc 显卡驱动

从以下地址下载并安装最新的 Intel Arc 显卡驱动：
👉 https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

### 2.2 Intel oneAPI Base Toolkit（必须安装）

SYCL 运行时依赖 Intel oneAPI，但无需安装完整工具包，只需安装以下组件：

| 组件 | 用途 |
|------|------|
| Intel® oneAPI DPC++/C++ Compiler | 提供 SYCL 编译器（icx） |
| Intel® oneAPI DPC++ Library | 提供 sycl8.dll 运行时（oneAPI 2025+ 需单独勾选） |
| Intel oneAPI Math Kernel Library (oneMKL) | 提供 MKL SYCL 运行时 |
| Intel oneAPI Deep Neural Network Library (oneDNN) | 提供 dnnl.dll |
| Intel oneAPI Threading Building Blocks (oneTBB) | 提供 tbb12.dll |

下载 Intel oneAPI Base Toolkit（安装时选择自定义安装）：
👉 https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **提示：**
> - 安装时选择「自定义安装」，只勾选上表中的组件，可节省大量磁盘空间
> - oneAPI 2025+ 版本中，**DPC++ Library** 是独立于 Compiler 的组件，需单独勾选

### 2.3 Visual Studio Build Tools（必需）

编译 llama-cpp-python 需要 MSVC 编译器和 Windows SDK。

**下载地址**：👉 https://visualstudio.microsoft.com/zh-hans/downloads/#build-tools-for-visual-studio-2022

**安装时选择以下工作负载：**

| 工作负载 | 说明 |
|---------|------|
| 使用 C++ 的桌面开发 | 包含 MSVC 编译器、Windows SDK、CMake 支持 |
| 适用于 Windows 的 C++ CMake 工具 | 提供 Ninja 等构建工具 |

**提示：**
- 不必须安装完整 Visual Studio IDE，**Build Tools 版本** 即可
- 安装完成后，记下安装路径，后续编译时需要用到（如 `D:\Microsoft Visual Studio\2022\BuildTools`）
- 需要确保安装的 **Windows SDK 版本** 与你的系统版本兼容（安装程序默认会选匹配的版本）

### 2.4 CMake（必需）

CMake 是 llama-cpp-python 编译过程的构建系统配置工具。

**下载地址**：👉 https://cmake.org/download/

**安装要求：**
- 版本 >= 3.22（推荐使用最新稳定版）
- 安装时勾选 **Add CMake to system PATH**，或安装后手动将 CMake 的 `bin` 目录加入环境变量

**验证安装：**

```cmd
cmake --version
```

应输出类似：

```
cmake version 4.2.0
```

---

## 第三章：编译步骤

### 3.1 确认工具已就绪

打开 cmd 执行：

```cmd
git --version
cmake --version
ninja --version
```

全部输出版本号才能继续。

### 3.2 确认 Python 版本

```cmd
F:\ComfyUI-aki-v3\python\python.exe -V
```

确认输出 `Python 3.13.x`。

### 3.3 降级 scikit-build-core

scikit-build-core 新版本在此环境下存在已知 bug，需固定到 0.10.7：

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip install scikit-build-core==0.10.7
```

### 3.4 获取源码（二选一）

**方式 A：更新已有源码**

```cmd
cd F:\ComfyUI-aki-v3\llama-cpp-python
git fetch
git reset --hard origin/sycl
git submodule update --init --recursive
```

**方式 B：全新克隆**

```cmd
git clone https://github.com/JamePeng/llama-cpp-python F:\ComfyUI-aki-v3\llama-cpp-python
cd F:\ComfyUI-aki-v3\llama-cpp-python
git submodule update --init --recursive
```

`submodule update` 会下载底层 llama.cpp 源码，需要几分钟，请耐心等待。

### 3.5 清理旧的 site-packages

```cmd
rd /s /q "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp"
rd /s /q "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp_python-0.3.32.dist-info"
```

⚠️ 第二行的版本号改成当前已安装的版本号。

### 3.6 设置编译环境

```cmd
set VS2022INSTALLDIR=D:\Microsoft Visual Studio\2022\BuildTools
"F:\Intel-oneAPI\setvars.bat" --force
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=on -DGGML_ONEDNN=off -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_TARGET=INTEL -Wno-dev
```

> 为了更好的兼容性，设置 `-DGGML_ONEDNN=off`，有需要的可以打开。

### 3.7 编译安装

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

### 3.8 验证安装

**验证版本号：**

```cmd
F:\ComfyUI-aki-v3\python\python.exe -c "import llama_cpp; print(llama_cpp.__version__)"
```

**验证视觉模块（JamePeng 分支特有）：**

```cmd
F:\ComfyUI-aki-v3\python\python.exe -c "from llama_cpp.llama_chat_format import Qwen3VLChatHandler, Qwen25VLChatHandler; print('handlers OK')"
```

两条命令都正常输出即安装成功。

> **注：为什么验证 QwenVL？**
> - 作者编译的 llama-cpp-python 源代码来自于 JamePeng fork 的版本
> - 这个版本里面有专门用于视觉处理的 handler：`Qwen3VLChatHandler` 和 `Qwen25VLChatHandler`
> - 其他来源的 llama-cpp-python 没有这两个类
> - 这两个类是 ComfyUI 加载 Qwen 系列模型处理图文、视频转文的基础

### 3.9 删除 oneAPI 运行时 DLL（可选）

先确认文件名：

```cmd
dir "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\"
```

然后删除 Intel 运行时（mkl/dnnl/tbb），保留编译产物（ggml/llama/mtmd）：

```cmd
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\dnnl.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_core.2.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_sycl_blas.5.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_tbb_thread.2.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\tbb12.dll"
```

⚠️ oneAPI 升级后文件名可能变化，以 `dir` 实际输出为准。

### 3.10 验证运行正常

启动 ComfyUI / Python 跑一次推理，确认日志输出：

- `using device SYCL0` ✅
- `clip_ctx: CLIP using SYCL0 backend` ✅
- token 速度正常（~44 t/s） ✅

---

## 第四章：让 SYCL 在 ComfyUI 中生效

### 4.1 在启动脚本中加载 oneAPI 环境

安装完 oneAPI 后，在 ComfyUI 的启动 `.bat` 文件里，Python 启动之前加入以下一行：

```bat
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
```

**启动脚本示例 `start_comfyui.bat`：**

```bat
@echo off
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
......
......
"C:\python\python.exe" main.py --listen 0.0.0.0
```

### 4.2 创建专用的预加载插件

为所有基于 `llama-cpp-python` 的 ComfyUI 节点启用 SYCL GPU 加速，需要创建一个专用的预加载插件。

**第一步：创建插件目录**

```cmd
mkdir "your_comfyui\custom_nodes\sycl-preloader"
```

**第二步：创建空的 `__init__.py`**

```cmd
echo. > "your_comfyui\custom_nodes\sycl-preloader\__init__.py"
```

**第三步：创建 `prestartup_script.py`**

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
            print("[SYCL] 找不到 llama_cpp 包")
            return
        _pkg_dir = Path(_spec.origin).parent
        for _sub in ['', 'lib', 'bin']:
            _d = _pkg_dir / _sub if _sub else _pkg_dir
            if _d.exists():
                os.add_dll_directory(str(_d))
        for _p in os.environ.get("PATH", "").split(os.pathsep):
            if "Intel" in _p and os.path.exists(_p):
                os.add_dll_directory(_p)
        print("[SYCL] DLL搜索路径注册完成")
    except Exception as e:
        print(f"[SYCL] Error: {e}")

sycl_preloader()
```

### 4.3 为什么需要 prestartup_script.py？

**问题背景：**

编译并安装 SYCL 版本的 llama-cpp-python 之后，直接用 Python 脚本调用时 GPU 可以正常工作。但是，ComfyUI 里基于 llama-cpp-python 的插件（例如提示词反推插件）却无法激活 SYCL，只能回退到 CPU 运行。

**根本原因：**

Python 3.8+ 在 Windows 上引入的 DLL 加载限制——出于安全考虑，Python 3.8+ 在加载 DLL 时完全忽略 `PATH` 环境变量。即使 `setvars.bat` 已经正确地把 oneAPI 路径写入了 `PATH`，Python 也不会通过这个机制找到 SYCL DLL。唯一可靠的方式是在 Python 代码里显式调用 `os.add_dll_directory()`，在需要 DLL 之前提前注册搜索路径。

**为什么 .bat 启动文件和 main.py 都不行？**

- **启动 .bat 文件**：可以设置 `PATH` 和环境变量，但无法调用 Python 的 `os.add_dll_directory()`，DLL 加载限制依然存在。
- **ComfyUI 的 main.py**：看起来是个选项，但 `main.py` 第一行就开始导入 ComfyUI 核心模块（`import comfy.options` 等），这些 import 会间接触发插件加载链，导致 `llama_cpp` 可能在预加载代码执行之前就已经被导入了。时机太晚，不可靠。

**解决方案：利用 ComfyUI 的 prestartup 机制**

ComfyUI 内置了一个钩子函数 `execute_prestartup_script()`。启动时，ComfyUI 会扫描 `custom_nodes\` 下每一个子文件夹，找到并执行其中名为 `prestartup_script.py` 的文件。这个过程发生在所有插件节点被导入之前，是整个 ComfyUI 进程中最早能可靠运行 Python 代码的时机。

**启动顺序：**

```
main.py 基础初始化
    ↓
execute_prestartup_script()  ← prestartup_script.py 在这里执行
    ↓
加载各插件的 __init__.py / nodes.py
    ↓
启动服务器
```

通过 `os.add_dll_directory()` 加载 SYCL DLL 之后，效果是进程级别的。后续所有基于 `llama-cpp-python` 的插件（ComfyUI-QwenVL、comfyui-sg-llama-cpp 等）都能自动找到已经在内存中的 DLL，无需每个插件单独配置。

### 4.4 为什么要建一个专用的插件文件夹？

如果把 `prestartup_script.py` 放在某个现有插件的文件夹里（例如 `comfyui-sg-llama-cpp`），风险很高——一旦那个插件被删除或更新，这个文件就消失了。

最稳妥的做法是创建一个只包含两个文件的最小专用插件目录：

```
custom_nodes\sycl-preloader\
    __init__.py          （空文件）
    prestartup_script.py （SYCL DLL 预加载器）
```

这个文件夹没有节点、没有依赖，永远不会被 ComfyUI Manager 的更新机制修改。它只有一个职责：在正确的时机为整个 ComfyUI 进程完成 SYCL DLL 的预加载。

---

## 第五章：已知问题和注意事项

### 5.1 0.3.39 及以上版本的 MTMD + SYCL 兼容性问题（重要）

**问题描述：**

在 0.3.39 版本中，llama.cpp 主线合并了 MTMD（Multi-Modal Token Decoding）重构。这条新路径在 SYCL 后端上存在内存访问问题，会导致 `access violation` 崩溃：

```
Windows fatal exception: access violation
Llama.eval(decode): Fatal Decode Error at Pos 0, Batch size 68
```

**影响范围：**
- 所有走 MTMD 路径的多模态推理：Qwen3-ASR 音频转录、新版本的多模态图片/视频处理
- 无论 `n_gpu_layers` 和 `use_gpu` 如何设置，只要 SYCL 运行时 DLL 被加载就会触发

**不影响：**
- 纯 CPU 编译的 0.3.39 版本（已验证正常）
- 0.3.38 及更早版本的 SYCL 编译（走旧的 llava 路径，不受影响）

**原因：**

llama.cpp 主线中 CUDA、Metal、Vulkan 后端更新频繁，始终紧跟 MTMD 重构的接口变化。SYCL 后端维护节奏较慢，结构体变更和 API 调整后容易出现对齐问题。不是特定代码的 bug，而是后端跟进速度差异导致的兼容性断层。

**当前建议：**
- 日常使用请继续用 0.3.38+sycl 版本
- 如需使用 Qwen3-ASR 等 0.3.39 新增功能，可暂时改用纯 CPU 版
- 等待上游 llama.cpp 修复或 SYCL 后端跟进后再编译新版

### 5.2 MSVC 中文编码问题

**问题描述：**

用 MSVC 编译 JamePeng 分支的 llama-cpp-python 时，`vendor/llama.cpp/common/jinja/utils.h` 文件中的 Unicode 字符（`↵` U+21B5）在简体中文 Windows（代码页 936）下会导致编译错误：

```
error C2001: 常量中有换行符
error C2146: 语法错误: 缺少")"
```

**解决方法：**

用记事本打开 `vendor/llama.cpp/common/jinja/utils.h`，另存为 **UTF-8 编码**（带 BOM）即可。

或者用 PowerShell 命令转换：

```powershell
$content = Get-Content -Path "vendor\llama.cpp\common\jinja\utils.h" -Raw -Encoding UTF8
$utf8bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText("vendor\llama.cpp\common\jinja\utils.h", $content, $utf8bom)
```

### 5.3 scikit-build-core 版本锁定

编译环境需要将 `scikit-build-core` 固定到 **0.10.7** 版本，新版本在此环境下存在兼容性问题：

```cmd
pip install scikit-build-core==0.10.7
```

如果不固定版本，可能会出现 CMake 配置失败或 wheel 构建异常。

### 5.4 GGML_ONEDNN 的取舍

编译参数中设置了 `-DGGML_ONEDNN=off`，原因如下：

- **开启 oneDNN**：提供 Intel 优化过的矩阵运算 kernel，理论上性能更好
- **关闭 oneDNN**：兼容性更稳定，某些环境下 oneDNN 可能导致额外的 DLL 依赖或运行时报错

如果希望获得最佳性能，可以尝试设置为 `on`，但建议先以 `off` 验证编译通过和运行正常后，再开启对比效果。

### 5.5 编译生成器选择

当前推荐使用 **Ninja**：

```cmd
set CMAKE_GENERATOR=Ninja
```

Ninja 比 MSBuild 编译速度更快，尤其是在增量编译场景下。如果未安装 Ninja，可通过 Visual Studio Installer 添加"适用于 Windows 的 C++ CMake 工具"组件，或单独下载安装。

如果 Ninja 不可用，CMake 会自动回退到 MSBuild，编译时间会显著变长。

### 5.6 oneAPI 版本兼容性

不同版本的 Intel oneAPI 对 SYCL 后端的支持有差异。如果遇到编译失败或运行时报错，建议：

- 使用 **2024 年及以后发布的 oneAPI 版本**（较老的版本可能缺少某些 SYCL kernel 支持）
- oneAPI 升级后，`lib/` 目录下的运行时 DLL 文件名可能发生变化（如 `mkl_core.2.dll` → `mkl_core.3.dll`），删除运行时 DLL 前务必以 `dir` 实际输出为准
- 不同 oneAPI 大版本之间，`setvars.bat` 的路径可能不同，请以实际安装路径为准：

| oneAPI 版本 | 默认路径 |
|-------------|---------|
| 2024 及之后 | `C:\Program Files\Intel\oneAPI\setvars.bat` |
| 较旧版本 | `C:\Program Files (x86)\Intel\oneAPI\setvars.bat` |

### 5.7 验证编译是否成功的快速方法

编译完成后，在 cmd 中执行以下命令（需要先运行 `setvars.bat` 加载环境）：

```cmd
F:\ComfyUI-aki-v3\python\python.exe -c "import llama_cpp; print(llama_cpp.__version__)"
```

如果输出版本号且无 DLL 加载错误，说明编译成功。

如需确认 SYCL 后端可用，运行一次模型推理，观察日志是否包含：

```
using device SYCL0 (Intel(R) Arc(TM) B580 Graphics)
clip_ctx: CLIP using SYCL0 backend
```

### 5.8 编译纯 CPU 版本

如果不需要 SYCL GPU 加速（例如用于测试或对比），可以编译纯 CPU 版本：

```cmd
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=off -Wno-dev
pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

纯 CPU 版不需要 oneAPI，也不需要 `setvars.bat` 加载环境，但推理速度会慢 5-10 倍。

### 5.9 编译 Vulkan 版本

如果 SYCL 后端遇到兼容性问题（如 5.1 所述的 MTMD 崩溃），可以考虑改用 Vulkan 后端。Intel Arc 显卡对 Vulkan 支持良好，且 llama.cpp 的 Vulkan 后端更新较为活跃。

**环境要求：**

- 安装 **Vulkan SDK**：👉 https://vulkan.lunarg.com/sdk/home
- 安装时确保勾选 **Vulkan SDK 组件**（默认安装即可）
- 需要 **Visual Studio Build Tools**（与 SYCL 编译相同，参见第二章）

**编译命令：**

```cmd
set VS2022INSTALLDIR=D:\Microsoft Visual Studio\2022\BuildTools
call "D:\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=on -Wno-dev
pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

**注意事项：**

- Vulkan 编译**不需要 oneAPI**，环境更轻量
- 编译产物不依赖 Intel 运行时 DLL（无需删除运行时文件的步骤）
- 性能方面，Vulkan 在 Intel Arc 上约为 SYCL 的 **90-95%**，大部分场景差距不明显
- 如果同时安装了 CUDA 后端，可以用 `-DGGML_CUDA=off` 强制关闭

**验证运行：**

启动 ComfyUI 后，观察日志确认 Vulkan 后端生效：

```
using device Vulkan0 (Intel(R) Arc(TM) B580 Graphics)
```

---

## 已知限制

- **Intel Arc（SYCL0）不支持 Flash Attention**，显存占用会高于 CUDA 方案
- **部分 CLIP 图计算算子会回退到 CPU**，视觉编码性能受限
- **Qwen3.5-2B（混合/循环架构）可能导致不稳定**，建议改用 Qwen3-2B

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

- [JamePeng 的 SYCL 分支](https://github.com/JamePeng/llama-cpp-python)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
