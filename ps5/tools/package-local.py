#!/usr/bin/env python3
"""Stage a private test title from the user's extracted game, never a public release."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
TITLE = 'PPSA99641'
RPX_SHA = 'c4f0ab300542e0bfc462696850534e71db2ad02288a7eb55e5a4cd4062f16153'
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def validate(title):
    for name in ['eboot.bin', 'sce_module/libc.prx', 'sce_sys/icon0.png', 'sce_sys/param.json', 'game/code/cking.rpx']:
        if not (title / name).is_file():
            raise ValueError(f'Missing {name}')
    if json.loads((title/'sce_sys/param.json').read_text())['titleId'] != TITLE:
        raise ValueError('Wrong title ID')
    if sha(title/'game/code/cking.rpx') != RPX_SHA:
        raise ValueError('Unsupported RPX')
    files = []
    for path in sorted(title.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symbolic link: {path}')
        if path.is_file():
            if path.suffix.lower() in {'.key', '.wux', '.wud', '.iso', '.pem'}:
                raise ValueError(f'Private key or image: {path}')
            files.append({'path':path.relative_to(title).as_posix(), 'size':path.stat().st_size, 'sha256':sha(path)})
    return files
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path)
    p.add_argument('--vulkan', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--validate-only', action='store_true')
    p.add_argument('--ps-prompts-archive', type=Path, help='Use a local PlayStation UI archive instead of downloading')
    p.add_argument('--without-ps-prompts', action='store_true', help='Explicitly omit the default PlayStation texture mod')
    a = p.parse_args()
    if a.validate_only:
        expected = json.loads((a.output.parent/'manifest.json').read_text())['files']
        if validate(a.output) != expected:
            raise ValueError('Manifest mismatch')
        print('All title files match the manifest'); return
    if not a.game or not a.vulkan:
        p.error('--game and --vulkan are required when staging')
    if a.output.exists():
        raise ValueError('Output exists; choose a new path')
    if sha(a.game/'code/cking.rpx') != RPX_SHA:
        raise ValueError('Unsupported RPX')
    a.output.mkdir(parents=True)
    shutil.copy2(ROOT/'build/native-game/eboot.bin', a.output/'eboot.bin')
    shutil.copytree(ROOT/'ps5/sce_sys', a.output/'sce_sys')
    shutil.copytree(a.game, a.output/'game')
    (a.output/'sce_module').mkdir()
    shutil.copy2(a.vulkan/'runtime/libc.prx', a.output/'sce_module/libc.prx')
    with Image.open(a.game/'meta/iconTex.tga') as image:
        image.convert('RGB').resize((512,512), Image.Resampling.LANCZOS).save(a.output/'sce_sys/icon0.png')
    (a.output/'user/save').mkdir(parents=True)
    (a.output/'user/captures').mkdir()
    if not a.without_ps_prompts:
        command = [sys.executable, str(ROOT/'ps5/tools/prepare-ps-prompts.py'), '--title', str(a.output)]
        if a.ps_prompts_archive:
            command += ['--archive', str(a.ps_prompts_archive)]
        subprocess.run(command, check=True)
    manifest = {'title':TITLE, 'private_test_build':True, 'console_tested':False, 'files':validate(a.output)}
    (a.output.parent/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f"Validated {len(manifest['files'])} files: {a.output}")
if __name__ == '__main__': main()
