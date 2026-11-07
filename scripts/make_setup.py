#!/usr/bin/env python3
"""Build "dist/Kirby-Redream-PC-Setup.exe", the one download for players (and dist/Kirby-Redream-PC.zip, the same files as a
zip): launcher/setup.c compiled with clang, and in its resources the release's files (PAYLOAD: `git archive` of <ref>),
a manifest (common controls 6 for its dialog, no elevation, DPI aware) and an icon (drawn here: no game art is shipped).

    python scripts/make_setup.py [--ref v1.0.0] [--clang <clang.exe>] [--out dist]
"""
import argparse
import ctypes
import hashlib
import io
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from ctypes import wintypes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = 'Kirby-Redream-PC/'
NAME = 'Kirby-Redream-PC-Setup.exe'
MANIFEST = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="KirbyRedream.Setup" version="1.0.0.0" processorArchitecture="amd64"/>
  <description>Kirby: Redream Setup</description>
  <dependency><dependentAssembly><assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0"
    processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/></dependentAssembly></dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"><security><requestedPrivileges>
    <requestedExecutionLevel level="asInvoker" uiAccess="false"/></requestedPrivileges></security></trustInfo>
  <application xmlns="urn:schemas-microsoft-com:asm.v3"><windowsSettings>
    <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
    <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness></windowsSettings></application>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1"><application>
    <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/></application></compatibility>
</assembly>
'''


def git(*args):
    return subprocess.run(['git', '-C', REPO] + list(args), check=True, capture_output=True).stdout


def payload(ref):
    """the zip the setup unpacks: the repository at ref"""
    return git('archive', '--format=zip', '--prefix=' + PREFIX, ref)


def icon():
    """a yellow star on pink, 16-256 px, as .ico bytes"""
    from PIL import Image, ImageDraw
    big = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.ellipse((8, 8, 248, 248), fill=(255, 160, 200, 255), outline=(190, 60, 120, 255), width=10)
    star = [(128 + (92 if i % 2 == 0 else 42) * math.sin(i * math.pi / 5), 128 - (92 if i % 2 == 0 else 42) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(star, fill=(255, 214, 64, 255), outline=(214, 120, 20, 255))
    f = io.BytesIO()
    big.save(f, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return f.getvalue()


def stamp(exe, zipdata, ico):
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.BeginUpdateResourceW.restype = wintypes.HANDLE
    k32.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
    k32.UpdateResourceW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_char_p, wintypes.DWORD]
    k32.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]
    n = struct.unpack_from('<H', ico, 4)[0]
    entries = [struct.unpack_from('<BBBBHHII', ico, 6 + 16 * i) for i in range(n)]
    group = struct.pack('<HHH', 0, 1, n) + b''.join(struct.pack('<BBBBHHIH', *e[:7], i + 1) for i, e in enumerate(entries))
    h = k32.BeginUpdateResourceW(exe, False)
    ok = bool(h)
    ok = ok and bool(k32.UpdateResourceW(h, 24, 1, 0, MANIFEST, len(MANIFEST)))                           # RT_MANIFEST
    for i, e in enumerate(entries):
        ok = ok and bool(k32.UpdateResourceW(h, 3, i + 1, 0, ico[e[7]:e[7] + e[6]], e[6]))               # RT_ICON
    ok = ok and bool(k32.UpdateResourceW(h, 14, 1, 0, group, len(group)))                                # RT_GROUP_ICON
    name = ctypes.create_unicode_buffer('PAYLOAD')
    ok = ok and bool(k32.UpdateResourceW(h, 10, ctypes.addressof(name), 0, zipdata, len(zipdata)))     # RT_RCDATA
    ok = bool(h) and bool(k32.EndUpdateResourceW(h, not ok)) and ok
    if not ok:
        sys.exit('the resources could not be written into %s (error %d)' % (exe, ctypes.get_last_error()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ref', default='HEAD', help='the git tag or commit whose files the setup installs')
    ap.add_argument('--clang', default=os.environ.get('LAUNCHER_CLANG', r'C:\Program Files\LLVM\bin\clang.exe'))
    ap.add_argument('--out', default=os.path.join(REPO, 'dist'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    zipdata = payload(a.ref)
    with open(os.path.join(a.out, 'Kirby-Redream-PC.zip'), 'wb') as f:      # the same files as a zip (the release's other download)
        f.write(zipdata)
    exe = os.path.join(a.out, NAME)
    with tempfile.TemporaryDirectory() as tmp:
        built = os.path.join(tmp, 'setup.exe')
        subprocess.run([a.clang, '-O2', '-w', os.path.join(REPO, 'launcher', 'setup.c'), '-o', built, '-luser32', '-lshell32', '-lole32',
                        '-lcomctl32', '-luuid', '-Wl,/SUBSYSTEM:WINDOWS', '-Wl,/ENTRY:wWinMainCRTStartup'], check=True)
        stamp(built, zipdata, icon())
        shutil.copyfile(built, exe)                       # (the temporary folder may be on another drive)
    commit = git('rev-parse', '--short=10', a.ref + '^{commit}').decode().strip()
    print('%s  (%.1f MB): %s at %s' % (exe, os.path.getsize(exe) / 1048576, a.ref, commit))
    print('sha256: %s' % hashlib.sha256(open(exe, 'rb').read()).hexdigest())


if __name__ == '__main__':
    main()
