__all__ = [
    "map", "max", "skip", "take", "delay", "merge", "retry", "slice", "filter",
    "concat", "filteri", "debounce", "flat_map", "flat_map_latest",
    "switch_latest", "with_latest_from", "to_async_iterable",
    "distinct_until_changed"
]

# Internal
import typing as T

from functools import partial

# Project
from ..observer.base import BaseObserver

K = T.TypeVar("K")
L = T.TypeVar("L")


def debounce(seconds: float) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by
    another value before seconds has elapsed.

    Example:
    partial = debounce(5) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value

    Returns a partially applied function that takes a source stream to
    debounce."""
    from .interface.debounce import debounce as op_debounce
    return partial(op_debounce, seconds)


def delay(seconds: float) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
    from .interface.delay import delay as op_delay
    return partial(op_delay, seconds)


def filter(predicate: T.Callable[[K], bool]
           ) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
    from .interface.filter import filter as op_filter
    return partial(op_filter, predicate)


def flat_map(fn: T.Callable[[K], BaseObserver]
             ) -> T.Callable[[BaseObserver], BaseObserver]:
    from .interface.flat_map import flat_map as op_flat_map
    return partial(op_flat_map, fn)


def map(fn: T.Callable) -> T.Callable[[BaseObserver[K]], BaseObserver[L]]:
    from .interface.map import map as op_map
    return partial(op_map, fn)


def merge(other: BaseObserver) -> T.Callable[[BaseObserver], BaseObserver]:
    from .interface.merge import merge as op_merge
    return partial(op_merge, other)


def with_latest_from(mapper: T.Callable, other: BaseObserver
                     ) -> T.Callable[[BaseObserver], BaseObserver]:
    from .interface.with_latest_from import (
        with_latest_from as op_with_latest_from
    )
    return partial(op_with_latest_from, mapper, other)


def distinct_until_changed() -> T.Callable[[BaseObserver], BaseObserver]:
    from .interface.distinct_until_changed import (
        distinct_until_changed as op_distinct_until_changed
    )
    return partial(op_distinct_until_changed)


def switch_latest() -> T.Callable[[BaseObserver], BaseObserver]:
    from .interface.switch_latest import switch_latest as op_switch_latest
    return partial(op_switch_latest)


def to_async_iterable() -> T.Callable[[BaseObserver], T.AsyncIterable]:
    from .interface.to_async_iterable import (
        to_async_iterable as op_to_async_iterable
    )
    return partial(op_to_async_iterable)
