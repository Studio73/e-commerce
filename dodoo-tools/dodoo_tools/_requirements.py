#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import hashlib
import json
import logging
import os
import subprocess as sp
import sys

from packaging.requirements import Requirement
from packaging.version import Version

from ._utils import run, echo

_logger = logging.getLogger(__name__)


def cache_files(files, key):
    cache_dir = os.path.join(os.environ["DATA"], ".cache")
    install_json = os.path.join(cache_dir, "install.json")
    if not os.path.isdir(cache_dir):
        run(["mkdir", "-p", cache_dir])
    if not os.path.isfile(install_json):
        run(["chown", "-R", "odoo:odoo", cache_dir])
        run(["touch", install_json], "odoo")
    try:
        with open(install_json, "r") as fil:
            json_cache = json.load(fil)
    except Exception:
        json_cache = {}
    changed_files = []
    key_cache = json_cache.get(key, {})
    for f in files:
        if not os.path.exists(f):
            continue
        _hash = hashlib.md5(open(f, "rb").read()).hexdigest()
        if key_cache.get(f) != _hash:
            key_cache[f] = _hash
            changed_files.append(f)
    json_cache[key] = key_cache
    if changed_files:
        with open(install_json, "w") as fil:
            fil.write(json.dumps(json_cache, indent=4))
    return changed_files


def pip_install(pip_files, quiet=True):
    files2install = cache_files(pip_files, "pip")
    if not files2install:
        return True
    pip_bin = "pip3" if sys.version_info[0] == 3 else "pip"
    freeze = run([pip_bin, "freeze"])
    installed_pip_packages = {}
    for p in freeze.out.strip().split("\n"):
        p = Requirement(p)
        installed_pip_packages[p.name.lower()] = p
    packages2install = {}
    for pip_file in files2install:
        packages = open(pip_file, "r+").read().splitlines()
        for package in packages:
            package = package.strip()
            # Skip comments or empty lines
            if not package or package[0] == "#":
                continue
            # Packages like git+https://github.com/ORG/REPO.git
            # or like git+https://github.com/ORG/REPO.git@master
            if ".git" in package:
                if " @ " in package:
                    # e.g. server-ux/requirements.txt
                    # openupgradelib @ git+https://github.com/OCA/openupgradelib.git
                    requirement = Requirement(package)
                else:
                    _name = package.split(".git")[0].split("/")[-1]
                    requirement = Requirement("%s @ %s" % (_name, package))
                packages2install[requirement.name.lower()] = requirement
                # Stop iteration, always install git repos
                continue
            requirement = Requirement(package)
            if requirement.marker and not requirement.marker.evaluate():
                # If package has a marker check if is compatible with current env
                # e.g. matplotlib==3.4.1; python_version >= '3.7'
                continue
            req_name = requirement.name.lower()
            req_version = list(requirement.specifier)
            req_version = Version(req_version and req_version[0].version or "0.0")
            if installed_pip_packages.get(req_name):
                # Discarting current version if is not set or lower than the installed one
                i_version = list(installed_pip_packages[req_name].specifier)
                i_version = Version(i_version and i_version[0].version or "0.0")
                if req_version <= i_version:
                    continue
            if packages2install.get(req_name):
                # Discarting current version if is lower than the one to be installed
                i_version = list(packages2install[req_name].specifier)
                i_version = Version(i_version and i_version[0].version or "0.0")
                if req_version <= i_version:
                    continue
            # Install the highest version
            packages2install[requirement.name] = requirement
    for requirement in packages2install.values():
        package = requirement.name
        if list(requirement.specifier):
            spec = list(requirement.specifier)[0]
            package = "%s%s%s" % (package, spec.operator, spec.version)
        elif requirement.url:
            # git+https://github.com/ORG/REPO.git@abcd1234
            package = requirement.url
        install_cmd = [
            pip_bin,
            "--disable-pip-version-check",
            "install",
            "--ignore-installed",
            "--upgrade",
            # Avoid upgrade packages from Odoo requirements.txt
            "--constraint",
            os.path.join(os.environ["SRC"], "odoo", "odoo", "requirements.txt"),
            package,
        ]
        if quiet:
            with echo("%s install %s" % (pip_bin, package)):
                r = run(install_cmd)
                if "ERROR:" in r.error and "dependency resolver" not in r.error:
                    raise Exception(r.error)
        else:
            _logger.info(" ".join(install_cmd))
            r = sp.call(install_cmd)
            if r != 0:
                exit(r)


def main():
    # TODO: others requirements apt, npm, ...
    pip_install([os.path.join(os.environ["SETUP"], "pip.txt")])


if __name__ == "__main__":
    main()
