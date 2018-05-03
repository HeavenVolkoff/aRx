import logging


class Loggable(object):
    def __init__(self, *, parent_logger, **kwargs):
        cls = type(self)

        super().__init__(**kwargs)

        self._logger = (
            parent_logger if parent_logger.getChild(cls.__name__) else
            logging.getLogger(cls.__name__)
        )
