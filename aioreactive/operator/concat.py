# Internal
import typing as T
import asyncio

# Project
from ..disposable import AnonymousDisposable, CompositeDisposable
from ..observer.base import BaseObserver
from ..observable.base import BaseObservable
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable

from aioreactive.core import AsyncSingleStream


class Concat(BaseObservable):
    """Observable that is the concatenation of multiple observables"""

    class Stream(AsyncSingleStream):
        async def aclose_core(self) -> None:
            self.logger.debug("Concat._:close()")
            self.cancel()

    def __init__(self, *operators: Observable, **kwargs) -> None:
        """Concat constructor.

        Args:
            operators: Observables to be concatenated
            kwargs: BaseObservable superclass name parameters
        """
        super().__init__(**kwargs)

        self._task = None  # type: T.Optional[asyncio.Task]
        self._operators = iter(operators)
        self._subscription = None  # type: T.Optional[Disposable]

    async def worker(self, observer: BaseObserver) -> None:
        def recurse(_) -> None:
            self._task = asyncio.ensure_future(self.worker(observer))

        try:
            source = next(self._operators)
        except StopIteration:
            await observer.aclose()
        except Exception as ex:
            await observer.araise(ex)
        else:
            sink = Concat.Stream()
            down = await sink.__aobserve__(observer)
            sink.add_done_callback(recurse)
            up = await source.__aobserve__(sink)
            self._subscription = CompositeDisposable(up, down)

    async def __aobserve__(self, observer: BaseObserver) -> Disposable:
        async def cancel() -> None:
            if self._subscription is not None:
                await self._subscription.__adispose__()

            if self._task is not None:
                self._task.cancel()

        self._task = asyncio.ensure_future(self.worker(observer))
        return AnonymousDisposable(cancel)


def concat(*operators: BaseObserver) -> BaseObservable:
    """Concatenate two source streams.

    Returns concatenated source stream.
    """
    return Concat(*operators)
