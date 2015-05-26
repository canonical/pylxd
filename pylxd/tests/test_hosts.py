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

import unittest

from pylxd import api

class LXDTestHost(unittest.TestCase):
    def setUp(self):
        self.api = api.API()

    def test_host_available(self):
        self.assertTrue(self.api.host_ping())

    def test_host_info(self):
        host = self.api.host_info()

        self.assertIn('kernel_version', host)
        self.assertIn('lxd_api_compat_level', host)
        self.assertIn('lxd_trusted_host', host)
        self.assertIn('lxd_backing_fs', host)
        self.assertIn('lxd_driver', host)
        self.assertIn('lxc_version', host)
        self.assertIn('kernel_version', host)

    def test_lxd_api_compat(self):
        host = self.api.get_lxd_api_compat(data=None)
        self.assertEquals(host, 1)

    def test_lxd_trusted_host(self):
        host = self.api.get_lxd_host_trust(data=None)
        self.assertTrue(host)

    def test_lxd_backing_fs(self):
        host = self.api.get_lxd_backing_fs(data=None)
        self.assertIn('ext4', host)

    def test_lxd_driver(self):
        host = self.api.get_lxd_driver(data=None)
        self.assertIn('lxc', host)
