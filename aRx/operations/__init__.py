"""Operations Module

The aRx operations are the building blocks for enabling ease of use. They offer
constructs for joining, composing and structuring the Observers, Observables and
Transformers into custom data pipelines.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Project
from .pipe_op import pipe
from .sink_op import sink
from .concat_op import concat
from .observe_op import observe
