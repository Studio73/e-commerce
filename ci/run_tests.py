#!/usr/bin/python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import os
import dodoo_tools
from set_env import set_env


def main():
    set_env()
    dodoo_tools._utils.run(["git", "config", "--global", "user.name", "dodoo"], "odoo")
    dodoo_tools._utils.run(["git", "config", "--global", "user.email", "dodoo@studio73.es"], "odoo")
    dodoo_tools.install.main()
    odoorc = ".odoorc"
    if os.environ["ODOO_VERSION"] in ["8.0", "9.0"]:
        odoorc = ".openerp_serverrc"
    ci_odoorc = os.path.expanduser("~/{}".format(odoorc))
    dodoo_tools._utils.run(["cp", os.path.join("/opt/odoo", odoorc), ci_odoorc])
    return dodoo_tools.tests.run()


if __name__ == "__main__":
    main()
