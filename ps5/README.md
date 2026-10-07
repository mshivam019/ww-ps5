# Setup and installation

The release builds **PPSA99641** from your own **USA Wii U version 0** dump.
Use an extracted folder containing `code`, `content` and `meta`, or a WUX image
with your own disc key and Wii U common key files. Other regions and revisions
are rejected before compilation.

## Windows, macOS and Linux

Install **Python 3.11 or newer**, then extract the setup release ZIP. No Docker,
WSL, SDK installation or manual compiler setup is needed.

1. **Windows:** double-click `Setup-Windows.cmd`. **macOS:** open `Setup-macOS.command` (or run `sh setup.sh`). **Linux:** run `sh setup.sh`.
2. Enter your WUX file or extracted game folder path and press Enter.
3. Wait for “Ready”. Your finished `Wind-Waker-HD-PS5-install/PPSA99641` folder is beside the setup folder.

For WUX, setup looks for a same-named `.key` and `common.key` beside the image.
If missing, it asks for their paths. Keys stay on your computer.

Our runtime, graphics libraries and packaging tools are already built. Setup
automatically downloads a verified portable compiler, compiles only the code
from your dump, adds PlayStation prompts and checks the finished files. Windows,
macOS and Linux releases support x86-64 and ARM64 computers. Internet access and
space for your dump, tools and final game folder are required.

The commands below are optional alternatives.

Windows PowerShell, using an extracted game:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 --game "D:\Games\Wind Waker HD" --output "D:\PS5\PPSA99641"
```

Linux or macOS:

```sh
sh setup.sh --game "/path/to/Wind Waker HD" --output "/path/to/install/PPSA99641"
```

For a WUX, replace `--game` with the image and key-file arguments:

```sh
sh setup.sh --image "/path/to/game.wux" --disc-key "/path/to/game.key" --common-key "/path/to/common.key" --output "/path/to/install/PPSA99641"
```

The same arguments work with `setup.ps1`. Keys stay in local files. The scripts
extract the game, use our prebuilt libraries, compile the game code, add the PlayStation prompts
and validate every packaged file. The output must be a new folder named
`PPSA99641`. Game files and generated executables stay on your computer.

Use `--jobs 2` to reduce compilation memory use. Compiler downloads are cached
for future attempts. The game and installation still run on PS5; these scripts
run on your computer only to prepare its files.

## Install on PS5

1. Close Wind Waker HD if it is running.
2. Upload the generated `PPSA99641` folder to `/mnt/ext1/etaHEN/games/PPSA99641`.
   Use FTP, or the included installer with FTP and PS5 Upload running:

   ```sh
   python3 ps5/tools/install.py --src /path/to/install/PPSA99641 --console YOUR_PS5_IP
   ```

   On Windows, use `py -3` instead of `python3`.
3. Register/mount the folder using PS5 Upload or your native-title launcher.
4. Launch **Wind Waker HD** from the PS5 home screen.

The installer preserves existing settings and saves, checks stored file sizes
and refuses to update the running title. FTP upload alone does not register it.
Normal saves and settings live in `/download0/user/`; save states use the title's
`user/states` directory on M.2. Preserve both when updating.

## Controls, mods and languages

See the [main README](../README.md#controls-and-settings-menu) for controller
shortcuts and [language configuration](../README.md#language-configuration).

The setup downloads and verifies [pivotiii's PlayStation UI](https://gamebanana.com/mods/385841)
and enables it for a new profile. Existing disabled choices are preserved.
Cross=A, Circle=B, Triangle=X and Square=Y. The pack replaces English prompts;
French and Spanish retain the original prompts.

Open **Touchpad → Mods** to manage compatible content mods. The upstream mod
manager supports `.wwhdmod` content/settings packages and Cemu graphics packs.
See [package layouts](../docs/mod-manager.md). Desktop native mod libraries and
Dolphin texture packs cannot be used directly. L3 + R3 shows the GamePad map.

## Native Linux build

For developers who already have clang/LLVM, Mesa build prerequisites, CMake,
Ninja, make, Git, curl, wget, rsync and Python 3.11+:

```sh
python3 -m venv .venv
.venv/bin/pip install pillow pycryptodome
.venv/bin/python ps5/tools/build.py --setup --build-radv --game /path/to/game --output /path/to/install/PPSA99641
.venv/bin/python ps5/tools/validate.py --title /path/to/install/PPSA99641
```

[Dependency pins](dependencies.json) record the sources and revisions.
For standalone WUX extraction, use `ps5/tools/prepare-game.py` with
`--image`, `--disc-key`, `--common-key` and a new `--output` folder outside the repo.

## Release checks

[RELEASING.md](RELEASING.md) documents packaging and validation. Releases contain
source and setup tools, without game data, keys or game-derived executables.
