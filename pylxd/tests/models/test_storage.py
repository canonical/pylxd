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
from pylxd import models
from pylxd.tests import testing


class TestStoragePool(testing.PyLXDTestCase):
    """Tests for pylxd.models.StoragePool."""

    def test_all(self):
        """A list of all storage_pools are returned."""
        storage_pools = models.StoragePool.all(self.client)

        self.assertEqual(1, len(storage_pools))

    def test_get(self):
        """Return a container."""
        name = 'lxd'

        an_storage_pool = models.StoragePool.get(self.client, name)

        self.assertEqual(name, an_storage_pool.name)

    def test_partial(self):
        """A partial storage_pool is synced."""
        an_storage_pool = models.StoragePool(self.client, name='lxd')

        self.assertEqual('zfs', an_storage_pool.driver)

    def test_create(self):
        """A new storage pool is created."""
        config = {"config": {}, "driver": "zfs", "name": "lxd"}

        an_storage_pool = models.StoragePool.create(self.client, config)

        self.assertEqual(config['name'], an_storage_pool.name)

    def test_delete(self):
        """delete is not implemented in storage_pools."""
        an_storage_pool = models.StoragePool(self.client, name='lxd')

        with self.assertRaises(NotImplementedError):
            an_storage_pool.delete()

    def test_save(self):
        """save is not implemented in storage_pools."""
        an_storage_pool = models.StoragePool(self.client, name='lxd')

        with self.assertRaises(NotImplementedError):
            an_storage_pool.save()
