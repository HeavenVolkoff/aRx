"""aRx operators implementation.

The aRx operators are special observables that can be applied to other
observables in order to compose them into transformed, filtered, aggregated or
combined observables. This observables can be streamed into an observer as
normal.

.. code-block:: none

    Observable -> Operator -> Operator -> Operator -> Observer
"""

__all__ = (
    "map", "Map", "max", "Max", "Min", "min", "skip", "Skip", "take", "Take",
    "filter", "Filter", "concat", "Concat"
)

from .map import Map, map
from .max import Max, max
from .min import Min, min
from .skip import Skip, skip
from .take import Take, take
from .filter import Filter, filter
from .concat import Concat, concat
