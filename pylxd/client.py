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

import requests
import requests_unixsocket


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

    def __init__(self, endpoint=None):
        if endpoint is not None:
            self.api = _APINode(endpoint)['1.0']
        else:
            if 'LXD_DIR' in os.environ:
                path = os.path.join(
                    os.environ.get['LXD_DIR'], 'unix.socket')
            else:
                path = '/var/lib/lxd/unix.socket'
            self._api = _APINode('http+unix://{}'.format(path))

        self.containers = _Containers(self)
        self.images = _Images(self)
        self.profiles = _Profiles(self)
        self.operations = _Operations(self)


class _Containers(object):
    """A wrapper for working with containers."""

    def __init__(self, client):
        self._client = client

    def get(self, name):
        pass

    def all(self):
        response = self.client.api.containers.get()

        return []

    def create(self, config):
        pass


class _Images(object):
    """A wrapper for working with images."""

    def __init__(self, client):
        self._client = client


class _Profiles(object):
    """A wrapper for working with profiles."""

    def __init__(self, client):
        self._client = client


class _Operations(object):
    """A wrapper for working with operations."""

    def __init__(self, client):
        self._client = client
