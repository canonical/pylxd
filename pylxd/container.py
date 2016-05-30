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
import functools

import six

from pylxd import exceptions, mixin
from pylxd.operation import Operation


class ContainerState():
    def __init__(self, **kwargs):
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)


class Container(mixin.Waitable, mixin.Marshallable):
    """An LXD Container.

    This class is not intended to be used directly, but rather to be used
    via `Client.containers.create`.
    """

    class Snapshots(object):
        def __init__(self, client, container):
            self.get = functools.partial(Snapshot.get, client, container)
            self.all = functools.partial(Snapshot.all, client, container)
            self.create = functools.partial(Snapshot.create, client, container)

    __slots__ = [
        '_client',
        'architecture', 'config', 'created_at', 'devices', 'ephemeral',
        'expanded_config', 'expanded_devices', 'name', 'profiles', 'status'
        ]

    @classmethod
    def get(cls, client, name):
        """Get a container by name."""
        response = client.api.containers[name].get()

        if response.status_code == 404:
            raise exceptions.NotFound(response.json())
        container = cls(_client=client, **response.json()['metadata'])
        return container

    @classmethod
    def all(cls, client):
        """Get all containers.

        Containers returned from this method will only have the name
        set, as that is the only property returned from LXD. If more
        information is needed, `Container.reload` is the method call
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
        response = client.api.containers.post(json=config)

        if response.status_code != 202:
            raise exceptions.CreateFailed(response.json())
        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return cls(name=config['name'], _client=client)

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

        self.snapshots = self.Snapshots(self._client, self)

    def fetch(self):
        """Reload the container information."""
        response = self._client.api.containers[self.name].get()
        if response.status_code == 404:
            raise NameError(
                'Container named "{}" has gone away'.format(self.name))
        for key, value in six.iteritems(response.json()['metadata']):
            setattr(self, key, value)
    # XXX: rockstar (28 Mar 2016) - This method was named improperly
    # originally. It's being kept here for backwards compatibility.
    reload = fetch

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
            self.wait_for_operation(response.json()['operation'])

    def rename(self, name, wait=False):
        """Rename a container."""
        response = self._client.api.containers[
            self.name].post(json={'name': name})

        if wait:
            self.wait_for_operation(response.json()['operation'])
        self.name = name

    def delete(self, wait=False):
        """Delete the container."""
        response = self._client.api.containers[self.name].delete()

        if response.status_code != 202:
            raise RuntimeError('Error deleting instance {}'.format(self.name))
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

    # The next four methods are left for backwards compatibility,
    # but are deprecated for the snapshots manager API.
    def snapshot(self, name, stateful=False, wait=False):  # pragma: no cover
        """Take a snapshot of the container."""
        self.snapshots.create(name, stateful, wait)

    def list_snapshots(self):  # pragma: no cover
        """List all container snapshots."""
        return [s.name for s in self.snapshots.all()]

    def rename_snapshot(self, old, new, wait=False):  # pragma: no cover
        """Rename a snapshot."""
        snapshot = self.snapshots.get(old)
        snapshot.rename(new, wait=wait)

    def delete_snapshot(self, name, wait=False):  # pragma: no cover
        """Delete a snapshot."""
        snapshot = self.snapshots.get(name)
        snapshot.delete()

    def get_file(self, filepath):
        """Get a file from the container."""
        response = self._client.api.containers[self.name].files.get(
            params={'path': filepath})
        if response.status_code == 500:
            # XXX: rockstar (15 Feb 2016) - This should really return a 404.
            # I blame LXD. :)
            raise IOError('Error reading "{}"'.format(filepath))
        return response.content

    def put_file(self, filepath, data):
        """Put a file on the container."""
        response = self._client.api.containers[self.name].files.post(
            params={'path': filepath}, data=data)
        return response.status_code == 200

    def execute(self, commands, environment={}):
        """Execute a command on the container."""
        # XXX: rockstar (15 Feb 2016) - This functionality is limited by
        # design, for now. It needs to grow the ability to return web sockets
        # and perform interactive functions.
        if isinstance(commands, six.string_types):
            commands = [commands]
        response = self._client.api.containers[self.name]['exec'].post(json={
            'command': commands,
            'environment': environment,
            'wait-for-websocket': False,
            'interactive': False,
            })
        operation_id = response.json()['operation']
        self.wait_for_operation(operation_id)


class Snapshot(mixin.Waitable, mixin.Marshallable):
    """A container snapshot."""

    @classmethod
    def get(cls, client, container, name):
        response = client.api.containers[container.name].snapshots[name].get()

        if response.status_code == 404:
            raise exceptions.NotFound(response.json())

        snapshot = cls(
            _client=client, _container=container,
            **response.json()['metadata'])
        # Snapshot names are namespaced in LXD, as container-name/snapshot-name.
        # We hide that implementation detail.
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
            snapshot.wait_for_operation(response.json()['operation'])
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
            self.wait_for_operation(response.json()['operation'])
        self.name = new_name

    def delete(self, wait=False):
        """Delete a snapshot."""
        response = self._client.api.containers[
            self._container.name].snapshots[self.name].delete()

        if response.status_code != 202:
            raise RuntimeError('Error deleting snapshot {}'.format(self.name))
        if wait:
            self.wait_for_operation(response.json()['operation'])
