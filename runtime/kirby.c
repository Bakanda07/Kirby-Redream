/* What is Kirby's own in the host.
 * Save now: PC Settings asks, and the game's next present calls the game's own save request (0x71005333e8, w0 = 0 as most of
 * its 30-odd callers pass: it queues the current file for the save thread and shows the game's "now saving" mark), so nothing
 * is written behind the game's back.
 * Which screen: the pause screen's update (0x71010c5ad8) and the title menus' update (0x7100b37828) run once a frame only while
 * those screens are up (found with a code mod that counted calls, 2026-11-04). PC Settings shows its prompt there, and a press
 * of A, B or + there runs the clock fast for the transition that follows (faster menus; display.c). */
#include <windows.h>
#include "hostrt.h"

#define KIRBY_MAIN_TEXT_SIZE 0x110aef0ull
#define KIRBY_SAVE_REQUEST 0x71005333e8ull
#define KIRBY_PAUSE_UPDATE 0x71010c5ad8ull
#define KIRBY_MENU_UPDATE 0x7100b37828ull
#define KIRBY_BURST_MS 450

int hook_install(uint64_t addr, void (*repl)(Ctx *, void *), void *user, ImportFn *orig);      /* fighter_sdk/hook_host.c */
uint64_t nnhid_game_buttons(void);                /* bit 0 A, 1 B, 10 + */

int g_game_is_kirby(void) { return g_main.text_size == KIRBY_MAIN_TEXT_SIZE; }

static volatile LONG g_save_wanted;
static volatile LONG64 g_saved_at, g_pause_tick, g_menu_tick, g_burst_until;
static ImportFn g_pause_orig, g_menu_orig;

static void pause_hook(Ctx *c, void *user) { (void)user; g_pause_tick = (LONG64)GetTickCount64(); g_pause_orig(c); }
static void menu_hook(Ctx *c, void *user) { (void)user; g_menu_tick = (LONG64)GetTickCount64(); g_menu_orig(c); }
static int recent(LONG64 tick) { return tick && (LONG64)GetTickCount64() - tick < 100; }

void kirby_install(void) {
    if (!g_game_is_kirby()) return;
    int a = hook_install(KIRBY_PAUSE_UPDATE, pause_hook, NULL, &g_pause_orig), b = hook_install(KIRBY_MENU_UPDATE, menu_hook, NULL, &g_menu_orig);
    printf("kirby: screen hooks %s\n", a && b ? "installed" : "NOT installed (no prompt in the game's menus, no faster menus)");
}

/* the game's pause screen or title menus are up */
int kirby_menu_up(void) { return recent(g_pause_tick) || recent(g_menu_tick); }
/* a menu transition is under way (display.c) */
int kirby_fast_now(void) { return g_burst_until && (LONG64)GetTickCount64() < g_burst_until; }

void menu_notice(const char *text);               /* menu.cpp */
static volatile LONG64 g_notice_until;
void kirby_online_notice(void) {
    menu_notice("Online features aren't available in Kirby: Redream.\nChoose Don't Connect to keep playing.");
    g_notice_until = (LONG64)GetTickCount64() + 5000;
}

void kirby_save_now(void) { InterlockedExchange(&g_save_wanted, 1); }
/* milliseconds since the last save asked for here, -1 if none */
long long kirby_save_age(void) { return g_saved_at ? (long long)GetTickCount64() - g_saved_at : -1; }

void kirby_frame(Ctx *c) {                        /* the game's thread, at nvnQueuePresentTexture */
    static uint64_t prev;
    if (!g_game_is_kirby()) return;
    uint64_t b = nnhid_game_buttons(), down = b & ~prev;
    prev = b;
    if ((down & 1u << 10) || (kirby_menu_up() && (down & 3u))) g_burst_until = (LONG64)GetTickCount64() + KIRBY_BURST_MS;
    if (g_notice_until && (LONG64)GetTickCount64() >= g_notice_until) { g_notice_until = 0; menu_notice(NULL); }
    if (!g_save_wanted || !InterlockedExchange(&g_save_wanted, 0)) return;
    Ctx *saved = malloc(sizeof *saved);
    if (!saved) return;
    *saved = *c;                                  /* the import's own arguments stay as they were */
    c->x[0] = 0;
    call_guest(c, KIRBY_SAVE_REQUEST);
    *c = *saved;
    free(saved);
    g_saved_at = (LONG64)GetTickCount64();
    printf("kirby: save now: the game's save request made\n");
    fflush(stdout);
}
