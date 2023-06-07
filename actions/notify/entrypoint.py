#!/usr/bin/env python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import os

import requests


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    url = f"{os.environ['INPUT_URL']}/mail/webhook/{os.environ['INPUT_TOKEN']}"
    headers = {"Content-Type": "application/json"}
    body = os.environ["INPUT_BODY"]
    body += f"""<br/>
    <a href='https://github.com/{repo}/actions/runs/{run_id}' target='_blank'>
        {repo}
    </a>
    """
    params = {
        "body": body,
        "channel_id": os.environ.get("INPUT_CHANNEL", 0),
    }
    r = requests.post(url, json={"params": params}, headers=headers)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        print(data)
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
