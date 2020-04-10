#!/usr/bin/python
import os
import subprocess as sp
import sys

import dodoo_tools


def main():
    """
    Entrypoint main function
    """
    # Hack to fix wrong uid/gid inside container
    host_uid = os.environ.get("HOST_UID", os.getuid())
    host_gid = os.environ.get("HOST_GID", os.getgid())
    if host_uid != os.getuid():
        dodoo_tools._utils.run(["usermod", "-u", str(host_uid), "odoo"])
    if host_gid != os.getgid():
        dodoo_tools._utils.run(["groupmod", "-g", str(host_uid), "odoo"])
    if "dodoo-tools" in sys.argv:
        # Allow run one-liner commands without instalation
        # Like -> docker run --rm ... dodoo-tools database restore
        return sp.call(sys.argv[1:])
    dodoo_tools.install.main()
    cmd = ["gosu", "odoo:odoo"] + sys.argv[1:]
    if os.environ.get("ODOO_VERSION") == "8.0":
        cmd = [c.replace("odoo-bin", "odoo.py") for c in cmd]
    return sp.call(cmd)


if __name__ == "__main__":
    main()
