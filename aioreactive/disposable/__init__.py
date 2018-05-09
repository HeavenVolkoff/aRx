from .anonymous_disposable import AnonymousDisposable
from .composite_disposable import CompositeDisposable
from ..abstract import Disposable


async def adispose(disposable: Disposable):
    await disposable.__adispose__()
