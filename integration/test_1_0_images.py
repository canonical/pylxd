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


class ImageTestCase(IntegrationTestCase):
    """An Image test case."""

    def setUp(self):
        super(ImageTestCase, self).setUp()
        self.fingerprint, _ = self.create_image()


class Test10ImageExport(ImageTestCase):
    """Tests for /1.0/images/<fingerprint>/export."""

    def test_1_0_images_export(self):
        """Return: dict representing an image properties."""
        response = self.lxd['1.0'].images[self.fingerprint].export.get()

        self.assertEqual(200, response.status_code)


class Test10ImageSecret(ImageTestCase):
    """Tests for /1.0/images/<fingerprint>/secret."""

    def test_1_0_images_secret(self):
        """Return: dict representing an image properties."""
        response = self.lxd['1.0'].images[self.fingerprint].secret.post({
            'name': 'abcdef'
            })

        self.assertEqual(202, response.status_code)


class Test10ImageAliases(IntegrationTestCase):
    """Tests for /1.0/images/aliases."""

    def test_1_0_images_aliases(self):
        """Return: list of URLs for images this server publishes."""
        response = self.lxd['1.0'].images.aliases.get()

        self.assertEqual(200, response.status_code)

    def test_1_0_images_aliases_POST(self):
        """Return: list of URLs for images this server publishes."""
        fingerprint, _ = self.create_image()
        alias = 'test-alias'
        self.addCleanup(self.delete_image, alias)
        response = self.lxd['1.0'].images.aliases.post(json={
            'target': fingerprint,
            'name': alias
            })

        self.assertEqual(200, response.status_code)
