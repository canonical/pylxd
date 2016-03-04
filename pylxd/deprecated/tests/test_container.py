# Copyright (c) 2015 Canonical Ltd
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

from collections import OrderedDict
from ddt import ddt
import json
import mock
import tempfile

from pylxd.deprecated import connection

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=('200', fake_api.fake_operation()))
class LXDAPIContainerTestObject(LXDAPITestBase):

    def test_list_containers(self, ms):
        ms.return_value = ('200', fake_api.fake_container_list())
        self.assertEqual(
            ['trusty-1'],
            self.lxd.container_list())
        ms.assert_called_once_with('GET',
                                   '/1.0/containers')

    @annotated_data(
        ('STOPPED', False),
        ('STOPPING', False),
        ('ABORTING', False),
        ('RUNNING', True),
        ('STARTING', True),
        ('FREEZING', True),
        ('FROZEN', True),
        ('THAWED', True),
    )
    def test_container_running(self, status, running, ms):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_container_state(status))
            self.assertEqual(running, self.lxd.container_running('trusty-1'))
            ms.assert_called_once_with('GET',
                                       '/1.0/containers/trusty-1/state')

    def test_container_init(self, ms):
        self.assertEqual(ms.return_value, self.lxd.container_init('fake'))
        ms.assert_called_once_with('POST',
                                   '/1.0/containers',
                                   '"fake"')

    def test_container_update(self, ms):
        self.assertEqual(ms.return_value,
                         self.lxd.container_update('trusty-1',
                                                   'fake'))
        ms.assert_called_once_with('PUT',
                                   '/1.0/containers/trusty-1',
                                   '"fake"')

    def test_container_state(self, ms):
        ms.return_value = ('200', fake_api.fake_container_state('RUNNING'))
        self.assertEqual(ms.return_value, self.lxd.container_state('trusty-1'))
        ms.assert_called_with('GET',
                              '/1.0/containers/trusty-1/state')

    @annotated_data(
        ('start', 'start'),
        ('stop', 'stop'),
        ('suspend', 'freeze'),
        ('resume', 'unfreeze'),
        ('reboot', 'restart'),
    )
    def test_container_actions(self, method, action, ms):
        self.assertEqual(
            ms.return_value,
            getattr(self.lxd, 'container_' + method)('trusty-1', 30))
        ms.assert_called_once_with('PUT',
                                   '/1.0/containers/trusty-1/state',
                                   json.dumps({'action': action,
                                               'force': True,
                                               'timeout': 30, }))

    def test_container_destroy(self, ms):
        self.assertEqual(
            ms.return_value, self.lxd.container_destroy('trusty-1'))
        ms.assert_called_once_with('DELETE',
                                   '/1.0/containers/trusty-1')

    def test_container_log(self, ms):
        ms.return_value = ('200', fake_api.fake_container_log())
        self.assertEqual(
            'fake log', self.lxd.get_container_log('trusty-1'))
        ms.assert_called_once_with('GET',
                                   '/1.0/containers/trusty-1?log=true')

    def test_container_config(self, ms):
        ms.return_value = ('200', fake_api.fake_container_state('fake'))
        self.assertEqual(
            {'status': 'fake'}, self.lxd.get_container_config('trusty-1'))
        ms.assert_called_once_with('GET',
                                   '/1.0/containers/trusty-1?log=false')

    def test_container_info(self, ms):
        ms.return_value = ('200', fake_api.fake_container_state('fake'))
        self.assertEqual(
            {'status': 'fake'}, self.lxd.container_info('trusty-1'))
        ms.assert_called_once_with('GET',
                                   '/1.0/containers/trusty-1/state')

    def test_container_migrate(self, ms):
        ms.return_value = ('200', fake_api.fake_container_migrate())
        self.assertEqual(
            ('200', {'type': 'sync', 'status': 'Success',
                     'metadata': {'criu': 'fake_criu', 'fs':
                                  'fake_fs', 'control':
                                  'fake_control'}, 'operation':
                     '/1.0/operations/1234', 'status_code': 200}),
            self.lxd.container_migrate('trusty-1'))
        ms.assert_called_once_with('POST',
                                   '/1.0/containers/trusty-1',
                                   '{"migration": true}')

    def test_container_publish(self, ms):
        ms.return_value = ('200', fake_api.fake_operation())
        self.assertEqual(
            ms.return_value, self.lxd.container_publish('trusty-1'))
        ms.assert_called_once_with('POST',
                                   '/1.0/images',
                                   '"trusty-1"')

    def test_container_put_file(self, ms):
        temp_file = tempfile.NamedTemporaryFile()
        ms.return_value = ('200', fake_api.fake_standard_return())
        self.assertEqual(
            ms.return_value, self.lxd.put_container_file('trusty-1',
                                                         temp_file.name,
                                                         'dst_file'))
        ms.assert_called_once_with(
            'POST',
            '/1.0/containers/trusty-1/files?path=dst_file',
            body=b'',
            headers={'X-LXD-gid': 0, 'X-LXD-mode': 0o644, 'X-LXD-uid': 0})

    def test_list_snapshots(self, ms):
        ms.return_value = ('200', fake_api.fake_snapshots_list())
        self.assertEqual(
            ['/1.0/containers/trusty-1/snapshots/first'],
            self.lxd.container_snapshot_list('trusty-1'))
        ms.assert_called_once_with('GET',
                                   '/1.0/containers/trusty-1/snapshots')

    @annotated_data(
        ('create', 'POST', '', ('fake config',), ('"fake config"',)),
        ('info', 'GET', '/first', ('first',), ()),
        ('rename', 'POST', '/first',
         ('first', 'fake config'), ('"fake config"',)),
        ('delete', 'DELETE', '/first', ('first',), ()),
    )
    def test_snapshot_operations(self, method, http, path,
                                 args, call_args, ms):
        self.assertEqual(
            ms.return_value,
            getattr(self.lxd,
                    'container_snapshot_' + method)('trusty-1', *args))
        ms.assert_called_once_with(http,
                                   '/1.0/containers/trusty-1/snapshots' +
                                   path,
                                   *call_args)

    def test_container_run_command(self, ms):
        data = OrderedDict((
            ('command', ['/fake/command']),
            ('interactive', False),
            ('wait-for-websocket', False),
            ('environment', {'FAKE_ENV': 'fake'})
        ))

        self.assertEqual(
            ms.return_value,
            self.lxd.container_run_command('trusty-1', *data.values()))
        self.assertEqual(1, ms.call_count)
        self.assertEqual(
            ms.call_args[0][:2],
            ('POST', '/1.0/containers/trusty-1/exec'))
        self.assertEqual(
            json.loads(ms.call_args[0][2]),
            dict(data)
        )


@ddt
@mock.patch.object(connection.LXDConnection, 'get_object',
                   return_value=('200', fake_api.fake_container_list()))
class LXDAPIContainerTestStatus(LXDAPITestBase):

    def test_container_defined(self, ms):
        self.assertTrue(self.lxd.container_defined('trusty-1'))
        ms.assert_called_once_with('GET', '/1.0/containers')


@ddt
@mock.patch.object(connection.LXDConnection, 'get_raw',
                   return_value='fake contents')
class LXDAPIContainerTestRaw(LXDAPITestBase):

    def test_container_file(self, ms):
        self.assertEqual(
            'fake contents', self.lxd.get_container_file('trusty-1',
                                                         '/file/name'))
        ms.assert_called_once_with(
            'GET', '/1.0/containers/trusty-1/files?path=/file/name')
