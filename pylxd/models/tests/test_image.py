import hashlib
import json
import warnings
from io import StringIO
from unittest import mock

from pylxd import exceptions, models
from pylxd.tests import testing

FINGERPRINT = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
IMAGES_URL = "http://pylxd.test/1.0/images"
IMAGES2_URL = "http://pylxd2.test/1.0/images"


class TestImage(testing.PyLXDTestCase):
    """Tests for pylxd.models.Image."""

    def test_get(self):
        """An image is fetched."""
        fingerprint = hashlib.sha256(b"").hexdigest()
        a_image = models.Image.get(self.client, fingerprint)

        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_get_not_found(self):
        """LXDAPIException is raised when the image isn't found."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )

        fingerprint = hashlib.sha256(b"").hexdigest()

        self.assertRaises(
            exceptions.LXDAPIException, models.Image.get, self.client, fingerprint
        )

    def test_get_error(self):
        """LXDAPIException is raised on error."""

        def error(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )

        fingerprint = hashlib.sha256(b"").hexdigest()

        self.assertRaises(
            exceptions.LXDAPIException, models.Image.get, self.client, fingerprint
        )

    def test_get_by_alias(self):
        fingerprint = hashlib.sha256(b"").hexdigest()

        a_image = models.Image.get_by_alias(self.client, "an-alias")

        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_exists(self):
        """An image is fetched."""
        fingerprint = hashlib.sha256(b"").hexdigest()

        self.assertTrue(models.Image.exists(self.client, fingerprint))

    def test_eq_with_unrelated_type_returns_not_implemented(self):
        """Image.__eq__ should return NotImplemented for unrelated types."""
        fingerprint = hashlib.sha256(b"").hexdigest()
        img = models.Image(self.client, fingerprint=fingerprint)
        self.assertIs(img.__eq__(object()), NotImplemented)

    def test_exists_by_alias(self):
        """An image is fetched."""
        self.assertTrue(models.Image.exists(self.client, "an-alias", alias=True))

    def test_not_exists(self):
        """LXDAPIException is raised when the image isn't found."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )

        fingerprint = hashlib.sha256(b"").hexdigest()

        self.assertFalse(models.Image.exists(self.client, fingerprint))

    def test_all(self):
        """A list of all images is returned."""
        images = models.Image.all(self.client)

        self.assertEqual(1, len(images))

    def test_create(self):
        """An image is created."""
        fingerprint = hashlib.sha256(b"").hexdigest()
        a_image = models.Image.create(self.client, b"", public=True)

        self.assertIsInstance(a_image, models.Image)
        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_create_with_metadata(self):
        """An image with metadata is created."""
        fingerprint = hashlib.sha256(b"").hexdigest()
        a_image = models.Image.create(self.client, b"", metadata=b"", public=True)

        self.assertIsInstance(a_image, models.Image)
        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_create_with_metadata_streamed(self):
        """An image with metadata is created."""
        fingerprint = hashlib.sha256(b"").hexdigest()
        a_image = models.Image.create(
            self.client, StringIO(""), metadata=StringIO(""), public=True
        )

        self.assertIsInstance(a_image, models.Image)
        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_update(self):
        """An image is updated."""
        a_image = self.client.images.all()[0]
        a_image.sync()

        a_image.save()

    def test_fetch(self):
        """A partial object is fetched and populated."""
        a_image = self.client.images.all()[0]

        a_image.sync()

        self.assertEqual(1, a_image.size)

    def test_fetch_notfound(self):
        """A bogus image fetch raises LXDAPIException."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )
        fingerprint = hashlib.sha256(b"").hexdigest()

        a_image = models.Image(self.client, fingerprint=fingerprint)

        self.assertRaises(exceptions.LXDAPIException, a_image.sync)

    def test_fetch_error(self):
        """A 500 error raises LXDAPIException."""

        def not_found(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )
        fingerprint = hashlib.sha256(b"").hexdigest()

        a_image = models.Image(self.client, fingerprint=fingerprint)

        self.assertRaises(exceptions.LXDAPIException, a_image.sync)

    def test_delete(self):
        """An image is deleted."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        a_image = self.client.images.all()[0]

        a_image.delete(wait=True)

    def test_export(self):
        """An image is exported."""
        expected = "e2943f8d0b0e7d5835f9533722a6e25f669acb8980daee378b4edb44da212f51"
        a_image = self.client.images.all()[0]

        data = a_image.export()
        data_sha = hashlib.sha256(data.read()).hexdigest()

        self.assertEqual(expected, data_sha)

    def test_export_not_found(self):
        """LXDAPIException is raised on export of bogus image."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/export$",
            }
        )
        a_image = self.client.images.all()[0]

        self.assertRaises(exceptions.LXDAPIException, a_image.export)

    def test_export_error(self):
        """LXDAPIException is raised on API error."""

        def error(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "LOLOLOLOL", "error_code": 500}
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/export$",
            }
        )
        a_image = self.client.images.all()[0]

        self.assertRaises(exceptions.LXDAPIException, a_image.export)

    def test_add_alias(self):
        """Try to add an alias."""
        a_image = self.client.images.all()[0]
        a_image.add_alias("lol", "Just LOL")

        aliases = [a["name"] for a in a_image.aliases]
        self.assertTrue("lol" in aliases, "Image didn't get updated.")

    def test_add_alias_duplicate(self):
        """Adding a alias twice should raise an LXDAPIException."""

        def error(request, context):
            context.status_code = 409
            return json.dumps(
                {"type": "error", "error": "already exists", "error_code": 409}
            )

        self.add_rule(
            {
                "text": error,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/images/aliases$",
            }
        )

        a_image = self.client.images.all()[0]

        self.assertRaises(
            exceptions.LXDAPIException, a_image.add_alias, "lol", "Just LOL"
        )

    def test_remove_alias(self):
        """Try to remove an-alias."""
        a_image = self.client.images.all()[0]
        a_image.delete_alias("an-alias")

        self.assertEqual(0, len(a_image.aliases), "Alias didn't get deleted.")

    def test_remove_alias_error(self):
        """Try to remove an non existant alias."""

        def error(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": error,
                "method": "DELETE",
                "url": r"^http://pylxd.test/1.0/images/aliases/lol$",
            }
        )

        a_image = self.client.images.all()[0]
        self.assertRaises(exceptions.LXDAPIException, a_image.delete_alias, "lol")

    def test_remove_alias_not_in_image(self):
        """Try to remove an alias which is not in the current image."""
        a_image = self.client.images.all()[0]
        a_image.delete_alias("b-alias")

    def test_copy(self):
        """Try to copy an image to another LXD instance."""
        from pylxd.client import Client

        a_image = self.client.images.all()[0]

        client2 = Client(endpoint="http://pylxd2.test")
        copied_image = a_image.copy(client2, wait=True)
        self.assertEqual(a_image.fingerprint, copied_image.fingerprint)
        # The legacy body names this server and pins its certificate.
        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertEqual(
            {
                "type": "image",
                "mode": "pull",
                "server": "http://pylxd.test",
                "protocol": "lxd",
                "fingerprint": FINGERPRINT,
                "secret": "abcdefg",
                "certificate": "an-pem-cert",
            },
            body["source"],
        )

    def test_copy_public(self):
        """Try to copy a public image."""
        from pylxd.client import Client

        def image_get(request, context):
            context.status_code = 200
            return json.dumps(
                {
                    "type": "sync",
                    "metadata": {
                        "aliases": [
                            {
                                "name": "an-alias",
                                "fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                            }
                        ],
                        "architecture": "x86_64",
                        "cached": False,
                        "filename": "a_image.tar.bz2",
                        "fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "public": True,
                        "properties": {},
                        "size": 1,
                        "auto_update": False,
                        "created_at": "1983-06-16T02:42:00Z",
                        "expires_at": "1983-06-16T02:42:00Z",
                        "last_used_at": "1983-06-16T02:42:00Z",
                        "uploaded_at": "1983-06-16T02:42:00Z",
                    },
                }
            )

        self.add_rule(
            {
                "text": image_get,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$",
            }
        )

        a_image = self.client.images.all()[0]
        self.assertTrue(a_image.public)

        client2 = Client(endpoint="http://pylxd2.test")
        copied_image = a_image.copy(client2, wait=True)
        self.assertEqual(a_image.fingerprint, copied_image.fingerprint)
        # A public image needs neither a secret nor a certificate.
        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertNotIn("secret", body["source"])
        self.assertNotIn("certificate", body["source"])

    def test_copy_no_wait(self):
        """Try to copy and don't wait."""
        from pylxd.client import Client

        a_image = self.client.images.all()[0]

        client2 = Client(endpoint="http://pylxd2.test")
        a_image.copy(client2, public=False, auto_update=False)

    def test_create_from_simplestreams(self):
        """Without image_registries the simplestreams source is not deprecated."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            image = self.client.images.create_from_simplestreams(
                "https://cloud-images.ubuntu.com/releases", "trusty/amd64"
            )

        self.assertEqual(FINGERPRINT, image.fingerprint)
        self.assertFalse([w for w in caught if w.category is DeprecationWarning])
        body = self.last_matching_request("POST", IMAGES_URL).json()
        self.assertEqual("simplestreams", body["source"]["protocol"])

    def test_create_from_simplestreams_warns_with_extension(self):
        """With image_registries the simplestreams source is deprecated."""
        testing.add_api_extension_helper(self, ["image_registries"])

        with self.assertWarns(DeprecationWarning):
            image = self.client.images.create_from_simplestreams(
                "https://cloud-images.ubuntu.com/releases", "trusty/amd64"
            )

        self.assertEqual(FINGERPRINT, image.fingerprint)
        # The request itself is unchanged.
        body = self.last_matching_request("POST", IMAGES_URL).json()
        self.assertEqual(
            {
                "type": "image",
                "mode": "pull",
                "server": "https://cloud-images.ubuntu.com/releases",
                "protocol": "simplestreams",
                "fingerprint": "trusty/amd64",
            },
            body["source"],
        )

    def test_create_from_url(self):
        """create_from_url is deprecated but still sends the request."""
        with self.assertWarns(DeprecationWarning):
            image = self.client.images.create_from_url("https://dl.stgraber.org/lxd")

        self.assertEqual(FINGERPRINT, image.fingerprint)
        body = self.last_matching_request("POST", IMAGES_URL).json()
        self.assertEqual("url", body["source"]["type"])

    def test_create_from_registry(self):
        """An image is copied from an image registry."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.images.create_from_registry("images", "alpine/edge")
        testing.add_api_extension_helper(self, ["image_registries"])

        image = self.client.images.create_from_registry(
            "images", "alpine/edge", public=True, copy_aliases=True
        )

        self.assertEqual(FINGERPRINT, image.fingerprint)
        body = self.last_matching_request("POST", IMAGES_URL).json()
        self.assertEqual(
            {
                "public": True,
                "auto_update": False,
                "source": {
                    "type": "image",
                    "mode": "pull",
                    "image_registry": "images",
                    "fingerprint": "alpine/edge",
                    "copy_aliases": True,
                },
            },
            body,
        )

    def test_create_from_registry_image_type(self):
        """image_type is sent only when given."""
        testing.add_api_extension_helper(self, ["image_registries"])

        self.client.images.create_from_registry(
            "images", "alpine/edge", image_type="virtual-machine"
        )

        body = self.last_matching_request("POST", IMAGES_URL).json()
        self.assertEqual("virtual-machine", body["source"]["image_type"])

    def test_copy_registry(self):
        """A private image is copied through a registry on the destination."""
        from pylxd.client import Client

        a_image = self.client.images.all()[0]
        client2 = Client(endpoint="http://pylxd2.test")
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_image.copy(client2, image_registry="source-lxd")
        client2.host_info["api_extensions"].append("image_registries")

        copied_image = a_image.copy(
            client2, wait=True, image_registry="source-lxd", copy_aliases=True
        )

        self.assertEqual(a_image.fingerprint, copied_image.fingerprint)
        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertEqual(
            {
                "type": "image",
                "mode": "pull",
                "image_registry": "source-lxd",
                "fingerprint": FINGERPRINT,
                "copy_aliases": True,
                "secret": "abcdefg",
            },
            body["source"],
        )

    def test_copy_registry_public_image(self):
        """A public image needs no secret, and its project is passed on."""
        from pylxd.client import Client

        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": {
                        "fingerprint": FINGERPRINT,
                        "public": True,
                        "project": "p1",
                        "aliases": [],
                        "properties": {},
                        "filename": "a_image.tar.bz2",
                        "auto_update": False,
                    },
                },
                "method": "GET",
                "url": rf"^{IMAGES_URL}/{FINGERPRINT}$",
            }
        )
        a_image = self.client.images.get(FINGERPRINT)
        client2 = Client(endpoint="http://pylxd2.test")
        client2.host_info["api_extensions"].append("image_registries")

        a_image.copy(client2, image_registry="source-lxd")

        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertEqual(
            {
                "type": "image",
                "mode": "pull",
                "image_registry": "source-lxd",
                "fingerprint": FINGERPRINT,
                "copy_aliases": False,
                "project": "p1",
            },
            body["source"],
        )

    def test_copy_copy_aliases(self):
        """copy_aliases is gated and sent with the legacy body too."""
        from pylxd.client import Client

        a_image = self.client.images.all()[0]
        client2 = Client(endpoint="http://pylxd2.test")
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_image.copy(client2, copy_aliases=True)
        client2.host_info["api_extensions"].append("image_registries")

        a_image.copy(client2, copy_aliases=True)

        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertTrue(body["source"]["copy_aliases"])
        self.assertEqual("http://pylxd.test", body["source"]["server"])
        self.assertEqual("an-pem-cert", body["source"]["certificate"])

    def test_copy_copy_aliases_public_image(self):
        """The legacy body with copy_aliases carries the certificate even for
        a public image: servers with image_registries match it to a registry's
        cluster link by certificate."""
        from pylxd.client import Client

        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": {
                        "fingerprint": FINGERPRINT,
                        "public": True,
                        "aliases": [],
                        "properties": {},
                        "filename": "a_image.tar.bz2",
                        "auto_update": False,
                    },
                },
                "method": "GET",
                "url": rf"^{IMAGES_URL}/{FINGERPRINT}$",
            }
        )
        a_image = self.client.images.get(FINGERPRINT)
        client2 = Client(endpoint="http://pylxd2.test")
        client2.host_info["api_extensions"].append("image_registries")

        a_image.copy(client2, copy_aliases=True)

        body = self.last_matching_request("POST", IMAGES2_URL).json()
        self.assertTrue(body["source"]["copy_aliases"])
        self.assertEqual("an-pem-cert", body["source"]["certificate"])
        self.assertNotIn("secret", body["source"])

    def test_eq_same_fingerprint_no_project(self):
        """Two images with same fingerprint and no project are equal."""
        fp = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        a = models.Image(self.client, fingerprint=fp)
        b = models.Image(self.client, fingerprint=fp)
        self.assertEqual(a, b)

    def test_eq_different_project(self):
        """Two images with same fingerprint but different projects differ."""
        fp = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        a = models.Image(self.client, fingerprint=fp, project="p1")
        b = models.Image(self.client, fingerprint=fp, project="p2")
        self.assertNotEqual(a, b)

    def test_eq_does_not_trigger_sync(self):
        """__eq__ must not call sync() when project is unset."""
        fp = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        a = models.Image(self.client, fingerprint=fp)
        b = models.Image(self.client, fingerprint=fp)
        with mock.patch.object(models.Image, "sync") as mock_sync:
            result = a == b
            self.assertTrue(result)
            mock_sync.assert_not_called()
