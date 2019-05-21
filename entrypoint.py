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
    if os.environ.get("DEBUG") and "python" in sys.argv[1]:
        cmd = [
            "gosu",
            "odoo:odoo",
            sys.argv[1],
            "-m",
            "ptvsd",
            "--host",
            "0.0.0.0",
            "--port",
            "5678",
        ]
        cmd += sys.argv[2:]
    else:
        cmd = ["gosu", "odoo:odoo"] + sys.argv[1:]

    if os.environ.get("ODOO_VERSION") == "8.0":
        cmd = [c.replace("odoo-bin", "odoo.py") for c in cmd]
    return sp.call(cmd)


if __name__ == "__main__":
    main()
