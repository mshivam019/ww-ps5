#!/usr/bin/env python3
"""Generate the game-independent bridge and build a private loadable game module."""
import argparse
import hashlib
import importlib.util
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def abi():
    paths = [ROOT/'runtime/include/ppc.h', ROOT/'runtime/include/recomp_table.h', ROOT/'runtime/include/guest_addr.h', ROOT/'tools/recomp/builds/eu.json', *sorted((ROOT/'tools/recomp').glob('hooks*.txt'))]
    return hashlib.sha256(b'wwhd-ps5-module-v2\0'+b''.join(p.read_bytes().replace(b'\r\n', b'\n') for p in paths)).hexdigest()

def legacy_abi():
    # The published ps5-v0.1.2 USA-only ABI, derived from its LF source tree.
    return 'bfb5c6228ce124452e7f1dd79c8b88538539cbbcb82bce28c3abc7c1805e1be4'

def legacy_compatible():
    paths = [ROOT/'runtime/include/ppc.h', ROOT/'runtime/include/recomp_table.h', *sorted((ROOT/'tools/recomp').glob('hooks*.txt'))]
    current = hashlib.sha256(b'wwhd-ps5-module-v1\0'+b''.join(p.read_bytes().replace(b'\r\n', b'\n') for p in paths)).hexdigest()
    return current == legacy_abi()

def symbols(nm, path, *flags):
    text = subprocess.check_output([nm, *flags, str(path)], text=True)
    return [line.split() for line in text.splitlines() if line.strip() and not line.endswith(':')]

def bridge(out, nm, archive, module):
    spec = importlib.util.spec_from_file_location('stubgen', ROOT/'tools/recomp/stubgen.py')
    stub = importlib.util.module_from_spec(spec); spec.loader.exec_module(stub)
    stub.main(str(out))
    hooks, _ = stub.hook_lists(); funcs = sorted(stub.runtime_refs() | hooks)
    code = ['#include "funcs.h"', '#include <stdatomic.h>', 'extern PpcFunc wwhd_module_function(const char* name);']
    for e in funcs:
        for suffix in (['', '_orig'] if e in hooks else ['']):
            name = f'f_{e:08X}{suffix}'
            code.append(f'void {name}(Cpu* c) {{ static _Atomic(PpcFunc) cache; PpcFunc fn=atomic_load_explicit(&cache,memory_order_acquire); if (!fn) {{ fn=wwhd_module_function("{name}"); atomic_store_explicit(&cache,fn,memory_order_release); }} fn(c); }}')
    (out/'code_000.c').write_text('\n'.join(code)+'\n')
    # The actual tables belong to the user's module, never the app binary.
    (out/'table.c').write_text('#include "recomp_table.h"\nconst RecompEntry* g_recomp_funcs;\nunsigned g_recomp_func_count;\nconst RecompImport* g_recomp_imports;\nunsigned g_recomp_import_count;\nuint32_t g_recomp_entry_point;\n')
    defined = {r[-1] for r in symbols(nm, archive, '--defined-only') if len(r)>=3 and r[-2] in {'T','D','B','R'}}
    exports = sorted(n for n in defined if n.startswith(('imp_', 'hook_', 'site_', 'ppc_', 'hle_')) or n in {'g_core_preempt','g_ppc_trace'})
    if module:
        undefined = {r[-1] for r in symbols(nm, module, '-D', '--undefined-only')}
        if undefined - set(exports): raise ValueError('Unresolved game imports: '+str(sorted(undefined-set(exports))))
    assert all(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', n) for n in exports)
    lines = ['#include <cstring>', '#include "ppc.h"', '#include "loader.h"']
    for i, name in enumerate(exports): lines.append(f'extern "C" char host_{i}[] __asm__("{name}");')
    lines.append('void* wwhd_host_symbol(const char* name) {')
    for i, name in enumerate(exports): lines.append(f'  if (!strcmp(name,"{name}")) return host_{i};')
    lines += ['  return nullptr;', '}']
    (out/'exports.cpp').write_text('\n'.join(lines)+'\n')
    (out/'abi.h').write_text(f'#define WWHD_MODULE_ABI "{abi()}"\n#define WWHD_LEGACY_USA_ABI "{legacy_abi()}"\n#define WWHD_CAN_LOAD_LEGACY_USA {int(legacy_compatible())}\n')
    (out/'required.inc').write_text(''.join(f'REQUIRE_GAME_SYMBOL("f_{e:08X}{s}")\n' for e in funcs for s in (['','_orig'] if e in hooks else [''])))
    print(f'Generated bridge: {len(funcs)} runtime calls, {len(exports)} host symbols')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--nm',default='llvm-nm')
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--module',type=Path,help='Optional private module to check imports against the runtime')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    bridge(a.output,a.nm,a.runtime,a.module)
if __name__=='__main__': main()
