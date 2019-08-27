# Internal
import typing as T

# External
from async_tools import attempt_await

# Project
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class Assert(SingleStream[K]):
    def __init__(
        self,
        asend_predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]],
        exc: Exception,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        self._exc = exc
        self._asend_predicate = asend_predicate

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if not await attempt_await(self._asend_predicate(value)):
            raise self._exc

        awaitable = super()._asend(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable


__all__ = ("Assert",)
