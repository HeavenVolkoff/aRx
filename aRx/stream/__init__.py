"""aRx streams implementations.

Streams are objects that combine a observer end for data input with a observable
end for data output. Their purpose is to act as a path for data flow between a
diversity of other observables and observers.
"""

from .multi_stream import MultiStream
from .single_stream import SingleStream

Stream = MultiStream
