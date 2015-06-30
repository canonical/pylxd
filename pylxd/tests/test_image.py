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

class LXDUnitTestImages(unittest.TestCase):
    def setUp(self):
        super(LXDUnitTestImages, self).setUp()
        self.lxd = api.API()

        self.fake_list_images_empty = {
        		"type": "sync",
	        	"status": "Success",
		        "status_code": 200,
		        "metadata": []
	    }

        self.fake_list_images = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": [
                {
                  "aliases": [
                    {
                        "target": "11528ed2-a504-4586-8ab3-14c293f7def3",
                        "description": "11528ed2-a504-4586-8ab3-14c293f7def3",                                                  }
                   ],
                   "architecture": 2,
                   "fingerprint": "875b8cde5f63e61c5de8cbccdcdf1c282f722790393ae86939fc573710f436d8",
                   "filename": "",
                   "properties": {},
                   "public": 0,
                   "size": 64662852,
                   "created_at": 0,
                   "expires_at": 0,
                   "uploaded_at": 1435605945   
                }
            ]
        }

        self.fake_image_upload = {

        }

        def test_list_iamges(self):
            with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
                ms.return_value = ('200', self.fake_list_images_empty)
                self.assertEqual(0, len(self.lxd.image_list()))

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
                ms.return_value = ('200', self.fake_list_images)
                self.assertIsInstance(self.lxd.image_info('875b8cde5f63'), dict)

        def test_image_search(self):
            with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
                ms.return_value = ('200', self.fake_list_images)
                self.assertEquals(1, len(self.lxd.image_search({'arch': 'amd64'})))

        def test_image_upload_date(self):
            with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
                ms.return_value = ('200', self.fake_list_images)
                self.assertEquals('1435605945', self.lxd.image_create_date('875b8cde5f63'))

        def test_image_create_date(self):
            with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
                ms.return_value = ('200', self.fake_list_images)
                self.assertEquals('1435605945', self.lxd.image_upload_date('875b8cde5f63'))

        @mock.patch.object(api.API, 'image_upload')
        def test_image_upload(self, mock_api):
            mock_api.return_value = True
            self.assertTrue(self.lxd.image_upload(data=''))