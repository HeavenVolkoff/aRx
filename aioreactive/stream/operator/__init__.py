__all__ = ["filter", "concat", "map", "max", "skip", "take"]

# Internal
import typing as T

from functools import partial

# Project
from ...abstract import Observable
from .interface import (
    filter as filter_op, concat as concat_op, map as map_op, max as max_op, skip
    as skip_op, take as take_op
)
from .interface.map import MapCallable
from .interface.filter import FilterCallable

K = T.TypeVar("K")
L = T.TypeVar("L")


def max(*, close_observer: bool = True) -> T.Callable[[Observable], Observable]:
    return partial(max_op, close_observer=close_observer)


def skip(count: int) -> T.Callable[[Observable], Observable]:
    return partial(skip_op, count)


def take(count: int) -> T.Callable[[Observable], Observable]:
    return partial(take_op, count)


def concat(operator: Observable) -> T.Callable[concat_op]:
    return partial(concat_op, operator)


def map(mapper: MapCallable) -> T.Callable[[Observable], Observable]:
    return partial(map_op, mapper)


def filter(predicate: FilterCallable) -> T.Callable[[Observable], Observable]:
    return partial(filter_op, predicate)
