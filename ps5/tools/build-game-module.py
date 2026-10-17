#!/usr/bin/env python3
"""Link locally generated game code as a PS5 module. Never publish this output."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--clang',required=True)
    p.add_argument('--linker',required=True)
    p.add_argument('--nm',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('module_support',ROOT/'ps5/tools/module-support.py')
    support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
    source=a.output.parent/'module-abi.c';obj=source.with_suffix('.o')
    source.write_text(f'const char wwhd_game_abi[] = "{support.abi()}";\n')
    subprocess.run([a.clang,'-target','x86_64-sie-ps5','-fvisibility-nodllstorageclass=default','-fPIC','-c',str(source),'-o',str(obj)],check=True)
    subprocess.run([a.linker,'-shared','-z','max-page-size=16384','-z','common-page-size=16384','--hash-style=sysv',
                    '--whole-archive',str(a.archive),'--no-whole-archive',str(obj),'-o',str(a.output)],check=True)
    exports=subprocess.check_output([a.nm,'-D','--defined-only',str(a.output)],text=True)
    names={line.split()[-1] for line in exports.splitlines() if line.strip()}
    required={'wwhd_game_abi','g_recomp_funcs','g_recomp_func_count','g_recomp_imports','g_recomp_import_count','g_recomp_entry_point','g_guest_build_name','g_guest_build_title_id','g_guest_code_steps','g_guest_code_step_count','g_guest_data_steps','g_guest_data_step_count','g_guest_code_lo','g_guest_code_hi','g_guest_data_lo','g_guest_data_hi','g_guest_changed_code','g_guest_changed_code_count'}
    if required-names:raise ValueError('Missing module exports: '+str(sorted(required-names)))
    print('Private game module:',a.output)
if __name__=='__main__':main()
