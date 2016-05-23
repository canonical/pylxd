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


class TestContainers(IntegrationTestCase):
    """Tests for `Client.containers`"""

    def test_get(self):
        """A container is fetched by name."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        container = self.client.containers.get(name)

        self.assertEqual(name, container.name)

    def test_all(self):
        """A list of all containers is returned."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        containers = self.client.containers.all()

        self.assertEqual(1, len(containers))
        self.assertEqual(name, containers[0].name)

    def test_create(self):
        """Creates and returns a new container."""
        config = {
            'name': 'an-container',
            'architecture': '2',
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }
        self.addCleanup(self.delete_container, config['name'])

        container = self.client.containers.create(config, wait=True)

        self.assertEqual(config['name'], container.name)


class TestContainer(IntegrationTestCase):
    """Tests for Client.Container."""

    def setUp(self):
        super(TestContainer, self).setUp()
        name = self.create_container()
        self.container = self.client.containers.get(name)

    def tearDown(self):
        super(TestContainer, self).tearDown()
        self.delete_container(self.container.name)

    def test_update(self):
        """The container is updated to a new config."""
        self.container.config['limits.cpu'] = '1'
        self.container.update(wait=True)

        self.assertEqual('1', self.container.config['limits.cpu'])
        container = self.client.containers.get(self.container.name)
        self.assertEqual('1', container.config['limits.cpu'])

    def test_rename(self):
        """The container is renamed."""
        name = 'an-renamed-container'
        self.container.rename(name, wait=True)

        self.assertEqual(name, self.container.name)
        container = self.client.containers.get(name)
        self.assertEqual(name, container.name)

    def test_delete(self):
        """The container is deleted."""
        self.container.delete(wait=True)

        self.assertRaises(
            NameError, self.client.containers.get, self.container.name)

    def test_start_stop(self):
        """The container is started and then stopped."""
        # NOTE: rockstar (15 Feb 2016) - I don't care for the
        # multiple assertions here, but it's a okay-ish way
        # to test what we need.
        self.container.start(wait=True)

        self.assertEqual('Running', self.container.status)
        container = self.client.containers.get(self.container.name)
        self.assertEqual('Running', container.status)

        self.container.stop(wait=True)

        self.assertEqual('Stopped', self.container.status)
        container = self.client.containers.get(self.container.name)
        self.assertEqual('Stopped', container.status)

    def test_snapshot(self):
        """A container snapshot is made, renamed, and deleted."""
        # NOTE: rockstar (15 Feb 2016) - Once again, multiple things
        # asserted in the same test.
        name = 'an-snapshot'
        self.container.snapshot(name, wait=True)

        self.assertEqual([name], self.container.list_snapshots())

        new_name = 'an-other-snapshot'
        self.container.rename_snapshot(name, new_name, wait=True)

        self.assertEqual([new_name], self.container.list_snapshots())

        self.container.delete_snapshot(new_name, wait=True)

        self.assertEqual([], self.container.list_snapshots())

    def test_put_get_file(self):
        """A file is written to the container and then read."""
        filepath = '/tmp/an_file'
        data = 'abcdef'

        retval = self.container.put_file(filepath, data)

        self.assertTrue(retval)

        contents = self.container.get_file(filepath)

        self.assertEqual(data, contents)

    def test_execute(self):
        """A command is executed on the container."""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)

        self.container.execute('ls /')
