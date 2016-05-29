import hashlib
import json

from pylxd import exceptions, image
from pylxd.tests import testing


class TestImage(testing.PyLXDTestCase):
    """Tests for pylxd.image.Image."""

    def test_get(self):
        """An image is fetched."""
        fingerprint = hashlib.sha256(b'').hexdigest()
        a_image = image.Image.get(self.client, fingerprint)

        self.assertEqual(fingerprint, a_image.fingerprint)

    def test_get_not_found(self):
        """NotFound is raised when the image isn't found."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
        })

        fingerprint = hashlib.sha256(b'').hexdigest()

        self.assertRaises(
            exceptions.NotFound,
            image.Image.get, self.client, fingerprint)

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

    def test_create_failed(self):
        """If image creation fails, CreateFailed is raised."""
        def create_fail(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'An unknown error',
                'error_code': 500})
        self.add_rule({
            'text': create_fail,
            'method': 'POST',
            'url': r'^http://pylxd.test/1.0/images$',
        })

        self.assertRaises(
            exceptions.CreateFailed,
            image.Image.create, self.client, b'')

    def test_update_partial_objects(self):
        """A partially fetched image can't be pushed."""
        a_image = self.client.images.all()[0]

        self.assertRaises(
            exceptions.ObjectIncomplete,
            a_image.update)

    def test_fetch(self):
        """A partial object is fetched and populated."""
        a_image = self.client.images.all()[0]

        a_image.fetch()

        self.assertEqual(1, a_image.size)

    def test_fetch_notfound(self):
        """A bogus image fetch raises NotFound."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
        })
        fingerprint = hashlib.sha256(b'').hexdigest()

        a_image = image.Image(fingerprint=fingerprint, _client=self.client)

        self.assertRaises(exceptions.NotFound, a_image.fetch)
