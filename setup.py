# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2023 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2023 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# https://pythonhosted.org/setuptools
# python setup.py --help-commands
# python setup.py build
# python setup.py sdist
# python setup.py bdist --format=rpm
# python setup.py --command-packages=stdeb.command bdist_deb (python-stdeb)

# http://zetcode.com/articles/packageinpython/
# TODO https://wiki.ubuntu.com/PackagingGuide/Python
# TODO https://help.ubuntu.com/community/PythonRecipes/DebianPackage

import sys

if not hasattr(sys, 'version_info') or sys.version_info < (3, 8, 0, 'final'):
    raise SystemExit('migasfree-backend requires Python 3.8 or later.')

import os

from setuptools import setup, find_packages
from distutils.command.install_data import install_data

PATH = os.path.dirname(__file__)
README = open(os.path.join(PATH, 'README.md'), encoding='utf_8').read()
VERSION = __import__('migasfree').__version__

REQUIRES = filter(
    lambda s: len(s) > 0,
    open(os.path.join(PATH, 'requirements', 'base.txt'), encoding='utf_8').read().split('\n')
)


class InstallData(install_data):
    @staticmethod
    def _find_pub_files():
        data_files = []

        for root, _, files in os.walk('pub'):
            if 'source' in root:
                continue  # exclude SVG files

            final_files = []
            for archive in files:
                final_files.append(os.path.join(root, archive))

            data_files.append(
                (
                    f'/var/{os.path.join("migasfree-backend", root)}',
                    final_files
                )
            )

        return data_files

    @staticmethod
    def _find_other_files():
        data_files = []

        for directory in ['packages']:
            for root, _, files in os.walk(directory):
                final_files = []
                for archive in files:
                    final_files.append(os.path.join(root, archive))

                data_files.append(
                    (
                        f'/usr/share/{os.path.join("migasfree-backend", root)}',
                        final_files
                    )
                )

        return data_files

    @staticmethod
    def _find_doc_files():
        data_files = []

        for root, _, files in os.walk('doc'):
            # first level does not matter
            if root == 'doc':
                continue

            final_files = []
            for archive in files:
                final_files.append(os.path.join(root, archive))

            # remove doc directory from root
            tmp_dir = root.replace('doc/', '', 1)

            data_files.append(
                (
                    f'/usr/share/doc/{os.path.join("migasfree-backend", tmp_dir)}',
                    final_files
                )
            )

        return data_files

    def run(self):
        # self.data_files.extend(self._find_pub_files())
        self.data_files.extend(self._find_other_files())
        self.data_files.extend(self._find_doc_files())
        install_data.run(self)


setup(
    name='migasfree-backend',
    version=VERSION,
    description='migasfree-backend is a Django app to manage systems management',
    long_description=README,
    license='GPLv3',
    author='Alberto Gacías, Jose Antonio Chavarría',
    author_email='alberto@migasfree.org, jachavar@gmail.com',
    url='http://www.migasfree.org/',
    platforms=['Linux'],
    install_requires=REQUIRES,
    packages=find_packages(),
    cmdclass={
        'install_data': InstallData,
    },
    package_data={
        'migasfree': [
            'i18n/*/LC_MESSAGES/*.mo',
            'app_catalog/fixtures/*',
            'core/fixtures/*',
            'client/fixtures/*',
            'device/fixtures/*',
            'stats/management/commands/*'
        ],
    },
    data_files=[
        ('/usr/share/doc/migasfree-backend', [
            'AUTHORS',
            'LICENSE',
            # 'INSTALL',  # TODO
            'MANIFEST.in',
            'README.md',
            'migasfree-backend.doap'
        ]),
    ],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
