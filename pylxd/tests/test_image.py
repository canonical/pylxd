# Copyright (c) 2015 Canonical Ltd
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

import os
import hashlib

import unittest

from pylxd import client

TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, '..', '..', '..'))
IMAGE = os.path.join(ROOTDIR, 'images', 'lxd.tar.xz')

class LXDTestHost(unittest.TestCase):
    def setUp(self):
        self.client = client.Client()

    def test_image_upload_and_delete(self):
        image = IMAGE
        self.assertTrue(self.client.image_upload(image, image.split('/')[-1]))

        with open(image, "rb") as fd:
            fingerprint = hashlib.sha256(fd.read()).hexdigest()
            self.assertTrue(self.client.image_delete(fingerprint))

    def test_list_images(self):
        self.assertEqual(0, len(self.client.image_list()))

    def test_list_images_with_key(self):
        self._image_upload()
        params = {'architecture': 'x86_64'}
        self.assertEquals(1, len(self.client.image_search(params)))
        self._image_delete()

    def test_image_info(self):
        self._image_upload()

        local_img = IMAGE
        image = self.client.image_info(local_img)

        self.assertIn('image_upload_date', image)
        self.assertIn('image_created_date', image)
        self.assertIn('image_expires_date', image)
        self.assertIn('image_public', image)
        self.assertIn('image_size', image)
        self.assertIn('image_fingerprint', image)
        self.assertIn('image_architecture', image)

        self._image_delete()

    def _image_upload(self):
        image = IMAGE
        self.client.image_upload(image, image.split('/')[-1])

    def _image_delete(self):
        image = IMAGE
        with open(image, "rb") as fd:
            fingerprint = hashlib.sha256(fd.read()).hexdigest()
            self.client.image_delete(fingerprint)