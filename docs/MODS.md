# Mods

Everything goes in the `mods` folder beside the game's `work` folder (`<install location>\mods`; the game makes it). Each mod has
a folder of its own. Mods are read in name order, and the first mod that has a file wins.

## Files: textures, models, sound, text, levels

Put replaced files under `romfs`, with the game's own paths:

```text
mods\My Mod\romfs\gfx\Step\Chara\Kirby\Model.bfres.cmp
```

A folder that holds a `romfs` folder a few levels down also works, so most mods made for an emulator or a modded Switch work
unpacked as they are (`<title id>\My Mod\romfs\...`). Files that the game does not have are added.

## Code: gameplay and anything else

A code mod is a Windows DLL in the mod's folder. It runs before the game's first instruction and can hook any function of the
game. A hook sees all the guest registers, can change them, and decides whether the original runs:

```c
/* clang -shared -O2 my_mod.c -o "mods\My Mod\my_mod.dll" */
#include <stdint.h>

typedef struct { uint64_t x[32]; /* x[31] is SP; the vector registers and flags follow */ } Ctx;
typedef void (*ImportFn)(Ctx *c);
typedef struct {
    int version;                /* 1 */
    int (*hook)(uint64_t addr, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);
    int (*hook_name)(const char *mangled, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);
    int (*unhook)(int id);
    int (*log)(const char *fmt, ...);
} KirbyModApi;

static const KirbyModApi *api;
static ImportFn orig_save;

static void on_save(Ctx *c, void *user) {
    api->log("my mod: the game is writing its save file\n");
    orig_save(c);               /* leave this out to skip the original */
}

__declspec(dllexport) void kirby_mod_main(const KirbyModApi *a) {
    api = a;
    /* 0x7100914388: the function that writes a save file, in the base game 1.0.0 */
    a->log("my mod: hook %d\n", a->hook(0x7100914388ull, on_save, 0, &orig_save));
}
```

Things to know:

- Addresses are those of the game's `main` as loaded at `0x7100000000`. Hooks work on function entries, which is where the
  translated code can be entered. A hook on any other address returns 0.
- Guest addresses are real addresses in this process, so a mod reads and writes the game's memory through plain pointers.
- Arguments are in `x[0]`, `x[1]` and so on, and the return value goes in `x[0]`, as on the console.

## Skyline plugins

The Skyline plugin API is there too (`runtime/skyline.c`). Plugins are NROs and have to be lifted ahead of time with
`tools/nro/build_plugins.py`. Plugins are read from `sd\atmosphere\contents\01006B601380E000\romfs\skyline\plugins`.

## What does not work

`exefs` patches (`.ips`, `.pchtxt`) are not applied: the game's code is translated at install time, not read from the ExeFS when
it starts. The log says when a mod has an `exefs` folder. Write the change as a code mod instead.
