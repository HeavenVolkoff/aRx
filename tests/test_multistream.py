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


def r(_):
    raise Exception("Fuuuu")


@asynctest.strict
class TestMultiStream(asynctest.TestCase, unittest.TestCase):
    async def test_asend_aclose(self):
        with expires(1, suppress=True) as timeout:
            a = MultiStream()
            await (a | Map(r) > AnonymousObserver(athrow=lambda _, __: True, aclose=a.aclose))

            await a.asend("whatevs")
            await a.aclose()

        self.assertFalse(timeout.expired)

    async def test_asend_aclose_complex(self):
        with expires(1, suppress=True) as timeout:
            a = MultiStream()

            await (
                a | Map(r) | Filter(lambda _: True) | Map(lambda x: x)
                > AnonymousObserver(athrow=lambda _, __: True, aclose=a.aclose)
            )

            await a.asend("whatevs")
            await a.aclose()

        self.assertFalse(timeout.expired)
