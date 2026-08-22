#!/usr/bin/env python
# test_mtmd_large_image.py
# 纯 llama-cpp-python 复现 MTMD 视觉推理（绕过任何 ComfyUI 插件），
# 用于隔离"插件问题" vs "llama.cpp 核心问题"。
#
# 用法（用目标 python 跑，或走 test_mtmd_large_image.bat 自动 setvars）：
#   python test_mtmd_large_image.py <model.gguf> <image.png> [mmproj.gguf] [prompt]
#   # 顺带验证规避手段（swa_full 走标准 KV cache）：追加 --swa-full
#   python test_mtmd_large_image.py <model.gguf> <image.png> <mmproj.gguf> --swa-full
#
# 说明：mmproj 为可选参数；以 .gguf/.bin 结尾的额外位置参数会被当作 clip_model_path。
#
# 判读：
#   - 默认模式也崩（failed to prepare attention ubatches / failed to find a memory slot）
#     => 核心 llama.cpp hybrid 内存后端 bug，与插件无关
#   - 默认模式正常、--swa-full 也正常 => 进一步坐实是 hybrid 后端触发，swa_full 可规避
#   - 默认模式正常 => 之前是插件调用方式的问题（需对齐插件参数）

import sys
import os
import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import GenericMTMDChatHandler


def run(model_path, image_path, clip_model_path, prompt, swa_full):
    n_ctx = int(os.environ.get("N_CTX", "8192"))
    print(f"[test] model        = {model_path}")
    print(f"[test] image        = {image_path}")
    print(f"[test] clip_model   = {clip_model_path}")
    print(f"[test] swa_full     = {swa_full}")
    print(f"[test] n_ctx        = {n_ctx}")

    # 0.3.48 破坏性签名变更：GenericMTMDChatHandler(chat_format, mmproj_path, verbose=True, ...)
    # chat_format=None 时由模型自身 chat_template 解析；mmproj_path 为必填（视觉投影器）。
    handler = GenericMTMDChatHandler(
        chat_format=None,
        mmproj_path=clip_model_path,
        verbose=True,
    )
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=-1,
        chat_handler=handler,
        vision=True,
        swa_full=swa_full,   # 仅 hybrid/SWA 模型有效；标准 KV cache 路径不受影响
        verbose=True,
    )

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    print("[test] sending chat completion with image ...")
    resp = llm.create_chat_completion(
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        max_tokens=512,
    )
    print("[test] RESPONSE:")
    print(resp["choices"][0]["message"]["content"])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) < 2:
        print("Usage: python test_mtmd_large_image.py <model.gguf> <image.png> [mmproj.gguf] [prompt] [--swa-full]")
        sys.exit(1)
    model_path = args[0]
    image_path = args[1]
    # 额外位置参数：以 .gguf/.bin 结尾的视为 clip_model_path，否则视为 prompt
    clip_model_path = None
    prompt = "用中文详细描述这张图片的内容"
    for a in args[2:]:
        if a.lower().endswith((".gguf", ".bin")):
            clip_model_path = a
        else:
            prompt = a
    swa_full = "--swa-full" in flags
    run(model_path, image_path, clip_model_path, prompt, swa_full)


if __name__ == "__main__":
    main()
