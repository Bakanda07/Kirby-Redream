# Kirby: Redream

A native PC port of *Kirby's Return to Dream Land Deluxe* (Nintendo Switch). The game's own code is translated to C and compiled
for your PC, so no emulator runs underneath.

**Nothing of the game is in this repository or in the downloads.** You build it on your own PC from your own copy of the game,
dumped from your own Switch, with your own console keys. Not affiliated with or endorsed by Nintendo or HAL Laboratory.

## What you need

- Windows 10 or 11, 64-bit, with about 15 GB free on the drive you install to.
- A GPU with Vulkan 1.3. Developed and tested on an NVIDIA RTX 3060. AMD and Intel GPUs have not been tested yet.
- **The base game** (`.nsp`, `.nsz` or `.xci`, title id `01006B601380E000`, version 1.0.0). Updates are not supported yet.
- Your console's **`prod.keys`**, dumped with Lockpick_RCM. The installer finds it in `%USERPROFILE%\.switch` or in an emulator's
  key folder. Key values are never copied or shown.

## Install

1. Download the project and unpack it, for example to `C:\Games\KirbyRedream`.
2. Double-click **`Install Kirby Redream.bat`**. It sets up a private copy of Python and opens the installer window.
3. The installer looks for your game files and keys by itself. Choose anything it missed, then press **Install**.
4. Start the game from the **Kirby Redream** shortcut on your desktop.

The first install compiles the game and every shader for your PC. That takes about half an hour on a fast PC, and it only happens
once. A new graphics driver compiles the shaders again when the game starts, in a few minutes.

## Settings

Press **F1**, the **Home** button, or hold **- and +** together for a second to open PC Settings. It works with a controller.

| Setting | What it does |
|---|---|
| Screen, Window size | Window, borderless or full screen |
| Resolution | 810p (the console's 3D), 1080p, 1620p or 4K, whatever your window size |
| Widescreen | Fits the screen, up to 32:9. The 3D shows more at the sides, while the HUD and menus keep their shape |
| Frame rate, Vsync | 60 or 30 fps. Even pacing comes from locking to your monitor when it runs at a multiple of 60 Hz |
| Fast-forward | Speed while you hold Tab or press both sticks: 2x, 3x or 4x |
| Faster loading | Runs the game 4x as fast while it opens files, so loading screens and their wipes pass quicker |
| Controls | Rebind any button for any controller or the keyboard |
| Updates | Shows whether a new version is out, and installs it |
| Quit to desktop | Closes the game |

Some settings take effect at the next start, and those are marked with `*`. All of them are also in `config\graphics.ini`, each with
an explanation.

## Mods

Put mods in the `mods` folder of your install. File mods (`romfs`) work as they do on an emulator, and code mods are DLLs that can
hook any function of the game. See [docs/MODS.md](docs/MODS.md).

## Steam Deck

Not tested yet. It should run through Proton, because the renderer is Vulkan and the game uses the whole screen on small displays:
build the game on a Windows PC, copy the install folder over, and add `work\kirby_redream.exe` to Steam as a non-Steam game.

## Known issues

- **There is no save anywhere.** The game saves where it normally does. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) says what stands
  in the way.
- PC Settings is a page of its own in the game's style, not an entry in the game's pause menu.
- Faster loading only helps while files are opening. Menus that load nothing run at normal speed.
- Cutscene movies stay 16:9 on an ultrawide screen, with bars at the sides.
- Copy abilities and bosses have not been played through yet. So far testing has covered the menus, the story opening, the map and
  Stage 1-1.

## For developers

[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) is the development log: how the port works, what was found and how to reproduce it.

## License

GPL-3.0, see [LICENSE](LICENSE). Based on TomodachiLife-recomp and ssbu-recomp.
