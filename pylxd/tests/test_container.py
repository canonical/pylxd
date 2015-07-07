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
from ddt import data
from ddt import ddt
import json
import mock
import unittest

from pylxd import api
from pylxd import connection

from pylxd.tests import annotated_data
from pylxd.tests import fake_api


@ddt
class LXDUnitTestContainer(unittest.TestCase):

    def setUp(self):
        super(LXDUnitTestContainer, self).setUp()
        self.lxd = api.API()

    def test_list_containers(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_container_list())
            self.assertEqual(
                ['trusty-1'],
                self.lxd.container_list())
            ms.assert_called_with('GET',
                                  '/1.0/containers')

    @data(True, False)
    def test_container_defined(self, defined):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = defined
            self.assertEqual(defined, self.lxd.container_defined('trusty-1'))
            ms.assert_called_with('GET',
                                  '/1.0/containers/trusty-1/state')

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
    def test_container_running(self, status, running):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_container_state(status))
            self.assertEqual(running, self.lxd.container_running('trusty-1'))
            ms.assert_called_with('GET',
                                  '/1.0/containers/trusty-1/state')

    def test_container_init(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(ms.return_value, self.lxd.container_init('fake'))
            ms.assert_called_with('POST',
                                  '/1.0/containers',
                                  '"fake"')

    def test_container_update(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(ms.return_value,
                             self.lxd.container_update('trusty-1',
                                                       'fake'))
            ms.assert_called_with('PUT',
                                  '/1.0/containers/trusty-1',
                                  '"fake"')

    def test_container_state(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_container_state('RUNNING'))
            self.assertEqual('RUNNING', self.lxd.container_state('trusty-1'))
            ms.assert_called_with('GET',
                                  '/1.0/containers/trusty-1/state')

    @annotated_data(
        ('start', 'start'),
        ('stop', 'stop'),
        ('suspend', 'freeze'),
        ('resume', 'unfreeze'),
        ('reboot', 'restart'),
    )
    def test_container_actions(self, method, action):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(
                ms.return_value,
                getattr(self.lxd, 'container_' + method)('trusty-1', 30))
            ms.assert_called_with('PUT',
                                  '/1.0/containers/trusty-1/state',
                                  json.dumps({'action': action,
                                              'timeout': 30}))

    def test_container_destroy(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(
                ms.return_value, self.lxd.container_destroy('trusty-1'))
            ms.assert_called_with('DELETE',
                                  '/1.0/containers/trusty-1')

    def test_container_log(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_container_log())
            self.assertEqual(
                'fake log', self.lxd.get_container_log('trusty-1'))
            ms.assert_called_with('GET',
                                  '/1.0/containers/trusty-1?log=true')

    def test_container_file(self):
        with mock.patch.object(connection.LXDConnection, 'get_raw') as ms:
            ms.return_value = 'fake contents'
            self.assertEqual(
                'fake contents', self.lxd.get_container_file('trusty-1',
                                                             '/file/name'))
            ms.assert_called_with(
                'GET', '/1.0/containers/trusty-1/files?path=/file/name')

    def test_container_publish(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(
                ms.return_value, self.lxd.container_publish('trusty-1'))
            ms.assert_called_with('POST',
                                  '/1.0/images',
                                  '"trusty-1"')

    def test_container_put_file(self):
        self.assertRaises(NotImplementedError, self.lxd.put_container_file)

    def test_list_snapshots(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_snapshots_list())
            self.assertEqual(
                ['/1.0/containers/trusty-1/snapshots/first'],
                self.lxd.container_snapshot_list('trusty-1'))

    @annotated_data(
        ('create', 'POST', '', ('fake config',), ('"fake config"',)),
        ('info', 'GET', '/first', ('first',)),
        ('rename', 'POST', '/first',
         ('first', 'fake config'), ('"fake config"',)),
        ('delete', 'DELETE', '/first', ('first',)),
    )
    def test_snapshot_operations(self, method, http, path, args, call_args=()):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            self.assertEqual(
                ms.return_value,
                getattr(self.lxd,
                        'container_snapshot_' + method)('trusty-1', *args))
            ms.assert_called_with(http,
                                  '/1.0/containers/trusty-1/snapshots' + path,
                                  *call_args)

    def test_container_run_command(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_operation())
            data = OrderedDict((
                ('command', ['/fake/command']),
                ('interactive', False),
                ('wait-for-websocket', False),
                ('environment', {'FAKE_ENV': 'fake'})
            ))

            self.assertEqual(
                ms.return_value,
                self.lxd.container_run_command('trusty-1', *data.values()))
            ms.assert_called_with('POST',
                                  '/1.0/containers/trusty-1/exec',
                                  json.dumps(dict(data)))
