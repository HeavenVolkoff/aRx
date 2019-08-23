# Internal
import unittest

# External
import asynctest
from aRx.streams import MultiStream
from aRx.namespace import Namespace
from aRx.observers import AnonymousObserver
from aRx.operators import Map, Assert, Filter
from async_tools.operator import aexit


# noinspection PyAttributeOutsideInit
@asynctest.strict
class TestStream(asynctest.TestCase, unittest.TestCase):
    async def setUp(self):
        self.exception_ctx = None
        self.loop.set_exception_handler(lambda l, c: setattr(self, "exception_ctx", c))

    def tearDown(self):
        pass

    async def test_simple_stream_observation(self):
        results = []

        async def send_data():
            await stream.asend("test")
            await stream.asend(10)
            await stream.asend(1.000)
            await stream.asend({})
            await stream.asend([])

        async with MultiStream(loop=self.loop) as stream, AnonymousObserver(
            asend=lambda d, _: results.append(d), aclose=lambda: len(results)
        ) as listener, await stream > listener:
            await send_data()

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)
        self.assertEqual(results, ["test", 10, 1.000, {}, []])

    async def test_stream_filter_observation(self):
        async def send_data():
            x = 0
            while x < 100:
                await stream.asend(x)
                x += 1

        async with MultiStream(loop=self.loop) as stream:
            listener = AnonymousObserver(asend=lambda d, _: self.assertTrue(bool(d % 2)))
            async with await (stream | Filter(lambda x, _: bool(x % 2)) > listener):
                await send_data()

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_map_observation(self):
        async def send_data():
            x = 0
            while x < 100:
                await stream.asend(x)
                x += 1

            await aexit(observation)

        x = 0

        def check(d, _):
            nonlocal x
            self.assertEqual(str(x), d)
            x += 1

        async with MultiStream(loop=self.loop) as stream:
            listener = AnonymousObserver(asend=check)
            async with (stream | map_op(lambda x, _: str(x)), listener) as observation:
                self.loop.create_task(send_data())
                self.assertIsNone(await listener)

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_assert_observation(self):
        async def send_data():
            await stream.asend(1)
            await stream.asend(2)

            await aexit(observation)

        exc = Exception("Test")

        async with MultiStream(loop=self.loop) as stream:
            listener = AnonymousObserver(
                asend=lambda x, _: self.assertEqual(x, 1),
                araise=lambda e, _: self.assertIs(e, exc),
            )
            async with observe(stream | assert_op(lambda x: x == 1, exc), listener) as observation:
                self.loop.create_task(send_data())
                self.assertIsNone(await listener)

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_stream_raise_observation(self):
        exc = Exception("Test")

        async def send_data():
            await stream.athrow(exc)
            await aexit(observation)

        async with MultiStream(loop=self.loop) as stream, AnonymousObserver(
            araise=lambda e, _: self.assertEqual(e, exc)
        ) as listener:
            async with observe(stream, listener) as observation:
                self.loop.create_task(send_data())
                self.assertIsNone(await listener)

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)

    async def test_namespace(self):
        async def send_data():
            await stream.asend("test")
            await stream.asend(10)
            await stream.athrow(Exception("Test"))
            await stream.asend(1.000)
            await aexit(observation)

        async with MultiStream(loop=self.loop) as stream, AnonymousObserver(
            asend=lambda _, n: (
                self.assertIsInstance(n, Namespace),
                self.assertEqual(n.type, "AnonymousObserver"),
                self.assertEqual(n.action, "asend"),
                self.assertIs(n.ref, listener),
                self.assertIsInstance(n.previous, Namespace),
                self.assertEqual(n.previous.type, "MultiStream"),
                self.assertEqual(n.previous.action, "asend"),
                self.assertIs(n.previous.ref, stream),
                self.assertTrue(n.previous.is_root),
            ),
            araise=lambda _, n: not bool(
                (
                    self.assertIsInstance(n, Namespace),
                    self.assertEqual(n.type, "AnonymousObserver"),
                    self.assertEqual(n.action, "araise"),
                    self.assertIs(n.ref, listener),
                    self.assertIsInstance(n.previous, Namespace),
                    self.assertEqual(n.previous.type, "MultiStream"),
                    self.assertEqual(n.previous.action, "araise"),
                    self.assertIs(n.previous.ref, stream),
                    self.assertTrue(n.previous.is_root),
                )
            ),
        ) as listener:
            async with observe(stream, listener) as observation:
                self.loop.create_task(send_data())
                self.assertIsNone(await listener)

        self.assertIsNone(self.exception_ctx)
        self.assertIsNone(await stream)
        self.assertTrue(stream.closed)
        self.assertTrue(listener.closed)


if __name__ == "__main__":
    unittest.main()
