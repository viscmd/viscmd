import json
import os
import subprocess
import sys
import tempfile

deepin_terminal = ''
gnome_terminal = ''


def check():
    global deepin_terminal
    global gnome_terminal
    out = subprocess.getoutput('which deepin-terminal')
    deepin_terminal = out.strip()
    out = subprocess.getoutput('which gnome-terminal')
    gnome_terminal = out.strip()
    if deepin_terminal == '' and gnome_terminal == '':
        return False
    else:
        return True


def run(cmdline: str):
    if deepin_terminal != '':
        subprocess.call([deepin_terminal, '--keep-open', '-C', cmdline])
    elif gnome_terminal != '':
        dir = os.path.expandvars('$HOME/.local/bin')
        with tempfile.TemporaryFile(prefix='viscmd', dir=dir) as f:
            f.write(cmdline)
            path = os.path.join(dir, f.name)
            subprocess.call([deepin_terminal, '--', 'bash', '--init-file', path])
