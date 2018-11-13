#!/usr/bin/env python3

# Internal
from configparser import ConfigParser
import os
import re
import shlex  # python>=3.3
import sys


def main():
    """Exec setup"""
    from setuptools import setup, find_namespace_packages

    setup(packages=find_namespace_packages("src"), package_dir={"": "src"})


try:
    import pkg_resources
except ImportError:
    raise RuntimeError(
        "The setuptools package is missing or broken. To (re)install it run:\n"
        "{} -m pip install -U setuptools",
        sys.executable,
    )


def has_requirement(req):
    try:
        pkg_resources.require(req)
    except pkg_resources.ResolutionError:
        return False
    else:
        return True


if os.path.isfile("setup.cfg"):
    # Read setup.cfg as a simple config file
    setup_config = ConfigParser()
    setup_config.read("setup.cfg", encoding="utf8")  # python>=3.2
    # Filter out the setup-requires key
    setup_requires = tuple(
        filter(
            lambda req: bool(req) and not has_requirement(req),
            re.split(
                r"\s*(?:\n+|;(?!;))\s*", setup_config.get("options", "setup-requires", fallback="")
            ),
        )
    )

    if setup_requires:
        raise RuntimeError(
            "Missing dependencies for installing {}. To proceed run:\n{} -m pip install {}".format(
                setup_config.get("metadata", "name", fallback="this package"),
                sys.executable,
                " ".join(map(shlex.quote, setup_requires)),
            )
        )

main()
