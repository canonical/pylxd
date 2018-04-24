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
    description = model.Attribute()
    type = model.Attribute()
    config = model.Attribute()
    managed = model.Attribute(readonly=True)
    used_by = model.Attribute(readonly=True)

    @classmethod
    def exists(cls, client, name):
        """Determine whether a network exists."""
        try:
            client.networks.get(name)
            return True
        except cls.NotFound:
            return False

    @classmethod
    def get(cls, client, name):
        """Get a network by name."""
        response = client.api.networks[name].get()

        return cls(client, **response.json()['metadata'])

    @classmethod
    def all(cls, client):
        """Get all networks."""
        response = client.api.networks.get()

        networks = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            networks.append(cls(client, name=name))
        return networks

    @classmethod
    def create(cls, client, name, description=None, type_=None,
               config=None):
        """Create a network"""
        network = {'name': name}
        if description is not None:
            network['description'] = description
        if type_ is not None:
            network['type'] = type_
        if config is not None:
            network['config'] = config
        client.api.networks.post(json=network)
        return cls.get(client, name)

    def rename(self, new_name):
        """Rename network."""
        self.client.api.networks.post(json={'name': new_name})
        return Network.get(self.client, new_name)

    @property
    def api(self):
        return self.client.api.networks[self.name]
