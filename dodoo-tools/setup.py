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
    install_requires=["click>=7"],
    entry_points={"console_scripts": ["dodoo-tools = dodoo_tools.cli:cli"]},
)
