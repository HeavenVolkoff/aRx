"""TransformerProtocol

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""


# Internal
import typing as T

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import (
    ObservableProtocol,
    ObservableProtocolWithOperators,
    add_operators as observable_add_operators,
)

# Generic Types
K = T.TypeVar("K", contravariant=True)
L = T.TypeVar("L", covariant=True)
M = T.TypeVar("M")
N = T.TypeVar("N")


@T.runtime_checkable
class TransformerProtocol(ObservableProtocol[L], ObserverProtocol[K], T.Protocol[K, L]):
    """Transformer abstract class.

    Base class for defining an object that is an Observer and Observable at the same time,
    in other words something through which data is inputted, transformed and outputted.
    """

    pass


@T.runtime_checkable
class TransformerProtocolWithOperators(
    TransformerProtocol[K, N], ObservableProtocolWithOperators[N], T.Protocol[K, N]
):
    pass


def add_operators(
    transformer: TransformerProtocol[M, N]
) -> TransformerProtocolWithOperators[M, N]:
    new = observable_add_operators(transformer)
    assert isinstance(new, TransformerProtocolWithOperators)
    return new


__all__ = ("TransformerProtocol", "TransformerProtocolWithOperators", "add_operators")
