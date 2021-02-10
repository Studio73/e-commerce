#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="dodoo-tools",
    author="Studio73",
    author_email="contacto@studio73.es",
    url="https://www.studio73.es",
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        "click>=7",
        "coloredlogs",
        "future",
        "inquirer",
        "minio>=7.0.0;python_version>='3.6'",
        "minio==6.0.2;python_version<'3.6'",
        "tabulate",
    ],
    entry_points={"console_scripts": ["dodoo-tools = dodoo_tools.cli:cli"]},
)
