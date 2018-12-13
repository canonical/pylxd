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


class TestContainer(IntegrationTestCase):
    """Tests for Client.Container."""

    def setUp(self):
        super(TestContainer, self).setUp()
        name = self.create_container()
        self.container = self.client.containers.get(name)

    def tearDown(self):
        super(TestContainer, self).tearDown()
        self.delete_container(self.container.name)

    def test_migrate_running(self):
        """A running container is migrated."""
        from pylxd.client import Client
        first_host = 'https://10.0.3.111:8443/'
        second_host = 'https://10.0.3.222:8443/'

        client1 = Client(endpoint=first_host, verify=False)
        client1.authenticate('password')

        client2 = Client(endpoint=second_host, verify=False)
        client2.authenticate('password')
        an_container = \
            client1.containers.get(self.container.name)
        an_container.start(wait=True)
        an_container.sync()
        an_migrated_container = \
            an_container.migrate(client2, wait=True)

        self.assertEqual(an_container.name,
                         an_migrated_container.name)
        self.assertEqual(client2,
                         an_migrated_container.client)

    def test_migrate_local_client(self):
        """Raise ValueError, cannot migrate from local connection"""
        from pylxd.client import Client

        second_host = 'https://10.0.3.222:8443/'
        client2 =\
            Client(endpoint=second_host, verify=False)
        client2.authenticate('password')

        self.assertRaises(ValueError,
                          self.container.migrate, client2)

    def test_migrate_stopped(self):
        """A stopped container is migrated."""
        from pylxd.client import Client

        first_host = 'https://10.0.3.111:8443/'
        second_host = 'https://10.0.3.222:8443/'

        client1 = \
            Client(endpoint=first_host, verify=False)
        client1.authenticate('password')

        client2 = \
            Client(endpoint=second_host, verify=False)
        client2.authenticate('password')
        an_container = \
            client1.containers.get(self.container.name)
        an_migrated_container = \
            an_container.migrate(client2, wait=True)

        self.assertEqual(an_container.name,
                         an_migrated_container.name)
        self.assertEqual(client2,
                         an_migrated_container.client)
