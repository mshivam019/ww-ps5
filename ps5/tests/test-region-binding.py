#!/usr/bin/env python3
"""Exercise late-loaded USA/EU maps and reject malformed modules without game files."""
from pathlib import Path
import importlib.util
import io
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/recomp'))
import builds
from recomp import Recompiler

spec = importlib.util.spec_from_file_location('module_support', ROOT / 'ps5/tools/module-support.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)

def run(*args):
    subprocess.run(list(map(str, args)), check=True)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / 'abi.h').write_text('#define WWHD_MODULE_ABI "' + support.abi() + '"\n' +
                             '#define WWHD_LEGACY_USA_ABI "' + support.legacy_abi() + '"\n' +
                             '#define WWHD_CAN_LOAD_LEGACY_USA ' + str(int(support.legacy_compatible())) + '\n')
    (tmp / 'required.inc').write_text('REQUIRE_GAME_SYMBOL("fixture_function")\n')
    includes = ['-I' + str(ROOT / 'runtime/include'), '-I' + str(ROOT / 'ps5/module'), '-I' + str(tmp)]
    run('clang', '-DWWHD_GAME_MODULE', *includes, '-c', ROOT / 'runtime/src/guest_addr_identity.c', '-o', tmp / 'identity.o')
    run('clang++', '-std=c++20', '-DWWHD_GAME_MODULE', '-fsanitize=address,undefined', '-g',
        *includes, ROOT / 'ps5/tests/region-binding.cpp', ROOT / 'ps5/module/bind.cpp',
        ROOT / 'ps5/module/loader.cpp', tmp / 'identity.o', '-o', tmp / 'test')
    for name, expected in [('USA', 'USA'), ('EU', 'EU'), ('legacy-USA', 'USA'), ('bad-abi', 'invalid'),
                           ('bad-count', 'invalid'), ('bad-title', 'invalid'), ('missing-map', 'invalid')]:
        compiler = Recompiler.__new__(Recompiler)
        compiler.build = builds.by_name('USA' if name == 'USA' else 'EU')
        mapping = io.StringIO()
        compiler.write_build_map(mapping)
        tables = mapping.getvalue()
        if name == 'legacy-USA':
            tables = ''  # Original modules have no regional exports.
        if name == 'bad-count':
            tables = tables.replace('g_guest_code_step_count = 15', 'g_guest_code_step_count = 257')
        if name == 'bad-title':
            tables = tables.replace('0005000010143600', '0005000010143500')
        if name == 'missing-map':
            tables = tables.replace('g_guest_data_steps[]', 'missing_data_steps[]')
        abi = 'wrong' if name == 'bad-abi' else support.abi()
        if name == 'legacy-USA':
            abi = support.legacy_abi()
        source = '#include "guest_addr.h"\n#include "recomp_table.h"\n' + tables + '''
void fixture_function(Cpu* c) {(void)c;}
const RecompEntry g_recomp_funcs[] = {{0x02000020u, fixture_function}};
const unsigned g_recomp_func_count = 1;
const RecompImport g_recomp_imports[1] = {{0}};
const unsigned g_recomp_import_count = 0;
const uint32_t g_recomp_entry_point = 0x02000020u;
''' + 'const char wwhd_game_abi[] = "' + abi + '";\n'
        (tmp / 'fixture.c').write_text(source)
        run('clang', '-fPIC', '-fno-stack-protector', *includes, '-c', tmp / 'fixture.c', '-o', tmp / 'fixture.o')
        run('ld.lld', '-shared', '-z', 'max-page-size=16384', tmp / 'fixture.o', '-o', tmp / 'fixture.so')
        run(tmp / 'test', tmp / 'fixture.so', expected)
