#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import hashlib
import json
import os
import sys
from ._utils import run



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
        _hash = hashlib.md5(open(f, 'rb').read()).hexdigest()
        if key_cache.get(f) != _hash:
            key_cache[f] = _hash
            changed_files.append(f)
    json_cache[key] = key_cache
    if changed_files:
        with open(install_json, "w") as fil:
            fil.write(json.dumps(json_cache, indent=4))
    return changed_files


def pip_install(pip_files):
    files2install = cache_files(pip_files, "pip")
    if not files2install:
        return True
    freeze = run(["pip", "freeze"])
    installed_pip_packages = [
        p.split("==")[0].lower() for p in freeze.out.strip().split("\n")
    ]
    for pip_file in files2install:
        packages = open(pip_file, "r+").read().splitlines()
        for package in packages:
            package = package.strip()
            # Skip comments or empty lines
            if not package or package[0] == "#":
                continue
            # Convert zpl2>=1.1 -> zpl2==1.1
            package_name = package.replace(">", "=").replace("<", "=")
            package_name = package_name.split("==")[0]
            # Packages like git+https://github.com/ORG/REPO.git
            # or like git+https://github.com/ORG/REPO.git@master
            if ".git" in package_name:
                package_name = package_name.split(".git")[0].split("/")[-1]
            if package_name.lower() not in installed_pip_packages:
                r = run(["pip", "install", "-q", package])
                if r.returncode != 0:
                    raise Exception("Error installing %s\n\n %s" % (package, r.error))
                installed_pip_packages.append(package_name.lower())


def main():
    # TODO: others requirements apt, npm, ...
    pip_install([os.path.join(os.environ["SETUP"], "pip.txt")])


if __name__ == "__main__":
    main()
