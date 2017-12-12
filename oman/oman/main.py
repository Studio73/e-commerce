# -*- coding: utf-8 -*-
# (c) 2017 Pablo Fuentes <pablo@studio73.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import argparse
import glob
import subprocess
import os.path

from os.path import expandvars

import kaptan

from .utils import \
    backup, \
    build_conf, \
    copy_ssh_key, \
    init_git_conf


SRC = os.environ['SRC']
DATA = os.environ['DATA']
SETUP = os.environ['SETUP']


def clone_odoo(force=False):
    odoo_path = os.path.join(SRC, 'odoo')
    if force or not os.path.exists(
        os.path.join(odoo_path, 'odoo-bin')
    ):
        odoo_yaml = os.path.join(SETUP, 'odoo.yaml')
        if not os.path.exists(odoo_yaml):
            print('[!] No odoo.yaml provided')
        else:
            output = subprocess.check_call(
                ['gitaggregate', '-c', odoo_yaml, '--expand-env']
            )
            if output == 0:
                print("[+] Odoo succesfully cloned")  # TODO use logger
            else:
                raise Exception
    else:
        print("[+] Skipping, Odoo already cloned...")


def clone_addons(force=False):
    odoo_path = os.path.join(SRC, 'odoo')
    repos_list = glob.glob(
        os.path.join(SETUP, 'repos*.yaml')
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


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start',
        action='store_true',
        help="Clone for first time Odoo & OCA & Others"
    )
    parser.add_argument(
        '--update',
        choices=('odoo', 'addons', 'all'),
        help='Update Odoo or OCA & Others repositories or all'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Backup database'
    )
    args = parser.parse_args()
    if not any([getattr(args, arg) for arg in vars(args)]):
        parser.error('No arguments provided.')
    if args.start:
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
    elif args.backup:
        backup()


if __name__ == '__main__':
    main()
