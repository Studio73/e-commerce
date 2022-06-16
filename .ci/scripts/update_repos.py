#!/usr/bin/env python3
import logging
import os
import re
import sys
from collections import OrderedDict

import requests
import yaml

AVAILABLE_VERSIONS = ["14.0", "15.0"]
AVAILABLE_ORGS = ["odoo", "oca", "all"]
GH_API = "https://api.github.com/repos/{org}/{repo}/{verb}/{nbr}"

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)
_logger = logging.getLogger(__name__)


def update_repos_yaml(version, org):
    headers = {}
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        _logger.error("Missing GITHUB_TOKEN environment variable")
        exit(255)
    headers = {"Authorization": "token {}".format(gh_token)}
    res_yaml = OrderedDict()
    dirname = os.path.dirname(__file__)
    repos_yaml = "{}/../../{}/{}.yaml".format(dirname, version, org)
    if not os.path.exists(repos_yaml):
        print("File not found: {}".format(repos_yaml))
        exit(255)
    with open(repos_yaml, "r") as stream:
        repos_loaded = yaml.safe_load(stream)
        for repo_name, repo_data in repos_loaded.items():
            _logger.info("[{}/{}]".format(version, repo_name))
            merges = []
            for merge in repo_data["merges"]:
                pr = re.findall("(?:refs/pull/)(\\d+)(?:/head)", merge)
                if pr:
                    # Pull request -> origin refs/pull/XXX/head
                    pr_url = GH_API.format(
                        org=org, repo=repo_name, verb="pulls", nbr=pr[0]
                    )
                    r = requests.get(pr_url, headers=headers)
                    r.raise_for_status()
                    gh_data = r.json()
                    pr_state = gh_data.get("state")
                    pr_merged = gh_data.get("merged")
                    if pr_state not in ["open", "closed"]:
                        _logger.error("{} not a valid value".format(pr_state))
                        exit(255)
                    if not isinstance(pr_merged, bool):
                        _logger.error("{} not a Boolean".format(pr_merged))
                        exit(255)
                    if pr_state == "closed":
                        if pr_merged:
                            action = "🔥"
                        else:
                            action = "⁉️"
                            merges.append(merge)
                    else:
                        action = "✅"
                        merges.append(merge)

                    _logger.info("* {}\t->\t{}".format(pr[0], action))
                else:
                    # Base commit -> origin latest_commit_sha
                    remote_name = merge.split()[0]
                    repo_url = GH_API.format(
                        org=org, repo=repo_name, verb="branches", nbr=version
                    )
                    r = requests.get(repo_url, headers=headers)
                    r.raise_for_status()
                    gh_data = r.json()
                    gh_commit = gh_data.get("commit")
                    if not isinstance(gh_commit, dict):
                        _logger.error("{} not a valid value".format(gh_commit))
                        _logger.error(gh_data)
                        exit(255)
                    new_sha = gh_commit.get("sha", "asdf")
                    if not re.findall("[0-9a-f]{5,40}", new_sha):
                        _logger.error("{} not a valid commit".format(gh_commit))
                        exit(255)
                    gh_commit_date = (
                        gh_commit.get("commit", {}).get("author", {}).get("date", "")
                    )
                    _logger.info(
                        "* commit\t->\t{}  #{}".format(new_sha, gh_commit_date)
                    )
                    merges.append("{} {}".format(remote_name, new_sha))
            repo_data["defaults"]["depth"] = 500 if len(merges) > 1 else 1
            repo_data["merges"] = merges
            res_yaml[repo_name] = repo_data
    with open(repos_yaml, "w") as yaml_file:
        yaml.dump(dict(res_yaml), yaml_file)
    return True


def main(version, org="all"):
    if org == "all":
        update_repos_yaml(version, "odoo")
        update_repos_yaml(version, "oca")
    else:
        update_repos_yaml(version, org)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in AVAILABLE_VERSIONS:
        main(sys.argv[1])
    elif (
        len(sys.argv) == 3
        and sys.argv[1] in AVAILABLE_VERSIONS
        and sys.argv[2] in AVAILABLE_ORGS
    ):
        main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: update_repos.py <ODOO_VERSION> <ORG>")
        print("ODOO_VERSION\t->\t%s" % " | ".join(AVAILABLE_VERSIONS))
        print("ORG <optional>\t->\t%s" % " | ".join(AVAILABLE_ORGS))
        exit(255)
