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

        self.fake_list_images = {
        		"type": "sync",
	        	"status": "Success",
		        "status_code": 200,
		        "metadata": []
	    }

        def test_list_instances(self):
            with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
                ms.return_value = ('200', self.fake_list_images)
                self.assertEqual(0, len(self.lxd.image_list()))

        def test_get_image_defined_fail(self):
            with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
                ms.return_value = False
                self.assertFalse(self.lxd.image_defined('test-image'))

        def test_get_image_defined(self):
             with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
                ms.return_value = True
                self.assertFalse(self.lxd.image_defined('test-image'))
