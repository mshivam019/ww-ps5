#!/usr/bin/env python3
"""Extract a supplied WUX into a new private folder and verify the supported RPX."""
import argparse
import hashlib
from pathlib import Path
import sys
from game_build import identify_game
from builds import by_title

ROOT = Path(__file__).resolve().parents[2]

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
    if by_title(title_id) is None:
        game.wud.f.close()
        raise ValueError('Expected the USA or European Wind Waker HD disc')
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
    build = identify_game(output)
    if build.title_id != title_id:
        raise ValueError('Disc title and executable region do not match')
    print('Extracted and verified ' + build.name + ' version 0. Game files remain outside Git.')

if __name__ == '__main__':
    main()
