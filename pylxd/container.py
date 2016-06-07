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
import time

import six
from six.moves.urllib import parse
from ws4py.client import WebSocketBaseClient
from ws4py.manager import WebSocketManager

from pylxd import exceptions, managers, mixin
from pylxd.deprecation import deprecated
from pylxd.operation import Operation


class ContainerState(object):
    """A simple object for representing container state."""

    def __init__(self, **kwargs):
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)


class Container(mixin.Marshallable):
    """An LXD Container.

    This class is not intended to be used directly, but rather to be used
    via `Client.containers.create`.
    """

    class FilesManager(object):
        """A pseudo-manager for namespacing file operations."""

        def __init__(self, client, container):
            self._client = client
            self._container = container

        def put(self, filepath, data):
            response = self._client.api.containers[
                self._container.name].files.post(
                params={'path': filepath}, data=data)
            return response.status_code == 200

        def get(self, filepath):
            try:
                response = self._client.api.containers[
                    self._container.name].files.get(
                    params={'path': filepath})
            except exceptions.LXDAPIException as e:
                # LXD 2.0.3+ return 404, not 500,
                if e.response.status_code in (500, 404):
                    raise exceptions.NotFound()
                raise
            return response.content

    __slots__ = [
        '_client',
        'architecture', 'config', 'created_at', 'devices', 'ephemeral',
        'expanded_config', 'expanded_devices', 'name', 'profiles', 'status'
    ]

    @classmethod
    def get(cls, client, name):
        """Get a container by name."""
        try:
            response = client.api.containers[name].get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise

        container = cls(_client=client, **response.json()['metadata'])
        return container

    @classmethod
    def all(cls, client):
        """Get all containers.

        Containers returned from this method will only have the name
        set, as that is the only property returned from LXD. If more
        information is needed, `Container.fetch` is the method call
        that should be used.
        """
        response = client.api.containers.get()

        containers = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            containers.append(cls(_client=client, name=name))
        return containers

    @classmethod
    def create(cls, client, config, wait=False):
        """Create a new container config."""
        try:
            response = client.api.containers.post(json=config)
        except exceptions.LXDAPIException as e:
            raise exceptions.CreateFailed(e.response)

        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return cls(name=config['name'], _client=client)

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

        self.snapshots = managers.SnapshotManager(self._client, self)
        self.files = self.FilesManager(self._client, self)

    def fetch(self):
        """Reload the container information."""
        try:
            response = self._client.api.containers[self.name].get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise
        for key, value in six.iteritems(response.json()['metadata']):
            setattr(self, key, value)
    # XXX: rockstar (28 Mar 2016) - This method was named improperly
    # originally. It's being kept here for backwards compatibility.
    reload = deprecated(
        "Container.reload is deprecated. Please use Container.fetch")(
        fetch)

    def update(self, wait=False):
        """Update the container in lxd from local changes."""
        try:
            marshalled = self.marshall()
        except AttributeError:
            raise exceptions.ObjectIncomplete()
        # These two properties are explicitly not allowed.
        del marshalled['name']
        del marshalled['status']

        response = self._client.api.containers[self.name].put(
            json=marshalled)

        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])

    def rename(self, name, wait=False):
        """Rename a container."""
        response = self._client.api.containers[
            self.name].post(json={'name': name})

        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])
        self.name = name

    def delete(self, wait=False):
        """Delete the container."""
        response = self._client.api.containers[self.name].delete()

        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])

    def _set_state(self, state, timeout=30, force=True, wait=False):
        response = self._client.api.containers[self.name].state.put(json={
            'action': state,
            'timeout': timeout,
            'force': force
        })
        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])
            self.fetch()

    def state(self):
        response = self._client.api.containers[self.name].state.get()
        state = ContainerState(**response.json()['metadata'])
        return state

    def start(self, timeout=30, force=True, wait=False):
        """Start the container."""
        return self._set_state('start',
                               timeout=timeout,
                               force=force,
                               wait=wait)

    def stop(self, timeout=30, force=True, wait=False):
        """Stop the container."""
        return self._set_state('stop',
                               timeout=timeout,
                               force=force,
                               wait=wait)

    def restart(self, timeout=30, force=True, wait=False):
        """Restart the container."""
        return self._set_state('restart',
                               timeout=timeout,
                               force=force,
                               wait=wait)

    def freeze(self, timeout=30, force=True, wait=False):
        """Freeze the container."""
        return self._set_state('freeze',
                               timeout=timeout,
                               force=force,
                               wait=wait)

    def unfreeze(self, timeout=30, force=True, wait=False):
        """Unfreeze the container."""
        return self._set_state('unfreeze',
                               timeout=timeout,
                               force=force,
                               wait=wait)

    @deprecated('Container.snapshot is deprecated. Please use Container.snapshots.create')  # NOQA
    def snapshot(self, name, stateful=False, wait=False):  # pragma: no cover
        """Take a snapshot of the container."""
        self.snapshots.create(name, stateful, wait)

    @deprecated('Container.list_snapshots is deprecated. Please use Container.snapshots.all')  # NOQA
    def list_snapshots(self):  # pragma: no cover
        """List all container snapshots."""
        return [s.name for s in self.snapshots.all()]

    @deprecated('Container.rename_snapshot is deprecated. Please use Snapshot.rename')  # NOQA
    def rename_snapshot(self, old, new, wait=False):  # pragma: no cover
        """Rename a snapshot."""
        snapshot = self.snapshots.get(old)
        snapshot.rename(new, wait=wait)

    @deprecated('Container.delete_snapshot is deprecated. Please use Snapshot.delete')  # NOQA
    def delete_snapshot(self, name, wait=False):  # pragma: no cover
        """Delete a snapshot."""
        snapshot = self.snapshots.get(name)
        snapshot.delete(wait=wait)

    @deprecated('Container.get_file is deprecated. Please use Container.files.get')  # NOQA
    def get_file(self, filepath):  # pragma: no cover
        """Get a file from the container."""
        return self.files.get(filepath)

    @deprecated('Container.put_file is deprecated. Please use Container.files.put')  # NOQA
    def put_file(self, filepath, data):  # pragma: no cover
        """Put a file on the container."""
        return self.files.put(filepath, data)

    def execute(self, commands, environment={}):
        """Execute a command on the container."""
        if isinstance(commands, six.string_types):
            raise TypeError("First argument must be a list.")
        response = self._client.api.containers[self.name]['exec'].post(json={
            'command': commands,
            'environment': environment,
            'wait-for-websocket': True,
            'interactive': False,
        })

        fds = response.json()['metadata']['metadata']['fds']
        operation_id = response.json()['operation'].split('/')[-1]
        parsed = parse.urlparse(
            self._client.api.operations[operation_id].websocket._api_endpoint)

        manager = WebSocketManager()

        stdin = _StdinWebsocket(manager, self._client.websocket_url)
        stdin.resource = '{}?secret={}'.format(parsed.path, fds['0'])
        stdin.connect()
        stdout = _CommandWebsocketClient(manager, self._client.websocket_url)
        stdout.resource = '{}?secret={}'.format(parsed.path, fds['1'])
        stdout.connect()
        stderr = _CommandWebsocketClient(manager, self._client.websocket_url)
        stderr.resource = '{}?secret={}'.format(parsed.path, fds['2'])
        stderr.connect()

        manager.start()

        while True:  # pragma: no cover
            for websocket in manager.websockets.values():
                if not websocket.terminated:
                    break
            else:
                break
            time.sleep(1)

        return stdout.data, stderr.data


class _CommandWebsocketClient(WebSocketBaseClient):  # pragma: no cover
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super(_CommandWebsocketClient, self).__init__(*args, **kwargs)

    def handshake_ok(self):
        self.manager.add(self)
        self.buffer = []

    def received_message(self, message):
        if message.encoding:
            self.buffer.append(message.data.decode(message.encoding))
        else:
            self.buffer.append(message.data.decode('utf-8'))

    @property
    def data(self):
        return ''.join(self.buffer)


class _StdinWebsocket(WebSocketBaseClient):  # pragma: no cover
    """A websocket client for handling stdin."""
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super(_StdinWebsocket, self).__init__(*args, **kwargs)

    def handshake_ok(self):
        self.manager.add(self)
        self.close()


class Snapshot(mixin.Marshallable):
    """A container snapshot."""

    @classmethod
    def get(cls, client, container, name):
        try:
            response = client.api.containers[
                container.name].snapshots[name].get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise

        snapshot = cls(
            _client=client, _container=container,
            **response.json()['metadata'])
        # Snapshot names are namespaced in LXD, as
        # container-name/snapshot-name. We hide that implementation
        # detail.
        snapshot.name = snapshot.name.split('/')[-1]
        return snapshot

    @classmethod
    def all(cls, client, container):
        response = client.api.containers[container.name].snapshots.get()

        return [cls(
                name=snapshot.split('/')[-1], _client=client,
                _container=container)
                for snapshot in response.json()['metadata']]

    @classmethod
    def create(cls, client, container, name, stateful=False, wait=False):
        response = client.api.containers[container.name].snapshots.post(json={
            'name': name, 'stateful': stateful})

        snapshot = cls(_client=client, _container=container, name=name)
        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return snapshot

    def __init__(self, **kwargs):
        super(Snapshot, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def rename(self, new_name, wait=False):
        """Rename a snapshot."""
        response = self._client.api.containers[
            self._container.name].snapshots[self.name].post(
            json={'name': new_name})
        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])
        self.name = new_name

    def delete(self, wait=False):
        """Delete a snapshot."""
        response = self._client.api.containers[
            self._container.name].snapshots[self.name].delete()

        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])
