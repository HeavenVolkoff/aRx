"""aRx streams implementations.

Streams are objects that combine a observer for data input with a observable
for data output. Their purpose is to act as path for data flow between a
diversity of other observables and observers.
"""

from .multi_stream import MultiStream
from .single_stream import SingleStream

Stream = MultiStream
