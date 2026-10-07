#!/usr/bin/env python3
"""Extract a supplied WUX into a new private folder and verify the supported RPX."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
RPX_SHA256 = 'c4f0ab300542e0bfc462696850534e71db2ad02288a7eb55e5a4cd4062f16153'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--disc-key', type=Path, required=True)
    parser.add_argument('--common-key', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        parser.error('Keep extracted game files outside the source repository')
    for p in (args.image, args.disc_key, args.common_key):
        if not p.is_file():
            parser.error(f'File not found: {p}')
    if output.exists():
        parser.error('Output already exists; use a new folder to avoid overwriting assets')
    output.mkdir(parents=True, mode=0o700)
    # The upstream extractor expects adjacent key files. Symlink privately without
    # changing the originals or passing key bytes on a command line.
    with tempfile.TemporaryDirectory(prefix='wwhd-input-') as name:
        temp = Path(name)
        (temp / 'game.wux').symlink_to(args.image.resolve())
        (temp / 'game.key').symlink_to(args.disc_key.resolve())
        (temp / 'common.key').symlink_to(args.common_key.resolve())
        subprocess.run([sys.executable, str(ROOT / 'tools/wudextract.py'),
                        str(temp / 'game.wux'), 'extract', str(output)], check=True)
    rpx = output / 'code/cking.rpx'
    if not rpx.is_file() or hashlib.sha256(rpx.read_bytes()).hexdigest() != RPX_SHA256:
        raise RuntimeError('Extracted RPX does not match the supported USA version 0')
    print('Extracted and verified USA version 0. Game files remain outside Git.')

if __name__ == '__main__':
    main()
