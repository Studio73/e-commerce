#!/usr/bin/python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import os
import dodoo_tools


def set_env():
    if os.environ.get("GITHUB_ACTIONS"):
        os.environ["DEV"] = "true"
        os.environ["VERBOSE"] = "true"
        # Disable C compiler optimisations, speed up lxml install
        # DOCS: https://lxml.de/build.html
        os.environ["CFLAGS"] = "-O0"  
        for f in ["src", "data", "setup"]:
            old_val = os.environ[f.upper()]
            new_val =  os.path.join(os.environ["GITHUB_WORKSPACE"], f)
            os.environ[f.upper()] = new_val
            dodoo_tools._utils.run(["mkdir", "-p", new_val], "odoo")
            if old_val in os.environ["PATH"]:
                os.environ["PATH"] = os.environ["PATH"].replace(old_val, new_val)
            if old_val in os.environ["PYTHONPATH"]:
                os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"].replace(old_val, new_val)
            if old_val in os.environ["PYTHONUSERBASE"]:
                os.environ["PYTHONUSERBASE"] = os.environ["PYTHONUSERBASE"].replace(old_val, new_val)
        dodoo_tools._utils.run(["chown", "-R", "odoo:odoo", os.environ["HOME"]])
        dodoo_tools._utils.run(["chown", "-R", "odoo:odoo", os.environ["GITHUB_WORKSPACE"]])
    if not os.environ.get("GIT_REPO") and os.environ.get("GITHUB_REPOSITORY"):
        os.environ["GIT_REPO"] = "git@github.com:{}.git".format(os.environ["GITHUB_REPOSITORY"])
    if not os.environ.get("DATABASE"):
        os.environ["DATABASE"] = "odoo"
    return True


