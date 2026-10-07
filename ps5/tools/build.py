#!/usr/bin/env python3
"""Build and package a private PS5 title from an extracted USA version 0 game."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def run(*args):
    subprocess.run(list(map(str, args)), check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--setup', action='store_true')
    p.add_argument('--build-radv', action='store_true')
    p.add_argument('--sdk', type=Path, default=ROOT/'.deps/native/ps5-payload-sdk')
    p.add_argument('--vulkan', type=Path, default=ROOT/'.deps/src/vulkan')
    p.add_argument('--sdl-source', type=Path, default=ROOT/'.deps/src/SDL')
    p.add_argument('--ps-prompts-archive', type=Path)
    p.add_argument('--jobs', type=int, default=4)
    a = p.parse_args()
    if a.jobs < 1: p.error('--jobs must be positive')
    if a.output.exists(): p.error('--output must be a new directory')
    game = a.game.resolve()
    if hashlib.sha256((game/'code/cking.rpx').read_bytes()).hexdigest() != 'c4f0ab300542e0bfc462696850534e71db2ad02288a7eb55e5a4cd4062f16153':
        p.error('Only the USA version 0 RPX is supported')
    if a.setup:
        cmd = [sys.executable, ROOT/'ps5/tools/setup-deps.py', '--vulkan-dir', a.vulkan]
        if a.vulkan == ROOT/'.deps/src/vulkan': cmd = cmd[:-2]
        if a.build_radv: cmd += ['--build-radv']
        run(*cmd)
    sdk, vulkan, sdl = a.sdk.resolve(), a.vulkan.resolve(), a.sdl_source.resolve()
    pins = json.loads((ROOT/'ps5/dependencies.json').read_text())
    revision = subprocess.check_output(['git', '-C', str(sdl), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != pins['sdl3']['revision']: raise RuntimeError('SDL source differs from the tested pin')
    sdl_build = ROOT/'build/sdl3-ps5'
    options = dict(SDL_SHARED='OFF', SDL_STATIC='ON', SDL_TEST_LIBRARY='OFF', SDL_TESTS='OFF',
        SDL_UNIX_CONSOLE_BUILD='ON', SDL_X11='OFF', SDL_WAYLAND='OFF', SDL_KMSDRM='OFF',
        SDL_AUDIO='ON', SDL_JOYSTICK='ON', SDL_JOYSTICK_VIRTUAL='ON', SDL_HAPTIC='ON',
        SDL_SENSOR='ON', SDL_HIDAPI='OFF', SDL_DUMMYAUDIO='OFF', SDL_DISKAUDIO='OFF',
        SDL_CAMERA='OFF', SDL_DIALOG='OFF', SDL_TRAY='OFF', SDL_VULKAN='OFF',
        SDL_OPENGL='OFF', SDL_OPENGLES='OFF', LIBC_HAS_WCSNLEN='OFF',
        LIBC_HAS_WCSLCPY='OFF', LIBC_HAS_WCSLCAT='OFF')
    run('cmake', '-S', sdl, '-B', sdl_build, '-G', 'Ninja',
        f'-DCMAKE_TOOLCHAIN_FILE={sdk}/toolchain/prospero.cmake',
        '-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY', '-DCMAKE_BUILD_TYPE=Release',
        *[f'-D{k}={v}' for k,v in options.items()])
    run('cmake', '--build', sdl_build, '--target', 'SDL3-static', '--parallel', a.jobs)
    run(sys.executable, ROOT/'tools/recomp/recomp.py', game/'code/cking.rpx', ROOT/'build/gen')
    run(sys.executable, ROOT/'ps5/tools/build-native.py', '--sdk', sdk, '--sdl-build', sdl_build,
        '--sdl-source', sdl, '--vulkan', vulkan, '--jobs', a.jobs)
    cmd = [sys.executable, ROOT/'ps5/tools/package-local.py', '--game', game, '--vulkan', vulkan, '--output', a.output]
    if a.ps_prompts_archive: cmd += ['--ps-prompts-archive', a.ps_prompts_archive]
    run(*cmd)
    run(sys.executable, ROOT/'ps5/tools/package-local.py', '--output', a.output, '--validate-only')

if __name__ == '__main__': main()
