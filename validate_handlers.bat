@echo off
call "F:\Intel-oneAPI\setvars.bat" --force
"F:\ComfyUI-aki-v3\python\python.exe" "D:\projects\llama-cpp-python-sycl-windows\validate_handlers.py"
