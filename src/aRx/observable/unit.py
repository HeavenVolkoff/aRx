__all__ = ("Unit",)

# Internal
import typing as T
from asyncio import isfuture, ensure_future

# External
from async_tools.abstract.loopable import Loopable

# Project
from ..misc.namespace import Namespace, get_namespace
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable

# Generic Types
K = T.TypeVar("K")


class Unit(Observable[K], Loopable):
    """Observable that outputs a single value then closes."""

    @staticmethod
    async def _worker(
        value: T.Union[K, T.Awaitable[K]], observer: Observer[K, T.Any], namespace: Namespace
    ) -> None:
        if isfuture(value):
            try:
                value = await T.cast(T.Awaitable[K], value)
            except Exception as ex:
                await observer.araise(ex, namespace)
            else:
                await observer.asend(value)
        else:
            await observer.asend(T.cast(K, value))

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, value: T.Union[K, T.Awaitable[K]], **kwargs: T.Any) -> None:
        """Unit constructor

        Arguments:
            value: Value to be outputted by observable.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Internal
        try:
            self._value: T.Union[K, T.Awaitable[K]] = ensure_future(T.cast(T.Awaitable[K], value))
        except TypeError:
            self._value = value

        self._namespace = get_namespace(self, "fixed")

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        # Add worker execution to loop queue
        task = observer.loop.create_task(Unit._worker(self._value, observer, self._namespace))

        return AnonymousDisposable(task.cancel)
