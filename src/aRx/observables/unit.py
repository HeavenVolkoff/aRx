# Internal
import typing as T
from asyncio import Task, wait, isfuture, ensure_future

# External
from async_tools import get_running_loop

# Project
from ..namespace import Namespace, get_namespace
from ..protocols import ObserverProtocol, ObservableProtocol

__all__ = ("Unit",)


# Generic Types
K = T.TypeVar("K")


class Unit(ObservableProtocol[K]):
    """Observable that outputs a single value then closes."""

    @staticmethod
    async def _worker(
        value: T.Union[K, T.Awaitable[K]], observer: ObserverProtocol[K], namespace: Namespace
    ) -> None:
        if isfuture(value):
            try:
                value = await T.cast(T.Awaitable[K], value)
            except Exception as ex:
                await observer.athrow(ex, namespace)
            else:
                await observer.asend(value)
        else:
            await observer.asend(T.cast(K, value))

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, value: T.Union[K, T.Awaitable[K]], **kwargs: T.Any) -> None:
        """Unit constructor

        Arguments:
            value: Value to be outputted by observables.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)  # type: ignore

        # Internal
        try:
            self._value: T.Union[K, T.Awaitable[K]] = ensure_future(T.cast(T.Awaitable[K], value))
        except TypeError:
            self._value = value

        self._task: T.Optional["Task[None]"] = None
        self._namespace = get_namespace(self, "fixed")

    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        # Add worker execution to loop queue
        self._task = get_running_loop().create_task(
            Unit._worker(self._value, observer, self._namespace)
        )

    async def __dispose__(self, observer: ObserverProtocol[K]) -> None:
        if self._task:
            self._task.cancel()
            await wait((self._task,))
            self._task = None
