[中文](README.md) | [English](README_EN.md)

# llama-cpp-python-sycl-windows

为 Windows 平台预编译的 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) 安装包，支持 **Intel Arc GPU (SYCL)** 加速。

基于 [JamePeng 的分支](https://github.com/JamePeng/llama-cpp-python) 编译，为 Intel Arc GPU 提供 SYCL 加速支持。

手工安装/升级whl的步骤扫盲包 [https://www.yuque.com/allan-gmwqz/xq0z39/ckgeuiklqkazz75k?singleDoc#](https://www.yuque.com/allan-gmwqz/xq0z39/ckgeuiklqkazz75k?singleDoc)

---

## 0.3.39+ 重要变更说明

### 1. llama-cpp-python-sycl-windows 在 0.3.39 之后发生了哪些变化

从 0.3.39 版本开始，llama-cpp-python 引入了重大的 **MTMD（Multi-Modal Token Decomposition）重写**，对视觉模型的支持方式做了底层重构：

| 变更项 | 0.3.38 及之前 | 0.3.39+ |
|--------|-------------|---------|
| 视觉模型加载方式 | 手动创建 `clip_model_path` handler 注入 `Llama()` | `mmproj_path` 直接传给 `Lama()`，内部自动创建 handler |
| 视觉 handler 类 | 模型特定 handler（如 `Qwen3VLChatHandler`） | `GenericMTMDChatHandler` 统一处理 |
| handler 参数传递 | 直接传给 handler 构造函数 | 通过 `chat_handler_kwargs` dict 传递 |
| 混合架构模型 | 无特殊处理 | 需设置 `ctx_checkpoints=0`（如 Qwen3.5） |

### 2. 从 0.3.38 或更早版本升级的用户需要手工清理哪些内容

> **重要**：不要直接使用 `pip install --upgrade`，旧版本残留文件可能与新版冲突。请按以下步骤操作：

#### 步骤 1：完全卸载旧版本

```bat
pip uninstall llama-cpp-python -y
```

#### 步骤 2：安装新版本 whl

```bat
pip install llama_cpp_python-0.3.41+sycl-cp313-cp313-win_amd64.whl
```

#### 步骤 3：更新 ComfyUI 插件

如果你在 ComfyUI 中使用此 whl，必须使用适配 0.3.39+ 的插件版本（见下方第 3 节）。

### 3. 对应适配的 ComfyUI 插件

原版 `comfyui-sg-llama-cpp` 插件不支持 0.3.39+ 的 MTMD 重写。以下 fork 已完成适配：

**https://github.com/allanmeng/comfyui-sg-llama-cpp**

适配内容：
- **`clip_model_path` → `mmproj_path`**：直接传给 `Llama()`，不再手动创建 handler
- **`GenericMTMDChatHandler` 参数过滤**：取 `GenericMTMDChatHandler` ∪ `MTMDChatHandler` 参数并集，过滤掉 `force_reasoning`、`enable_thinking` 等 0.3.39+ 不接受的参数
- **新增 `ctx_checkpoints` 选项**（默认 `0`）：混合架构模型（Qwen3.5 等 Transformer+Mamba）必须设置
- **`vision_image_min_tokens` 默认值**从 `-1` 改为 `1024`（Qwen-VL 最低要求）
- **移除无效 UI 参数**：`vision_enable_thinking`、`vision_force_reasoning`、`vision_add_vision_id`

安装方式：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/allanmeng/comfyui-sg-llama-cpp
```

---

## 0.3.43+ 构建与部署说明（oneAPI 2026 / Python XPU ≥ 2.13）

### 1. 为什么 0.3.43 起使用 oneAPI 2026 编译

从 0.3.43 开始，本项目的构建环境升级到 **Intel oneAPI Base Toolkit 2026**（对应 Intel Deep Learning Essentials 2026.0）。升级动机：

- Intel 官方建议安装并使用最新 oneAPI / 显卡驱动，以确保 Intel Arc B580（Battlemage）的性能与兼容性。
- 0.3.43 的编译需要搭配 **Python XPU 运行时（`intel-xpu-backend-for-pytorch` / PyTorch XPU）≥ 2.13**（即 PyTorch 2.13 生态）。oneAPI 2026 与之在 ABI 与运行时层面匹配；若混用旧版 Python XPU 后端（如 2.12 + oneAPI 2025）可能导致运行时不匹配。

> **重要**：若你的 ComfyUI / 推理环境使用 PyTorch XPU 方案，请确保 `intel-xpu-backend-for-pytorch` **≥ 2.13**，与 0.3.43 的 oneAPI 2026 构建保持一致。

### 2. whl 自带 oneAPI 运行时（自包含部署）

自 0.3.43 起，发布的 whl **自带完整的 oneAPI 运行时**（包含 `dnnl.dll`、`mkl_*.dll`、`tbb12.dll`、`libomp140.x86_64.dll` 等），因此部署目标机 **无需预先安装 oneAPI** 即可直接使用 SYCL 加速。（使用 0.3.43+ 自包含 whl 时，可跳过下方「前置要求」中的 oneAPI 安装步骤。）

### 3. 已安装 oneAPI Toolkit 的用户可精简（可选）

若目标机上 **已经安装了** Intel oneAPI Base Toolkit（或 Deep Learning Essentials），whl 内打包的 oneAPI 运行时 DLL 是冗余的，可手动删除以节省磁盘空间：

- 目录：`your_python\Lib\site-packages\llama_cpp\lib\`
- 可删除的文件：
  - `dnnl.dll`
  - `mkl_core.3.dll`
  - `mkl_sycl_blas.6.dll`
  - `mkl_tbb_thread.3.dll`
  - `tbb12.dll`
  - （`libomp140.x86_64.dll` 若系统已通过 VS / oneAPI 提供 OpenMP，亦可删除）

> 删除后，运行时将通过目标机已安装的 oneAPI（经 `setvars.bat` 或系统 PATH）提供这些 DLL。请确保 oneAPI 已正确安装并加载，否则会因缺少运行时而加载失败。

### 4. PR #25880 补丁：修复 SYCL onednn fattn 长上下文乱码

0.3.43 版本本地应用了 [PR #25880](https://github.com/ggml-org/llama.cpp/pull/25880)（ggml-org/llama.cpp）补丁，修复了 SYCL onednn flash-attention 路径下的 **use-after-return** 问题。

**症状**：在较长上下文（n_kv ≥ ~26k，如多轮对话第二轮）时，oneDNN fattn 的输出塌缩为重复 token（"GGGGG…" 模式）。

**根因**：SDPA scale 值通过 async memcpy 从 CPU 上传到 GPU device buffer，源是栈局部变量。当 K/V staging 内核在 in-order 队列中先于 memcpy 完成时，栈帧已被回收，memcpy 读到垃圾值 → 后续 SDPA 使用错误的 scale → 输出乱码。

**修复方案**：
- 将 scale 上传改为**同步 memcpy**（`.wait()`），确保拷贝完成后再返回 buffer 指针
- 使用 **per-device device scalar 缓存**（`static std::unordered_map`），scale 值仅首次同步上传一次，后续复用缓存，消除重复 sync 开销
- 新增环境变量 `GGML_SYCL_FA_ONEDNN_MAX_KV`（默认 0 = 不限），可在极长序列场景选择性回退到原生 FA kernel

**与之前 PR #25741 的区别**：原先的 #25741 使用无条件 `wait_and_throw()` 来掩盖问题（靠撑住栈帧让 async memcpy 完成），但每调用付出 ~6% PP 性能代价。`#25880` 从根因修复，且单设备无性能损失。

---

## 前置要求

安装前，请确保已完成以下步骤：

### 1. Intel Arc 显卡驱动

从以下地址下载并安装最新的 Intel Arc 显卡驱动：
https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

### 2. Intel oneAPI Base Toolkit（必须安装）

SYCL 运行时依赖 Intel oneAPI，但 **无需安装完整工具包**，只需安装以下组件：

| 组件 | 用途 |
|------|------|
| Intel oneAPI DPC++/C++ Compiler | 提供 `sycl8.dll`、`OpenCL.dll` 运行时 |
| Intel oneAPI Math Kernel Library (oneMKL) | 提供 MKL SYCL 运行时 |
| Intel oneAPI Deep Neural Network Library (oneDNN) | 提供 `dnnl.dll` |
| Intel oneAPI Threading Building Blocks (oneTBB) | 提供 `tbb12.dll` |

下载 Intel oneAPI Base Toolkit（安装时选择自定义安装）：
https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **提示：** 安装时选择「自定义安装」，只勾选上表中的 4 个组件，可节省大量磁盘空间。

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 x64 |
| 显卡 | Intel Arc（炼金师 / 战法师架构） |
| 驱动 | Intel Arc 显卡驱动（最新版） |
| oneAPI | 必须安装 — DPC++ Compiler、oneMKL、oneDNN、oneTBB |

---

## 可用安装包

| 版本 | 文件 | 大小 |
|------|------|------|
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

从 [Releases](https://github.com/allanmeng/llama-cpp-python-sycl-windows/releases) 页面下载。

---

## 安装方法

### 方法一：pip 安装（推荐）

```bat
pip uninstall llama-cpp-python -y
pip install llama_cpp_python-0.3.41+sycl-cp313-cp313-win_amd64.whl
```

先 uninstall 再 install 是最干净的安装方式。

### 方法二：手动安装（适用于 ComfyUI 等嵌入式 Python 环境）

1. 将 whl 文件重命名为 `.zip` 后解压
2. 将 `llama_cpp` 文件夹复制到 `site-packages` 目录：
   ```
   your_python\Lib\site-packages\llama_cpp\
   ```

---

## 在 ComfyUI 中使用

### 在启动脚本中加载 oneAPI 环境

安装完 oneAPI 后，在 ComfyUI 的启动 `.bat` 文件里， **Python 启动之前** 加入以下一行：

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

---

### 创建专用的预加载插件

> **注意（自 0.3.43 起）**：0.3.43 的 whl 已自带 oneAPI 运行时，并在导入 `llama_cpp` 时自动将自身 `lib/` 目录注册到 DLL 搜索路径（继承上游 0.3.42 的 Windows DLL 搜索修复）。因此 **通常情况下，ComfyUI 中不再需要放置 `sycl-preloader` 插件**。以下内容仅供需要兼容 0.3.42 及更早版本，或自定义部署环境的用户参考。

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

#### 为什么使用 prestartup_script.py？

##### 问题背景

编译并安装 SYCL 版本的 llama-cpp-python 之后，直接用 Python 脚本调用时 GPU 可以正常工作。但是，ComfyUI 里基于 llama-cpp-python 的插件（例如提示词反推插件）却无法激活 SYCL，只能回退到 CPU 运行。

根本原因是 **Python 3.8+ 在 Windows 上引入的 DLL 加载限制**：

> 出于安全考虑，Python 3.8+ 在加载 DLL 时完全忽略 `PATH` 环境变量。即使 `setvars.bat` 已经正确地把 oneAPI 路径写入了 `PATH`，Python 也不会通过这个机制找到 SYCL DLL。唯一可靠的方式是在 Python 代码里显式调用 `os.add_dll_directory()`，在需要 DLL 之前提前注册搜索路径。

##### 为什么 bat 启动文件和 main.py 都不行？

- **启动 `.bat` 文件**：可以设置 `PATH` 和环境变量，但无法调用 Python 的 `os.add_dll_directory()`，DLL 加载限制依然存在。
- **ComfyUI 的 `main.py`**：看起来是个选项，但 `main.py` 第一行就开始导入 ComfyUI 核心模块（ `import comfy.options` 等），这些 import 会间接触发插件加载链，导致 `llama_cpp` 可能在预加载代码执行之前就已经被导入了。时机太晚，不可靠。

##### 解决方案：利用 ComfyUI 的 prestartup 机制

ComfyUI 内置了一个钩子函数 `execute_prestartup_script()`。启动时，ComfyUI 会扫描 `custom_nodes\` 下每一个子文件夹，找到并执行其中名为 `prestartup_script.py` 的文件。这个过程发生在 **所有插件节点被导入之前**，是整个 ComfyUI 进程中最早能可靠运行 Python 代码的时机。

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

通过 `os.add_dll_directory()` 和 `ctypes.CDLL()` 加载 SYCL DLL 之后，效果是 **进程级别** 的。后续所有基于 llama-cpp-python 的插件（ComfyUI-QwenVL、comfyui-sg-llama-cpp 等）都能自动找到已经在内存中的 DLL，无需每个插件单独配置。

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
| `ctx_checkpoints` | `0`（禁用；混合架构模型如 Qwen3.5 必须设置） |
| `vision_image_min_tokens` | `1024`（Qwen-VL 最低要求） |
| `vision_image_max_tokens` | `-1`（使用默认值） |

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
