class RepoPloneException(Exception):
    """Base exception for the repoplone package."""

    message: str

    def __init__(self, message: str = "An error occurred in the repoplone."):
        self.message = message


class RepoPloneExternalException(RepoPloneException):
    """Base exception for external errors in the repoplone package."""

    pass
