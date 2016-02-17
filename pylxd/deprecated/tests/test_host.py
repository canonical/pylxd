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

from pylxd.deprecated import connection
from pylxd.deprecated import exceptions

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=('200', fake_api.fake_host()))
class LXDAPIHostTestObject(LXDAPITestBase):

    def test_get_host_info(self, ms):
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
    def test_get_host_data(self, method, expected, ms):
        result = getattr(self.lxd, 'get_' + method)(data=None)
        self.assertEqual(expected, result)
        ms.assert_called_once_with('GET', '/1.0')

    @annotated_data(*host_data)
    def test_get_host_data_fail(self, method, expected, ms):
        ms.side_effect = exceptions.PyLXDException
        result = getattr(self.lxd, 'get_' + method)(data=None)
        self.assertEqual(None, result)
        ms.assert_called_once_with('GET', '/1.0')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_status')
class LXDAPIHostTestStatus(LXDAPITestBase):

    @data(True, False)
    def test_get_host_ping(self, value, ms):
        ms.return_value = value
        self.assertEqual(value, self.lxd.host_ping())
        ms.assert_called_once_with('GET', '/1.0')

    def test_get_host_ping_fail(self, ms):
        ms.side_effect = Exception
        self.assertRaises(exceptions.PyLXDException, self.lxd.host_ping)
        ms.assert_called_once_with('GET', '/1.0')
