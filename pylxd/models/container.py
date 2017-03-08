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
import collections
import time

import six
from six.moves.urllib import parse
try:
    from ws4py.client import WebSocketBaseClient
    from ws4py.manager import WebSocketManager
    _ws4py_installed = True
except ImportError:  # pragma: no cover
    WebSocketBaseClient = object
    _ws4py_installed = False

from pylxd import managers
from pylxd.models import _model as model


class ContainerState(object):
    """A simple object for representing container state."""

    def __init__(self, **kwargs):
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)


_ContainerExecuteResult = collections.namedtuple(
    'ContainerExecuteResult',
    ['exit_code', 'stdout', 'stderr'])


class Container(model.Model):
    """An LXD Container.

    This class is not intended to be used directly, but rather to be used
    via `Client.containers.create`.
    """

    architecture = model.Attribute()
    config = model.Attribute()
    created_at = model.Attribute()
    devices = model.Attribute()
    ephemeral = model.Attribute()
    expanded_config = model.Attribute()
    expanded_devices = model.Attribute()
    name = model.Attribute(readonly=True)
    profiles = model.Attribute()
    status = model.Attribute(readonly=True)
    last_used_at = model.Attribute(readonly=True)

    status_code = model.Attribute(readonly=True)
    stateful = model.Attribute(readonly=True)

    snapshots = model.Manager()
    files = model.Manager()

    @property
    def api(self):
        return self.client.api.containers[self.name]

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
            response = self._client.api.containers[
                self._container.name].files.get(
                params={'path': filepath})
            return response.content

    @classmethod
    def exists(cls, client, name):
        """Determine whether a container exists."""
        try:
            client.containers.get(name)
            return True
        except cls.NotFound:
            return False

    @classmethod
    def get(cls, client, name):
        """Get a container by name."""
        response = client.api.containers[name].get()

        container = cls(client, **response.json()['metadata'])
        return container

    @classmethod
    def all(cls, client):
        """Get all containers.

        Containers returned from this method will only have the name
        set, as that is the only property returned from LXD. If more
        information is needed, `Container.sync` is the method call
        that should be used.
        """
        response = client.api.containers.get()

        containers = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            containers.append(cls(client, name=name))
        return containers

    @classmethod
    def create(cls, client, config, wait=False):
        """Create a new container config."""
        response = client.api.containers.post(json=config)

        if wait:
            client.operations.wait_for_operation(response.json()['operation'])
        return cls(client, name=config['name'])

    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)

        self.snapshots = managers.SnapshotManager(self.client, self)
        self.files = self.FilesManager(self.client, self)

    def rename(self, name, wait=False):
        """Rename a container."""
        response = self.api.post(json={'name': name})

        if wait:
            self.client.operations.wait_for_operation(
                response.json()['operation'])
        self.name = name

    def _set_state(self, state, timeout=30, force=True, wait=False):
        response = self.api.state.put(json={
            'action': state,
            'timeout': timeout,
            'force': force
        })
        if wait:
            self.client.operations.wait_for_operation(
                response.json()['operation'])
            if 'status' in self.__dirty__:
                del self.__dirty__[self.__dirty__.index('status')]
            if self.ephemeral and state == 'stop':
                self.client = None
            else:
                self.sync()

    def state(self):
        response = self.api.state.get()
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

    def execute(self, commands, environment={}):
        """Execute a command on the container.

        In pylxd 2.2, this method will be renamed `execute` and the existing
        `execute` method removed.
        """
        if not _ws4py_installed:
            raise ValueError(
                'This feature requires the optional ws4py library.')
        if isinstance(commands, six.string_types):
            raise TypeError("First argument must be a list.")
        response = self.api['exec'].post(json={
            'command': commands,
            'environment': environment,
            'wait-for-websocket': True,
            'interactive': False,
        })

        fds = response.json()['metadata']['metadata']['fds']
        operation_id = response.json()['operation'].split('/')[-1]
        parsed = parse.urlparse(
            self.client.api.operations[operation_id].websocket._api_endpoint)

        with managers.web_socket_manager(WebSocketManager()) as manager:
            stdin = _StdinWebsocket(self.client.websocket_url)
            stdin.resource = '{}?secret={}'.format(parsed.path, fds['0'])
            stdin.connect()
            stdout = _CommandWebsocketClient(
                manager, self.client.websocket_url)
            stdout.resource = '{}?secret={}'.format(parsed.path, fds['1'])
            stdout.connect()
            stderr = _CommandWebsocketClient(
                manager, self.client.websocket_url)
            stderr.resource = '{}?secret={}'.format(parsed.path, fds['2'])
            stderr.connect()

            manager.start()

            while len(manager.websockets.values()) > 0:
                time.sleep(.1)

            operation = self.client.operations.get(operation_id)

            return _ContainerExecuteResult(
                operation.metadata['return'], stdout.data, stderr.data)

    def migrate(self, new_client, wait=False):
        """Migrate a container.

        Destination host information is contained in the client
        connection passed in.

        If the container is running, it either must be shut down
        first or criu must be installed on the source and destination
        machines.
        """
        if self.api.scheme in ('http+unix',):
            raise ValueError('Cannot migrate from a local client connection')

        return new_client.containers.create(
            self.generate_migration_data(), wait=wait)

    def generate_migration_data(self):
        """Generate the migration data.

        This method can be used to handle migrations where the client
        connection uses the local unix socket. For more information on
        migration, see `Container.migrate`.
        """
        self.sync()  # Make sure the object isn't stale
        response = self.api.post(json={'migration': True})
        operation = self.client.operations.get(response.json()['operation'])
        operation_url = self.client.api.operations[operation.id]._api_endpoint
        secrets = response.json()['metadata']['metadata']
        cert = self.client.host_info['environment']['certificate']

        return {
            'name': self.name,
            'architecture': self.architecture,
            'config': self.config,
            'devices': self.devices,
            'epehemeral': self.ephemeral,
            'default': self.profiles,
            'source': {
                'type': 'migration',
                'operation': operation_url,
                'mode': 'pull',
                'certificate': cert,
                'secrets': secrets,
            }
        }

    def publish(self, public=False, wait=False):
        """Publish a container as an image.

        The container must be stopped in order publish it as an image. This
        method does not enforce that constraint, so a LXDAPIException may be
        raised if this method is called on a running container.

        If wait=True, an Image is returned.
        """
        data = {
            'public': public,
            'source': {
                'type': 'container',
                'name': self.name,
            }
        }

        response = self.client.api.images.post(json=data)
        if wait:
            operation = self.client.operations.wait_for_operation(
                response.json()['operation'])

            return self.client.images.get(operation.metadata['fingerprint'])


class _CommandWebsocketClient(WebSocketBaseClient):  # pragma: no cover
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super(_CommandWebsocketClient, self).__init__(*args, **kwargs)

    def handshake_ok(self):
        self.manager.add(self)
        self.buffer = []

    def received_message(self, message):
        if len(message.data) == 0:
            self.close()
            self.manager.remove(self)
        if message.encoding:
            self.buffer.append(message.data.decode(message.encoding))
        else:
            self.buffer.append(message.data.decode('utf-8'))

    @property
    def data(self):
        return ''.join(self.buffer)


class _StdinWebsocket(WebSocketBaseClient):  # pragma: no cover
    """A websocket client for handling stdin.

    The nature of stdin in Container.execute means that we don't
    ever use this connection. It is closed as soon as it completes
    the handshake.
    """

    def handshake_ok(self):
        self.close()


class Snapshot(model.Model):
    """A container snapshot."""

    name = model.Attribute()
    stateful = model.Attribute()

    container = model.Parent()

    @property
    def api(self):
        return self.client.api.containers[
            self.container.name].snapshots[self.name]

    @classmethod
    def get(cls, client, container, name):
        response = client.api.containers[
            container.name].snapshots[name].get()

        snapshot = cls(
            client, container=container,
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
                client, name=snapshot.split('/')[-1],
                container=container)
                for snapshot in response.json()['metadata']]

    @classmethod
    def create(cls, client, container, name, stateful=False, wait=False):
        response = client.api.containers[container.name].snapshots.post(json={
            'name': name, 'stateful': stateful})

        snapshot = cls(client, container=container, name=name)
        if wait:
            client.operations.wait_for_operation(response.json()['operation'])
        return snapshot

    def rename(self, new_name, wait=False):
        """Rename a snapshot."""
        response = self.api.post(json={'name': new_name})
        if wait:
            self.client.operations.wait_for_operation(
                response.json()['operation'])
        self.name = new_name

    def publish(self, public=False, wait=False):
        """Publish a snapshot as an image.

        If wait=True, an Image is returned.

        This functionality is currently broken in LXD. Please see
        https://github.com/lxc/lxd/issues/2201 - The implementation
        here is mostly a guess. Once that bug is fixed, we can verify
        that this works, or file a bug to fix it appropriately.
        """
        data = {
            'public': public,
            'source': {
                'type': 'snapshot',
                'name': '{}/{}'.format(self.container.name, self.name),
            }
        }

        response = self.client.api.images.post(json=data)
        if wait:
            operation = self.client.operations.wait_for_operation(
                response.json()['operation'])
            return self.client.images.get(operation.metadata['fingerprint'])
