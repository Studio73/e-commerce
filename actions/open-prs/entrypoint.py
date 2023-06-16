#!/usr/bin/env python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import logging
import json
import os
import re
import subprocess as sp
from pprint import pprint

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)
_logger = logging.getLogger(__name__)


def main():
    branch = str(os.environ["GITHUB_REF_NAME"])
    org, repo = os.environ["GITHUB_REPOSITORY"].split("/")
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
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"prs={json.dumps(prs)}")
    exit(0)


if __name__ == "__main__":
    main()
