class ClientConnectionFailed(Exception):
    """An exception raised when the Client connection fails."""


class _LXDAPIException(Exception):
    """A LXD API Exception.

    An exception representing an issue in the LXD API. It
    contains the error information returned from LXD.

    DO NOT CATCH THIS EXCEPTION DIRECTLY.
    """

    def __init__(self, data):
        self.data = data
        self.message = self.data.get('error')


class NotFound(_LXDAPIException):
    """Generic get failure exception."""


class CreateFailed(_LXDAPIException):
    """Generic create failure exception."""
