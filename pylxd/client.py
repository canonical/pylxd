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

    def get_operation(self, operation_id):
        if operation_id.startswith('/'):
            operation_id = operation_id.split('/')[-1]
        return self._client.operations.get(operation_id)

    def wait_for_operation(self, operation_id):
        operation = self.get_operation(operation_id)
        operation.wait()
        return operation


class _Containers(Waitable):
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


class _Images(Waitable):
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


class Marshallable(object):

    def marshall(self):
        marshalled = {}
        for name in self.__slots__:
            if name.startswith('_'):
                continue
            marshalled[name] = getattr(self, name)
        return marshalled


class Image(object):

    __slots__ = [
        '_client',
        'aliases', 'architecture', 'created_at', 'expires_at', 'filename',
        'fingerprint', 'properties', 'public', 'size', 'uploaded_at'
        ]

    def __init__(self, **kwargs):
        super(Image, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Container(Waitable, Marshallable):

    __slots__ = [
        '_client',
        'architecture', 'config', 'creation_date', 'devices', 'ephemeral',
        'expanded_config', 'expanded_devices', 'name', 'profiles', 'status'
        ]

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def reload(self):
        response = self._client.api.containers[self.name].get()
        if response.status_code == 404:
            raise NameError('Container named "{}" has gone away'.format(self.name))
        for key, value in response.json()['metadata'].iteritems():
            setattr(self, key, value)

    def update(self, wait=False):
        marshalled = self.marshall()
        # These two properties are explicitly not allowed.
        del marshalled['name']
        del marshalled['status']

        response = self._client.api.containers[self.name].put(
            json=marshalled)

        if wait:
            self.wait_for_operation(response.json()['operation'])

    def rename(self, name, wait=False):
        response = self._client.api.containers[self.name].post(json={'name': name})

        if wait:
            self.wait_for_operation(response.json()['operation'])
        self.name = name

    def delete(self, wait=False):
        response = self._client.api.containers[self.name].delete()

        if wait:
            self.wait_for_operation(response.json()['operation'])

    def _set_state(self, state, timeout=30, force=True, wait=False):
        response = self._client.api.containers[self.name].state.put(json={
            'action': state,
            'timeout': timeout,
            'force': force
            })
        if wait:
            self.wait_for_operation(response.json()['operation'])
            self.reload()

    def start(self, timeout=30, force=True, wait=False):
        return self._set_state('start', timeout=timeout, force=force, wait=wait)

    def stop(self, timeout=30, force=True, wait=False):
        return self._set_state('stop', timeout=timeout, force=force, wait=wait)

    def restart(self, timeout=30, force=True, wait=False):
        return self._set_state('stop', timeout=timeout, force=force, wait=wait)

    def freeze(self, timeout=30, force=True, wait=False):
        return self._set_state('stop', timeout=timeout, force=force, wait=wait)

    def unfreeze(self, timeout=30, force=True, wait=False):
        return self._set_state('stop', timeout=timeout, force=force, wait=wait)

    def snapshot(self, name, stateful=False, wait=False):
        response = self._client.api.containers[self.name].snapshots.post(json={
            'name': name, 'stateful': stateful})
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def list_snapshots(self):
        response = self._client.api.containers[self.name].snapshots.get()
        return [snapshot.split('/')[-1] for snapshot in response.json()['metadata']]

    def rename_snapshot(self, old, new, wait=False):
        response = self._client.api.containers[self.name].snapshots[old].post(json={
            'name': new
            })
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def delete_snapshot(self, name, wait=False):
        response = self._client.api.containers[self.name].snapshots[name].delete()
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def get_file(self, filepath):
        response = self._client.api.containers[self.name].files.get(
            params={'path': filepath})
        if response.status_code == 500:
            # XXX: rockstar (15 Feb 2016) - This should really return a 404.
            # I blame LXD. :)
            raise IOError('Error reading "{}"'.format(filepath))
        return response.content

    def put_file(self, filepath, data):
        response = self._client.api.containers[self.name].files.post(
            params={'path': filepath}, data=data)
        return response.status_code == 200

    def execute(self, commands, environment={}):
        # XXX: rockstar (15 Feb 2016) - This functionality is limited by
        # design, for now. It needs to grow the ability to return web sockets
        # and perform interactive functions.
        if type(commands) in [str, unicode]:
            commands = [commands]
        response = self._client.api.containers[self.name]['exec'].post(json={
            'command': commands,
            'environment': environment,
            'wait-for-websocket': False,
            'interactive': False,
            })
        operation_id = response.json()['operation']
        self.wait_for_operation(operation_id)


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
