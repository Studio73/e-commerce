#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import logging
import os
import sys
import subprocess as sp

import psycopg2

from ._requirements import main as requirements
from ._utils import DEVNULL, run, build_ssh_conf, echo
from .addons import get_addons_path
from .addons import main as clone_repos

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser


def symlink():
    odoo_bin = os.path.join(os.environ["SRC"], "odoo", "odoo-bin")
    run(["ln", "-s", odoo_bin, "/usr/local/bin/odoo"])


def set_ssh_environ():
    """
    Create /opt/odoo/data/.ssh if doesn't exists
    Then `ln -s /opt/odoo/data/.ssh -> ~/.ssh`
    """
    ssh_path = os.path.join(os.environ["DATA"], ".ssh")
    ssh_symlink_path = os.path.join("/opt", "odoo", ".ssh")
    if not os.path.exists(ssh_path):
        run(["mkdir", ssh_path], "odoo")
    if not os.path.exists(ssh_symlink_path):
        run(["ln", "-s", ssh_path, ssh_symlink_path], "odoo")
    if not os.path.exists("/opt/odoo/.gitconfig"):
        run(["git", "config", "--global", "user.name", "dodoo"], "odoo")
        run(["git", "config", "--global", "user.email", "dodoo@studio73.es"], "odoo")
    result = run(["ssh-keygen", "-H", "-F", "github.com"], "odoo", check_call=False)
    if not len(result.out.strip()):
        sp.check_call(
            "ssh-keyscan github.com >> %s"
            % os.path.join(ssh_symlink_path, "known_hosts"),
            shell=True,
            stderr=DEVNULL,
        )
    build_ssh_conf()


def install_cron():
    cron_file = os.path.join(os.environ["SETUP"], "cron")
    if os.path.exists(cron_file):
        sp.call("printenv > /etc/environment", shell=True)
        if os.path.exists("/etc/cron.d/cron"):
            os.remove("/etc/cron.d/cron")
        sp.call(["cp", cron_file, "/etc/cron.d/cron"])
        sp.call(["service", "cron", "start"])


def block_outbound_mail():
    block = any([os.environ.get("DEV"), os.environ.get("BLOCK_SMTP")])
    if not block:
        return True
    for smtp_port in ["25", "465", "587"]:
        p = run(
            [
                "iptables",
                "-C",
                "OUTPUT",
                "-p",
                "tcp",
                "--dport",
                smtp_port,
                "-j",
                "DROP",
            ],
            check_call=False,
        )
        if p.returncode != 0:
            if "you must be root" in p.error:
                raise Exception(
                    "The container must have at least NET_ADMIN capabilities\n"
                    "e.g. docker run --cap-add=NET_ADMIN ..."
                )
            sp.check_call(
                [
                    "iptables",
                    "-A",
                    "OUTPUT",
                    "-p",
                    "tcp",
                    "--dport",
                    smtp_port,
                    "-j",
                    "DROP",
                ]
            )
    db_name = os.environ.get("DATABASE", "odoo")
    query = "DELETE from ir_mail_server"
    sp.call(["psql", "-d", db_name, "-c", query], stdout=DEVNULL, stderr=DEVNULL)
    return True


def build_conf():
    db_name = os.environ.get("DATABASE", "odoo")
    options = {
        "data_dir": os.path.join(os.environ.get("DATA"), "data"),
        "db_host": os.environ.get("PGHOST", "postgres"),
        "db_port": os.environ.get("PGPORT", 5432),
        "db_user": os.environ.get("PGUSER", "odoo"),
        "db_password": os.environ.get("PGPASSWORD", "changeme"),
        "db_name": db_name,
        "dbfilter": db_name,
        "admin_passwd": os.environ.get("ADMINPASSWORD", "changeme"),
    }
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=options["db_user"],
            password=options["db_password"],
            host=options["db_host"],
        )
        conn.close()
    except psycopg2.DatabaseError:
        # Only if the database doesn't exists
        if os.environ.get("LANG"):
            options["load_language"] = os.environ["LANG"]
        if not os.environ.get("DEMO"):
            options["without_demo"] = True

    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.environ["SETUP"], "odoo.conf"))
    try:
        # Override default options with setup/odoo.conf values
        setup_options = dict(cfg.items("options"))
        options.update(setup_options)
    except configparser.NoSectionError:
        pass
    if not options.get("addons_path"):
        options["addons_path"] = get_addons_path()

    odoorc = "/opt/odoo/.odoorc"
    if os.environ["ODOO_VERSION"] == "8.0":
        odoorc = "/opt/odoo/.openerp_serverrc"

    with open(odoorc, "w") as odoo_conf:
        odoo_conf.write("[options]\n")
        odoo_conf.writelines(["%s=%s\n" % (k, v) for k, v in options.items()])
    odoo_conf.close()


def main():
    with echo("🤖 Setting up the container"):
        install_cron()
        set_ssh_environ()
        block_outbound_mail()
        requirements()
    clone_repos()
    build_conf()
    symlink()


if __name__ == "__main__":
    main()
