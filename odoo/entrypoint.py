#!/usr/bin/python
import glob
import os
import subprocess as sp
import sys
from collections import OrderedDict

MEMORY_SOFT = 640
MEMORY_HARD = 768


def compute_addons_path():
    src = os.environ["SRC"]
    addons_path = [os.path.join(src, "custom")]
    if os.environ.get("GITHUB_WORKSPACE"):
        addons_path.append(os.environ["GITHUB_WORKSPACE"])
    for org in ["studio73", "oca"]:
        org_path = os.path.join(src, org)
        if os.path.exists(org_path):
            repos = []
            _manifest = "{}/**/__manifest__.py".format(org_path)
            _openerp = "{}/**/__openerp__.py".format(org_path)
            globs = glob.glob(_manifest, recursive=True) + glob.glob(
                _openerp, recursive=True
            )
            for addon in globs:
                if "setup/" in addon:
                    continue
                repos.append(os.path.dirname(os.path.dirname(addon)))
            addons_path += sorted(list(set(repos)))
    addons_path.append(os.path.join(src, "odoo", "design-themes"))
    addons_path.append(os.path.join(src, "odoo", "odoo", "addons"))
    return ",".join(addons_path)


def build_conf():
    db_name = os.environ.get("PGDATABASE", os.environ.get("DATABASE", "odoo"))
    workers = int(os.environ.get("ODOO_WORKERS", 1)) or 1
    options = {
        "data_dir": os.environ.get("DATA"),
        "db_host": os.environ.get("PGHOST", "localhost"),
        "db_port": os.environ.get("PGPORT", 5432),
        "db_user": os.environ.get("PGUSER", "odoo"),
        "db_password": os.environ.get("PGPASSWORD", "changeme"),
        "db_name": db_name,
        "dbfilter": db_name,
        "list_db": False,
        "admin_passwd": "changeme",
        "addons_path": compute_addons_path(),
        "workers": workers,
        "limit_time_cpu": 480,
        "limit_time_real": 960,
        "limit_memory_soft": (workers * MEMORY_SOFT) * 1024 * 1024,
        "limit_memory_hard": (workers * MEMORY_HARD) * 1024 * 1024,
    }

    if os.environ.get("ODOO_SENTRY_DSN"):
        options.update(
            {
                "sentry_enabled": True,
                "sentry_event_logging_level": "error",
                "sentry_breadcrum_logging_level": "info",
                "sentry_traces_sample_rate": 0.2,
                "sentry_profiles_sample_rate": 0.2,
            }
        )

    openupgrade_version = float(os.environ.get("OPENUPGRADE_TARGET_VERSION", 0))
    if openupgrade_version >= 14.0:
        options["server_wide_modules"] = "base,web,openupgrade_framework"
    if not os.environ.get("DEMO"):
        options["without_demo"] = True
    new_conf = OrderedDict({"options": options})
    cfg_prefix = "ODOO_"
    blacklist = ["release", "version", "rc"]
    for k, val in os.environ.items():
        if k.startswith(cfg_prefix):
            opt = k.replace(cfg_prefix, "").lower()
            if opt not in blacklist and "queue_job" not in opt:
                new_conf["options"][opt] = val
    with open(os.environ["ODOO_RC"], "w") as odoo_conf:
        for section, values in new_conf.items():
            odoo_conf.write("[%s]\n" % section)
            odoo_conf.writelines(["{}={}\n".format(k, v) for k, v in values.items()])


def main():
    """
    Entrypoint main function
    """
    build_conf()
    sys.exit(sp.call(sys.argv[1:]))


if __name__ == "__main__":
    main()
