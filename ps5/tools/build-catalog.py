#!/usr/bin/env python3
"""Build the game-independent PS5 app. No ROM, generated game code or keys required."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def run(*args):subprocess.run(list(map(str,args)),check=True)
def configure(build,gen,a,module):
    run('cmake','-S',ROOT,'-B',build,'-G','Ninja',
        f'-DCMAKE_TOOLCHAIN_FILE={a.sdk}/toolchain/prospero.cmake',
        '-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY','-DCMAKE_BUILD_TYPE=Release',
        f'-DGEN_DIR={gen}',f'-DSDL3_DIR={a.sdl_build}',
        f'-DPS5_VULKAN_HEADERS={a.vulkan}/.deps/native/radv-release/include',
        '-DWWHD_GAME_MODULE='+('ON' if module else 'OFF'))
    run('cmake','--build',build,'--target','wwhd','--parallel',a.jobs)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',type=Path,required=True)
    p.add_argument('--vulkan',type=Path,required=True)
    p.add_argument('--sdl-build',type=Path,required=True)
    p.add_argument('--sdl-source',type=Path,required=True)
    p.add_argument('--runtime-reference',type=Path,help='Existing runtime archive for its public symbol list; otherwise build a ROM-free reference')
    p.add_argument('--jobs',type=int,default=4)
    a=p.parse_args()
    if a.jobs<1:p.error('--jobs must be positive')
    for name in ['sdk','vulkan','sdl_build','sdl_source']:setattr(a,name,getattr(a,name).resolve())
    gen=ROOT/'build/gen-module';build=ROOT/'build/ps5-module-runtime';work=ROOT/'build/catalog-app';work.mkdir(parents=True,exist_ok=True)
    reference=a.runtime_reference
    if not reference:
        stub=ROOT/'build/catalog-stub';bootstrap=ROOT/'build/catalog-bootstrap'
        run(sys.executable,ROOT/'tools/recomp/stubgen.py',stub)
        configure(bootstrap,stub,a,False);reference=bootstrap/'libwwhd.a'
    run(sys.executable,ROOT/'ps5/tools/module-support.py','--output',gen,'--runtime',reference,'--nm',a.sdk/'bin/llvm-nm')
    configure(build,gen,a,True)
    run(a.sdk/'bin/prospero-clang++','-std=c++20','-O2','-I',a.sdl_source/'include','-c',ROOT/'ps5/main.cpp','-o',work/'main.o')
    run(a.sdk/'bin/prospero-clang++','-std=c++20','-O2','-c',ROOT/'ps5/storage.cpp','-o',work/'storage.o')
    run(a.sdk/'bin/prospero-clang','-std=c11','-O2','-c',ROOT/'ps5/native/platform.c','-o',work/'platform.o')
    runtime=build/'libwwhd.a'
    deps=sorted(p for p in build.rglob('*.a') if p!=runtime and p.name not in {'libz.a','libzlibstatic.a','libzlib.a'})
    run('bash',ROOT/'ps5/tools/link-game.sh',work,a.vulkan,a.sdk,work/'main.o',work/'platform.o',work/'storage.o',
        '--whole-archive',runtime,'--no-whole-archive','--start-group',*deps,a.sdl_build/'libSDL3.a','--end-group')
    (work/'build.json').write_text(json.dumps({'game_independent':True,'console_tested':False,'executable':str(work/'eboot.bin')},indent=2)+'\n')
    print('Catalog app built; console validation is still required:',work/'eboot.bin')
if __name__=='__main__':main()
