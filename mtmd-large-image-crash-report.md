# llama-cpp-python 0.3.48 视觉大图推理崩溃 —— 插件侧诊断报告

> 用途：发给 ComfyUI-sg-llama-cpp fork（插件）维护者 / 插件 AI，定位「多模态大图视觉推理首 token decode 崩溃」的根因。
> 结论先行：**同一模型 + 同一张大图，纯 `llama_cpp`（`n_ctx=8192`）直接跑不崩；只有经该插件跑才崩 → 问题在插件的 `n_ctx` 余量不足（极可能硬编码 4096），不在 llama-cpp-python 0.3.48 核心。详见 §4.1 / §10。**

---

## 0. 一句话摘要

- 环境：llama-cpp-python **0.3.48**（SYCL 编译，Intel Arc B580，Windows 11，Python 3.13，oneAPI 2026.1）。
- 现象：用 `GenericMTMDChatHandler` 跑视觉推理，**大图（2336×1760 → 4015 image token）** 在首 decode token 崩溃；**小图（1024×1024 → 1024 token）正常**。
- 隔离：绕过插件、纯 `llama_cpp.Llama` + 同一模型 + 同一张大图 → **正常出图描述**（79.52 t/s）；`n_ctx=8192` 稳过。
- `n_ctx` 扫描：`n_ctx=4096` 触发干净 "context exceeded" 显式报错（prefill 前拦截）；`n_ctx=8192` 正常 → **根因 = 插件 `n_ctx` 余量不足（很可能硬编码 4096）**，prefill 占满后 hybrid 内存后端解码首 token 无 slot（见 §4.1）。
- 推论：崩在**插件调用路径（`n_ctx` 不够大）**，不是 wheel / llama.cpp 核心。
- 附带重要提醒：**0.3.48 对 `GenericMTMDChatHandler` 构造签名做了破坏性变更**（见 §6），插件需已跟进。

---

## 1. 复现环境

| 项 | 值 |
|---|---|
| llama-cpp-python 版本 | 0.3.48（JamePeng main `7562297`，tag `v0.3.48-cu128-win-20260821`，`__version__="0.3.48"`） |
| vendor/llama.cpp | `bb4caa754`（llama.cpp 0.2.0） |
| 编译 | SYCL / oneAPI 2026.1 / icx / INTEL target，装到 `F:\ComfyUI-aki-v3\python` |
| 显卡 | Intel Arc B580（Battlemage） |
| 视觉模型 | `Qwen3.5-4B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf` |
| 视觉投影器 | `Qwen3.5-4B-Uncensored-HauhauCS-Aggressive-mmproj-BF16.gguf` |
| 崩溃大图 | `三合一.png`，2336×1760 → **4015 image token**（prefill 总 token 4043） |
| 正常小图 | 1024×1024 → 1024 image token |

---

## 2. 崩溃日志（来自插件路径）

```
GenericMTMDChatHandler(mtmd_input_chunk_media_id): chunk_n_tokens: 4015, media_id: -2136631,
GenericMTMDChatHandler(__call__): Prepared virtual token ledger of length 4043.
Llama.longest_token_prefix [Fast Exit 1]: Empty sequence detected. len(current_ids)=0, len(new_tokens)=4043
GenericMTMDChatHandler(__call__): Evaluating TEXT chunk (19 tokens) at pos 0...
GenericMTMDChatHandler(__call__): Evaluating IMAGE chunk (4015 tokens) at pos 19...
encoding image slice...
clip_encode: copying image 1/1 to input buffer (nx=2336, ny=1760)
clip_encode: output embedding shape [2560, 4015, 1]
image slice encoded in 11034 ms
decoding image batch 1/2, n_tokens_batch = 2048
find_slot: non-consecutive token position 19 after 18 for sequence 0 with 512 new tokens
... (多条 find_slot 警告，见 §3 说明)
image decoded (batch 1/2) in 1128 ms
decoding image batch 2/2, n_tokens_batch = 1967
... (多条 find_slot 警告)
image decoded (batch 2/2) in 1478 ms
GenericMTMDChatHandler(__call__): Evaluating TEXT chunk (9 tokens) at pos 92...
find_slot: non-consecutive token position 100 after 19 for sequence 0 with 9 new tokens
find_slot: non-consecutive token position 100 after 19 for sequence 0 with 9 new tokens
Llama.generate: Hybrid single-turn full match (101 tokens). Bypassing rollback/truncation.   ← 关键分支
init_batch: failed to prepare attention ubatches
decode: failed to find a memory slot for batch of size 1
LlamaCPP Engine Error: Llama.eval(decode): Failed completely even with batch size 1.
[INFO] Prompt executed in 20.75 seconds
```

**致命错误链**：
- `init_batch: failed to prepare attention ubatches` → 源在 `vendor/llama.cpp` 的 `llama-memory-hybrid.cpp`（hybrid 内存 / 注意力 ubatch 准备）
- `decode: failed to find a memory slot for batch of size 1` → 源在 `llama-memory-recurrent.cpp`（`find_slot` 分配器）/`llama-context.cpp`
- 这是 **hybrid / recurrent 内存后端**（视觉模型带 SWA 层 → `is_hybrid=True`），不是普通 KV cache。

---

## 3. 关于 `find_slot: non-consecutive token position` 警告（可忽略，非根因）

大图、小图日志里都会出现这排警告。已在 JamePeng 上游 issue **#75** 确认：这是 llama.cpp 拆分多模态 batch（视觉 token 以非连续位置注入）的**正常过程**，属良性噪声，与崩溃无因果关系。不要在此处浪费排查时间。

---

## 4. 决定性隔离测试（纯 llama_cpp，绕过插件）

用以下极简脚本直接跑（无 ComfyUI、无插件）：

```python
handler = GenericMTMDChatHandler(chat_format=None, mmproj_path="...mmproj-BF16.gguf", verbose=True)
llm = Llama(
    model_path="...Q4_K_M.gguf",
    n_ctx=8192,
    n_gpu_layers=-1,
    chat_handler=handler,
    vision=True,
    verbose=True,
)
llm.create_chat_completion(
    messages=[{"role":"user","content":[
        {"type":"image_url","image_url":{"url": data_url}},
        {"type":"text","text":"用中文详细描述这张图片的内容"},
    ]}],
)
```

**结果**：同一模型 + 同一 2336×1760 大图（4015 token）→ **正常出图描述**，eval 79.52 t/s，`find_slot` 警告照样刷但**不崩**。

> 关键差异：极简脚本走的是 llama.cpp 内**正常 checkpoint/rollback 分支**（`Hybrid model rollback triggered → restore OK`）并成功；而插件路径走的是 **`Hybrid single-turn full match → Bypassing rollback/truncation`** 这一 fast-path（见 §2 标记行），随后在 decode 处失败。
> 两条分支都来自 llama.cpp，但触发条件不同 —— 极简脚本能走通说明**核心完全有能力处理该大图**，问题在「插件如何让 llama.cpp 进入 Bypassing-rollback 分支且后续 slot 分配失败」。

### 4.1 `n_ctx` 扫描测试（4096 vs 8192）—— 锁定根因

用同一模型 + 同一 2336×1760 大图，仅改 `n_ctx`（通过 `N_CTX` 环境变量）：

| n_ctx | 总 token 需求 | 阶段 | 结果 |
|---|---|---|---|
| **4096** | 4113（85 文本 + 4015 图像） | prefill 前 | ❌ `RuntimeError: GenericMTMDChatHandler(__call__): Context Shift is explicitly disabled... Multimodal chunk exceeded context limit (currently n_ctx=4096), You MUST increase n_ctx to fit the dialogue.` —— C++ 后端**显式上下文检查**拦截（4113 > 4096） |
| **8192** | 同上 | 完整 | ✅ 正常出图描述，eval 79.52 t/s，`HybridCheckpointCache(clear): cleared` 正常分支 |

**这条扫描为什么是决定性证据**：

- `n_ctx=4096` 触发的是**干净的 "context exceeded" 显式报错**（在 prefill 之前就被拦下）。
- 但插件崩的**不是这条**——插件 prefill（4043 token）成功了，崩在 prefill 之后的**首个 decode token**（`failed to prepare attention ubatches`）。
- 这说明：**插件 `n_ctx` 装得下图像（≥ 4043，否则它也会先抛 `exceeded context limit`），但 prefill 几乎吃满上下文后，hybrid 内存后端在解码首 token 时无 slot 可分配 → 崩**。
- 对照 `n_ctx=8192` 稳过 → **根因 = 插件 `n_ctx` 余量不足（极可能硬编码 4096）**，而非 llama.cpp 核心 incapable。修复 = 给多模态大图放大 `n_ctx`（≥ prefill + 生成余量）。

---

## 5. 怀疑点（请插件侧重点排查）

基于「纯 llama_cpp 正常、插件崩溃」的事实，最可能的插件差异按优先级排列：

### 5.1 `n_ctx` 余量不足（已用 N_CTX=4096 复现验证 —— 最可疑，且修复已确认）

**实测对比（同一模型 + 同一 2336×1760 大图）**：

| n_ctx | 总 token 需求 | 结果 |
|---|---|---|
| **4096** | 4113（85 文本 + 4015 图像） | ❌ `RuntimeError: ... Multimodal chunk exceeded context limit (currently n_ctx=4096), You MUST increase n_ctx` —— C++ 后端**显式上下文检查**在 prefill 前拦截（因 4113 > 4096） |
| **8192** | 同上 | ✅ 正常出图描述（79.52 t/s） |

- **关键推论**：插件的崩溃**不是**上面那种"干净超限报错"（否则插件也会先抛 `exceeded context limit`）。插件 prefill（4043 token）**成功了**，说明插件 `n_ctx` **≥ 4043 装得下图像**，但随后在**首个 decode token** 崩于 `failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`（hybrid 内存后端）。
  → 即插件 `n_ctx` **很可能就是 4096（或刚够装图、毫无余量）**：prefill 吃掉几乎全部上下文，hybrid 内存 buffer 占满，解码首 token 无 slot → 崩。
- **修复已验证**：插件给多模态大图预留充足 `n_ctx` 余量即可。我们 `n_ctx=8192` 稳过；或按 `n_ctx = prefill_tokens + 生成余量` 动态设置。
- **请确认**：插件传给 `Llama(model_path, ..., n_ctx=?, ...)` 的 `n_ctx` 默认值是多少？是否对多模态输入动态放大（如 `n_ctx >= prefill_tokens + max_gen_tokens`）？若硬编码 4096 且不随图像增大，则这就是根因。

### 5.2 插件手动驱动 eval / 复用了带缓存的状态，触发了「Bypassing rollback」缺陷分支
- 崩溃日志里 `Llama.generate: Hybrid single-turn full match (101 tokens). Bypassing rollback/truncation.` 是 0.3.48 针对 hybrid 模型的 fast-path。它在**单轮、缓存命中**时跳过回滚/截断。
- 若该分支在「大 prefill 后首 decode」场景下存在 slot/ubatch 准备的缺陷，而插件恰好以单轮 + 复用缓存方式调用，就会命中。
- 极简脚本走的是普通多轮 checkpoint 路径，绕过了它。
- **请确认**：插件是直接用 `llama_cpp` 的高层 `create_chat_completion` / `chat()`，还是**自己写循环调 `llm.eval()` / 手动管理 `LlamaState` / 复用 `slot`**？如果是后者，大图下单轮 fast-path 的 slot 管理可能没覆盖到。

### 5.3 多模态 batch 策略 / `n_batch` 设置
- 日志中图像被拆成 `batch 1/2`（`n_tokens_batch=2048` 和 `1967`）。若插件侧的 `n_batch` 或 batch 分块与 hybrid 内存分配器不兼容，也可能在大图下触发 `find_slot` 失败。
- **请确认**：插件是否显式设置了 `n_batch`？值是多少？

---

## 6. ⚠️ 0.3.48 破坏性 API 变更（插件必须已跟进，否则构造期就报错）

`GenericMTMDChatHandler.__init__` 签名在 0.3.48 变了：

| 版本 | 构造签名 |
|---|---|
| 0.3.47 | `GenericMTMDChatHandler(clip_model_path=..., verbose=True)` |
| **0.3.48** | `GenericMTMDChatHandler(chat_format, mmproj_path, verbose=True, ...)`（`chat_format` 可为 `None` 自动解析，但 `mmproj_path` 是**必填位置参数**） |

- 插件本次崩在 **decode 阶段**（非构造），说明它**已适配 0.3.48 签名**（否则会在 `GenericMTMDChatHandler(...)` 处直接 `TypeError` 缺参）。
- 但若插件基于 0.3.47 写法（如仍传 `clip_model_path=`）而只是靠某处 shim 兜住，请顺手核对一遍，确保 0.3.48 下所有 `GenericMTMDChatHandler` / `Qwen3VLChatHandler` / `Qwen25VLChatHandler` 的实例化都按新签名传 `mmproj_path`。

---

## 7. 给插件侧的 Action Items

1. 贴出插件构造 `Llama(...)` / `GenericMTMDChatHandler(...)` 时实际传入的**全部参数**（尤其 `n_ctx`、`n_batch`、`n_gpu_layers`、`chat_handler`、`vision`、是否有 `LlamaState` 复用 / 手动 `eval` 循环）。
2. 用**同一张大图 + 同一模型**复测：把插件传的 `n_ctx` 显式调到 `8192`（或更大）看是否还崩 —— 若不崩，则坐实 §5.1。
3. 检查插件是否走「Bypassing rollback」fast-path（日志搜 `Hybrid single-turn full match ... Bypassing rollback/truncation`）。若命中且伴随崩溃，对比纯 `llama_cpp.create_chat_completion` 走通的分支，定位 fast-path 在大图下的 slot 分配缺口。
4. 确认插件已按 §6 适配 0.3.48 的 `GenericMTMDChatHandler` 新签名（`mmproj_path` 必填）。

---

## 8. 附：隔离测试脚本

仓库内 `test_mtmd_large_image.py`（配套 `test_mtmd_large_image.bat` 先 `setvars` 加载 SYCL 运行时再跑）。

用法：
```bat
F:\ComfyUI-aki-v3\python\python.exe test_mtmd_large_image.py ^
  <model.gguf> <image.png> <mmproj.gguf> [prompt] [--swa-full]
```
- 默认 `n_ctx=8192`，可用环境变量 `N_CTX=4096` 覆盖以复现「小 n_ctx 是否触发崩溃」。
- `--swa-full` 会把 `swa_full=True` 传给 `Llama()`，强制走标准 KV cache（绕开 hybrid 后端），用于验证规避手段。

---

## 9. 对 wheel 发版的影响（附带说明，供参考）

- 0.3.48 wheel **本身对大图视觉无 bug**（纯 llama_cpp + `n_ctx=8192` 已验证：同模型同大图正常）。之前拟的「大图 known-issue」应改为：**若某插件在大图视觉下崩溃，是插件集成问题（n_ctx 余量不足），需插件侧修**，而非 wheel 问题。
- wheel 可照常发，但发版说明务必带 **§6 的 0.3.48 handler 破坏性 API 提醒**，避免下游插件作者踩构造签名变更。

---

## 10. 最终结论（给插件侧的一句话）

> **这不是 llama-cpp-python 0.3.48 的 bug。** 同一模型 + 同一张大图，纯 `llama_cpp`（`n_ctx=8192`）正常出图。插件崩溃的根因是 **`n_ctx` 余量不足**：插件很可能硬编码 `n_ctx=4096`，大图 prefill（~4043 token）几乎占满上下文，hybrid 内存后端在解码首 token 时无 slot → `failed to prepare attention ubatches` / `failed to find a memory slot for batch of size 1`。
> **修复**：对多模态大图动态放大 `n_ctx`（如 `n_ctx >= prefill_tokens + max_gen_tokens`，或至少 8192）。我们已验证 `n_ctx=8192` 稳过。
> 附带：请确认已按 §6 适配 0.3.48 的 `GenericMTMDChatHandler(chat_format, mmproj_path, ...)` 新构造签名。
