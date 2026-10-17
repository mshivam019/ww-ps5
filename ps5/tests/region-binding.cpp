// SPDX-License-Identifier: MPL-2.0
#include "bind.h"
#include "guest_addr.h"
#include "recomp_table.h"
#include <cassert>
#include <cstring>
#include <iostream>
extern "C" {
const RecompEntry* g_recomp_funcs;
unsigned g_recomp_func_count;
const RecompImport* g_recomp_imports;
unsigned g_recomp_import_count;
uint32_t g_recomp_entry_point;
}
void* wwhd_host_symbol(const char*) { return nullptr; }
// These objects are initialized before the game module and must remain regional.
const GuestAddress code{0x028F8250, true};
const GuestAddress data{0x101F84DC, false};
const GuestAddress field{0x1046F0B0, false, 0x5134};
int main(int argc, char** argv) {
    assert(argc == 3);
    assert(uint32_t(code) == 0x028F8250);
    std::string error;
    bool ok = wwhd_load_game_module(argv[1], error);
    if (!strcmp(argv[2], "invalid")) {
        assert(!ok && !error.empty());
        assert(uint32_t(code) == 0x028F8250); // failed bindings never install a partial map
    } else {
        if (!ok) { std::cerr << error << '\n'; return 1; }
        const bool eu = !strcmp(argv[2], "EU");
        assert(!strcmp(g_guest_build_name, argv[2]));
        assert(uint32_t(code) == (eu ? 0x028F8B10 : 0x028F8250));
        assert(uint32_t(data) == (eu ? 0x101F84F4 : 0x101F84DC));
        assert(uint32_t(field) == GD(0x1046F0B0) + 0x5134);
        assert(g_recomp_func_count > 0);
    }
    std::cout << argv[2] << " region binding: PASS\n";
}
