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
import json

from pylxd import models, exceptions
from pylxd.tests import testing


class TestNetwork(testing.PyLXDTestCase):
    """Tests for pylxd.models.Network."""

    def test_get(self):
        """A network is fetched."""
        name = 'eth0'
        an_network = models.Network.get(self.client, name)

        self.assertEqual(name, an_network.name)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown network."""

        def not_found(_, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})

        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/networks/eth0$',
        })

        self.assertRaises(
            exceptions.LXDAPIException,
            models.Network.get, self.client, 'eth0')

    def test_get_error(self):
        """LXDAPIException is raised on error."""

        def error(_, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 500,
            })

        self.add_rule({
            'text': error,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/networks/eth0$',
        })

        self.assertRaises(
            exceptions.LXDAPIException,
            models.Network.get, self.client, 'eth0')

    def test_exists(self):
        """True is returned if network exists."""
        name = 'eth0'

        self.assertTrue(models.Network.exists(self.client, name))

    def test_not_exists(self):
        """False is returned when network does not exist."""
        def not_found(_, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/networks/eth0$',
        })

        name = 'eth0'

        self.assertFalse(models.Network.exists(self.client, name))

    def test_all(self):
        """A list of all networks are returned."""
        networks = models.Network.all(self.client)

        self.assertEqual(2, len(networks))

    def test_create(self):
        """A new network is created."""
        network = models.Network.create(
            self.client, name='eth1', config={}, type_='bridge',
            description='Network description')

        self.assertIsInstance(network, models.Network)
        self.assertEqual('eth1', network.name)
        self.assertEqual('Network description', network.description)
        self.assertEqual('bridge', network.type)
        self.assertTrue(network.managed)

    def test_rename(self):
        """A network is renamed."""
        network = models.Network.get(self.client, 'eth0')

        renamed_network = network.rename('eth2')

        self.assertEqual('eth2', renamed_network.name)

    def test_update(self):
        """A network is updated."""
        network = models.Network.get(self.client, 'eth0')
        network.config = {}
        network.save()
        self.assertEqual({}, network.config)

    def test_fetch(self):
        """A partial network is synced."""
        network = self.client.networks.all()[1]

        network.sync()

        self.assertEqual('Network description', network.description)

    def test_fetch_not_found(self):
        """LXDAPIException is raised on bogus network fetch."""
        def not_found(_, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/networks/eth0$',
        })
        network = models.Network(self.client, name='eth0')

        self.assertRaises(exceptions.LXDAPIException, network.sync)

    def test_fetch_error(self):
        """LXDAPIException is raised on fetch error."""
        def error(_, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 500})
        self.add_rule({
            'text': error,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/networks/eth0$',
        })
        network = models.Network(self.client, name='eth0')

        self.assertRaises(exceptions.LXDAPIException, network.sync)

    def test_delete(self):
        """A network is deleted."""
        network = models.Network(self.client, name='eth0')

        network.delete()
