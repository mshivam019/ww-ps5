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
    p.add_argument('--runtime',type=Path,help='Optional reusable runtime bundle')
    p.add_argument('--host-tools',type=Path,help='Required with --runtime')
    p.add_argument('--output',type=Path,default=ROOT/'dist')
    a=p.parse_args()
    if not a.version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-' for c in a.version): p.error('Invalid version')
    if git('status','--porcelain').strip(): raise RuntimeError('Commit source changes before packaging')
    if a.runtime and not a.host_tools: p.error('--runtime requires --host-tools')
    commit=git('rev-parse','HEAD').decode().strip()
    files=[x.decode() for x in git('ls-files','-z').split(b'\0') if x]
    a.output.mkdir(parents=True,exist_ok=True)
    kind='setup' if a.runtime else 'source-setup'
    dest=a.output/f'Wind-Waker-HD-PS5-{a.version}-{kind}.zip'
    if dest.exists(): raise RuntimeError('Release archive already exists; choose a new output directory')
    entries={name:ROOT/name for name in files}
    if a.runtime:
        for path in a.runtime.rglob('*'):
            if path.is_file(): entries['runtime-prebuilt/'+path.relative_to(a.runtime).as_posix()]=path
        for host in ('windows-x86_64','windows-arm64','macos-x86_64','macos-arm64','linux-x86_64','linux-arm64'):
            name='ps5-native-tool.exe' if host.startswith('windows') else 'ps5-native-tool'
            path=a.host_tools/host/name
            if not path.is_file(): raise ValueError(f'Missing {path}')
            entries['host-tools/'+host+'/'+name]=path
    records=[]
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in sorted(entries.items()):
            if path.is_symlink(): raise ValueError(f'Symlink: {name}')
            data=path.read_bytes();records.append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            info=zipfile.ZipInfo(name,(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if path.stat().st_mode & 0o111 else 0o100644)<<16
            z.writestr(info,data)
        info=zipfile.ZipInfo('RELEASE-MANIFEST.json',(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,json.dumps({'version':a.version,'commit':commit,'kind':'prebuilt-setup' if a.runtime else 'source-setup','files':records},indent=2)+'\n')
    validate_archive(dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    with (a.output/'SHA256SUMS').open('a') as sums: sums.write(f'{digest}  {dest.name}\n')
    print(dest)

if __name__ == '__main__': main()
