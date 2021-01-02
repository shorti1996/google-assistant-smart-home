import logging
import re
from logging import FileHandler

from pymaybe import maybe

import config


class CustomFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        arg_pattern = re.compile(r'%\((\w+)\)')
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt)]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None

        return super().format(record)


logger = maybe(None)

if config.LOGGING_ENABLED:
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = CustomFormatter(config.LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.setLevel(config.LOG_LEVEL)
    logger.addHandler(handler)
    logger.addHandler(FileHandler(config.LOG_FILE))


def get_logger():
    return logger
