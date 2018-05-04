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
from ...observer.base import BaseObserver

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
    return partial(debounce, seconds)


def delay(seconds: float) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
    return partial(delay, seconds)


def filter(predicate: T.Callable[[K], bool]
           ) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
    return partial(filter, predicate)


def flat_map(fn: T.Callable[[K], BaseObserver]
             ) -> T.Callable[[BaseObserver], BaseObserver]:
    return partial(flat_map, fn)


def map(fn: T.Callable) -> T.Callable[[BaseObserver[K]], BaseObserver[L]]:
    return partial(map, fn)


def merge(other: BaseObserver) -> T.Callable[[BaseObserver], BaseObserver]:
    return partial(merge, other)


def with_latest_from(mapper: T.Callable, other: BaseObserver
                     ) -> T.Callable[[BaseObserver], BaseObserver]:
    return partial(with_latest_from, mapper, other)


def distinct_until_changed() -> T.Callable[[BaseObserver], BaseObserver]:
    return partial(distinct_until_changed)


def switch_latest() -> T.Callable[[BaseObserver], BaseObserver]:
    return partial(switch_latest)


def to_async_iterable() -> T.Callable[[BaseObserver], T.AsyncIterable]:
    return partial(to_async_iterable)
