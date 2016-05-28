class ClientConnectionFailed(Exception):
    """An exception raised when the Client connection fails."""


class ClientAuthenticationFailed(Exception):
    """The LXD client's certificates are not trusted."""
    message = "LXD client certificates are not trusted."""


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


class ObjectIncomplete(Exception):
    """An exception raised when an object isn't completely populated.

    When an object is fetched via `all`, it isn't a complete object
    just yet. It requires a call to `fetch` to populate the object before
    it can be pushed back up to the server.
    """

    def __str__(self):
        return 'Object incomplete. Please call `fetch` before updating.'
