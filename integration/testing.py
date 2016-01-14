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
import uuid

from pylxd.api import LXD


class IntegrationTestCase(unittest.TestCase):
    """A base test case for pylxd integration tests."""

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.lxd = LXD('http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket')

    def create_container(self):
        """Create a container in lxd."""
        name = 'a' + str(uuid.uuid4())
        machine = {
            'name': name,
            'architecture': 2,
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }
        result = self.lxd['1.0']['containers'].post(json=machine)
        operation_uuid = result.json()['operation'].split('/')[-1]
        self.lxd['1.0'].operations[operation_uuid].wait.get()
        return name

    def delete_container(self, name):
        """Delete a container in lxd."""
        self.lxd['1.0']['containers'][name].delete()

    def assertCommon(self, response):
        """Assert common LXD responses.

        LXD responses are relatively standard. This function makes assertions
        to all those standards.
        """
        self.assertEqual(response.status_code, response.json()['status_code'])
        self.assertEqual(
            ['metadata', 'operation', 'status', 'status_code', 'type'],
            sorted(response.json().keys()))
