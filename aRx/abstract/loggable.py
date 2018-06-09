__all__ = ("Loggable", )

# Internal
import typing as T

from logging import Logger, getLogger


class Loggable(object):
    """Interface that enables logging access.

    Attributes:
        logger: Instance logger
    """

    __slots__ = ("logger", )

    def __init__(
        self,
        *,
        logger_level: T.Optional[T.Union[str, int]] = None,
        parent_logger: T.Optional[Logger] = None,
        **kwargs
    ):
        """Loggable constructor.

        Args:
            logger_level: Logger level definition.
            parent_logger: Parent logger from which a child logger will be
                instantiated.
            kwargs: Keyword parameters for super.
        """
        cls = type(self)

        super().__init__(**kwargs)

        self.logger = (
            parent_logger.getChild(cls.__name__)
            if parent_logger else getLogger(cls.__name__)
        )

        if logger_level is not None:
            self.logger.setLevel(logger_level)
