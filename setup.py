#!/usr/bin/env python3

from os import path
from codecs import open as c_open

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup, find_packages

# Get __version__ data
here = str(path.abspath(path.dirname(__file__)))
about = {}
with c_open(path.join(here, "aRx", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

# Get README text
with c_open(path.join(here, "README.md"), "r", "utf-8") as readme_file:
    readme = readme_file.read()

setup(
    url=about["__url__"],
    name=about["__title__"],
    author=about["__authors__"],
    version=about["__version__"],
    license=about["__license__"],
    keywords="aRx, reactive, async, asyncio, promise, observer, observable",
    zip_safe=True,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    maintainer=about["__maintainer__"],
    description=about["__description__"],
    author_email=about["__email__"],
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    extras_require={':python_version<"3.7"': ["async-exit-stack"]},
    tests_require=["pytest", "pytest-asyncio"],
    setup_requires=["pytest-runner"],
    python_requires=">=3.6",
    maintainer_email=about["__maintainer_email__"],
    long_description=readme,
)
