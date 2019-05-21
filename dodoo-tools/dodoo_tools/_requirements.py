#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import os
import sys
import subprocess as sp


def pip_install(pip_files):
    freeze = sp.Popen(["pip", "freeze"], stdout=sp.PIPE).communicate()[0]
    installed_pip_packages = [
        p.split("==")[0].lower() for p in freeze.decode().strip().split("\n")
    ]
    for pip_file in pip_files:
        if os.path.exists(pip_file):
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
                    err_out = sp.call(["pip", "install", "-q", package])
                    if err_out:
                        print("Error installing %s" % package)
                        sys.exit(err_out)
                    installed_pip_packages.append(package_name.lower())


def main():
    # TODO: others requirements apt, npm, ...
    pip_install([os.path.join(os.environ["SETUP"], "pip.txt")])


if __name__ == "__main__":
    main()
