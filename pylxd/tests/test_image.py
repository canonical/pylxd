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

import mock
import unittest

from pylxd import api
from pylxd import connection

import fake_api

class LXDUnitTestImage(unittest.TestCase):
    def setUp(self):
        super(LXDUnitTestImage, self).setUp()
        self.lxd = api.API()

    def test_list_images(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_list())
            self.assertEqual(1, len(self.lxd.image_list()))

    def test_get_image_defined_fail(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = False
            self.assertFalse(self.lxd.image_defined('test-image'))

    def test_get_image_defined(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertFalse(self.lxd.image_defined('test-image'))

    def test_get_image_info(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertIsInstance(self.lxd.image_info('04aac4257341'), dict)

    def test_image_upload_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertEqual('2015-06-30 09:10:53', 
                            self.lxd.image_upload_date('04aac4257341', data=None))

    def test_image_create_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertEqual('Unknown',
                            self.lxd.image_create_date('04aac4257341', data=None))

    def test_image_expire_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertEqual('Unknown',
                            self.lxd.image_expire_date('04aac4257341', data=None))

    def test_image_delete(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(self.lxd.image_delete('fake'))

    def test_image_update(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(self.lxd.image_update('fake'))

    def test_image_rename(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(self.lxd.image_rename('fake'))