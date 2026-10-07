// Native startup uses the tested PS5 Vulkan Template platform contract.
#include <cstdlib>
#include <exception>
#include <cstdio>
#include <filesystem>
#include <sys/stat.h>
#include <unistd.h>
#include <SDL3/SDL.h>
#include "native/platform.h"
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
    char game[] = "/app0/game";
    char save_option[] = "--save";
    char save[] = "/download0/user/save";
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
