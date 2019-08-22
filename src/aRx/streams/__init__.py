"""aRx streams implementations.

Streams are objects that combine a observers for data input with a observables
for data output. Their purpose is to act as path for data flow between a
diversity of other observables and observers.
"""

# Project
from .multi_stream import MultiStream
from .single_stream import SingleStream
