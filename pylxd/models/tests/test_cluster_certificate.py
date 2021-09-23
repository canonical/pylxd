# Copyright (c) 2021 Canonical Ltd
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


class TestClusterCertificate(testing.PyLXDTestCase):
    """Tests for pylxd.models.ClusterCertificate"""

    def test_put(self):
        """Update the certificate for a cluster"""

        self.client.cluster.certificate.put(
            cert="my-cluster-cert", key="my-cluster-key"
        )
