#!/usr/bin/python
import os.path
import subprocess as sp
import sys
import logging


def main():
    """
    Entrypoint main function
    """
    # Hack to fix wrong uid/gid inside container
    uid = sp.Popen(['id', '-u'], stdout=sp.PIPE).stdout.read()
    host_uid = os.environ.get('HOST_UID', False)
    gid = sp.Popen(['id', '-g'], stdout=sp.PIPE).stdout.read()
    host_gid = os.environ.get('HOST_GID', False)
    if host_uid and host_uid != uid:
        sp.call(['usermod', '-u', '%s' % host_uid, 'odoo'])
    if host_gid and host_gid != gid:
        sp.call(['groupmod', '-g', '%s' % host_gid, 'odoo'])

    # Cron jobs
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
    # Pip requirements
    pip_file = os.path.join(os.environ['SETUP'], 'pip.txt')
    if os.path.exists(pip_file):
        freeze = sp.Popen(['pip', 'freeze'], stdout=sp.PIPE).communicate()[0]
        installed_pip_packages = [
            p.split('==')[0] for p in freeze.decode().strip().split('\n')]
        packages = open(pip_file, 'r+').read().splitlines()
        for package in packages:
            package_name = package.split('==')[0]
            #Packages like git+https://github.com/ORG/REPO.git
            if package_name[-4:] == '.git': 
                package_name = package_name.split('/')[-1][:-4]
            print(package_name)
            if package_name not in installed_pip_packages:
                sp.call(['pip', 'install', package])
    # TODO others requirements apt, npm, etc...
    logging.info("asdfasdfasdf")
    args = ['gosu', 'odoo:odoo', 'oman']
    if os.environ.get('DEV', False):
        args.append('--dev')
    elif os.environ.get('UPDATE', False):
        args += ['--update', 'all']
    else:
        args.append('--start')
    sp.call(args)
    args = ['gosu', 'odoo:odoo'] + sys.argv[1:]
    sp.call(args)

if __name__ == '__main__':
    main()
