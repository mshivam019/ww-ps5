// Native startup uses the tested PS5 Vulkan Template platform contract.
#include <cstdlib>
#include <exception>
#include <cstdio>
#include <filesystem>
#include <sys/stat.h>
#include <unistd.h>
#include <SDL3/SDL.h>
#include "native/platform.h"
#include "storage.h"
extern "C" void catchReturnFromMain(int status);
extern "C" [[noreturn]] void __wrap_exit(int status) {
    catchReturnFromMain(status);
    for (;;) {}
}
extern "C" [[noreturn]] void __wrap__Exit(int status) { __wrap_exit(status); }
extern "C" [[noreturn]] void __wrap__exit(int status) { __wrap_exit(status); }
extern "C" [[noreturn]] void __wrap_abort() {
    say("Fatal game error; see the captured log");
    catchReturnFromMain(1);
    for (;;) {}
}
namespace interp { void set_mode(int); void set_paced_interpolation(bool); }
namespace gfxvk { void set_res_scale(float); }
int wwhd_main(int argc, char** argv);
int main() {
    platform_init("Wind Waker HD");
    // Opt-in timings for console diagnostics; no on-screen performance overlay.
    if (FILE* flag = fopen("/app0/ps5-perf.txt", "rb")) {
        const bool detailed = fgetc(flag) == '2';
        fclose(flag);
        setenv(detailed ? "WWHD_VK_STATS" : "WWHD_VK_CPU_ONLY_STATS", "1", 1);
        say("Rendering timing diagnostics enabled (%s)", detailed ? "detailed" : "lightweight");
    }
    // The PS5 render thread can exceed its frame budget on busy views. Use the
    // renderer's exact-match reuse paths; mutable guest data is still checked
    // before reuse, and submission/save-state invalidation remains in place.
    for (const char* name : {
             "WWHD_VK_REUSE_UNIFORM_SNAPSHOTS", "WWHD_VK_DESCRIPTOR_RANKS",
             "WWHD_VK_PIPELINE_LOOKASIDE", "WWHD_VK_SHADER_ADDRESS_MEMO",
             "WWHD_VK_FETCH_MEMO", "WWHD_VK_SPECIALIZE_INDICES",
             "WWHD_VK_SHADER_STATE_MEMO", "WWHD_VK_SAMPLER_MEMO",
             "WWHD_VK_SHADER_KEY_DIRTY", "WWHD_VK_REUSE_VERTEX_SNAPSHOTS",
             "WWHD_VK_SKIP_VERTEX_BINDS", "WWHD_VK_VERTEX_HISTORY_REUSE"})
        setenv(name, "1", 0);
    mkdir("/download0/user", 0777);
    mkdir("/download0/user/save", 0777);
    mkdir("/download0/user/captures", 0777);
    // The sandbox refuses chdir; all game paths are absolute.
    try {
        const std::filesystem::path bundled = "/app0/user/ModManager";
        const std::filesystem::path writable = "/download0/user/ModManager";
        if (std::filesystem::exists(bundled)) {
            std::filesystem::create_directories(writable);
            std::filesystem::copy(bundled / "Mods", writable / "Mods",
                std::filesystem::copy_options::recursive | std::filesystem::copy_options::skip_existing);
            if (!std::filesystem::exists(writable / "profiles.json"))
                std::filesystem::copy_file(bundled / "profiles.json", writable / "profiles.json");
        }
    } catch (const std::exception& error) { say("Mod setup: %s", error.what()); }
    SDL_Environment* environment = SDL_GetEnvironment();
    SDL_SetEnvironmentVariable(environment, "SDL_VIDEODRIVER", "dummy", true);
    SDL_SetEnvironmentVariable(environment, "SDL_AUDIODRIVER", "ps5", true);
    // Saved graphics preferences can override these initial targets at startup.
    gfxvk::set_res_scale(3.0f);
    interp::set_mode(1);
    interp::set_paced_interpolation(true);
    char app[] = "/app0/eboot.bin";
    char game_option[] = "--game";
    std::string game_path = "/app0/game";
    std::string save_path = "/download0/user/save";
    try {
        const std::string title = ps5_storage::title_id("/app0/sce_sys/param.json");
        const std::filesystem::path persistent = "/data/wwhd/" + title;
        const auto storage = ps5_storage::prepare({"/app0", persistent,
            std::filesystem::path("/data/prosperostore/previous") / title, "/download0"});
        game_path = storage.game.string();
        save_path = storage.save.string();
        setenv("WWHD_PS5_USER_DIR", storage.user.c_str(), 1);
        setenv("WWHD_STATE_DIR", storage.states.c_str(), 0);
        if (!storage.error.empty()) throw std::runtime_error(storage.error);
    } catch (const std::exception& error) {
        // The runtime selects its renderer before showing an actionable setup error.
        setenv("WWHD_PS5_STORAGE_ERROR", error.what(), 1);
    }
    platform_dismiss_splash();  // keep the launch picture visible during the first data copy
    say("Game data: %s", game_path.c_str());
    setenv("WWHD_PS5_GAME_LOCATION", game_path.c_str(), 1);
    char* game = game_path.data();
    char save_option[] = "--save";
    char* save = save_path.data();
    char trace[] = "--trace";
    char smoke[] = "--renderer-smoke";
    if (FILE* flag = fopen("/app0/ps5-display-test.txt", "rb")) {
        fclose(flag);
        char* test_args[] = {app, smoke, nullptr};
        say("[display] running renderer diagnostic without the game");
        return wwhd_main(2, test_args);
    }
    char* args[] = {app, game_option, game, save_option, save, nullptr, nullptr};
    int argc = 5;
    if (FILE* flag = fopen("/app0/ps5-trace.txt", "rb")) {
        fclose(flag); args[argc++] = trace;
        setenv("WWHD_LOG_BUTTONS", "1", 1);
    }
    try { return wwhd_main(argc, args); }
    catch (const std::exception& error) {
        say("Launch failed: %s", error.what());
        return 1;
    }
}
