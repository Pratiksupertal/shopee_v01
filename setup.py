# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in shopee_v01/__init__.py
from shopee_v01 import __version__ as version

setup(
	name='shopee_v01',
	version=version,
	description='Authentication App',
	author='Pratik Mane',
	author_email='pratik@supertal.io',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
