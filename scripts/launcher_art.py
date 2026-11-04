"""The exe's icon: a star drawn here, no game art. build/work/kirby_redream.ico is written into kirby_redream.exe (Explorer,
shortcuts, taskbar) and copied to opensmash.ico, the file runtime/display.c loads for the game window's icon.

    python scripts/launcher_art.py [build folder [game folder]]      (default build, build/dump)

The settings page's fonts come from the player's game files too (game_fonts): they stay in build/ and are never committed.

Needs Pillow and lz4.
"""
import ctypes
import math
import os
import shutil
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_EXES = ('kirby_redream.exe',)
SIZES = (16, 24, 32, 48, 64, 128, 256)


def make_icon(work):
    from PIL import Image, ImageDraw
    n = 1024
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 20, n - 20, n - 20), fill=(255, 160, 200, 255), outline=(190, 60, 120, 255), width=36)
    star = [(n / 2 + (360 if i % 2 == 0 else 165) * math.sin(i * math.pi / 5), n / 2 - (360 if i % 2 == 0 else 165) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(star, fill=(255, 214, 64, 255), outline=(214, 120, 20, 255), width=24)
    ico = os.path.join(work, 'kirby_redream.ico')
    im.save(ico, sizes=[(s, s) for s in SIZES])
    shutil.copy2(ico, os.path.join(work, 'opensmash.ico'))
    return ico


def game_fonts(game, work):
    """The page's fonts, from the player's own game files: romfs/font/ScalableFontBin/*.bfotf.cmp (a u32 size + an LZ4 frame,
    then the words XORed with a key that follows from the known first word; the font starts at +8) -> work/ui."""
    import lz4.frame
    out = os.path.join(work, 'ui')
    os.makedirs(out, exist_ok=True)
    for src, dst in (('FOT-SeuratProN-EB', 'seurat_eb.otf'), ('FOT-RodinWanpakuPro-EB', 'seurat_b.otf')):
        with open(os.path.join(game, 'romfs', 'font', 'ScalableFontBin', src + '.bfotf.cmp'), 'rb') as f:
            data = lz4.frame.decompress(f.read()[4:])
        n = len(data) // 4
        words = struct.unpack('>%dI' % n, data[:n * 4])
        key = words[0] ^ 0x7f9a0218
        size = words[1] ^ key
        font = struct.pack('>%dI' % (n - 2), *[w ^ key for w in words[2:]])[:size]
        if font[:4] not in (b'OTTO', b'\x00\x01\x00\x00'):
            raise ValueError('%s: not a font after decoding' % src)
        with open(os.path.join(out, dst), 'wb') as f:
            f.write(font)
    return out


def stamp_icon(work):
    """work/kirby_redream.ico as the icon resource of ICON_EXES; -> the exes that could not be changed (missing, or running)."""
    if os.name != 'nt':
        return []
    with open(os.path.join(work, 'kirby_redream.ico'), 'rb') as f:
        ico = f.read()
    count = struct.unpack_from('<H', ico, 4)[0]
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.BeginUpdateResourceW.restype = ctypes.c_void_p
    k32.BeginUpdateResourceW.argtypes = (ctypes.c_wchar_p, ctypes.c_int)
    k32.UpdateResourceW.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ushort, ctypes.c_char_p, ctypes.c_ulong)
    k32.EndUpdateResourceW.argtypes = (ctypes.c_void_p, ctypes.c_int)
    failed = []
    for name in ICON_EXES:
        h = k32.BeginUpdateResourceW(os.path.join(work, name), 0)
        if not h:
            failed.append(name)
            continue
        group = struct.pack('<HHH', 0, 1, count)
        for i in range(count):
            w, hh, colors, res, planes, bits, size, off = struct.unpack_from('<BBBBHHII', ico, 6 + i * 16)
            k32.UpdateResourceW(h, 3, i + 1, 1033, ico[off:off + size], size)      # RT_ICON
            group += struct.pack('<BBBBHHIH', w, hh, colors, res, planes, bits, size, i + 1)
        k32.UpdateResourceW(h, 14, 1, 1033, group, len(group))                     # RT_GROUP_ICON
        if not k32.EndUpdateResourceW(h, 0):
            failed.append(name)
    return failed


def main():
    work = os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'build'), 'work')
    print('icon:', make_icon(work), 'not stamped:', stamp_icon(work))
    print('fonts:', game_fonts(sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'build', 'dump'), work))


if __name__ == '__main__':
    main()
