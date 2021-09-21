#!/usr/bin/python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import os
import dodoo_tools


def set_env():
    if os.environ.get("GITHUB_ACTIONS"):
        os.environ["DEV"] = "true"
        os.environ["VERBOSE"] = "true"
        for f in ["src", "data", "setup"]:
            old_val = os.environ[f.upper()]
            new_val =  os.path.join(os.environ["GITHUB_WORKSPACE"], f)
            os.environ[f.upper()] = new_val
            dodoo_tools._utils.run(["mkdir", "-p", new_val], "odoo")
            if old_val in os.environ["PYTHONPATH"]:
                os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"].replace(old_val, new_val)
            if old_val in os.environ["PIP_TARGET"]:
                os.environ["PIP_TARGET"] = os.environ["PIP_TARGET"].replace(old_val, new_val)
        dodoo_tools._utils.run(["chown", "-R", "odoo:odoo", os.environ["GITHUB_WORKSPACE"]])
    if not os.environ.get("GIT_REPO") and os.environ.get("GITHUB_REPOSITORY"):
        os.environ["GIT_REPO"] = "git@github.com:{}.git".format(os.environ["GITHUB_REPOSITORY"])
    return True


