// Native startup uses the tested PS5 Vulkan Template platform contract.
#include <cstdlib>
#include <exception>
#include <cstdio>
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
    mkdir("/app0/user", 0777);
    mkdir("/app0/user/save", 0777);
    mkdir("/app0/user/captures", 0777);
    // Relative diagnostic files stay alongside the writable settings and saves.
    if (chdir("/app0/user")) say("Could not enter writable user folder");
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
    char save[] = "/app0/user/save";
    char* args[] = {app, game_option, game, save_option, save, nullptr};
    try { return wwhd_main(5, args); }
    catch (const std::exception& error) {
        say("Launch failed: %s", error.what());
        return 1;
    }
}
