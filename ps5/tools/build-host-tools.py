#!/usr/bin/env python3
"""Cross-build the portable SELF packer from pinned Vulkan/zlib sources with Zig."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--zig', type=Path, required=True)
p.add_argument('--vulkan', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--target', action='append', choices=['linux-x86_64', 'linux-arm64', 'windows-x86_64', 'windows-arm64', 'macos-x86_64', 'macos-arm64'])
a = p.parse_args()
zig = str(a.zig.resolve())
native = a.vulkan.resolve()/'tooling/native'
zlib = a.vulkan.resolve()/'.deps/native/zlib/zlib-1.3.2'
targets = {'linux-x86_64':'x86_64-linux-musl', 'linux-arm64':'aarch64-linux-musl',
           'windows-x86_64':'x86_64-windows-gnu', 'windows-arm64':'aarch64-windows-gnu',
           'macos-x86_64':'x86_64-macos', 'macos-arm64':'aarch64-macos'}
for name in a.target or targets:
    target = targets[name]
    work = a.output.resolve()/name
    work.mkdir(parents=True, exist_ok=True)
    sources = ['adler32','compress','crc32','deflate','gzclose','gzlib','gzread','gzwrite',
               'infback','inffast','inflate','inftrees','trees','uncompr','zutil']
    def compile_one(source):
        subprocess.run([zig,'cc','-target',target,'-O2','-I',str(zlib),'-c',str(zlib/(source+'.c')),
                        '-o',str(work/(source+'.o'))],check=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(compile_one, sources))
    output = work/('ps5-native-tool.exe' if name.startswith('windows') else 'ps5-native-tool')
    subprocess.run([zig,'c++','-target',target,'-std=c++20','-O2','-I',str(zlib),
                    *[str(native/file) for file in ['native_app_builder.cpp','self_container.cpp','elf_object.cpp','sce_module_writer.cpp']],
                    *[str(work/(source+'.o')) for source in sources],'-o',str(output)],check=True)
    print(output,flush=True)
