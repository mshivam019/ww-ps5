# Recomp mod manager

The mod manager installs, enables and configures mods from inside the game. No game
content is part of the repository or of mod packages; mods that need game data read it
from the player's own game files.

## Public project references (checked 2026-10-06)

- [Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp): its built-in
  manager installs mod files through a button or drag-and-drop, lists mods,
  allows enable/disable, and exposes configurable options. This is the user
  experience reference. Its packages target a different recomp runtime.
- [Its mod template](https://github.com/Zelda64Recomp/MMRecompModTemplate/blob/main/mod.toml):
  stable IDs, display metadata, versions, game targeting, dependency versions,
  and typed configuration belong in a manifest rather than scattered UI code.
- [BlueWake mod documentation](https://github.com/chrissotraidis/bluewake/blob/main/docs/MODS.md):
  BlueWake does have a Mods menu. It manages compiled options and texture
  replacement. Its translated code variants are prepared during the build;
  selecting them does not provide arbitrary runtime package installation.
  Its option-site and chunk-table system is useful architectural research,
  but differs from this Wii U recomp's generated functions and hook dispatch.
- [ModernGekko](https://github.com/ExpansionPak/ModernGekko): a GameCube/Wii
  runtime with native code-mod packages, a versioned ABI, dependency resolution
  and hook/patch registration. This is the loader reference. Its existing
  packages cannot be assumed ABI-compatible with this runtime.

No source from those projects has been copied into this mod manager. References
guide the design; any future reuse requires a separate license review.

## Player workflow

Open the in-game settings overlay (F1, Fn+F1 on many Macs, Cmd+, or Settings in
the menu) and select **Mods**. The searchable built-in catalogue manages the
mods that are part of this build: direct camera, mouse camera, first-person
shortcut, wall climbing, quick doors and fast scenes. Descriptions and options
appear beside the selected entry. All defaults are off.

The Installed packages section accepts a local folder or `.wwhdmod` ZIP. Choose
it with the file/folder picker, then press Install package. Installed packages
start disabled; nothing from a package is loaded until you enable it. Enabling
resolves required dependencies; missing versions, cycles, declared conflicts and
overlapping settings presets produce an error. The details show metadata, status
and bool/number/string/enum options. String edits commit with Enter. Disable a
package and wait for its next game update before updating or removing it.
Reinstall the same ID while disabled to update; configuration is preserved by
ID. Refresh discovers manual folder changes when all packages are disabled.

### Native code confirmation

Enabling a package with native code (`kind: native`) first shows a confirmation:
"<Mod name> contains native code. It runs with the game's full permissions and
can do anything a program on your computer can. Only enable mods from sources
you trust." **Enable** confirms and enables it; **Cancel** (the default button,
also B on a controller) leaves it disabled. If enabling a package would also
enable native dependencies that are not confirmed yet, the one dialog names all
of them. The dialog works with the mouse, the keyboard (Tab/arrows, Enter or
Space) and a controller (D-pad, A, B), on the AppKit and the SDL host.

The confirmation is asked once per package and native library: it is stored in
`profiles.json` as `native_trust`, mapping the package ID to the SHA-256 of the
package's library for this platform (the file named in `binaries`). It applies
to every profile. Installing an update whose library differs asks again;
removing a package forgets its confirmation. Only that one library is
fingerprinted; anything the library itself loads from its folder is not.
Built-in mods and settings presets never ask.

Native code is never loaded without a matching confirmation, also when a
profile switch, an older `profiles.json` or an updated library would enable it.
Such a package stays unloaded and is switched off in that profile, and the tab
shows "Not loaded: it contains native code you have not confirmed. Enable it
again to review." Ticking it again shows the confirmation. Packages that depend
on it report that a dependency failed to load, as for any failed load. The
manager API enforces this as well (`enable()` refuses unconfirmed native code;
`unconfirmed_native()` and `confirm_native()` serve the dialog).

Profiles save package toggles/configuration and built-in choices. Clone current
creates another profile; select it in Active profile. Switch away before deleting
a profile. Disable all covers both built-ins and external packages. Explicit
startup environment values, including zero, override saved choices at startup.

Storage is `<host config directory>/ModManager`: `Mods/<id>/manifest.json` plus
package files, and `profiles.json`. `WWHD_MOD_MANAGER_DIR` selects isolated
storage. `WWHD_NO_HOST_INPUT` skips user preferences and package storage unless
an explicit manager directory is supplied for a test. Game assets and saves
are never installed or redistributed by this manager.

Test aids (only with `WWHD_NO_HOST_INPUT`): `WWHD_TEST_TRUST_NATIVE_MODS=id[,id…]`
treats those native packages as confirmed without writing `native_trust`; it
also needs an explicit `WWHD_MOD_MANAGER_DIR`, so it never applies to a player's
storage. `WWHD_TEST_MOD_ENABLE=<id>` ticks that package's checkbox once when the
Mods tab is drawn (with `WWHD_TEST_OVERLAY=open:mods`), which shows the
confirmation for an unconfirmed native package.

## Native mod SDK v1

`runtime/include/wwhd_mod.h` defines a plain C ABI. Export
`wwhd_mod_init_v1`, validate host size/ABI, and return initialized `WWHDModV1`.
Initialization, configuration callbacks, game-update callbacks and unloading run
on the game thread. The frame callback runs once per original logic step after
actor execution; interpolated draws do not invoke it. Host/context pointers and
configuration strings remain valid until configuration changes or unload. Copy
strings if retaining them across either boundary. Callbacks must not throw or
start asynchronous guest-memory work; stop any owned workers before unloading.

Host services provide typed option access, a status line, logging and bounded
reads/writes of guest data RAM (MEM2, MEM1 and foreground bucket, maximum 1 MiB
per request). Bytes use guest big-endian order. Native packages execute trusted
host code with the same permissions as the game; the player confirms each
native library once before it loads (see Native code confirmation). Unload callbacks run when a
mod is disabled/profile-switched, before its library closes; process termination
is not a guaranteed cleanup callback.

This ABI supports frame-driven native mods. It does **not** provide arbitrary
translated-function interception, PPC instruction patch execution, texture
providers, or compatibility with Zelda64Recomp/BlueWake packages.

Package manifest fields:

| Field | Meaning |
| --- | --- |
| `format_version` | `1` |
| `id`, `name`, `version` | Stable lowercase ASCII identifier, display name, three-part version |
| `game_id` | `wwhd-usa` (the runtime also verifies its exact RPX entry) |
| `author`, `description` | Optional display metadata |
| `minimum_manager_version` | Optional three-part minimum |
| `kind` | `native` or `settings` |
| `abi_version`, `binaries` | Native ABI `1`; platform-to-relative-library map |
| `settings` | Settings preset: built-in IDs to booleans |
| `dependencies` | Objects with `id` and optional `minimum_version`; `builtin:<id>` allowed |
| `conflicts` | Package or `builtin:<id>` IDs |
| `options` | Typed defaults and names; numeric min/max/step or enum choices |

Platform keys include `macos-arm64`, `macos-x86_64`, `windows-x86_64`,
`windows-arm64`, `linux-x86_64`, `linux-arm64` and `android-arm64`.
Unsupported platform binaries remain visible as incompatible. The desktop
folder/file install workflow is the current supported UI; Android document URIs
need a separate import bridge. Online downloads/catalogues are outside v1.

## Packaging a mod

A package is a folder, or a ZIP archive of that folder's contents renamed to
`.wwhdmod`, with `manifest.json` at its root and, for a native mod, the library
named in `binaries`. Packages must not contain game files. Native packages run
with the same permissions as the game: install only mods you trust.

## Validation

The standalone `mod_manager` CTest checks defaults, saved settings, invalid
values, explicit environment precedence, persistence and test isolation.
`mod_packages` loads an independently compiled fixture library and exercises
install, profiles, missing dependencies, live configuration, disable/unload and
removal. It also checks the native confirmation: an unconfirmed library is not
enabled or loaded, a confirmed one loads in a second process on the same storage
without asking, a changed library asks again (also through a profile switch),
removal forgets the confirmation, settings presets never ask, and the test aid
applies without writing to `profiles.json`.
