from abstract import Disposable
from .anonymous_disposable import AnonymousDisposable
from .composite_disposable import CompositeDisposable


async def adispose(disposable: Disposable):
    await disposable.__adispose__()
