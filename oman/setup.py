#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name='oman',
    license="AGPLv3+",
    author='Consultoria Informatica Studio73 S.L',
    author_email='contacto@studio73.es',
    url='https://www.studio73.es',
    packages=[
        'oman',
    ],
    entry_points=dict(
        console_scripts=['oman=oman.main:main']
    ),
)