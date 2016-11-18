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
import pylxd
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from integration.testing import IntegrationTestCase

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TestClient(IntegrationTestCase):
    """Tests for `Client`."""

    def test_authenticate(self):
        # This is another test with multiple assertions, as it is a test of
        # flow, rather than a single source of functionality.
        client = pylxd.Client('https://127.0.0.1:8443/', verify=False)

        self.assertFalse(client.trusted)

        client.authenticate('password')

        self.assertTrue(client.trusted)
