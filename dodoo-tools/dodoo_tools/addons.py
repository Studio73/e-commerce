#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from os import environ, listdir, path

import click

from ._requirements import pip_install
from .cli import cli
from .repo import Repo


MERGE_STATUS = {
    "Not found": "❔",
    "Merged": "💟",
    "Not merged": "✅",
    "Conflicts": "⚠️",
}


def get_dependencies():
    src = environ["SRC"]
    odoo_version = environ["ODOO_VERSION"]
    repo_url = environ.get("GIT_REPO")
    main_repo = Repo(repo_url, odoo_version)
    main_repo.main_repo = True
    dependencies = [main_repo]
    merges = {}
    oca_dependencies_path = path.join(main_repo.path, "oca_dependencies.txt")
    if path.exists(oca_dependencies_path):
        # Inspired by OCA maintainer-quality-tools clone_oca_dependencies#L37
        with open(oca_dependencies_path) as oca_dependencies_file:
            for line in oca_dependencies_file:
                line = line.strip()
                if not line or not line.startswith("#merges"):
                    continue
                # eg: #merges l10n-spain 113,145
                parts = line.split()
                if len(parts) != 3:
                    _logger.error("Wrong merges definition: %s", line)
                    sys.exit(-1)
                merges[parts[1]] = parts[2].split(",")
            dependencies[0].merges = merges.get(dependencies[0].name, [])
            oca_dependencies_file.seek(0)  # Jump to first line
            for line in oca_dependencies_file:
                line = line.strip()
                if not line or line[0] == "#":
                    continue
                parts = line.split()
                repo_name = parts[0]
                if len(parts) > 1:
                    url = parts[1]
                else:
                    url = "https://github.com/OCA/%s.git" % repo_name
                if len(parts) > 2:
                    branch = parts[2]
                else:
                    branch = odoo_version
                repo = Repo(url, branch, merges.get(repo_name, []), repo_name)
                if len(parts) > 3:
                    org = parts[3]
                    repo_path = path.join(src, org, repo_name)
                    repo.path = repo_path
                dependencies.append(repo)
    if environ.get("ENTERPRISE"):
        enter_url = environ.get(
            "ENTERPRISE_REPO", "git@github.com:Studio73/enterprise.git"
        )
        enter_path = path.join(src, "odoo", "enterprise")
        enter_repo = Repo(enter_url, odoo_version, path=enter_path)
        enter_repo.odoo_repo = True
        dependencies.append(enter_repo)
    odoo_url = environ.get("ODOO_REPO", "https://github.com/odoo/odoo.git")
    odoo_path = path.join(src, "odoo", "odoo", "addons")
    odoo_repo = Repo(odoo_url, odoo_version, path=odoo_path)
    odoo_repo.odoo_repo = True
    dependencies.append(odoo_repo)
    return dependencies


def get_addons_path():
    return ",".join([a.path for a in get_dependencies()])


def _check_repos_permission(repos):
    access_granted = False
    access_error = []
    username = False
    password = False
    for r in repos:
        if not r.check_access():
            # Avoid ask for creadentials several times
            if not username or not password:
                r.api.set_credentials()
                username = r.api.username
                password = r.api.password
            else:
                r.api.set_credentials(username, password)
            r.ssh_keygen()
            access_granted = True
            upload_ok = r.upload_pub_key()
            if not upload_ok:
                access_error.append(r)
    if len(access_error):
        print("\n********************************************")
        print("*   Please, before start you must grant    *")
        print("*   SSH access to the next repositories    *")
        print("********************************************\n")
        for repo in access_error:
            print(repo.name)
            print("-" * len(repo.name))
            print(repo.get_pub_key())
            print("")
        sys.exit(-1)
    if access_granted:
        build_ssh_conf()


def main(to_update=False):
    if not environ.get("GIT_REPO"):
        _logger.error("Missing Git repository")
        sys.exit(-1)
    if not environ.get("ODOO_VERSION"):
        _logger.error("Missing Odoo version")
        sys.exit(-1)
    repos = get_dependencies()
    # ~/src/odoo/addons -> ~/src/odoo/
    repos[-1].path = repos[-1].path.replace("addons", "")
    _check_repos_permission(repos)
    if not path.exists(repos[0].path) or not listdir(repos[0].path):
        # First boot and the repository is not cloned yet
        repos[0].clone()
        repos = get_dependencies()
    for repo in repos:
        repo.clone()
        # Avoid update current development repository
        if environ.get("DEV") and repo.main_repo:
            continue
        if to_update:
            should_update = False
            if to_update == "all":
                should_update = True
            elif to_update == "all-skip-odoo":
                if not repo.odoo_repo:
                    should_update = True
            elif to_update in repo.name:
                should_update = True
            if should_update:
                repo.update()
    pip_install(
        [
            path.join(repo.path, "requirements.txt")
            for repo in repos[:-1]  # Skip Odoo requirements.txt
        ]
    )


@cli.group()
def addons():
    pass


@addons.command()
@click.argument("name")
def update(name):
    """Fetch and update sources from Github.

    \b
    NAME has this avaliable options:
    - 'all': Will update all repositories, including Odoo and Enterprise.
    - 'all-skip-odoo': Will update all repositories except Odoo & Enterprise.
    - <any>: Will update all matching repositories.
    """
    main(name)


@addons.command()
@click.argument("repo_name", default=False)
def merge_status(repo_name):
    """Check PR status using Gihub public API

    \b
    REPO_NAME:
    - If set, will check all matching repositories.
    - If not set, will check only repositories with "merges"
    """
    repos = []
    username = False
    password = False
    for r in get_dependencies():
        if (repo_name and repo_name in r.name) or (
            not repo_name and len(r.merges)
        ):
            if r.ssh_auth:
                # Avoid ask for creadentials several times
                if not username or not password:
                    r.api.set_credentials()
                    username = r.api.username
                    password = r.api.password
                else:
                    r.api.set_credentials(username, password)
            repos.append(r)
    max_len = max([len(r.name) for r in repos])
    if not len(repos):
        return True
    print("-" * max_len)
    for repo in repos:
        print("%s\n%s\n" % (repo.name, "-" * max_len))
        if repo.merges:
            for pr in repo.merges:
                status = repo.pr_status(pr)
                print("%s: %s %s\n" % (pr, MERGE_STATUS[status], status))
        else:
            print("Nothing to check\n")
        print("-" * max_len)


if __name__ == "__main__":
    main()
