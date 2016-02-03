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


class Test10Networks(IntegrationTestCase):
    """Tests for /1.0/networks"""

    PARTS = ['1.0', 'networks']

    def test_GET(self):
        """Return: a list of networks that are currently defined on the host."""
        response = self.lxd.get()

        self.assertEqual(200, response.status_code)


class Test10Network(IntegrationTestCase):
    """Tests for /1.0/networks/<name>"""

    PARTS = ['1.0', 'networks']

    def test_GET(self):
        """Return: dict representing the network."""
        response = self.lxd['lo'].get()

        self.assertEqual(200, response.status_code)
