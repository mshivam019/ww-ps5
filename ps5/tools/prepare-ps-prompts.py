#!/usr/bin/env python3
"""Add pivotiii's USA English swapped PlayStation UI to a private staged title."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
EXPECTED_MD5 = '4460c869eec9e255f939e69d6a4267d9'
PACK = 'WindWakerHD_PS_UI_swapped/content/Common/Pack/permanent_2d_UsEnglish.pack'
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--title', type=Path, required=True)
    a = p.parse_args()
    with a.archive.open('rb') as stream:
        if hashlib.file_digest(stream,'md5').hexdigest() != EXPECTED_MD5:
            raise ValueError('Expected the recorded swapped-layout release')
    if json.loads((a.title/'sce_sys/param.json').read_text())['titleId'] != 'PPSA99641':
        raise ValueError('Wrong title')
    mod = a.title/'user/ModManager/Mods/playstation-ui'
    target = mod/'content/Common/Pack/permanent_2d_UsEnglish.pack'
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.archive) as z:
        if z.testzip(): raise ValueError('Archive CRC failure')
        target.write_bytes(z.read(PACK))
    manifest = {'format_version':1,'id':'playstation-ui','name':'PlayStation UI (USA English)',
      'version':'1.0.0','author':'pivotiii','game_id':'wwhd-usa','kind':'content',
      'minimum_manager_version':'1.1.0','content_dir':'content',
      'description':'USA English swapped layout: Cross=A, Circle=B, Triangle=X, Square=Y. Restart after enabling/disabling. Source: https://gamebanana.com/mods/385841'}
    (mod/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    profile = a.title/'user/ModManager/profiles.json'
    if not profile.exists():
        profile.write_text(json.dumps({'format_version':1,'active':'Default','profiles':{'Default':{'enabled':{'playstation-ui':True}}}},indent=2)+'\n')
    manifest_path = a.title.parent/'manifest.json'
    if manifest_path.exists():
        receipt = json.loads(manifest_path.read_text())
        files = []
        for file in sorted(a.title.rglob('*')):
            if file.is_symlink(): raise ValueError('Symbolic link in title')
            if file.is_file():
                with file.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                files.append({'path':file.relative_to(a.title).as_posix(),'size':file.stat().st_size,'sha256':digest})
        receipt['files'] = files
        manifest_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PlayStation prompts prepared; existing profile preserved')
if __name__ == '__main__': main()
