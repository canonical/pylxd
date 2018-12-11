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

from pylxd.tests import testing


class TestClusterMember(testing.PyLXDTestCase):
    """Tests for pylxd.models.ClusterMember."""

    def test_get(self):
        """A cluster member is retrieved."""
        member = self.client.cluster.members.get('an-member')

        self.assertEqual('https://10.1.1.101:8443', member.url)

    def test_all(self):
        """All cluster members are returned."""
        members = self.client.cluster.members.all()

        self.assertIn('an-member', [m.server_name for m in members])
