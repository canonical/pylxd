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
from pylxd import exceptions


class NetworkTestCase(IntegrationTestCase):

    def setUp(self):
        super(NetworkTestCase, self).setUp()

        if not self.client.has_api_extension('network'):
            self.skipTest('Required LXD API extension not available!')


class TestNetworks(NetworkTestCase):
    """Tests for `Client.networks.`"""

    def test_get(self):
        """A network is fetched by its name."""
        name = self.create_network()

        self.addCleanup(self.delete_network, name)
        network = self.client.networks.get(name)

        self.assertEqual(name, network.name)

    def test_all(self):
        """All networks are fetched."""
        name = self.create_network()

        self.addCleanup(self.delete_network, name)

        networks = self.client.networks.all()

        self.assertIn(name, [network.name for network in networks])

    def test_create_default_arguments(self):
        """A network is created with default arguments"""
        name = 'eth10'
        network = self.client.networks.create(name=name)
        self.addCleanup(self.delete_network, name)

        self.assertEqual(name, network.name)
        self.assertTrue(network.managed)
        self.assertEqual('bridge', network.type)
        self.assertEqual('', network.description)

    def test_create_with_parameters(self):
        """A network is created with provided arguments"""
        kwargs = {
            'name': 'eth10',
            'config': {
                'ipv4.address': '10.10.10.1/24',
                'ipv4.nat': 'true',
                'ipv6.address': 'none',
                'ipv6.nat': 'false',
            },
            'type': 'bridge',
            'description': 'network description',
        }

        network = self.client.networks.create(**kwargs)
        self.addCleanup(self.delete_network, kwargs['name'])

        self.assertEqual(kwargs['name'], network.name)
        self.assertEqual(kwargs['config'], network.config)
        self.assertEqual(kwargs['type'], network.type)
        self.assertTrue(network.managed)
        self.assertEqual(kwargs['description'], network.description)


class TestNetwork(NetworkTestCase):
    """Tests for `Network`."""

    def setUp(self):
        super(TestNetwork, self).setUp()
        name = self.create_network()
        self.network = self.client.networks.get(name)

    def tearDown(self):
        super(TestNetwork, self).tearDown()
        self.delete_network(self.network.name)

    def test_save(self):
        """A network is updated"""
        self.network.config['ipv4.address'] = '11.11.11.1/24'
        self.network.save()

        network = self.client.networks.get(self.network.name)
        self.assertEqual('11.11.11.1/24', network.config['ipv4.address'])

    def test_rename(self):
        """A network is renamed"""
        name = 'eth20'
        self.addCleanup(self.delete_network, name)

        self.network.rename(name)
        network = self.client.networks.get(name)

        self.assertEqual(name, network.name)

    def test_delete(self):
        """A network is deleted"""
        self.network.delete()

        self.assertRaises(
            exceptions.LXDAPIException,
            self.client.networks.get, self.network.name)
