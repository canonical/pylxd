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

import time
import unittest

from pylxd import api
from pylxd import exceptions as lxd_exceptions

import utils

class LXDFunctionalTestImage(unittest.TestCase):
    def setUp(self):
        super(LXDFunctionalTestImage, self).setUp()
        self.lxd = api.API()
        self.lxd_remote = api.API(host='images.linuxcontainers.org')

        self.image = {'os': 'ubuntu',
                      'release': 'precise',
                      'arch': 'amd64',
                      'variant': 'default'}

        self.target = utils.upload_image(self.image)

    def test_list_instances(self):
        self.assertEqual(1, len(self.lxd.image_list()))

    #def test_image_defined_fail(self):
    #    image = 'test-dummy'
    #    self.assertFalse(self.lxd.image.image_defined(image))

    #def test_image_defined(self):
    #    self.assertTrue(self.lxd.image_defined(self.target))

    def test_image_search(self):
        data = self.lxd_remote.image_search({'arch': 'amd64'})
        self.assertEqual(64, len(data[0]))

    def TearDown(self):
        utils.delete_image(self.target)
