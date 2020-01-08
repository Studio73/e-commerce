#!/usr/bin/python
import os
import subprocess as sp
import sys

import dodoo_tools


def main():
    """
    Entrypoint main function
    """
    dodoo_tools.install.main()
    cmd = ["gosu", "odoo:odoo"] + sys.argv[1:]
    if os.environ.get("ODOO_VERSION") == "8.0":
        cmd = [c.replace("odoo-bin", "odoo.py") for c in cmd]
    return sp.call(cmd)


if __name__ == "__main__":
    main()
