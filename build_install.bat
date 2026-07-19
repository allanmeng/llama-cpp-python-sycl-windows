@echo off
set "VS2022INSTALLDIR=D:\Microsoft Visual Studio\2022\BuildTools"
call "F:\Intel-oneAPI\setvars.bat" --force
set "CMAKE_GENERATOR=Ninja"
set "CMAKE_ARGS=-DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=on -DGGML_ONEDNN=off -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_TARGET=INTEL -Wno-dev"
cd /d "D:\projects\llama-cpp-python-sycl-windows\llama-cpp-python"
"F:\ComfyUI-aki-v3\python\python.exe" -m pip install . --no-build-isolation --no-deps --force-reinstall --no-cache-dir
echo === BUILD_INSTALL_EXIT=%ERRORLEVEL% ===
