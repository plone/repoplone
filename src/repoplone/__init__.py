import logging


__version__ = "1.1.1"


PACKAGE_NAME = "repoplone"


def _setup_logging():
    logger = logging.getLogger(PACKAGE_NAME)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


logger = _setup_logging()
