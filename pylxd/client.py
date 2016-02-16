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
import hashlib
import os
import urllib

import requests
import requests_unixsocket

from pylxd import mixin
from pylxd.container import Container
from pylxd.image import Image
from pylxd.profiles import Profile

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


class _Containers(mixin.Waitable):
    """A wrapper for working with containers."""

    def __init__(self, client):
        self._client = client

    def get(self, name):
        response = self._client.api.containers[name].get()

        if response.status_code == 404:
            raise NameError('No container named "{}"'.format(name))
        container = Container(_client=self._client, **response.json()['metadata'])
        return container

    def all(self):
        response = self._client.api.containers.get()

        containers = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            containers.append(Container(_client=self._client, name=name))
        return containers

    def create(self, config, wait=False):
        response = self._client.api.containers.post(json=config)

        if wait:
            operation_id = response.json()['operation'].split('/')[-1]
            self.wait_for_operation(operation_id)
        return Container(name=config['name'])


class _Images(mixin.Waitable):
    """A wrapper for working with images."""

    def __init__(self, client):
        self._client = client

    def get(self, fingerprint):
        response = self._client.api.images[fingerprint].get()

        if response.status_code == 404:
            raise NameError('No image with fingerprint "{}"'.format(fingerprint))
        image = Image(_client=self._client, **response.json()['metadata'])
        return image

    def all(self):
        response = self._client.api.images.get()

        images = []
        for url in response.json()['metadata']:
            fingerprint = url.split('/')[-1]
            images.append(Image(_client=self._client, fingerprint=fingerprint))
        return images

    def create(self, image_data, public=False, wait=False):
        fingerprint = hashlib.sha256(image_data).hexdigest()

        headers = {}
        if public:
            headers['X-LXD-Public'] = '1'
        response = self._client.api.images.post(
            data=image_data, headers=headers)

        if wait:
            self.wait_for_operation(response.json()['operation'])
        return self.get(fingerprint)


class _Profiles(mixin.Waitable):
    """A wrapper for working with profiles."""

    def __init__(self, client):
        self._client = client

    def get(self, name):
        response = self._client.api.profiles[name].get()

        if response.status_code == 404:
            raise NameError('No profile with name "{}"'.format(name))
        return Profile(_client=self._client, **response.json()['metadata'])

    def all(self):
        response = self._client.api.profiles.get()

        profiles = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            profiles.append(Profile(_client=self._client, name=name))
        return profiles

    def create(self, name, config):
        self._client.api.profiles.post(json={
            'name': name,
            'config': config
            })

        return self.get(name)


class _Operations(mixin.Waitable):
    """A wrapper for working with operations."""

    def __init__(self, client):
        self._client = client

    def get(self, operation_id):
        response = self._client.api.operations[operation_id].get()

        return Operation(_client=self._client, **response.json()['metadata'])


class Operation(object):

    __slots__ = [
        '_client',
        'class', 'created_at', 'err', 'id', 'may_cancel', 'metadata',
        'resources', 'status', 'status_code', 'updated_at']

    def __init__(self, **kwargs):
        super(Operation, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def wait(self):
        self._client.api.operations[self.id].wait.get()
