#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import logging
import os
import sys
import subprocess as sp

import psycopg2

from collections import OrderedDict
from ._requirements import main as requirements
from ._utils import DEVNULL, run, build_ssh_conf, echo
from .addons import get_addons_path
from .addons import main as clone_repos

_logger = logging.getLogger(__name__)


if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser


def symlink():
    if os.environ["ODOO_VERSION"] in ["8.0", "9.0"]:
        odoo_bin = "openerp-server"
    else:
        odoo_bin = "odoo-bin"
    odoo_path = os.path.join(os.environ["SRC"], "odoo", odoo_bin)
    run(["ln", "-s", odoo_path, "/usr/local/bin/odoo"])


def debugger_bin():
    debugger = os.environ.get("DEBUGGER", False)
    if not debugger:
        return
    if os.environ.get("DEBUG"):
        _logger.warning(
            "Deprecated env variable DEBUG, use instead DEBUGGER=<debugpy|pydevd>"
        )
        debugger = os.environ.get("DEBUG", False)
    pyversion = "python{}".format(sys.version_info.major)
    if debugger == "ptvsd":
        debugger = "debugpy"
        _logger.warning("ptvsd is deprecated, see https://github.com/microsoft/ptvsd/")
    if debugger == "debugpy":
        debugger_host = os.environ.get("DEBUGGER_HOST", "0.0.0.0")
        debugger_port = os.environ.get("DEBUGGER_PORT", "5678")
        debug_cmd = "{} -m debugpy --listen {}:{} /usr/local/bin/odoo $@\n".format(
            pyversion, debugger_host, debugger_port
        )
    elif debugger == "pydevd":
        if os.environ["ODOO_VERSION"] in ["8.0", "9.0"]:
            odoo_lib = "openerp"
        else:
            odoo_lib = "odoo"
        debugger_host = os.environ.get("DEBUGGER_HOST", "localhost")
        debugger_port = os.environ.get("DEBUGGER_PORT", "12345")
        debug_cmd = """#!/usr/bin/env {}
__import__('os').environ['TZ'] = 'UTC'
import {}
import pydevd_pycharm
if __name__ == "__main__":
    pydevd_pycharm.settrace('{}', port={}, stdoutToServer=True, stderrToServer=True)
    {}.cli.main()
""".format(
            pyversion, odoo_lib, debugger_host, debugger_port, odoo_lib
        )
    else:
        raise Exception(
            "Wrong DEBUGGER option ({}), please choose between (debugpy|pydevd)".format(
                debugger
            )
        )
    debug_odoo_bin = "/usr/local/bin/debug_odoo"
    with open(debug_odoo_bin, "w") as debug_file:
        debug_file.write(debug_cmd)
    run(["chmod", "+x", debug_odoo_bin])


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
        sp.call(["crontab", "-u", "odoo", cron_file])
        sp.call(["service", "cron", "start"], stdout=DEVNULL, stderr=DEVNULL)


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
    querys = [
        "DELETE from ir_mail_server",
        "DELETE from ir_cron where cron_name = 'Publisher: Update Notification'",
    ]
    for query in querys:
        sp.call(["psql", "-d", db_name, "-c", query], stdout=DEVNULL, stderr=DEVNULL)
    with open("/etc/hosts", "a") as f:
        f.write("127.0.0.1 services.openerp.com services.odoo.com\n")
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
        "list_db": False,
        "admin_passwd": os.environ.get("ADMINPASSWORD", "changeme"),
    }
    if os.environ.get("LANG"):
        options["load_language"] = os.environ["LANG"]
    if not os.environ.get("DEMO"):
        options["without_demo"] = True
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.environ["SETUP"], "odoo.conf"))
    new_conf = OrderedDict({"options": options})
    for section in list(cfg._sections.keys()):
        new_conf.setdefault(section, {})
        new_conf[section].update(dict(cfg.items(section)))
    if not new_conf["options"].get("addons_path"):
        new_conf["options"]["addons_path"] = get_addons_path()

    odoorc = "/opt/odoo/.odoorc"
    if os.environ["ODOO_VERSION"] in ["8.0", "9.0"]:
        odoorc = "/opt/odoo/.openerp_serverrc"

    with open(odoorc, "w") as odoo_conf:
        for section, values in new_conf.items():
            odoo_conf.write("[%s]\n" % section)
            odoo_conf.writelines(["%s=%s\n" % (k, v) for k, v in values.items()])
    run(["chown", "-R", "odoo:odoo", odoorc])


def install_runbot_build():
    if os.environ.get("RUNBOT_BUILD") and os.path.exists("/data/build"):
        run(["touch", "/data/build/start-%s" % os.environ["RUNBOT_BUILD"]], "odoo")
        org = os.environ["GIT_REPO"].strip("/").split("/")[-2].lower().split(":")[-1]
        reponame = os.environ["GIT_REPO"].split("/")[-1].replace(".git", "")
        run(
            ["mkdir", "-p", os.path.join(os.environ["SRC"], org)],
            "odoo",
            check_call=True,
        )
        data_dir = os.path.join(os.environ["DATA"], "data")
        src_dir = os.path.join(os.environ["SRC"], org, reponame)
        odoo_dir = os.path.join(os.environ["SRC"], "odoo")
        run(["ln", "-s", "/data/build/datadir", data_dir], "odoo", check_call=True)
        run(["ln", "-s", "/data/build/%s" % reponame, src_dir], "odoo", check_call=True)
        if os.path.exists("/data/build/odoo"):
            run(["ln", "-s", "/data/build/odoo", odoo_dir], "odoo", check_call=True)
        if os.path.exists("/data/build/odoo.conf"):
            run(
                ["cp", "/data/build/odoo.conf", os.environ["SETUP"]],
                "odoo",
                check_call=True,
            )
        ssh_dir = "/opt/odoo/.ssh"
        if os.path.exists("/data/build/.ssh") and not os.path.exists(ssh_dir):
            run(["ln", "-s", "/data/build/.ssh", ssh_dir], "odoo", check_call=True)


def migrate_pip_cache():
    # To remove in next release
    pip_target = os.environ["PIP_TARGET"]
    legacy_pip_target = os.path.join(os.environ["DATA"], ".pypi")
    if not os.path.exists(pip_target) and os.path.exists(legacy_pip_target):
        run(["mv", legacy_pip_target, pip_target])
    return True


def main():
    with echo("Configuring the container"):
        install_runbot_build()
        migrate_pip_cache()
        install_cron()
        set_ssh_environ()
        block_outbound_mail()
        requirements()
    clone_repos()
    build_conf()
    symlink()
    debugger_bin()


if __name__ == "__main__":
    main()
