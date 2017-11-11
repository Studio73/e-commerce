# -*- coding: utf-8 -*-
import argparse
import glob
import kaptan
import os.path
import psycopg2
import subprocess

from os.path import expandvars


def clone_odoo(force_update=False):
    odoo_path = expandvars('$SRC_PATH/odoo')
    if force_update or not os.path.exists(
        os.path.join(odoo_path, 'odoo-bin')
    ):
        odoo_yaml = expandvars('$SETUP_PATH/odoo.yaml')
        if not os.path.exists(odoo_yaml):
            print '[!] No odoo.yaml provided'
        else:
            output = subprocess.check_call(
                ['gitaggregate', '-c', odoo_yaml, '--expand-env']
            )
            if output == 0:
                print "[+] Odoo succesfully cloned"
            else:
                raise Exception
    else:
        print "[+] Skipped, Odoo already cloned..."


def clone_addons(force_update=False):
    odoo_path = expandvars('$SRC_PATH/odoo')
    repos_setup = glob.glob(
        os.path.join(expandvars('$SETUP_PATH'), 'repos*.yaml')
    )
    repos_setup.sort()
    conf = kaptan.Kaptan(handler="yaml")
    addons = []

    for repo_yaml in repos_setup:
        if force_update:
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
                    print "[+] Skipped, %s already cloned..." % repo_exp
    addons.append(os.path.join(odoo_path, 'addons'))
    return addons


def copy_ssh_key():
    ssh_path = os.path.join(expandvars('$SETUP_PATH'), '.ssh/')
    if os.path.exists(ssh_path):
        subprocess.check_call(['cp', '-r', ssh_path, '/opt/odoo/'])
        subprocess.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa'])
        subprocess.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa.pub'])


def build_conf(addons=[]):
    conf = open(os.path.join(expandvars('$SRC_PATH'), 'odoo.conf'), 'w+')
    db_options = {
        'host': expandvars('$DB_HOST'),
        'port': expandvars('$DB_PORT'),
        'user': expandvars('$DB_USER'),
        'pswd': expandvars('$DB_PSWD'),
        'name': expandvars('$DB_NAME'),
    }
    options = [
        '[options]\n'
        'data_dir=%s\n' % os.path.join(expandvars('$DATA_PATH'), 'data'),
        'db_host=%s\n' % db_options['host'],
        'db_port=%s\n' % db_options['port'],
        'db_user=%s\n' % db_options['user'],
        'db_password=%s\n' % db_options['pswd'],
        'db_name=%s\n' % db_options['name'],
        'dbfilter=%s\n' % db_options['name'],
        'admin_passwd=%s\n' % expandvars('$ADMIN_PSWD'),
        'addons_path=%s\n' % ','.join(addons)
    ]

    # If running for first time and database doesn't
    # force the language to be used when database creation
    try:
        psycopg2.connect(
            "dbname='%s' host='%s' port='%s' user='%s' password='%s'" % (
                db_options['name'], db_options['host'], db_options['port'],
                db_options['user'], db_options['pswd']
            )
        )
    except psycopg2.OperationalError:
        if expandvars('$LANG') != '$LANG':
            options.append('load_language=%s\n' % expandvars('$LANG'))
    conf.writelines(options)
    if os.path.exists(os.path.join(expandvars('$SETUP_PATH'), 'odoo.conf')):
        setup_conf = open(
            os.path.join(expandvars('$SETUP_PATH'), 'odoo.conf')
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
        action='store_true',
        help='Update Odoo & OCA & Others repositories'
    )
    parser.add_argument(
        '--update-odoo',
        action='store_true',
        help='Update Odoo repository'
    )
    parser.add_argument(
        '--update-addons',
        action='store_true',
        help='Update OCA & Others repositories'
    )
    args = parser.parse_args()
    if not any([getattr(args, arg) for arg in vars(args)]):
        parser.error('No arguments provided.')

    if args.init or args.update:
        force = False if args.init else True
        copy_ssh_key()
        clone_odoo(force)
        addons = clone_addons(force)
        build_conf(addons)
    else:
        if args.update_odoo:
            clone_odoo(True)
        if args.update_addons:
            addons = clone_addons(True)
            build_conf(addons)


if __name__ == '__main__':
    main()
