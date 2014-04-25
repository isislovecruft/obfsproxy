#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

import versioneer
versioneer.versionfile_source = 'obfsproxy/_version.py'
versioneer.versionfile_build = 'obfsproxy/_version.py'
versioneer.tag_prefix = 'obfsproxy-' # tags are like 1.2.0
versioneer.parentdir_prefix = 'obfsproxy-' # dirname like 'myproject-1.2.0'

setup(
    name = "obfsproxy",
    author = "asn",
    author_email = "asn@torproject.org",
    description = ("A pluggable transport proxy written in Python"),
    license = "BSD",
    keywords = ['tor', 'obfuscation', 'twisted'],

    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'obfsproxy = obfsproxy.pyobfsproxy:run'
            ]
        },

    install_requires = [
        'setuptools',
        'PyCrypto',
        'Twisted',
        'argparse',
        'pyptlib >= 0.0.6',
        'pyyaml'
        ],

    extras_require = {
        'SOCKS': ["txsocksx"]
        }
)
