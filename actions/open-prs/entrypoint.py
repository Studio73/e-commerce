#!/usr/bin/env python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import json
import logging
import os
import re
from collections import OrderedDict
from pprint import pprint

import requests
import yaml

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)
_logger = logging.getLogger(__name__)


def get_prs(org, repo, branch):
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
                                        contexts(first: 10) {
                                            nodes {
                                                __typename
                                                ... on CheckRun{
                                                    name
                                                    conclusion
                                                }
                                                __typename
                                                ... on StatusContext{
                                                    description
                                                    state
                                                    context
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    headers = {
        "Authorization": f"token {os.environ['INPUT_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {
        "query": query,
        "variables": {"owner": org, "repo": repo, "branch": branch},
    }
    r = requests.post("https://api.github.com/graphql", json=params, headers=headers)
    r.raise_for_status()
    data = r.json()
    if not data.get("data"):
        _logger.error("Github query error:")
        pprint(data)
        exit(1)
    data = data["data"]
    prs = []
    open_prs = data["repository"]["pullRequests"]["nodes"]
    if len(open_prs):
        _logger.info("[Open PRS]")
    for pr in open_prs:
        tag = pr["number"]
        title = pr.get("title", "").lower()
        if "[force dev]" in title or "[dev force]" in title:
            _logger.info("✅ {}\t->\tTitle contains [force dev]".format(tag))
            prs.append(str(pr["number"]))
            continue
        if "[skip dev]" in title or "[dev skip]" in title:
            _logger.info("❌ {}\t->\tTitle contains [skip dev]".format(tag))
            continue
        if pr.get("isDraft"):
            _logger.info("❌ {}\t->\tDraft PR".format(tag))
            continue
        if pr.get("mergeable") == "CONFLICTING":
            _logger.info("❌ {}\t->\tPR with conflicts".format(tag))
            continue
        status_check_rollup = (
            pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"] or {}
        )
        checks_passed = []
        checks = []
        for context in status_check_rollup.get("contexts", {}).get("nodes") or []:
            if context["__typename"] == "CheckRun":  # Github Actions
                if "concourse" in context["name"]:  # Ignore everything from concourse
                    continue
                if context["conclusion"] == "SUCCESS":
                    checks_passed.append(True)
                else:
                    checks_passed.append(False)
                checks.append(f"\t- {context['name']}\t{context['conclusion']}")
            elif context["__typename"] == "StatusContext":  # Other checks
                if context["state"] == "SUCCESS" or context["context"] == "functional":
                    checks_passed.append(True)
                else:
                    checks_passed.append(False)
                checks.append(f"\t- {context['context']}\t{context['state']}")
        if all(checks_passed):
            _logger.info("✅ {}\t->\tMergeable PR".format(tag))
            prs.append(str(pr["number"]))
        else:
            _logger.info("❌ {}\t->\tCI status check FAILED".format(tag))
        for check in checks:
            _logger.info(check)
    return prs


def update_config(config_file, branch):
    with open(config_file, "r") as stream:
        config_yaml = yaml.safe_load(stream) or {}
    res_yaml = OrderedDict()
    for name, data in config_yaml.items():
        origin = data.get("remotes", {}).get("origin")
        origin_data = re.findall(
            r"github.com[:|\/](?P<org>\w+)\/(?P<repo>[\w|-]+)", origin
        )
        if not origin_data:
            _logger.error("Unable to parse remote origin")
            exit(1)
        org, repo = origin_data[0]
        _logger.info(f"[{branch}/{repo}]")
        prs = get_prs(org, repo, branch)
        if len(prs):
            data["defaults"]["depth"] = 500
            for pr in sorted(prs):
                data["merges"].append(f"origin refs/pull/{pr}/head")
        res_yaml[name] = data
    with open(config_file, "w") as stream:
        yaml.dump(dict(res_yaml), stream)


def main():
    branch = str(os.environ.get("INPUT_BRANCH", os.environ.get("GITHUB_REF_NAME")))
    config_file = os.environ.get("INPUT_FILE")
    if config_file:
        update_config(config_file, branch)
        prs = []
    else:
        org, repo = os.environ["GITHUB_REPOSITORY"].split("/")
        prs = get_prs(org, repo, branch)
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"prs={json.dumps(prs)}")
    exit(0)


if __name__ == "__main__":
    main()
