#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Studio73 <https://www.studio73.es>
import logging

import click
import coloredlogs

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO,
)
coloredlogs.install(level=logging.INFO)


@click.group()
def cli():
    pass


# Test: python3 -c "import dodoo_tools; dodoo_tools.cli.cli()"
