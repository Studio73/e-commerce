#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import logging
import os
import re
import subprocess as sp
import sys
from collections import OrderedDict
from pprint import pprint

import click
import requests
import yaml

AVAILABLE_VERSIONS = ["14.0", "15.0"]

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)
_logger = logging.getLogger(__name__)


class ToolsYaml(object):
    def __init__(self, version, repos_yaml):
        self.headers = self.get_gh_headers()
        self.version = version
        self.repos_yaml = repos_yaml
        self.gh_rate_remaing = 0
        self.gh_rate_limit = 0
        self.gh_rate_used = 0
        if not os.path.exists(repos_yaml):
            print("File not found: {}".format(repos_yaml))
            sys.exit(1)
        stream = open(self.repos_yaml, "r")
        self.yaml = yaml.safe_load(stream) or {}
        stream.close()

    def get_gh_headers(self):
        headers = {}
        gh_token = os.environ.get("GITHUB_TOKEN")
        if not gh_token:
            _logger.error("Missing GITHUB_TOKEN environment variable")
            sys.exit(1)
        headers = {
            "Authorization": "token {}".format(gh_token),
            "Accept": "application/vnd.github.v3+json",
        }
        return headers

    def run_query(self, query, variables=None):
        params = {"query": query}
        if variables:
            params["variables"] = variables
        r = requests.post(
            "https://api.github.com/graphql", json=params, headers=self.get_gh_headers()
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("data"):
            _logger.error("Github query error:")

            click.echo(pprint(data))
            sys.exit(1)
        self.gh_rate_limit = r.headers["X-RateLimit-Limit"]
        self.gh_rate_remaing = r.headers["X-RateLimit-Remaining"]
        self.gh_rate_used = r.headers["X-RateLimit-Used"]
        return data["data"]

    def is_pr_open(self, org, repo, nbr):
        is_open = True
        query = """
            query($owner: String!, $repo: String!, $number: Int!) {
                repository(owner: $owner, name: $repo){
                    pullRequest(number: $number){
                        state
                        merged
                    }
                }
            }
        """
        data = self.run_query(query, {"owner": org, "repo": repo, "number": int(nbr)})
        # If pullRequest == None is because it doesnt exists
        pr_data = data["repository"]["pullRequest"] or {"state": "MERGED"}
        pr_state = pr_data.get("state")
        pr_merged = pr_data.get("merged")
        if pr_state == "CLOSED":
            action = "⁉️"
        if pr_state == "MERGED" or pr_merged:
            action = "🔥"
            is_open = False
        else:
            action = "✅"
        _logger.info("* {}\t->\t{}".format(nbr, action))
        return is_open

    def get_latest_sha(self, org, repo, branch):
        query = """
            query($owner: String!, $repo: String!, $branch: String!) {
                repository(owner: $owner, name: $repo){
                    object(expression: $branch){
                        ... on Commit {
                            history(first: 1){
                                nodes {
                                    oid
                                    committedDate
                                }
                            }
                        }
                    }
                }
            }
        """
        data = self.run_query(query, {"owner": org, "repo": repo, "branch": branch})
        gh_commit = data["repository"]["object"]["history"]["nodes"][0]
        if not isinstance(gh_commit, dict):
            _logger.error("{} not a valid value".format(gh_commit))
            _logger.error(data)
            sys.exit(1)
        new_sha = gh_commit.get("oid", "asdf")
        if not re.findall("[0-9a-f]{5,40}", new_sha):
            _logger.error("{} not a valid commit".format(gh_commit))
            sys.exit(1)
        _logger.info(
            "* commit\t->\t{}  # {}".format(new_sha, gh_commit.get("committedDate", ""))
        )
        return new_sha

    def get_open_prs(self, org, repo, branch):
        query = """
            query($owner: String!, $repo: String!, $branch: String!) {
                repository(owner: $owner, name:$repo) {
                    pullRequests(last: 50, states: OPEN, baseRefName: $branch) {
                        nodes {
                            number
                            title
                            isDraft
                            mergeable
                            state
                            commits(last: 1) {
                                nodes {
                                    commit {
                                        statusCheckRollup {
                                            state
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """
        data = self.run_query(query, {"owner": org, "repo": repo, "branch": branch})
        prs = []
        open_prs = data["repository"]["pullRequests"]["nodes"]
        if len(open_prs):
            _logger.info("[Open PRS]")
        for pr in open_prs:
            tag = "* {}".format(pr["number"])
            title = pr.get("title", "").lower()
            if "[force dev]" in title or "[dev force]" in title:
                _logger.info("{}\t->\t ✅ Title contains [force dev]".format(tag))
                prs.append("origin refs/pull/{}/head".format(pr["number"]))
                continue
            if "[skip dev]" in title or "[dev skip]" in title:
                _logger.info("{}\t->\t ❌ Title contains [skip dev]".format(tag))
                continue
            if pr.get("isDraft"):
                _logger.info("{}\t->\t ❌ Draft PR".format(tag))
                continue
            if pr.get("mergeable") == "CONFLICTING":
                _logger.info("{}\t->\t ❌ PR with conflicts".format(tag))
                continue
            status_check_rollup = (
                pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"] or {}
            )
            if status_check_rollup.get("state") == "SUCCESS":
                _logger.info("{}\t->\t ✅ Mergeable PR".format(tag))
                prs.append("origin refs/pull/{}/head".format(pr["number"]))
            else:
                _logger.info("{}\t->\t ❌ CI status check FAILED".format(tag))
        return prs

    def add_repo(self, repo_name, repo_url):
        if repo_name in self.yaml.items():
            return True
        self.yaml[repo_name] = {
            "defaults": {"depth": 1},
            "merges": ["origin {}".format(self.version)],
            "remotes": {"origin": repo_url},
        }
        return True

    def update_repos(self, add_open_prs):
        res_yaml = OrderedDict()
        for name, data in self.yaml.items():
            origin = data.get("remotes", {}).get("origin")
            origin = (
                origin.replace("git@github.com:", "")
                .replace("https://github.com/", "")
                .replace(".git", "")
            )
            org, repo = origin.split("/")
            _logger.info("[{}/{}]".format(self.version, repo))
            merges = []
            for merge in data["merges"]:
                pr = re.findall("(?:refs/pull/)(\\d+)(?:/head)", merge)
                if pr:
                    # Pull request -> origin refs/pull/XXX/head
                    if self.is_pr_open(org, repo, pr[0]):
                        merges.append(merge)
                else:
                    if add_open_prs:
                        # We dont want to update the commit sha
                        # because we are just adding all open prs
                        merges.append(merge)
                        commit_sha = merge.split()[-1]
                        _logger.info("* commit\t->\t{}".format(commit_sha))
                    else:
                        # Update commit sha to latest version
                        # Base commit -> origin latest_commit_sha
                        remote_name = merge.split()[0]
                        new_sha = self.get_latest_sha(org, repo, self.version)
                        merges.append("{} {}".format(remote_name, new_sha))
            if add_open_prs:
                open_prs = self.get_open_prs(org, repo, self.version)
                merges = list(set(merges + open_prs))
            data["defaults"]["depth"] = 500 if len(merges) > 1 else 1
            data["merges"] = sorted(merges)
            res_yaml[name] = data
        self.yaml = res_yaml

    def print_limits(self):
        _logger.info(
            "GH Limits\t->\t Total: {} | Remaining: {} | Used: {} ".format(
                self.gh_rate_limit, self.gh_rate_remaing, self.gh_rate_used
            )
        )

    def save(self):
        with open(self.repos_yaml, "w") as yaml_file:
            yaml.dump(dict(self.yaml), yaml_file)


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


@click.group()
def tools():
    pass


@tools.command()
@click.option("-c", "--cwd")
def lint(cwd):
    if not cwd:
        cwd = os.getcwd()
    exitcode = sp.call(["pre-commit", "run", "--all-files"], cwd=cwd)
    sys.exit(exitcode)


@tools.command()
@click.option(
    "--add-open-prs",
    is_flag=True,
    envvar="ADD_OPEN_PRS",
    help="If true instead of update to latest version will look for open PR and add them to the file",
)
@click.option("--commit", is_flag=True, envvar="COMMIT")
@click.option(
    "-v",
    "--version",
    type=click.Choice(AVAILABLE_VERSIONS),
    required=True,
    envvar="ODOO_VERSION",
)
@click.option(
    "--config",
    default="repos.yaml",
    help="git-aggregattor config file to update",
)
@click.option("-c", "--cwd", help="Move to directory")
def update_repos(cwd, config, version, commit, add_open_prs):
    if not cwd:
        cwd = os.getcwd()
    elif os.path.exists(cwd):
        sp.call(["mkdir", "-p", cwd])
    if add_open_prs:
        # Update base repo
        if not os.environ.get("SSH_KEY"):
            _logger.error("Missing SSH_KEY environment variable")
            sys.exit(1)
        ssh_cmd = """
            mkdir -p ~/.ssh
            echo -e "${SSH_KEY//_/\\n}" > ~/.ssh/id_rsa
            chmod og-rwx ~/.ssh/id_rsa 
            ssh-keyscan github.com >> ~/.ssh/known_hosts
        """
        sp.call(
            ssh_cmd,
            shell=True,
            executable="/bin/bash",
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )
        remotes = sp.check_output(["git", "remote", "-v"], cwd=cwd).splitlines()
        repo_url = remotes[0].decode().split("\t")[-1].split(" ")[0]
        # Convert https -> git+ssl
        repo_url = repo_url.replace("https://github.com/", "git@github.com:")
        tmp_repos_yaml = "/tmp/repos.yaml"
        sp.call(["touch", tmp_repos_yaml])
        obj = ToolsYaml(version, tmp_repos_yaml)
        obj.add_repo(".", repo_url)
        obj.update_repos(add_open_prs)
        obj.save()
        sp.call(["gitaggregate", "-c", tmp_repos_yaml], cwd=cwd)
    repos_yaml = os.path.join(cwd, config)
    obj = ToolsYaml(version, repos_yaml)
    obj.update_repos(add_open_prs)
    obj.print_limits()
    obj.save()
    if commit:
        if sp.call(["git", "diff", "--exit-code"], cwd=cwd):
            sp.call(["git", "add", config], cwd=cwd)
            sp.call(
                [
                    "git",
                    "commit",
                    "--no-verify",
                    "-m",
                    "[{}][UPD] {}".format(version, config),
                ],
                cwd=cwd,
            )


if __name__ == "__main__":
    tools()
