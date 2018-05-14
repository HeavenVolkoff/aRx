# Internal
import typing as T

from asyncio import gather
from functools import partial

# Project
from ...single_stream import SingleStream
from ....abstract import Observer, Observable, Disposable
from ....observable import observe
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable

K = T.TypeVar("K")


class Concat(BaseObservable):
    """Observable that is the concatenation of multiple observables"""

    @staticmethod
    def _sinking(sink: SingleStream,
                 observable: Observable) -> T.Awaitable[Disposable]:
        return observe(observable, sink)

    def __init__(
        self, a: Observable, b: Observable, *sources: Observable, **kwargs
    ) -> None:
        """Concat constructor.

        Args:
            sources: Observables to be concatenated
            kwargs: BaseObservable superclass named parameters
        """
        super().__init__(**kwargs)

        self._sources_iterator = iter((a, b) + sources)

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = SingleStream(parent_logger=self.logger)

        observations = (
            list(map(partial(self._sinking, sink), self._sources_iterator)) +
            [observe(sink, observer)]
        )

        return CompositeDisposable(
            *(await gather(observations, loop=observer.loop))
        )


def concat(
    a: Observable, b: Observable, *sources: Observable
) -> BaseObservable:
    """Concatenate multiple source streams.

    Returns:
        Concatenated source stream.
    """
    parent_logger = None
    if isinstance(b, BaseObservable):
        parent_logger = b.logger

    return Concat(a, b, *sources, parent_logger=parent_logger)
