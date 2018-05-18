# Internal
import typing as T

from logging import Logger, getLogger


class Loggable(object):
    def __init__(
        self,
        *,
        logger_level: T.Optional[T.Union[str, int]] = None,
        parent_logger: T.Optional[Logger] = None,
        **kwargs
    ):
        cls = type(self)

        super().__init__(**kwargs)

        self.logger = (
            parent_logger.getChild(cls.__name__)
            if parent_logger else getLogger(cls.__name__)
        )

        if logger_level is not None:
            self.logger.setLevel(logger_level)
