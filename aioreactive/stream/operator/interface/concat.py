# Internal
import typing as T

from asyncio import gather
from functools import partial

# Project
from ....stream import SingleStream
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

    def __init__(self, *sources: Observable, **kwargs) -> None:
        """Concat constructor.

        Args:
            sources: Observables to be concatenated
            kwargs: BaseObservable superclass named parameters
        """
        super().__init__(**kwargs)

        self._sources_iterator = iter(sources)

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = SingleStream()

        observations = (
            list(map(partial(self._sinking, sink), self._sources_iterator)) +
            [observe(sink, observer)]
        )

        return CompositeDisposable(
            *(await gather(observations, loop=observer.loop))
        )


def concat(*operators: Observable) -> Concat:
    """Concatenate multiple source streams.

    Returns:
        Concatenated source stream.
    """
    return Concat(*operators)
