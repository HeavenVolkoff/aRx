# Internal
from asyncio import ensure_future

# Project
from ..abstract.observer import Observer
from ..abstract.loopable import Loopable
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable.anonymous_disposable import AnonymousDisposable


class Unit(Observable, Loopable):
    """Observable that outputs a single value.

    Attributes:
        value: Value to be outputted by observable.
    """

    def __init__(self, value, **kwargs) -> None:
        """Unit constructor

        Args:
            value: Value to be outputted by observable.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Public
        self.value = value

    async def _worker(self, observer: Observer) -> None:
        try:
            value = ensure_future(self.value)
        except TypeError:
            await observer.asend(self.value)
        else:
            try:
                value = await value
            except Exception as ex:
                await observer.araise(ex)
            else:
                await observer.asend(value)

        await observer.aclose()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        # Add worker execution to loop queue
        task = observer.loop.create_task(self._worker(observer))

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)
