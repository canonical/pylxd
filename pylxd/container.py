# Copyright (c) 2015 Canonical Ltd
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
import json

import six

from pylxd import base
from pylxd import exceptions
from pylxd import mixin
from pylxd.operation import Operation


class LXDContainer(base.LXDBase):
    # containers:

    def container_list(self):
        (state, data) = self.connection.get_object('GET', '/1.0/containers')
        return [container.split('/1.0/containers/')[-1]
                for container in data['metadata']]

    def container_running(self, container):
        (state, data) = self.connection.get_object(
            'GET',
            '/1.0/containers/%s/state' % container)
        data = data.get('metadata')
        container_running = False
        if data['status'].upper() in ['RUNNING', 'STARTING', 'FREEZING',
                                      'FROZEN', 'THAWED']:
            container_running = True
        return container_running

    def container_init(self, container):
        return self.connection.get_object('POST', '/1.0/containers',
                                          json.dumps(container))

    def container_update(self, container, config):
        return self.connection.get_object('PUT', '/1.0/containers/%s'
                                          % container, json.dumps(config))

    def container_defined(self, container):
        _, data = self.connection.get_object('GET', '/1.0/containers')
        try:
            containers = data["metadata"]
        except KeyError:
            raise exceptions.PyLXDException("no metadata in GET containers?")

        container_url = "/1.0/containers/%s" % container
        for ct in containers:
            if ct == container_url:
                return True
        return False

    def container_state(self, container):
        return self.connection.get_object(
            'GET', '/1.0/containers/%s/state' % container)

    def container_start(self, container, timeout):
        action = {'action': 'start', 'force': True, 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_stop(self, container, timeout):
        action = {'action': 'stop', 'force': True, 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_suspend(self, container, timeout):
        action = {'action': 'freeze', 'force': True, 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_resume(self, container, timeout):
        action = {'action': 'unfreeze', 'force': True, 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_reboot(self, container, timeout):
        action = {'action': 'restart', 'force': True, 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_destroy(self, container):
        return self.connection.get_object('DELETE', '/1.0/containers/%s'
                                          % container)

    def get_container_log(self, container):
        (state, data) = self.connection.get_object(
            'GET', '/1.0/containers/%s?log=true' % container)
        return data['metadata']['log']

    def get_container_config(self, container):
        (state, data) = self.connection.get_object(
            'GET', '/1.0/containers/%s?log=false' % container)
        return data['metadata']

    def get_container_websocket(self, container):
        return self.connection.get_status(
            'GET',
            '/1.0/operations/%s/websocket?secret=%s'
            % (container['operation'], container['fs']))

    def container_info(self, container):
        (state, data) = self.connection.get_object(
            'GET', '/1.0/containers/%s/state' % container)
        return data['metadata']

    def container_migrate(self, container):
        action = {'migration': True}
        (state, data) = self.connection.get_object(
            'POST', '/1.0/containers/%s' % container,
            json.dumps(action))

        return_data = {
            'operation': str(data['operation'].split('/1.0/operations/')[-1]),
        }
        return_data.update(data['metadata'])
        return return_data

    def container_migrate_sync(self, operation_id, container_secret):
        return self.connection.get_ws(
            '/1.0/operations/%s/websocket?secret=%s'
            % (operation_id, container_secret))

    def container_local_copy(self, container):
        return self.connection.get_object(
            'POST',
            '/1.0/containers', json.dumps(container))

    def container_local_move(self, instance, config):
        return self.connection.get_object(
            'POST',
            '/1.0/containers/%s' % instance, json.dumps(config))

    # file operations
    def get_container_file(self, container, filename):
        return self.connection.get_raw(
            'GET',
            '/1.0/containers/%s/files?path=%s' % (container, filename))

    def put_container_file(self, container, src_file,
                           dst_file, uid, gid, mode):
        with open(src_file, 'rb') as f:
            data = f.read()
        return self.connection.get_object(
            'POST',
            '/1.0/containers/%s/files?path=%s' % (container, dst_file),
            body=data,
            headers={'X-LXD-uid': uid, 'X-LXD-gid': gid, 'X-LXD-mode': mode})

    def container_publish(self, container):
        return self.connection.get_object('POST', '/1.0/images',
                                          json.dumps(container))

    # misc operations
    def run_command(self, container, args, interactive, web_sockets, env):
        env = env or {}
        data = {'command': args,
                'interactive': interactive,
                'wait-for-websocket': web_sockets,
                'environment': env}
        return self.connection.get_object('POST', '/1.0/containers/%s/exec'
                                          % container, json.dumps(data))

    # snapshots
    def snapshot_list(self, container):
        (state, data) = self.connection.get_object(
            'GET',
            '/1.0/containers/%s/snapshots' % container)
        return [snapshot.split('/1.0/containers/%s/snapshots/%s/'
                               % (container, container))[-1]
                for snapshot in data['metadata']]

    def snapshot_create(self, container, config):
        return self.connection.get_object('POST',
                                          '/1.0/containers/%s/snapshots'
                                          % container,
                                          json.dumps(config))

    def snapshot_info(self, container, snapshot):
        return self.connection.get_object('GET',
                                          '/1.0/containers/%s/snapshots/%s'
                                          % (container, snapshot))

    def snapshot_rename(self, container, snapshot, config):
        return self.connection.get_object('POST',
                                          '/1.0/containers/%s/snapshots/%s'
                                          % (container, snapshot),
                                          json.dumps(config))

    def snapshot_delete(self, container, snapshot):
        return self.connection.get_object('DELETE',
                                          '/1.0/containers/%s/snapshots/%s'
                                          % (container, snapshot))


class Container(mixin.Waitable, mixin.Marshallable):

    __slots__ = [
        '_client',
        'architecture', 'config', 'creation_date', 'devices', 'ephemeral',
        'expanded_config', 'expanded_devices', 'name', 'profiles', 'status'
        ]

    @classmethod
    def get(cls, client, name):
        response = client.api.containers[name].get()

        if response.status_code == 404:
            raise NameError('No container named "{}"'.format(name))
        container = cls(_client=client, **response.json()['metadata'])
        return container

    @classmethod
    def all(cls, client):
        response = client.api.containers.get()

        containers = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            containers.append(cls(_client=client, name=name))
        return containers

    @classmethod
    def create(cls, client, config, wait=False):
        response = client.api.containers.post(json=config)

        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return cls(name=config['name'])

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def reload(self):
        response = self._client.api.containers[self.name].get()
        if response.status_code == 404:
            raise NameError(
                'Container named "{}" has gone away'.format(self.name))
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
        response = self._client.api.containers[
            self.name].post(json={'name': name})

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
        return self._set_state(
            'start', timeout=timeout, force=force, wait=wait)

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
        return [snapshot.split('/')[-1]
                for snapshot in response.json()['metadata']]

    def rename_snapshot(self, old, new, wait=False):
        response = self._client.api.containers[
            self.name].snapshots[old].post(json={
                'name': new
                })
        if wait:
            self.wait_for_operation(response.json()['operation'])

    def delete_snapshot(self, name, wait=False):
        response = self._client.api.containers[
            self.name].snapshots[name].delete()
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
