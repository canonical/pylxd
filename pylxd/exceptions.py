import exceptions

class ContainerUnDefined(Exception):
    pass

class UntrustedHost(Exception):
    pass

class ContainerProfileCreateFail(Exception):
    pass

class ContainerProfileDeleteFail(Exception):
    pass

class ImageInvalidSize(Exception):
    pass

class APIError(Exception):
    def __init__(self, error, status_code):
        msg = 'Error %s - %s.' % (status_code, error)
        Exception.__init__(self, msg)
        self.status_code = status_code
        self.error = error
