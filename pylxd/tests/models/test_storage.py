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

try:
    from unittest import mock
except ImportError:
    import mock

from pylxd import exceptions
from pylxd import models
from pylxd.tests import testing


def add_api_extension_helper(obj, extensions):
    obj.add_rule({
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'auth': 'trusted',
                         'environment': {
                             'certificate': 'an-pem-cert',
                             },
                         'api_extensions': extensions
                         }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0$',
    })
    # Update hostinfo
    obj.client.host_info = obj.client.api.get().json()['metadata']


class TestStoragePool(testing.PyLXDTestCase):
    """Tests for pylxd.models.StoragePool."""

    def test_all(self):
        """A list of all storage_pools are returned."""
        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.all(self.client)
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        storage_pools = models.StoragePool.all(self.client)
        self.assertEqual(1, len(storage_pools))

    def test_get(self):
        """Return a container."""
        name = 'lxd'

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.get(self.client, name)
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        a_storage_pool = models.StoragePool.get(self.client, name)

        self.assertEqual(name, a_storage_pool.name)

    def test_partial(self):
        """A partial storage_pool is synced."""
        a_storage_pool = models.StoragePool(self.client, name='lxd')

        self.assertEqual('zfs', a_storage_pool.driver)

    def test_create(self):
        """A new storage pool is created."""
        config = {"config": {}, "driver": "zfs", "name": "lxd"}

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.create(self.client, config)
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        a_storage_pool = models.StoragePool.create(self.client, config)

        self.assertEqual(config['name'], a_storage_pool.name)

    def test_exists(self):
        """A storage pool exists."""
        name = 'lxd'

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            models.StoragePool.exists(self.client, name)
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        self.assertTrue(models.StoragePool.exists(self.client, name))

    def test_not_exists(self):
        """A storage pool exists."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/storage-pools/an-missing-storage-pool$',  # NOQA
        })

        name = 'an-missing-storage-pool'

        with mock.patch.object(self.client, 'assert_has_api_extension'):
            self.assertFalse(models.StoragePool.exists(self.client, name))

    def test_delete(self):
        """A storage pool can be deleted"""
        a_storage_pool = models.StoragePool(self.client, name='lxd')

        with mock.patch.object(self.client, 'assert_has_api_extension'):
            a_storage_pool.delete()

    def test_save(self):
        """A storage pool can be saved"""
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_storage_pool.config = {'some': 'value'}

        with mock.patch.object(self.client, 'assert_has_api_extension'):
            a_storage_pool.save()

    def test_put(self):
        """A storage pool can be PUT to"""
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        put_object = {'some': 'value'}

        with mock.patch.object(self.client, 'assert_has_api_extension'):
            a_storage_pool.put(put_object)

    def test_patch(self):
        """A storage pool can be PATCHed"""
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        patch_object = {'some': 'value'}

        with mock.patch.object(self.client, 'assert_has_api_extension'):
            a_storage_pool.patch(patch_object)


class TestStorageResources(testing.PyLXDTestCase):
    """Tests for pylxd.models.StorageResources."""

    def test_get(self):
        a_storage_pool = models.StoragePool(self.client, name='lxd')

        # first assert that the lxd storage resource requires 'resources'
        # api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.resources.get()

        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['resources'])
        resources = a_storage_pool.resources.get()

        self.assertEqual(resources.space['used'], 207111192576)
        self.assertEqual(resources.space['total'], 306027577344)
        self.assertEqual(resources.inodes['used'], 3275333)
        self.assertEqual(resources.inodes['total'], 18989056)


class TestStorageVolume(testing.PyLXDTestCase):
    """Tests for pylxd.models.StorageVolume."""

    def test_all(self):
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        # first assert that the lxd storage resource requires 'storage'
        # api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.all()

        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        volumes = a_storage_pool.volumes.all()

        # assert that we decoded stuff reasonably well.
        self.assertEqual(len(volumes), 6)
        self.assertEqual(volumes[0].type, 'container')
        self.assertEqual(volumes[0].name, 'c1')
        self.assertEqual(volumes[3].type, 'image')
        self.assertEqual(volumes[3].name, 'i1')
        self.assertEqual(volumes[5].type, 'custom')
        self.assertEqual(volumes[5].name, 'cu1')

    def test_get(self):
        a_storage_pool = models.StoragePool(self.client, name='lxd')

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.get('custom', 'cu1')
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        # now do the proper get
        volume = a_storage_pool.volumes.get('custom', 'cu1')
        self.assertEqual(volume.type, 'custom')
        self.assertEqual(volume.name, 'cu1')
        config = {
            "block.filesystem": "ext4",
            "block.mount_options": "discard",
            "size": "10737418240"
        }
        self.assertEqual(volume.config, config)

    def test_create(self):
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        config = {
            "config": {},
            "pool": "lxd",
            "name": "cu1",
            "type": "custom"
        }

        # first assert that the lxd storage requires 'storage' api_extension
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_storage_pool.volumes.create(self.client, config)
        # now make sure that it's available without mocking it out.
        add_api_extension_helper(self, ['storage'])

        a_volume = a_storage_pool.volumes.create(self.client, config)

        self.assertEqual(config['name'], a_volume.name)

    def test_create_async(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='async-lxd')
        config = {
            "config": {},
            "pool": "async-lxd",
            "name": "cu1",
            "type": "custom"
        }
        a_storage_pool.volumes.create(self.client, config, wait=True)

    def test_rename(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')

        _input = {
            "name": "vol1",
            "pool": "pool3",
            "migration": True
        }
        result = a_volume.rename(_input)
        self.assertEqual(result['control'], 'secret1')
        self.assertEqual(result['fs'], 'secret2')

    def test_rename_async(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='async-lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')

        _input = {
            "name": "vol1",
            "pool": "pool3",
            "migration": True
        }
        a_volume.rename(_input, wait=True)

    def test_put(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')
        put_object = {
            'config': {'size': 1}
        }
        a_volume.put(put_object)

    def test_patch(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')
        patch_object = {
            'config': {'size': 1}
        }
        with mock.patch.object(self.client, 'assert_has_api_extension'):
            a_volume.patch(patch_object)

    def test_save(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')
        a_volume.config = {'size': 2}
        a_volume.save()

    def test_delete(self):
        add_api_extension_helper(self, ['storage'])
        a_storage_pool = models.StoragePool(self.client, name='lxd')
        a_volume = a_storage_pool.volumes.get('custom', 'cu1')
        a_volume.delete()
