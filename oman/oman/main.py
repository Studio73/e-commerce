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
    init_git_conf, \
    gen_ssh_key


SRC = os.environ.get('SRC', "")
DATA = os.environ.get('DATA', "")
SETUP = os.environ.get('SETUP', "")


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


def clone_addons(force=False, dirmatch=None):
    if dirmatch:
        dirmatch = dirmatch[0]
    odoo_path = os.path.join(SRC, 'odoo')
    repos_list = glob.glob(
        os.path.join(SETUP, 'repos*.yaml')
    )
    repos_list.sort()
    conf_handler = kaptan.Kaptan(handler="yaml")
    addons = []

    for repo_yaml in repos_list:
        conf = conf_handler.import_config(repo_yaml).export('dict')
        for repo, repo_data in sorted(conf.items(), key=lambda x: x[1].get("order", 9999)):
            repo_exp = expandvars(repo)
            addons.append(repo_exp)
            if repo_data.get("private", False):
                gen_ssh_key(repo.split("/")[-1])
            update = False
            if dirmatch:
                if dirmatch in repo_exp or not os.path.exists(repo_exp):
                    update = True
            elif force or not os.path.exists(repo_exp):
                update = True

            if update:
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
        '--dev',
        action='store_true',
        help="Clone OCA & Others repos if not exists"
    )
    parser.add_argument(
        '--dirmatch',
        '-d',
        metavar='container',
        nargs=1,
        help='Update only the directories'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Backup database'
    )
    parser.add_argument(
        '--ssh-key',
        metavar='repo',
        nargs=1,
        help="Generate ssh for private repository"
    )
    args = parser.parse_args()
    if not any([getattr(args, arg) for arg in vars(args)]):
        parser.error('No arguments provided.')
    if args.start:
        init_git_conf()
        clone_odoo(False)
        addons = clone_addons(False)
        build_conf(addons)
    elif args.update:
        init_git_conf()
        if args.update in ['odoo', 'all']:
            clone_odoo(True)
        if args.update in ['addons', 'all']:
            addons = clone_addons(True, args.dirmatch)
            build_conf(addons)
    elif args.dev:
        build_conf()
    elif args.backup:
        backup()
    elif args.ssh_key:
        gen_ssh_key(args.ssh_key[0])


if __name__ == '__main__':
    main()
