import logging


__version__ = "1.0.0a6.dev0"


PACKAGE_NAME = "repoplone"


def _setup_logging():
    logger = logging.getLogger(PACKAGE_NAME)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


logger = _setup_logging()
