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

import json
import re
from unittest import TestCase, mock

import requests_mock

from pylxd import exceptions, models
from pylxd.client import Client
from pylxd.tests import testing


class TestStoragePool(testing.PyLXDTestCase):
    """Tests for pylxd.models.StoragePool."""

    def test_all(self):
        """A list of all storage_pools are returned."""
        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.all(self.client)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        storage_pools = models.StoragePool.all(self.client)
        self.assertEqual(1, len(storage_pools))

    def test_get(self):
        """Return a container."""
        name = "lxd"

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.get(self.client, name)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        a_storage_pool = models.StoragePool.get(self.client, name)

        self.assertEqual(name, a_storage_pool.name)

    def test_partial(self):
        """A partial storage_pool is synced."""
        a_storage_pool = models.StoragePool(self.client, name="lxd")

        self.assertEqual("zfs", a_storage_pool.driver)

    def test_create(self):
        """A new storage pool is created."""
        config = {"config": {}, "driver": "zfs", "name": "lxd"}

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.create(self.client, config)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        a_storage_pool = models.StoragePool.create(self.client, config)

        self.assertEqual(config["name"], a_storage_pool.name)

    def test_exists(self):
        """A storage pool exists."""
        name = "lxd"

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.exists(self.client, name)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        self.assertTrue(models.StoragePool.exists(self.client, name))

    def test_not_exists(self):
        """A storage pool exists."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/storage-pools/an-missing-storage-pool$",
            }
        )

        name = "an-missing-storage-pool"

        with mock.patch.object(self.client, "assert_has_api_extension"):
            self.assertFalse(models.StoragePool.exists(self.client, name))

    def test_delete(self):
        """A storage pool can be deleted"""
        a_storage_pool = models.StoragePool(self.client, name="lxd")

        with mock.patch.object(self.client, "assert_has_api_extension"):
            a_storage_pool.delete()

    def test_save(self):
        """A storage pool can be saved"""
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_storage_pool.config = {"some": "value"}

        with mock.patch.object(self.client, "assert_has_api_extension"):
            a_storage_pool.save()

    def test_put(self):
        """A storage pool can be PUT to"""
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        put_object = {"some": "value"}

        with mock.patch.object(self.client, "assert_has_api_extension"):
            a_storage_pool.put(put_object)

    def test_patch(self):
        """A storage pool can be PATCHed"""
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        patch_object = {"some": "value"}

        with mock.patch.object(self.client, "assert_has_api_extension"):
            a_storage_pool.patch(patch_object)


class TestStorageResources(testing.PyLXDTestCase):
    """Tests for pylxd.models.StorageResources."""

    def test_get(self):
        a_storage_pool = models.StoragePool(self.client, name="lxd")

        # first assert that the lxd storage resource requires 'resources'
        # api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.resources.get()

        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["resources"])
        resources = a_storage_pool.resources.get()

        self.assertEqual(resources.space["used"], 207111192576)
        self.assertEqual(resources.space["total"], 306027577344)
        self.assertEqual(resources.inodes["used"], 3275333)
        self.assertEqual(resources.inodes["total"], 18989056)


class TestStorageVolume(testing.PyLXDTestCase):
    """Tests for pylxd.models.StorageVolume."""

    def test_all(self):
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        # first assert that the lxd storage resource requires 'storage'
        # api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.all()

        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        volumes = a_storage_pool.volumes.all()

        # assert that we decoded stuff reasonably well.
        self.assertEqual(len(volumes), 9)
        self.assertEqual(volumes[0].type, "instance")
        self.assertEqual(volumes[0].name, "c1")
        self.assertEqual(volumes[1].type, "instance")
        self.assertEqual(volumes[1].name, "c2")
        self.assertEqual(volumes[2].type, "container")
        self.assertEqual(volumes[2].name, "c3")
        self.assertEqual(volumes[3].type, "container")
        self.assertEqual(volumes[3].name, "c4")
        self.assertEqual(volumes[4].type, "virtual-machine")
        self.assertEqual(volumes[4].name, "vm1")
        self.assertEqual(volumes[5].type, "virtual-machine")
        self.assertEqual(volumes[5].name, "vm2")
        self.assertEqual(volumes[6].type, "image")
        self.assertEqual(volumes[6].name, "i1")
        self.assertEqual(volumes[7].type, "image")
        self.assertEqual(volumes[7].name, "i2")
        self.assertEqual(volumes[8].type, "custom")
        self.assertEqual(volumes[8].name, "cu1")

    def test_get(self):
        a_storage_pool = models.StoragePool(self.client, name="lxd")

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.get("custom", "cu1")
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        # now do the proper get
        volume = a_storage_pool.volumes.get("custom", "cu1")
        self.assertEqual(volume.type, "custom")
        self.assertEqual(volume.name, "cu1")
        config = {
            "block.filesystem": "ext4",
            "block.mount_options": "discard",
            "size": "10737418240",
        }
        self.assertEqual(volume.config, config)

    def test_create(self):
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        config = {"config": {}, "pool": "lxd", "name": "cu1", "type": "custom"}

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.create(self.client, config)
        # now make sure that it's available without mocking it out.
        testing.add_api_extension_helper(self, ["storage"])

        a_volume = a_storage_pool.volumes.create(self.client, config)

        self.assertEqual(config["name"], a_volume.name)

    def test_create_async(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="async-lxd")
        config = {"config": {}, "pool": "async-lxd", "name": "cu1", "type": "custom"}
        a_storage_pool.volumes.create(self.client, config, wait=True)

    def test_rename(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")

        _input = {"name": "vol1", "pool": "pool3", "migration": True}
        result = a_volume.rename(_input)
        self.assertEqual(result["control"], "secret1")
        self.assertEqual(result["fs"], "secret2")

    def test_rename_async(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="async-lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")

        _input = {"name": "vol1", "pool": "pool3", "migration": True}
        a_volume.rename(_input, wait=True)

    def test_put(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")
        put_object = {"config": {"size": 1}}
        a_volume.put(put_object)

    def test_patch(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")
        patch_object = {"config": {"size": 1}}
        with mock.patch.object(self.client, "assert_has_api_extension"):
            a_volume.patch(patch_object)

    def test_save(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")
        a_volume.config = {"size": 2}
        a_volume.save()

    def test_delete(self):
        testing.add_api_extension_helper(self, ["storage"])
        a_storage_pool = models.StoragePool(self.client, name="lxd")
        a_volume = a_storage_pool.volumes.get("custom", "cu1")
        a_volume.delete()

    def test_eq_same_name_type_pool(self):
        """Two volumes with same name, type, and pool (no project) are equal."""
        testing.add_api_extension_helper(self, ["storage"])
        pool = models.StoragePool(self.client, name="lxd")
        a = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool
        )
        b = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool
        )
        self.assertEqual(a, b)

    def test_eq_different_project(self):
        """Two volumes with same name/type/pool but different projects differ."""
        testing.add_api_extension_helper(self, ["storage"])
        pool = models.StoragePool(self.client, name="lxd")
        a = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool, project="p1"
        )
        b = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool, project="p2"
        )
        self.assertNotEqual(a, b)

    def test_eq_does_not_trigger_sync(self):
        """__eq__ must not call sync() when project is unset."""
        testing.add_api_extension_helper(self, ["storage"])
        pool = models.StoragePool(self.client, name="lxd")
        a = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool
        )
        b = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool
        )
        with mock.patch.object(models.StorageVolume, "sync") as mock_sync:
            result = a == b
            self.assertTrue(result)
            mock_sync.assert_not_called()

    def test_eq_with_unrelated_type_returns_not_implemented(self):
        """StorageVolume.__eq__ should return NotImplemented for unrelated types."""
        testing.add_api_extension_helper(self, ["storage"])
        pool = models.StoragePool(self.client, name="lxd")
        a = models.StorageVolume(
            self.client, name="cu1", type="custom", storage_pool=pool
        )
        # Direct __eq__ call should return NotImplemented for unrelated types
        self.assertIs(a.__eq__(42), NotImplemented)


class TestStoragePoolAsync(testing.PyLXDTestCase):
    """Tests for async operations in pylxd.models.StoragePool."""

    def setUp(self):
        """Set up common test data."""
        super().setUp()
        testing.add_api_extension_helper(self, ["storage"])
        self.config = {"config": {}, "driver": "zfs", "name": "test-pool"}
        self.storage_pool = models.StoragePool(self.client, name="test-pool")

    def _setup_create_mocks(self, response_type, operation_id=None):
        """
        Sets up mocks for the StoragePool.create POST and subsequent GET.
        Uses 202 for async and 200 for sync responses.
        """
        # 1. Mock POST response
        json_data = {"type": response_type, "status": "Success", "status_code": 200}
        status_code = 200
        if response_type == "async":
            json_data["operation"] = operation_id
            json_data["status_code"] = 202
            status_code = 202

        self.add_rule(
            {
                "json": json_data,
                "status_code": status_code,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/storage-pools$",
            }
        )

        # 2. Mock GET pool response (for cls.get)
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": 200,
                    "metadata": {
                        "name": self.config["name"],
                        "driver": self.config["driver"],
                        "config": self.config["config"],
                        "used_by": [],
                        "status": "Created",
                    },
                },
                "method": "GET",
                "url": rf"^http://pylxd.test/1.0/storage-pools/{self.config['name']}$",
            }
        )

    def _setup_async_operation_rule(self, method, endpoint, operation_id):
        """Generic helper for setting up async PUT/DELETE rules on the pool endpoint."""
        self.add_rule(
            {
                "json": {
                    "type": "async",
                    "status": "Success",
                    "status_code": 202,
                    "operation": operation_id,
                },
                "status_code": 202,
                "method": method,
                "url": rf"^http://pylxd.test/1.0/storage-pools/{self.storage_pool.name}{endpoint}$",
            }
        )

    def test_create_async_wait_true(self):
        """Async response with wait=True should wait for operation."""
        self._setup_create_mocks("async", "/1.0/operations/create-pool-wait")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            storage_pool = models.StoragePool.create(
                self.client, self.config, wait=True
            )
            mock_wait.assert_called_once_with("/1.0/operations/create-pool-wait")
            self.assertEqual(self.config["name"], storage_pool.name)

    def test_create_async_wait_false(self):
        """Async response with wait=False should not wait."""
        self._setup_create_mocks("async", "/1.0/operations/create-pool-nowait")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            storage_pool = models.StoragePool.create(
                self.client, self.config, wait=False
            )
            mock_wait.assert_not_called()
            self.assertEqual(self.config["name"], storage_pool.name)

    def test_create_sync_no_wait(self):
        """Sync response should never wait, testing old LXD compatibility."""
        # Note: We rely on the initial default response rules for the GET
        self._setup_create_mocks("sync")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            models.StoragePool.create(self.client, self.config, wait=True)
            mock_wait.assert_not_called()

    def test_delete_async_with_wait(self):
        """Test async storage pool deletion with wait=True (via inherited Model.delete)"""
        operation_id = "/1.0/operations/delete-op"
        self._setup_async_operation_rule("DELETE", "", operation_id)

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.delete(wait=True)
            mock_wait.assert_called_once_with(operation_id)

    def test_save_async_with_wait(self):
        """Test async storage pool save with wait=True (via inherited Model.save)"""
        self.storage_pool.config = {"new": "config"}
        operation_id = "/1.0/operations/save-op"

        # Note: The endpoint path is empty string "" as PUT is directly on the pool URL
        self._setup_async_operation_rule("PUT", "", operation_id)
        self._setup_create_mocks("async", operation_id)

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.save(wait=True)
            mock_wait.assert_called_once_with(operation_id)

    def test_save_async_without_wait(self):
        """Test async storage pool save with wait=False (via inherited Model.save)"""
        self.storage_pool.config = {"new": "config"}
        operation_id = "/1.0/operations/save-op"

        self._setup_async_operation_rule("PUT", "", operation_id)
        self._setup_create_mocks("async", operation_id)

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.save(wait=False)
            mock_wait.assert_not_called()

    def test_delete_async_without_wait(self):
        """Test async storage pool deletion with wait=False should not wait."""
        operation_id = "/1.0/operations/delete-op-nowait"
        self._setup_async_operation_rule("DELETE", "", operation_id)

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.delete(wait=False)
            mock_wait.assert_not_called()

    def test_patch_async_with_wait(self):
        """Test async storage pool patch with wait=True (via inherited Model.patch)"""
        operation_id = "/1.0/operations/patch-op"
        self._setup_async_operation_rule("PATCH", "", operation_id)

        # patch() calls raw_patch then sync; mock GET for the sync call
        self._setup_create_mocks("sync")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.patch({"config": {"new": "value"}}, wait=True)
            mock_wait.assert_called_once_with(operation_id)

    def test_patch_async_without_wait(self):
        """Test async storage pool patch with wait=False should not wait."""
        operation_id = "/1.0/operations/patch-op-nowait"
        self._setup_async_operation_rule("PATCH", "", operation_id)

        # patch() calls raw_patch then sync; mock GET for the sync call
        self._setup_create_mocks("sync")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.patch({"config": {"new": "value"}}, wait=False)
            mock_wait.assert_not_called()

    def test_put_async_with_wait(self):
        """Test async storage pool put() with wait=True (via inherited Model.put)"""
        operation_id = "/1.0/operations/put-op"
        self._setup_async_operation_rule("PUT", "", operation_id)

        # put() calls raw_put then sync(rollback=True); mock GET for the sync call
        self._setup_create_mocks("sync")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.put({"config": {"new": "value"}}, wait=True)
            mock_wait.assert_called_once_with(operation_id)

    def test_put_async_without_wait(self):
        """Test async storage pool put() with wait=False should not wait."""
        operation_id = "/1.0/operations/put-op-nowait"
        self._setup_async_operation_rule("PUT", "", operation_id)

        # put() calls raw_put then sync(rollback=True); mock GET for the sync call
        self._setup_create_mocks("sync")

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.put({"config": {"new": "value"}}, wait=False)
            mock_wait.assert_not_called()


class TestStoragePoolOperationsExtension(TestCase):
    """Tests for storage_and_network_operations extension on StoragePool.

    Uses requests_mock directly (no mock_services wrapper) to verify that
    StoragePool.put() and StoragePool.patch() are forced to wait for async
    responses when the storage_and_network_operations extension is present
    (introduced by LXD PR #17955 and pylxd PR #719).
    """

    _POOL_NAME = "test-pool"
    _POOL_METADATA = {
        "config": {"size": "0"},
        "description": "",
        "name": "test-pool",
        "driver": "zfs",
        "used_by": [],
        "status": "Created",
        "managed": True,
        "locations": [],
    }

    def setUp(self):
        self.mocker = requests_mock.Mocker()
        self.mocker.start()
        self.addCleanup(self.mocker.stop)

        # Required for Client.__init__ and has_api_extension() checks.
        self.mocker.get(
            re.compile(r"http://pylxd\.test/1\.0$"),
            json={
                "type": "sync",
                "metadata": {
                    "auth": "trusted",
                    "environment": {"certificate": "an-pem-cert"},
                    "api_extensions": ["storage"],
                },
            },
        )
        # Used by put()/patch() → sync(rollback=True) and save()'s dirty sync.
        self.mocker.get(
            re.compile(rf"http://pylxd\.test/1\.0/storage-pools/{self._POOL_NAME}$"),
            json={"type": "sync", "metadata": self._POOL_METADATA},
        )

        self.client = Client(endpoint="http://pylxd.test")
        self.storage_pool = models.StoragePool(self.client, name=self._POOL_NAME)

    def _enable_extension(self, *extensions):
        """Directly add API extensions to host_info without an HTTP round-trip."""
        self.client.host_info["api_extensions"].extend(extensions)

    def test_put_async_forced_by_extension(self):
        """StoragePool.put(wait=False) still waits when storage_and_network_operations
        is present, because _model.py overrides wait to True."""
        self._enable_extension("storage_and_network_operations")
        operation_id = "/1.0/operations/put-ext-forced"
        self.mocker.put(
            re.compile(rf"http://pylxd\.test/1\.0/storage-pools/{self._POOL_NAME}$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.put({"config": {"new": "value"}}, wait=False)
            mock_wait.assert_called_once_with(operation_id)

    def test_patch_async_forced_by_extension(self):
        """StoragePool.patch(wait=False) still waits when storage_and_network_operations
        is present."""
        self._enable_extension("storage_and_network_operations")
        operation_id = "/1.0/operations/patch-ext-forced"
        self.mocker.patch(
            re.compile(rf"http://pylxd\.test/1\.0/storage-pools/{self._POOL_NAME}$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.patch({"config": {"new": "value"}}, wait=False)
            mock_wait.assert_called_once_with(operation_id)

    def test_save_async_not_forced_by_extension(self):
        """StoragePool.save(wait=False) does NOT force wait even when
        storage_and_network_operations is present — PR #719 only adds forced-wait
        to put() and patch(), preserving save()'s explicit-wait contract."""
        self._enable_extension("storage_and_network_operations")
        self.storage_pool.config = {"new": "config"}
        operation_id = "/1.0/operations/save-ext-not-forced"
        self.mocker.put(
            re.compile(rf"http://pylxd\.test/1\.0/storage-pools/{self._POOL_NAME}$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.save(wait=False)
            mock_wait.assert_not_called()

    def test_put_without_extension_respects_wait_false(self):
        """Without the storage_and_network_operations extension,
        StoragePool.put(wait=False) does NOT call wait_for_operation."""
        # setUp adds only "storage" — no storage_and_network_operations.
        operation_id = "/1.0/operations/put-no-ext"
        self.mocker.put(
            re.compile(rf"http://pylxd\.test/1\.0/storage-pools/{self._POOL_NAME}$"),
            json={"type": "async", "operation": operation_id},
            status_code=202,
        )

        with mock.patch.object(
            self.client.operations, "wait_for_operation"
        ) as mock_wait:
            self.storage_pool.put({"config": {"new": "value"}}, wait=False)
            mock_wait.assert_not_called()


class TestStorageVolumeSnapshotAsync(testing.PyLXDTestCase):
    """Tests for async operations in StorageVolumeSnapshot."""

    def setUp(self):
        super().setUp()
        testing.add_api_extension_helper(
            self, ["storage", "storage_api_volume_snapshots"]
        )
        self.storage_pool = models.StoragePool(self.client, name="test-pool")
        self.volume = models.StorageVolume(
            self.client,
            name="test-volume",
            type="custom",
            storage_pool=self.storage_pool,
        )
        self.mock_wait = mock.patch.object(
            self.client.operations, "wait_for_operation"
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _mock_async_op(self, operation_id, method="POST", url_suffix=""):
        """Helper to mock async operation responses."""
        base_url = (
            "http://pylxd.test/1.0/storage-pools/test-pool/volumes/custom/test-volume"
        )
        self.add_rule(
            {
                "json": {
                    "type": "async",
                    "status_code": 202,
                    "operation": operation_id,
                },
                "status_code": 202,
                "method": method,
                "url": f"^{base_url}{url_suffix}$",
            }
        )

    def _mock_snapshots_list(self, snapshots):
        """Mock the snapshots list response."""
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": 200,
                    "metadata": [f"/1.0/.../snapshots/{name}" for name in snapshots],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/storage-pools/test-pool/volumes/custom/test-volume/snapshots$",
            }
        )

    def _mock_snapshot_get(self, name, content_type="filesystem"):
        """Mock GET snapshot response."""
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": 200,
                    "metadata": {
                        "name": f"test-volume/{name}",
                        "content_type": content_type,
                    },
                },
                "method": "GET",
                "url": rf"^http://pylxd.test/1.0/storage-pools/test-pool/volumes/custom/test-volume/snapshots/{name}$",
            }
        )

    def test_create_async_with_wait_and_auto_name(self):
        """Test async snapshot creation with wait=True and auto-generated name"""
        self._mock_async_op(
            "/1.0/operations/snapshot-create-op", url_suffix="/snapshots"
        )
        self._mock_snapshots_list(["snap0", "snap1"])
        self._mock_snapshot_get("snap1")

        snapshot = models.StorageVolumeSnapshot.create(self.volume, wait=True)

        self.mock_wait.assert_called_once_with("/1.0/operations/snapshot-create-op")
        self.assertEqual("snap1", snapshot.name)

    def test_rename_async_with_wait(self):
        """Test async snapshot rename with wait=True"""
        snapshot = models.StorageVolumeSnapshot(
            self.client, name="old-snapshot", volume=self.volume
        )

        self._mock_async_op(
            "/1.0/operations/snapshot-rename-op", url_suffix="/snapshots/old-snapshot"
        )

        snapshot.rename("new-snapshot", wait=True)

        self.mock_wait.assert_called_once_with("/1.0/operations/snapshot-rename-op")
        self.assertEqual("new-snapshot", snapshot.name)


class TestStorageVolumeSnapshotEquality(TestCase):
    """Tests for StorageVolumeSnapshot equality semantics."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = mock.Mock()
        self.storage_pool = models.StoragePool(self.client, name="test-pool")
        self.volume = models.StorageVolume(
            self.client,
            name="test-volume",
            type="custom",
            storage_pool=self.storage_pool,
        )

    def test_equal_snapshots_same_name_and_volume(self):
        """Two snapshots with same name and volume are equal."""
        snap1 = models.StorageVolumeSnapshot(
            self.client, name="snap1", volume=self.volume
        )
        snap2 = models.StorageVolumeSnapshot(
            self.client, name="snap1", volume=self.volume
        )

        self.assertEqual(snap1, snap2)

    def test_unequal_snapshots_different_name(self):
        """Two snapshots with different names are not equal."""
        snap1 = models.StorageVolumeSnapshot(
            self.client, name="snap1", volume=self.volume
        )
        snap2 = models.StorageVolumeSnapshot(
            self.client, name="snap2", volume=self.volume
        )

        self.assertNotEqual(snap1, snap2)

    def test_unequal_snapshots_different_volume(self):
        """Two snapshots with different volumes are not equal."""
        volume2 = models.StorageVolume(
            self.client,
            name="test-volume-2",
            type="custom",
            storage_pool=self.storage_pool,
        )
        snap1 = models.StorageVolumeSnapshot(
            self.client, name="snap1", volume=self.volume
        )
        snap2 = models.StorageVolumeSnapshot(self.client, name="snap1", volume=volume2)

        self.assertNotEqual(snap1, snap2)

    def test_not_equal_to_unrelated_type(self):
        """StorageVolumeSnapshot compared to other types returns NotImplemented."""
        snap = models.StorageVolumeSnapshot(
            self.client, name="snap1", volume=self.volume
        )

        # Comparison with other types should return NotImplemented (which makes != True)
        self.assertNotEqual(snap, "string")
        self.assertNotEqual(snap, 123)
        self.assertNotEqual(snap, None)
