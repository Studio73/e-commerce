#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import getpass
import logging
import os
import re
import subprocess as sp
import tempfile
import time

import click

from ._utils import DEVNULL, format_time, print_table, run as _run
from .addons import get_dependencies
from .cli import cli
from .database import _database_exists

_logger = logging.getLogger(__name__)


def get_addons(repo):
    addons = []
    for fil in os.listdir(repo.path):
        manifest = os.path.join(repo.path, fil, "__manifest__.py")
        if not os.path.exists(manifest):
            manifest = os.path.join(repo.path, fil, "__openerp__.py")
        if os.path.exists(manifest):
            m = ast.literal_eval(open(manifest, "r").read())
            if m.get("installable", True):
                addons.append(fil)
    return addons


def get_diff_patch(repo_path, available_addons):
    r = _run(
        [
            "git",
            "--no-pager",
            "diff",
            "--name-only",
            "{}..HEAD".format(os.environ["ODOO_VERSION"]),
        ],
        cwd=repo_path,
    )
    addons = []
    for l in (r.out or "").split():
        addon = os.path.normpath(l)
        if addon:
            addon = str(addon).split(os.sep)[0]
            if addon not in addons and addon in available_addons:
                addons.append(addon)
    return addons


def parse_log(logfile):
    # '<DATE> ERROR <DATABASE> odoo.modules.loading: Module <MODULE>: 1 failures, 0 errors of 1 tests
    re_err = re.compile(r"^(?P<date>.*?)ERROR(.*?)Module(?P<module>.*?):(.*#?)tests$")
    re_warn = re.compile(
        r"^(?P<date>.*?)WARNING (?P<database>.*?) (?P<logger>.*?): (?P<warning>.*?)$"
    )
    result = {"error": [], "warning": [], "critical": []}
    logfile.seek(0)
    for line in logfile.readlines():
        line = line.strip().decode("UTF-8")
        err_match = re_err.match(line)
        if err_match:
            result["error"].append(err_match.groupdict()["module"].strip())
        elif "CRITICAL" in line:
            result["critical"].append(line)
        else:
            # WARNING message
            warn_match = re_warn.match(line)
            if warn_match:
                warn_dict = warn_match.groupdict()
                warn_logger = warn_dict["logger"].strip()
                if warn_logger == "odoo.tests.runner":
                    # Test results: 0 failed, 0 error(s) of 0 tests when loading database
                    continue
                warn_msg = warn_dict["warning"].strip()
                if (warn_logger, warn_msg) not in result["warning"]:
                    result["warning"].append((warn_logger, warn_msg))
    return result


@cli.group()
def tests():
    pass


@tests.command()
@click.option("-f", "--force-recreate", is_flag=True)
@click.option("-l", "--log-level", default="info")
@click.option("-d", "--database")
@click.argument("addons", default="")
def run(addons, database, log_level, force_recreate):
    start_time = time.time()
    if not database:
        database = "{}_test".format(os.environ["DATABASE"])
    repos = get_dependencies()
    main_repo = list(filter(lambda r: r.main_repo, repos))[0]
    odoo_repo = list(filter(lambda r: r.odoo_repo, repos))[0]
    local_addons = get_addons(main_repo)
    if addons:
        addons = [m.strip() for m in addons.split(",") if m.strip() in local_addons]
    else:
        addons = local_addons
    if not addons:
        raise Exception("No addons to test")
    cmd = [
        os.path.join(odoo_repo.path, "odoo-bin"),
        "-d",
        database,
        "--log-level=%s" % log_level,
        "--stop-after-init",
        "-i",
        ",".join(addons),
    ]
    if not _database_exists(database) or force_recreate:
        sp.call(["dropdb", "--if-exists", database], stdout=DEVNULL, stderr=DEVNULL)
        _logger.info("Creating instance: {}".format(" ".join(cmd)))
        try:
            sp.check_call(cmd)
        except sp.CalledProcessError as e:
            exit(e.returncode)
    tests_cmd = ["coverage", "run"]
    rcfile = os.path.join(main_repo.path, ".coveragerc")
    if os.path.exists(rcfile):
        tests_cmd += ["--rcfile={}".format(rcfile)]
    cmd = tests_cmd + cmd + ["--test-enable"]
    _logger.info("Running tests: {}".format(" ".join(cmd)))
    pipe = sp.Popen(cmd, stderr=sp.STDOUT, stdout=sp.PIPE, cwd=main_repo.path)
    logfile = tempfile.TemporaryFile()
    for line in iter(pipe.stdout.readline, b""):
        logfile.write(line)
        print(line.strip().decode("UTF-8", errors="backslashreplace"))
    result = parse_log(logfile)
    logfile.close()
    returncode = pipe.wait()
    if result.get("critical") or result.get("error"):
        returncode = 254
    if result.get("warning"):
        print_table(result["warning"], ["Logger", "Warning message"])
        print("")
    print_table(
        [
            [a, "❌"] if a in result.get("error", []) else [a, "✅"]
            for a in sorted(addons)
        ],
        ["Module", "Result"],
    )
    elapsed_time = format_time(round(time.time() - start_time, 2))
    if returncode != 0:
        print_table([["❌ Failed ({})".format(returncode), elapsed_time]])
    else:
        print_table([["✅ Succeed", elapsed_time]])
    exit(returncode)


@tests.command()
@click.argument("addons", default="")
def coverage(addons):
    repos = get_dependencies()
    main_repo = list(filter(lambda r: r.main_repo, repos))[0]
    local_addons = get_addons(main_repo)
    if addons:
        diff_addons = [m.strip() for m in addons.split(",")]
    else:
        diff_addons = get_diff_patch(main_repo.path, local_addons)
    coverage_cmd = ["coverage", "report", "-m"]
    rcfile = os.path.join(main_repo.path, ".coveragerc")
    if os.path.exists(rcfile):
        coverage_cmd += ["--rcfile={}".format(rcfile)]
    total = "~"
    pipe = sp.Popen(coverage_cmd, stderr=sp.STDOUT, stdout=sp.PIPE, cwd=main_repo.path)
    for line in iter(pipe.stdout.readline, b""):
        line = line.strip().decode("UTF-8", errors="backslashreplace")
        print(line)
        if "TOTAL" in line:
            total = line.split()[-1]
    print("")
    print_table([["☔Project coverage", total]])
    if diff_addons:
        print("")
        diff_addons = ["{}*".format(a) for a in diff_addons]
        coverage_cmd.append("--include={}".format(",".join(diff_addons)))
        total = "~"
        pipe = sp.Popen(
            coverage_cmd, stderr=sp.STDOUT, stdout=sp.PIPE, cwd=main_repo.path
        )
        for line in iter(pipe.stdout.readline, b""):
            line = line.strip().decode("UTF-8", errors="backslashreplace")
            print(line)
            if "TOTAL" in line:
                total = line.split()[-1]
        print("")
        print_table([["☔Patch coverage", total]])
    exit(0)
