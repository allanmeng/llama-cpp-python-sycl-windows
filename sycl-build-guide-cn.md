# llama-cpp-python-sycl-windows 编译指南

> **最近更新时间**：2026-08-09

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

### 2.2 Intel oneAPI Base Toolkit（推荐安装 oneAPI 2026.1）

SYCL 运行时依赖 Intel oneAPI，但无需安装完整工具包，只需安装以下组件：

| 组件 | 用途 |
|------|------|
| Intel® oneAPI DPC++/C++ Compiler | 提供 SYCL 编译器（icx） |
| Intel® oneAPI DPC++ Library | 提供 sycl9.dll 运行时（2026.1 版本） |
| Intel oneAPI Math Kernel Library (oneMKL) | 提供 MKL SYCL 运行时 |
| Intel oneAPI Deep Neural Network Library (oneDNN) | 提供 dnnl.dll |
| Intel oneAPI Threading Building Blocks (oneTBB) | 提供 tbb12.dll |

下载 Intel oneAPI Base Toolkit（安装时选择自定义安装）：
👉 https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **提示：**
> - 安装时选择「自定义安装」，只勾选上表中的组件，可节省大量磁盘空间
> - oneAPI 2025+ 版本中，**DPC++ Library** 是独立于 Compiler 的组件，需单独勾选

**为什么推荐 oneAPI 2026.1？**

- **Arc B 系列（Battlemage）支持更好**：本仓库面向 Intel Arc B580 等 B 系列显卡。Battlemage 是新架构，需要较新的 oneAPI 才有完整的 SYCL kernel 支持与性能优化；较旧版本（如 2024.x）对 B 系列支持不完善。
- **与 PyTorch XPU 2.13 年度对齐**：oneAPI 2026 ↔ Intel Deep Learning Essentials 2026.0 ↔ PyTorch XPU 2.13 是官方年度配对组合，ABI 对齐。若 oneAPI 版本与 PyTorch XPU 版本错位，可能出现运行时不匹配。
- **Intel 官方建议**：官方推荐使用最新 oneAPI 与驱动以确保最佳性能与兼容性。

> ⚠️ **注意**：本仓库预编译的 wheel（0.3.43 及以后）使用 oneAPI 2026.1 编译，部署时目标机也需安装 oneAPI 2026.1（版本需与编译时对齐）。如果只需要**纯反推/推理**（不依赖 PyTorch XPU 跑图），Python 版本无硬性限制；但若同时用 PyTorch XPU 跑图，需确保 PyTorch XPU ≥ 2.13。

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
cd D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
git fetch
git reset --hard origin/main
git submodule update --init --recursive
```

> ⚠️ 源码路径以你的实际位置为准（本仓库测试环境在 `D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python`）。`git reset --hard` 后记得 `git status` 核对工作树是否真的有文件——`submodule update` 偶尔只更新 index/HEAD 而工作树文件没落盘（表现为大量文件显示"被删"），此时进入 `vendor/llama.cpp` 执行 `git reset --hard HEAD` 写回即可。

**方式 B：全新克隆**

```cmd
git clone https://github.com/JamePeng/llama-cpp-python D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
cd D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python
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

> `-DGGML_ONEDNN=off` 仅关闭 CPU 通用后端的 oneDNN 优化（见 5.2 说明），不影响 SYCL 后端的 oneDNN flash-attention（默认开启）。

### 3.7 编译安装

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

### 3.8 验证安装

**验证版本号：**

```cmd
F:\ComfyUI-aki-v3\python\python.exe -m pip show llama_cpp_python
```

> ⚠️ 用 `pip show` 而非 `import llama_cpp` 打印版本：裸 CLI 下 `import llama_cpp` 可能因 SYCL 运行时 DLL 未加载报 `Failed to load 'ggml-base'`（误导性错误）。`pip show` 直接读元数据，不受 DLL 加载影响。

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

然后删除 Intel 运行时（mkl/dnnl/tbb），保留编译产物（ggml/llama/mtmd）和 `libomp140.x86_64.dll`（OpenMP 预加载修复依赖，**不可删除**）：

```cmd
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\dnnl.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_core.3.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_sycl_blas.6.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\mkl_tbb_thread.3.dll"
del "F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp\lib\tbb12.dll"
```

⚠️ oneAPI 升级后文件名可能变化（如 `mkl_core.2` → `mkl_core.3`），以 `dir` 实际输出为准。

> **注意**：删除后 DLL 由已安装的 oneAPI 提供，**必须在加载了 oneAPI 环境（setvars.bat）的进程中运行**，否则会报 `Failed to load 'ggml-base'`。

### 3.10 验证运行正常

启动 ComfyUI / Python 跑一次推理，确认日志输出：

- `using device SYCL0` ✅
- `clip_ctx: CLIP using SYCL0 backend` ✅
- token 速度正常（Qwen3-VL 视觉模型实测 ~70 t/s，纯文本更高） ✅

---

## 第四章：让 SYCL 在 ComfyUI 中生效

### 4.1 在启动脚本中加载 oneAPI 环境

安装完 oneAPI 后，在 ComfyUI 的启动 `.bat` 文件里，Python 启动之前加入以下一行：

```bat
call "F:\Intel-oneAPI\setvars.bat" --force
```

> ⚠️ `setvars.bat` 的实际路径以你安装 oneAPI 的位置为准（如 `C:\Program Files\Intel\oneAPI\setvars.bat`），不确定时用 `dir /s setvars.bat` 搜索。

**启动脚本示例 `start_comfyui.bat`：**

```bat
@echo off
call "F:\Intel-oneAPI\setvars.bat" --force
......
......
"F:\ComfyUI-aki-v3\python\python.exe" main.py --listen 0.0.0.0
```

> **说明**：0.3.42 及以后的版本已在 `llama_cpp` 导入时自动注册包内 `lib/`、`bin/` 目录的 DLL 搜索路径，**无需再创建 `sycl-preloader` 预加载插件**（旧版本文档的 4.2-4.4 节已废弃删除）。只要在启动脚本中加载 oneAPI 环境，基于 llama-cpp-python 的插件（如 comfyui-sg-llama-cpp）即可正常使用 SYCL GPU 加速。

---

## 第五章：已知问题和注意事项

### 5.1 scikit-build-core 版本锁定

编译环境需要将 `scikit-build-core` 固定到 **0.10.7** 版本，新版本在此环境下存在兼容性问题：

```cmd
pip install scikit-build-core==0.10.7
```

如果不固定版本，可能会出现 CMake 配置失败或 wheel 构建异常。

### 5.2 GGML_ONEDNN 参数说明

编译参数中设置了 `-DGGML_ONEDNN=off`，说明如下：

- `GGML_ONEDNN` 控制的是 **CPU 通用后端的 oneDNN 优化**（仅影响纯 CPU 推理），与 SYCL 后端无关
- **SYCL 后端的 oneDNN flash-attention** 由另一个开关 `GGML_SYCL_DNN` 控制（默认开启），编译时若能找到 oneAPI 的 oneDNN 会自动启用 `GGML_SYCL_DNNL`，该路径是 SYCL 推理的最优性能路径
- 因此不要为了"开启 onednn"去改 `GGML_ONEDNN`——它对 SYCL 推理没有任何影响，保持 `off` 即可

### 5.3 编译生成器选择

当前推荐使用 **Ninja**：

```cmd
set CMAKE_GENERATOR=Ninja
```

Ninja 比 MSBuild 编译速度更快，尤其是在增量编译场景下。如果未安装 Ninja，可通过 Visual Studio Installer 添加"适用于 Windows 的 C++ CMake 工具"组件，或单独下载安装。

如果 Ninja 不可用，CMake 会自动回退到 MSBuild，编译时间会显著变长。

### 5.4 oneAPI 版本兼容性

不同版本的 Intel oneAPI 对 SYCL 后端的支持有差异。如果遇到编译失败或运行时报错，建议：

- 使用 **2026.1 及以后发布的 oneAPI 版本**（0.3.43 及以后的预编译 wheel 均基于 oneAPI 2026.1 编译，运行环境需与编译版本对齐；较老的版本可能缺少某些 SYCL kernel 支持，且与 B 系列显卡的配合不完整）
- oneAPI 升级后，`lib/` 目录下的运行时 DLL 文件名可能发生变化（如 `mkl_core.2.dll` → `mkl_core.3.dll`、`sycl8.dll` → `sycl9.dll`），删除运行时 DLL 前务必以 `dir` 实际输出为准
- 不同 oneAPI 大版本之间，`setvars.bat` 的路径可能不同，请以实际安装路径为准（本仓库测试环境为 `F:\Intel-oneAPI\setvars.bat`）：

| oneAPI 版本 | 常见路径 |
|-------------|---------|
| 2025+（本仓库实测） | `F:\Intel-oneAPI\setvars.bat`（自定义安装路径） |
| 2024 及之后（默认安装） | `C:\Program Files\Intel\oneAPI\setvars.bat` |
| 较旧版本 | `C:\Program Files (x86)\Intel\oneAPI\setvars.bat` |

### 5.5 验证编译是否成功的快速方法

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

### 5.6 编译纯 CPU 版本

如果不需要 SYCL GPU 加速（例如用于测试或对比），可以编译纯 CPU 版本：

```cmd
set CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=off -Wno-dev
pip install . --no-build-isolation --force-reinstall --no-cache-dir
```

纯 CPU 版不需要 oneAPI，也不需要 `setvars.bat` 加载环境，但推理速度会慢 5-10 倍。

### 5.7 编译 Vulkan 版本

如果 SYCL 后端遇到兼容性问题，可以考虑改用 Vulkan 后端。Intel Arc 显卡对 Vulkan 支持良好，且 llama.cpp 的 Vulkan 后端更新较为活跃。

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

- **Intel Arc（SYCL0）的 Flash Attention 依赖 oneDNN**：SYCL 后端的 FA 通过 oneDNN flash-attention 路径实现（`GGML_SYCL_DNNL`，默认开启）。该路径曾存在多轮对话乱码问题（llama.cpp PR #25741 / #25880），0.3.45 起已由上游原生修复。
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
| oneAPI | 2026.1 |
| llama-cpp-python | 0.3.46+sycl |
| ComfyUI | 0.16.3 |

---

## 相关项目

- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [llama-cpp-python](https://github.com/JamePeng/llama-cpp-python) by JamePeng
- [llama-cpp-python-sycl-windows](https://github.com/allanmeng/llama-cpp-python-sycl-windows) by allanmeng
