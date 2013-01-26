#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

setup(
    name = "pyobfsproxy",
    version = "0.0.1",
    author = "asn",
    author_email = "asn@torproject.org",
    description = ("A pluggable transport proxy written in Python"),
    license = "BSD",
    keywords = ['tor', 'obfuscation', 'twisted'],

    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'pyobfsproxy = obfsproxy.pyobfsproxy:run'
            ]
        },
)
