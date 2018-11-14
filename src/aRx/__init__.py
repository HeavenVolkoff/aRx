"""Asynchronous Reactive eXtensions."""

__all__ = ("__version__",)

import pkg_resources

try:
    __version__ = str(pkg_resources.resource_string(__name__, "VERSION"), encoding="utf8")
except pkg_resources.ResolutionError:
    __version__ = "0.0a0"
