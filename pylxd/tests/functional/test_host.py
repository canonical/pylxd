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

import unittest

from pylxd import api

class LXDFunctionalTestHost(unittest.TestCase):
    def setUp(self):
        super(LXDFunctionalTestHost, self).setUp()
        self.lxd = api.API()

    def test_host_ping(self):
        self.assertTrue(self.lxd.host_ping())

    def test_host_info(self):
        host = self.lxd.host_info()
        self.assertIsInstance(host, dict)

        self.assertEqual(host['lxd_driver'], 'lxc')
        self.assertEqual(host['lxd_api_compat_level'], 1)
        kernel_version = os.uname()[2]
        self.assertEqual(host['kernel_version'], kernel_version)