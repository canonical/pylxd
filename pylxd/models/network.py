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


class Network(model.Model):
    """A LXD network."""
    name = model.Attribute()
    type = model.Attribute()
    used_by = model.Attribute()
    config = model.Attribute()
    managed = model.Attribute()

    @classmethod
    def get(cls, client, name):
        """Get a network by name."""
        response = client.api.networks[name].get()

        network = cls(client, **response.json()['metadata'])
        return network

    @classmethod
    def all(cls, client):
        """Get all networks."""
        response = client.api.networks.get()

        networks = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            networks.append(cls(client, name=name))
        return networks

    @property
    def api(self):
        return self.client.api.networks[self.name]

    def save(self, wait=False):
        """Save is not available for networks."""
        raise NotImplementedError('save is not implemented')

    def delete(self):
        """Delete is not available for networks."""
        raise NotImplementedError('delete is not implemented')
