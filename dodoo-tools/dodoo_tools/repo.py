#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess as sp
import requests

from os import environ, listdir, path

from .github import GithubAPI
from ._utils import echo, run, DEVNULL


class Repo(object):
    def __init__(self, url, branch, merges=[], name=None, path=None):
        self.url = url
        self.branch = branch
        self.merges = merges
        self.name = name or self.get_name()
        self.org = self.get_org()
        self.path = path or self.get_path()
        self.main_repo = False
        self.odoo_repo = False
        self.ssh_auth = self.url.startswith("git@")
        if self.ssh_auth and not environ.get("DEV"):
            self.url = self.url.replace("github.com", self.name)
        self.api = GithubAPI(self.org, self.name)

    def get_name(self):
        """
        Extract repository name from Github URL e.g.
        e.g. github.com/Studio73/studio73-addons.git -> studio73-addons
        """
        return self.url.split("/")[-1].replace(".git", "")

    def get_org(self):
        """
        Extract org name from Github URL e.g.
        github.com/Studio73/studio73-addons/ -> studio73
        git@github.com:Studio73/studio73-addons/ -> studio73
        """
        return self.url.strip("/").split("/")[-2].lower().split(":")[-1]

    def get_path(self):
        """
        Build path from ORG name
        """
        return path.join(environ["SRC"], self.org, self.name)

    def git_cmd(self, cmd, args=None, quiet=True):
        _cmd = [
            "git",
            "--git-dir=%s" % path.join(self.path, ".git"),
            "--work-tree=%s" % self.path,
            cmd,
        ]
        if quiet:
            _cmd.append("-q")
        if args:
            _cmd += args
        return _cmd

    def clean(self, depth=1, quiet=True):
        sp.check_call(
            self.git_cmd("reset", ["--hard", "origin/%s" % self.branch], quiet),
            stderr=DEVNULL,
        )
        sp.check_call(
            self.git_cmd("checkout", [self.branch], quiet), stderr=DEVNULL
        )
        sp.check_call(
            self.git_cmd("fetch", ["origin", "--depth=%s" % depth], quiet),
            stderr=DEVNULL,
        )
        sp.check_call(self.git_cmd("clean", ["-fdx"], quiet), stderr=DEVNULL)
        r = run(self.git_cmd("branch"))
        active_branch = "* %s" % self.branch
        for branch in r.out.strip().split("\n"):
            branch = branch.strip()
            if branch == active_branch:
                continue
            sp.check_call(
                self.git_cmd("branch", ["-D", branch], quiet), stderr=DEVNULL
            )

    def do_merges(self, quiet=True):
        prs = {"to_merge": [], "not_merge": {}}
        if not len(self.merges):
            return prs
        depth = 1
        for pr in self.merges:
            status = self.pr_status(pr)
            if status not in ["Not merged", "Not found"]:
                prs["not_merge"][pr] = status
                continue
            sp.check_call(
                self.git_cmd(
                    "fetch",
                    ["origin", "refs/pull/%s/head:%s" % (pr, pr)],
                    quiet,
                )
            )
            r = run(
                self.git_cmd(
                    "rev-list",
                    [
                        "--count",
                        "--no-merges",
                        "origin/%s..%s" % (self.branch, pr),
                    ],
                    False,
                )
            )
            depth += int(r.out.strip())
            prs["to_merge"].append(pr)
        if not len(prs["to_merge"]):
            return prs
        sp.check_call(
            self.git_cmd("fetch", ["origin", "--depth=%s" % depth], quiet)
        )
        sp.check_call(
            self.git_cmd(
                "checkout", ["-b", "merges", "origin/%s" % self.branch], quiet
            )
        )
        r = run(self.git_cmd("branch"))
        for pr in prs["to_merge"]:
            sp.check_call(self.git_cmd("merge", ["--no-edit", pr], quiet))
        return prs

    def update(self, quiet=True):
        with echo("Updating %s" % self.name):
            self.clean(quiet=quiet)
            merge_status = self.do_merges(quiet)
        if merge_status["not_merge"].keys():
            print("Some merges where not applied, please check \n")
            for pr, status in merge_status["not_merge"].items():
                print("%s: %s %s\n" % (pr, MERGE_STATUS[status], status))

    def clone(self, depth=1, **kwargs):
        if not path.exists(self.path) or not listdir(self.path):
            with echo("Cloning %s" % self.name):
                cmd = ["git", "clone", "--quiet"]
                if depth:
                    cmd += ["--depth", repr(depth)]
                cmd += ["-b", self.branch, self.url, self.path]
                sp.check_call(cmd)
            self.do_merges()

    def check_access(self):
        if not self.ssh_auth:
            return True
        call = run(["git", "ls-remote", "--exit-code", "-h", self.url], "odoo")
        if call.returncode == 0:
            return True
        if (
            "Permission denied" in call.error
            or "Could not resolve hostname" in call.error
        ):
            return False
        else:
            raise Exception(call.error)

    def ssh_keygen(self):
        ssh_key = path.join(environ["DATA"], ".ssh", self.name)
        if not path.exists(ssh_key):
            comment = "%s@%s" % (self.name, environ["DATABASE"])
            run(["ssh-keygen", "-N", "", "-f", ssh_key, "-C", comment], "odoo")
        return True

    def get_pub_key(self):
        if not self.ssh_auth:
            return ""
        ssh_key = path.join(environ["DATA"], ".ssh", "%s.pub" % self.name)
        if not path.exists(ssh_key):
            raise Exception("Not found public key: %s" % ssh_key)
        return run(["cat", ssh_key]).out.strip()

    def upload_pub_key(self):
        # TODO: Move to Github
        # docs https://developer.github.com/v3/repos/keys/#add-a-new-deploy-key
        params = {
            "title": "Dodoo %s - (auto)" % environ["DATABASE"],
            "key": self.get_pub_key(),
            "read_only": True,
        }
        with echo("Uploading %s deploy key" % self.name):
            call = self.api.post("keys", auth=True, **params)
        if call.status_code != 201:  # Created
            print("! API response: %s" % call.json()["message"])
            return False
        return True

    def pr_status(self, pr_id):
        call = self.api.get("pulls", pr_id, self.ssh_auth)
        if call.status_code != 200:
            return "Not found"
        else:
            resp = call.json()
            if resp.get("merged"):
                return "Merged"
            elif resp.get("mergeable"):
                return "Not merged"
            else:
                return "Conflicts"

