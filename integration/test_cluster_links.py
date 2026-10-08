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

# The integration runner sets core.https_address to 127.0.0.1, so a public
# link to the server itself exercises the whole flow without a second server.
SELF_ADDRESS = "127.0.0.1:8443"


class TestClusterLinks(IntegrationTestCase):
    """Tests for `Client.cluster.links`."""

    def setUp(self):
        super().setUp()
        if not self.client.has_api_extension("cluster_links_public"):
            self.skipTest("cluster_links_public extension not available")

    def delete_link(self, name):
        try:
            self.client.cluster.links.get(name).delete()
        except exceptions.NotFound:
            pass

    def test_public_self_link(self):
        """A public link to this server is created, used and removed."""
        name = self.generate_object_name()
        renamed = f"{name}-renamed"
        self.addCleanup(self.delete_link, name)
        self.addCleanup(self.delete_link, renamed)

        fingerprint = self.client.cluster.links.create_pending_public(
            name, SELF_ADDRESS
        )
        self.assertTrue(fingerprint)

        link = self.client.cluster.links.create(
            name, type="public", fingerprint=fingerprint
        )
        self.assertEqual("public", link.type)
        self.assertEqual(SELF_ADDRESS, link.config["volatile.addresses"])
        self.assertIn(link, self.client.cluster.links.all())

        # A public link presents no client certificate, so the remote never
        # reports it as trusted: "Unauthenticated" is the reachable state for
        # public links, "Active" is reserved for authenticated link types.
        member = link.state()["cluster_link_members"][0]
        self.assertEqual(SELF_ADDRESS, member["address"])
        self.assertEqual("Unauthenticated", member["status"])

        link.patch({"description": "patched"})
        self.assertEqual("patched", link.description)

        link.rename(renamed)
        self.assertFalse(self.client.cluster.links.exists(name))
        self.assertTrue(self.client.cluster.links.exists(renamed))

        link.delete()
        self.assertFalse(self.client.cluster.links.exists(renamed))
