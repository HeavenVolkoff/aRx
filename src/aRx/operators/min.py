# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from ..streams import SingleStream
from ..namespace import Namespace

# Generic Types
K = T.TypeVar("K")


class Comparable(Te.Protocol):
    def __lt__(self: K, other: K) -> bool:
        ...


M = T.TypeVar("M", bound=Comparable)
_NOT_PROVIDED: Te.Final = object()


class Min(SingleStream[M]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)
        self._min: M = _NOT_PROVIDED  # type: ignore
        self._namespace: T.Optional[Namespace] = None

    async def _asend(self, value: M, namespace: Namespace) -> None:
        if self._min != _NOT_PROVIDED:
            if not value < self._min:
                return

        self._min = value
        self._namespace = namespace

    async def _aclose(self) -> None:
        if self._min != _NOT_PROVIDED:
            assert self._namespace is not None

            awaitable = super()._asend(self._min, self._namespace)

            self._min = _NOT_PROVIDED  # type: ignore
            self._namespace = None

            await awaitable

        await super()._aclose()


__all__ = ("Min",)