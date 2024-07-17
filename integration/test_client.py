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

import os

import pylxd
from integration.testing import IntegrationTestCase
from pylxd import exceptions


class TestClient(IntegrationTestCase):
    """Tests for `Client`."""

    def test_authenticate(self):
        client = pylxd.Client("https://127.0.0.1:8443/")

        if client.has_api_extension("explicit_trust_token"):
            secret = os.getenv("LXD_TOKEN")
        else:
            secret = "password"

        self.assertFalse(client.trusted)

        client.authenticate(secret)

        self.assertTrue(client.trusted)

    def test_authenticate_with_project(self):
        if self.client.has_api_extension("explicit_trust_token"):
            self.skipTest(
                "Required LXD support for password authentication not available!"
            )

        try:
            client = pylxd.Client("https://127.0.0.1:8443/", project="test-project")
        except exceptions.ClientConnectionFailed as e:
            message = str(e)
            if message == "Remote server doesn't handle projects":
                self.skipTest(message)
            raise

        if client.has_api_extension("explicit_trust_token"):
            secret = os.getenv("LXD_TOKEN")
        else:
            secret = "password"

        client.authenticate(secret)
        self.assertEqual(client.host_info["environment"]["project"], "test-project")
