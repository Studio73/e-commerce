#!/usr/bin/python
import os.path
import subprocess
import sys


if __name__ == '__main__':
    args = ['oman']
    if os.path.expandvars('$FORDE_UPDATE') == '$FORDE_UPDATE':
        args.append('--init')
    else:
        args.append('--update')
    subprocess.call(args)
    subprocess.call(sys.argv[1:])
