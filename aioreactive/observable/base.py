# Internal
import typing as T
import logging

from abc import ABCMeta
from ..supervision import observe

# Project
from .. import abstract
from .. import operators as op

K = T.TypeVar('K')
M = T.TypeVar('M')


class BaseObservable(T.Generic[K], abstract.Observable, metaclass=ABCMeta):
    """An AsyncObservable that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    @classmethod
    def unit(cls, value: T) -> 'BaseObservable[K]':
        return op.unit(value)

    @classmethod
    def empty(cls) -> 'BaseObservable[K]':
        return op.empty()

    @classmethod
    def never(cls) -> 'BaseObservable[K]':
        return op.never()

    @classmethod
    def from_iterable(cls, iterable: T.Iterable[K]) -> 'BaseObservable[K]':
        return op.from_iterable(iterable)

    @classmethod
    def from_async_iterable(cls, iterable: T.AsyncIterable[K]
                            ) -> 'BaseObservable[K]':
        return op.from_async_iterable(iterable)

    def __init__(self, *, logger: T.Optional[logging.Logger] = None) -> None:
        """Observable Constructor

        Args:
            logger: Optional logger
        """
        cls = type(self)
        self._logger = logger if logger else logging.getLogger(cls.__name__)

    def __or__(
        self, other: T.Callable[['BaseObservable[K]'], 'BaseObservable[M]']
    ) -> 'BaseObservable[M]':
        """Forward pipe. Compose new observable with operator.

        Args:
            other: Partial implementation of operator

        Returns:
             New Observable resulted from composition of this observable with
             operator
        """
        return other(self)

    def __gt__(self, observer: abstract.Observer) -> abstract.Disposable:
        """Grater than. Call observe.

        Args:
            observer: Observer that will observe this observable

        Returns:
            Disposable to control observation life-cycle
        """
        return observe(self, observer)

    def __add__(self, other: 'BaseObservable[K]') -> 'BaseObservable[K]':
        """Pythonic version of concat

        Example:
        zs = xs + ys

        Returns concat(other, self)"""
        return op.concat(self, other)

    def __iadd__(self, other: 'BaseObservable[K]') -> 'BaseObservable[K]':
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(other, self)"""
        return op.concat(self, other)

    def __getitem__(self, key) -> 'BaseObservable[K]':
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

        Return a sliced source stream."""

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
        elif isinstance(key, int):
            start, stop, step = key, key + 1, 1
        else:
            raise TypeError("Invalid argument type.")

        return op.slice(start, stop, step, self)

    def delay(self, seconds: float) -> 'BaseObservable':
        return op.delay(seconds, self)

    def where(self, predicate: T.Callable) -> 'BaseObservable':
        return op.filter(predicate, self)

    def select(self, selector: T.Callable) -> 'BaseObservable':
        return op.map(selector, self)

    def debounce(self, seconds: float) -> 'BaseObservable':
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """
        return op.debounce(seconds, self)

    def select_many(self, selector: T.Callable) -> 'BaseObservable':
        return op.flat_map(selector, self)

    def with_latest_from(self, mapper, other) -> 'BaseObservable':
        return op.with_latest_from(mapper, other, self)
