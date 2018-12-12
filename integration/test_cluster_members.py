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


class ClusterMemberTestCase(IntegrationTestCase):

    def setUp(self):
        super(ClusterMemberTestCase, self).setUp()

        if not self.client.has_api_extension('clustering'):
            self.skipTest('Required LXD API extension not available!')


class TestClusterMembers(ClusterMemberTestCase):
    """Tests for `Client.cluster_members.`"""

    def test_get(self):
        """A cluster member is fetched by its name."""

        members = self.client.cluster.members.all()

        random_member_name = "%s" % members[0].server_name
        random_member_url = "%s" % members[0].url

        member = self.client.cluster.members.get(random_member_name)

        new_url = "%s" % member.url
        self.assertEqual(random_member_url, new_url)
