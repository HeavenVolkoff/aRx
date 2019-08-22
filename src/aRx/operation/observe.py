# Internal
import typing as T

# External
from aRx.abstract import Observer, Observable

K = T.TypeVar("K")


def observe(
    observable: Observable[K], observer: Observer[K], *, keep_alive: T.Optional[bool] = None
) -> T.AsyncContextManager[None]:
    """Register an observer to an observable.

    Enable the observation of the data flowing through the observable to be captured by the
    observer.

    A simple data flow chart would be:
    data ‐→ observable ‐‐(data)‐→ observer

    The logic for registering an observer is specific to each observable, so this function acts as a
    simple access to the :meth:`~.Observable.__observe__` magic method.

    Arguments:
        observable: Observable to be subscribed.
        observer: Observer which will subscribe.
        keep_alive: Flag to keep observer alive when observation is disposed.

    Returns:
        Disposable that undoes this subscription.

    """
    return observable.__observe__(
        observer, keep_alive=observer.keep_alive if keep_alive is None else keep_alive
    )
