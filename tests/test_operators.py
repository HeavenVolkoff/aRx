# Internal
import unittest

# External
import asynctest
from aRx.streams import MultiStream
from aRx.namespace import Namespace
from aRx.observers import AnonymousObserver
from aRx.operators import Map, Assert, Filter


# noinspection PyAttributeOutsideInit
@asynctest.strict
class TestOperators(asynctest.TestCase, unittest.TestCase):
    async def setUp(self):
        self.exception_ctx = None
        self.loop.set_exception_handler(lambda l, c: setattr(self, "exception_ctx", c))

    def tearDown(self):
        pass

    async def test_simple_stream_observation(self):
        results = []

        listener = AnonymousObserver(asend=lambda d, _: results.append(d))

        async with MultiStream() as stream, stream > listener:
            await stream.asend("test")
            await stream.asend(10)
            await stream.asend(1.000)
            await stream.asend({})
            await stream.asend([])

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)
        self.assertEqual(results, ["test", 10, 1.000, {}, []])

    async def test_stream_filter_observation(self):
        listener = AnonymousObserver(asend=lambda d, _: self.assertTrue(bool(d % 2)))

        async with MultiStream() as stream, stream | Filter(lambda x: bool(x % 2)) > listener:
            for x in range(100):
                await stream.asend(x)

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_map_observation(self):
        listener = AnonymousObserver(asend=lambda d, _: self.assertEqual(str(x), d))

        async with MultiStream() as stream, stream | Map(lambda d: str(d)) > listener:
            for x in range(100):
                await stream.asend(x)

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_assert_observation(self):

        exc = Exception("Test")

        listener = AnonymousObserver(
            asend=lambda x, _: self.assertEqual(x, 1), athrow=lambda e, _: self.assertIs(e, exc)
        )

        async with MultiStream() as stream, stream | Assert(lambda x: x == 1, exc) > listener:
            await stream.asend(1)
            await stream.asend(2)

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_raise_observation(self):
        exc = Exception("Test")

        listener = AnonymousObserver(athrow=lambda e, _: self.assertEqual(e, exc))

        async with MultiStream() as stream, stream > listener:
            await stream.athrow(exc)

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_namespace(self):

        listener = AnonymousObserver(
            asend=lambda _, n: (
                self.assertIsInstance(n, Namespace),
                self.assertEqual(n.type, AnonymousObserver),
                self.assertEqual(n.action, "asend"),
                self.assertIs(n.ref, listener),
                self.assertIsInstance(n.previous, Namespace),
                self.assertEqual(n.previous.type, MultiStream),
                self.assertEqual(n.previous.action, "asend"),
                self.assertIs(n.previous.ref, stream),
                self.assertTrue(n.previous.is_root),
            ),
            athrow=lambda _, n: not bool(
                (
                    self.assertIsInstance(n, Namespace),
                    self.assertEqual(n.type, AnonymousObserver),
                    self.assertEqual(n.action, "araise"),
                    self.assertIs(n.ref, listener),
                    self.assertIsInstance(n.previous, Namespace),
                    self.assertEqual(n.previous.type, MultiStream),
                    self.assertEqual(n.previous.action, "araise"),
                    self.assertIs(n.previous.ref, stream),
                    self.assertTrue(n.previous.is_root),
                )
            ),
        )

        async with MultiStream() as stream, stream > listener:
            await stream.asend("test")
            await stream.asend(10)
            await stream.athrow(Exception("Test"))
            await stream.asend(1.000)

        self.assertIsNone(self.exception_ctx)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)


if __name__ == "__main__":
    unittest.main()
