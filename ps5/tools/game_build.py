"""Identify supported version-0 Wii U builds, retaining exact hash checks."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/recomp"))
from builds import identify

def identify_game(game):
    rpx = Path(game) / "code/cking.rpx"
    if not rpx.is_file():
        raise ValueError("Select an extracted Wii U folder containing code/cking.rpx, content and meta.")
    build = identify(rpx)
    if build is None:
        raise ValueError("Unsupported game executable. Use USA or Europe Wii U version 0, without an update.")
    for name in ("content", "meta"):
        if not (Path(game) / name).is_dir():
            raise ValueError("Missing game folder: " + name)
    return build
