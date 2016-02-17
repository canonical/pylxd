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

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object')
class LXDAPIImageAliasTestObject(LXDAPITestBase):

    def test_alias_list(self, ms):
        ms.return_value = ('200', fake_api.fake_alias_list())
        self.assertEqual(['ubuntu'], self.lxd.alias_list())
        ms.assert_called_once_with('GET', '/1.0/images/aliases')

    def test_alias_show(self, ms):
        ms.return_value = ('200', fake_api.fake_alias())
        self.assertEqual(
            fake_api.fake_alias(), self.lxd.alias_show('fake')[1])
        ms.assert_called_once_with('GET', '/1.0/images/aliases/fake')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_status')
class LXDAPIImageAliasTestStatus(LXDAPITestBase):

    @data(True, False)
    def test_alias_defined(self, expected, ms):
        ms.return_value = expected
        self.assertEqual(expected, self.lxd.alias_defined('fake'))
        ms.assert_called_once_with('GET', '/1.0/images/aliases/fake')

    @annotated_data(
        ('create', 'POST', '', ('fake',), ('"fake"',)),
        ('update', 'PUT', '/test-alias',
         ('test-alias', 'fake',), ('"fake"',)),
        ('rename', 'POST', '/test-alias',
         ('test-alias', 'fake',), ('"fake"',)),
        ('delete', 'DELETE', '/test-alias', ('test-alias',), ()),
    )
    def test_alias_operations(self, method, http, path, args, call_args, ms):
        self.assertTrue(getattr(self.lxd, 'alias_' + method)(*args))
        ms.assert_called_once_with(
            http,
            '/1.0/images/aliases' + path,
            *call_args
        )
