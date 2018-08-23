__all__ = ("Unit",)

import typing as T
from asyncio import ensure_future

from ..abstract.loopable import Loopable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable


class Unit(Observable, Loopable):
    """Observable that outputs a single value then closes."""

    @staticmethod
    async def _worker(value: T.Any, observer: Observer):
        try:
            value = ensure_future(value)
        except TypeError:
            await observer.asend(value)
        else:
            try:
                value = await value
            except Exception as ex:
                await observer.araise(ex)
            else:
                await observer.asend(value)

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, value, **kwargs) -> None:
        """Unit constructor

        Arguments:
            value: Value to be outputted by observable.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Internal
        self._value = value

    def __observe__(self, observer: Observer) -> Disposable:
        # Add worker execution to loop queue
        task = observer.loop.create_task(Unit._worker(self._value, observer))

        return AnonymousDisposable(task.cancel)
