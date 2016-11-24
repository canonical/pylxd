# Copyright (c) 2016 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import warnings

import six

from pylxd import exceptions


class Attribute(object):
    """A metadata class for model attributes."""

    def __init__(self, validator=None, readonly=False, optional=False):
        self.validator = validator
        self.readonly = readonly
        self.optional = optional


class Manager(object):
    """A manager declaration.

    This class signals to the model that it will have a Manager
    attribute.
    """


class Parent(object):
    """A parent declaration.

    Child managers must keep a reference to their parent.
    """


class ModelType(type):
    """A Model metaclass.

    This metaclass converts the declarative Attribute style
    to attributes on the model instance itself.
    """

    def __new__(cls, name, bases, attrs):
        if '__slots__' in attrs and name != 'Model':  # pragma: no cover
            raise TypeError('__slots__ should not be specified.')
        attributes = {}
        for_removal = []
        managers = []

        for key, val in attrs.items():
            if type(val) == Attribute:
                attributes[key] = val
                for_removal.append(key)
            if type(val) in (Manager, Parent):
                managers.append(key)
                for_removal.append(key)
        for key in for_removal:
            del attrs[key]

        slots = list(attributes.keys())
        if '__slots__' in attrs:
            slots = slots + attrs['__slots__']
        for base in bases:
            if '__slots__' in dir(base):
                slots = slots + base.__slots__
        if len(managers) > 0:
            slots = slots + managers
        attrs['__slots__'] = slots
        attrs['__attributes__'] = attributes

        return super(ModelType, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(ModelType)
class Model(object):
    """A Base LXD object model.

    Objects fetched from the LXD API have state, which allows
    the objects to be used transactionally, with E-tag support,
    and be smart about I/O.

    The model lifecycle is this: A model's get/create methods will
    return an instance. That instance may or may not be a partial
    instance. If it is a partial instance, `sync` will be called
    and the rest of the object retrieved from the server when
    un-initialized attributes are read. When attributes are modified,
    the instance is marked as dirty. `save` will save the changes
    to the server.
    """
    NotFound = exceptions.NotFound
    __slots__ = ['client', '__dirty__']

    def __init__(self, client, **kwargs):
        self.__dirty__ = set()
        self.client = client

        for key, val in kwargs.items():
            try:
                setattr(self, key, val)
            except AttributeError:
                warnings.warn(
                    'Attempted to set unknown attribute "{}" '
                    'on instance of "{}"'.format(
                        key, self.__class__.__name__
                    ))
        self.__dirty__.clear()

    def __getattribute__(self, name):
        try:
            return super(Model, self).__getattribute__(name)
        except AttributeError:
            if name in self.__attributes__:
                self.sync()
                return super(Model, self).__getattribute__(name)
            else:
                raise

    def __setattr__(self, name, value):
        if name in self.__attributes__:
            attribute = self.__attributes__[name]

            if attribute.validator is not None:
                if attribute.validator is not type(value):
                    value = attribute.validator(value)
            self.__dirty__.add(name)
        return super(Model, self).__setattr__(name, value)

    @property
    def dirty(self):
        return len(self.__dirty__) > 0

    def sync(self, rollback=False):
        """Sync from the server.

        When collections of objects are retrieved from the server, they
        are often partial objects. The full object must be retrieved before
        it can modified. This method is called when getattr is called on
        a non-initaliazed object.
        """
        # XXX: rockstar (25 Jun 2016) - This has the potential to step
        # on existing attributes.
        response = self.api.get()
        for key, val in response.json()['metadata'].items():
            if key not in self.__dirty__ or rollback:
                setattr(self, key, val)
                self.__dirty__.remove(key)
        if rollback:
            self.__dirty__.clear()

    def rollback(self):
        """Reset the object from the server."""
        return self.sync(rollback=True)

    def save(self, wait=False):
        """Save data to the server.

        This method should write the new data to the server via marshalling.
        It should be a no-op when the object is not dirty, to prevent needless
        I/O.
        """
        marshalled = self.marshall()
        response = self.api.put(json=marshalled)

        if response.json()['type'] == 'async' and wait:
            self.client.operations.wait_for_operation(
                response.json()['operation'])
        self.__dirty__.clear()

    def delete(self, wait=False):
        """Delete an object from the server."""
        response = self.api.delete()

        if response.json()['type'] == 'async' and wait:
            self.client.operations.wait_for_operation(
                response.json()['operation'])
        self.client = None

    def marshall(self):
        """Marshall the object in preparation for updating to the server."""
        marshalled = {}
        for key, val in self.__attributes__.items():
            if ((not val.readonly and not val.optional) or
                    (val.optional and hasattr(self, key))):
                marshalled[key] = getattr(self, key)
        return marshalled
