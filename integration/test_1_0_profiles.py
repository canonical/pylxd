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

from integration.testing import IntegrationTestCase


class Test10Profiles(IntegrationTestCase):
    """Tests for /1.0/profiles"""

    PARTS = ['1.0', 'profiles']

    def test_GET(self):
        """Return: a list of URLs to defined profiles."""
        result = self.lxd.get()

        self.assertEqual(200, result.status_code)

    def test_POST(self):
        """Return: a standard return value or a standard error."""
        name = 'bus-rider'
        self.addCleanup(self.delete_profile, name)

        result = self.lxd.post(json={
            'name': name,
            'config': {
                'limits.memory': '1GB',
                }
            })

        self.assertEqual(200, result.status_code)


class Test10Profile(IntegrationTestCase):
    """Tests for /1.0/profiles/<name>"""

    PARTS = ['1.0', 'profiles']

    def setUp(self):
        super(Test10Profile, self).setUp()
        self.profile = self.create_profile()
        self.addCleanup(self.delete_profile, self.profile)
        self.lxd = self.lxd[self.profile]

    def test_GET(self):
        """Return: dict representing profile content."""
        result = self.lxd.get()

        self.assertEqual(200, result.status_code)

    def test_PUT(self):
        """Return: standard return value or standard error."""
        result = self.lxd.put(json={
            'config': {
                'limits.memory': '2GB',
                }
            })

        self.assertEqual(200, result.status_code)

    @unittest.skip("Not yet implemented in LXD")
    def test_POST(self):
        """Return: a standard return value or a standard error."""
        name = 'busrider'
        self.addCleanup(self.delete_profile, name)

        result = self.lxd.post(json={
            'name': name,
            })

        self.assertEqual(204, result.status_code)

    def test_DELETE(self):
        """Return: a standard return value or a standard error."""
        result = self.lxd.delete()

        self.assertEqual(200, result.status_code)
