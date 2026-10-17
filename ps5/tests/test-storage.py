#!/usr/bin/env python3
"""Host regression test with small synthetic files; no game data required."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    subprocess.run(['clang++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-g', '-I' + str(ROOT / 'ps5'),
                    str(ROOT / 'ps5/tests/storage.cpp'), str(ROOT / 'ps5/storage.cpp'),
                    '-o', str(tmp / 'test')], check=True)
    subprocess.run([str(tmp / 'test'), str(tmp / 'fixture')], check=True)
