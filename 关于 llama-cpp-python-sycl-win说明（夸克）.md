# 关于 llama-cpp-python-sycl-win

## 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| PyTorch XPU | ≥ 2.13 | 仅当 ComfyUI 使用 PyTorch XPU 方案时需要 |
| Intel oneAPI | 2026.1 | SYCL 运行时必需 |
| Python | 3.13 | 预编译目标版本 |

## 版本进度

> 📌 **当前最新**：0.3.47+sycl（2026-08-16）

### [0.3.47+sycl] - 2026-08-16

- **零本地补丁**（#25880 已由上游原生合入，多轮对话乱码修复稳定）
- MTMD **Pocket TTS 音频绑定**同步（音频生成实验线继续演进，目前仍为绑定级）
- 新增**多输出后端采样器 API** + 自定义采样器钩子修复
- **模型 reset 修复**（`reset()` 完全清理模型状态）
- **🚀 实测性能提升**：B580 实测 83.61 t/s（较 0.3.45 的 72.7 t/s 提升约 15%），热启动总耗时 25.75s（较 0.3.45 的 33.28s 快 7.5s）
- 打包为**精简版**（约 36MB），运行时 DLL 由 oneAPI 提供

### [0.3.46+sycl] - 2026-08-08

- **零本地补丁**（#25880 已由上游原生合入，多轮对话乱码修复稳定）
- 新增扩展模型 API（`target_layer_ids()` / `get_tok_embd()`）
- MTMD 绑定更新（HunyuanVL 解码器位置、音频生成实验接口）
- **Windows 运行时兼容性改进**：修复同一进程多 OpenMP / 外部 ggml DLL 冲突
- 打包为**精简版**（约 35MB），运行时 DLL 由 oneAPI 提供

### [0.3.45+sycl] - 2026-08-01

- **🎉 PR #25880 上游合入，本地补丁正式退役**（多轮对话乱码修复由上游原生提供）
- 修复 llama-ext 绑定签名、新增模型加载选项（`load_mode` 等）
- 打包为**精简版**（约 36MB），运行时 DLL 由 oneAPI 提供

### [0.3.44+sycl+pr25880] - 2026-07-31

- 上游新增 **OpenMP 预加载修复**（Windows DLL 加载更稳定）
- 保留 **PR #25880** 补丁（修复 SYCL 多轮对话乱码）
- 打包改为**精简版**（约 36MB），运行时 DLL 由 oneAPI 提供

### [0.3.43+sycl+pr25880+oneapi2610] - 2026-07-20

- 自包含 oneAPI 运行时（约 109MB），部署**无需预装 oneAPI**

## 关于在 ComfyUI 中正常使用

1. 本版本由 **oneAPI 2026.1** 编译，使用前请先安装 oneAPI
2. 在 ComfyUI 的 bat 启动文件中增加 `setvars.bat` 以加载 oneAPI 环境
3. 安装包中已去除与 oneAPI 相同的 DLL（`dnnl.dll`、`mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`、`tbb12.dll`），运行时由 oneAPI 提供
4. 安装 oneAPI 时建议选择**自定义安装**，勾选 DPC++ Compiler、oneMKL、oneDNN、oneTBB 即可

## 关于提示词反推插件 ~ comfyui-sg-llama-cpp

从 **0.3.39** 版本开始，llama-cpp-python 引入了重大的 **MTMD（Multi-Modal Token Decomposition）重写**，对视觉模型的支持方式做了底层重构。

之前的 `comfyui-sg-llama-cpp` 官方版本已经无法支持，所以我 **Fork** 此项目，修改了代码，继续适配新版本的 llama-cpp-python。

> ⚠️ llama-cpp-python-sycl **≥ 0.3.39** 版本，请删除原版插件，改用 Fork 版本插件：  
> https://github.com/allanmeng/comfyui-sg-llama-cpp

## 相关内容

- 项目仓库：https://github.com/allanmeng/llama-cpp-python-sycl-windows
- 《Intel ARC 显卡，给 ComfyUI 手工安装/升级 llama-cpp-python-sycl 的步骤》：  
  https://www.yuque.com/allan-gmwqz/xq0z39/ckgeuiklqkazz75k?singleDoc#
- 编译指南（中文）：https://github.com/allanmeng/llama-cpp-python-sycl-windows/blob/main/sycl-build-guide-cn.md
- 编译指南（英文）：https://github.com/allanmeng/llama-cpp-python-sycl-windows/blob/main/sycl-build-guide-en.md
