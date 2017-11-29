#!/usr/bin/python
import os.path
import subprocess
import sys


if __name__ == '__main__':
    # Hack to fix wrong uid/gid inside container
    uid = subprocess.Popen(['id', '-u'], stdout=subprocess.PIPE).stdout.read()
    host_uid = os.environ.get('HOST_UID', False)
    gid = subprocess.Popen(['id', '-g'], stdout=subprocess.PIPE).stdout.read()
    host_gid = os.environ.get('HOST_GID', False)
    if host_uid and host_uid != uid:
        subprocess.call(
            ['usermod', '-u', '%s' % host_uid, 'odoo']
        )
    if host_gid and host_gid != gid:
        subprocess.call(
            ['groupmod', '-g', '%s' % host_gid, 'odoo']
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
