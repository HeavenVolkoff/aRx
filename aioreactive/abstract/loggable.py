# Internal
import typing as T

from logging import Logger, getLogger


class Loggable(object):
    def __init__(self, *, parent_logger: T.Optional[Logger] = None, **kwargs):
        cls = type(self)

        super().__init__(**kwargs)

        self.logger = (
            parent_logger.getChild(cls.__name__)
            if parent_logger else getLogger(cls.__name__)
        )
