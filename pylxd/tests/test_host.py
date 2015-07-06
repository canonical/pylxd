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


class LXDUnitTestHost(unittest.TestCase):
    def setUp(self):
        super(LXDUnitTestHost, self).setUp()
        self.lxd = api.API()

        self.fake_host = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": {
                "api_compat": 1,
                "auth": "trusted",
                "config": {},
                "environment": {
                    "backing_fs": "ext4",
                    "driver": "lxc",
                    "kernel_version": "3.19.0-22-generic",
                    "lxc_version": "1.1.2",
                    "lxd_version": "0.12"
                }
            }
        }

    @mock.patch.object(api.API, 'host_ping')
    def test_get_host_ping(self, mock_api):
        mock_api.return_value = True
        self.assertTrue(self.lxd.host_ping())

    @mock.patch.object(api.API, 'host_ping')
    def test_get_host_ping_fail(self, mock_api):
        mock_api.return_value = False
        self.assertFalse(self.lxd.host_ping())

    @mock.patch.object(api.API, 'host_info')
    def test_get_host_info(self, mock_api):
        mock_api.return_value = self.fake_host
        data = self.lxd.host_info()
        self.assertIsInstance(data, dict)

    def test_get_lxd_api_compat(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            data = self.lxd.get_lxd_api_compat(data=None)
            self.assertEqual(data, 1)

    def test_get_lxd_host_trusted(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertTrue(self.lxd.get_lxd_host_trust(data=None))

    def test_get_lxd_host_backing_fs(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertEqual('ext4', self.lxd.get_lxd_backing_fs(data=None))

    def test_get_lxd_driver(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertEqual('lxc', self.lxd.get_lxd_driver(data=None))

    def test_get_lxc_version(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertEqual('1.1.2', self.lxd.get_lxc_version(data=None))

    def test_get_lxd_version(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertEqual(0.12, self.lxd.get_lxd_version(data=None))

    def test_get_kernel_version(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', self.fake_host)
            self.assertEqual('3.19.0-22-generic',
                             self.lxd.get_kernel_version(data=None))
