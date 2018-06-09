__all__ = ("filter", "concat", "map", "max", "skip", "take")

# Internal
import typing as T

from .interface.max import max
from functools import partial

# Project
from .interface.map import MapCallable
from .interface.filter import FilterCallable
from ...abstract.observable import Observable

K = T.TypeVar("K")


def map(mapper: MapCallable) -> T.Callable[[Observable], Observable]:
    from .interface.map import map as map_op
    return partial(map_op, mapper)


def skip(count: int) -> T.Callable[[Observable], Observable]:
    from .interface.skip import skip as skip_op
    return partial(skip_op, count)


def take(count: int) -> T.Callable[[Observable], Observable]:
    from .interface.take import take as take_op
    return partial(take_op, count)


def concat(operator: Observable) -> T.Callable[[Observable], Observable]:
    from .interface.concat import concat as concat_op
    return partial(concat_op, operator)


def filter(predicate: FilterCallable) -> T.Callable[[Observable], Observable]:
    from .interface.filter import filter as filter_op
    return partial(filter_op, predicate)
