[中文](README.md) | [English](README_EN.md)

# llama-cpp-python-sycl-windows

为 Windows 平台预编译的 [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) 安装包，支持 **Intel Arc GPU (SYCL)** 加速。

基于 [JamePeng 的分支](https://github.com/JamePeng/llama-cpp-python) 编译，为 Intel Arc GPU 提供 SYCL 加速支持。

手工安装/升级whl的步骤扫盲包 [https://www.yuque.com/allan-gmwqz/xq0z39/ckgeuiklqkazz75k?singleDoc#](https://www.yuque.com/allan-gmwqz/xq0z39/ckgeuiklqkazz75k?singleDoc)

---

## 最新版本说明（v0.4.7+sycl · 2026-11-13）

**核心亮点：oneAPI 2026.2 编译迁移 + 打包剔除项增至 6 个（新增 `mkl_intel_thread.3.dll`）+ 性能与 0.4.6 持平 + 上游 MTP 设备态与多 GGUF 分片支持**

- 升级至 llama-cpp-python **0.4.7**（基于 JamePeng `c7c7055`，同步 llama.cpp `2a4daf0e0` = b12345，子模块跨 **171 个提交**，零本地补丁；距 0.4.6 的 `1dd04be` 共 **16 个提交**，其中 1 个仅提升版本号、5 个仅推进子模块指针）
- **🆕 打包剔除项由 5 个增至 6 个（本版最需要你注意的变化）**：新增剔除 **`mkl_intel_thread.3.dll`（38.95 MiB）** —— oneAPI 2026.2 编出的 `ggml-sycl.dll` 新增依赖它，随包会让 whl 从 43 MB 翻到约 **84 MB**。完整剔除名单：`dnnl.dll`、`mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`、`tbb12.dll`、`mkl_intel_thread.3.dll`，**whl 仍为 43 MB（43.13 MiB）**。上游同期提交 **`#32005`** 也在做同一件事（为 Windows SYCL 发布包补 MKL 运行时 DLL），说明这是 2026.2 的普遍问题
- **⚠️ 必须保留 `setvars.bat`**：被剔除的 DLL 全靠目标机的 oneAPI 提供。**若启动脚本去掉 `setvars.bat`，`ggml-sycl.dll` 会加载失败并静默回退 CPU，且没有醒目报错。** 曾尝试「免 setvars」方案（补齐 12 个 DLL + 调整 `lib/` 加载路径），实测否决：B580 在 2026.2 上要求 **Level Zero v2 adapter**，而 `ur_adapter_level_zero_v2.dll` 报 **error 127（入口点缺失）**，退回 `[opencl:gpu:0]`
- **oneAPI 2026.2 编译迁移**：编译器 clang **22 → 23**（`icx` 2026.2.0 Build 20261001），**构建参数无需改动**；随附 oneDNN 仍为 **3.13.2**（2026.2 安装包内 `dnnl` 目录仍指向 2026.1），运行时 DLL 名称未变。**本版 wheel 用 2026.2 编译并实测；若你仍在 2026.1**，所需运行库文件名一致（2026.1 同样带 `mkl_intel_thread.3.dll`），但**未实测，按 `setvars.bat` 正常加载即可**
- **上游主仓要点**（对本插件均向后兼容）：**MTP 设备侧 hidden-state 传输**（新增 `draft_n_ubatch`，可用 `LLAMA_MTP_DEV=0` 强制 host 路径；本插件不用投机解码，不命中）；**`Llama(model_shards=...)` / `SpecConfig.draft_model_shards`** 支持额外 GGUF 分片与外部 PLE 表；**bindings 对齐**（NextN device-state、architecture-capability、decision-label、`moe_cache_cpu_share`）；**MTMD 音频 ABI + mono f32 PCM 流式重采样器 + Kimi K3.1 图像占位符**；**grammar** 支持数值 `allOf` 交集、修正国际象棋与日本将棋规则（`llama_grammar.py` 首次出现内容变化）
- **⚠️ 自建者必读——vendor 必须钉在 `2a4daf0e0`**：上游明确该修订位于 `ggml : prune`（`29dbbad2b`）与 `llama : prune`（`8ca5a8008`）**之前**，并注明原生库**必须从该修订重建**才能匹配更新后的 context 与音频参数 ABI。**本构建正是基于它编译，请勿改用更晚的 prune 提交重编**
- **SYCL 侧 13 项无一项面向吞吐，故性能与 0.4.6 持平（预期结果）**：**`#31285` 拒绝超显存分配 + 新增 `GGML_SYCL_BMG_VRAM_CHECK`（默认 1）** —— 仅对 **BMG 架构**生效，**B580 默认开启**，超分配时打印 `cannot allocate ... MiB` 并拒绝（而非让驱动崩溃）；`#31138` oneDNN FA cache 线程安全化；`#31784` 修复 `CLAMP` 对 strided view 的支持；`#31896` MUL_MAT src1 精度 gating（本机 F32 路径不变）；`#31126`/`#32013` 缓存 device-id；`#31873` AOT >4GB（本机 JIT）；`#30156` 设备侧 MoE 调度（dense 模型不命中）；`#31574` **Alchemist / A770 专用**，B580 不适用；`#30802` YaRN（未启用）；`#30857` `SWIGLU_OAI` f16（本构建 `F16: no`）；`#31465` CPY 舍入精度（本模型无对应类型）
- **⚠️ 一条易误读**：`#31084`（CUDA / Metal radix Top-K 确定性）**不含任何 SYCL 代码改动**（仅 `ggml-cuda`、`ggml-metal` 与测试），不应计入 SYCL 项
- **插件兼容性零改动**：`Llama.__init__` **76 参数**、`create_chat_completion` **55 参数**、`GenericMTMDChatHandler.__init__` **6 参数**，与 0.4.6 完全一致。[comfyui-sg-llama-cpp](https://github.com/allanmeng/comfyui-sg-llama-cpp) 无需改动
- **新增 API 都在 `_internals`（写探测脚本易踩坑）**：`suppress_tokens` / `classifier_free_guidance` 在 `llama_cpp._internals.LlamaModel`，`supports_embd_row` / `set_embeddings_layer_inp_dev` 在 `llama_cpp._internals.LlamaContext` —— **顶层 `llama_cpp` 不导出 `LlamaModel` / `LlamaContext`**，用 `hasattr(llama_cpp.LlamaModel, ...)` 判断会误报缺失
- **显存工作集与 0.4.3 / 0.4.5 / 0.4.6 完全一致**：`SYCL0 compute buffer` **513.02 MiB**、`SYCL_Host` **28.03 MiB**，冷热两次均 `matches expectation`，未增长、无泄漏；新增的 BMG 显存检查在 4032-token 大图下**未触发拒绝**
- **新增 2 个 SYCL 环境变量**：**`GGML_SYCL_BMG_VRAM_CHECK`**（默认 `1`，BMG 显存检查开关，设 `0` 可关闭）、**`GGML_SYCL_MMID_SCHED`**（默认 `1`，设备侧 MoE 调度，仅 MoE 模型生效）；其余环境变量无移除、默认值不变，`GGML_SYCL_ENABLE_GRAPH` 仍默认 `0`
- **构建备查**：零错误一次通过（10 分 28 秒）；`-fsycl` 设备侧编译在 `fattn-vec-instance-q4_0-f16.cpp` 处**第二次出现死锁**（CPU 零增长），清理进程树后重跑即通过，与 0.4.5 记录的链接期死锁同源，**不是代码问题**
- **⚠️ 已知集成注意（延续 0.3.48 / 0.3.49 / 0.4.0 / 0.4.1 / 0.4.2 / 0.4.3 / 0.4.5）：hybrid 视觉模型 + `ctx_checkpoints=0` 首 decode 崩溃**

- 现象：Qwen3.5 等带 SWA 层的 hybrid 视觉模型，大图（约 4000+ vision tokens）下 prefill 正常，但**首 decode token 崩溃**（`failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`）
- 根因：调用方传 `ctx_checkpoints=0` 会强制 hybrid 模型走 "Bypassing rollback" fast-path，大 prefill 下无槽余量给首 decode token
- **本版状态：仍未做专项复测**。0.4.6 对 context 容量与采样器生命周期做过一轮安全清理（`n_ctx_seq`、超限 embedding 输入提前拒绝、采样器持有至 context 析构），0.4.7 又把 context 参数与 `moe_cache_cpu_share` 对齐；本次两次真机跑（冷 + 热）均沿用 `ctx_checkpoints=-1`，未触发该问题
- 规避：**建议继续沿用 `ctx_checkpoints` 默认 `-1`**
- **✅ 官方推荐插件已修复**：[comfyui-sg-llama-cpp](https://github.com/allanmeng/comfyui-sg-llama-cpp) 已在 `1f0fc15` 将 `ctx_checkpoints` 默认改为 `-1` 并加响应式 `n_ctx` hint。使用此插件无需手动处理
- **本 wheel 本身无此 bug**：纯 `llama_cpp.Llama` 同模型同大图在 `n_ctx=8192` 下已验证正常

**🚀 实测性能（Qwen3.5-4B 视觉模型 + 图像，0.4.7，Intel Arc B580）：**

> ✅ 测试机为 **Intel Arc B580 Graphics**，驱动与 0.4.6 完全一致（SYCL 20.1 / `1.17.39894+4` / 160 CU / `Reorder=Y`），硬件侧无变量。**⚠️ 但热跑所用的图与 0.4.6 基线不是同一张**（0.4.7 为 **2336×1760 / 4015 tokens**，0.4.6 为 **1792×2304 / 4032 tokens**），因此**只对速率类指标做跨版本 Δ，不对图像编码与总耗时横比**。

| 指标 | 大图 2336×1760（热跑） | 大图 1792×2304（冷跑，仅备查） |
|------|------------------------|--------------------------------|
| 视觉 token 数 | 4015 | 4032 |
| 图像编码耗时 | **11233 ms**（clip_encode） | 26731 ms（clip_encode） |
| 图像解码耗时 | 1125 ms（1/2）+ 1451 ms（2/2） | 3935 ms（1/2）+ 3161 ms（2/2） |
| prompt eval | **1328.76 t/s**（3041.93 ms / 4042 tokens） | 31.59 t/s（128494.43 ms / 4059 tokens） |
| 生成速度 | **90.02 t/s**（eval 12897.76 ms / 1161 runs） | 90.53 t/s（eval 13774.83 ms / 1247 runs） |
| 总耗时 | 42.03 s | 191.62 s |
| load time | 131.20 ms | 66111.51 ms |
| SYCL 计算缓冲 | SYCL0 513.02 MiB / SYCL_Host 28.03 MiB | 同左 |

**与 0.4.6 的速率对比**（图像不同，只比速率类指标）：

| 项 | 0.4.6 | 0.4.7 | Δ |
|----|-------|-------|---|
| prompt eval（热跑） | 1330.03 t/s | **1328.76 t/s** | **持平（−0.10%）** |
| 生成速度（热跑） | 90.66 t/s | **90.02 t/s** | −0.71%（噪声内） |
| 生成速度（冷跑） | 89.89 t/s | **90.53 t/s** | +0.7%（噪声内） |
| SYCL 计算缓冲 | 513.02 / 28.03 MiB | 同左 | 一致 |

> 测试场景：Qwen3.5-4B-Uncensored-Q4_K_M + mmproj-BF16，hybrid 架构（含 SWA 层），`ctx_checkpoints=-1`，`n_ctx=8192`，`n_batch=2048`（大图按 `2048 + 1967` 两批喂入）。
>
> **本版为何没有提升 —— 这是预期结果，不是优化失效**：SYCL 侧 13 项改动逐项性质为打包修复（`#32005`）、显存分配防护（`#31285`）、线程安全与失败记忆化（`#31138`）、`CLAMP` 正确性（`#31784`）、精度语义对齐（`#31896`）、device-id 缓存微优化（`#31126` / `#32013`）、AOT（`#31873`）、MoE 调度（`#30156`）、Alchemist 专用解禁（`#31574`）、YaRN（`#30802`）、CPY 舍入精度（`#31465`）、`SWIGLU_OAI` f16（`#30857`）—— **没有一项面向 `mul_mat` 吞吐**。0.4.6 的 +5.9% 来自 `#31013` / `#31008` / `#31325` 那批 MMVQ 模板化，本版无同类提交。
>
> **生成速度两次独立读数高度一致**：冷跑 90.53、热跑 90.02，跨两种图像尺寸与两种 cache 状态偏差仅 **0.57%**，说明该指标稳定可复现；与 0.4.6 的 90.66 差异属测量噪声。
>
> **冷跑数据（191.62 s）不可用于横比**：首次加载全新 DLL 时 `load time` 66.1 s、`clip_encode` 26.7 s、`prompt eval` 31.59 t/s，原因是 Level Zero 的 program cache 全部失效、kernel 被全量重新 JIT。**该成本一次性**，第二次运行 `load time` 回落至 131 ms、`prompt eval` 恢复 1328.76 t/s。注意生成速度在冷跑时已属正常（decode 所需 kernel 在 encode 阶段就完成 JIT）。

**社区反馈：**

> ✅ **"Qwen 3.8 27B working fine with `llama_multimodal.GenericMTMDChatHandler`"** —— 视觉模型兼容性良好
> 详见：https://github.com/JamePeng/llama-cpp-python/discussions/169#discussioncomment-18036209

**安装包**：`llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl`（**43.13 MiB / 45,220,961 B**，md5 `cbede18e0214fadc5c980d773a9e43ac`，精简版，**需预装 oneAPI 2026.2** 且启动脚本必须保留 `setvars.bat`）

> 📥 **oneAPI 2026.2 下载**
>
> - 官方地址：https://www.intel.com/content/www/us/en/developer/tools/oneapi/oneapi-toolkit-download.html
> - 网盘备用：https://pan.quark.cn/s/be61433cc224
>
> 官方页是通用入口，下载器里请**手动选 2026.2**（别顺手装成更新或更旧的版本）；网盘那份是固定版本。安装前先完全退出 ComfyUI 等程序，装完**重启**，确认启动脚本仍有 `call setvars.bat` —— 日志出现 `GGML_SYCL_SUPPORT_LEVEL_ZERO_API: yes` 与 `[level_zero:gpu:0]` 才算正常，否则说明**静默回退到了 CPU**。

---

## 0.3.39+ 重要变更说明

### 1. llama-cpp-python-sycl-windows 在 0.3.39 之后发生了哪些变化

从 0.3.39 版本开始，llama-cpp-python 引入了重大的 **MTMD（Multi-Modal Token Decomposition）重写**，对视觉模型的支持方式做了底层重构：

| 变更项 | 0.3.38 及之前 | 0.3.39+ |
|--------|-------------|---------|
| 视觉模型加载方式 | 手动创建 `clip_model_path` handler 注入 `Llama()` | `mmproj_path` 直接传给 `Lama()`，内部自动创建 handler |
| 视觉 handler 类 | 模型特定 handler（如 `Qwen3VLChatHandler`） | `GenericMTMDChatHandler` 统一处理 |
| handler 参数传递 | 直接传给 handler 构造函数 | 通过 `chat_handler_kwargs` dict 传递 |
| 混合架构模型 | 无特殊处理 | 用默认 `ctx_checkpoints=-1`（如 Qwen3.5）；**勿传 `0`**，0.3.48+ 会触发 hybrid fast-path 首 decode 崩溃 |

### 2. 从 0.3.38 或更早版本升级的用户需要手工清理哪些内容

> **重要**：不要直接使用 `pip install --upgrade`，旧版本残留文件可能与新版冲突。请按以下步骤操作：

#### 步骤 1：完全卸载旧版本

```bat
pip uninstall llama-cpp-python -y
```

#### 步骤 2：安装新版本 whl

```bat
pip install llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl
```

#### 步骤 3：更新 ComfyUI 插件

如果你在 ComfyUI 中使用此 whl，必须使用适配 0.3.39+ 的插件版本（见下方第 3 节）。

### 3. 对应适配的 ComfyUI 插件

原版 `comfyui-sg-llama-cpp` 插件不支持 0.3.39+ 的 MTMD 重写。以下 fork 已完成适配：

**https://github.com/allanmeng/comfyui-sg-llama-cpp**

适配内容：
- **`clip_model_path` → `mmproj_path`**：直接传给 `Llama()`，不再手动创建 handler
- **`GenericMTMDChatHandler` 参数过滤**：取 `GenericMTMDChatHandler` ∪ `MTMDChatHandler` 参数并集，过滤掉 `force_reasoning`、`enable_thinking` 等 0.3.39+ 不接受的参数
- **新增 `ctx_checkpoints` 选项**（默认 `-1`）：混合架构模型（Qwen3.5 等 Transformer+Mamba）使用默认即可；**勿设为 `0`**，0.3.48+ 会触发 hybrid fast-path 首 decode 崩溃
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

- Intel 官方建议安装并使用最新 oneAPI / 显卡驱动，以确保 Intel Arc B580 / B70（Battlemage）的性能与兼容性。
- 0.3.43 的编译需要搭配 **Python XPU 运行时（`intel-xpu-backend-for-pytorch` / PyTorch XPU）≥ 2.13**（即 PyTorch 2.13 生态）。oneAPI 2026 与之在 ABI 与运行时层面匹配；若混用旧版 Python XPU 后端（如 2.12 + oneAPI 2025）可能导致运行时不匹配。

> **重要**：若你的 ComfyUI / 推理环境使用 PyTorch XPU 方案，请确保 `intel-xpu-backend-for-pytorch` **≥ 2.13**，与 0.3.43 的 oneAPI 2026 构建保持一致。

### 2. whl 打包方式：方案 A（精简版，不含 oneAPI 运行时）

自 0.3.45 起，发布的 whl 采用**方案 A（精简版）**：**不包含** oneAPI 运行时 DLL（`dnnl.dll`、`mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`、`tbb12.dll` 均已移除），whl 体积约 36–43 MB。

> **🆕 自 0.4.7 起剔除项增至 6 个**：新增 **`mkl_intel_thread.3.dll`**（38.95 MiB）—— oneAPI 2026.2 编出的 `ggml-sycl.dll` 新增依赖它。若不剔除，whl 会从 43 MB 膨胀到约 84 MB。**该 DLL 与其他被剔除项一样由目标机的 oneAPI 提供**，因此启动脚本里的 `setvars.bat` 不可省略。

因此部署目标机 **必须预先安装 Intel oneAPI**（SYCL 核心运行时 `sycl9.dll` / `OpenCL.dll` 及上述数值库由 oneAPI 提供）。

> **⚠️ 注意**：`libomp140.x86_64.dll` **保留在 whl 中**（OpenMP 预加载修复依赖），不可删除。

若目标机未安装 oneAPI，SYCL 运行时无法加载，推理会失败。请先按下方「前置要求」安装 oneAPI Base Toolkit。

### 3. 已安装 oneAPI Toolkit 的用户（默认即精简版，无需再删）

方案 A 的 whl 本身已不含 oneAPI 冗余 DLL，目标机安装 oneAPI 后这些运行时由 oneAPI 经 `setvars.bat` 或系统 PATH 提供。whl 内仅保留 `libomp140.x86_64.dll`（必需）。

> 若你从旧版（0.3.43/0.3.44 自包含 whl）升级，site-packages 里可能残留旧版 oneAPI DLL，建议先 `pip uninstall` 清理再装新版。

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
| Intel oneAPI DPC++/C++ Compiler | 提供 SYCL 编译器（icx）与 `OpenCL.dll` |
| Intel oneAPI DPC++ Library | 提供 `sycl9.dll` 运行时（oneAPI 2026.2） |
| Intel oneAPI Math Kernel Library (oneMKL) | 提供 `mkl_core.3.dll`、`mkl_sycl_blas.6.dll`、`mkl_tbb_thread.3.dll`，以及 **0.4.7 起新依赖的 `mkl_intel_thread.3.dll`** |
| Intel oneAPI Deep Neural Network Library (oneDNN) | 提供 `dnnl.dll` |
| Intel oneAPI Threading Building Blocks (oneTBB) | 提供 `tbb12.dll` |

下载 Intel oneAPI Base Toolkit（安装时选择自定义安装）：
https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html

> **提示：** 安装时选择「自定义安装」，只勾选上表中的这几个组件，可节省大量磁盘空间。oneAPI 2025+ 中 **DPC++ Library** 是独立于 Compiler 的组件，需单独勾选。

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

从 [Releases](https://github.com/allanmeng/llama-cpp-python-sycl-windows/releases) 页面下载。

---

## 安装方法

### 方法一：pip 安装（推荐）

```bat
pip uninstall llama-cpp-python -y
pip install llama_cpp_python-0.4.7+sycl-cp313-cp313-win_amd64.whl
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

> **注意（自 0.3.43 起）**：`llama_cpp` 在导入时会自动将自身 `lib/` 目录注册到 DLL 搜索路径（继承上游 0.3.42 的 Windows DLL 搜索修复）。因此 **通常情况下，ComfyUI 中不再需要放置 `sycl-preloader` 插件**。以下内容仅供需要兼容 0.3.42 及更早版本，或自定义部署环境的用户参考。

> **另注（自 0.3.45 起）**：whl 采用方案 A（精简版），**不再自带** oneAPI 运行时 DLL；但仍会自动注册自身 `lib/` 目录，且目标机需预装 oneAPI（见上文「whl 打包方式」）。

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
| `ctx_checkpoints` | `-1`（默认；混合架构模型如 Qwen3.5 用默认即可，**勿设 `0`**——0.3.48+ 会触发 hybrid fast-path 首 decode 崩溃） |
| `vision_image_min_tokens` | `1024`（Qwen-VL 最低要求） |
| `vision_image_max_tokens` | `-1`（使用默认值） |

---

## 已知限制

- Intel Arc（SYCL0）的 Flash Attention 通过 **oneDNN 路径**实现（`GGML_SYCL_DNNL`，默认开启）：B 系列（B580/B70 等）实测 `GGML_SYCL_ENABLE_FLASH_ATTN` / `GGML_SYCL_FA_ONEDNN` / `GGML_SYCL_ENABLE_MKL_FA` 均为开启；上游对 **A 系列（Alchemist）** 做了 oneDNN 特性 gate，A 系列上该路径不可用。无论哪种情况，显存占用都高于 CUDA 方案
- 部分 CLIP 图计算算子会回退到 CPU，视觉编码性能受限
- Qwen3.5-2B（混合/循环架构）可能导致不稳定，建议改用 Qwen3-2B

---

## 测试环境

| 项目 | 版本 |
|------|------|
| 显卡 | Intel Arc B580 Graphics（160 CU / 12526 MB / `Reorder=Y`） |
| 驱动 | SYCL 20.1 / driver `1.17.39894+4` |
| 操作系统 | Windows 11 x64 |
| Python | 3.13.11 |
| oneAPI | **2026.2.0 Build 20261001**（icx，clang 23） |
| ComfyUI | 0.33.2 |

---

## 致谢

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) by abetlen
- [JamePeng 的 SYCL 分支](https://github.com/JamePeng/llama-cpp-python)
- [llama.cpp](https://github.com/ggml-org/llama.cpp) by ggml-org
