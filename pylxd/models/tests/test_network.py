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
import re
import unittest
from unittest import mock

import requests_mock

from pylxd import exceptions, models
from pylxd.client import Client
from pylxd.exceptions import LXDAPIExtensionNotAvailable
from pylxd.tests import testing


class TestNetwork(testing.PyLXDTestCase):
    """Tests for pylxd.models.Network."""

    def test_get(self):
        """A network is fetched."""
        name = "eth0"
        an_network = models.Network.get(self.client, name)

        self.assertEqual(name, an_network.name)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown network."""

        def not_found(_, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Network.get, self.client, "eth0"
        )

    def test_get_error(self):
        """LXDAPIException is raised on error."""

        def error(_, context):
            context.status_code = 500
            return json.dumps(
                {
                    "type": "error",
                    "error": "Not found",
                    "error_code": 500,
                }
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Network.get, self.client, "eth0"
        )

    def test_exists(self):
        """True is returned if network exists."""
        name = "eth0"

        self.assertTrue(models.Network.exists(self.client, name))

    def test_not_exists(self):
        """False is returned when network does not exist."""

        def not_found(_, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0$",
            }
        )

        name = "eth0"

        self.assertFalse(models.Network.exists(self.client, name))

    def test_all(self):
        networks = models.Network.all(self.client)

        self.assertEqual(2, len(networks))

    def test_create_with_parameters(self):
        with mock.patch.object(self.client, "assert_has_api_extension"):
            network = models.Network.create(
                self.client,
                name="eth1",
                config={},
                type="bridge",
                description="Network description",
            )

        self.assertIsInstance(network, models.Network)
        self.assertEqual("eth1", network.name)
        self.assertEqual("Network description", network.description)
        self.assertEqual("bridge", network.type)
        self.assertTrue(network.managed)

    def test_create_default(self):
        with mock.patch.object(self.client, "assert_has_api_extension"):
            network = models.Network.create(self.client, "eth1")

        self.assertIsInstance(network, models.Network)
        self.assertEqual("eth1", network.name)
        self.assertEqual("bridge", network.type)
        self.assertTrue(network.managed)

    def test_create_api_not_available(self):
        # Note, by default with the tests, no 'network' extension is available.
        with self.assertRaises(LXDAPIExtensionNotAvailable):
            models.Network.create(
                self.client,
                name="eth1",
                config={},
                type="bridge",
                description="Network description",
            )

    def test_rename(self):
        with mock.patch.object(self.client, "assert_has_api_extension"):
            network = models.Network.get(self.client, "eth0")
            renamed_network = network.rename("eth2")

        self.assertEqual("eth2", renamed_network.name)

    def test_update(self):
        """A network is updated."""
        with mock.patch.object(self.client, "assert_has_api_extension"):
            network = models.Network.get(self.client, "eth0")
            network.config = {}
            network.save()
        self.assertEqual({}, network.config)

    def test_fetch(self):
        """A partial network is synced."""
        network = self.client.networks.all()[1]

        network.sync()

        self.assertEqual("Network description", network.description)

    def test_fetch_not_found(self):
        """LXDAPIException is raised on bogus network fetch."""

        def not_found(_, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0$",
            }
        )
        network = models.Network(self.client, name="eth0")

        self.assertRaises(exceptions.LXDAPIException, network.sync)

    def test_fetch_error(self):
        """LXDAPIException is raised on fetch error."""

        def error(_, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0$",
            }
        )
        network = models.Network(self.client, name="eth0")

        self.assertRaises(exceptions.LXDAPIException, network.sync)

    def test_delete(self):
        """A network is deleted."""
        network = models.Network(self.client, name="eth0")

        network.delete()

    def test_state(self):
        state = {
            "addresses": [
                {
                    "family": "inet",
                    "address": "10.87.252.1",
                    "netmask": "24",
                    "scope": "global",
                },
                {
                    "family": "inet6",
                    "address": "fd42:6e0e:6542:a212::1",
                    "netmask": "64",
                    "scope": "global",
                },
            ],
            "counters": {
                "bytes_received": 0,
                "bytes_sent": 17724,
                "packets_received": 0,
                "packets_sent": 95,
            },
            "hwaddr": "36:19:09:9b:f9:aa",
            "mtu": 1500,
            "state": "up",
            "type": "broadcast",
        }
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": state,
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0/state$",
            }
        )
        network = models.Network.get(self.client, "eth0")
        assert dict(network.state()) == state

    def test_str(self):
        """Network is printed in JSON format."""
        network = models.Network.get(self.client, "eth0")
        self.assertEqual(
            json.loads(str(network)),
            {
                "name": "eth0",
                "description": "Network description",
                "type": "bridge",
                "config": {
                    "ipv4.address": "10.80.100.1/24",
                    "ipv4.nat": "true",
                    "ipv6.address": "none",
                    "ipv6.nat": "false",
                },
                "managed": True,
                "used_by": [],
            },
        )

    def test_repr(self):
        network = models.Network.get(self.client, "eth0")
        self.assertEqual(
            repr(network),
            'Network(config={"ipv4.address": "10.80.100.1/24", "ipv4.nat": '
            '"true", "ipv6.address": "none", "ipv6.nat": "false"}, '
            'description="Network description", name="eth0", type="bridge")',
        )


class TestNetworkForward(testing.PyLXDTestCase):
    """Tests for pylxd.models.NetworkForward."""

    def test_get(self):
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)
        forward = an_network.forwards.get("192.0.2.1")

        self.assertEqual("Forward description", forward.description)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown network."""
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)

        def not_found(_, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0/forwards/192.0.2.1$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException,
            models.NetworkForward.get,
            self.client,
            an_network,
            "192.0.2.1",
        )

    def test_get_error(self):
        """LXDAPIException is raised on error."""
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)

        def error(_, context):
            context.status_code = 500
            return json.dumps(
                {
                    "type": "error",
                    "error": "Not found",
                    "error_code": 500,
                }
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/networks/eth0/forwards/192.0.2.1$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException,
            models.NetworkForward.get,
            self.client,
            an_network,
            "192.0.2.1",
        )

    def test_create(self):
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)
        config = {
            "config": {},
            "description": "Forward description",
            "listen_address": "192.0.2.1",
            "ports": [
                {
                    "description": "Port description",
                    "listen_port": "80",
                    "target_address": "192.0.2.2",
                    "target_port": "80",
                }
            ],
        }

        with mock.patch.object(self.client, "assert_has_api_extension"):
            forward = models.NetworkForward.create(
                self.client,
                network=an_network,
                config=config,
            )

        self.assertIsInstance(forward, models.NetworkForward)
        self.assertEqual("Forward description", forward.description)
        self.assertEqual("192.0.2.1", forward.listen_address)
        self.assertEqual(len(forward.ports), 1)
        self.assertEqual("80", forward.ports[0]["listen_port"])
        self.assertEqual("192.0.2.2", forward.ports[0]["target_address"])
        self.assertEqual("80", forward.ports[0]["target_port"])
        self.assertEqual("Port description", forward.ports[0]["description"])

    def test_update(self):
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)
        config = {
            "config": {},
            "description": "Forward description",
            "listen_address": "192.0.2.1",
            "ports": [
                {
                    "description": "Port description",
                    "listen_port": "80",
                    "target_address": "192.0.2.2",
                    "target_port": "80",
                }
            ],
        }

        with mock.patch.object(self.client, "assert_has_api_extension"):
            forward = models.NetworkForward.create(
                self.client,
                network=an_network,
                config=config,
            )
            forward.description = "Updated"
            forward.save()

        self.assertIsInstance(forward, models.NetworkForward)
        self.assertEqual("Updated", forward.description)
        self.assertEqual("192.0.2.1", forward.listen_address)
        self.assertEqual(len(forward.ports), 1)
        self.assertEqual("80", forward.ports[0]["listen_port"])
        self.assertEqual("192.0.2.2", forward.ports[0]["target_address"])
        self.assertEqual("80", forward.ports[0]["target_port"])
        self.assertEqual("Port description", forward.ports[0]["description"])

    def test_str(self):
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)
        forward = an_network.forwards.get("192.0.2.1")
        self.assertEqual(
            json.loads(str(forward)),
            {
                "config": {},
                "description": "Forward description",
                "location": "eth0",
                "listen_address": "192.0.2.1",
                "ports": [
                    {
                        "description": "Port description",
                        "listen_port": "80",
                        "target_address": "192.0.2.2",
                        "target_port": "80",
                    }
                ],
            },
        )

    def test_repr(self):
        network_name = "eth0"
        an_network = models.Network.get(self.client, network_name)
        forward = an_network.forwards.get("192.0.2.1")
        self.assertEqual(
            repr(forward),
            'NetworkForward(config={}, description="Forward description", listen_address="192.0.2.1",'
            ' location="eth0", ports=[{"description": "Port description", "listen_port": "80",'
            ' "target_address": "192.0.2.2", "target_port": "80"}])',
        )


class TestNetworkAsync(unittest.TestCase):
    """Tests for async operations in pylxd.models.Network.

    Uses requests_mock directly (no mock_services wrapper) to exercise the
    behaviour introduced by the storage_and_network_operations API extension
    (LXD PRs #17955 / #17978) and the corresponding pylxd adaptation (PR #719):
      - Network.create() waits for the async operation before fetching.
      - Network.create() with a synchronous response stays backward-compatible.
      - Network.delete() respects the wait parameter on async responses.
      - Network.put() / Network.patch() are forced to wait when the extension
        is present, regardless of the wait argument passed by the caller.
    """

    _NETWORK_ETH0 = {
        "type": "sync",
        "metadata": {
            "config": {
                "ipv4.address": "10.80.100.1/24",
                "ipv4.nat": "true",
                "ipv6.address": "none",
                "ipv6.nat": "false",
            },
            "name": "eth0",
            "description": "Network description",
            "type": "bridge",
            "managed": True,
            "used_by": [],
        },
    }

    _NETWORK_ETH1 = {
        "type": "sync",
        "metadata": {
            "config": {},
            "name": "eth1",
            "description": "",
            "type": "bridge",
            "managed": True,
            "used_by": [],
        },
    }

    def setUp(self):
        self.mocker = requests_mock.Mocker()
        self.mocker.start()
        self.addCleanup(self.mocker.stop)

        # Required for Client.__init__ and has_api_extension("network") checks.
        self.mocker.get(
            re.compile(r"http://pylxd\.test/1\.0$"),
            json={
                "type": "sync",
                "metadata": {
                    "auth": "trusted",
                    "environment": {"certificate": "an-pem-cert"},
                    "api_extensions": ["network"],
                },
            },
        )
        # Used by Network.create() → cls.get() and by put()/patch() → sync().
        self.mocker.get(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json=self._NETWORK_ETH0,
        )
        self.mocker.get(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth1$"),
            json=self._NETWORK_ETH1,
        )

        self.client = Client(endpoint="http://pylxd.test")

    def _enable_extension(self, *extensions):
        """Directly add API extensions to host_info without an HTTP round-trip."""
        self.client.host_info["api_extensions"].extend(extensions)

    # ------------------------------------------------------------------
    # Network.create() — async handling
    # ------------------------------------------------------------------

    def test_create_async_waits_for_operation(self):
        """Network.create() calls wait_for_operation when the server returns 202."""
        operation_id = "/1.0/operations/net-create-op"
        self.mocker.post(
            re.compile(r"http://pylxd\.test/1\.0/networks$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network = models.Network.create(self.client, "eth1")
            mock_wait.assert_called_once_with(operation_id)

        self.assertIsInstance(network, models.Network)
        self.assertEqual("eth1", network.name)

    def test_create_sync_does_not_wait(self):
        """Network.create() does not call wait_for_operation on a sync 200 response
        (old LXD backward-compatibility)."""
        self.mocker.post(
            re.compile(r"http://pylxd\.test/1\.0/networks$"),
            json={"type": "sync", "metadata": {}},
            status_code=200,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network = models.Network.create(self.client, "eth1")
            mock_wait.assert_not_called()

        self.assertIsInstance(network, models.Network)

    # ------------------------------------------------------------------
    # Network.delete() — async handling
    # ------------------------------------------------------------------

    def test_delete_async_with_wait(self):
        """Network.delete(wait=True) waits for the async operation to complete."""
        operation_id = "/1.0/operations/net-delete-op"
        self.mocker.delete(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network.delete(wait=True)
            mock_wait.assert_called_once_with(operation_id)

    def test_delete_async_without_wait(self):
        """Network.delete(wait=False) does not block on the async operation."""
        operation_id = "/1.0/operations/net-delete-op-nowait"
        self.mocker.delete(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network.delete(wait=False)
            mock_wait.assert_not_called()

    # ------------------------------------------------------------------
    # Network.put() / patch() — extension-forced wait
    # ------------------------------------------------------------------

    def test_put_async_forced_by_extension(self):
        """When storage_and_network_operations is present, Network.put() waits
        for the async operation even when wait=False is passed."""
        self._enable_extension("storage_and_network_operations")
        operation_id = "/1.0/operations/net-put-op"
        self.mocker.put(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            # wait=False must be overridden by the extension being present
            network.put({"config": {}}, wait=False)
            mock_wait.assert_called_once_with(operation_id)

    def test_patch_async_forced_by_extension(self):
        """When storage_and_network_operations is present, Network.patch() waits
        for the async operation even when wait=False is passed."""
        self._enable_extension("storage_and_network_operations")
        operation_id = "/1.0/operations/net-patch-op"
        self.mocker.patch(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            # wait=False must be overridden by the extension being present
            network.patch({"config": {}}, wait=False)
            mock_wait.assert_called_once_with(operation_id)

    def test_put_without_extension_respects_wait_false(self):
        """Without the extension, Network.put(wait=False) does NOT wait."""
        operation_id = "/1.0/operations/net-put-op-noext"
        self.mocker.put(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network.put({"config": {}}, wait=False)
            mock_wait.assert_not_called()

    def test_patch_without_extension_respects_wait_false(self):
        """Without the extension, Network.patch(wait=False) does NOT wait."""
        operation_id = "/1.0/operations/net-patch-op-noext"
        self.mocker.patch(
            re.compile(r"http://pylxd\.test/1\.0/networks/eth0$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )
        network = models.Network(self.client, name="eth0")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network.patch({"config": {}}, wait=False)
            mock_wait.assert_not_called()

    def test_create_extension_forces_wait_even_when_caller_passes_false(self):
        """When storage_and_network_operations is present, Network.create() waits
        for the async operation even when the caller explicitly passes wait=False."""
        self._enable_extension("storage_and_network_operations")
        operation_id = "/1.0/operations/net-create-op-forced"
        self.mocker.post(
            re.compile(r"http://pylxd\.test/1\.0/networks$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            network = models.Network.create(self.client, "eth1", wait=False)
            mock_wait.assert_called_once_with(operation_id)

        self.assertIsInstance(network, models.Network)
        self.assertEqual("eth1", network.name)
