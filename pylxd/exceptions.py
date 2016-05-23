class PylxdException(Exception):
    """Base exception for all exceptions of this module."""


class ContainerCreationFailure(PylxdException):
    """Raised when creating a container has failed."""

    def __init__(self, response):
        self.response = response

        super(ContainerCreationFailure, self).__init__(
            response.status_code,
            response.json()
        )
