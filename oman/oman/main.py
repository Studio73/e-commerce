# -*- coding: utf-8 -*-
import argparse
import glob
import kaptan
import os.path
import psycopg2
import subprocess

from os.path import expandvars
SRC_PATH = os.environ['SRC_PATH']
DATA_PATH = os.environ['DATA_PATH']
SETUP_PATH = os.environ['SETUP_PATH']


def clone_odoo(force=False):
    odoo_path = os.path.join(SRC_PATH, 'odoo')
    if force or not os.path.exists(
        os.path.join(odoo_path, 'odoo-bin')
    ):
        odoo_yaml = os.path.join(SETUP_PATH, 'odoo.yaml')
        if not os.path.exists(odoo_yaml):
            print('[!] No odoo.yaml provided')
        else:
            output = subprocess.check_call(
                ['gitaggregate', '-c', odoo_yaml, '--expand-env']
            )
            if output == 0:
                print("[+] Odoo succesfully cloned")
            else:
                raise Exception
    else:
        print("[+] Skipping, Odoo already cloned...")


def clone_addons(force=False):
    odoo_path = os.path.join(SRC_PATH, 'odoo')
    repos_list = glob.glob(
        os.path.join(SETUP_PATH, 'repos*.yaml')
    )
    repos_list.sort()
    conf = kaptan.Kaptan(handler="yaml")
    addons = []

    for repo_yaml in repos_list:
        if force:
            output = subprocess.check_call(
                ['gitaggregate', '-c', repo_yaml, '--expand-env']
            )
            if output != 0:
                raise Exception
        else:
            for repo in conf.import_config(repo_yaml).export('dict').keys():
                repo_exp = expandvars(repo)
                addons.append(repo_exp)
                if not os.path.exists(repo_exp):
                    output = subprocess.check_call(
                        ['gitaggregate', '-c', repo_yaml,
                         '-d', repo_exp, '--expand-env']
                    )
                    if output != 0:
                        raise Exception
                else:
                    print("[+] Skipping, %s already cloned..." % repo_exp)
    addons.append(os.path.join(odoo_path, 'addons'))
    return addons


def init_git_conf():
    cfg = open(os.path.expanduser('~/.gitconfig'), 'w+')
    cfg.writelines([
        '[user]\n',
        '\temail = container-saas@studio73.es\n',
        '\tname = Container SaaS Studio73\n',
    ])


def copy_ssh_key():
    ssh_path = os.path.join(SETUP_PATH, '.ssh/')
    if os.path.exists(ssh_path):
        subprocess.check_call(['cp', '-r', ssh_path, '/opt/odoo/'])
        subprocess.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa'])
        subprocess.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa.pub'])


def build_conf(addons=None):
    if addons is None:
        addons = []

    conf = open(os.path.join(SRC_PATH, 'odoo.conf'), 'w+')
    db_options = {
        'host': expandvars('$DB_HOST'),
        'port': expandvars('$DB_PORT'),
        'user': expandvars('$DB_USER'),
        'pswd': expandvars('$DB_PSWD'),
        'name': expandvars('$DB_NAME'),
    }
    options = [
        '[options]\n'
        'data_dir=%s\n' % os.path.join(DATA_PATH, 'data'),
        'db_host=%s\n' % db_options['host'],
        'db_port=%s\n' % db_options['port'],
        'db_user=%s\n' % db_options['user'],
        'db_password=%s\n' % db_options['pswd'],
        'db_name=%s\n' % db_options['name'],
        'dbfilter=%s\n' % db_options['name'],
        'admin_passwd=%s\n' % expandvars('$ADMIN_PSWD'),
        'addons_path=%s\n' % ','.join(addons)
    ]
    # If running for first time and database doesn't exists,
    # force the language to be used on database creation
    try:
        psycopg2.connect(
            "dbname='%s' host='%s' port='%s' user='%s' password='%s'" % (
                db_options['name'], db_options['host'], db_options['port'],
                db_options['user'], db_options['pswd']
            )
        )
    except psycopg2.OperationalError:
        if os.environ.get('LANG', False):
            options.append('load_language=%s\n' % os.environ['LANG'])
        if not os.environ.get('DEMO', False):
            options.append('without_demo=True\n')

    conf.writelines(options)
    if os.path.exists(os.path.join(SETUP_PATH, 'odoo.conf')):
        setup_conf = open(
            os.path.join(SETUP_PATH, 'odoo.conf')
        )
        conf.writelines([l for l in setup_conf.readlines()])
        setup_conf.close()
    conf.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--init',
        action='store_true',
        help="Clones for first time Odoo & OCA & Others"
    )
    parser.add_argument(
        '--update',
        choices=('odoo', 'addons', 'all'),
        help='Update Odoo or OCA & Others repositories or both'
    )
    args = parser.parse_args()
    if not any([getattr(args, arg) for arg in vars(args)]):
        parser.error('No arguments provided.')
    if args.init:
        init_git_conf()
        copy_ssh_key()
        clone_odoo(False)
        addons = clone_addons(False)
        build_conf(addons)
    elif args.update:
        if args.update in ['odoo', 'all']:
            clone_odoo(True)
        if args.update in ['addons', 'all']:
            addons = clone_addons(True)
            build_conf(addons)


if __name__ == '__main__':
    main()
