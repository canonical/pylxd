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

import datetime
from ddt import ddt
import mock
import unittest

from pylxd import api
from pylxd import connection
from pylxd import exceptions

from pylxd.tests import annotated_data
from pylxd.tests import fake_api


@ddt
class LXDUnitTestImage(unittest.TestCase):

    def setUp(self):
        super(LXDUnitTestImage, self).setUp()
        self.lxd = api.API()

    list_data = (
        ('list',),
        ('search', ({'foo': 'bar'},), ('foo=bar',)),
    )

    @annotated_data(*list_data)
    def test_list_images(self, method, args=(), call_args=()):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_list())
            self.assertEqual(
                ['trusty'], getattr(self.lxd, 'image_' + method)(*args))
            ms.assert_called_once_with('GET', '/1.0/images', *call_args)

    @annotated_data(*list_data)
    def test_list_images_fail(self, method, args=(), call_args=()):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.side_effect = Exception
            self.assertRaises(exceptions.PyLXDException,
                              getattr(self.lxd, 'image_' + method),
                              *args)
            ms.assert_called_once_with('GET', '/1.0/images', *call_args)

    @annotated_data(
        (True, (('200', fake_api.fake_image_info()),)),
        (False, exceptions.APIError("404", 404)),
    )
    def test_image_defined(self, expected, side_effect):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.side_effect = side_effect
            self.assertEqual(expected, self.lxd.image_defined('test-image'))
            ms.assert_called_once_with('GET', '/1.0/images/test-image')

    def test_image_defined_fail(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.side_effect = exceptions.APIError("500", 500)
            self.assertRaises(exceptions.APIError,
                              self.lxd.image_defined, ('test-image',))
            ms.assert_called_once_with('GET', '/1.0/images/test-image')

    def test_image_info(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertIsInstance(self.lxd.image_info('04aac4257341'), dict)

    def test_image_upload_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            dt = (datetime.datetime.fromtimestamp(1435669853)
                  .strftime('%Y-%m-%d %H:%M:%S'))
            self.assertEqual(dt,
                             self.lxd.image_upload_date('04aac4257341',
                                                        data=None))

    def test_image_create_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertEqual('Unknown',
                             self.lxd.image_create_date('04aac4257341',
                                                        data=None))

    def test_image_expire_date(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_image_info())
            self.assertEqual('Unknown',
                             self.lxd.image_expire_date('04aac4257341',
                                                        data=None))

    def test_image_upload(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(self.lxd.image_upload(data='fake'))

    def test_image_export(self):
        with mock.patch.object(connection.LXDConnection, 'get_raw') as ms:
            ms.return_value = 'fake contents'
            self.assertEqual('fake contents', self.lxd.image_export('fake'))

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
