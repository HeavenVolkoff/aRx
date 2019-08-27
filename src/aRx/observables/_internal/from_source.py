# Internal
import typing as T
from abc import abstractmethod
from asyncio import CancelledError
from contextlib import suppress

# External
from async_tools import get_running_loop
from async_tools.abstract import AsyncABCMeta

# Project
from ...namespace import Namespace
from ..observable import Observable

if T.TYPE_CHECKING:
    # Internal
    from asyncio import Task

    # Project
    from ...protocols import ObserverProtocol


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class FromSource(T.Generic[K, L], Observable[K], metaclass=AsyncABCMeta):
    __slots__ = ("_task", "_source", "_observer", "_namespace")

    def __init__(self, source: L, **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        # Project
        super().__init__(**kwargs)  # type: ignore

        # Internal
        self._task: T.Optional["Task[None]"] = None
        self._source: L = source
        self._observer: T.Optional["ObserverProtocol[K]"] = None
        self._namespace = Namespace(self, "_worker")

    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        if self._task is not None:
            raise RuntimeError("Iterator is already in use")

        self._task = get_running_loop().create_task(self._worker())
        self._observer = observer

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        if self._observer is not observer:
            return

        if self._task:
            if self._task.cancelled():
                self._task.result()  # raise CancelledError
            self._task.cancel()

            with suppress(CancelledError, Exception):
                await self._task

        self._task = None
        self._observer = None

    @abstractmethod
    async def _worker(self) -> None:
        raise NotImplementedError
