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

from ddt import data
from ddt import ddt
import mock
import unittest

from pylxd import api
from pylxd import connection
from pylxd import exceptions

from pylxd.tests import annotated_data
from pylxd.tests import fake_api


@ddt
class LXDUnitTestHost(unittest.TestCase):

    def setUp(self):
        super(LXDUnitTestHost, self).setUp()
        self.lxd = api.API()

    @data(True, False)
    def test_get_host_ping(self, value):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = value
            self.assertEqual(value, self.lxd.host_ping())
            ms.assert_called_once_with('GET', '/1.0')

    def test_get_host_ping_fail(self):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.side_effect = Exception
            self.assertRaises(exceptions.PyLXDException, self.lxd.host_ping)
            ms.assert_called_once_with('GET', '/1.0')

    def test_get_host_info(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_host())
            result = self.lxd.host_info()
            self.assertEqual(result, {
                'lxd_api_compat_level': 1,
                'lxd_trusted_host': True,
                'lxd_backing_fs': 'ext4',
                'lxd_driver': 'lxc',
                'lxd_version': 0.12,
                'lxc_version': '1.1.2',
                'kernel_version': '3.19.0-22-generic',
            })
            ms.assert_called_once_with('GET', '/1.0')

    host_data = (
        ('lxd_api_compat', 1),
        ('lxd_host_trust', True),
        ('lxd_backing_fs', 'ext4'),
        ('lxd_driver', 'lxc'),
        ('lxc_version', '1.1.2'),
        ('lxd_version', 0.12),
        ('kernel_version', '3.19.0-22-generic'),
    )

    @annotated_data(*host_data)
    def test_get_host_data(self, method, expected):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_host())
            result = getattr(self.lxd, 'get_' + method)(data=None)
            self.assertEqual(expected, result)
            ms.assert_called_once_with('GET', '/1.0')

    @annotated_data(*host_data)
    def test_get_host_data_fail(self, method, expected):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.side_effect = exceptions.PyLXDException
            result = getattr(self.lxd, 'get_' + method)(data=None)
            self.assertEqual(None, result)
            ms.assert_called_once_with('GET', '/1.0')
