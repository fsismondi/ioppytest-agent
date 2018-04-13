# Author:
#     Federico Sismondi <federicosismondi@gmail.com>

from __future__ import absolute_import

import io
from setuptools import setup, find_packages

MAJOR = 0
MINOR = 1
PATCH = 2
VERSION = "{}.{}.{}".format(MAJOR, MINOR, PATCH)

name = 'ioppytest-agent'

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Intended Audience :: Testers",
    # "License :: OSI Approved :: BSD License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Topic :: Networks",
    "Topic :: Interoperability testing",
    "Topic :: Scientific/Engineering",
    # "Operating System :: Microsoft :: Windows", not there yet..
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Operating System :: MacOS"
]

with open("version.py", "w") as f:
    f.write("__version__ = '{}'\n".format(VERSION))

setup(
    name=name,
    author='Federico Sismondi',
    author_email="federicosismondi@gmail.com",
    description="Component for setting up user's environment for the tests",
    version=VERSION,
    license='GPLv3+',
    classifiers=CLASSIFIERS,
    packages=['agent'],
    long_description=io.open('README.md', 'r', encoding='utf-8').read(),
    install_requires=[
        'click',
        'six',
        'kombu',
        'pika',
        'pyserial',
    ],
    entry_points={'console_scripts': ['ioppytest-agent=agent.agent_cli:main']},
)

