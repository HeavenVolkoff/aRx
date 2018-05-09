# Internal
import typing as T

from abc import ABCMeta

# Project
from ..abstract import Observable, Loggable, Disposable, Observer


async def observe(source: Observable, sink: Observer) -> Disposable:
    return await source.__aobserve__(sink)


class BaseObservable(Observable, Loggable, metaclass=ABCMeta):
    """The base class for all Observables.

    Implements all the common behaviour of a Observable
    """

    def __init__(self, **kwargs) -> None:
        """Observable Constructor.

        Args:
            kwargs: Super classes named parameters
        """
        super().__init__(**kwargs)

    def __or__(self, other: T.Callable[[Observable], 'BaseObservable']
               ) -> 'BaseObservable':
        """Forward pipe. Compose new observable with operator.

        Args:
            other: Partial implementation of operator

        Returns:
             New Observable resulted from composition of this observable with
             operator
        """
        return other(self)

    def __gt__(self, observer: Observer) -> Disposable:
        """Grater than. Call observe.

        Args:
            observer: Observer that will observe this observable

        Returns:
            Disposable to control observation life-cycle
        """
        from ..supervision import supervise
        return supervise(self, observer)

    def __add__(self, other: 'BaseObservable') -> 'BaseObservable':
        """Pythonic version of concat

        Example:
        zs = xs + ys

        Returns concat(other, self)"""
        from ..stream.operator.interface import concat as concat_op
        return concat_op(self, other)

    def __iadd__(self, other: 'BaseObservable') -> 'BaseObservable':
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(other, self)"""
        from ..stream.operator.interface import concat as concat_op
        return concat_op(self, other)

    # def __getitem__(self, key) -> 'BaseObservable':
    #     """Slices the given source stream using Python slice notation.
    #     The arguments to slice is start, stop and step given within
    #     brackets [] and separated with the ':' character. It is
    #     basically a wrapper around the operator skip(), skip_last(),
    #     take(), take_last() and filter().
    #
    #     This marble diagram helps you remember how slices works with
    #     streams. Positive numbers is relative to the start of the
    #     events, while negative numbers are relative to the end
    #     (on_completed) of the stream.
    #
    #     r---e---a---c---t---i---v---e---|
    #     0   1   2   3   4   5   6   7   8
    #    -8  -7  -6  -5  -4  -3  -2  -1
    #
    #     Example:
    #     result = source[1:10]
    #     result = source[1:-2]
    #     result = source[1:-1:2]
    #
    #     Keyword arguments:
    #     self -- Source to slice
    #     key -- Slice object
    #
    #     Return a sliced source stream."""
    #
    #     if isinstance(key, slice):
    #         start, stop, step = key.start, key.stop, key.step
    #     elif isinstance(key, int):
    #         start, stop, step = key, key + 1, 1
    #     else:
    #         raise TypeError("Invalid argument type.")
    #
    #     return slice(start, stop, step, self)

    # def delay(self, seconds: float) -> 'BaseObservable':
    #     return delay(seconds, self)

    def where(self, predicate: T.Callable) -> 'BaseObservable':
        from ..stream.operator.interface import filter as filter_op
        return filter_op(predicate, self)

    def select(self, selector: T.Callable) -> 'BaseObservable':
        from ..stream.operator.interface import map as map_op
        return map_op(selector, self)

    # def debounce(self, seconds: float) -> 'BaseObservable':
    #     """Debounce observable source.
    #
    #     Ignores values from a source stream which are followed by
    #     another value before seconds has elapsed.
    #
    #     Example:
    #     partial = debounce(5) # 5 seconds
    #
    #     Keyword arguments:
    #     seconds -- Duration of the throttle period for each value
    #
    #     Returns partially applied function that takes a source sequence.
    #     """
    #     return debounce(seconds, self)

    # def select_many(self, selector: T.Callable) -> 'BaseObservable':
    #     return flat_map(selector, self)

    # def with_latest_from(self, mapper, other) -> 'BaseObservable':
    #     return with_latest_from(mapper, other, self)
