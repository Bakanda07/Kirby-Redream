# KirbyRtDLDeluxe-recomp: development log

Static recompilation of *Kirby's Return to Dream Land Deluxe* (Switch, title 01006B601380E000, v0) to a native PC
program, built on the tree of [TomodachiLife-recomp](../TomodachiLife-recomp) (itself built on
[ssbu-recomp](../ssbu-recomp)).

No game code, assets or keys go in this repository. Everything derived from the game is made from your own dump into
`build/` (ignored by git).

Prior art: the 2011 Wii original has a static recompilation by ModernGekko. No port of the Deluxe (Switch) version was
found (2026-11-02).

## Status: Stage 1-1 plays and looks right (2026-11-03)

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
- Compute programs #105 (a placeholder blob) and #106 (`SUST` with the image handle in a register) are not translated;
  no visible effect found yet.
- The Vulkan renderer (`SSBU_RENDERER=vk`) stops at start: it supports only the upper-left origin with depth 0..1, and
  Kirby uses NVN's defaults (lower-left, -1..1).
- `SetBoldWeight` is not implemented by the font engine (glyphs stay regular).
- No `libopus` beside the exe: Opus streams are silent (`SSBU_OPUS_DLL`).
- Names are still Tomodachi's (`tomodachi_native.exe`, `tomodachi_game.dll`, `tomo.c`).

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

## Next steps

1. Listen to the audio (pitch, effects); libopus beside the exe (the installer fetches it) once a stage uses Opus.
2. Play further (more stages, copy abilities, bosses, saving) and fix what breaks.
3. Rename (`kirby_native.exe`, `kirby_game.dll`, `kirby.c`), setup / installer / launcher texts.
4. The port quality bar: 60 fps with even pacing, 4K and resolution scale, widescreen to 32:9 with the HUD placed for
   it, settings in the game's own menus, save anywhere, fast-forward, faster menus, quit to desktop, mods beyond
   LayeredFS, Steam Deck (Linux: Tomodachi is Windows only so far), updater.

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
set RECOMP_CLANG=<clang.exe> & set RECOMP_NOCRT=1 & set RECOMP_INLINE=0 & set RECOMP_DLL=tomodachi_game.dll
python build_opt.py main 12                              (game DLL)
set SDL3_ROOT=<SDL3 VC package> & set VULKAN_HEADERS=... & set IMGUI_ROOT=... & set RECOMP_EXE=tomodachi_native.exe
python build.py link                                     (host exe + game DLL)
set SSBU_ROMFS=..\dump\romfs & set SSBU_USERDATA=..\test_userdata & set SSBU_RENDERER=gl
tomodachi_native.exe ..\dump\exefs\main.elf 120          (120 s test run; SSBU_SHOT_EVERY=500 saves frames)
```

`nro_registry.c` and the empty strict-mode lists come from `scripts/setup.py` (`step_tables`).
