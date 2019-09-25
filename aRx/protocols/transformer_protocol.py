"""TransformerProtocol

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""


# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import ObservableProtocol

if T.TYPE_CHECKING:
    from ..operations import sink, pipe

# Generic Types
K = T.TypeVar("K", contravariant=True)
L = T.TypeVar("L", covariant=True)
M = T.TypeVar("M")
N = T.TypeVar("N")


@Te.runtime
class TransformerProtocol(ObservableProtocol[L], ObserverProtocol[K], Te.Protocol[K, L]):
    """Transformer abstract class.

    Base class for defining an object that is an Observer and Observable at the same time,
    in other words something through which data is inputted, transformed and outputted.
    """

    pass


@Te.runtime
class TransformerProtocolWithOperators(TransformerProtocol[K, N], Te.Protocol[K, N]):
    """Transformer abstract class.

    Base class for defining an object that is an Observer and Observable at the same time,
    in other words something through which data is inputted, transformed and outputted.
    """

    def __gt__(self, observer: ObserverProtocol[N]) -> "sink[N]":
        ...

    def __or__(self, transformer: TransformerProtocol[N, M]) -> "pipe[N, M]":
        ...


def add_operators(
    transformer: TransformerProtocol[M, N]
) -> TransformerProtocolWithOperators[M, N]:
    from copy import copy
    from ..observables import Observable
    from types import MethodType

    if isinstance(transformer, TransformerProtocolWithOperators):
        return transformer
    else:
        # Don't change the original object
        new = copy(transformer)

        # Warning:
        #   This should implement all the operators defined in TransformerProtocolWithOperators
        new.__gt__ = MethodType(Observable.__gt__, new)  # type: ignore
        new.__or__ = MethodType(Observable.__or__, new)  # type: ignore

        assert isinstance(new, TransformerProtocolWithOperators)

        return new


__all__ = ("TransformerProtocol", "TransformerProtocolWithOperators", "add_operators")
