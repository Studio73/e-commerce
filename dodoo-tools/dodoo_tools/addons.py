#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import sys
import time
from datetime import timedelta
from os import environ, listdir, path
from tabulate import tabulate

import click

from ._requirements import pip_install
from .cli import cli
from .repo import Repo, MERGE_STATUS

_logger = logging.getLogger(__name__)


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
                # eg: web https://github.com/OCA/web 14.0 aaabbbccc
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
                if len(parts) > 3:
                    sha = parts[3]
                else:
                    sha = False
                repo = Repo(url, branch, merges.get(repo_name, []), repo_name, sha=sha)
                dependencies.append(repo)
    odoo_url = environ.get("ODOO_REPO", "https://github.com/odoo/odoo.git")
    odoo_path = path.join(src, "odoo")
    odoo_repo = Repo(odoo_url, odoo_version, path=odoo_path)
    odoo_repo.odoo_repo = True
    dependencies.append(odoo_repo)
    return dependencies


def get_addons_path():
    deps = [a.path for a in get_dependencies()]
    deps[-1] = path.join(deps[-1], "addons")  # ~/src/odoo/ -> ~/src/odoo/addons
    return ",".join(deps)


def main(to_update=False, org=False, quiet=True):
    if not environ.get("GIT_REPO"):
        _logger.error("Missing Git repository")
        sys.exit(-1)
    if not environ.get("ODOO_VERSION"):
        _logger.error("Missing Odoo version")
        sys.exit(-1)
    repos = get_dependencies()
    if not path.exists(repos[0].path) or not listdir(repos[0].path):
        # First boot and the repository is not cloned yet
        repos[0].clone(quiet=quiet)
        # Compute again repo dependencies
        repos = get_dependencies()
    for repo in repos:
        # Avoid update current development repository
        if environ.get("DEV") and repo.main_repo:
            continue
        if not path.exists(repo.path) or not listdir(repo.path):
            repo.clone(quiet=quiet)
        if to_update:
            should_update = False
            if org and to_update == repo.org:
                should_update = True
            else:
                if to_update == "all":
                    should_update = True
                elif to_update == "all-skip-odoo":
                    if not repo.odoo_repo:
                        should_update = True
                elif to_update in repo.name:
                    should_update = True
            if should_update:
                repo.update(quiet)
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
@click.option(
    "-o",
    "--org",
    is_flag=True,
    help="Match by organization name instead of repository name",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Turn on verbosity",
)
@click.argument("name")
def update(name, org, verbose):
    """Fetch and update sources from Github.

    \b
    NAME has this avaliable options:
    - 'all': Will update all repositories, including Odoo.
    - 'all-skip-odoo': Will update all repositories except Odoo.
    - <any>: Will update all matching repositories.
    """
    quiet = not verbose
    main(name, org, quiet)


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
    token = environ.get("GITHUB_TOKEN", "")
    for r in get_dependencies():
        if (repo_name and repo_name in r.name) or (not repo_name and len(r.merges)):
            repos.append(r)
    if not len(repos):
        return True
    table = []
    for repo in repos:
        for pr in repo.merges:
            status = repo.pr_status(pr)
            table.append([repo.name, pr, "%s %s" % (MERGE_STATUS[status], status)])
    print(
        tabulate(
            table,
            headers=["Repo", "PR", "Status"],
            showindex="always",
            tablefmt="psql",
        )
    )


if __name__ == "__main__":
    main()
