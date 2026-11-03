"""elf_imports.py <elf> [--defined]: undefined (imported) or defined (exported) dynamic symbol names, one per line."""
import struct, sys

d = open(sys.argv[1], 'rb').read()
shoff, = struct.unpack_from('<Q', d, 0x28)
shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 0x3A)
secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff + i * shentsize) for i in range(shnum)]
names = secs[shstrndx][4]
by = {d[names + s[0]:d.index(b'\0', names + s[0])].decode(): s for s in secs}
sym, st = by['.dynsym'], by['.dynstr']
want_defined = '--defined' in sys.argv
for off in range(sym[4], sym[4] + sym[5], 24):
    name_off, info, other, shndx = struct.unpack_from('<IBBH', d, off)
    if not name_off or (shndx != 0) != want_defined:
        continue
    print(d[st[4] + name_off:d.index(b'\0', st[4] + name_off)].decode())
