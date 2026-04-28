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

from pylxd import exceptions, models
from pylxd.tests import testing


class TestCluster(testing.PyLXDTestCase):
    """Tests for pylxd.models.Cluster."""

    def test_enable(self):
        """Clustering is enabled."""
        server_name = "foo-cluster"
        # first assert that the lxd cluster requires 'clustering_join' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.Cluster.enable(self.client, server_name)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["clustering_join"])

        # XXX: don't actually call the method as mocking it properly is too hard
        # self.client.cluster.enable(server_name=server_name)

    def test_get(self):
        """A cluster is retrieved."""
        # first assert that the lxd cluster requires 'clustering' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.Cluster.get(self.client)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["clustering"])

        cluster = self.client.cluster.get()

        self.assertEqual("an-member", cluster.server_name)


class TestClusterEquality(testing.PyLXDTestCase):
    """Tests for Cluster equality semantics."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        testing.add_api_extension_helper(self, ["clustering"])

    def test_equal_clusters_same_server_name(self):
        """Two clusters with same server_name are equal."""
        cluster1 = models.Cluster(self.client, server_name="cluster-node-1")
        cluster2 = models.Cluster(self.client, server_name="cluster-node-1")

        self.assertEqual(cluster1, cluster2)

    def test_unequal_clusters_different_server_name(self):
        """Two clusters with different server_name are not equal."""
        cluster1 = models.Cluster(self.client, server_name="cluster-node-1")
        cluster2 = models.Cluster(self.client, server_name="cluster-node-2")

        self.assertNotEqual(cluster1, cluster2)

    def test_not_equal_to_unrelated_type(self):
        """Cluster compared to other types returns NotImplemented."""
        cluster = models.Cluster(self.client, server_name="cluster-node-1")

        # Comparison with other types should return NotImplemented (which makes != True)
        self.assertNotEqual(cluster, "string")
        self.assertNotEqual(cluster, 123)
        self.assertNotEqual(cluster, None)
