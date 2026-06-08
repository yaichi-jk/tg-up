#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Upload (and download) files to Telegram up to 4 GiB using your account.
"""
import copy
import os
import glob
from itertools import chain
from setuptools import setup, find_packages

AUTHOR = "yaichi-jk"
EMAIL = ''
URL = 'https://github.com/yaichi-jk/tg-up/'

PACKAGE_NAME = 'yaichi-tg'
PACKAGE_DOWNLOAD_URL = 'https://github.com/yaichi-jk/tg-up/archive/main.zip'
MODULE = 'tg_up'
REQUIREMENT_FILE = 'requirements.txt'
STATUS_LEVEL = 4  # 1:Planning 2:Pre-Alpha 3:Alpha 4:Beta 5:Production/Stable 6:Mature 7:Inactive
KEYWORDS = ['tg-up', 'telegram', 'upload', 'video', 'tg-dw']
LICENSE = 'MIT license'

CLASSIFIERS = [
    'License :: OSI Approved :: MIT License',
]
NATURAL_LANGUAGE = 'English'

PLATFORMS = [
    'linux',
]
PYTHON_VERSIONS = ['3.9', '3.10', '3.11', '3.12', '3.13']


def read_requirement_file(path):
    with open(path) as f:
        return f.readlines()


def get_package_version(module_name):
    return __import__(module_name).__version__


def get_packages(directory):
    packages_list = find_packages(directory)
    for package in tuple(packages_list):
        path = os.path.join(directory, package.replace('.', '/'))
        if not os.path.exists(path) or os.path.islink(path):
            packages_list.remove(package)
    return packages_list


def get_python_versions(string_range):
    if '-' not in string_range:
        return [string_range]
    return ['{0:.1f}'.format(version * 0.1) for version
            in range(*[int(x * 10) + (1 * i) for i, x in enumerate(map(float, string_range.split('-')))])]


def get_python_classifiers(versions):
    for version in range(2, 4):
        if not next(iter(filter(lambda x: int(float(x)) != version, versions.copy())), False):
            versions.add('{} :: Only'.format(version))
            break
    return ['Programming Language :: Python :: %s' % version for version in versions]


def get_platform_classifiers(platform):
    parts = {
        'linux': ('POSIX', 'Linux'),
        'win': ('Microsoft', 'Windows'),
        'solaris': ('POSIX', 'SunOS/Solaris'),
        'aix': ('POSIX', 'Linux'),
        'unix': ('Unix',),
        'bsd': ('POSIX', 'BSD')
    }[platform]
    return ['Operating System :: {}'.format(' :: '.join(parts[:i+1]))
            for i in range(len(parts))]


here = os.path.abspath(os.path.dirname(__file__))
readme = glob.glob('{}/{}*'.format(here, 'README'))[0]
scripts = [os.path.join('scripts', os.path.basename(script)) for script in glob.glob('{}/scripts/*'.format(here))]

packages = get_packages(here)
modules = list(filter(lambda x: '.' not in x, packages))
module = MODULE if MODULE else modules[0]
python_versions = set(chain(*[get_python_versions(versions) for versions in PYTHON_VERSIONS])) - {2.8, 2.9}
status_name = ['Planning', 'Pre-Alpha', 'Alpha', 'Beta',
               'Production/Stable', 'Mature', 'Inactive'][STATUS_LEVEL - 1]

classifiers = copy.copy(CLASSIFIERS)
classifiers.extend(get_python_classifiers(python_versions))
classifiers.extend(chain(*[get_platform_classifiers(platform) for platform in PLATFORMS]))
classifiers.extend([
    'Natural Language :: {}'.format(NATURAL_LANGUAGE),
    'Development Status :: {} - {}'.format(STATUS_LEVEL, status_name),
])


setup(
    name=PACKAGE_NAME,
    version=get_package_version(module),
    packages=packages,
    provides=modules,
    scripts=scripts,
    include_package_data=True,

    description=__doc__.replace('\n', ' '),
    long_description=open(readme, 'r').read(),
    keywords=KEYWORDS,
    download_url=PACKAGE_DOWNLOAD_URL,

    author=AUTHOR,
    author_email=EMAIL,
    url=URL,

    classifiers=classifiers,
    platforms=PLATFORMS,

    install_requires=read_requirement_file(REQUIREMENT_FILE),

    entry_points={
        "console_scripts": [
            "tg-up = tg_up.management:upload_cli",
            "tg-dw = tg_up.management:download_cli",
        ],
    },

    zip_safe=False,
)
