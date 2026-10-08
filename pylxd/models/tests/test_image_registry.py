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

from pylxd import exceptions, models
from pylxd.tests import testing

REGISTRIES_URL = "http://pylxd.test/1.0/image-registries"
REGISTRY_URL = f"{REGISTRIES_URL}/my-registry"
WAIT_URL = "http://pylxd.test/1.0/operations/operation-abc/wait"
CONFIG = {"url": "https://images.example.test"}


class TestImageRegistry(testing.PyLXDTestCase):
    """Tests for pylxd.models.ImageRegistry."""

    def enable_extension(self):
        testing.add_api_extension_helper(self, ["image_registries"])

    def requests_to(self, url_prefix, method=None):
        return [
            r
            for r in self.requests_mock.request_history
            if r.url.startswith(url_prefix) and method in (None, r.method)
        ]

    def assert_waited(self, waited):
        """Assert whether the async operation was waited for."""
        self.assertEqual(waited, bool(self.requests_to(WAIT_URL)))

    def test_all(self):
        """All image registries are listed as sparse objects."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.image_registries.all()
        self.enable_extension()

        registries = self.client.image_registries.all()

        self.assertEqual(["ubuntu", "my-registry"], [r.name for r in registries])
        # Only the listing was fetched; the rest is synced on first access.
        self.assertFalse(self.requests_to(REGISTRY_URL))
        self.assertEqual("simplestreams", registries[1].protocol)

    def test_all_empty(self):
        """LXD answers null, not [], when no registry is visible."""
        self.enable_extension()
        self.add_rule(
            {
                "text": json.dumps({"type": "sync", "metadata": None}),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/image-registries$",
            }
        )

        self.assertEqual([], self.client.image_registries.all())

    def test_get(self):
        """An image registry is fetched by name."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.image_registries.get("my-registry")
        self.enable_extension()

        registry = self.client.image_registries.get("my-registry")

        self.assertEqual("my-registry", registry.name)
        self.assertEqual("simplestreams", registry.protocol)
        self.assertTrue(registry.public)
        self.assertFalse(registry.builtin)
        self.assertEqual(CONFIG, registry.config)

    def test_get_builtin(self):
        """Built-in registries report builtin."""
        self.enable_extension()

        self.assertTrue(self.client.image_registries.get("ubuntu").builtin)

    def test_exists(self):
        """exists is True for an existing registry."""
        self.enable_extension()

        self.assertTrue(self.client.image_registries.exists("my-registry"))

    def test_exists_not_found(self):
        """exists is False when LXD answers 404."""
        self.enable_extension()
        self.add_rule(
            {
                "text": json.dumps(
                    {"type": "error", "error": "not found", "error_code": 404}
                ),
                "status_code": 404,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/image-registries/missing$",
            }
        )

        self.assertFalse(self.client.image_registries.exists("missing"))

    def test_create(self):
        """A registry is created without a protocol and the operation waited for."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.image_registries.create("my-registry", CONFIG)
        self.enable_extension()

        registry = self.client.image_registries.create("my-registry", CONFIG)

        self.assertIsInstance(registry, models.ImageRegistry)
        self.assertEqual("my-registry", registry.name)
        self.assertEqual("simplestreams", registry.protocol)
        body = self.last_matching_request("POST", REGISTRIES_URL).json()
        self.assertEqual(
            {"name": "my-registry", "description": "", "config": CONFIG}, body
        )
        # LXD infers the protocol from the config.
        self.assertNotIn("protocol", body)
        self.assert_waited(True)

    def test_create_no_wait(self):
        """With wait=False the operation is not waited for and only the name is known."""
        self.enable_extension()

        registry = self.client.image_registries.create(
            "my-registry", CONFIG, description="d", wait=False
        )

        self.assertEqual("my-registry", registry.name)
        body = self.last_matching_request("POST", REGISTRIES_URL).json()
        self.assertEqual("d", body["description"])
        self.assert_waited(False)
        self.assertFalse(self.requests_to(REGISTRY_URL, "GET"))

    def test_rename(self):
        """A registry is renamed."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.rename("renamed")

        body = self.last_matching_request("POST", REGISTRY_URL).json()
        self.assertEqual({"name": "renamed"}, body)
        self.assertEqual("renamed", registry.name)
        self.assert_waited(True)

    def test_save(self):
        """save sends only the writable fields and waits."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.description = "updated"
        registry.save()

        body = self.last_matching_request("PUT", REGISTRY_URL).json()
        self.assertEqual({"description": "updated", "config": CONFIG}, body)
        self.assert_waited(True)

    def test_put(self):
        """put sends the given body, waits and re-syncs."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")
        put_object = {"description": "d", "config": {"url": "https://o.example.test"}}

        registry.put(put_object)

        body = self.last_matching_request("PUT", REGISTRY_URL).json()
        self.assertEqual(put_object, body)
        self.assert_waited(True)
        self.assertEqual("GET", self.requests_mock.last_request.method)

    def test_patch(self):
        """patch sends the given fields, waits and re-syncs."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.patch({"description": "patched"})

        body = self.last_matching_request("PATCH", REGISTRY_URL).json()
        self.assertEqual({"description": "patched"}, body)
        self.assert_waited(True)
        self.assertEqual("GET", self.requests_mock.last_request.method)

    def test_put_no_wait(self):
        """With wait=False put returns without waiting or re-syncing."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.put({"description": "d", "config": CONFIG}, wait=False)

        self.assertEqual("PUT", self.requests_mock.last_request.method)
        self.assert_waited(False)

    def test_patch_no_wait(self):
        """With wait=False patch returns without waiting or re-syncing."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.patch({"description": "patched"}, wait=False)

        self.assertEqual("PATCH", self.requests_mock.last_request.method)
        self.assert_waited(False)

    def test_delete(self):
        """A registry is deleted."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        registry.delete()

        self.last_matching_request("DELETE", REGISTRY_URL)
        self.assert_waited(True)
        self.assertIsNone(registry.client)

    def test_images(self):
        """The upstream images are returned as plain dicts."""
        self.enable_extension()
        registry = self.client.image_registries.get("my-registry")

        images = registry.images()

        self.assertEqual("abc123", images[0]["fingerprint"])
        self.assertEqual("alpine/edge", images[0]["aliases"][0]["name"])
        self.last_matching_request("GET", f"{REGISTRY_URL}/images")

    def test_images_empty(self):
        """LXD answers null, not [], when the registry has no images."""
        self.enable_extension()
        self.add_rule(
            {
                "text": json.dumps({"type": "sync", "metadata": None}),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/image-registries/my-registry/images$",
            }
        )

        self.assertEqual([], self.client.image_registries.get("my-registry").images())

    def test_builtin_is_immutable(self):
        """LXD rejects changes to built-in registries; pylxd raises."""
        self.enable_extension()
        ubuntu = self.client.image_registries.get("ubuntu")

        for call in (
            ubuntu.save,
            lambda: ubuntu.rename("renamed"),
            lambda: ubuntu.patch({"description": "d"}),
            ubuntu.delete,
        ):
            with self.assertRaises(exceptions.LXDAPIException):
                call()
        self.assertEqual("ubuntu", ubuntu.name)
        self.assertIs(self.client, ubuntu.client)

    def test_instance_methods_require_extension(self):
        """A directly built registry is gated like the class methods."""
        registry = models.ImageRegistry(
            self.client, name="my-registry", description="", config={}
        )

        for call in (
            registry.images,
            lambda: registry.rename("renamed"),
            lambda: registry.patch({"description": "d"}),
            registry.save,
            registry.delete,
        ):
            with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
                call()
        self.assertFalse(self.requests_to(REGISTRY_URL))

    def test_eq(self):
        """Registries compare by name."""
        registry = models.ImageRegistry(self.client, name="my-registry")

        self.assertEqual(
            registry, models.ImageRegistry(self.client, name="my-registry")
        )
        self.assertNotEqual(registry, models.ImageRegistry(self.client, name="ubuntu"))
        self.assertNotEqual(registry, "my-registry")
