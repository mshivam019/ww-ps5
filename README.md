# Wind Waker HD for PS5

A native PS5 port of [ZeldaWWHDRecomp v0.2.3](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp), using the PS5 Vulkan runtime. Companion project to [Ocarina of Time](https://github.com/mshivam019/oot64-ps5), [Majora’s Mask](https://github.com/mshivam019/tmm64-ps5) and [Dusklight](https://github.com/mshivam019/dusklight-ps5) for PS5.

[Download v0.1.1](https://github.com/mshivam019/ww-ps5/releases/tag/ps5-v0.1.1) · [Installation and mods](ps5/README.md) · [Build from source](ps5/README.md#windows-macos-and-linux)

**Stable release.** Tested on PS5 firmware 9.00 with kstuff and ShadowMount.

## Features

- Native homebrew title **Wind Waker HD** (`PPSA99641`), launched from the PS5 home screen.
- 3840 × 2160 output with paced 60 FPS interpolation and the original 30 Hz game logic.
- PS5 controller input, audio, and an on-screen keyboard for name entry.
- Controller-operated settings, graphics options and mod menu.
- PlayStation button textures enabled by default during setup.
- Normal saves across restarts and save states stored on M.2.
- Show or hide the Wii U GamePad screen with a controller shortcut.

## Requirements

- A homebrew-capable PS5 with native folder-title support, FTP and a title registration/mounting setup.
- Your own **USA Wii U version 0** dump, or its extracted `code`, `content` and `meta` folders.
- A Windows, macOS or Linux computer with Python 3.11+ for setup and enough M.2 space for the game and save states.

The setup ZIP includes our prebuilt runtime and libraries. Game files, keys, saves and the generated game executable are not included.

## Installation

1. Download and extract the [setup ZIP](https://github.com/mshivam019/ww-ps5/releases/tag/ps5-v0.1.1).
2. Run **Setup-Windows.cmd** on Windows, **Setup-macOS.command** on macOS, or `sh setup.sh` on Linux. Choose your dump and wait for the finished `PPSA99641` folder. [First-time prerequisites](ps5/README.md#windows-macos-and-linux).
3. Close the game, then upload the generated folder to `/mnt/ext1/etaHEN/games/PPSA99641` using FTP or the included [installer](ps5/tools/install.py).
4. Register/mount the folder with your native-title launcher or PS5 Upload, then launch **Wind Waker HD** from the home screen.

Preserve the title’s save sandbox and `user/` folder when updating. FTP upload alone does not register the title.

## Controls and settings menu

| Control | Action |
| --- | --- |
| Touchpad | Open/close settings and mods |
| Options | Game pause/save menu |
| L3 + R3 | Show/hide the GamePad screen |
| Left stick / Cross in settings | Move pointer / select |
| Right stick in settings | Scroll |
| L1 / R1 in settings | Previous / next tab |
| Circle | Back or cancel |

Face buttons map to **Cross=A, Circle=B, Triangle=X, Square=Y**. Use the game’s Save command to keep normal progress; save states are available in the touchpad menu.

## Mods

The included setup enables [pivotiii’s PlayStation UI](https://gamebanana.com/mods/385841) for USA English. Open **Touchpad → Mods** to manage it and other compatible content mods. Existing disabled choices are preserved during updates.

See [mod setup and paths](ps5/README.md#mods) for details.

## Language configuration

1. Press **Touchpad**, then use **L1/R1** to open **Language / About**.
2. Under **Console language**, select **English**, **French** or **Spanish** with the pointer and Cross.
3. Save your game, close it and relaunch to apply the language.

This changes the emulated Wii U language, not your PS5 system language. The settings menu stays in English. PlayStation button textures currently cover English only; French and Spanish use the original prompts.

## Build and validate

See [build instructions](ps5/README.md#windows-macos-and-linux), [dependency pins](ps5/dependencies.json) and [release validation](ps5/RELEASING.md). The build creates a private installation from your dump; keep that generated package local.

## Credits and license

- [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp) and its [contributors](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp): the original recompilation, runtime and mod manager.
- [Mihawk](https://github.com/mihawk-99): [PS5 Vulkan](https://github.com/mihawk-99/PS5_Vulkan), [PS5 Mesa](https://github.com/mihawk-99/PS5_Mesa), [PayloadSDK](https://github.com/mihawk-99/PS5_PayloadSDK) and [native template](https://github.com/mihawk-99/PS5_VulkanTemplate).
- [John Törnblom](https://github.com/john-tornblom) and [ps5-payload-dev](https://github.com/ps5-payload-dev): the PS5 homebrew SDK.
- [BlackBearReloaded](https://github.com/blackbearreloaded): [native-app boilerplate](https://github.com/blackbearreloaded/ps5-native-app-boilerplate) underlying parts of the native runtime.
- [premohq](https://github.com/premohq/PS5CEMU-HAR): PS5 Vulkan integration reference.
- [pivotiii](https://gamebanana.com/mods/385841): PlayStation button textures, downloaded separately during setup.
- The [SDL](https://github.com/libsdl-org/SDL), [Mesa](https://gitlab.freedesktop.org/mesa/mesa), [LLVM](https://github.com/llvm/llvm-project), [Dear ImGui](https://github.com/ocornut/imgui) and other upstream contributors.

The project retains upstream’s [MPL-2.0 license](LICENSE). See [third-party notices](ps5/THIRD_PARTY_NOTICES.md) for the bundled libraries and tools. The linked PS5 platform uses GPL-3.0-or-later; dependencies retain their own licenses and notices.

Not affiliated with Nintendo or Sony Interactive Entertainment. PlayStation and PS5 are Sony trademarks. Vulkan is a Khronos Group trademark; the PS5 RADV port is not a conformant product.
