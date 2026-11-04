#!/usr/bin/env python3
"""Start the built game.

    python scripts/run.py [--build <folder>] [--userdata <folder>] [--seconds N] [--env NAME=VALUE ...]

The exe also starts by itself (double-click, or the shortcut): it finds main.elf and the game files from its build folder.
"""
import argparse
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_location  # noqa: E402

EXE, GAME_DLL = 'kirby_redream.exe', 'kirby_redream_game.dll'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--build', help='build folder (default: the install location of build_location.txt, else <repo>/build)')
    ap.add_argument('--userdata', help='the save folder (default <build>\\userdata)')
    ap.add_argument('--seconds', type=int, default=0, help='stop after this many seconds (0 = play until you quit)')
    ap.add_argument('--env', action='append', default=[], help='NAME=VALUE for the game, may be repeated')
    a = ap.parse_args()
    build = os.path.abspath(a.build or build_location.get())
    work = os.path.join(build, 'work')
    if not (os.path.isfile(os.path.join(work, EXE)) and os.path.isfile(os.path.join(build, 'state.json'))):
        print('The game is not built yet (looked in %s): double-click "Install Kirby Redream.bat" first.' % build)
        return 1
    gone = [f for f in (GAME_DLL, 'SDL3.dll') if not os.path.isfile(os.path.join(work, f))]
    if gone:
        print('The game files are incomplete: %s missing in %s.\n'
              'Usually an antivirus removed it (Windows Security > Virus & threat protection > Protection history: restore it\n'
              'and allow it), or the installation stopped before the end. Double-click "Install Kirby Redream.bat" and press\n'
              'Resume: it makes the missing files again in a few minutes.' % (', '.join(gone), work))
        return 1
    with open(os.path.join(build, 'state.json')) as f:
        state = json.load(f)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RECOMP_', 'SSBU_'))}
    romfs = state['dump']['romfs']
    if not os.path.isdir(romfs) and os.path.isdir(os.path.join(build, 'dump', 'romfs')):
        romfs = os.path.join(build, 'dump', 'romfs')       # the folder was moved: state.json still names the old place
    env['SSBU_ROMFS'] = romfs
    env['SSBU_USERDATA'] = os.path.abspath(a.userdata or os.path.join(build, 'userdata'))
    env['SSBU_OS_CONSOLE_CORES'] = '1'
    env['SSBU_KEYBOARD_PLAYER'] = '1'
    if os.path.isdir(os.path.join(build, 'sysdata', 'fonts')):
        env['SSBU_FONTS'] = os.path.join(build, 'sysdata', 'fonts')
    for kv in a.env:
        k, _, v = kv.partition('=')
        env[k] = v
    os.makedirs(env['SSBU_USERDATA'], exist_ok=True)
    logs = os.path.join(build, 'logs')
    os.makedirs(logs, exist_ok=True)
    log = os.path.join(logs, time.strftime('game_%Y%m%d_%H%M%S.log'))
    print('Playing. The game log goes to %s. Close the game window to quit.' % log)
    cmd = [os.path.join(work, EXE), os.path.join(build, 'binaries', state.get('game_version', '1.0.0'), 'main.elf'), str(a.seconds)]
    t0 = time.time()
    with open(log, 'wb') as out:
        p = subprocess.run(cmd, cwd=work, env=env, stdout=out, stderr=subprocess.STDOUT)
    print('game exited with code %d after %.0f s' % (p.returncode, time.time() - t0))
    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
