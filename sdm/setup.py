"""
Data Extraction Tool for BoM Statistical Downscaling Model.
"""

import os
import sys

from setuptools import setup

BASE_DIR = os.path.dirname(__file__)


def read(filename):
    with open(os.path.join(BASE_DIR, filename)) as f:
        return f.read()


def get_requirements():
    lines = read('requirements.txt').splitlines()
    # argparse is part of stdlib for version 2.7+
    if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
        lines.append('argparse>=1.1')
    return lines


setup(name='sdm',
      version='0.1.0',
      description='data extraction tool for BoM SDM',
      long_description=__doc__,
      author='Yang Wang',
      author_email='y.wang@bom.gov.au',
      platforms='any',
      packages=['sdm'],
      install_requires=get_requirements(),
      scripts=['sdmrun.py'],
)
