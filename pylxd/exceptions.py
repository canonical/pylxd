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