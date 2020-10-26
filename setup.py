# -*- coding: utf-8 -*-
'''
Copyright (C) 2014  walker li <walker8088@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os

from pathlib import Path 
from warnings import warn

from setuptools import find_packages

try:
    # use setuptools namespace, allows for "develop"
    import setuptools  # noqa, analysis:ignore
except ImportError:
    warn("unable to load setuptools. 'setup.py develop' will not work")
    pass  # it's not essential for installation
#from distutils.core import setup
from setuptools import setup, Extension

# Get version and docstring
__version__ = None
__doc__ = ''
name = 'cchess'
description = 'ChineseChess library'
with open("README.md", "r", encoding='utf-8') as fh:
    __doc__ = fh.read()
    
initFile = Path(os.path.dirname(__file__), 'cchess', '__init__.py')
for line in open(initFile).readlines():
    if (line.startswith('version_info') or line.startswith('__version__')):
        exec(line.strip())
    
def package_tree(pkgroot):
    path = os.path.dirname(__file__)
    subdirs = [os.path.relpath(i[0], path).replace(os.path.sep, '.')
               for i in os.walk(Path(path, pkgroot))
               if '__init__.py' in i[2]]
    return subdirs

setup(
    name=name,
    version=__version__,
    author='Walker Li',
    author_email='walker8088@gmail.com',
    license='GPL-3.0',
    url='https://github.com/walker8088/cchess',
    #download_url='https://pypi.python.org/pypi/cchess',
    keywords="ChineseChess xiang_qi xiangqi",
    description=description,
    long_description=__doc__,
    platforms='Windows, Linux',
    provides=['walker8088'],
    setup_requires=[
        'pytest-runner',
    ],
    #install_requires=[
    #    'pygame',
    #],
    extras_require={   },
    packages=find_packages(),
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ],
)
