"""Protocols Module

Here are defined abstract constructs that enable ease implementation of aRx's
definitions by leveraging python's duck typing system.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import ObservableProtocol
from .transformer_protocol import TransformerProtocol, TransformerProtocolWithOperators
