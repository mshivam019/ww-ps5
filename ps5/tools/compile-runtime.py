#!/usr/bin/env python3
"""Cross-compile the PS5 runtime using placeholder game code, without executing it."""
import argparse
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def run(*args):
    subprocess.run(list(map(str, args)), check=True)
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--sdl-build', type=Path, required=True)
    parser.add_argument('--vulkan-headers', type=Path, required=True)
    parser.add_argument('--generated', type=Path, help='Actual recompiler output; omit for placeholders')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    generated = args.generated.resolve() if args.generated else ROOT / 'build/gen-stub'
    build = ROOT / 'build/ps5-runtime'
    if not args.generated:
        run('python3', ROOT / 'tools/recomp/stubgen.py', generated)
    run('cmake', '-S', ROOT, '-B', build, '-G', 'Ninja',
        f'-DCMAKE_TOOLCHAIN_FILE={args.sdk.resolve()}/toolchain/prospero.cmake',
        '-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY', '-DCMAKE_BUILD_TYPE=Release',
        f'-DGEN_DIR={generated}', f'-DSDL3_DIR={args.sdl_build.resolve()}',
        f'-DPS5_VULKAN_HEADERS={args.vulkan_headers.resolve()}')
    run('cmake', '--build', build, '--target', 'wwhd', '--parallel', args.jobs)
    print('Runtime archive compiled. Final native link and console validation are still required.')
if __name__ == '__main__':
    main()
