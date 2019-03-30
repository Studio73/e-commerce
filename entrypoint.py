#!/usr/bin/python
import logging
import os
import subprocess as sp
import sys


try:
    from subprocess import DEVNULL # py3
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def main():
    """
    Entrypoint main function
    """
    # Hack to fix wrong uid/gid inside container
    host_uid = os.environ.get('HOST_UID', False)
    host_gid = os.environ.get('HOST_GID', False)
    if host_uid and host_uid != os.getuid():
        sp.call(['usermod', '-u', '%s' % host_uid, 'odoo'], 
            stdout=DEVNULL, stderr=DEVNULL)
    if host_gid and host_gid != os.getgid():
        sp.call(['groupmod', '-g', '%s' % host_gid, 'odoo'], 
            stdout=DEVNULL, stderr=DEVNULL)

    # Cron jobs
    if os.path.exists(os.path.join(os.environ['SETUP'], 'cron')):
        sp.call('printenv > /etc/environment', shell=True)
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
            if package_name not in installed_pip_packages:
                sp.call(['pip', 'install', package])
    # TODO others requirements apt, npm, etc...
    args = ['gosu', 'odoo:odoo', 'oman']
    if os.environ.get('DEV', False):
        # Block SMTP ports
        for smtp_port in ['25', '465', '587']:
            try:
                sp.check_call(
                    ['iptables', '-C', 'OUTPUT', '-p', 'tcp',
                     '--dport', smtp_port, '-j', 'DROP'], 
                    stdout=DEVNULL, stderr=DEVNULL)
            except sp.CalledProcessError:
                sp.check_call(
                    ['iptables', '-A', 'OUTPUT', '-p', 'tcp', 
                     '--dport', smtp_port, '-j', 'DROP'])
        db_name = os.environ.get('DATABASE', 'odoo')
        query = "UPDATE ir_mail_server set active = 'f'"
        sp.call(
            ['psql', '-d', db_name, '-c', query], 
            stdout=DEVNULL, stderr=DEVNULL)
        args.append('--dev')
    elif os.environ.get('UPDATE', False):
        args += ['--update', 'all']
    else:
        args.append('--start')
    sp.call(args)
    if os.environ.get('DEBUG', False) and 'python' in sys.argv[1]:
        cmd = [
            'gosu', 'odoo:odoo', 
            sys.argv[1], '-m', 'ptvsd', '--host', '0.0.0.0', '--port', '5678']
        sp.call(cmd + sys.argv[2:])
    else:
        sp.call(['gosu', 'odoo:odoo'] + sys.argv[1:])

if __name__ == '__main__':
    main()
