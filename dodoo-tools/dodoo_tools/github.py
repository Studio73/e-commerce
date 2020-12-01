#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
from builtins import input
from getpass import getpass


GITHUB_ENDPOINTS = {"pulls", "keys"}


class GithubAPI(object):
    def __init__(self, org, repo, token=None):
        self.org = org
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.url = "https://api.github.com/repos/%s/%s" % (org, repo)

    def _build_url(self, endpoint, id=None, auth=None):
        if not endpoint in GITHUB_ENDPOINTS:
            print("Wrong endpoing: %s" % endpoint)
            sys.exit(-1)
        url = "%s/%s" % (self.url, endpoint)
        if id:
            url += "/%s" % id
        headers = {}
        if auth:
            headers["Authorization"] = "token {}".format(self.token)
        return url, headers

    def set_credentials(self, token=None):
        if token:
            self.token = token
        elif not self.token:
            token = getpass("? Github token: ")
            self.token = token
        return True

    def get(self, endpoint, id=None, auth=None, **kwargs):
        url, headers = self._build_url(endpoint, id, auth)
        return requests.get(url, headers=headers)

    def post(self, endpoint, id=None, auth=None, **kwargs):
        url, headers = self._build_url(endpoint, id, auth)
        return requests.post(url, headers=headers, data=json.dumps(kwargs))

