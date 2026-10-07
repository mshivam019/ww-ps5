# Wind Waker HD PS5

Native PS5 port of [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp),
using direct Vulkan through [Mihawk's PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan).
Separate title ID **PPSA99641**. This repository remains private.

The release artifact is a **source/setup bundle**, not a prebuilt game. It creates
a private install folder from your own dump. See [release checks](RELEASING.md).

The executable builds and passes native SELF inspection and unresolved-import checks.
Console testing confirms rendering, controller input, manual-save persistence after
relaunch, the touchpad settings/mod menu, and the L3 + R3 GamePad-screen toggle.
Save-state creation was also confirmed after moving snapshots to M.2 storage.

## Graphics and controls

First-start targets: 3840x2160 output at approximately 60 Hz, 3x internal resolution
(3840x2160 from the game's 1280x720), and paced 60 FPS interpolation. Game logic
retains its normal 30 Hz clock.
Saved graphics options override the initial defaults, so resolution and interpolation
can be changed in the controller-accessible settings overlay.

DualSense Cross/Circle/Triangle/Square map to A/B/X/Y. Options maps to Start.
Click the touchpad to open or close the settings/mod menu. Press L3 + R3 together
to show or hide the Wii U GamePad screen. Options opens the game's own menu
when gameplay allows it. In settings, use the left stick to move the visible pointer
and Cross to click; the right stick scrolls. D-pad navigation is also available,
and L1/R1 switch tabs.
The GamePad screen is composited into the TV output rather than a desktop window.
Controller input and audio use the native SDL3 PS5 backend used by Dusklight.
Controller text entry uses the upstream overlay, not Sony's native keyboard.
The menu shortcuts and save reload have been confirmed on the console.

## Build on Linux

Requires Python 3.11+, Git, CMake, Ninja, clang/LLVM, make, curl, tar and the
prerequisites needed to build the pinned Mesa/RADV source. Python packages:

```sh
python3 -m venv .venv
.venv/bin/pip install pillow pycryptodome
```

Use your own **USA Wii U version 0** dump. An extracted `code/content/meta`
folder is accepted directly. To extract WUX first (keys stay in local files):

```sh
.venv/bin/python ps5/tools/prepare-game.py --image /path/to/game.wux --disc-key /path/to/game.key --common-key /path/to/common.key --output /path/outside/repository/game
```

Build dependencies, recompile the game and stage the private title:

```sh
.venv/bin/python ps5/tools/build.py --setup --build-radv --game /path/outside/repository/game --output /path/outside/repository/install/PPSA99641
.venv/bin/python ps5/tools/validate.py --title /path/outside/repository/install/PPSA99641
```

The dependency bootstrap uses published, pinned SDK, SDL3 and Vulkan source.
It can take substantially longer than an incremental game build. Existing
prepared dependencies can be supplied with `--sdk`, `--vulkan`, and `--sdl-source`
instead of `--setup`. `--jobs` defaults to 4. The release build was checked using
existing pinned dependencies; a full dependency bootstrap on a clean Linux
machine has not yet been verified. No Windows setup is provided in this release.

PlayStation prompts are downloaded and checked automatically. For offline setup,
add `--ps-prompts-archive /path/to/swapped.zip`. Extracted game files and generated
code stay local and must not be committed or included in a shareable archive.

## Private test package and installation

Install Pillow in the Python environment used for packaging:

```sh
python3 ps5/tools/package-local.py --game /path/outside/repository/game --vulkan /path/to/PS5_Vulkan --output /path/outside/repository/test/PPSA99641
python3 ps5/tools/package-local.py --output /path/outside/repository/test/PPSA99641 --validate-only
python3 ps5/tools/install.py --src /path/outside/repository/test/PPSA99641 --console 192.168.50.6
```

The package contains your extracted game and generated executable. Keep it private;
do not attach it to GitHub releases. The manifest records every file's size and
SHA-256. The installer requires FTP port 2121 and PS5 Upload control port 9114. It
refuses to update a running title, verifies raw stored sizes, and preserves user
data. Close Wind Waker HD before updating it. Register the installed folder
`/mnt/ext1/etaHEN/games/PPSA99641` through PS5 Upload or your native-title launcher.
FTP alone does not register or launch the game.

Saves and settings are in the persistent sandbox at `/download0/user/`.
Game saves are under `save/user/`; use the game's Save command before closing.
Full save states use `/app0/user/states/` in the installed title folder on M.2,
because memory snapshots can exceed the sandbox's storage allowance. Existing Dusklight,
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

## PlayStation prompts

The private test package includes pivotiii’s [PlayStation UI](https://gamebanana.com/mods/385841),
USA English swapped layout. It is enabled as a content mod on first installation.
Cross is A, Circle is B, Triangle is X and Square is Y. The mod does not include
USA French/Spanish replacements. Disable it in Mods and restart to restore the
original prompts. Existing profiles are preserved during updates. The asset pack is kept outside Git.

`package-local.py` includes this mod by default: it downloads the pinned archive
to `build/downloads/`, verifies SHA-256, and enables it for a new profile.
For offline packaging, pass `--ps-prompts-archive /path/to/swapped.zip`.
Use `--without-ps-prompts` to explicitly omit it. Existing profiles and disabled
mod choices are preserved; updating never silently re-enables a disabled mod.

To add the recorded mod download to an existing staged private title:

```sh
python3 ps5/tools/prepare-ps-prompts.py --archive /path/to/windwakerhd_ps_ui_swapped_a2747.zip --title /path/to/test/PPSA99641
python3 ps5/tools/package-local.py --output /path/to/test/PPSA99641 --validate-only
```

## Optional minimap

The upstream author has [demonstrated a GameCube-style minimap](https://www.reddit.com/r/decomps/comments/1wzf3qg/zelda_wind_waker_hd_recompdecomp_who_needed_the/).
As checked on October 7, no installable minimap package or source was found in
the public upstream repository or v0.2.3 release. It is not bundled or tested
on PS5. Use L3 + R3 to show/hide the GamePad screen for now. A future minimap
port should be optional and disabled by default.

## Credits

- [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp): original recompilation, runtime, mod manager and tools.
- [Mihawk](https://github.com/mihawk-99): [PS5 Vulkan](https://github.com/mihawk-99/PS5_Vulkan), [Mesa port](https://github.com/mihawk-99/PS5_Mesa), [Payload SDK](https://github.com/mihawk-99/PS5_PayloadSDK) and [native template](https://github.com/mihawk-99/PS5_VulkanTemplate).
- [premohq/PS5CEMU-HAR](https://github.com/premohq/PS5CEMU-HAR): PS5 Vulkan integration reference.
- [pivotiii](https://gamebanana.com/mods/385841): PlayStation button textures, downloaded separately during setup.
- SDL, Mesa/RADV, LLVM, Dear ImGui, Cemu shader code and the other upstream dependencies retain their original licenses and notices.

Not affiliated with Nintendo, Sony Interactive Entertainment or the upstream
projects. PlayStation and PS5 are Sony Interactive Entertainment trademarks.
Vulkan is a Khronos Group trademark; the PS5 RADV port is not a conformant product.
