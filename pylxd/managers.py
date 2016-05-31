import functools
import importlib
import inspect


class BaseManager(object):
    """A BaseManager class for handling collection operations."""

    @property
    def manager_for(self):  # pragma: no cover
        raise AttributeError(
            "Manager class requires 'manager_for' attribute")

    def __init__(self, *args, **kwargs):
        manager_for = self.manager_for
        module = '.'.join(manager_for.split('.')[0:-1])
        obj = manager_for.split('.')[-1]
        target_module = importlib.import_module(module)
        target = getattr(target_module, obj)

        methods = inspect.getmembers(target, predicate=inspect.ismethod)
        for name, method in methods:
            func = functools.partial(method, *args, **kwargs)
            setattr(self, name, func)
        return super(BaseManager, self).__init__()


class ContainerManager(BaseManager):
    manager_for = 'pylxd.container.Container'


class ImageManager(BaseManager):
    manager_for = 'pylxd.image.Image'


class ProfileManager(BaseManager):
    manager_for = 'pylxd.profile.Profile'


class OperationManager(BaseManager):
    manager_for = 'pylxd.operation.Operation'


class SnapshotManager(BaseManager):
    manager_for = 'pylxd.container.Snapshot'
