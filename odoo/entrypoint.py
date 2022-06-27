#!/usr/bin/python
import glob
import os
import subprocess as sp
import sys
from collections import OrderedDict


def compute_addons_path():
    src = os.environ["SRC"]
    addons_path = [os.path.join(src, "custom")]
    for org in ["studio73", "oca"]:
        org_path = os.path.join(src, org)
        if os.path.exists(org_path):
            repos = []
            for addon in glob.glob(
                "{}/**/__manifest__.py".format(org_path), recursive=True
            ):
                if "setup/" in addon:
                    continue
                repos.append(os.path.dirname(os.path.dirname(addon)))
            addons_path += sorted(list(set(repos)))
    addons_path.append(os.path.join(src, "odoo", "design-themes"))
    addons_path.append(os.path.join(src, "odoo", "odoo", "addons"))
    return ",".join(addons_path)


def build_conf():
    db_name = os.environ.get("PGDATABASE", os.environ.get("DATABASE", "odoo"))
    options = {
        "data_dir": os.environ.get("DATA"),
        "db_host": os.environ.get("PGHOST", "postgres"),
        "db_port": os.environ.get("PGPORT", 5432),
        "db_user": os.environ.get("PGUSER", "odoo"),
        "db_password": os.environ.get("PGPASSWORD", "changeme"),
        "db_name": db_name,
        "dbfilter": db_name,
        "list_db": False,
        "admin_passwd": "changeme",
        "load_language": "es_ES",
        "addons_path": compute_addons_path(),
    }
    if not os.environ.get("DEMO"):
        options["without_demo"] = True
    new_conf = OrderedDict({"options": options})
    cfg_prefix = "ODOO_"
    blacklist = ["release", "version"]
    for k, val in os.environ.items():
        if k.startswith(cfg_prefix):
            opt = k.replace(cfg_prefix, "").lower()
            if opt not in blacklist and "queue_job" not in opt:
                new_conf["options"][opt] = val
    with open("/opt/odoo/.odoorc", "w") as odoo_conf:
        for section, values in new_conf.items():
            odoo_conf.write("[%s]\n" % section)
            odoo_conf.writelines(["%s=%s\n" % (k, v) for k, v in values.items()])


def main():
    """
    Entrypoint main function
    """
    build_conf()
    exit(sp.call(sys.argv[1:]))

if __name__ == "__main__":
    main()
