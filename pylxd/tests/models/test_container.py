import contextlib
import json
import os
import shutil
import tempfile

import mock

from six.moves.urllib.parse import quote as url_quote

from pylxd import exceptions, models
from pylxd.tests import testing


class TestContainer(testing.PyLXDTestCase):
    """Tests for pylxd.models.Container."""

    def test_all(self):
        """A list of all containers are returned."""
        containers = models.Container.all(self.client)

        self.assertEqual(1, len(containers))

    def test_get(self):
        """Return a container."""
        name = 'an-container'

        an_container = models.Container.get(self.client, name)

        self.assertEqual(name, an_container.name)

    def test_get_not_found(self):
        """LXDAPIException is raised when the container doesn't exist."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/an-missing-container$',
        })

        name = 'an-missing-container'

        self.assertRaises(
            exceptions.LXDAPIException,
            models.Container.get, self.client, name)

    def test_get_error(self):
        """LXDAPIException is raised when the LXD API errors."""
        def not_found(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 500})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/an-missing-container$',
        })

        name = 'an-missing-container'

        self.assertRaises(
            exceptions.LXDAPIException,
            models.Container.get, self.client, name)

    def test_create(self):
        """A new container is created."""
        config = {'name': 'an-new-container'}

        an_new_container = models.Container.create(
            self.client, config, wait=True)

        self.assertEqual(config['name'], an_new_container.name)

    def test_create_remote(self):
        """A new container is created at target."""
        config = {'name': 'an-new-remote-container'}

        an_new_remote_container = models.Container.create(
            self.client, config, wait=True, target="an-remote")

        self.assertEqual(config['name'], an_new_remote_container.name)
        self.assertEqual("an-remote", an_new_remote_container.location)

    def test_exists(self):
        """A container exists."""
        name = 'an-container'

        self.assertTrue(models.Container.exists(self.client, name))

    def test_not_exists(self):
        """A container exists."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/an-missing-container$',
        })

        name = 'an-missing-container'

        self.assertFalse(models.Container.exists(self.client, name))

    def test_fetch(self):
        """A sync updates the properties of a container."""
        an_container = models.Container(
            self.client, name='an-container')

        an_container.sync()

        self.assertTrue(an_container.ephemeral)

    def test_fetch_not_found(self):
        """LXDAPIException is raised on a 404 for updating container."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/an-missing-container$',
        })

        an_container = models.Container(
            self.client, name='an-missing-container')

        self.assertRaises(exceptions.LXDAPIException, an_container.sync)

    def test_fetch_error(self):
        """LXDAPIException is raised on error."""
        def not_found(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'An bad error',
                'error_code': 500})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/an-missing-container$',
        })

        an_container = models.Container(
            self.client, name='an-missing-container')

        self.assertRaises(exceptions.LXDAPIException, an_container.sync)

    def test_update(self):
        """A container is updated."""
        an_container = models.Container(
            self.client, name='an-container')
        an_container.architecture = 1
        an_container.config = {}
        an_container.created_at = 1
        an_container.devices = {}
        an_container.ephemeral = 1
        an_container.expanded_config = {}
        an_container.expanded_devices = {}
        an_container.profiles = 1
        an_container.status = 1

        an_container.save(wait=True)

        self.assertTrue(an_container.ephemeral)

    def test_rename(self):
        an_container = models.Container(
            self.client, name='an-container')

        an_container.rename('an-renamed-container', wait=True)

        self.assertEqual('an-renamed-container', an_container.name)

    def test_delete(self):
        """A container is deleted."""
        # XXX: rockstar (21 May 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_container = models.Container(
            self.client, name='an-container')

        an_container.delete(wait=True)

    @testing.requires_ws4py
    @mock.patch('pylxd.models.container._StdinWebsocket')
    @mock.patch('pylxd.models.container._CommandWebsocketClient')
    def test_execute(self, _CommandWebsocketClient, _StdinWebsocket):
        """A command is executed on a container."""
        fake_websocket = mock.Mock()
        fake_websocket.data = 'test\n'
        _StdinWebsocket.return_value = fake_websocket
        _CommandWebsocketClient.return_value = fake_websocket

        an_container = models.Container(
            self.client, name='an-container')

        result = an_container.execute(['echo', 'test'])

        self.assertEqual(0, result.exit_code)
        self.assertEqual('test\n', result.stdout)

    def test_execute_no_ws4py(self):
        """If ws4py is not installed, ValueError is raised."""
        from pylxd.models import container
        old_installed = container._ws4py_installed
        container._ws4py_installed = False

        def cleanup():
            container._ws4py_installed = old_installed
        self.addCleanup(cleanup)

        an_container = models.Container(
            self.client, name='an-container')

        self.assertRaises(ValueError, an_container.execute, ['echo', 'test'])

    @testing.requires_ws4py
    def test_execute_string(self):
        """A command passed as string raises a TypeError."""
        an_container = models.Container(
            self.client, name='an-container')

        self.assertRaises(TypeError, an_container.execute, 'apt-get update')

    def test_raw_interactive_execute(self):
        an_container = models.Container(self.client, name='an-container')

        result = an_container.raw_interactive_execute(['/bin/bash'])

        self.assertEqual(result['ws'],
                         '/1.0/operations/operation-abc/websocket?secret=abc')
        self.assertEqual(result['control'],
                         '/1.0/operations/operation-abc/websocket?secret=jkl')

    def test_raw_interactive_execute_env(self):
        an_container = models.Container(self.client, name='an-container')

        result = an_container.raw_interactive_execute(['/bin/bash'],
                                                      {"PATH": "/"})

        self.assertEqual(result['ws'],
                         '/1.0/operations/operation-abc/websocket?secret=abc')
        self.assertEqual(result['control'],
                         '/1.0/operations/operation-abc/websocket?secret=jkl')

    def test_raw_interactive_execute_string(self):
        """A command passed as string raises a TypeError."""
        an_container = models.Container(
            self.client, name='an-container')

        self.assertRaises(TypeError,
                          an_container.raw_interactive_execute,
                          'apt-get update')

    def test_migrate(self):
        """A container is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint='http://pylxd2.test')
        an_container = models.Container(
            self.client, name='an-container')

        an_migrated_container = an_container.migrate(client2)

        self.assertEqual('an-container', an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)

    @mock.patch('pylxd.models.container.Container.generate_migration_data')
    def test_migrate_exception_error(self, generate_migration_data):
        """LXDAPIException is raised in case of migration failure"""
        from pylxd.client import Client
        from pylxd.exceptions import LXDAPIException

        def generate_exception(*args, **kwargs):
            response = mock.Mock()
            response.status_code = 400
            raise LXDAPIException(response)

        generate_migration_data.side_effect = generate_exception

        an_container = models.Container(
            self.client, name='an-container')

        client2 = Client(endpoint='http://pylxd2.test')
        self.assertRaises(LXDAPIException, an_container.migrate, client2)

    @mock.patch('pylxd.models.container.Container.generate_migration_data')
    def test_migrate_exception_running(self, generate_migration_data):
        """Migrated container already running on destination"""
        from pylxd.client import Client
        from pylxd.exceptions import LXDAPIException

        client2 = Client(endpoint='http://pylxd2.test')
        an_container = models.Container(
            self.client, name='an-container')
        an_container.status_code = 103

        def generate_exception(*args, **kwargs):
            response = mock.Mock()
            response.status_code = 103
            raise LXDAPIException(response)

        generate_migration_data.side_effect = generate_exception

        an_migrated_container = an_container.migrate(client2, live=True)

        self.assertEqual('an-container', an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)
        generate_migration_data.assert_called_once_with(True)

    def test_migrate_started(self):
        """A container is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint='http://pylxd2.test')
        an_container = models.Container.get(self.client, name='an-container')
        an_container.status_code = 103

        an_migrated_container = an_container.migrate(client2)

        self.assertEqual('an-container', an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)

    def test_migrate_stopped(self):
        """A container is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint='http://pylxd2.test')
        an_container = models.Container.get(self.client, name='an-container')
        an_container.status_code = 102

        an_migrated_container = an_container.migrate(client2)

        self.assertEqual('an-container', an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)

    @mock.patch('pylxd.client._APINode.get')
    def test_migrate_local_client(self, get):
        """Migration from local clients is not supported."""
        # Mock out the _APINode for the local instance.
        response = mock.Mock()
        response.json.return_value = {'metadata': {'fake': 'response'}}
        response.status_code = 200
        get.return_value = response

        from pylxd.client import Client

        client2 = Client(endpoint='http+unix://pylxd2.test')
        an_container = models.Container(
            client2, name='an-container')

        self.assertRaises(ValueError, an_container.migrate, self.client)

    def test_publish(self):
        """Containers can be published."""
        self.add_rule({
            'text': json.dumps({
                'type': 'sync',
                'metadata': {
                    'id': 'operation-abc',
                    'metadata': {
                        'fingerprint': ('e3b0c44298fc1c149afbf4c8996fb92427'
                                        'ae41e4649b934ca495991b7852b855')
                        }
                    }
                }),
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/operations/operation-abc$',
        })

        an_container = models.Container(
            self.client, name='an-container')

        image = an_container.publish(wait=True)

        self.assertEqual(
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            image.fingerprint)

    def test_restore_snapshot(self):
        """Snapshots can be restored"""
        an_container = models.Container(
            self.client, name='an-container')
        an_container.restore_snapshot('thing')


class TestContainerState(testing.PyLXDTestCase):
    """Tests for pylxd.models.ContainerState."""

    def test_get(self):
        """Return a container."""
        name = 'an-container'

        an_container = models.Container.get(self.client, name)
        state = an_container.state()

        self.assertEqual('Running', state.status)
        self.assertEqual(103, state.status_code)

    def test_start(self):
        """A container is started."""
        an_container = models.Container.get(self.client, 'an-container')

        an_container.start(wait=True)

    def test_stop(self):
        """A container is stopped."""
        an_container = models.Container.get(self.client, 'an-container')

        an_container.stop()

    def test_restart(self):
        """A container is restarted."""
        an_container = models.Container.get(self.client, 'an-container')

        an_container.restart()

    def test_freeze(self):
        """A container is suspended."""
        an_container = models.Container.get(self.client, 'an-container')

        an_container.freeze()

    def test_unfreeze(self):
        """A container is resumed."""
        an_container = models.Container.get(self.client, 'an-container')

        an_container.unfreeze()


class TestContainerSnapshots(testing.PyLXDTestCase):
    """Tests for pylxd.models.Container.snapshots."""

    def setUp(self):
        super(TestContainerSnapshots, self).setUp()
        self.container = models.Container.get(self.client, 'an-container')

    def test_get(self):
        """Return a specific snapshot."""
        snapshot = self.container.snapshots.get('an-snapshot')

        self.assertEqual('an-snapshot', snapshot.name)

    def test_all(self):
        """Return all snapshots."""
        snapshots = self.container.snapshots.all()

        self.assertEqual(1, len(snapshots))
        self.assertEqual('an-snapshot', snapshots[0].name)
        self.assertEqual(self.client, snapshots[0].client)
        self.assertEqual(self.container, snapshots[0].container)

    def test_create(self):
        """Create a snapshot."""
        snapshot = self.container.snapshots.create(
            'an-snapshot', stateful=True, wait=True)

        self.assertEqual('an-snapshot', snapshot.name)


class TestSnapshot(testing.PyLXDTestCase):
    """Tests for pylxd.models.Snapshot."""

    def setUp(self):
        super(TestSnapshot, self).setUp()
        self.container = models.Container.get(self.client, 'an-container')

    def test_rename(self):
        """A snapshot is renamed."""
        snapshot = models.Snapshot(
            self.client, container=self.container,
            name='an-snapshot')

        snapshot.rename('an-renamed-snapshot', wait=True)

        self.assertEqual('an-renamed-snapshot', snapshot.name)

    def test_delete(self):
        """A snapshot is deleted."""
        snapshot = models.Snapshot(
            self.client, container=self.container,
            name='an-snapshot')

        snapshot.delete(wait=True)

        # TODO: add an assertion here

    def test_delete_failure(self):
        """If the response indicates delete failure, raise an exception."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'DELETE',
            'url': (r'^http://pylxd.test/1.0/containers/'
                    'an-container/snapshots/an-snapshot$')
        })

        snapshot = models.Snapshot(
            self.client, container=self.container,
            name='an-snapshot')

        self.assertRaises(exceptions.LXDAPIException, snapshot.delete)

    def test_publish(self):
        """Snapshots can be published."""
        self.add_rule({
            'text': json.dumps({
                'type': 'sync',
                'metadata': {
                    'id': 'operation-abc',
                    'metadata': {
                        'fingerprint': ('e3b0c44298fc1c149afbf4c8996fb92427'
                                        'ae41e4649b934ca495991b7852b855')
                        }
                    }
                }),
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/operations/operation-abc$',
        })

        snapshot = models.Snapshot(
            self.client, container=self.container,
            name='an-snapshot')

        image = snapshot.publish(wait=True)

        self.assertEqual(
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            image.fingerprint)

    def test_restore_snapshot(self):
        """Snapshots can be restored from the snapshot object"""
        snapshot = models.Snapshot(
            self.client, container=self.container,
            name='an-snapshot')
        snapshot.restore(wait=True)


class TestFiles(testing.PyLXDTestCase):
    """Tests for pylxd.models.Container.files."""

    def setUp(self):
        super(TestFiles, self).setUp()
        self.container = models.Container.get(self.client, 'an-container')

    def test_put_delete(self):
        """A file is put on the container and then deleted"""
        # we are mocked, so delete should initially not be available
        self.assertEqual(False, self.container.files.delete_available())
        self.assertRaises(exceptions.LXDAPIExtensionNotAvailable,
                          self.container.files.delete, '/some/file')
        # Now insert delete
        self.add_rule({
            'text': json.dumps({
                'type': 'sync',
                'metadata': {'auth': 'trusted',
                             'environment': {
                                 'certificate': 'an-pem-cert',
                                 },
                             'api_extensions': ['file_delete']
                             }}),
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0$',
        })

        # Update hostinfo
        self.client.host_info = self.client.api.get().json()['metadata']

        self.assertEqual(True, self.container.files.delete_available())

        # mock out the delete rule:
        self.add_rule({
            'method': 'DELETE',
            'url': (r'^http://pylxd.test/1.0/containers/an-container/files'
                    r'\?path=%2Fsome%2Ffile$')
        })
        self.container.files.delete('/some/file')

        # now check that an error (non 200) causes an exception
        def responder(request, context):
            context.status_code = 404

        self.add_rule({
            'text': responder,
            'method': 'DELETE',
            'url': (r'^http://pylxd.test/1.0/containers/an-container/files'
                    r'\?path=%2Fsome%2Ffile%2Fnot%2Ffound$')
        })
        with self.assertRaises(exceptions.LXDAPIException):
            self.container.files.delete('/some/file/not/found')

    def test_put_mode_uid_gid(self):
        """Should be able to set the mode, uid and gid of a file"""
        # fix up the default POST rule to allow us to see the posted vars
        _capture = {}

        def capture(request, context):
            _capture['headers'] = getattr(request._request, 'headers')
            context.status_code = 200

        self.add_rule({
            'text': capture,
            'method': 'POST',
            'url': (r'^http://pylxd.test/1.0/containers/an-container/files'
                    r'\?path=%2Ftmp%2Fputted$'),
        })

        data = 'The quick brown fox'
        # start with an octal mode
        self.container.files.put('/tmp/putted', data, mode=0o123, uid=1, gid=2)
        headers = _capture['headers']
        self.assertEqual(headers['X-LXD-mode'], '0123')
        self.assertEqual(headers['X-LXD-uid'], '1')
        self.assertEqual(headers['X-LXD-gid'], '2')
        # use a str mode this type
        self.container.files.put('/tmp/putted', data, mode='456')
        headers = _capture['headers']
        self.assertEqual(headers['X-LXD-mode'], '0456')
        # check that mode='0644' also works (i.e. already has 0 prefix)
        self.container.files.put('/tmp/putted', data, mode='0644')
        headers = _capture['headers']
        self.assertEqual(headers['X-LXD-mode'], '0644')
        # check that assertion is raised
        with self.assertRaises(ValueError):
            self.container.files.put('/tmp/putted', data, mode=object)

    def test_recursive_put(self):

        @contextlib.contextmanager
        def tempdir(prefix='tmp'):
            tmpdir = tempfile.mkdtemp(prefix=prefix)
            try:
                yield tmpdir
            finally:
                shutil.rmtree(tmpdir)

        def create_file(_dir, name, content):
            path = os.path.join(_dir, name)
            actual_dir = os.path.dirname(path)
            if not os.path.exists(actual_dir):
                os.makedirs(actual_dir)
            with open(path, 'w') as f:
                f.write(content)

        _captures = []

        def capture(request, context):
            _captures.append({
                'headers': getattr(request._request, 'headers'),
                'body': request._request.body,
            })
            context.status_code = 200

        with tempdir() as _dir:
            base = (r'^http://pylxd.test/1.0/containers/'
                    r'an-container/files\?path=')
            rules = [
                {
                    'text': capture,
                    'method': 'POST',
                    'url': base + url_quote('target', safe='') + '$'
                },
                {
                    'text': capture,
                    'method': 'POST',
                    'url': base + url_quote('target/dir', safe='') + '$'
                },
                {
                    'text': capture,
                    'method': 'POST',
                    'url': base + url_quote('target/file1', safe='') + '$'
                },
                {
                    'text': capture,
                    'method': 'POST',
                    'url': base + url_quote('target/dir/file2',
                                            safe='') + '$'
                }
            ]
            self.add_rules(rules)

            create_file(_dir, 'file1', "This is file1")
            create_file(_dir, 'dir/file2', "This is file2")

            self.container.files.recursive_put(_dir, './target/')

            self.assertEqual(_captures[0]['headers']['X-LXD-type'],
                             'directory')
            self.assertEqual(_captures[1]['body'], b"This is file1")
            self.assertEqual(_captures[2]['headers']['X-LXD-type'],
                             'directory')
            self.assertEqual(_captures[3]['body'], b"This is file2")

    def test_get(self):
        """A file is retrieved from the container."""
        data = self.container.files.get('/tmp/getted')

        self.assertEqual(b'This is a getted file', data)

    def test_get_not_found(self):
        """LXDAPIException is raised on bogus filenames."""
        def not_found(request, context):
            context.status_code = 500
        rule = {
            'text': not_found,
            'method': 'GET',
            'url': (r'^http://pylxd.test/1.0/containers/an-container/files'
                    r'\?path=%2Ftmp%2Fgetted$'),
        }
        self.add_rule(rule)

        self.assertRaises(
            exceptions.LXDAPIException,
            self.container.files.get, '/tmp/getted')

    def test_get_error(self):
        """LXDAPIException is raised on error."""
        def not_found(request, context):
            context.status_code = 503
        rule = {
            'text': not_found,
            'method': 'GET',
            'url': (r'^http://pylxd.test/1.0/containers/an-container/files'
                    r'\?path=%2Ftmp%2Fgetted$'),
        }
        self.add_rule(rule)

        self.assertRaises(
            exceptions.LXDAPIException,
            self.container.files.get, '/tmp/getted')

    # for bug/281 -- getting an empty json file is interpreted as an API
    # get rather than a raw get.
    def test_get_json_file(self):
        data = self.container.files.get('/tmp/json-get')
        self.assertEqual(b'{"some": "value"}', data)
