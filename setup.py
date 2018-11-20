#!/usr/bin/env python3

# Internal
import sys
import shlex  # python>=3.3
from os import path, scandir

SETUP_CONFIG = "setup.cfg"
VERSION_FILE = "VERSION"
SOURCE_LOCATION = "src"


def main():
    """Exec setup"""
    from setuptools import setup, find_namespace_packages
    from distutils.errors import DistutilsOptionError

    try:
        setup(packages=find_namespace_packages("src"), package_dir={"": "src"})
    except DistutilsOptionError:
        raise RuntimeError(
            "Maybe the setuptools package is too old. To update it run:\n"
            "{} -m pip install -U setuptools",
            sys.executable,
        )


try:
    import pkg_resources
except ImportError:
    raise RuntimeError(
        "The setuptools package is missing or broken. To (re)install it run:\n"
        "{} -m pip install -U setuptools".format(sys.executable)
    )


def has_requirement(req):
    try:
        pkg_resources.require(req)
    except pkg_resources.ResolutionError:
        return False
    else:
        return True


if path.isfile(SETUP_CONFIG):
    # Read setup configuration
    from setuptools.config import read_configuration

    config = read_configuration(SETUP_CONFIG)
    options = config.get("options", {})
    metadata = config.get("metadata", {})
    setup_requires = tuple(
        filter(lambda req: not has_requirement(req), options.get("setup_requires", []))
    )

    if setup_requires:
        raise RuntimeError(
            "Missing dependencies for installing {}. To proceed run:\n{} -m pip install {}".format(
                metadata.get("name", "this package"),
                sys.executable,
                " ".join(map(shlex.quote, setup_requires)),
            )
        )

    version = metadata.get("version", None)
    if version:
        with scandir(SOURCE_LOCATION) as src:
            for module in src:
                if module.is_dir() and path.isfile(path.join(module.path, "__init__.py")):
                    with open(path.join(module.path, VERSION_FILE), mode="w") as file:
                        file.write(version)
main()
