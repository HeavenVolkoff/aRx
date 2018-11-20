__all__ = ("Loopable",)

# Internal
import typing as T
from asyncio import AbstractEventLoop, get_event_loop


class Loopable(object):
    """Interface for easy access to asyncio loop."""

    __slots__ = ("_loop",)

    def __init__(self, *, loop: T.Optional[AbstractEventLoop] = None, **kwargs: T.Any) -> None:
        """Loopable constructor.

        Arguments:
            loop: Existing asyncio loop to be used.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)  # type: ignore

        self._loop = get_event_loop() if loop is None else loop

    @property
    def loop(self) -> AbstractEventLoop:
        """Public access to loop."""
        return self._loop
