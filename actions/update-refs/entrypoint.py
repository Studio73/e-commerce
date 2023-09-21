#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import logging
import os
import re
import sys
from collections import OrderedDict
from pprint import pprint

import requests
import yaml
from plumbum import local

AVAILABLE_VERSIONS = ["9.0", "10.0", "11.0", "12.0", "13.0", "14.0", "15.0", "16.0"]
AVAILABLE_ORGS = ["odoo", "oca", "openupgrade"]
git = local["git"]

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
            _logger.info("Nothing to do, file not found: {}".format(repos_yaml))
            sys.exit(0)
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
            _logger.error(pprint(data))
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

    def update_repos(self):
        res_yaml = OrderedDict()
        for name, data in self.yaml.items():
            origin = data.get("remotes", {}).get("origin")
            origin_data = re.findall(
                r"github.com[:|\/](?P<org>\w+)\/(?P<repo>[\w|-]+)", origin
            )
            if not origin_data:
                _logger.error("Unable to parse remote origin")
                exit(1)
            org, repo = origin_data[0]
            _logger.info("[{}/{}]".format(self.version, repo))
            merges = []
            for merge in data["merges"]:
                pr = re.findall("(?:refs/pull/)(\\d+)(?:/head)", merge)
                if pr:
                    # Pull request -> origin refs/pull/XXX/head
                    if self.is_pr_open(org, repo, pr[0]):
                        merges.append(merge)
                else:
                    # Update commit sha to latest version
                    # Base commit -> origin latest_commit_sha
                    remote_name = merge.split()[0]
                    new_sha = self.get_latest_sha(org, repo, self.version)
                    merges.append("{} {}".format(remote_name, new_sha))
            old_depth = data["defaults"]["depth"]
            new_depth = old_depth
            if len(merges) > 1:
                new_depth = 500
            elif old_depth == 500:
                new_depth = 1
            data["defaults"]["depth"] = new_depth
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


def commit():
    git[
        "config",
        "--global",
        "user.email",
        "113453776+leonidas73[bot]@users.noreply.github.com",
    ]()
    git["config", "--global", "user.name", "leonidas73[bot]"](
        stdout=sys.stdout, stderr=sys.stderr
    )
    git["config", "--global", "--add", "safe.directory", "/github/workspace"](
        stdout=sys.stdout, stderr=sys.stderr
    )
    git["status", "--porcelain"](stdout=sys.stdout, stderr=sys.stderr)
    git["add", "."](stdout=sys.stdout, stderr=sys.stderr)
    git["commit", "-m", "feat(odoo): Update repos refs"](
        stdout=sys.stdout, stderr=sys.stderr
    )
    git["push", "origin", "master"](stdout=sys.stdout, stderr=sys.stderr)


def main():
    for version in AVAILABLE_VERSIONS:
        for org in AVAILABLE_ORGS:
            repos_yaml = f"odoo/{version}/{org}.yaml"
            obj = ToolsYaml(version, repos_yaml)
            obj.update_repos()
            obj.print_limits()
            obj.save()
    commit()


if __name__ == "__main__":
    main()
