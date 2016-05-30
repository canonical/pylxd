import warnings

warnings.simplefilter('once', DeprecationWarning)


class deprecated():
    """A decorator for warning about deprecation warnings.

    The decorator takes an optional message argument. This message can
    be used to direct the user to a new API or specify when it will
    be removed.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, f):
        def wrapped(*args, **kwargs):
            if self.message is None:
                self.message = '{} is deprecated and will be removed soon.'.format(
                    f.__name__)
            warnings.warn(self.message, DeprecationWarning)
            return f(*args, **kwargs)
        return wrapped
