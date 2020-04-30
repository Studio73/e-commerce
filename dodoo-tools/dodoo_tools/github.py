#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
from getpass import getpass


class GithubAPI(object):
    def __init__(self, org, repo, username=False, password=False):
        self.org = org
        self.repo = repo
        self.username = username or os.environ.get("GH_USER")
        self.password = password or os.environ.get("GH_TOKEN")
        self.url = "https://api.github.com/repos/%s/%s" % (org, repo)

    def _build_url(self, endpoint, id=False, auth=False):
        available_endpoints = ["pulls", "keys"]
        if not endpoint in available_endpoints:
            print("Wrong endpoing: %s" % endpoint)
            sys.exit(-1)
        basic_auth = False
        if auth:
            if not self.username and not self.password:
                self.set_credentials()
            basic_auth = (self.username, self.password)
        url = "%s/%s" % (self.url, endpoint)
        if id:
            url += "/%s" % id
        return url, basic_auth

    def set_credentials(self, username=False, password=False):
        self.username = username or input("? Github username: ")
        self.password = password or getpass("? Github password: ")
        return True

    def get(self, endpoint, id=False, auth=False):
        url, basic_auth = self._build_url(endpoint, id, auth)
        return requests.get(url, auth=basic_auth)

    def post(self, endpoint, id=False, auth=False, **kwargs):
        url, basic_auth = self._build_url(endpoint, id, auth)
        return requests.post(url, auth=basic_auth, data=json.dumps(kwargs))

