"""Observers Module

Holds the definition of the concrete Observer class together with some common
used custom ones.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Project
from .consumer import Consumer
from .observer import Observer
from .iterator_observer import IteratorObserver
from .anonymous_observer import AnonymousObserver

__all__ = ("Observer", "Consumer", "AnonymousObserver", "IteratorObserver")
