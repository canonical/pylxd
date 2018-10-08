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
from pylxd.models import _model as model


class ClusterMember(model.Model):
    """A LXD certificate."""

    name = model.Attribute(readonly=True)
    url = model.Attribute(readonly=True)
    database = model.Attribute(readonly=True)
    state = model.Attribute(readonly=True)
    server_name = model.Attribute(readonly=True)
    status = model.Attribute(readonly=True)
    message = model.Attribute(readonly=True)

    @classmethod
    def get(cls, client, name):
        """Get a certificate by fingerprint."""
        response = client.api.cluster_members[name].get()

        return cls(client, **response.json()['metadata'])

    @classmethod
    def all(cls, client):
        """Get all certificates."""
        response = client.api.cluster_members.get()

        nodes = []
        for node in response.json()['metadata']:
            name = node.split('/')[-1]
            nodes.append(cls(client, name=name))
        return nodes

    @property
    def api(self):
        return self.client.api.cluster_members[self.name]
