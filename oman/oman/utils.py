# -*- coding: utf-8 -*-
# (c) 2017 Pablo Fuentes <pablo@studio73.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import os
import psycopg2
import subprocess as sp

from datetime import datetime

SRC = os.environ['SRC']
DATA = os.environ['DATA']
SETUP = os.environ['SETUP']
DBNAME = os.environ['DATABASE']


def backup():
    tday = datetime.now().strftime("%A").upper()
    backup_folder = os.path.join(DATA, 'backup')
    sp.check_call(
        'pg_dump %s | gzip > %s_%s.tar.gz' % (
            DBNAME,
            os.path.join(backup_folder, DBNAME),
            tday
        ), shell=True
    )
    # https://orville.thebennettproject.com/articles/tar-removing-leading-slash/
    sp.check_call([
        'tar', '-C', DATA, '-cf',
        os.path.join(backup_folder, '%s-fstore-%s.tar.gz' % (DBNAME, tday)),
        'data'
    ])
    return True


def build_conf(addons=None):
    if addons is None:
        addons = []
    conf = open(os.path.join(SRC, 'odoo.conf'), 'w+')
    db_options = {
        'host': os.environ['PGHOST'],
        'port': os.environ['PGPORT'],
        'user': os.environ['PGUSER'],
        'pswd': os.environ['PGPASSWORD'],
        'name': DBNAME,
    }
    options = [
        '[options]\n'
        'data_dir=%s\n' % os.path.join(DATA, 'data'),
        'db_host=%s\n' % db_options['host'],
        'db_port=%s\n' % db_options['port'],
        'db_user=%s\n' % db_options['user'],
        'db_password=%s\n' % db_options['pswd'],
        'db_name=%s\n' % db_options['name'],
        'dbfilter=%s\n' % db_options['name'],
        'admin_passwd=%s\n' % os.environ['ADMINPASSWORD'],
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
    if os.path.exists(os.path.join(SETUP, 'odoo.conf')):
        setup_conf = open(
            os.path.join(SETUP, 'odoo.conf')
        )
        conf.writelines([l for l in setup_conf.readlines()])
        setup_conf.close()
    conf.close()


def copy_ssh_key():
    ssh_path = os.path.join(SETUP, '.ssh/')
    if os.path.exists(ssh_path):
        sp.check_call(['cp', '-r', ssh_path, '/opt/odoo/'])
        sp.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa'])
        sp.check_call(['chmod', '600', '/opt/odoo/.ssh/id_rsa.pub'])


def init_git_conf():
    cfg = open(os.path.expanduser('~/.gitconfig'), 'w+')
    cfg.writelines([
        '[user]\n',
        '\temail = container-saas@studio73.es\n',
        '\tname = Container SaaS Studio73\n',
    ])
