import os, zipfile
from pathlib import Path

src = Path(r'F:\ComfyUI-aki-v3\python\Lib\site-packages\llama_cpp')
out = Path(r'D:\projects\llama-cpp-python-sycl-windows\whl\llama_cpp_python-0.3.43+sycl+pr25741+oneapi2610-cp313-cp313-win_amd64.whl')

excludes = {'__pycache__', 'include'}
files = []
for f in src.rglob('*'):
    if f.is_file():
        parts = f.relative_to(src).parts
        if any(p in excludes for p in parts):
            continue
        if f.suffix == '.pyc':
            continue
        files.append(f)

print(f'共 {len(files)} 个文件')

sp = src.parent
dist_info_src = None
for d in sp.iterdir():
    if d.name.startswith('llama_cpp_python-') and d.suffix == '.dist-info':
        dist_info_src = d
        break

if dist_info_src:
    print(f'找到 dist-info: {dist_info_src.name}')
else:
    print('未找到 dist-info，将跳过')

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in files:
        arcname = 'llama_cpp/' + '/'.join(f.relative_to(src).parts)
        zf.write(f, arcname)
    if dist_info_src:
        for f in dist_info_src.rglob('*'):
            if f.is_file():
                arcname = dist_info_src.name + '/' + '/'.join(f.relative_to(dist_info_src).parts)
                zf.write(f, arcname)

print(f'打包完成: {out}')
print(f'文件大小: {out.stat().st_size / 1024 / 1024:.1f} MiB')