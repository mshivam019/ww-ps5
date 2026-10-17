# Separate app and game setup

Available in v0.1.2. The separate app and game module have been tested on PS5
firmware 9.00, including the missing-game screen, save loading, controls and menu.

The app contains the PS5 runtime and renderer. Your game code and assets stay
in a separate, locally prepared `game/` folder. This remains a native PS5 port.

## Player flow

1. Install the matching `PPSA99641.zip` app.
2. Extract the matching computer setup bundle. Run `Prepare-Game-Windows.cmd`,
   `Prepare-Game-macOS.command`, or `sh prepare-game.sh` on Linux.
3. Select your **USA or European/PAL Wii U version 0** dump: WUX or extracted `code`, `content`
   and `meta` folders. WUX extraction also needs your locally supplied keys.
4. With the game closed, copy `game/` to `/data/wwhd/PPSA99641/game` and merge any
   generated `user/` into `/data/wwhd/PPSA99641/user`. Keep existing saves and settings.
5. Launch Wind Waker HD from the PS5 home screen.

`game/game.wwhd` is the compiled game-code module. The adjacent `code`, `content`
and `meta` folders are also required. It is not a renamed ROM or a complete game
archive. Never distribute this module or the game assets.

GameCube `.gcm`, `.iso` and `.rvz` dumps are for the original Wind Waker and
cannot be used by this Wii U HD port. Supplying only `cking.rpx` is insufficient.

A missing or incompatible module opens a setup screen. Press Cross to exit.
Use the converter supplied with the app version: incompatible module interfaces
are rejected before starting the game. Preserve `game/` when replacing app files.

## Update protection

Prepared game files and user data are stored in `/data/wwhd/<TITLEID>/game` and
`/data/wwhd/<TITLEID>/user`, outside the app folder replaced by Store updates.
On the first launch, existing app-local game data is copied to a temporary
folder, verified byte-for-byte and renamed after completion. Existing persistent
files take priority; `/download0/user` saves are imported before app defaults.
The first copy needs writable `/data`, additional free space and time. The PS5
launch picture stays visible during this copy. Let one launch finish before
updating again. Originals are retained and interrupted imports can resume.

Top-level `.iso`, `.wud`, `.wux` and `.wua` images in the app folder are copied
and verified under `/data/wwhd/<TITLEID>/images`. Different files with the same
name get numbered names. An image is preserved as data; it still requires the
normal preparation step before this port can play it.

The app also checks `/data/prosperostore/previous/<TITLEID>` when available.
It cannot recover files already deleted before a completed import or guarantee
the behavior of a third-party updater. Backups on another drive need manual
recovery. A failed copy leaves the originals intact and shows a setup error.

The same app accepts USA and European modules. Existing USA v0.1.2 modules
retain their recorded ABI compatibility. New European modules require the
matching setup. Rendering defaults, controller mappings and the existing
settings UI are unchanged. The USA English prompt pack is omitted for Europe.

## Developer build

Run the existing dependency/SDL setup first. Build the app without a ROM:

```sh
python3 ps5/tools/build-catalog.py --sdk /path/to/sdk --vulkan /path/to/PS5_Vulkan \
  --sdl-build build/sdl3-ps5 --sdl-source /path/to/SDL --jobs 4
python3 ps5/tools/package-catalog.py --executable build/catalog-app/eboot.bin \
  --libc /path/to/PS5_Vulkan/runtime/libc.prx --output dist/catalog-test
```

The builder creates a placeholder runtime to discover its exported functions,
then builds the app with forwarding functions and a separate module loader.
No generated game instructions are linked into this app. The original monolithic
build is still available with `WWHD_GAME_MODULE=OFF` (the default).

The compiler bundle used by player setup is unchanged. To prepare private data:

```sh
python3 ps5/tools/setup.py --game-package --game /path/to/extracted-game \
  --output /path/to/private/PPSA99641
```

## Validation

```sh
python3 ps5/tests/test-module-loader.py
python3 ps5/tests/test-frame-pacing.py
```

This runs synthetic code through the module loader under address/undefined
behavior sanitizers: callbacks, weak import overrides, relocations, invalid
headers, invalid relocations, missing imports, exception unwinding and absent
files. It does not run the game. The actual locally generated module also passed
host binding checks; an incompatible interface marker was rejected.

Before publishing a new stable release or catalog submission, test the missing
module screen, normal launch, saves, controls, touchpad menu and GamePad toggle
on PS5. Host tests cannot verify console executable-memory permissions.

The catalog icon is original vector artwork in `ps5/art/catalog-icon.svg`,
licensed under this repository's MPL-2.0 license. It uses no extracted game art.
