"""ObservableProtocol

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# External
import typing_extensions as Te

if T.TYPE_CHECKING:
    # Project
    from ..operations import sink, pipe
    from .observer_protocol import ObserverProtocol
    from .transformer_protocol import TransformerProtocol


# Generic Types
K = T.TypeVar("K", covariant=True)
L = T.TypeVar("L")
M = T.TypeVar("M")


class ObservableProtocol(Te.Protocol[K]):
    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        ...

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        ...


@Te.runtime
class ObservableProtocolWithOperators(ObservableProtocol[L], Te.Protocol[L]):
    def __gt__(self, observer: "ObserverProtocol[L]") -> "sink[L]":
        ...

    def __or__(self, transformer: "TransformerProtocol[L, M]") -> "pipe[L, M]":
        ...


def add_operators(transformer: ObservableProtocol[L]) -> ObservableProtocolWithOperators[L]:
    from copy import copy
    from ..observables import Observable
    from types import MethodType

    if isinstance(transformer, ObservableProtocolWithOperators):
        return transformer
    else:
        # Don't change the original object
        new = copy(transformer)

        # Warning:
        #   This should implement all the operators defined in TransformerProtocolWithOperators
        new.__gt__ = MethodType(Observable.__gt__, new)  # type: ignore
        new.__or__ = MethodType(Observable.__or__, new)  # type: ignore

        assert isinstance(new, ObservableProtocolWithOperators)

        return new


__all__ = ("ObservableProtocol", "ObservableProtocolWithOperators", "add_operators")
