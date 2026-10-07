#!/usr/bin/env python3
"""Archive corresponding dependency source from the exact clean build pins."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-root',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=a.build_root.resolve()
pins=json.loads((root/'ps5/dependencies.json').read_text())
if a.output.exists():p.error('Output exists')
a.output.parent.mkdir(parents=True,exist_ok=True)
with tarfile.open(a.output,'w:gz') as archive:
    for key,folder in [('sdl3','SDL'),('sdk-platform','sdk'),('vulkan-runtime','vulkan'),('mesa','mesa')]:
        with tempfile.TemporaryFile() as stream:
            subprocess.run(['git','-C',str(root/'.deps/src'/folder),'archive','--format=tar',
                            '--prefix='+folder+'/',pins[key]['revision']],stdout=stream,check=True)
            stream.seek(0)
            with tarfile.open(fileobj=stream,mode='r:') as source:
                for member in source:
                    archive.addfile(member,source.extractfile(member) if member.isfile() else None)
    for name in ('glslang','lz4','zlib'):
        archive.add(root/'build/ps5-runtime/_deps'/(name+'-src'),arcname=name,
                    filter=lambda member: None if '/.git/' in member.name else member)
    archive.add(root/'.deps/src/vulkan/.deps/native/zlib/zlib-1.3.2',arcname='host-zlib-1.3.2')
with a.output.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
with (a.output.parent/'SHA256SUMS').open('a') as sums:sums.write(f'{digest}  {a.output.name}\n')
print(a.output)
