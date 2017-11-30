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
    if os.path.exists(os.path.join(os.environ['SETUP'], 'cron')):
        sp.call(
            'printenv > /etc/environment', shell=True
        )
        if os.path.exists('/etc/cron.d/cron'):
            os.remove('/etc/cron.d/cron')
        sp.call([
            'cp',
            os.path.join(os.environ['SETUP'], 'cron'),
            '/etc/cron.d/cron'
        ])
        sp.call(['service', 'cron', 'start'])

    args = ['gosu', 'odoo:odoo', 'oman']
    if os.environ.get('UPDATE', False):
        args += ['--update', 'all']
    else:
        args.append('--init')
    sp.call(args)

    args = ['gosu', 'odoo:odoo'] + sys.argv[1:]
    sp.call(args)
