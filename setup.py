# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro bro.devel+zfssnaps@gmail.com
#
# This file is part of zfssnaps and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

import zfssnaps

__plugin_name__ = "zfssnaps"
__author__ = "bendikro"
__author_email__ = "bro.devel+zfssnaps@gmail.com"
__version__ = zfssnaps.__version__
__url__ = "http://github.com/bendikro/zfssnaps"
__license__ = "GPLv3"
__description__ = "A simple CLI tool to handle snapshots in ZFS"
__long_description__ = """
"""

packages = find_packages()

entry_points = {
    'console_scripts': [
        'zfssnaps = zfssnaps.zfssnaps:main'
    ],
}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,
    packages=packages,
    install_requires=[
        'sh>=1.11',
        'humanfriendly>=2.4'
    ],
    entry_points=entry_points
)
