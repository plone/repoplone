"""Init and utils."""

from zope.i18nmessageid import MessageFactory

import logging


__version__ = "20251006.1"

PACKAGE_NAME = "fake.project"

_ = MessageFactory(PACKAGE_NAME)

logger = logging.getLogger(PACKAGE_NAME)
