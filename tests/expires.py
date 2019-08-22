# Internal
from asyncio import TimeoutError, sleep, gather, get_event_loop
from contextlib import suppress

# External
from aRx.expires import expires


async def test_expires_timeout():
    with expires(1):
        await sleep(2)


try:
    get_event_loop().run_until_complete(test_expires_timeout())
except Exception:
    print("Success")
else:
    print("Failed")


async def test_expires_no_timeout():
    with expires(1):
        await sleep(0.5)


try:
    get_event_loop().run_until_complete(test_expires_no_timeout())
except Exception:
    print("Failed")
else:
    print("Success")


async def test_expires_timeout_suppress():
    with suppress(TimeoutError):
        with expires(1):
            await sleep(2)


try:
    get_event_loop().run_until_complete(test_expires_timeout_suppress())
except Exception:
    print("Failed")
else:
    print("Success")


async def test_expires_reset_timeout():
    with expires(1) as timeout:
        await sleep(0.5)
        timeout.reset()
        await sleep(2)


try:
    get_event_loop().run_until_complete(test_expires_reset_timeout())
except Exception:
    print("Success")
else:
    print("Failed")


async def test_expires_reset_no_timeout():
    with expires(1) as timeout:
        await sleep(0.5)
        timeout.reset()
        await sleep(0.5)
        timeout.reset()
        await sleep(0.8)


try:
    get_event_loop().run_until_complete(test_expires_reset_no_timeout())
except Exception:
    print("Failed")
else:
    print("Success")

try:
    print(
        get_event_loop().run_until_complete(
            gather(
                test_expires_timeout(),
                test_expires_no_timeout(),
                test_expires_timeout_suppress(),
                test_expires_reset_timeout(),
                test_expires_reset_no_timeout(),
                return_exceptions=True,
            )
        )
    )
except Exception as exc:
    print("Failed")
    print(exc)
