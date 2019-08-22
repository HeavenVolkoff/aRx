"""Example to show how to split a stream into two substreams."""
# Internal
import asyncio

# External
from aioreactive.core import Operators as op, AsyncObservable, AsyncAnonymousObserver, subscribe


async def main():
    xs = AsyncObservable.from_iterable(range(10))

    # Split into odds and evens
    odds = xs | op.filter(lambda x: x % 2 == 1)
    evens = xs | op.filter(lambda x: x % 2 == 0)

    async def mysink(value):
        print(value)

    await subscribe(odds, AsyncAnonymousObserver(mysink))
    await subscribe(evens, AsyncAnonymousObserver(mysink))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
