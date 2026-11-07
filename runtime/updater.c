/* The updater behind PC Settings' Updates row. The version of the release is read from GitHub (only when the page is opened),
 * compared with version.txt of the player's copy (..\repo.txt names it: scripts/setup.py writes it), and "install" starts
 * scripts/install.py in a window of its own (its first step updates the project, the next ones build what changed); the game then
 * quits. No copy of the project known: the row says so. */
#include <stdio.h>
#include <string.h>
#include <windows.h>

#define UPDATE_HOST L"raw.githubusercontent.com"
#define UPDATE_PATH L"/Bakanda07/Kirby-Redream/main/version.txt"

/* winhttp.dll by name: the exe links without it */
typedef void *(WINAPI *OpenFn)(LPCWSTR, DWORD, LPCWSTR, LPCWSTR, DWORD);
typedef void *(WINAPI *ConnectFn)(void *, LPCWSTR, WORD, DWORD);
typedef void *(WINAPI *RequestFn)(void *, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR *, DWORD);
typedef BOOL (WINAPI *SendFn)(void *, LPCWSTR, DWORD, void *, DWORD, DWORD, DWORD_PTR);
typedef BOOL (WINAPI *ReceiveFn)(void *, void *);
typedef BOOL (WINAPI *ReadFn)(void *, void *, DWORD, DWORD *);
typedef BOOL (WINAPI *CloseFn)(void *);

static volatile LONG g_state;                     /* 0 not asked, 1 asking, 2 up to date, 3 a new version, 4 no answer, 5 no copy of the project */
static char g_repo[MAX_PATH], g_here[32], g_there[32];

static void trim(char *s) { size_t n = strlen(s); while (n && (s[n - 1] == '\r' || s[n - 1] == '\n' || s[n - 1] == ' ')) s[--n] = 0; }

static int read_text(const char *path, char *out, int n) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    size_t got = fread(out, 1, (size_t)n - 1, f);
    fclose(f);
    out[got] = 0;
    trim(out);
    return got > 0;
}

static DWORD WINAPI ask(void *arg) {
    char path[MAX_PATH + 32];
    (void)arg;
    if (!read_text("..\\repo.txt", g_repo, sizeof g_repo)) { g_state = 5; return 0; }
    snprintf(path, sizeof path, "%s\\version.txt", g_repo);
    if (!read_text(path, g_here, sizeof g_here)) { g_state = 5; return 0; }
    HMODULE m = LoadLibraryA("winhttp.dll");
    OpenFn open = m ? (OpenFn)GetProcAddress(m, "WinHttpOpen") : NULL;
    ConnectFn connect = m ? (ConnectFn)GetProcAddress(m, "WinHttpConnect") : NULL;
    RequestFn request = m ? (RequestFn)GetProcAddress(m, "WinHttpOpenRequest") : NULL;
    SendFn send = m ? (SendFn)GetProcAddress(m, "WinHttpSendRequest") : NULL;
    ReceiveFn receive = m ? (ReceiveFn)GetProcAddress(m, "WinHttpReceiveResponse") : NULL;
    ReadFn read = m ? (ReadFn)GetProcAddress(m, "WinHttpReadData") : NULL;
    CloseFn close = m ? (CloseFn)GetProcAddress(m, "WinHttpCloseHandle") : NULL;
    if (!open || !connect || !request || !send || !receive || !read || !close) { g_state = 4; return 0; }
    void *s = open(L"kirby-redream-update", 0, NULL, NULL, 0), *c = s ? connect(s, UPDATE_HOST, 443, 0) : NULL;
    void *r = c ? request(c, L"GET", UPDATE_PATH, NULL, NULL, NULL, 0x00800000 /* WINHTTP_FLAG_SECURE */) : NULL;
    DWORD got = 0;
    int ok = r && send(r, NULL, 0, NULL, 0, 0, 0) && receive(r, NULL) && read(r, g_there, sizeof g_there - 1, &got) && got;
    if (r) close(r);
    if (c) close(c);
    if (s) close(s);
    g_there[ok ? got : 0] = 0;
    trim(g_there);
    /* a version is digits and dots: a page of the host (404, a proxy's) is no answer */
    if (!ok || !g_there[0] || strspn(g_there, "0123456789.") != strlen(g_there)) { g_state = 4; return 0; }
    g_state = strcmp(g_here, g_there) ? 3 : 2;
    return 0;
}

void update_check(void) {
    if (InterlockedCompareExchange(&g_state, 1, 0) == 0) CloseHandle(CreateThread(NULL, 0, ask, NULL, 0, NULL));
}

void update_text(char *out, int n) {
    switch (g_state) {
    case 0: case 1: snprintf(out, (size_t)n, "Checking"); break;
    case 2: snprintf(out, (size_t)n, "Up to date (%s)", g_here); break;
    case 3: snprintf(out, (size_t)n, "Install %s", g_there); break;
    case 4: snprintf(out, (size_t)n, "No answer"); break;
    default: snprintf(out, (size_t)n, "Not available"); break;
    }
}

/* 1: started (the game should quit) */
int update_install(void) {
    char cmd[MAX_PATH * 3], py[MAX_PATH + 32];
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    if (g_state != 3) return 0;
    snprintf(py, sizeof py, "%s\\deps\\python\\python.exe", g_repo);      /* the installer's private Python, else the PC's */
    if (GetFileAttributesA(py) == INVALID_FILE_ATTRIBUTES) snprintf(py, sizeof py, "python");
    snprintf(cmd, sizeof cmd, "cmd /c \"\"%s\" \"%s\\scripts\\install.py\" --no-gui & pause\"", py, g_repo);
    memset(&si, 0, sizeof si); si.cb = sizeof si;
    if (!CreateProcessA(NULL, cmd, NULL, NULL, FALSE, CREATE_NEW_CONSOLE, NULL, g_repo, &si, &pi)) return 0;
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    return 1;
}
