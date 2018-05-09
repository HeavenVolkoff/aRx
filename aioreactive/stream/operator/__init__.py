__all__ = ["filter", "concat", "map", "max", "skip", "take"]

# Internal
import typing as T

from functools import partial

# Project
from .interface import (
    filter as filter_op, concat as concat_op, map as map_op, max, skip as
    skip_op, take as take_op
)
from .interface.map import MapCallable
from .interface.filter import FilterCallable
from ...abstract import Observable
from ...observable.base import BaseObservable

K = T.TypeVar("K")


def map(mapper: MapCallable) -> T.Callable[[Observable], BaseObservable[K]]:
    return partial(map_op, mapper)


def skip(count: int) -> T.Callable[[Observable], BaseObservable[K]]:
    return partial(skip_op, count)


def take(count: int) -> T.Callable[[Observable], BaseObservable[K]]:
    return partial(take_op, count)


def concat(operator: Observable) -> T.Callable[[Observable], BaseObservable[K]]:
    return partial(concat_op, operator)


def filter(predicate: FilterCallable
           ) -> T.Callable[[Observable], BaseObservable[K]]:
    return partial(filter_op, predicate)
