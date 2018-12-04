# Internal
import unittest

# External
from aRx.stream import MultiStream
from aRx.observer import AnonymousObserver
from aRx.observable import observe

# External
import asynctest
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
            await aexit(observation)

        async with MultiStream(loop=self.loop) as stream, AnonymousObserver(
            asend=lambda d, _: results.append(d), aclose=lambda: len(results)
        ) as listener:
            async with observe(stream, listener) as observation:
                self.loop.create_task(send_data())
                self.assertEqual(await listener, len(results))

        self.assertIsNone(self.exception_ctx)
        self.assertEqual(results, ["test", 10, 1.000, {}, []])


if __name__ == "__main__":
    unittest.main()
