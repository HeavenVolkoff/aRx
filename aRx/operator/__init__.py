"""aRx operators implementation.

The aRx operators are special observables that can be applied to other
observables in order to transform them. The resulting observable can be streamed
to an observer as normal.

.. code-block:: none

    Observable | Operator | Operator | Operator > Observer

.. Note::
    Binary OR ``|`` is used to apply operators to observables.

    Greater than ``>`` is used to subscribe observer to observables.

Example using operator to filter odd numbers from a Iterable source.

.. code-block:: python

    from aRx import observable, operator as op
    from aRx.observer import AnonymousObserver

    async def run():
        # Observer that will print all data that passes through it
        async with AnonymousObserver(asend=lambda x: print(x)) as listener:
            # Apply filter operator to source observable
            source = observable.FromIterable(range(100)) | op.filter(lambda x: bool(x % 2))
            # Subscribe listener to filtered observable, and await for all data to be processed
            await observable.observe(source, listener)
"""

__all__ = (
    "map", "Map", "max", "Max", "Min", "min", "skip", "Skip", "take", "Take",
    "filter", "Filter", "concat", "Concat"
)

from .map import Map, map
from .max import Max, max
from .min import Min, min
from .skip import Skip, skip
from .stop import Stop, stop
from .take import Take, take
from .filter import Filter, filter
from .concat import Concat, concat
