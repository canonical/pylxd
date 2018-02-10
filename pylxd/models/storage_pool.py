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


class StoragePool(model.Model):
    """A LXD storage_pool.

    This corresponds to the LXD endpoint at
    /1.0/storage-pools
    """
    name = model.Attribute()
    driver = model.Attribute()
    description = model.Attribute()
    used_by = model.Attribute()
    config = model.Attribute()
    managed = model.Attribute()

    @classmethod
    def get(cls, client, name):
        """Get a storage_pool by name."""
        response = client.api.storage_pools[name].get()

        storage_pool = cls(client, **response.json()['metadata'])
        return storage_pool

    @classmethod
    def all(cls, client):
        """Get all storage_pools."""
        response = client.api.storage_pools.get()

        storage_pools = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            storage_pools.append(cls(client, name=name))
        return storage_pools

    @classmethod
    def create(cls, client, config):
        """Create a storage_pool from config."""
        client.api.storage_pools.post(json=config)

        storage_pool = cls.get(client, config['name'])
        return storage_pool

    @classmethod
    def exists(cls, client, name):
        """Determine whether a storage pool exists."""
        try:
            client.storage_pools.get(name)
            return True
        except cls.NotFound:
            return False

    @property
    def api(self):
        return self.client.api.storage_pools[self.name]

    def save(self, wait=False):
        """Save is not available for storage_pools."""
        raise NotImplementedError('save is not implemented')

    def delete(self):
        """Delete is not available for storage_pools."""
        raise NotImplementedError('delete is not implemented')
