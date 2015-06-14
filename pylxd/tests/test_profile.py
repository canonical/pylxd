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

class PyLXDTestProfile(unittest.TestCase):
    def setUp(self):
        (PyLXDTestProfile, self).__init__()
        self.api = api.API()

    def _create_profile(self):
        config = {'name': 'test_profile'}
        self.api.profile_create(config)

    def _delete_profile(self):
        self.api.profile_delete('test_profile')

    def test_create_profile(self):
        self._create_profile()
        self.assertIn('test_profile', self.api.profile_list())
        self._delete_profile()

    def test_profile_show(self):
        self._create_profile()
        (state, data) = self.api.profile_show('test_profile')
        self.assertEqual(data['metadata']['name'], 'test_profile')
        self._delete_profile()

    def test_profile_update(self):
        old_profile = { 'name': 'test_profile',
                        'config': {'limits.memory': '2048'}
                       }
        self.api.profile_create(old_profile)
        profile_update = {
                            'name': 'test_profile',
                            'config': {'limits.memory': '1048'}
                         }
        self.api.profile_update('test_profile', profile_update)
        (state, data) = self.api.profile_show('test_profile')
        self.assertEqual(data['metadata']['config'],
                         {'limits.memory': '1048'})
        self.api.profile_delete('test_profile')

    def test_profile_rename(self):
        self.skipTest('Profile rename is not impletmented')
        self._create_profile()
        config = {'name': 'new_profile'}
        self.api.profile_rename('test_profile', config)
        self.assertIn('new_profile', self.api.profile_list())
        self.api.profile_delete('new_profile')