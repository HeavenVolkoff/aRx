"""aRx operators implementation.

The aRx operators are special observables that can be applied to other
observables in order to transform them. The resulting observables can be streamed
to an observers as normal.

.. code-block:: none

    Observable | Operator | Operator | Operator > Observer

.. Note::
    Binary OR ``|`` is used to apply operators to observables.

    Greater than ``>`` is used to subscribe observers to observables.

Example using operators to filter odd numbers from a Iterable source.

.. code-block:: python

    from aRx import observables, operators as op
    from aRx.observers import AnonymousObserver

    async def run() -> None:
        # Observer that will print all data that passes through it
        async with AnonymousObserver(asend=lambda x: print(x)) as listener:
            # Apply filter operators to source observables
            source = observables.FromIterable(range(100)) | op.filter(lambda x: bool(x % 2))
            # Subscribe listener to filtered observables, and await for all data to be processed
            await observables.observe(source, listener)
"""


# Project
from .map import Map
from .max import Max
from .min import Min
from .skip import Skip
from .stop import Stop
from .take import Take
from .filter import Filter
from .assertion import Assert