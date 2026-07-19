import os

# 复刻 sycl-preloader 行为：把当前进程 PATH 中的 oneAPI 目录注册进 DLL 搜索路径
# （Windows Python 3.8+ 无视 PATH 加载 DLL，必须显式 add_dll_directory）
for p in os.environ.get("PATH", "").split(";"):
    p = p.strip()
    if p and os.path.isdir(p):
        try:
            os.add_dll_directory(p)
        except Exception:
            pass

from llama_cpp.llama_chat_format import (
    Qwen3VLChatHandler,
    Qwen25VLChatHandler,
    GenericMTMDChatHandler,
)

print("handlers OK")
