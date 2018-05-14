#!/usr/bin/env python3

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    url='https://github.com/HeavenVolkoff/areact',
    name='areact',
    author='Børge Lanes, Dag Brattli, Vítor Augusto da Silva Vasconcellos',
    version='0.6.0rc1',
    license='Mozilla Public License 2.0 (MPL 2.0)',
    zip_safe=True,
    maintainer='Vítor Augusto da Silva Vasconcellos',
    description='Async/await Reactive Tools for Python 3.6+',
    author_email='"Dag Brattli" <dag@brattli.net>, '
                 '"Vítor Augusto da Silva Vasconcellos" '
                 '<vasconcellos.dev@gmail.com>',
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    package_dir={'areact': 'areact'},
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta', 'Environment :: Other Environment',
        'Intended Audience :: Developers', 'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)'
    ],
    maintainer_email='"Vítor Augusto da Silva Vasconcellos" '
                     '<vasconcellos.dev@gmail.com>',
    tests_require=['pytest', "pytest-asyncio"],
    setup_requires=['pytest-runner'],
    long_description="areact is a library for asynchronous and reactive "
                     "programming using asyncio, async and await",
)
