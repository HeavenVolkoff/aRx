# Internal
import typing as T
from abc import abstractmethod
from asyncio import Task, wait

# External
from async_tools import get_running_loop
from async_tools.abstract import AsyncABCMeta

# Project
from ..namespace import get_namespace
from ..protocols import ObserverProtocol, ObservableProtocol

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class _FromAsyncBase(T.Generic[K, L], ObservableProtocol[K], metaclass=AsyncABCMeta):
    def __init__(self, **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

        # Internal
        self._task: T.Optional["Task[None]"] = None
        self._namespace = get_namespace(self, "anext")
        self._iterator: T.Optional[L] = None

    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        """Schedule async iterator flush and register observers."""

        if not self._iterator:
            raise RuntimeError("Iterator was already used")

        self._task = get_running_loop().create_task(self._worker(self._iterator, observer))

        # Clear reference to prevent reiterations
        self._iterator = None

    async def __dispose__(self, _: ObserverProtocol[K]) -> None:
        if self._task:
            self._task.cancel()
            await wait((self._task,))
            self._task = None

    @abstractmethod
    async def _worker(self, async_iterator: L, observer: ObserverProtocol[K]) -> None:
        raise NotImplementedError
