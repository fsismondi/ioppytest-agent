# Authors:
#     Federico Sismondi
#     Remy Leone

from __future__ import absolute_import
from setuptools import setup, find_packages
from version import __version__

name = 'ioppytest-agent'

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet',
    'Topic :: Software Development :: Testing',
    'Topic :: Scientific/Engineering',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: MacOS'
]

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name=name,
    author='Federico Sismondi',
    author_email='federicosismondi@gmail.com',
    maintainer='Federico Sismondi',
    maintainer_email='federicosismondi@gmail.com',
    url='https://github.com/fsismondi/ioppytest-agent',
    description='Component for creating VPN client environments',
    version=__version__,
    license='GPLv3+',
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['tests']),
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'click',
        'six',
        'kombu',
        'pika',
        'pyserial',
    ],
    data_files=[("", ["README.md", "USAGE.md", "FAQ.md", "INSTALL.md", "LICENSE", "version.py"])],
    entry_points={'console_scripts': ['ioppytest-agent=agent.agent_cli:main']},
)
