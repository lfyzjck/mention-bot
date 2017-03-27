#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import find_packages, setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()
history = open('CHANGELOG.md').read().replace('.. :changelog:', '')

setup(
    name='mention',
    version='0.0.1',
    description='mention-bot for gitlab',
    long_description=readme + '\n\n' + history,
    author='lfyzjck',
    author_email='jickimkim@gmail.com',
    url='https://github.com/lfyzjck/mention-bot.git',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Testing',
        'requests',
        'pyapi-gitlab'
    ],
    license="Private",
    zip_safe=False,
    keywords='pier',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'mention_bot = mention.app:main'
            ]
        },
)
