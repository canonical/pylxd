import hashlib

from pylxd import image
from pylxd.tests import testing


class TestImage(testing.PyLXDTestCase):
    """Tests for pylxd.image.Image."""

    def test_all(self):
        """A list of all images is returned."""
        images = image.Image.all(self.client)

        self.assertEqual(1, len(images))

    def test_create(self):
        """An image is created."""
        fingerprint = hashlib.sha256(b'').hexdigest()
        a_image = image.Image.create(self.client, b'')

        self.assertIsInstance(a_image, image.Image)
        self.assertEqual(fingerprint, a_image.fingerprint)
