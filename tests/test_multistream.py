# Internal
import unittest

# External
import asynctest
from async_tools import expires

# External
from aRx.streams import MultiStream
from aRx.observers import AnonymousObserver
from aRx.operators import Map, Filter
from aRx.operations import observe


@asynctest.strict
class TestMultiStream(asynctest.TestCase, unittest.TestCase):
    async def test_asend_aclose_deadlock(self):
        with expires(1, suppress=True) as timeout:

            def r(_):
                raise Exception("Fuuuu")

            a = MultiStream()

            await observe(a, AnonymousObserver(aclose=print))

            c = await (a | Map(r))

            await (
                c | Filter(lambda _: True) | Map(lambda x: x)
                > AnonymousObserver(athrow=lambda _, __: True, aclose=a.aclose)
            )

            await a.asend("whatevs")
            await a.aclose()

        self.assertFalse(timeout.expired)
