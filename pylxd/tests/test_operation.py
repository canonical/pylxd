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
import unittest

from pylxd import api
from pylxd import connection

from pylxd.tests import annotated_data
from pylxd.tests import fake_api


@ddt
class LXDUnitTestOperation(unittest.TestCase):

    def setUp(self):
        super(LXDUnitTestOperation, self).setUp()
        self.lxd = api.API()

    def test_list_operations(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation_list())
            self.assertEqual(
                ['1234'],
                self.lxd.list_operations())
            ms.assert_called_with('GET',
                                  '/1.0/operations')

    def test_operation_info(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual({
                'operation_create_time':
                    datetime.datetime.utcfromtimestamp(1433876844)
                    .strftime('%Y-%m-%d %H:%M:%S'),
                'operation_update_time':
                    datetime.datetime.utcfromtimestamp(1433876843)
                    .strftime('%Y-%m-%d %H:%M:%S'),
                'operation_status_code':
                    'Running'
            }, self.lxd.operation_info('1234'))
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
    def test_operation_show(self, method, expected):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(
                expected, getattr(self.lxd,
                                  'operation_show_' + method)('1234'))
            ms.assert_called_with('GET',
                                  '/1.0/operations/1234')

    @annotated_data(
        ('operation_delete', 'DELETE', ''),
        ('wait_container_operation', 'GET',
         '/wait?status_code=200&timeout=30', ('200', '30')),
    )
    def test_operation_actions(self, method, http, path, args=()):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(
                getattr(self.lxd, method)('1234', *args))
            ms.assert_called_with(http,
                                  '/1.0/operations/1234' + path)
