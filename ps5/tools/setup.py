#!/usr/bin/env python3
"""Build your game dump using the release's precompiled PS5 runtime. No container needed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RPX_SHA = 'c4f0ab300542e0bfc462696850534e71db2ad02288a7eb55e5a4cd4062f16153'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def host():
    system = {'Windows':'windows', 'Darwin':'macos', 'Linux':'linux'}.get(platform.system())
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('aarch64','arm64') else 'x86_64' if machine in ('amd64','x86_64') else None
    if not system or not arch:
        raise ValueError('Supported hosts: Windows, macOS and Linux on x86-64 or ARM64.')
    return system+'-'+arch


def compiler(host_id):
    key = 'macos' if host_id.startswith('macos') else host_id
    pin = json.loads((ROOT/'ps5/toolchains.json').read_text())[key]
    cache = ROOT/'build/tools'
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache/Path(pin['url']).name
    tool = cache/pin['directory']/'bin'
    suffix = '.exe' if host_id.startswith('windows') else ''
    if not (tool/('clang'+suffix)).exists():
        if not archive.exists() or sha(archive) != pin['sha256']:
            print('Downloading the portable compiler...', flush=True)
            temporary = archive.with_suffix('.download')
            urllib.request.urlretrieve(pin['url'], temporary)
            if sha(temporary) != pin['sha256']:
                temporary.unlink()
                raise ValueError('Compiler checksum mismatch')
            temporary.replace(archive)
        if archive.suffix == '.zip':
            with zipfile.ZipFile(archive) as z:
                z.extractall(cache)
        else:
            with tarfile.open(archive) as t:
                t.extractall(cache, filter='data')
    return {name:str(tool/(name+suffix)) for name in ('clang','ld.lld','llvm-ar','llvm-nm')}


def run(*args):
    log=ROOT/'build/setup.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf-8') as stream:
        subprocess.run(list(map(str,args)),check=True,stdout=stream,stderr=subprocess.STDOUT)


def check_runtime(runtime):
    manifest = json.loads((runtime/'manifest.json').read_text())
    for row in manifest['files']:
        path = runtime/row['path']
        if not path.is_file() or path.stat().st_size != row['size'] or sha(path) != row['sha256']:
            raise ValueError(f'Damaged runtime file: {row["path"]}. Extract a fresh release.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    inputs = p.add_mutually_exclusive_group()
    inputs.add_argument('--game', type=Path, help='Extracted USA version 0 code/content/meta folder')
    inputs.add_argument('--image', type=Path, help='USA version 0 WUX image')
    p.add_argument('--disc-key', type=Path)
    p.add_argument('--common-key', type=Path)
    p.add_argument('--output', type=Path, default=ROOT.parent/'Wind-Waker-HD-PS5-install/PPSA99641')
    p.add_argument('--jobs', type=int, default=4)
    a = p.parse_args()
    if not a.game and not a.image:
        print('Wind Waker HD for PS5 setup\nUse your USA Wii U version 0 dump.')
        supplied = Path(input('Game folder or WUX file path: ').strip().strip('"').strip("'"))
        if supplied.is_dir(): a.game = supplied
        else: a.image = supplied
    if a.jobs < 1: p.error('--jobs must be positive')
    if a.output.exists(): p.error('Output already exists. Choose a new folder with --output.')
    if a.output.name != 'PPSA99641': p.error('--output must end in PPSA99641')
    runtime = ROOT/'runtime-prebuilt'
    if not (runtime/'manifest.json').is_file():
        p.error('Download the setup release ZIP, which includes our compiled runtime. For source builds use ps5/tools/build.py.')
    check_runtime(runtime)
    # Install only the small packaging/extraction modules into a private environment.
    venv = ROOT/'build/setup-python'
    python = venv/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file(): run(sys.executable,'-m','venv',venv)
    run(python,'-m','pip','install','--disable-pip-version-check','pillow==11.3.0','pycryptodome==3.23.0')
    game = a.game.resolve() if a.game else ROOT.parent/'Wind-Waker-HD-PS5-extracted'
    if a.image:
        if a.image.suffix.lower() != '.wux': p.error('Use a WUX or an extracted code/content/meta folder')
        a.disc_key = a.disc_key or a.image.with_suffix('.key')
        a.common_key = a.common_key or a.image.parent/'common.key'
        for field, label in [('disc_key','Disc key file'),('common_key','Wii U common key file')]:
            if not getattr(a,field).is_file() and sys.stdin.isatty():
                setattr(a,field,Path(input(label+' path: ').strip().strip('"').strip("'")))
        # The extractor refuses existing output. Reuse only if this exact input was recorded.
        marker = ROOT/'build/extracted-input.sha256'
        identity = hashlib.sha256(''.join(sha(x) for x in (a.image,a.disc_key,a.common_key)).encode()).hexdigest()
        if not (game.is_dir() and marker.exists() and marker.read_text()==identity):
            run(python,ROOT/'ps5/tools/prepare-game.py','--image',a.image,'--disc-key',a.disc_key,
                '--common-key',a.common_key,'--output',game)
            marker.write_text(identity)
    if not (game/'code/cking.rpx').is_file() or sha(game/'code/cking.rpx') != RPX_SHA:
        p.error('This dump is not the supported USA Wii U version 0.')
    host_id = host()
    tools = compiler(host_id)
    packer = ROOT/'host-tools'/host_id/('ps5-native-tool.exe' if os.name=='nt' else 'ps5-native-tool')
    if not packer.is_file(): p.error(f'Missing host packer: {host_id}')
    if os.name != 'nt': packer.chmod(0o755)
    gen = ROOT/'build/gen'
    print('Generating code from your dump...',flush=True)
    run(python,ROOT/'tools/recomp/recomp.py',game/'code/cking.rpx',gen)
    work = ROOT/'build/native-game';work.mkdir(parents=True,exist_ok=True)
    objects = work/'objects';objects.mkdir(exist_ok=True)
    flags = ['-target','x86_64-sie-ps5','-fvisibility-nodllstorageclass=default',
             '-isystem',str(runtime/'include'),'-I',str(ROOT/'runtime/include'),'-I',str(gen),
             '-fno-stack-protector','-fno-plt','-femulated-tls','-fdenormal-fp-math=ieee',
             '-fPIC','-O3','-DNDEBUG','-std=gnu11','-ffp-contract=off','-fno-strict-aliasing','-w']
    sources = sorted(gen.glob('code_*.c'))+[gen/'table.c',gen/'imports.c']
    build_identity = sha(runtime/'manifest.json') + sha(ROOT/'runtime/include/ppc.h') + sha(ROOT/'ps5/toolchains.json')
    def compile_one(source):
        obj=objects/(source.stem+'.o')
        stamp=obj.with_suffix('.sha256')
        identity=hashlib.sha256((build_identity+sha(source)+str(flags)).encode()).hexdigest()
        if not (obj.is_file() and stamp.is_file() and stamp.read_text()==identity+':'+sha(obj)):
            run(tools['clang'],*flags,'-c',source,'-o',obj)
            stamp.write_text(identity+':'+sha(obj))
        return obj
    print(f'Compiling {len(sources)} game files using our prebuilt runtime...',flush=True)
    with ThreadPoolExecutor(max_workers=a.jobs) as executor:
        compiled=list(executor.map(compile_one,sources))
    archive=work/'libgamecode.a'
    archive.unlink(missing_ok=True)
    run(tools['llvm-ar'],'rcs',archive,*compiled)
    elf=work/'llvm-pie.elf'
    recipe=json.loads((runtime/'link.json').read_text())
    args=[x.replace('{RUNTIME}',str(runtime)).replace('{GAME_ARCHIVE}',str(archive)).replace('{ELF}',str(elf)) for x in recipe]
    # A response file avoids Windows command-line length limits.
    response=work/'link.rsp'
    response.write_text('\n'.join('"'+x.replace('\\','/').replace('"','\\"')+'"' for x in args)+'\n')
    run(tools['ld.lld'],'@'+str(response))
    undefined=subprocess.check_output([tools['llvm-nm'],'-D','--undefined-only',str(elf)],text=True)
    needed={line.split()[-1].split('@')[0] for line in undefined.splitlines() if line.strip().startswith('U ')}
    provided=set()
    for library in (runtime/'lib').glob('*.so'):
        if library.name in {'libkernel_sys.so','libScePosixForWebKit.so'}: continue
        text=subprocess.check_output([tools['llvm-nm'],'-D','--defined-only',str(library)],text=True)
        provided.update(line.split()[-1].split('@')[0] for line in text.splitlines() if line.strip())
    if needed-provided: raise ValueError('Unresolved PS5 imports: '+', '.join(sorted(needed-provided)))
    print('Linking and checking the PS5 executable...',flush=True)
    run(packer,'link','--in',elf,'--out',work/'eboot.elf','--stub-dir',runtime/'lib',
        '--module-sdk','0x02000009','--companion-sdk','0x08050001','--file-name','eboot.elf')
    run(packer,'self','--sign','--in',work/'eboot.elf','--out',work/'eboot.bin','--magic','0x1D3D154F')
    run(packer,'self','--inspect','--file',work/'eboot.bin')
    print('Copying game files, adding PlayStation prompts and validating the installation...',flush=True)
    run(python,ROOT/'ps5/tools/package-local.py','--game',game,'--vulkan',runtime,'--output',a.output)
    run(python,ROOT/'ps5/tools/validate.py','--title',a.output)
    print(f'\nReady: {a.output.resolve()}\nUpload this folder to your PS5 and register it with your native-title launcher.')


if __name__=='__main__':
    try: main()
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print(f'Setup failed: {error}\nDetails: {ROOT / "build/setup.log"}',file=sys.stderr)
        sys.exit(1)
