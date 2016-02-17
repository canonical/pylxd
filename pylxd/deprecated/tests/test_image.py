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
from six.moves import builtins
from six.moves import cStringIO
import unittest

from pylxd.deprecated import connection
from pylxd.deprecated import exceptions
from pylxd.deprecated import image

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=('200', fake_api.fake_image_info()))
class LXDAPIImageTestObject(LXDAPITestBase):

    list_data = (
        ('list', (), ()),
        ('search', ({'foo': 'bar'},), ('foo=bar',)),
    )

    @annotated_data(*list_data)
    def test_list_images(self, method, args, call_args, ms):
        ms.return_value = ('200', fake_api.fake_image_list())
        self.assertEqual(
            ['trusty'], getattr(self.lxd, 'image_' + method)(*args))
        ms.assert_called_once_with('GET', '/1.0/images', *call_args)

    @annotated_data(*list_data)
    def test_list_images_fail(self, method, args, call_args, ms):
        ms.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException,
                          getattr(self.lxd, 'image_' + method),
                          *args)
        ms.assert_called_once_with('GET', '/1.0/images', *call_args)

    @annotated_data(
        (True, (('200', fake_api.fake_image_info()),)),
        (False, exceptions.APIError("404", 404)),
    )
    def test_image_defined(self, expected, side_effect, ms):
        ms.side_effect = side_effect
        self.assertEqual(expected, self.lxd.image_defined('test-image'))
        ms.assert_called_once_with('GET', '/1.0/images/test-image')

    @annotated_data(
        ('APIError', exceptions.APIError("500", 500), exceptions.APIError),
        ('PyLXDException', exceptions.PyLXDException,
         exceptions.PyLXDException)
    )
    def test_image_defined_fail(self, tag, side_effect, expected, ms):
        ms.side_effect = side_effect
        self.assertRaises(expected,
                          self.lxd.image_defined, ('test-image',))
        ms.assert_called_once_with('GET', '/1.0/images/test-image')

    def test_image_info(self, ms):
        self.assertEqual({
            'image_upload_date': (datetime.datetime
                                  .fromtimestamp(1435669853)
                                  .strftime('%Y-%m-%d %H:%M:%S')),
            'image_created_date': 'Unknown',
            'image_expires_date': 'Unknown',
            'image_public': False,
            'image_size': '63MB',
            'image_fingerprint': '04aac4257341478b49c25d22cea8a6ce'
                                 '0489dc6c42d835367945e7596368a37f',
            'image_architecture': 'x86_64',
        }, self.lxd.image_info('test-image'))
        ms.assert_called_once_with('GET', '/1.0/images/test-image')

    def test_image_info_fail(self, ms):
        ms.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException,
                          self.lxd.image_info, ('test-image',))
        ms.assert_called_once_with('GET', '/1.0/images/test-image')

    dates_data = (
        ('upload', (datetime.datetime.fromtimestamp(1435669853)
                    .strftime('%Y-%m-%d %H:%M:%S'))),
        ('create', 'Unknown'),
        ('expire', 'Unknown'),
    )

    @annotated_data(*dates_data)
    def test_image_date(self, method, expected, ms):
        self.assertEqual(expected, getattr(
            self.lxd, 'image_{}_date'.format(method))('test-image',
                                                      data=None))
        ms.assert_called_once_with('GET', '/1.0/images/test-image')

    @annotated_data(*dates_data)
    def test_image_date_fail(self, method, expected, ms):
        ms.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException, getattr(
            self.lxd,
            'image_{}_date'.format(method)),
            'test-image',
            data=None)
        ms.assert_called_once_with('GET', '/1.0/images/test-image')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_status', return_value=True)
class LXDAPIImageTestStatus(LXDAPITestBase):
    operations_data = (
        ('delete', 'DELETE', '/test-image', ('test-image',), ()),
        ('update', 'PUT', '/test-image', ('test-image', 'fake',), ('"fake"',)),
        ('rename', 'POST', '/test-image',
         ('test-image', 'fake',), ('"fake"',)),
    )

    @annotated_data(*operations_data)
    def test_image_operations(self, method, http, path, args, call_args, ms):
        self.assertTrue(
            getattr(self.lxd, 'image_' + method)(*args))
        ms.assert_called_once_with(
            http,
            '/1.0/images' + path,
            *call_args
        )

    @annotated_data(*operations_data)
    def test_image_operations_fail(self, method, http, path,
                                   args, call_args, ms):
        ms.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException,
                          getattr(self.lxd, 'image_' + method),
                          *args)
        ms.assert_called_once_with(
            http,
            '/1.0/images' + path,
            *call_args
        )


@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=('200', fake_api.fake_image_info()))
class LXDAPAPIImageTestUpload(LXDAPITestBase):
    @mock.patch.object(builtins, 'open', return_value=cStringIO('fake'))
    def test_image_upload_file(self, mo, ms):
        self.assertTrue(self.lxd.image_upload(path='/fake/path'))
        mo.assert_called_once_with('/fake/path', 'rb')
        ms.assert_called_once_with('POST', '/1.0/images', 'fake', {})


@mock.patch.object(connection.LXDConnection, 'get_raw')
class LXDAPIImageTestRaw(LXDAPITestBase):

    def test_image_export(self, ms):
        ms.return_value = 'fake contents'
        self.assertEqual('fake contents', self.lxd.image_export('fake'))
        ms.assert_called_once_with('GET', '/1.0/images/fake/export')

    def test_image_export_fail(self, ms):
        ms.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException,
                          self.lxd.image_export, 'fake')
        ms.assert_called_once_with('GET', '/1.0/images/fake/export')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=(200, fake_api.fake_image_info()))
class LXDAPIImageInfoTest(unittest.TestCase):

    def setUp(self):
        super(LXDAPIImageInfoTest, self).setUp()
        self.image = image.LXDImage()

    info_list = (
        ('permission', False),
        ('size', 63),
        ('fingerprint', '04aac4257341478b49c25d22cea8a6ce'
                        '0489dc6c42d835367945e7596368a37f'),
        ('architecture', 'x86_64'),
    )

    @annotated_data(*info_list)
    def test_info_no_data(self, method, expected, mc):
        self.assertEqual(expected,
                         (getattr(self.image, 'get_image_' + method)
                          ('test-image', data=None)))
        mc.assert_called_once_with('GET', '/1.0/images/test-image')

    @annotated_data(*info_list)
    def test_info_no_data_fail(self, method, expected, mc):
        mc.side_effect = exceptions.PyLXDException
        self.assertRaises(exceptions.PyLXDException,
                          getattr(self.image, 'get_image_' + method),
                          'test-image',
                          data=None)

    @annotated_data(
        ('permission_true', 'permission', {'public': 0}, False),
        ('permission_false', 'permission', {'public': 1}, True),
        ('size', 'size', {'size': 52428800}, 50),
        ('fingerprint', 'fingerprint', {'fingerprint': 'AAAA'}, 'AAAA'),
        *[('architecture_' + v, 'architecture', {'architecture': k}, v)
          for k, v in image.image_architecture.items()]
    )
    def test_info_data(self, tag, method, metadata, expected, mc):
        self.assertEqual(
            expected, getattr(self.image, 'get_image_' + method)
            ('test-image', data=metadata))
        self.assertFalse(mc.called)

    @annotated_data(
        ('permission', 'permission', {}, KeyError),
        ('size', 'size', {'size': 0}, exceptions.ImageInvalidSize),
        ('size', 'size', {'size': -1}, exceptions.ImageInvalidSize),
        ('fingerprint', 'fingerprint', {}, KeyError),
        ('architecture', 'architecture', {}, KeyError),
        ('architecture_invalid', 'architecture',
         {'architecture': -1}, KeyError)
    )
    def test_info_data_fail(self, tag, method, metadata, expected, mc):
        self.assertRaises(expected,
                          getattr(self.image, 'get_image_' + method),
                          'test-image',
                          data=metadata)
        self.assertFalse(mc.called)
