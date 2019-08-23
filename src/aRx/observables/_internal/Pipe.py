# Internal
import typing as T
from types import TracebackType
from asyncio import CancelledError

# External
import typing_extensions as Te
from async_tools import wait_with_care
from async_tools.context import asynccontextmanager

# Project
from ...protocols import ObserverProtocol, ObservableProtocol, TransformerProtocol

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


@asynccontextmanager
async def sink(
    source: ObservableProtocol[T.Any],
    transformations: T.List[TransformerProtocol[T.Any, T.Any]],
    sink: T.Optional[ObserverProtocol[T.Any]] = None,
) -> Te.AsyncGenerator[None, None]:
    from ...operations import dispose

    ops: T.List[T.Awaitable[None]] = []
    pairs: T.Tuple[T.Tuple[ObservableProtocol[T.Any], ObserverProtocol[T.Any]], ...] = tuple(
        pair for pair in zip(transformations[:-1], transformations[1:])
    )
    cancelled = False

    ops.append(source.__observe__(transformations[0]))
    ops.extend((observable.__observe__(observer) for observable, observer in pairs))
    if sink:
        ops.append(transformations[-1].__observe__(sink))

    try:
        for observation in ops:
            await observation

        yield None
    except CancelledError:
        cancelled = True
        raise
    except Exception:
        raise
    except BaseException:
        cancelled = True
        raise
    finally:
        ops.clear()

        if not cancelled:
            ops.append(dispose(source, transformations[0]))
            ops.extend(
                (
                    dispose(observable, observer)  # type: ignore
                    for observer, observable in pairs
                )
            )
            if sink:
                ops.append(dispose(transformations[-1], sink))

            await wait_with_care(*ops, raise_first_error=True)


class Pipe(T.Generic[K, L], T.AsyncContextManager[None], T.Awaitable[T.AsyncContextManager[None]]):
    def __init__(
        self, source: ObservableProtocol[K], transformation: TransformerProtocol[K, L]
    ) -> None:
        self._ctx: T.Optional[T.AsyncContextManager[None]] = None
        self._source: ObservableProtocol[K] = source
        self._transformations: T.List[TransformerProtocol[K, L]] = [transformation]

    def __or__(self, transformer: TransformerProtocol[L, M]) -> "Pipe[L, M]":
        # This is necessary for ensuring the correct propagation of type through the piping
        p = T.cast(Pipe[L, M], self)

        p.__append__(transformer)

        return p

    def __gt__(self, observer: ObserverProtocol[L]) -> Te.AsyncContextManager[None]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        self._ctx = sink(self._source, self._transformations, observer)

        return self

    def __await__(self) -> T.Generator[None, None, T.AsyncContextManager[None]]:
        ctx = sink(self._source, self._transformations)

        yield from self.__aenter__().__await__()

        return ctx

    __iter__ = __await__  # make compatible with 'yield from'.

    async def __aenter__(self) -> None:
        if self._ctx:
            raise RuntimeError("This pipe is already open")

        self._ctx = sink(self._source, self._transformations)

        return await self._ctx.__aenter__()

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> None:
        if not self._ctx:
            raise RuntimeError("This pipe is not open")

        await self._ctx.__aexit__(exc_type, exc_value, traceback)

        self._ctx = None

        return

    def __append__(self, value: TransformerProtocol[K, L]) -> None:
        if self._ctx:
            raise RuntimeError("This pipe is already open")

        if isinstance(value, TransformerProtocol):
            self._transformations.append(value)
        else:
            raise TypeError(
                "Unsupported operand type(s) for | rvalue. "
                "Must be an object that implements TransformerProtocol"
            )
