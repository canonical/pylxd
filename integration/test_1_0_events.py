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


class Test10Events(IntegrationTestCase):
    """Tests for /1.0/events."""

    def test_1_0_events(self):
        """Return: none (never ending flow of events)."""
        # XXX: rockstar (14 Jan 2016) - This returns a 400 in pylxd, because
        # websockets. I plan to sort this integration test out later, but nova-lxd
        # does not use websockets, so I'll wait a bit on that.
        result = self.lxd['1.0']['events'].get(params={'type': 'operation,logging'})

        self.assertEqual(400, result.status_code)
