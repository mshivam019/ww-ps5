# Prebuilt runtime and tools

The setup ZIP includes reusable libraries compiled from the pinned public
sources in `dependencies.json`, plus native packaging tools. It excludes
`libgamecode.a` and final game executables. Users generate those from their dump.

- PS5 payload SDK/platform and native Vulkan tooling: GPL-3.0-or-later, with
  BSD-licensed FreeBSD headers and other per-file exceptions. Full fork source
  is supplied in the release's dependency-source archive.
- SDL3: zlib license. The pinned PS5 fork source is in that archive.
- Mesa/RADV: MIT and other per-file licenses. Full pinned source and notices
  are in that archive.
- glslang, LZ4 and zlib: their original licenses and source are in the same archive.
- LLVM libc++, libc++abi, libunwind and compiler-rt: Apache-2.0 with LLVM
  exceptions. License retained in `licenses/LLVM.txt`. The SDK runtime uses
  LLVM 18.1.8; the clean Linux build's compiler builtins use LLVM 23.1.1.
  Source: https://github.com/llvm/llvm-project (tags llvmorg-18.1.8 and llvmorg-23.1.1).
- Host packaging tools use the pinned Vulkan tooling, zlib 1.3.2 and Zig 0.16.0
  cross-compilation. Zig's libc++ and platform runtime licenses are retained in
  its [source distribution](https://ziglang.org/download/0.16.0/zig-0.16.0.tar.xz).
  The Linux tools statically link musl (MIT); its notice is included below.
- Cemu, Dear ImGui, fmt and the other vendored runtime pieces retain their
  notices in `runtime/third_party`.

Portable compiler downloads are verified against the SHA-256 pins in
`toolchains.json`. They retain their own license files when extracted locally.
The player does not need the dependency-source archive to run setup. It provides
the corresponding source for the compiled libraries and is available with the
same release, together with this repository's source/setup ZIP and build scripts.
