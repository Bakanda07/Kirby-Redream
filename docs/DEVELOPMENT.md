# Kirby: Redream: development log

Static recompilation of *Kirby's Return to Dream Land Deluxe* (Switch, title 01006B601380E000, v0) to a native PC
program, built on the tree of [TomodachiLife-recomp](../TomodachiLife-recomp) (itself built on
[ssbu-recomp](../ssbu-recomp)).

No game code, assets or keys go in this repository. Everything derived from the game is made from your own dump into
`build/` (ignored by git).

Prior art: the 2011 Wii original has a static recompilation by ModernGekko. No port of the Deluxe (Switch) version was
found (2026-11-02).

## Status (2026-11-06)

A new file plays from the title through the online prompt, the opening cinematic and the helper dialogs into Stage 1-1. The level
check below opened 107 rooms; every story room runs and draws right. Magolor's Epilogue is the open question. The game has not been
played from start to finish, and it has only run on an NVIDIA RTX 3060. Windows only for now: the Linux scripts and build steps were
taken out on 2026-11-06, while the POSIX and Android code merged from TomodachiLife-recomp stays in `runtime/` for later merges.

### Level check (2026-11-06)

A romfs mod swaps one room over the file behind a door the game can reach, and input is only A until the log (`SSBU_FSLOG=1`) shows
that file open, so loading times cannot throw it off. Each room gets three pictures, which were all looked at: "the game stayed
alive" says little on its own. The rooms are the first of every stage and all of each boss stage.

- 95 of 107 rooms ran. The "dark" frames in the results are loading screens.
- `Level7/Stage5/Step04` crashed behind the ship's door, in a script opcode reading the game's empty list of players (`0x710076ba98`,
  list at `+0x2ac8`). Behind Stage 1's door it runs, so this is the ship scene, not the room. Kirby loses a life there, as the room is
  normally entered riding from the room before.
- 12 of the 39 `MahoroaMode` rooms crash on a low address, for example `0x7100ff3188` reading `0x644` as Kirby reaches a blue pickup.
  Most likely these need Magolor as the player. Not proven: the mode unlocks after the story, so it has never run as itself here.

### Taken from TomodachiLife-recomp (2026-11-06)

Merged to its release commit `b7ba150` with a three-way merge per file, keeping Kirby's lower-left origin, widened targets and 32-byte
push constants: TEX.B through candidate arrays, fences for LDAR and STLR (a full re-lift), the image pool, the stream ring's reuse,
fewer state calls, and fixes from players' Steam Decks and Intel GPUs. Its later `perf/vk-draw-cost` branch is not merged.

- `SSBU_VK_RINGKEEP` is off for Kirby: with it on, the world map draws stale data in blocks. The cause is not found. The ring wraps
  rarely here, so the copies cost little.
- `build.py` recorded a file that failed to compile as up to date, so the next run linked its old object. Fixed here; Tomodachi's
  copy has the same bug.

Frame pacing at 2x scale (3840x2160 targets, RTX 3060, ship room, no screenshots): 59.7 fps, median 16.6 ms, p99 21 ms, 1 % low 47.

## Stage 1-1 plays and looks right (2026-11-03)

With scripted input (`SSBU_SCRIPT`, keyboard: Z = A, J = d-pad left, I / u = up, Enter = +) the lifted game goes title
-> Select File -> "connect online?" (Don't Connect) -> Mode Selection -> Story Mode -> the opening cinematic (webm
through Media Foundation) -> Helper Magolor -> Planet Popstar -> the Cookie Country map (a door is entered with Up) ->
the co-op tutorial cards -> Stage 1-1: Kirby runs, pushes star blocks, collects stars. Every screen checked so far draws
as on the console (scenery, lighting, reflections, text). 60 fps with 0.3 % late frames (43 of 15,037); steady play
holds 60 with 1 % lows of 57-59, the waits at screen changes are the game's loading. No trap and no host exception in any
run. The first picture comes 4.7 s after the start (was 16-53 s, see "Start-up time" below).

From a save (`build/fixtures/save_stage1`, copied to the test save folder) the menus lead to the Lor Starcutter hub;
Magolor's ship and its inside draw right too.

Audio (measured, not listened to): the renderer's mix (`TOMO_AUDIO_WAV=<file>`) carries the intro, title and menu music
and sounds at about -24 dBFS RMS, peaks near -8 dBFS, no clipping; it is silent while a movie plays, whose sound goes
through AudioOut (2,456 buffers, 1 underrun in a full run). No Opus decoder was created on any screen so far.

Known problems:
- Compute program #106 stores to an image whose handle register (R31) the program never sets; it is taken as image
  slot 0 (see "Compute" below). Not compared against the console.
- `SetBoldWeight` is not implemented by the font engine (glyphs stay regular).
- No `libopus` beside the exe: Opus streams are silent (`SSBU_OPUS_DLL`).
- Save now is not a save state: see "Quality bar" below.
- Internal names keep their history (`tomo.c`, `SSBU_*` and `TOMO_*` variables, `launcher_art.py`). Everything a player sees
  says Kirby: Redream.

## Quality bar (2026-11-06)

| Item | State |
|---|---|
| Beats emulation, 60 fps, even pacing | Done on an RTX 3060, not yet measured on any other GPU. Scene changes are where late frames fall |
| 4K, scale above native | Done: `resolution_scale` up to 2.0; the 3D is drawn at the window's size, not the console's 1440x810 |
| Widescreen up to 32:9, adaptive HUD | Done: wider camera, HUD and menus keep their shape; movies stay 16:9 |
| Easy install | Scripts ready. A one-file download needs a published release |
| Built-in updater | Done in code (PC Settings, Updates). Needs the GitHub repository to exist |
| Settings in the game's menus | Partly: PC Settings is a page in Kirby's colours and fonts, opened with F1, Home, holding - and +, or - on the game's menus, map and pause menu, where a prompt shows. It is not an entry in the game's own pause menu |
| Mods beyond textures | Done: romfs mods, DLL code mods (tested with a hook on the save writer), Skyline API |
| Steam Deck | **Set aside for now** at the owner's request: no native build, Proton not tested |
| Save anywhere | Partly: Save now (PC Settings) runs the game's own save at any moment. It does not bring back the exact spot in a stage |
| Fast-forward | Done (hold Tab or both sticks) |
| Faster menus, saves, loads | Partly: the clock runs 4x while the game opens files and 3x for 450 ms after a menu press. Other animations run at normal speed |
| Quit to desktop | Done, tested from PC Settings |

Save anywhere: a saved position needs the whole game state back. Lifted frames live on host stacks and NVN objects live in the
host and on the GPU, so a snapshot of guest memory alone cannot restore it. Save now calls the game's save request `0x71005333e8`
(w0 = 0), which leads to the writer `0x7100914388` on the save thread.

## The Vulkan renderer (2026-11-03)

Vulkan is the default again. OpenGL stays as the fallback (`renderer = opengl`, or no `ssbu_glslang.dll` beside the exe).
What Kirby needed:

- **Origin and depth**: NVN's defaults are lower left and -1..1. Vulkan's own mapping is already lower left's, so the viewport
  is not flipped and the winding is swapped. The present flips, and vertex stages convert z (`MxIn.depth_m11`).
- **c0**: vertex stages read c0 byte 0x644, which was bound to nothing: undefined values exploded the 3D into streaks. It reads
  as zeros now, as OpenGL's unbound block does. The validation layer found this one straight away.
- **Compute images**: 3D `rgba16f` images (#105 and #106), with storage views, GENERAL layout and a barrier after the dispatch.
- **Compute constants**: c1 comes from the front end's copy, because Kirby's code starts past a header of its own.
- **Counters**: `ReportCounter` writes `{count, timestamp}`; the count behind types 1-15 is 1, because no queries run here.
- **The start wait**: `nvn_front_warm_pending` was OpenGL's and never finished on Vulkan.
- **Scissor overflow**: Kirby's "no limit" scissor (2^31 - 1) overflowed to nothing when scaled, and no 3D was drawn.

## Widescreen and resolution (2026-11-03)

The game's camera aspect is a float literal (0x3FE38E39) at 16 sites. `recomp_eh.py` turns each into a read of
`game_aspect_p`, so the wider aspect reaches culling and every pass that rebuilds positions from depth. Squeezing vertices alone
left lighting on 16:9 matrices, and characters came out dark.

Screen-class targets (`rs_screen_class`) are 1920x1080 >> k and 1440x810 >> k with the COMPRESSIBLE flag. The flag is what keeps
movie planes out (1920x1080 R8, flags 4): widened, they stretched the story cutscenes. 2D at w = 1 is squeezed by `mx_wide_fix`.
A full-screen quad keeps its width only to read a widened target, a texture up to 512 wide (letterbox bars, gradients) or to fill.

## Shaders are prepared at install (2026-11-03)

`scripts/shader_store.py` takes every BNSH container out of romfs (`.bfsha`, `.bnsh`, and `.cmp` files: a u32 size + zstd): 4,745
containers, 43,145 variations, 320 MB. `setup.py` then runs the exe with `TOMO_PREPARE_ONLY=1`: 16,261 stage variants compiled in
3 minutes on 14 threads, 1.2 GB in `cache/vk`. A normal start then shows its first picture in 3.3 s. A new driver repeats this
behind the first-run screen. Nothing of it is committed: it is all made from the player's own game files.

## How it got there (2026-11-03)

1. **Lift**: `recomp_eh.py` now cuts a plain function longer than 32,768 instructions into pieces of about 16,384 that
   tail-call each other, only where no `goto` crosses the cut (`split_points`, with an assert). Kirby has a 415,154
   instruction registration function (`0x710053f0e4`, 9,873 copies of one block) that crashed clang 9 even unoptimised;
   it is now 26 pieces (`c_006f.c`), the 72k function of `c_00f3.c` 5 pieces. All pieces stay under the optnone mark.
2. **Compile**: 328 C files. The two re-lifted ones and the host exe were built with clang 23 (C:\Program Files\LLVM):
   clang 9 lived on the N: drive, which is gone, and its 69 MB download was not approved yet. C objects of the two
   versions link together (same C ABI). Host fixes clang 16+ needed: `nvn_vk.c` debug callback types, `#include <io.h>`
   in `nnfs.c`, an `osk_run` prototype in `osk.c`.
3. **SDK image**: Kirby's `sdk` ends at 0xda7000, past the 0xcfb000 reserved for Tomodachi's: `SDK_IMAGE_SIZE` is
   16 MB now (`sdklift.h`, `skyline.c`, `hostrt.c`).
4. **Imports**: 66 pure SDK functions lifted from Kirby's own `sdk` (block "Kirby's Return to Dream Land Deluxe" of
   `sdklift_roots.txt`: `nn::lmem` exp / unit heaps, TinyMt, UTF conversion, the audio renderer's client side,
   resampler, PerformanceInfo, `NumberLineAllocator` whole, the BFTTF / BFOTF decoder, musl helpers). 30 host handlers:
   `CommitSaveData`, `CleanDirectoryRecursively`, `TryWaitEvent`, thread name pointers, `GetSharedFont`, four hid
   calls, the event-less `OpenDefaultAudioOut`, `SetAudioOutVolume`, Opus work size / destructor, bcat / nfp / pdm /
   diag / ssl variants, `pthread_once`. `SSBU_STRICT=report` lists no function import without a handler.
5. **Fixes found by booting**:
   - `nn::pl::GetSharedFont` counts at most 6 fonts: the SDK's service arrays hold 6, and Kirby read a 7th entry it was
     never given (a stale heap pointer handed to `LoadFont`).
   - The font engine: `font_data` clamps a font to its readable bytes and rejects a file without a table directory
     instead of reading past it; up to 2048 engines (Kirby keeps more than 256).
   - The SDK's own `ScalableFontEngineHelper::Decode` (lifted): it marks a buffer decoded, and Kirby decodes each font
     twice; the host version scrambled it again on the second call.
   - `nvnSyncWait` on a sync that was never fenced answers ALREADY_SIGNALED: Kirby traps on FAILED.
   - `nvnCommandBufferCopyBufferToTexture` honours `NVN_COPY_FLAGS_MIRROR_X / MIRROR_Y`.
   - **Depth and origin modes**: Kirby never calls `nvnDeviceSetDepthMode` / `SetWindowOriginMode` and gets NVN's
     defaults, NEAR_IS_MINUS_W (clip z in -1..1) and LOWER_LEFT. The renderer started with SSBU's 0..1 and upper left:
     the depth range clipped Kirby's whole stage layer (Kirby, the ground, the doors) and kept the backdrop; the origin
     turned every picture that a post pass reads through `uv = pos * 0.5 + 0.5` upside down (the stage, the title
     backdrop, text drawn into its own target first). Both now start at NVN's values; the window blit
     (`job_present` `wflip`), `save_bmp` (shots, target dumps) and the album video frames follow the origin.
     `NVN_DEPTH_MODE` / `NVN_ORIGIN_MODE` override them (test). Dead ends on the way, for the record: the glyph rows
     (`SSBU_FONT_FLIPY=1` turns plain and target-drawn text over together), `CopyBufferToTexture` mirror flags (now
     honoured, but the glyphs do not come that way).
   - `movie::Extractor::SetDataSource(path)` resolves the game's own path (`content:/mov/EventMovie/Opening.webm`)
     through the file system's mounts (`fs_host_file`, mods first): Story Mode waited on that movie forever.
   - Tomodachi's speech log is off for these runs (`TOMO_SPEECHLOG=0`); it printed a line per audio update for Kirby's
     music voice.

## Start-up time (2026-11-03)

`SSBU_IMPORT_TIME=1` (hostrt.c) times every import, inclusive, and prints the 20 largest at exit. At the start
`ScalableFontEngine::LoadFont` took 10-19 s (1,410 calls: Kirby loads each of its 31 fonts into many engines). Each call
looked the font up by hashing the whole 2-5 MB file and by `VirtualQuery` over its pages, and `VirtualQuery` is slow on
the guest heap's huge region (the system checks every page of the region it reports). A font is now found from its
table directory (each entry carries its table's checksum) and the size it gives; the whole-file checks run once per new
font. Also: GDI glyph outlines take their own lock (`g_gdi_lock`) instead of the font table's. Result: 1,410 loads in
0.3 s, first picture at 4.7 s.

Test aid: `SSBU_SCRIPT_FROM_PRESENT=1` counts `SSBU_SCRIPT` seconds from the first presented frame.

The stalls at screen changes went with it: after the fix every 300-frame window from the start through the menus to the
Lor Starcutter averages 57-60 fps (the main thread was blocked 116 ms in all, about 2 s before).

## Compute (2026-11-03)

A third of all compute dispatches (17,344 of 49,807 in a run) were skipped: programs #105 and #106 run every frame
(work grids 10x9x8 and 10x9x1, which look like light clustering). Two causes:
- Kirby's compute binaries (data magic 0x12345679, SDK 13.3.5) hold another number at control +0x6f0 than Tomodachi's,
  which give the code offset there; the code is at +0x100. `compute_code_off` (nvn_gl.c) takes +0x100 when the given
  offset holds zeros.
- Both store to an image through a handle in a register (bindless `SUST`). The translator now remembers registers loaded
  from constant bank 2 (`MOV R, c[2][w]`, where NVN keeps image handles from word 72 on) and treats such a store as the
  bound image of that word (#105: `c[2][72]`, slot 0). #106's handle register R31 is set nowhere in the program; it is
  taken as slot 0 (an unbound slot would only drop the store).
Now every dispatch runs (47,337 of 47,337), no GL error, pictures unchanged where checked. `SSBU_SHADERDUMP` also writes
compute code (`b<n>_compute.bin`).

## Next steps

1. Listen to the audio (pitch, effects); libopus beside the exe (the installer fetches it) once a stage uses Opus.
2. Play the game from start to finish with a controller and fix what breaks. Bosses and copy abilities past Level 1 have only been
   opened, not played.
3. Test Magolor's Epilogue as itself, from a save that has finished the story, and find whether the 12 room crashes above are real.
4. Run it on AMD and Intel GPUs.
5. Publish: create the GitHub repository, then run `scripts/make_release.py`, pin its zip in `RUNTIME_RELEASE` (`scripts/install.py`)
   and run `scripts/make_setup.py`. The updater reads `version.txt` from that repository.
6. Put PC Settings into the game's own pause menu.
7. Every timed test run ends with `GUEST TRAP: nn::detail::UnexpectedDefaultImpl` after the clean shutdown. It has not shown up
   during play.
8. Find what `SSBU_VK_RINGKEEP` misses on the world map, and consider TomodachiLife-recomp's later Vulkan fixes.

## Feasibility study (2026-11-02)

| Check | Result |
|---|---|
| ExeFS | `main` (NSO 11.4 MB, ELF 22.1 MB), `sdk`, `subsdk0` (NintendoSDK movie), `rtld` |
| SDK | NintendoSDK 13.3.5 (SSBU is older, Tomodachi is 20.5.3) |
| Engine | HAL's own: no `sead`, `agl`, `xlink` or Havok. NintendoWare G3d / Ui2d / Font 13.3.5, Vfx2 13.3.0, Atk2 13.3.0 (sound), Fxt 1.57.0; NVN graphics |
| Lifter coverage (`recomp.py cover`) | 53,520 function entries; 4,467,644 words, 99.93% translated. The rest is not code: 3,244 zero words and 7 data words in `.text` (class0), 80 `e7ffdefe` trap words after calls that do not return (class3) |
| Exceptions | 1,424 functions with an LSDA, 5,427 landing pads, 144 functions entered through `nro_catch_call` (Tomodachi has none) |
| SDK imports by `main` | 719; 96 not imported by Tomodachi or SSBU (`build/imports_missing.txt`); of those, 30 had no handler at all |
| Movie library | `main` calls 28 `movie::` entries of `subsdk0`; all 28 are already named in the runtime |

## Reproduce

Paths are relative to the repository; `build/work` is the staged runtime and lifter (setup.py `stage`).

```
python ..\TomodachiLife-recomp\tools\extract\dump_folder.py "<Kirby RtDL Deluxe>.nsz" build\dump --exefs-only
python ..\TomodachiLife-recomp\tools\extract\nso2elf.py build\dump\exefs\main build\dump\exefs\main.elf   (also sdk, subsdk0)
cd build\work
set RECOMP_BIN=..\dump\exefs
python recomp_eh.py gen_eh_o2 12                         (lift)
python gen_imports.py & python gen_sdkdata.py & python gen_eh_tests.py & python gen_quad_tests.py
set SUYU_ROOT=<a yuzu-family source checkout> & python gen_sdktest.py
python sdklift.py gen                                    (after copying tools\lifter\sdklift_roots.txt here)
set RECOMP_CLANG=<clang.exe> & set RECOMP_NOCRT=1 & set RECOMP_INLINE=0 & set RECOMP_DLL=kirby_redream_game.dll
python build_opt.py main 12                              (game DLL)
set SDL3_ROOT=<SDL3 VC package> & set VULKAN_HEADERS=... & set IMGUI_ROOT=... & set RECOMP_EXE=kirby_redream.exe
python build.py link                                     (host exe + game DLL)
set SSBU_ROMFS=..\dump\romfs & set SSBU_USERDATA=..\test_userdata & set SSBU_RENDERER=gl
kirby_redream.exe ..\dump\exefs\main.elf 120          (120 s test run; SSBU_SHOT_EVERY=500 saves frames)
```

`nro_registry.c` and the empty strict-mode lists come from `scripts/setup.py` (`step_tables`).
