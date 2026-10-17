#include "bind.h"
#include "loader.h"
#include "recomp_table.h"
#include "abi.h"
#include "guest_addr.h"
#include <limits>
#include <cstring>
#include <stdexcept>
namespace {
game_module::Image module;
void* required(const char* name, size_t size = 1) {
    void* result = module.symbol(name, size);
    if (!result) throw std::runtime_error(std::string("Missing game symbol: ") + name);
    return result;
}
unsigned count(const char* name, unsigned limit, bool empty = false) {
    unsigned n = *static_cast<unsigned*>(required(name, sizeof(unsigned)));
    if ((!n && !empty) || n > limit) throw std::runtime_error("Invalid regional map count");
    return n;
}
uint32_t number(const char* name) {
    return *static_cast<uint32_t*>(required(name, sizeof(uint32_t)));
}
struct RegionMap {
    const GuestStep *code, *data;
    const GuestChanged* changed;
    unsigned codes, datas, changes;
    uint32_t code_lo, code_hi, data_lo, data_hi;
    const char *name, *title;
    explicit RegionMap(bool legacy_usa) {
        if (legacy_usa) {
            // v0.1.2 modules only contain canonical USA code. Their CPU/table ABI
            // and hook list are unchanged; regional metadata was not yet emitted.
            static const GuestStep identity[] = {{0, 0}};
            static const GuestChanged unchanged[] = {{0, 0}};
            code = data = identity; changed = unchanged;
            codes = datas = 1; changes = 0;
            code_lo = code_hi = data_lo = data_hi = 0;
            name = "USA"; title = "0005000010143500";
            return;
        }
        name = static_cast<char*>(required("g_guest_build_name", 3));
        title = static_cast<char*>(required("g_guest_build_title_id", 17));
        const bool usa = !memcmp(name, "USA", 3) &&
            !memcmp(required("g_guest_build_name", 4), "USA", 4);
        const bool eu = !memcmp(name, "EU", 3);
        if ((!usa && !eu) || memcmp(title, eu ? "0005000010143600" : "0005000010143500", 17))
            throw std::runtime_error("Unsupported game module region");
        codes = count("g_guest_code_step_count", 256);
        datas = count("g_guest_data_step_count", 256);
        changes = count("g_guest_changed_code_count", 128, true);
        code = static_cast<GuestStep*>(required("g_guest_code_steps", codes * sizeof(GuestStep)));
        data = static_cast<GuestStep*>(required("g_guest_data_steps", datas * sizeof(GuestStep)));
        changed = static_cast<GuestChanged*>(required("g_guest_changed_code", (changes ? changes : 1) * sizeof(GuestChanged)));
        code_lo = number("g_guest_code_lo"); code_hi = number("g_guest_code_hi");
        data_lo = number("g_guest_data_lo"); data_hi = number("g_guest_data_hi");
        auto check = [](const GuestStep* steps, unsigned n) {
            for (unsigned i = 0; i < n; ++i) {
                const int64_t target = int64_t(steps[i].start) + steps[i].delta;
                if ((i && steps[i-1].start >= steps[i].start) || target < 0 ||
                    target > std::numeric_limits<uint32_t>::max())
                    throw std::runtime_error("Invalid regional address steps");
            }
        };
        check(code, codes); check(data, datas);
        if (eu && (code_lo >= code_hi || data_lo >= data_hi))
            throw std::runtime_error("Missing European executable bounds");
        if (usa && (code_lo || code_hi || data_lo || data_hi))
            throw std::runtime_error("Invalid USA identity bounds");
        for (unsigned i = 0; i < changes; ++i)
            if (changed[i].start < code_lo || changed[i].start >= changed[i].end ||
                changed[i].end > code_hi || (i && changed[i-1].end > changed[i].start))
                throw std::runtime_error("Invalid regional changed-code range");
    }
    void install() const {
        g_guest_code_steps = code; g_guest_code_step_count = codes;
        g_guest_data_steps = data; g_guest_data_step_count = datas;
        g_guest_changed_code = changed; g_guest_changed_code_count = changes;
        g_guest_code_lo = code_lo; g_guest_code_hi = code_hi;
        g_guest_data_lo = data_lo; g_guest_data_hi = data_hi;
        g_guest_build_name = name; g_guest_build_title_id = title;
    }
};
}
void* wwhd_host_symbol(const char*);
extern "C" PpcFunc wwhd_module_function(const char* name) {
    return reinterpret_cast<PpcFunc>(required(name));
}
bool wwhd_load_game_module(const char* path, std::string& error) {
    if (!module.load(path, wwhd_host_symbol, error)) return false;
    try {
        const void* abi = required("wwhd_game_abi", sizeof(WWHD_MODULE_ABI));
        const bool legacy_usa = WWHD_CAN_LOAD_LEGACY_USA &&
            !memcmp(abi, WWHD_LEGACY_USA_ABI, sizeof(WWHD_LEGACY_USA_ABI));
        if (!legacy_usa && memcmp(abi, WWHD_MODULE_ABI, sizeof(WWHD_MODULE_ABI)))
            throw std::runtime_error("Game package is for a different app version; rerun its matching setup");
        auto funcs = *static_cast<unsigned*>(required("g_recomp_func_count", sizeof(unsigned)));
        auto imports = *static_cast<unsigned*>(required("g_recomp_import_count", sizeof(unsigned)));
        if (!funcs || funcs > 1000000 || imports > 65536) throw std::runtime_error("Invalid game tables");
#define REQUIRE_GAME_SYMBOL(name) required(name);
#include "required.inc"
#undef REQUIRE_GAME_SYMBOL
        const RegionMap region(legacy_usa);
        g_recomp_funcs = static_cast<RecompEntry*>(required("g_recomp_funcs", funcs * sizeof(RecompEntry)));
        g_recomp_imports = static_cast<RecompImport*>(required("g_recomp_imports", imports * sizeof(RecompImport)));
        g_recomp_func_count = funcs;
        g_recomp_import_count = imports;
        g_recomp_entry_point = *static_cast<uint32_t*>(required("g_recomp_entry_point", sizeof(uint32_t)));
        region.install();
        return true;
    } catch (const std::exception& ex) { error = ex.what(); return false; }
}
