class ClientConnectionFailed(Exception):
    """An exception raised when the Client connection fails."""


class ClientAuthenticationFailed(Exception):
    """The LXD client's certificates are not trusted."""

    def __str__(self):
        return "LXD client certificates are not trusted."""


class LXDAPIException(Exception):
    """A generic exception for representing unexpected LXD API responses.

    LXD API responses are clearly documented, and are either a standard
    return value, and background operation, or an error. This exception
    is raised on an error case, or when the response status code is
    not expected for the response.
    """

    def __init__(self, response):
        super(LXDAPIException, self).__init__()
        self.response = response

    def __str__(self):
        try:
            data = self.response.json()
            return data['error']
        except (ValueError, KeyError):
            pass
        return self.response.content.decode('utf-8')


class _LXDAPIException(Exception):
    """A LXD API Exception.

    An exception representing an issue in the LXD API. It
    contains the error information returned from LXD.

    This exception type should be phased out, with the exception being
    raised at a lower level (i.e. where we actually talk to the LXD
    API, not in our pylxd logic).

    DO NOT CATCH THIS EXCEPTION DIRECTLY.
    """

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return self.data.get('error')


class NotFound(Exception):
    """Generic NotFound exception."""

    def __str__(self):
        return 'Object not found'


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
