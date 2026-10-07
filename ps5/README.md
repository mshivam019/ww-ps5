# Wind Waker HD PS5 bring-up

This is a port of ZeldaWWHDRecomp's Wii U Wind Waker HD recompilation.
It is separate from BlueWake, which targets the GameCube game.
No playable PS5 executable has been produced yet.

## Current checks

- The supplied WUX header and sector index passed structural validation.
- Disc-key decryption passed, game extraction completed, and the extracted RPX
  matches upstream's supported USA version 0 SHA-256.
- Actual game translation produced 39,713 functions in 78 generated C files.
- The upstream host Vulkan smoke test passed upload, clear, blit, depth, triangle,
  GPU readback and swapchain presentation on the Linux laptop.
- Actual translated game code, PS5 runtime, GLSL/SPIR-V translator and renderer
  compile as static archives.
  Compiling an archive does not prove PS5 input, sound, graphics or gameplay.

## Prepare private game files

Use Python with pycryptodome installed. Supply key file paths, not key bytes:

```sh
python3 ps5/tools/prepare-game.py --image /path/to/game.wux --disc-key /path/to/game.key --common-key /path/to/common.key --output /path/outside/repository/game
python3 tools/recomp/recomp.py /path/outside/repository/game/code/cking.rpx build/gen
```

Keep extracted files, generated code, keys, saves and captures outside Git.
The existing build/ ignore covers generated code; keys and disc images are also ignored.

## Cross-compile

The initial bring-up reuses the already built PS5 SDK, native SDL3 and RADV headers
from our Dusklight development setup. These paths are supplied explicitly:

```sh
python3 ps5/tools/compile-runtime.py --sdk /path/to/ps5-payload-sdk --sdl-build /path/to/sdl3-ps5 --vulkan-headers /path/to/radv-release/include --generated build/gen
```

Omit --generated to compile placeholder game code for platform-only checks.
The output is a static runtime archive, not an installable title. Do not try to
launch placeholders as the game.

## Next work

1. Replace the SDL desktop Vulkan loader and surfaces with static RADV dispatch
   and VK_KHR_display. Preserve GamePad picture-in-picture in the TV surface.
2. Verify guest virtual-memory reservation, per-thread floating point state,
   paths, crash handling and save handling on the PS5 platform layer.
3. Link through the native RADV recipe, sign a separate title, and test renderer
   initialization before game launch. Do not overwrite Dusklight's title.
4. Verify opening, native/controller text entry, movement, audio, save and clean exit.

The game already uses direct Vulkan; Dawn/WebGPU is not part of this port.
Native downloadable mods and save-state support need separate PS5 verification.
The bring-up avoids Linux-only stack classification for save-state entry parking;
ordinary gameplay saves are separate from save states and still require testing.

## References and credits

- [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp): runtime,
  recompiler, renderer and Wii U library implementations (MPL-2.0).
- [Cemu](https://github.com/cemu-project/Cemu): vendored shader/address code with
  upstream notices retained.
- [PS5CEMU-HAR](https://github.com/premohq/PS5CEMU-HAR): reference for native Vulkan
  display, memory and controller integration. No emulator binary is deployed.
- [Mihawk](https://github.com/mihawk-99): PS5 Vulkan/Mesa and platform SDK.
- [BlackBearReloaded](https://github.com/blackbearreloaded): native runtime foundation.
- [ps5-payload-dev](https://github.com/ps5-payload-dev): homebrew SDK.

Original MPL notices remain intact. The native PS5 runtime's GPL-3.0-or-later
requirements must be included with any eventual combined binary and source release.
