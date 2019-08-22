# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from ..stream import SingleStream
from ..abstract import Namespace


class Comparable(Te.Protocol):
    def __gt__(self, other: T.Any) -> bool:
        ...


# Generic Types
K = T.TypeVar("K", bound=Comparable)
_NOT_PROVIDED = object()


class Max(SingleStream[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)
        self._max: K = _NOT_PROVIDED  # type: ignore
        self._namespace: T.Optional[Namespace] = None

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._max != _NOT_PROVIDED:
            if not value > self._max:
                return

        self._max = value
        self._namespace = namespace

    async def __aclose__(self) -> None:
        if self._max != _NOT_PROVIDED:
            assert self._namespace is not None

            awaitable = super().__asend__(self._max, self._namespace)

            self._max = T.cast(K, _NOT_PROVIDED)
            self._namespace = None

            await awaitable

        await super().__aclose__()


__all__ = ("Max",)
