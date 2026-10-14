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

BUILTIN_REGISTRIES = {
    "images",
    "ubuntu",
    "ubuntu-daily",
    "ubuntu-minimal",
    "ubuntu-minimal-daily",
}
SIMPLESTREAMS_URL = "https://images.lxd.canonical.com"
# The integration runner sets core.https_address to 127.0.0.1, so a public
# link to the server itself backs an lxd registry without a second server.
SELF_ADDRESS = "127.0.0.1:8443"


class TestImageRegistries(IntegrationTestCase):
    """Tests for `Client.image_registries`."""

    def setUp(self):
        super().setUp()
        if not self.client.has_api_extension("image_registries"):
            self.skipTest("image_registries extension not available")

    def delete_registry(self, name):
        try:
            self.client.image_registries.get(name).delete()
        except exceptions.NotFound:
            pass

    def delete_link(self, name):
        try:
            self.client.cluster.links.get(name).delete()
        except exceptions.NotFound:
            pass

    def create_registry(self, config):
        name = self.generate_object_name()
        self.addCleanup(self.delete_registry, name)
        return self.client.image_registries.create(name, config)

    def test_builtin_registries(self):
        """The built-in registries are listed and immutable."""
        names = {r.name for r in self.client.image_registries.all()}
        self.assertLessEqual(BUILTIN_REGISTRIES, names)

        ubuntu = self.client.image_registries.get("ubuntu")
        self.assertTrue(ubuntu.builtin)
        self.assertTrue(ubuntu.public)
        self.assertEqual("simplestreams", ubuntu.protocol)

        with self.assertRaises(exceptions.LXDAPIException):
            ubuntu.save()
        with self.assertRaises(exceptions.LXDAPIException):
            ubuntu.rename("ubuntu-renamed")
        with self.assertRaises(exceptions.LXDAPIException):
            ubuntu.delete()
        self.assertTrue(self.client.image_registries.exists("ubuntu"))

    def test_reserved_name(self):
        """LXD refuses the reserved registry names."""
        self.addCleanup(self.delete_registry, "builtin")

        with self.assertRaises(exceptions.LXDAPIException):
            self.client.image_registries.create("builtin", {"url": SIMPLESTREAMS_URL})
        self.assertFalse(self.client.image_registries.exists("builtin"))

    def test_lifecycle(self):
        """A simplestreams registry is created, changed, renamed and removed."""
        registry = self.create_registry({"url": SIMPLESTREAMS_URL})
        name = registry.name
        renamed = f"{name}-renamed"
        self.addCleanup(self.delete_registry, renamed)

        self.assertEqual("simplestreams", registry.protocol)
        self.assertFalse(registry.builtin)
        self.assertEqual(SIMPLESTREAMS_URL, registry.config["url"])
        self.assertIn(registry, self.client.image_registries.all())

        registry.patch({"description": "patched"})
        self.assertEqual("patched", registry.description)

        registry.description = "saved"
        registry.save()
        self.assertEqual("saved", self.client.image_registries.get(name).description)

        registry.rename(renamed)
        self.assertFalse(self.client.image_registries.exists(name))
        self.assertTrue(self.client.image_registries.exists(renamed))

        registry.delete()
        self.assertFalse(self.client.image_registries.exists(renamed))

    def test_images(self):
        """The built-in images registry lists upstream images (network)."""
        images = self.client.image_registries.get("images").images()

        self.assertTrue(images)
        self.assertIn("fingerprint", images[0])

    def create_self_link_registry(self):
        """Create an lxd registry over a public cluster link to this server."""
        if not self.client.has_api_extension("cluster_links_public"):
            self.skipTest("cluster_links_public extension not available")
        link_name = self.generate_object_name()
        self.addCleanup(self.delete_link, link_name)
        fingerprint = self.client.cluster.links.create_pending_public(
            link_name, SELF_ADDRESS
        )
        link = self.client.cluster.links.create(
            link_name, type="public", fingerprint=fingerprint
        )
        registry = self.create_registry(
            {"cluster": link_name, "source_project": "default"}
        )
        return link, registry

    def test_lxd_registry_over_self_link(self):
        """An lxd registry over a public link to this server lists its images."""
        link, registry = self.create_self_link_registry()
        self.assertEqual("lxd", registry.protocol)
        self.assertTrue(registry.public)

        image_fingerprint, _ = self.create_image()
        self.assertIn(
            image_fingerprint, [image["fingerprint"] for image in registry.images()]
        )

        # The link is in use by the registry.
        with self.assertRaises(exceptions.LXDAPIException):
            link.delete()
        self.assertTrue(self.client.cluster.links.exists(link.name))

        registry.delete()
        link.delete()
        self.assertFalse(self.client.cluster.links.exists(link.name))

    def test_create_from_registry(self):
        """An image is copied from the built-in images registry (network)."""
        image = self.client.images.create_from_registry("images", "alpine/edge")
        self.addCleanup(self.delete_image, image.fingerprint)

        self.assertTrue(self.client.images.exists(image.fingerprint))

    def test_create_from_registry_lxd_protocol(self):
        """An image is copied through an lxd registry by fingerprint."""
        _, registry = self.create_self_link_registry()
        fingerprint, _ = self.create_image()

        image = self.client.images.create_from_registry(registry.name, fingerprint)

        self.assertEqual(fingerprint, image.fingerprint)

    def test_instance_from_registry(self):
        """An instance is created from an alias in an lxd registry."""
        _, registry = self.create_self_link_registry()
        _, alias = self.create_image()
        name = self.generate_object_name()
        self.addCleanup(self.delete_container, name)

        instance = self.client.instances.create(
            {
                "name": name,
                "source": {
                    "type": "image",
                    "image_registry": registry.name,
                    "alias": alias,
                },
            },
            wait=True,
        )

        self.assertEqual(name, instance.name)
