#!/usr/bin/env python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import json
import logging
import os
import re
import subprocess as sp

import yaml

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)
_logger = logging.getLogger(__name__)


def main():
    merges = [
        f"origin refs/pull/{str(m)}/head"
        for m in json.loads(os.environ.get("INPUT_MERGES", "[]"))
    ]
    if not merges:
        _logger.info("No merges to aggregate")
        exit(0)
    remotes = sp.check_output(["git", "remote", "-v"]).splitlines()
    origin_data = re.findall(
        r"github.com[:|\/](?P<org>\w+)\/(?P<repo>[\w|-]+)", str(remotes[0])
    )
    if not origin_data:
        _logger.error("Unable to parse remote origin")
        exit(1)
    org, repo = origin_data[0]
    repo_url = f"git@github.com:{org}/{repo}"
    os.environ["HOME"] = "/home/runner"
    ssh_cmd = """
        echo -e "${INPUT_SSH_KEY//_/\\n}" > ~/.ssh/id_rsa
        chmod og-rwx ~/.ssh/id_rsa
    """
    sp.call(
        ssh_cmd,
        shell=True,
        executable="/bin/bash",
        stdout=sp.DEVNULL,
        stderr=sp.DEVNULL,
    )
    with open("/tmp/repos.yaml", "w") as stream:
        vals = {
            os.getcwd(): {
                "defaults": {"depth": 500},
                "merges": [f"origin {str(os.environ['GITHUB_REF_NAME'])}"] + merges,
                "remotes": {"origin": repo_url},
            }
        }
        yaml.dump(vals, stream)
    exitcode = sp.call(["gitaggregate", "-c", "/tmp/repos.yaml"])
    exit(exitcode)


if __name__ == "__main__":
    main()
