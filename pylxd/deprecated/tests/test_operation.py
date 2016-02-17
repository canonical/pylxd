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

from pylxd.deprecated import connection

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=(200, fake_api.fake_operation()))
class LXDAPIOperationTestObject(LXDAPITestBase):

    def test_list_operations(self, ms):
        ms.return_value = ('200', fake_api.fake_operation_list())
        self.assertEqual(
            ['/1.0/operations/1234'],
            self.lxd.list_operations())
        ms.assert_called_with('GET',
                              '/1.0/operations')

    def test_operation_info(self, ms):
        ms.return_value = ('200', fake_api.fake_operation())
        self.assertEqual(
            ms.return_value, self.lxd.operation_info('/1.0/operations/1234'))
        ms.assert_called_with('GET',
                              '/1.0/operations/1234')

    @annotated_data(
        ('create_time',
         datetime.datetime.utcfromtimestamp(1433876844)
         .strftime('%Y-%m-%d %H:%M:%S')),
        ('update_time',
         datetime.datetime.utcfromtimestamp(1433876843)
         .strftime('%Y-%m-%d %H:%M:%S')),
        ('status', 'Running'),
    )
    def test_operation_show(self, method, expected, ms):
        call = getattr(self.lxd, 'operation_show_' + method)
        self.assertEqual(expected, call('/1.0/operations/1234'))
        ms.assert_called_with('GET',
                              '/1.0/operations/1234')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_status', return_value=True)
class LXDAPIOperationTestStatus(LXDAPITestBase):

    @annotated_data(
        ('operation_delete', 'DELETE', '', ()),
        ('wait_container_operation', 'GET',
         '/wait?status_code=200&timeout=30', ('200', '30')),
    )
    def test_operation_actions(self, method, http, path, args, ms):
        self.assertTrue(
            getattr(self.lxd, method)('/1.0/operations/1234', *args))
        ms.assert_called_with(http,
                              '/1.0/operations/1234' + path)
