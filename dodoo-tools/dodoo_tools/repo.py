#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import getpass
import subprocess as sp
import sys

from os import environ, listdir, path

from .github import GithubAPI
from ._utils import echo, run, DEVNULL, build_ssh_conf


_logger = logging.getLogger(__name__)
MERGE_STATUS = {"Not found": "❔", "Merged": "💟", "Not merged": "✅", "Conflicts": "⚠️"}


class Repo(object):
    def __init__(self, url, branch, merges=[], name=None, path=None, sha=None):
        self.url = url
        self.branch = branch
        self.merges = merges
        self.name = name or self.get_name()
        self.org = self.get_org()
        self.path = path or self.get_path()
        self.sha = sha
        self.main_repo = False
        self.odoo_repo = False
        self.private = self.url.startswith("git@")
        self.api = GithubAPI(self.org, self.name)
        self.set_url()

    def set_url(self):
        """Compute correct URL: ssh, https or https+token
        """
        if not self.private:
            return
        if environ.get("DEV"):
            if self.api.token:
                self.url = "https://{}@github.com/{}/{}.git".format(
                    self.api.token, self.org, self.name
                )
        else:
            # Only use ssh keys in production env
            self.url = self.url.replace("github.com", self.name)

    def get_name(self):
        """Extract repository name from Github URL e.g.
        e.g. github.com/Studio73/studio73-addons.git -> studio73-addons
        """
        return self.url.split("/")[-1].replace(".git", "")

    def get_org(self):
        """Extract org name from Github URL e.g.
        github.com/Studio73/studio73-addons/ -> studio73
        git@github.com:Studio73/studio73-addons/ -> studio73
        """
        return self.url.strip("/").split("/")[-2].lower().split(":")[-1]

    def get_path(self):
        """Build path from ORG name
        """
        return path.join(environ["SRC"], self.org, self.name)

    def git_cmd(self, cmd, args=None, quiet=True):
        _cmd = [
            "git",
            "--git-dir=%s" % path.join(self.path, ".git"),
            "--work-tree=%s" % self.path,
            cmd,
        ]
        if args:
            _cmd += args
        return _cmd

    def git_run(self, cmd, args=None, quiet=True, user="odoo"):
        _cmd = self.git_cmd(cmd, args, quiet)
        if quiet:
            result = run(_cmd, user)
        else:
            _logger.info(" ".join(_cmd))
            result = sp.call(_cmd)
        return result

    def clean(self, depth=10, quiet=True):
        self.git_run("reset", ["--hard"], quiet)
        self.git_run("checkout", [self.branch], quiet)
        self.git_run("fetch", ["origin", "--depth=%s" % depth], quiet)
        self.git_run("clean", ["-fd"], quiet)
        self.git_run("reset", ["--hard", "origin/%s" % self.branch], quiet)
        r = self.git_run("branch")
        active_branch = "* %s" % self.branch
        for branch in r.out.strip().split("\n"):
            branch = branch.strip()
            if branch == active_branch:
                continue
            self.git_run("branch", ["-D", branch], quiet)
        if self.sha:
            log_res = run(self.git_cmd("log"))
            sha_found = self.sha in log_res.out.strip()
            while not sha_found or depth <= 1000:
                depth += 10
                self.git_run("fetch", ["origin", "--depth=%s" % depth], quiet)
                log_res = run(self.git_cmd("log"))
                if self.sha in log_res.out.strip():
                    sha_found = True
            if sha_found:
                self.git_run("reset", ["--hard", self.sha], quiet)

    def do_merges(self, quiet=True):
        prs = {"to_merge": [], "not_merge": {}}
        if not len(self.merges) or self.sha:
            return prs
        depth = 10
        for pr in self.merges:
            status = self.pr_status(pr)
            if status not in ["Not merged", "Not found"]:
                prs["not_merge"][pr] = status
                continue
            self.git_run("fetch", ["origin", "refs/pull/%s/head:%s" % (pr, pr)], quiet)
            rev_list_cmd = self.git_cmd(
                "rev-list",
                ["--count", "--no-merges", "origin/%s..%s" % (self.branch, pr)],
            )
            r = run(rev_list_cmd)
            try:
                depth += int(r.out.strip())
            except ValueError:
                """ Case We're trying to merge a PR
                while the repo target branch is the same, e.g.,
                > oca_dependencies.txt
                    web https://github.com/Studio73/web.git 12.0-add_new_module
                    #merges web XXX
                > error
                    fatal: ambiguous argument 'origin/BRANCH_NAME..PR_NUMBER'
                """
                continue
            prs["to_merge"].append(pr)
        if not len(prs["to_merge"]):
            return prs
        self.git_run("fetch", ["origin", "--depth=%s" % depth], quiet)
        self.git_run("checkout", ["-b", "merges", "origin/%s" % self.branch], quiet)
        r = self.git_run("branch")
        for pr in prs["to_merge"]:
            self.git_run("merge", ["--no-edit", pr], quiet)
        return prs

    def update(self, quiet=True):
        if not path.exists(self.path) or not listdir(self.path):
            # If not exists clone instead of update
            self.clone(quiet=quiet)
            return
        self.check_access()
        with echo("Updating  %s/%s" % (self.org, self.name), tty=quiet):
            self.clean(quiet=quiet)
            merge_status = self.do_merges(quiet)
        if merge_status["not_merge"].keys():
            print("Some merges where not applied, please check \n")
            for pr, status in merge_status["not_merge"].items():
                print("%s: %s %s\n" % (pr, MERGE_STATUS[status], status))

    def clone(self, depth=10, quiet=True, **kwargs):
        if not path.exists(self.path) or not listdir(self.path):
            self.check_access()
            with echo("Cloning %s/%s" % (self.org, self.name), tty=quiet):
                cmd = ["git", "clone"]
                if environ.get("GIT_IDENTITY_FILE"):
                    id_file = environ.get("GIT_IDENTITY_FILE")
                    cmd += ["-c", "core.sshCommand=ssh -i ~/.ssh/%s" % id_file]
                if depth:
                    cmd += ["--depth", repr(depth)]
                if quiet:
                    cmd.append("--quiet")
                cmd += ["-b", self.branch, self.url, self.path]
                if quiet:
                    run(cmd, "odoo")
                else:
                    _logger.info(" ".join(cmd))
                    if getpass.getuser() != "odoo":
                        cmd = ["gosu", "odoo"] + cmd
                    sp.call(cmd)
            self.do_merges()

    def check_access(self):
        if not self.private:
            return True
        cmd = ["git"]
        if environ.get("GIT_IDENTITY_FILE"):
            cmd += ["-c", "core.sshCommand=ssh -i ~/.ssh/%s" % environ.get("GIT_IDENTITY_FILE")]
        cmd += ["ls-remote", "--exit-code", "-h", self.url]
        call = run(cmd, "odoo")
        if call.returncode == 0:
            return True
        if "UNPROTECTED PRIVATE KEY FILE" in call.error:
            ssh_key = path.join(environ["DATA"], ".ssh", self.name)
            run(["chmod", "0600", "%s.pub" % ssh_key])
            run(["chmod", "0600", ssh_key])
            return self.check_access()
        elif (
            "Permission denied" in call.error
            or "Could not resolve hostname" in call.error
        ):
            self.ssh_keygen()
            self.upload_pub_key()
            build_ssh_conf()
            return True
        else:
            raise Exception("%s\n%s" % (self.url, call.error))

    def ssh_keygen(self):
        ssh_key = path.join(environ["DATA"], ".ssh", self.name)
        if not path.exists(ssh_key):
            comment = "%s@%s" % (self.name, environ["DATABASE"])
            r = run(["ssh-keygen", "-N", "", "-f", ssh_key, "-C", comment], "odoo")
            if r.returncode != 0 and "Permission denied" in r.error:
                run(["chown", "-R", "odoo:odoo", path.join(environ["DATA"], ".ssh")])
                run(["ssh-keygen", "-N", "", "-f", ssh_key, "-C", comment], "odoo")
            run(["chmod", "0600", ssh_key, "%s.pub" % ssh_key])
        return True

    def get_pub_key(self):
        if not self.private:
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
        self.api.set_credentials()
        with echo("Uploading %s deploy key" % self.name):
            call = self.api.post("keys", auth=True, **params)
        if call.status_code != 201:  # Created
            print("! API response: %s" % call.json()["message"])
            print("\n*******************************************")
            print("*   Please, before start you must grant   *")
            print("*   SSH access to the next repository     *")
            print("*******************************************\n")
            print(self.name)
            print("-" * len(self.name))
            print(self.get_pub_key())
            print("")
            sys.exit(-1)
        return True

    def pr_status(self, pr_id):
        if self.private:
            self.api.set_credentials()
        call = self.api.get("pulls", pr_id, self.private)
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
