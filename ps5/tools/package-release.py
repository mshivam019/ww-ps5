#!/usr/bin/env python3
"""Create a shareable source/setup ZIP, never the game-derived private title."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from validate import validate_archive

ROOT=Path(__file__).resolve().parents[2]

def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'dist')
    a=p.parse_args()
    if not a.version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-' for c in a.version): p.error('Invalid version')
    if git('status','--porcelain').strip(): raise RuntimeError('Commit source changes before packaging')
    commit=git('rev-parse','HEAD').decode().strip()
    files=[x.decode() for x in git('ls-files','-z').split(b'\0') if x]
    # Desktop/mobile launch artwork is unrelated to the PS5 source setup.
    files=[x for x in files if not x.startswith('android/')]
    a.output.mkdir(parents=True,exist_ok=True)
    dest=a.output/f'Wind-Waker-HD-PS5-{a.version}-source-setup.zip'
    if dest.exists(): raise RuntimeError('Release archive already exists; choose a new output directory')
    records=[]
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(files):
            path=ROOT/name
            if path.is_symlink(): raise ValueError(f'Symlink: {name}')
            data=path.read_bytes();records.append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            info=zipfile.ZipInfo(name,(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if path.stat().st_mode & 0o111 else 0o100644)<<16
            z.writestr(info,data)
        info=zipfile.ZipInfo('RELEASE-MANIFEST.json',(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,json.dumps({'version':a.version,'commit':commit,'kind':'source-setup','files':records},indent=2)+'\n')
    validate_archive(dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    (a.output/'SHA256SUMS').write_text(f'{digest}  {dest.name}\n')
    print(dest)

if __name__ == '__main__': main()
