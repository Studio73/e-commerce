#!/usr/bin/python
import os.path
import subprocess
import sys


if __name__ == '__main__':
    # Hack to fix wrong uid/gid inside container
    if os.environ.get('HOST_UID', False):
        subprocess.call(
            ['usermod', '-u', '%s' % os.environ.get('HOST_UID'), 'odoo']
        )
    if os.environ.get('HOST_GID', False):
        subprocess.call(
            ['usermod', '-g', '%s' % os.environ.get('HOST_GID'), 'odoo']
        )

    if not os.environ.get('NO_UPDATE', False):
        args = ['gosu', 'odoo:odoo', 'oman']
        if os.environ.get('FORDE_UPDATE', False):
            args.append('--update')
        else:
            args.append('--init')
        subprocess.call(args)

    args = ['gosu', 'odoo:odoo'] + sys.argv[1:]
    subprocess.call(args)
