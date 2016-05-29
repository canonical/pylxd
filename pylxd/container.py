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

    def snapshot(self, name, stateful=False, wait=False):
        """Take a snapshot of the container."""
        response = self._client.api.containers[self.name].snapshots.post(json={
            'name': name, 'stateful': stateful})
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def list_snapshots(self):
        """List all container snapshots."""
        response = self._client.api.containers[self.name].snapshots.get()
        return [snapshot.split('/')[-1]
                for snapshot in response.json()['metadata']]

    def rename_snapshot(self, old, new, wait=False):
        """Rename a snapshot."""
        response = self._client.api.containers[
            self.name].snapshots[old].post(json={'name': new})
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def delete_snapshot(self, name, wait=False):
        """Delete a snapshot."""
        response = self._client.api.containers[
            self.name].snapshots[name].delete()
        if wait:
            self.wait_for_operation(response.json()['operation'])

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
