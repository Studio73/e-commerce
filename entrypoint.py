#!/usr/bin/python
import os.path
import subprocess as sp
import sys


if __name__ == '__main__':
    # Hack to fix wrong uid/gid inside container
    uid = sp.Popen(['id', '-u'], stdout=sp.PIPE).stdout.read()
    host_uid = os.environ.get('HOST_UID', False)
    gid = sp.Popen(['id', '-g'], stdout=sp.PIPE).stdout.read()
    host_gid = os.environ.get('HOST_GID', False)
    if host_uid and host_uid != uid:
        sp.call(
            ['usermod', '-u', '%s' % host_uid, 'odoo']
        )
    if host_gid and host_gid != gid:
        sp.call(
            ['groupmod', '-g', '%s' % host_gid, 'odoo']
        )

    if not os.environ.get('NO_UPDATE', False):
        args = ['gosu', 'odoo:odoo', 'oman']
        if os.environ.get('FORDE_UPDATE', False):
            args.append('--update')
        else:
            args.append('--init')
        sp.call(args)

    args = ['gosu', 'odoo:odoo'] + sys.argv[1:]
    sp.call(args)
