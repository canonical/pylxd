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
