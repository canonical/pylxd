# Copyright (c) 2016 Canonical Ltd
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

from pylxd import exceptions

from integration.testing import IntegrationTestCase


class TestProfiles(IntegrationTestCase):
    """Tests for `Client.profiles.`"""

    def test_get(self):
        """A profile is fetched by name."""
        name = self.create_profile()
        self.addCleanup(self.delete_profile, name)

        profile = self.client.profiles.get(name)

        self.assertEqual(name, profile.name)

    def test_all(self):
        """All profiles are fetched."""
        name = self.create_profile()
        self.addCleanup(self.delete_profile, name)

        profiles = self.client.profiles.all()

        self.assertIn(name, [profile.name for profile in profiles])

    def test_create(self):
        """A profile is created."""
        name = 'an-profile'
        config = {'limits.memory': '1GB'}
        profile = self.client.profiles.create(name, config)
        self.addCleanup(self.delete_profile, name)

        self.assertEqual(name, profile.name)
        self.assertEqual(config, profile.config)


class TestProfile(IntegrationTestCase):
    """Tests for `Profile`."""

    def setUp(self):
        super(TestProfile, self).setUp()
        name = self.create_profile()
        self.profile = self.client.profiles.get(name)

    def tearDown(self):
        super(TestProfile, self).tearDown()
        self.delete_profile(self.profile.name)

    def test_save(self):
        """A profile is updated."""
        self.profile.config['limits.memory'] = '16GB'
        self.profile.save()

        profile = self.client.profiles.get(self.profile.name)
        self.assertEqual('16GB', profile.config['limits.memory'])

    @unittest.skip('Not implemented in LXD')
    def test_rename(self):
        """A profile is renamed."""
        name = 'a-other-profile'
        self.addCleanup(self.delete_profile, name)

        self.profile.rename(name)
        profile = self.client.profiles.get(name)

        self.assertEqual(name, profile.name)

    def test_delete(self):
        """A profile is deleted."""
        self.profile.delete()

        self.assertRaises(
            exceptions.LXDAPIException,
            self.client.profiles.get, self.profile.name)
