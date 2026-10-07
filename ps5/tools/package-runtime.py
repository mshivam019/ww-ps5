#!/usr/bin/env python3
"""Stage reusable PS5 libraries from a checked build; exclude all generated game code."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-root',type=Path,required=True)
p.add_argument('--link-trace',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
r=a.build_root.resolve(); out=a.output.resolve()
if out.exists(): p.error('Output exists')
lib=out/'lib';lib.mkdir(parents=True)
lines=a.link_trace.read_text().splitlines()
line=next(x for x in lines if x.startswith('+ ') and '/bin/prospero-lld ' in x and 'llvm-pie.elf' in x)
args=shlex.split(line[2:])[1:]
result=['-m','elf_x86_64','-pie','-z','max-page-size=0x4000','-mllvm','-emulated-tls','--hash-style=gnu']
def copy(path):
    dest=lib/path.name
    if dest.exists() and dest.read_bytes()!=path.read_bytes():raise ValueError(f'Conflicting library: {path.name}')
    shutil.copy2(path,dest)
    return '{RUNTIME}/lib/'+path.name
for arg in args:
    if arg.endswith('/libgamecode.a'):
        result.append('{GAME_ARCHIVE}')
    elif arg.endswith('/llvm-pie.elf'):
        result.append('{ELF}')
    elif arg.startswith('/'):
        path=Path(arg)
        result.append('{RUNTIME}/lib' if path.is_dir() else copy(path))
    else:result.append(arg)
# Empty SDK archives satisfy compiler-emitted dependent-library directives.
for path in (r/'.deps/native/ps5-payload-sdk/target/lib').glob('*.a'):
    copy(path)
copy(r/'.deps/src/vulkan/tooling/native/ps5-pie.ld')
shutil.copytree(r/'.deps/native/ps5-payload-sdk/target/include',out/'include')
(out/'runtime').mkdir()
shutil.copy2(r/'.deps/src/vulkan/runtime/libc.prx',out/'runtime/libc.prx')
(out/'link.json').write_text(json.dumps(result,indent=2)+'\n')
files=[]
for path in sorted(out.rglob('*')):
    if path.is_file():
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        files.append({'path':path.relative_to(out).as_posix(),'size':path.stat().st_size,'sha256':digest})
(out/'manifest.json').write_text(json.dumps({'kind':'runtime-only','files':files},indent=2)+'\n')
print(f'Staged {len(files)} reusable runtime files. No gamecode archive or executable included.')
