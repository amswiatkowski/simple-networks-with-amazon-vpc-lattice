#!/usr/bin/env python
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

setup(
    name='simple-networks-with-amazon-vpc-lattice',
    version='3.1',
    description='CDK code showing possibilities of Amazon VPC Lattice service',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.10',
    ],
    url='https://github.com/sz3jdii/simple-networks-with-amazon-vpc-lattice',
    author='Adam Świątkowski',
    author_email='adam.swiatkowski@iodi.pl',
    packages=find_packages(exclude=['tests']),
    package_data={'': ['*.json']},
    include_package_data=True,
    python_requires='>=3.10',
    install_requires=[],
)
