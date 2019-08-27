# Internal
import typing as T

# Project
from .sink_op import sink
from .observe_op import observe

if T.TYPE_CHECKING:
    # Internal
    from types import TracebackType

    # Project
    from ..protocols import ObserverProtocol, ObservableProtocol, TransformerProtocol


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


class pipe(T.Generic[K, L], observe[K]):
    def __init__(
        self,
        observable: "ObservableProtocol[K]",
        transformer: "TransformerProtocol[K, L]",
        *,
        previous_pipe: T.Optional["pipe[M, K]"] = None,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(observable, transformer, **kwargs)

        # Internal
        self._previous = previous_pipe
        self._transformer = transformer

    def __or__(self, transformer: "TransformerProtocol[L, M]") -> "pipe[L, M]":
        return pipe(self._transformer, transformer, previous_pipe=self)

    def __gt__(self, observer: "ObserverProtocol[L]") -> sink[L]:
        return sink(self._transformer, observer, previous_pipe=self)

    async def __aenter__(self) -> None:
        await super().__aenter__()

        if self._previous:
            await self._previous.__aenter__()

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional["TracebackType"],
    ) -> None:
        if self._previous is not None:
            await self._previous.__aexit__(exc_type, exc_value, traceback)

        await super().__aexit__(exc_type, exc_value, traceback)
