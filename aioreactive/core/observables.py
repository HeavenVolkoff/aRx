# Internal
import typing as T

# Project
from .bases import AsyncObserver
from ..abstract import (
    AsyncDisposable, AsyncObservable as AbstractAsyncObservable
)
from ..operators import (
    unit, empty, never, from_iterable, from_async_iterable, concat, slice as
    slice_op
)
from .subscription import subscribe

K = T.TypeVar('K')
L = T.TypeVar('L')
M = T.TypeVar('M')


class AsyncChainedObservable(AsyncObservable):
    """An AsyncChainedObservable example class similar to Rx.

    This class supports has all operators as methods and supports
    method chaining.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable = None) -> None:
        super().__init__()
        self._source = source

    def subscribe(self, obv: AsyncObserver):
        from .subscription import subscribe
        return subscribe(self, obv)

    def __getitem__(self, key) -> 'AsyncChainedObservable':
        """Slices the given source stream using Python slice notation.
        The arguments to slice is start, stop and step given within
        brackets [] and separated with the ':' character. It is
        basically a wrapper around the operators skip(), skip_last(),
        take(), take_last() and filter().

        This marble diagram helps you remember how slices works with
        streams. Positive numbers is relative to the start of the
        events, while negative numbers are relative to the end
        (on_completed) of the stream.

        r---e---a---c---t---i---v---e---|
        0   1   2   3   4   5   6   7   8
       -8  -7  -6  -5  -4  -3  -2  -1

        Example:
        result = source[1:10]
        result = source[1:-2]
        result = source[1:-1:2]

        Keyword arguments:
        self -- Source to slice
        key -- Slice object

        Returne a sliced source stream."""

        return AsyncChainedObservable(
            super(AsyncChainedObservable, self).__getitem__(key)
        )

    def __add__(self, other) -> 'AsyncChainedObservable':
        """Pythonic version of concat

        Example:
        zs = xs + ys
        Returns self.concat(other)"""

        xs = super(AsyncChainedObservable, self).__add__(other)
        return AsyncChainedObservable(xs)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(self, other)"""

        xs = super(AsyncChainedObservable, self).__iadd__(other)
        return AsyncChainedObservable(xs)

    @classmethod
    def from_iterable(cls, iter):
        return AsyncChainedObservable(AsyncObservable.from_iterable(iter))

    @classmethod
    def just(cls, value) -> 'AsyncChainedObservable':
        return AsyncChainedObservable(AsyncObservable.unit(value))

    @classmethod
    def empty(cls) -> 'AsyncChainedObservable':
        return AsyncChainedObservable(AsyncObservable.empty())

    def debounce(self, seconds: float) -> 'AsyncChainedObservable':
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from aioreactive.operators.debounce import debounce
        return AsyncChainedObservable(debounce(seconds, self))

    def delay(self, seconds: float) -> 'AsyncChainedObservable':
        from aioreactive.operators.delay import delay
        return AsyncChainedObservable(delay(seconds, self))

    def where(self, predicate: Callable) -> 'AsyncChainedObservable':
        from aioreactive.operators.filter import filter
        return AsyncChainedObservable(filter(predicate, self))

    def select_many(self, selector: Callable) -> 'AsyncChainedObservable':
        from aioreactive.operators.flat_map import flat_map
        return AsyncChainedObservable(flat_map(selector, self))

    def select(self, selector: Callable) -> 'AsyncChainedObservable':
        from aioreactive.operators.map import map
        return AsyncChainedObservable(map(selector, self))

    def merge(
        self, other: 'AsyncChainedObservable'
    ) -> 'AsyncChainedObservable':
        from aioreactive.operators.merge import merge
        return AsyncChainedObservable(merge(other, self))

    def with_latest_from(self, mapper, other) -> 'AsyncChainedObservable':
        from aioreactive.operators.with_latest_from import with_latest_from
        return AsyncChainedObservable(with_latest_from(mapper, other, self))


def as_chained(source: AsyncObservable) -> AsyncChainedObservable:
    return AsyncChainedObservable(source)
