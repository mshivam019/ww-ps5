# Release preparation

Keep `mshivam019/ww-ps5` private until the owner changes visibility.

The player ZIP contains source, our compiled PS5 runtime and native packaging
tools. It does not contain game code, a finished eboot, game assets or keys.
The setup recompiles the user's own dump and links it locally.

1. Run a full native build using `ps5/tools/build.py` and validate its title.
2. Capture the checked `link-game.sh` invocation with `LINK_TRACE=1`. Stage only
   reusable libraries using `ps5/tools/package-runtime.py`. The script excludes
   `libgamecode.a` and final executables; it retains the SDK's empty dependency
   archives, headers, clean-room libc, link maps and runtime libraries.
3. Build host packaging tools using `ps5/tools/build-host-tools.py` with Zig
   0.16.0, the pinned Vulkan source and its zlib 1.3.2 source. Both x86-64 and
   ARM64 tools are built for Windows, macOS and Linux.
4. Run player setup from a clean extracted release and validate the title.
   Record host testing separately from gameplay testing.
5. Commit source, then package the player and source ZIPs:

```sh
python3 ps5/tools/package-release.py --version v0.1.1 --runtime /path/to/runtime-bundle --host-tools /path/to/host-tools
python3 ps5/tools/package-release.py --version v0.1.1
python3 ps5/tools/validate.py --archive dist/Wind-Waker-HD-PS5-v0.1.1-setup.zip
```

Include dependency source archives and licenses alongside the setup release.
All release files carry SHA-256 checksums. The ZIP validator checks every file
against its manifest, checks the runtime manifest, and rejects game code,
finished eboots, images, keys, unsafe paths and unexpected binaries.

Use the owner's gh account, verify repository privacy, tag the packaged commit
and publish a **stable** release. Download its assets and validate them again.
Never replace published assets in place; use a new version.

Firmware 9.00 gameplay testing confirmed rendering, controller input, save
reload, menus and the GamePad toggle. The player setup is a packaging change;
its fresh compilation is not an additional console gameplay test.
