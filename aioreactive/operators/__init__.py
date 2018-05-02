__all__ = [
    "map", "max", "scan", "skip", "take", "unit", "delay", "never", "merge",
    "retry", "slice", "empty", "filter", "concat", "filteri", "debounce",
    "flat_map", "flat_map_latest", "from_iterable", "switch_latest",
    "with_latest_from", "to_async_iterable", "from_async_iterable",
    "distinct_until_changed", "Operators"
]

# Internal
import typing as T

from functools import partial

# Project
from .map import map
from .max import max
from .skip import skip
from .take import take
from .unit import unit
from .delay import delay
from .never import never
from .merge import merge
from .retry import retry
from .slice import slice
from .empty import empty
from .filter import filter
from .concat import concat
from .filteri import filteri
from .debounce import debounce
from .flat_map import flat_map, flat_map_latest
from .from_iterable import from_iterable
from .switch_latest import switch_latest
from .with_latest_from import with_latest_from
from .to_async_iterable import to_async_iterable
from .from_async_iterable import from_async_iterable
from .distinct_until_changed import distinct_until_changed

from ..observer.base import BaseObserver

K = T.TypeVar("K")
L = T.TypeVar("L")


class Operators:
    """A collection of partially applicable and lazy loaded operators."""

    @staticmethod
    def debounce(seconds: float
                 ) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
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

    @staticmethod
    def delay(seconds: float) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
        return partial(delay, seconds)

    @staticmethod
    def filter(predicate: T.Callable[[K], bool]
               ) -> T.Callable[[BaseObserver[K]], BaseObserver[K]]:
        return partial(filter, predicate)

    @staticmethod
    def flat_map(fn: T.Callable[[K], BaseObserver]
                 ) -> T.Callable[[BaseObserver], BaseObserver]:
        return partial(flat_map, fn)

    @staticmethod
    def map(fn: T.Callable) -> T.Callable[[BaseObserver[K]], BaseObserver[L]]:
        return partial(map, fn)

    @staticmethod
    def merge(other: BaseObserver) -> T.Callable[[BaseObserver], BaseObserver]:
        return partial(merge, other)

    @staticmethod
    def with_latest_from(mapper: T.Callable, other: BaseObserver
                         ) -> T.Callable[[BaseObserver], BaseObserver]:
        return partial(with_latest_from, mapper, other)

    @staticmethod
    def distinct_until_changed() -> T.Callable[[BaseObserver], BaseObserver]:
        return partial(distinct_until_changed)

    @staticmethod
    def switch_latest() -> T.Callable[[BaseObserver], BaseObserver]:
        return partial(switch_latest)

    @staticmethod
    def to_async_iterable() -> T.Callable[[BaseObserver], T.AsyncIterable]:
        return partial(to_async_iterable)
