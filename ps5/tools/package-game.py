#!/usr/bin/env python3
"""Prepare a private game folder to add to the separately installed catalog app."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from game_build import identify_game
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--without-ps-prompts',action='store_true')
    p.add_argument('--ps-prompts-archive',type=Path)
    a=p.parse_args()
    if a.output.exists():p.error('Choose a new output folder')
    build = identify_game(a.game)
    for directory in ['code','content','meta']:
        root=a.game/directory
        if not root.is_dir() or root.is_symlink():p.error(f'Missing or unsafe {directory} folder')
        for f in root.rglob('*'):
            if f.is_symlink() or (f.is_file() and f.suffix.lower() in {'.key','.pem','.wux','.wud','.iso','.gcm'}):p.error(f'Unexpected private input: {f.name}')
    a.output.mkdir(parents=True)
    for directory in ['code','content','meta']:shutil.copytree(a.game/directory,a.output/'game'/directory)
    shutil.copy2(a.module,a.output/'game/game.wwhd')
    if not a.without_ps_prompts and build.name == 'USA':
        cmd=[sys.executable,str(ROOT/'ps5/tools/prepare-ps-prompts.py'),'--title',str(a.output)]
        if a.ps_prompts_archive:cmd+=['--archive',str(a.ps_prompts_archive)]
        metadata=a.output/'sce_sys'
        metadata.mkdir()
        shutil.copy2(ROOT/'ps5/sce_sys/param.json',metadata/'param.json')
        try:subprocess.run(cmd,check=True)
        finally:shutil.rmtree(metadata)
    files=[{'path':f.relative_to(a.output).as_posix(),'size':f.stat().st_size,'sha256':sha(f)} for f in sorted(a.output.rglob('*')) if f.is_file()]
    (a.output/'game-package.json').write_text(json.dumps({'private_game_data':True,'rpx_sha256':build.sha256,'region':build.name,'wiiu_title_id':build.title_id,'files':files},indent=2)+'\n')
    (a.output/'COPY-TO-PS5.txt').write_text('Install the matching Wind Waker HD app first.\nClose it, then copy game/ to /data/wwhd/PPSA99641/game. If present, merge user/ into /data/wwhd/PPSA99641/user.\nKeep existing saves and user settings. Do not delete the installed app folder.\nThe generated game.wwhd and game data are private; do not redistribute them.\n')
    print('Private game package ready:',a.output)
if __name__=='__main__':main()
