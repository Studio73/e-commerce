# -*- coding: utf-8 -*-
# (c) 2017 Pablo Fuentes <pablo@studio73.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import os
import glob
import psycopg2
import subprocess as sp

from datetime import datetime

SRC = os.environ.get('SRC', "")
DATA = os.environ.get('DATA', "")
SETUP = os.environ.get('SETUP', "")
DBNAME = os.environ.get('DATABASE', "")


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


def init_git_conf():
    cfg = open(os.path.expanduser('~/.gitconfig'), 'w+')
    cfg.writelines([
        '[user]\n',
        '\temail = container-saas@studio73.es\n',
        '\tname = Container SaaS Studio73\n',
    ])

def check_ssh():
    ssh_path = os.path.join(os.environ['DATA'], '.ssh')
    if not os.path.exists(ssh_path):
        os.makedirs(ssh_path)
    known_hosts = os.path.join(ssh_path, 'known_hosts')
    if not os.path.exists(known_hosts):
        sp.check_call(['touch', known_hosts])
    ssh_symbolic_path = os.path.join(os.environ['HOME'], '.ssh')
    if not os.path.exists(ssh_symbolic_path):
        sp.check_call(['ln', '-s', ssh_path, ssh_symbolic_path])

def gen_ssh_key(name):  
    check_ssh()
    known_hosts = sp.Popen(
        ['ssh-keygen', '-H', '-F' 'github.com'], stdout=sp.PIPE
    ).communicate()[0]
    if not len(known_hosts):
        sp.check_call(
            'ssh-keyscan github.com >> ~/.ssh/known_hosts', shell=True
        )
    ssh_file = os.path.join(
        os.path.join(DATA, '.ssh'), name
    )
    if not os.path.exists(ssh_file):
        comment = "%s@%s" % (name, DBNAME)
        sp.check_call(
            ['ssh-keygen', '-N', '', '-f', ssh_file, '-C', comment]
        )
        build_ssh_conf()

def build_ssh_conf():
    ssh_folder = os.path.join(DATA, '.ssh')
    cfg = open(os.path.join(ssh_folder, 'config'), 'w+')
    identityfiles = glob.glob(os.path.join(ssh_folder, '*.pub'))
    for identityfile in identityfiles:
        identityfile = identityfile.split('.pub')[0]
        cfg.writelines([
            'Host %s github.com\n' % identityfile.split('/')[-1],
            '\tHostName github.com\n',
            '\tIdentityFile %s\n' % identityfile,
        ])