# Changelog

## [0.3.31+sycl] - 2026-03-07

### Added
- Upgraded to llama-cpp-python 0.3.31
- Bundled full oneAPI runtime DLLs for standalone deployment (no oneAPI installation required)
- Added `ur_loader.dll`, `ur_adapter_level_zero.dll`, `ur_adapter_level_zero_v2.dll`, `ur_win_proxy_loader.dll`
- Added `ur_adapter_opencl.dll`, `libiomp5md.dll`, `libhwloc-15.dll`
- Added `umf.dll`, `tcm.dll`, `ggml-rpc.dll`, `svml_dispmd.dll`
- Support for `Qwen25VLChatHandler` and `Qwen3VLChatHandler`

### Fixed
- Removed duplicate DLLs from `bin/` and `lib/` subdirectories

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified

---

## [0.3.30+sycl] - 2026-03-07

### Added
- Initial release
- llama-cpp-python 0.3.30 compiled with SYCL support
- Intel Arc GPU acceleration via Intel oneAPI
- Verified working on Intel Arc B580 (Battlemage)
- Full oneAPI runtime DLLs bundled

### Environment
- Python 3.13.11
- Intel oneAPI 2025.3.2
- Intel Arc B580 (Battlemage) verified
