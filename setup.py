#!/usr/bin/env python

import sys

sys.path.insert(0, 'src')

from setuptools import setup

setup(name='pyptlib',
      version='0.1',
      description='A python implementation of the Pluggable Transports for Circumvention specification for Tor',
      long_description='A python implementation of the Pluggable Transports for Circumvention specification for Tor',
      author='Brandon Wiley',
      author_email='brandon@blanu.net',
      url='http://stepthreeprivacy.org/',
      classifiers=[
	"Development Status :: 3 - Alpha",
    	"Environment :: No Input/Output (Daemon)",
    	"License :: OSI Approved :: BSD License",
    	"Programming Language :: Python",
    	"Intended Audience :: Developers",
    	"Operating System :: OS Independent",
    	"Topic :: Internet",
    	"Topic :: Security :: Cryptography",
    	"Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='cryptography privacy internet',
      license='BSD',
      package_dir={'pyptlib': 'src/pyptlib'},
      packages=['pyptlib'],
     )
