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

import unittest

import pylxd.exceptions as exceptions
from integration.testing import IntegrationTestCase


class StorageTestCase(IntegrationTestCase):
    def setUp(self):
        super().setUp()

        if not self.client.has_api_extension("storage"):
            self.skipTest("Required LXD API extension not available!")


class TestStoragePools(StorageTestCase):
    """Tests for :py:class:`pylxd.models.storage_pools.StoragePools"""

    # note create and delete are tested in every method

    def test_get(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pool = self.client.storage_pools.get(name)
        self.assertEqual(name, storage_pool.name)

    def test_all(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pools = self.client.storage_pools.all()
        self.assertIn(name, [p.name for p in storage_pools])

    def test_save(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pool = self.client.storage_pools.get(name)
        storage_pool.description = "My storage pool"
        storage_pool.save()

        p = self.client.storage_pools.get(name)
        self.assertEqual(p.description, "My storage pool")

    def test_put(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pool = self.client.storage_pools.get(name)
        new_desc = "new description"
        self.assertNotEqual(storage_pool.description, new_desc)
        put_object = {
            "description": new_desc,
            "config": storage_pool.config,
        }
        storage_pool.put(put_object)
        self.assertEqual(storage_pool.description, new_desc)
        p = self.client.storage_pools.get(name)
        self.assertEqual(p.description, new_desc)

    def test_patch(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pool = self.client.storage_pools.get(name)
        new_desc = "new description"
        self.assertNotEqual(storage_pool.description, new_desc)
        patch_object = {
            "description": new_desc,
        }
        storage_pool.patch(patch_object)
        self.assertEqual(storage_pool.description, new_desc)
        p = self.client.storage_pools.get(name)
        self.assertEqual(p.description, new_desc)


class TestStorageResources(StorageTestCase):
    """Tests for :py:class:`pylxd.models.storage_pools.StorageResources"""

    def test_get(self):
        name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, name)

        storage_pool = self.client.storage_pools.get(name)
        # just assert that it can be fetched and that a key exists
        resources = storage_pool.resources.get()
        self.assertIsInstance(resources.space, dict)
        self.assertIsInstance(resources.inodes, dict)


class TestStorageVolume(StorageTestCase):
    """Tests for :py:class:`pylxd.models.storage_pools.StorageVolume"""

    def test_create_and_get_and_delete(self):
        pool_name = self.create_storage_pool()
        self.addCleanup(self.delete_storage_pool, pool_name)
        storage_pool = self.client.storage_pools.get(pool_name)

        volume = self.create_storage_volume(pool_name, "vol1")
        vol_copy = storage_pool.volumes.get("custom", "vol1")
        self.assertEqual(vol_copy.name, volume.name)
        volume.delete()

    @unittest.skip("Can't test PUT on volumes as it doesn't make sense yet")
    def test_put(self):
        pass

    @unittest.skip("Can't test .save() on volumes yet - doesn't make sense")
    def test_save(self):
        pass

    @unittest.skip("Can't test PATCH on volumes yet - doesn't make sense")
    def test_patch(self):
        # as we're not using ZFS (and can't in these integration tests) we
        # can't really patch anything on a dir volume.
        pass
