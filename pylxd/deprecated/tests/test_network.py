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

from ddt import ddt
import mock

from pylxd.deprecated import connection

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=(200, fake_api.fake_network()))
class LXDAPINetworkTest(LXDAPITestBase):

    def test_list_networks(self, ms):
        ms.return_value = ('200', fake_api.fake_network_list())
        self.assertEqual(
            ['lxcbr0'],
            self.lxd.network_list())
        ms.assert_called_with('GET',
                              '/1.0/networks')

    def test_network_show(self, ms):
        self.assertEqual({
            'network_name': 'lxcbr0',
            'network_type': 'bridge',
            'network_members': ['/1.0/containers/trusty-1'],
        }, self.lxd.network_show('lxcbr0'))
        ms.assert_called_with('GET',
                              '/1.0/networks/lxcbr0')

    @annotated_data(
        ('name', 'lxcbr0'),
        ('type', 'bridge'),
        ('members', ['/1.0/containers/trusty-1']),
    )
    def test_network_data(self, method, expected, ms):
        self.assertEqual(
            expected, getattr(self.lxd,
                              'network_show_' + method)('lxcbr0'))
        ms.assert_called_with('GET',
                              '/1.0/networks/lxcbr0')
