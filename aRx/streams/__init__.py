"""Streams Module

Streams are objects that combine a observers for data input with a observables
for data output. Their purpose is to act as path for data flow between a
diversity of other observables and observers.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Project
from .multi_stream import MultiStream
from .single_stream import SingleStream
