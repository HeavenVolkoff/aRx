__all__ = ("subscribe", "inquire")

# Internal
import typing as T

from collections.abc import Awaitable

# Project
from .abstract.observer import Observer
from .abstract.observable import Observable, aobserve
from .abstract.disposable import Disposable, adispose

K = T.TypeVar("K")


class Subscription(Awaitable, Disposable, T.Generic[K]):
    """Observable-Observer subscription management.

    A helper class that makes it possible to subscribe observers to observables
    using both await and async-with.
    """

    def __init__(self, observable: Observable, observer: Observer[K], **kwargs):
        """Subscription constructor.

        Args:
            observable: Observable to which subscribe.
            observer: Observer that will be subscribed.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._observer = observer
        self._observable = observable
        self._subscription = None  # type: T.Optional[Disposable]

    def __await__(self) -> T.Generator[T.Any, None, K]:
        """Implementation of the Future-like magic method.

        Redirect to self.create.__await__

        Returns:
            Iterator that will be used internally to manage asynchronous state.

        """
        return self.create().__await__()

    async def create(self):
        """Subscription creation.

        Awaits until stream has been created, and returns the new
        stream.

        """
        if self._subscription is None:
            self._subscription = await aobserve(
                self._observable, self._observer
            )

        return self._subscription

    async def __aenter__(self) -> Disposable:
        """Awaits subscription creation."""
        return await self.create()

    async def __adispose__(self) -> None:
        """:meth:`Disposable.__adispose__`

        Disposes of the subscription
        """
        if self._subscription is not None:
            await adispose(self._subscription)

        self._subscription = None


def subscribe(observer: Observer[K], observable: Observable) -> Subscription:
    """Subscribe observer into observable.

    Args:
        observer: Observer that will be subscribed.
        observable: Observable to which subscribe.

    Returns:
        Subscription that may either be awaited or entered using async-for.
    """
    return Subscription(observable, observer)


async def inquire(observer: Observer[K], observable: Observable) -> K:
    """Subscribe observer into observable and await for observer resolution.

    Args:
        observer: Observer that will be subscribed.
        observable: Observable to which subscribe.

    Returns:
        Subscription that may either be awaited or entered using async-for.
    """
    async with Subscription(observable, observer):
        return await observer
