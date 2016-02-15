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
            'architecture': 2,
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }
        self.addCleanup(self.delete_container, config['name'])

        container = self.client.containers.create(config, wait=True)

        self.assertEqual(config['name'], container.name)
