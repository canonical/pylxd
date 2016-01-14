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
from integration.testing import IntegrationTestCase


class Test10(IntegrationTestCase):
    """Tests for /1.0"""

    def test_1_0(self):
        """Return: Dict representing server state."""
        result = self.lxd['1.0'].get()

        self.assertCommon(result)
        self.assertEqual(200, result.status_code)
        self.assertEqual(
            ['api_compat', 'auth', 'config', 'environment'],
            sorted(result.json()['metadata'].keys()))
        self.assertEqual(
            ['addresses', 'architectures', 'driver', 'driver_version', 'kernel',
             'kernel_architecture', 'kernel_version', 'server', 'server_pid',
             'server_version', 'storage', 'storage_version'],
            sorted(result.json()['metadata']['environment'].keys()))

    def test_1_0_PUT(self):
        """Return: standard return value or standard error."""
        result = self.lxd['1.0'].put(json={'config': {'core.trust_password': 'test'}})

        self.assertCommon(result)
        self.assertEqual(200, result.status_code)
