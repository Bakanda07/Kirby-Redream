/* Code mods. Every DLL in a folder under ..\mods (the folder a romfs mod goes in too: nnfs.c) is loaded before the game
 * starts and its exported `kirby_mod_main` is called with the API below. A mod hooks any lifted function of the game by its
 * address (or of the system library by its mangled name): it sees and changes the guest registers and calls the original.
 * Guest addresses are host addresses, so a mod reads and writes the game's memory directly. docs/MODS.md has an example.
 * Graphics.ini has nothing to say here: no DLL, nothing runs. */
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "hostrt.h"

int hook_install(uint64_t addr, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);      /* fighter_sdk/hook_host.c */
int hook_install_name(const char *name, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);
int hook_remove(int id);

typedef struct {
    int version;                                  /* KIRBY_MOD_API (docs/MODS.md), 1 */
    int (*hook)(uint64_t addr, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);
    int (*hook_name)(const char *mangled, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);
    int (*unhook)(int id);
    int (*log)(const char *fmt, ...);
} KirbyModApi;

void mods_load_plugins(void) {
    static const KirbyModApi api = {1, hook_install, hook_install_name, hook_remove, printf};
    const char *env = getenv("TOMO_MODS");
    char root[MAX_PATH], pat[MAX_PATH + 8], sub[MAX_PATH + 8];
    WIN32_FIND_DATAA d, f;
    snprintf(root, sizeof root, "%s", env && env[0] ? env : "..\\mods");
    snprintf(pat, sizeof pat, "%s\\*", root);
    HANDLE h = FindFirstFileA(pat, &d);
    if (h == INVALID_HANDLE_VALUE) return;
    do {
        if (!(d.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || d.cFileName[0] == '.') continue;
        snprintf(sub, sizeof sub, "%s\\%s\\*.dll", root, d.cFileName);
        HANDLE g = FindFirstFileA(sub, &f);
        if (g == INVALID_HANDLE_VALUE) continue;
        do {
            char path[MAX_PATH * 2];
            snprintf(path, sizeof path, "%s\\%s\\%s", root, d.cFileName, f.cFileName);
            HMODULE m = LoadLibraryExA(path, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
            void (*entry)(const KirbyModApi *) = m ? (void (*)(const KirbyModApi *))GetProcAddress(m, "kirby_mod_main") : NULL;
            printf("mods: %s: %s\n", path, !m ? "cannot be loaded" : !entry ? "exports no kirby_mod_main: not used" : "code mod started");
            fflush(stdout);
            if (entry) entry(&api);
        } while (FindNextFileA(g, &f));
        FindClose(g);
    } while (FindNextFileA(h, &d));
    FindClose(h);
}
