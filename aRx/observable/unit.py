# Internal
import typing as T

from asyncio import ensure_future

# Project
from ..abstract.observer import Observer
from ..abstract.loopable import Loopable
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable.anonymous_disposable import AnonymousDisposable


class Unit(Observable, Loopable):
    """Observable that outputs a single value then closes."""

    @staticmethod
    async def _worker(value: T.Any, observer: Observer) -> None:
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

        await observer.aclose()

    def __init__(self, value, **kwargs) -> None:
        """Unit constructor

        Arguments:
            value: Value to be outputted by observable.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Public
        self._value = value

    def __observe__(self, observer: Observer) -> Disposable:
        # Add worker execution to loop queue
        task = observer.loop.create_task(Unit._worker(self._value, observer))

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)
