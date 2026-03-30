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


class TestInstanceWebSocket(IntegrationTestCase):
    """Tests that exercise WebSocket upgrade paths.

    These tests validate that the WebSocket handshake succeeds against
    LXD regardless of how it handles the ``Origin`` header.  They are
    the regression tests for the breakage introduced when LXD tightened
    its WebSocket ``CheckOrigin`` policy (PR #17950): ws4py sends an
    ``Origin`` header with scheme ``ws+unix://localhost`` whose host
    portion does not match the ``Host: localhost:None`` header it also
    generates for Unix-socket connections, causing LXD to return HTTP
    403 and the operation to time out.
    """

    def setUp(self):
        super().setUp()
        name = self.create_container()
        self.instance = self.client.instances.get(name)
        self.instance.start(wait=True)
        self.addCleanup(self.instance.stop, wait=True)

    def test_execute_websocket_handshake(self):
        """execute() completes the WebSocket upgrade and returns a result.

        This covers the _CommandWebsocketClient (stdout/stderr) and
        _StdinWebsocket paths.  If the Origin header causes HTTP 403 the
        ws4py handshake raises HandshakeError and the call never returns
        (LXD times out with "Timed out waiting for websockets to connect").
        """
        result = self.instance.execute(["echo", "websocket-origin-test"])

        self.assertEqual(0, result.exit_code)
        self.assertEqual("websocket-origin-test\n", result.stdout)

    def test_execute_stdin_websocket_handshake(self):
        """execute() with stdin_payload completes the WebSocket upgrade.

        This specifically exercises the _StdinWebsocket path with a
        non-empty payload, ensuring the stdin WebSocket also connects
        successfully.
        """
        result = self.instance.execute(
            ["cat", "-"], stdin_payload="websocket-stdin-test\n"
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual("websocket-stdin-test\n", result.stdout)


class TestInstances(IntegrationTestCase):
    """Tests for `Client.instances`."""

    def test_get(self):
        """An instance is fetched by name."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instance = self.client.instances.get(name)

        self.assertEqual(name, instance.name)

    def test_all(self):
        """A list of all instances is returned."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all()

        self.assertIn(name, [i.name for i in instances])

    def test_all_recursion_1(self):
        """A list of instances with basic attributes is returned."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all(recursion=1)

        self.assertIn(name, [i.name for i in instances])

    def test_all_recursion_2(self):
        """A list of instances with full state is returned at recursion=2."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all(recursion=2)

        self.assertIn(name, [i.name for i in instances])

    def test_all_selective_recursion_disk(self):
        """Selective recursion with state.disk returns instances correctly.

        Requires the ``instances_state_selective_recursion`` LXD API
        extension.  The test is skipped if the extension is not present.
        """
        if not self.client.has_api_extension("instances_state_selective_recursion"):
            self.skipTest("instances_state_selective_recursion extension not available")

        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all(recursion=2, fields=["state.disk"])

        self.assertIn(name, [i.name for i in instances])

    def test_all_selective_recursion_multiple_fields(self):
        """Selective recursion with multiple fields returns instances correctly.

        Requires the ``instances_state_selective_recursion`` LXD API
        extension.  The test is skipped if the extension is not present.
        """
        if not self.client.has_api_extension("instances_state_selective_recursion"):
            self.skipTest("instances_state_selective_recursion extension not available")

        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all(
            recursion=2, fields=["state.disk", "state.network"]
        )

        self.assertIn(name, [i.name for i in instances])

    def test_all_selective_recursion_empty_fields(self):
        """Selective recursion with empty fields list suppresses all state.

        Requires the ``instances_state_selective_recursion`` LXD API
        extension.  The test is skipped if the extension is not present.
        """
        if not self.client.has_api_extension("instances_state_selective_recursion"):
            self.skipTest("instances_state_selective_recursion extension not available")

        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        instances = self.client.instances.all(recursion=2, fields=[])

        self.assertIn(name, [i.name for i in instances])

    def test_all_selective_recursion_fallback(self):
        """When the extension is absent, fields is ignored and all() succeeds.

        This verifies the graceful-fallback path: passing ``fields`` on a
        server that does not advertise the extension must not raise and must
        still return the full instance list.
        """
        if self.client.has_api_extension("instances_state_selective_recursion"):
            self.skipTest(
                "Server has the extension; fallback path cannot be tested here"
            )

        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        # Should fall back to plain recursion=2 without raising.
        instances = self.client.instances.all(recursion=2, fields=["state.disk"])

        self.assertIn(name, [i.name for i in instances])
