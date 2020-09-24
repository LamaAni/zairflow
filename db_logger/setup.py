#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    setup.py
    ~~~~~~~~

    no description available

    :copyright: (c) 2020 by zav.
    :license: see LICENSE for more details.
"""

import codecs
import os
import re
from setuptools import setup

setup(
    name="airflow_db_logger",
    version="0.1.1",
    description="Airflow DB logger",
    long_description="An internal package to allow airflow db logs to be written/read to/from the airflow database",
    classifiers=[],
    author="zav",
    author_email="",
    url="",
    packages=["airflow_db_logger"],
    platforms="any",
    license="LICENSE",
    install_requires=[],
)
