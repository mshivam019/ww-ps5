#!/usr/bin/env python3
"""Add pivotiii's USA English swapped PlayStation UI to a private staged title."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import urllib.request
EXPECTED_SHA256 = '935a0274e5b68f21ab9eba14ebbb45ccf976695dba545ccb1273d31a07db606a'
DOWNLOAD_URL = 'https://gamebanana.com/dl/1126166'
DEFAULT_ARCHIVE = Path(__file__).resolve().parents[2] / 'build/downloads/playstation-ui-swapped.zip'
PACK = 'WindWakerHD_PS_UI_swapped/content/Common/Pack/permanent_2d_UsEnglish.pack'
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, help='Verified local archive; otherwise download to the build cache')
    p.add_argument('--title', type=Path, required=True)
    a = p.parse_args()
    archive = a.archive or DEFAULT_ARCHIVE
    if not archive.exists() and a.archive is None:
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = archive.with_suffix('.download')
        try:
            request = urllib.request.Request(DOWNLOAD_URL, headers={'User-Agent': 'Wind-Waker-HD-PS5-Setup'})
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as stream:
                import shutil
                shutil.copyfileobj(response, stream)
            with temporary.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != EXPECTED_SHA256:
                    raise ValueError('PlayStation UI download checksum mismatch')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != EXPECTED_SHA256:
            raise ValueError('Expected the recorded swapped-layout release')
    if json.loads((a.title/'sce_sys/param.json').read_text())['titleId'] != 'PPSA99641':
        raise ValueError('Wrong title')
    mod = a.title/'user/ModManager/Mods/playstation-ui'
    target = mod/'content/Common/Pack/permanent_2d_UsEnglish.pack'
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
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
