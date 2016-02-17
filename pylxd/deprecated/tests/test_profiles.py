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


@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=(200, fake_api.fake_profile()))
class LXDAPIProfilesTestObject(LXDAPITestBase):

    def test_list_profiles(self, ms):
        ms.return_value = ('200', fake_api.fake_profile_list())
        self.assertEqual(
            ['fake-profile'],
            self.lxd.profile_list())
        ms.assert_called_with('GET',
                              '/1.0/profiles')

    def test_profile_show(self, ms):
        self.assertEqual(
            ms.return_value, self.lxd.profile_show('fake-profile'))
        ms.assert_called_with('GET',
                              '/1.0/profiles/fake-profile')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_status', return_value=True)
class LXDAPIProfilesTestStatus(LXDAPITestBase):

    @data(True, False)
    def test_profile_defined(self, defined, ms):
        ms.return_value = defined
        self.assertEqual(defined, self.lxd.profile_defined('fake-profile'))
        ms.assert_called_with('GET',
                              '/1.0/profiles/fake-profile')

    @annotated_data(
        ('create', 'POST', '', ('fake config',), ('"fake config"',)),
        ('update', 'PUT', '/fake-profile',
         ('fake-profile', 'fake config',), ('"fake config"',)),
        ('rename', 'POST', '/fake-profile',
         ('fake-profile', 'fake config',), ('"fake config"',)),
        ('delete', 'DELETE', '/fake-profile', ('fake-profile',), ()),
    )
    def test_profile_operations(self, method, http, path, args, call_args, ms):
        self.assertTrue(
            getattr(self.lxd, 'profile_' + method)(*args))
        ms.assert_called_with(http,
                              '/1.0/profiles' + path,
                              *call_args)
