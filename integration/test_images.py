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
from integration.testing import create_busybox_image, IntegrationTestCase


class TestImages(IntegrationTestCase):
    """Tests for `Client.images.`"""

    def test_get(self):
        """An image is fetched by fingerprint."""
        fingerprint, _ = self.create_image()
        self.addCleanup(self.delete_image, fingerprint)

        image = self.client.images.get(fingerprint)

        self.assertEqual(fingerprint, image.fingerprint)

    def test_all(self):
        """A list of all images is returned."""
        fingerprint, _ = self.create_image()
        self.addCleanup(self.delete_image, fingerprint)

        images = self.client.images.all()

        self.assertIn(fingerprint, [image.fingerprint for image in images])

    def test_create(self):
        """An image is created."""
        path, fingerprint = create_busybox_image()
        self.addCleanup(self.delete_image, fingerprint)

        with open(path) as f:
            image = self.client.images.create(f.read(), wait=True)

        self.assertEqual(fingerprint, image.fingerprint)


class TestImage(IntegrationTestCase):
    """Tests for Image."""

    def setUp(self):
        super(TestImage, self).setUp()
        fingerprint, _ = self.create_image()
        self.image = self.client.images.get(fingerprint)

    def tearDown(self):
        super(TestImage, self).tearDown()
        self.delete_image(self.image.fingerprint)

    def test_update(self):
        """The image properties are updated."""
        description = 'an description'
        self.image.properties['description'] = description
        self.image.update()

        image = self.client.images.get(self.image.fingerprint)
        self.assertEqual(description, image.properties['description'])

    def test_delete(self):
        """The image is deleted."""
        self.image.delete()

        self.assertRaises(
            NameError, self.client.images.get, self.image.fingerprint)
