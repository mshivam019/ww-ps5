#!/usr/bin/env python3
"""Validate a source/setup release ZIP or a locally generated title manifest."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = {'.a','.o','.so','.exe','.dll','.dylib','.pdb','.rpx','.wux','.wud','.iso','.rvz','.key','.elf','.bin','.prx','.sav','.png','.jpg','.mp4','.zip'}

def validate_archive(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(set(names)) != len(names): raise ValueError('Duplicate archive entry')
        if z.testzip(): raise ValueError('Archive CRC mismatch')
        manifest = json.loads(z.read('RELEASE-MANIFEST.json'))
        prebuilt = manifest.get('kind') == 'prebuilt-setup'
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name: raise ValueError(f'Unsafe path: {name}')
            runtime_file = prebuilt and p.parts[0] == 'runtime-prebuilt' and p.suffix.lower() in {'.a','.o','.so','.prx','.h','.hpp','.inc','.def','.tcc','.txt','.json','.ld','.map',''}
            host_file = prebuilt and len(p.parts) == 3 and p.parts[0] == 'host-tools' and p.name in {'ps5-native-tool','ps5-native-tool.exe'}
            if p.name in {'libgamecode.a','eboot.bin','eboot.elf'} or (p.suffix.lower() in FORBIDDEN and not (runtime_file or host_file)) or any(x in p.parts for x in ('.git','.deps','build','private-assets','backups')):
                raise ValueError(f'Private/binary artifact in source release: {name}')
            if (z.getinfo(name).external_attr >> 16) & 0o170000 == 0o120000: raise ValueError(f'Symlink: {name}')
        manifest = json.loads(z.read('RELEASE-MANIFEST.json'))
        expected = {row['path']: row for row in manifest['files']}
        if set(names) != set(expected) | {'RELEASE-MANIFEST.json'}: raise ValueError('Manifest inventory mismatch')
        for name,row in expected.items():
            b = z.read(name)
            if len(b) != row['size'] or hashlib.sha256(b).hexdigest() != row['sha256']:
                raise ValueError(f'Hash mismatch: {name}')
        for name in ('README.md','LICENSE','ps5/README.md','ps5/tools/build.py','ps5/tools/setup-deps.py','ps5/dependencies.json'):
            if name not in names: raise ValueError(f'Missing setup source: {name}')
        if prebuilt:
            runtime_manifest = json.loads(z.read('runtime-prebuilt/manifest.json'))
            for row in runtime_manifest['files']:
                data = z.read('runtime-prebuilt/'+row['path'])
                if len(data) != row['size'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                    raise ValueError('Runtime manifest mismatch')
            if '{GAME_ARCHIVE}' not in z.read('runtime-prebuilt/link.json').decode():
                raise ValueError('Release must generate game code locally')
        print(f'Validated {len(expected)} source files at {manifest["commit"]}')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--archive',type=Path)
    group.add_argument('--title',type=Path)
    a=p.parse_args()
    if a.archive: validate_archive(a.archive)
    else: subprocess.run([sys.executable,str(ROOT/'ps5/tools/package-local.py'),'--output',str(a.title),'--validate-only'],check=True)

if __name__ == '__main__': main()
