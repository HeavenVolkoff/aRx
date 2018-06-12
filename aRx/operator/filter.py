# Internal
import typing as T

from asyncio import iscoroutinefunction
from functools import partial

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')
FilterCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Filter(Observable):
    """Observable that output filtered data from another observable source."""

    class _Sink(SingleStream):
        def __init__(self, predicate: FilterCallable, **kwargs) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._predicate = predicate

        async def __asend__(self, value: K) -> None:
            try:
                if iscoroutinefunction(self._predicate):
                    is_accepted = await self._predicate(value, self._index)
                else:
                    is_accepted = self._predicate(value, self._index)
            except Exception as ex:
                await self.araise(ex)
            else:
                if is_accepted:
                    await super().__asend__(value)

                self._index += 1

    def __init__(
        self, predicate: FilterCallable, source: Observable, **kwargs
    ) -> None:
        """Filter constructor.

        Args:
            predicate: Predicate to filter source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._Sink(self._predicate)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def filter(predicate: FilterCallable) -> partial[Filter]:
    """Partial implementation of `Filter`_ to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    .. _Filter::

        :class:`Filter`.
    """
    return partial(Filter, predicate)
