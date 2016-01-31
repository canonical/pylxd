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
from integration.testing import IntegrationTestCase


class Test10Containers(IntegrationTestCase):
    """Tests for /1.0/containers"""

    def test_1_0_containers(self):
        """Return: list of URLs for containers this server publishes."""
        result = self.lxd['1.0']['containers'].get()

        self.assertCommon(result)
        self.assertEqual(200, result.status_code)

    def test_1_0_containers_POST(self):
        """Return: background operation or standard error."""
        name = self.id().split('.')[-1].replace('_', '')
        machine = {
            'name': name,
            'architecture': 2,
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }
        result = self.lxd['1.0']['containers'].post(json=machine)
        self.addCleanup(self.delete_container, name, enforce=True)

        # self.assertCommon(result)
        self.assertEqual(202, result.status_code)


class ContainerTestCase(IntegrationTestCase):
    """A Container-specific test case."""

    def setUp(self):
        super(ContainerTestCase, self).setUp()
        self.name = self.create_container()

    def tearDown(self):
        super(ContainerTestCase, self).tearDown()
        self.delete_container(self.name)


class Test10Container(ContainerTestCase):
    """Tests for /1.0/containers/<name>"""

    def test10container(self):
        """Return: dict of the container configuration and current state."""
        result = self.lxd['1.0']['containers'][self.name].get()

        self.assertEqual(200, result.status_code)

    def test10container_put(self):
        """Return: background operation or standard error."""
        result = self.lxd['1.0']['containers'][self.name].put(json={
            'config': {'limits.cpu': '1'}
            })

        self.assertEqual(202, result.status_code)

    def test10container_post(self):
        """Return: background operation or standard error."""
        new_name = 'newname'
        result = self.lxd['1.0']['containers'][self.name].post(json={
            'name': new_name,
            })
        self.addCleanup(self.delete_container, new_name, enforce=True)

        self.assertEqual(202, result.status_code)

    def test10container_delete(self):
        """Return: background operation or standard error."""
        result = self.lxd['1.0']['containers'][self.name].delete()

        self.assertEqual(202, result.status_code)


class Test10ContainerState(ContainerTestCase):
    """Tests for /1.0/containers/<name>/state."""

    def test_GET(self):
        """Return: dict representing current state."""
        result = self.lxd['1.0'].containers[self.name].state.get()

        self.assertEqual(200, result.status_code)

    def test_PUT(self):
        """Return: background operation or standard error."""
        result = self.lxd['1.0'].containers[self.name].state.put(json={
            'action': 'freeze',
            'timeout': 30,
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerFiles(ContainerTestCase):
    """Tests for /1.0/containers/<name>/files."""

    def test10containerfiles(self):
        """Return: dict representing current files."""
        result = self.lxd['1.0'].containers[self.name].files.get(params={
            'path': '/bin/sh'
            })

        self.assertEqual(200, result.status_code)

    def test10containerfiles_POST(self):
        """Return: standard return value or standard error."""
        result = self.lxd['1.0'].containers[self.name].files.get(params={
            'path': '/bin/sh'
            }, data='abcdef')

        self.assertEqual(200, result.status_code)


class Test10ContainerSnapshots(ContainerTestCase):
    """Tests for /1.0/containers/<name>/snapshots."""

    def test10containersnapshots(self):
        """Return: list of URLs for snapshots for this container."""
        result = self.lxd['1.0'].containers[self.name].snapshots.get()

        self.assertEqual(200, result.status_code)

    def test10containersnapshots_POST(self):
        """Return: background operation or standard error."""
        result = self.lxd['1.0'].containers[self.name].snapshots.post(json={
            'name': 'test-snapshot',
            'stateful': False
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerSnapshot(ContainerTestCase):
    """Tests for /1.0/containers/<name>/snapshot/<name>."""

    def setUp(self):
        super(Test10ContainerSnapshot, self).setUp()
        result = self.lxd['1.0'].containers[self.name].snapshots.post(json={
            'name': 'test-snapshot', 'stateful': False})
        operation_uuid = result.json()['operation'].split('/')[-1]
        result = self.lxd['1.0'].operations[operation_uuid].wait.get()

    def test10containersnapshot(self):
        """Return: dict representing the snapshot."""
        result = self.lxd['1.0'].containers[self.name].snapshots['test-snapshot'].get()

        self.assertEqual(200, result.status_code)

    def test10containersnapshot_POST(self):
        """Return: dict representing the snapshot."""
        result = self.lxd['1.0'].containers[self.name].snapshots['test-snapshot'].post(json={
            'name': 'test-snapshot.bak-lol'
            })

        self.assertEqual(202, result.status_code)

    def test10containersnapshot_DELETE(self):
        """Return: dict representing the snapshot."""
        result = self.lxd['1.0'].containers[self.name].snapshots['test-snapshot'].delete()

        self.assertEqual(202, result.status_code)


class Test10ContainerExec(ContainerTestCase):
    """Tests for /1.0/containers/<name>/exec."""

    def setUp(self):
        super(Test10ContainerExec, self).setUp()

        result = self.lxd['1.0'].containers[self.name].state.put(json={
            'action': 'start', 'timeout': 30, 'force': True})
        operation_uuid = result.json()['operation'].split('/')[-1]
        self.lxd['1.0'].operations[operation_uuid].wait.get()
        self.addCleanup(self.stop_container)

    def stop_container(self):
        """Stop the container (before deleting it)."""
        result = self.lxd['1.0'].containers[self.name].state.put(json={
            'action': 'stop', 'timeout': 30, 'force': True})
        operation_uuid = result.json()['operation'].split('/')[-1]
        self.lxd['1.0'].operations[operation_uuid].wait.get()

    def test10containerexec(self):
        """Return: background operation + optional websocket information.

        ...or standard error."""
        result = self.lxd['1.0'].containers[self.name]['exec'].post(json={
            'command': ['/bin/bash'],
            'wait-for-websocket': False,
            'interactive': True,
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerLogs(ContainerTestCase):
    """Tests for /1.0/containers/<name>/logs."""

    def test10containerlogs(self):
        """Return: a list of the available log files."""
        result = self.lxd['1.0'].containers[self.name].logs.get()

        self.assertEqual(200, result.status_code)


class Test10ContainerLog(ContainerTestCase):
    """Tests for /1.0/containers/<name>/logs/<logfile>."""

    def setUp(self):
        super(Test10ContainerLog, self).setUp()
        result = self.lxd['1.0'].containers[self.name].logs.get()
        self.log_name = result.json()['metadata'][0]['name']

    def test10containerlog(self):
        """Return: the contents of the log file."""
        result = self.lxd['1.0'].containers[self.name].logs[self.log_name].get()

        self.assertEqual(200, result.status_code)

    def test10containerlog_DELETE(self):
        """Return: the contents of the log file."""
        result = self.lxd['1.0'].containers[self.name].logs[self.log_name].delete()

        self.assertEqual(200, result.status_code)
