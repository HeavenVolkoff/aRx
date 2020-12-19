"""Asynchronous Reactive Extensions

A library to make asynchronous reactive programming in python easy to use.

Its main purpose is to provide a framework for reactive programming built
following python's standard on top of asyncio module's constructs.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
from importlib.metadata import version

try:
    __version__: str = version(__name__)
except Exception:  # pragma: no cover
    # Internal
    import traceback
    from warnings import warn

    warn(f"Failed to set version due to:\n{traceback.format_exc()}", ImportWarning)
    __version__ = "0.0a0"

__all__ = ("__version__",)
