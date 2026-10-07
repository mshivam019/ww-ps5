#!/usr/bin/env python3
"""Link a complete native PS5 title from actual recompiler output and the runtime."""
import argparse
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[2]
def run(*args): subprocess.run(list(map(str, args)), check=True)
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--sdl-build', type=Path, required=True)
    parser.add_argument('--sdl-source', type=Path, required=True)
    parser.add_argument('--vulkan', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    sdk, sdl, vulkan = args.sdk.resolve(), args.sdl_build.resolve(), args.vulkan.resolve()
    run('python3', ROOT / 'ps5/tools/compile-runtime.py', '--sdk', sdk,
        '--sdl-build', sdl, '--vulkan-headers', vulkan / '.deps/native/radv-release/include',
        '--generated', ROOT / 'build/gen', '--jobs', args.jobs)
    work = ROOT / 'build/native-game'; work.mkdir(parents=True, exist_ok=True)
    run(sdk / 'bin/prospero-clang++', '-std=c++20', '-O2', '-I', args.sdl_source.resolve() / 'include',
        '-c', ROOT / 'ps5/main.cpp', '-o', work / 'main.o')
    run(sdk / 'bin/prospero-clang', '-std=c11', '-O2', '-c', ROOT / 'ps5/native/platform.c',
        '-o', work / 'platform.o')
    build = ROOT / 'build/ps5-runtime'
    # HLE implementations and their static registrations must all be present;
    # otherwise weak generated imports can hide missing runtime object files.
    runtime = build / 'libwwhd.a'
    dependencies = sorted(p for p in build.rglob('*.a')
                          if p != runtime and p.name not in {'libz.a', 'libzlibstatic.a', 'libzlib.a'})
    run('bash', ROOT / 'ps5/tools/link-game.sh', work, vulkan, sdk,
        work / 'main.o', work / 'platform.o', '--whole-archive', runtime, '--no-whole-archive',
        '--start-group', *dependencies, sdl / 'libSDL3.a', '--end-group')
    print(work / 'eboot.bin')
if __name__ == '__main__': main()
