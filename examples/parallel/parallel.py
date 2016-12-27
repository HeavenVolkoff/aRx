import time
import asyncio
import logging
from asyncio.futures import wrap_future
from concurrent.futures import ThreadPoolExecutor
from threading import current_thread

from aioreactive.core import AsyncObservable, subscribe
from aioreactive.core.operators import pipe as op

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

executor = ThreadPoolExecutor(max_workers=10)


def long_running(value):
    print("Long running ({0}) on thread {1}".format(value, current_thread().name))
    time.sleep(3)
    print("Long running, done ({0}) on thread {1}".format(value, current_thread().name))
    return value


async def main():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])

    async def mapper(value):
        fut = executor.submit(long_running, value)
        return AsyncObservable.unit(wrap_future(fut))

    ys = xs | op.flat_map(mapper)
    async with subscribe(ys) as stream:
        async for x in stream:
            print(x)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()