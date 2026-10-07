# Wind Waker HD PS5

Native PS5 port of [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp),
using direct Vulkan through [Mihawk's PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan).
Separate title ID **PPSA99641**. This repository remains private.

The complete game executable compiles, links and passes the native SELF inspection
and unresolved-import check. Console launch, gameplay, saves, audio and performance
are still unverified. A successful build does not establish a playable port.

## Graphics and controls

First-start targets: 3840x2160 output at approximately 60 Hz, 3x internal resolution
(3840x2160 from the game's 1280x720), and paced 60 FPS interpolation. Game logic
retains its normal 30 Hz clock. These are targets, not measured PS5 performance.
Saved graphics options override the initial defaults, so resolution and interpolation
can be changed in the controller-accessible settings overlay.

DualSense Cross/Circle/Square/Triangle map to A/B/X/Y. Options maps to Start.
Hold the touchpad button (Select) to open the upstream settings/mod menu.
The GamePad screen is composited into the TV output rather than a desktop window.
Controller input and audio use the native SDL3 PS5 backend used by Dusklight.
Controller text entry uses the upstream overlay, not Sony's native keyboard.
These mappings still need verification in this game on the console.

## Build from your own USA Wii U version 0 dump

Use Python with pycryptodome installed. Supply key file paths, not key bytes:

```sh
python3 ps5/tools/prepare-game.py --image /path/to/game.wux --disc-key /path/to/game.key --common-key /path/to/common.key --output /path/outside/repository/game
python3 tools/recomp/recomp.py /path/outside/repository/game/code/cking.rpx build/gen
python3 ps5/tools/build-native.py --sdk /path/to/ps5-payload-sdk --sdl-build /path/to/sdl3-ps5 --sdl-source /path/to/SDL --vulkan /path/to/PS5_Vulkan
```

Dependencies are recorded in `ps5/upstream.json`. The initial build reuses the
verified Dusklight SDK, SDL3 and static RADV stack. `build-native.py` translates no
game itself: prepare `build/gen` first. `compile-runtime.py` without `--generated`
uses placeholders for compilation checks only. Never package those as a game.

## Private test package and installation

Install Pillow in the Python environment used for packaging:

```sh
python3 ps5/tools/package-local.py --game /path/outside/repository/game --vulkan /path/to/PS5_Vulkan --output /path/outside/repository/test/PPSA99641
python3 ps5/tools/package-local.py --output /path/outside/repository/test/PPSA99641 --validate-only
python3 ps5/tools/install.py --src /path/outside/repository/test/PPSA99641 --console 192.168.50.6
```

The package contains your extracted game and generated executable. Keep it private;
do not attach it to GitHub releases. The manifest records every file's size and
SHA-256. The installer uses FTP port 2121, verifies stored sizes and preserves user
data. Close Wind Waker HD before updating it. Register the installed folder
`/mnt/ext1/etaHEN/games/PPSA99641` through PS5 Upload or your native-title launcher.
FTP alone does not register or launch the game.

Saves and settings are under the title's `user/` directory. Existing Dusklight,
Morrowind and other titles are not replaced. Keys, game files, derived code, captures
and saves must stay outside Git.

## Mods

The upstream mod manager supports `.wwhdmod` content/settings packages and imports
Cemu graphics packs. Native desktop mod libraries cannot run on this PS5 build.
Read upstream `docs/mod-manager.md` for package layouts and install/restart behavior.
PS5 mod installation is not yet verified. Do not assume Dolphin texture packs work:
Henriko's Wind Waker 4K pack targets the GameCube/Dolphin version, while this port
uses the Wii U HD game. No compatible replacement texture pack has been confirmed.
The initial private test package retains the original Wii U HD textures.

## Credits and licenses

- [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp): recompilation, runtime, renderer and mod manager.
- [Mihawk](https://github.com/mihawk-99): PS5 graphics/platform tooling and Vulkan Template.
- [premohq/PS5CEMU-HAR](https://github.com/premohq/PS5CEMU-HAR): Wii U PS5 integration reference.
- SDL, Mesa/RADV, glslang, Cemu, Dear ImGui and other upstream dependencies retain their licenses.

The original project is MPL-2.0. Imported template files retain MIT notices.
The linked SDK/native runtime has GPL-3.0-or-later obligations; any distributed
port binaries require the corresponding platform source and license notices.
No public binary distribution is prepared here. Not affiliated with Nintendo or Sony.
