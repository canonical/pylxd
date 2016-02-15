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
import os
import urllib

import requests
import requests_unixsocket

requests_unixsocket.monkeypatch()


class _APINode(object):
    """An api node object.

    This class allows us to dynamically create request urls by expressing them
    in python. For example:

        >>> node = _APINode('http://example.com/api')
        >>> node.users[1].comments.get()

    ...would make an HTTP GET request on
    http://example.com/api/users/1/comments
    """

    def __init__(self, api_endpoint):
        self._api_endpoint = api_endpoint

    def __getattr__(self, name):
        return self.__class__('{}/{}'.format(self._api_endpoint, name))

    def __getitem__(self, item):
        return self.__class__('{}/{}'.format(self._api_endpoint, item))

    @property
    def session(self):
        if self._api_endpoint.startswith('http+unix://'):
            return requests_unixsocket.Session()
        else:
            return requests

    def get(self, *args, **kwargs):
        """Perform an HTTP GET."""
        return self.session.get(self._api_endpoint, *args, **kwargs)

    def post(self, *args, **kwargs):
        """Perform an HTTP POST."""
        return self.session.post(self._api_endpoint, *args, **kwargs)

    def put(self, *args, **kwargs):
        """Perform an HTTP PUT."""
        return self.session.put(self._api_endpoint, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """Perform an HTTP delete."""
        return self.session.delete(self._api_endpoint, *args, **kwargs)


class Client(object):
    """A LXD client."""

    def __init__(self, endpoint=None, version='1.0'):
        if endpoint is not None:
            self.api = _APINode(endpoint)
        else:
            if 'LXD_DIR' in os.environ:
                path = os.path.join(
                    os.environ.get['LXD_DIR'], 'unix.socket')
            else:
                path = '/var/lib/lxd/unix.socket'
            self.api = _APINode('http+unix://{}'.format(
                urllib.quote(path, safe='')))
        self.api = self.api[version]

        self.containers = _Containers(self)
        self.images = _Images(self)
        self.profiles = _Profiles(self)
        self.operations = _Operations(self)


class Waitable(object):

    def wait_for_operation(self, operation_id):
        operation = self._client.operations.get(operation_id)
        operation.wait()


class _Containers(Waitable):
    """A wrapper for working with containers."""

    def __init__(self, client):
        self._client = client

    def get(self, name):
        response = self._client.api.containers[name].get()

        container = Container(**response.json()['metadata'])
        return container

    def all(self):
        response = self._client.api.containers.get()

        containers = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            containers.append(Container(name=name))
        return containers

    def create(self, config, wait=False):
        response = self._client.api.containers.post(json=config)

        if wait:
            operation_id = response.json()['operation'].split('/')[-1]
            self.wait_for_operation(operation_id)
        return Container(name=config['name'])


class _Images(Waitable):
    """A wrapper for working with images."""

    def __init__(self, client):
        self._client = client


class _Profiles(Waitable):
    """A wrapper for working with profiles."""

    def __init__(self, client):
        self._client = client


class _Operations(Waitable):
    """A wrapper for working with operations."""

    def __init__(self, client):
        self._client = client

    def get(self, operation_id):
        response = self._client.api.operations[operation_id].get()

        return Operation(_client=self._client, **response.json()['metadata'])


class Container(object):

    __slots__ = [
        'architecture', 'config', 'creation_date', 'devices', 'ephemeral',
        'expanded_config', 'expanded_devices', 'name', 'profiles', 'status'
        ]

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Operation(object):

    __slots__ = [
        '_client',
        'class', 'created_at', 'err', 'id', 'may_cancel', 'metadata', 'resources',
        'status', 'status_code', 'updated_at']

    def __init__(self, **kwargs):
        super(Operation, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def wait(self):
        self._client.api.operations[self.id].wait.get()
