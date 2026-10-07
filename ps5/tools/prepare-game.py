#!/usr/bin/env python3
"""Extract a supplied WUX into a new private folder and verify the supported RPX."""
import argparse
import hashlib
from pathlib import Path
import sys

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
    sys.path.insert(0, str(ROOT/'tools'))
    from wudextract import open_disc
    _, game, title_id = open_disc(str(args.image.resolve()), str(args.disc_key.resolve()),
                                 str(args.common_key.resolve()))
    if title_id != '0005000010143500':
        raise ValueError('Expected the USA Wind Waker HD disc')
    try:
        for entry in game.entries:
            if entry.is_dir or entry.flags & 0x80:
                continue
            destination = (output/entry.path).resolve()
            if not destination.is_relative_to(output):
                raise ValueError('Unsafe path in disc image')
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('wb') as stream:
                game.read_file(entry, stream)
    finally:
        game.wud.f.close()
    rpx = output / 'code/cking.rpx'
    if not rpx.is_file() or hashlib.sha256(rpx.read_bytes()).hexdigest() != RPX_SHA256:
        raise RuntimeError('Extracted RPX does not match the supported USA version 0')
    print('Extracted and verified USA version 0. Game files remain outside Git.')

if __name__ == '__main__':
    main()
