import json

from pylxd import container, exceptions
from pylxd.tests import testing


class TestContainer(testing.PyLXDTestCase):
    """Tests for pylxd.container.Container."""

    def test_all(self):
        """A list of all containers are returned."""
        containers = container.Container.all(self.client)

        self.assertEqual(1, len(containers))

    def test_get(self):
        """Return a container."""
        name = 'an-container'

        an_container = container.Container.get(self.client, name)

        self.assertEqual(name, an_container.name)

    def test_get_not_found(self):
        """NameError is raised when the container doesn't exist."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',  # NOQA
        })

        name = 'an-missing-container'

        self.assertRaises(
            exceptions.NotFound,
            container.Container.get, self.client, name)

    def test_create(self):
        """A new container is created."""
        config = {'name': 'an-new-container'}

        an_new_container = container.Container.create(
            self.client, config, wait=True)

        self.assertEqual(config['name'], an_new_container.name)

    def test_create_failed(self):
        """If the container creation fails, CreateFailed is raised."""
        def create_fail(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'An unknown error',
                'error_code': 500})
        self.add_rule({
            'text': create_fail,
            'method': 'POST',
            'url': r'^http://pylxd.test/1.0/containers$',
        })
        config = {'name': 'an-new-container'}

        self.assertRaises(
            exceptions.CreateFailed,
            container.Container.create, self.client, config)

    def test_reload(self):
        """A reload updates the properties of a container."""
        an_container = container.Container(
            name='an-container', _client=self.client)

        an_container.reload()

        self.assertTrue(an_container.ephemeral)

    def test_reload_not_found(self):
        """NameError is raised on a 404 for updating container."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',  # NOQA
        })

        an_container = container.Container(
            name='an-missing-container', _client=self.client)

        self.assertRaises(NameError, an_container.reload)

    def test_update(self):
        """A container is updated."""
        an_container = container.Container(
            name='an-container', _client=self.client)
        an_container.architecture = 1
        an_container.config = {}
        an_container.created_at = 1
        an_container.devices = {}
        an_container.ephemeral = 1
        an_container.expanded_config = {}
        an_container.expanded_devices = {}
        an_container.profiles = 1
        an_container.status = 1

        an_container.update(wait=True)

        self.assertTrue(an_container.ephemeral)

    def test_update_partial_objects(self):
        """A partially fetched profile can't be pushed."""
        an_container = self.client.containers.all()[0]

        self.assertRaises(
            exceptions.ObjectIncomplete,
            an_container.update)

    def test_rename(self):
        an_container = container.Container(
            name='an-container', _client=self.client)

        an_container.rename('an-renamed-container', wait=True)

        self.assertEqual('an-renamed-container', an_container.name)

    def test_delete(self):
        """A container is deleted."""
        # XXX: rockstar (21 May 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_container = container.Container(
            name='an-container', _client=self.client)

        an_container.delete(wait=True)


class TestContainerState(testing.PyLXDTestCase):
    """Tests for pylxd.container.ContainerState."""

    def test_get(self):
        """Return a container."""
        name = 'an-container'

        an_container = container.Container.get(self.client, name)
        state = an_container.state()

        self.assertEqual('Running', state.status)
        self.assertEqual(103, state.status_code)


class TestContainerSnapshots(testing.PyLXDTestCase):
    """Tests for pylxd.container.Container.snapshots."""

    def setUp(self):
        super(TestContainerSnapshots, self).setUp()
        self.container = container.Container.get(self.client, 'an-container')

    def test_get(self):
        """Return a specific snapshot."""
        snapshot = self.container.snapshots.get('an-snapshot')

        self.assertEqual('an-snapshot', snapshot.name)

    def test_all(self):
        """Return all snapshots."""
        snapshots = self.container.snapshots.all()

        self.assertEqual(1, len(snapshots))
        self.assertEqual('an-snapshot', snapshots[0].name)
        self.assertEqual(self.client, snapshots[0]._client)
        self.assertEqual(self.container, snapshots[0]._container)

    def test_create(self):
        """Create a snapshot."""
        snapshot = self.container.snapshots.create(
            'an-snapshot', stateful=True, wait=True)

        self.assertEqual('an-snapshot', snapshot.name)


class TestSnapshot(testing.PyLXDTestCase):
    """Tests for pylxd.container.Snapshot."""

    def setUp(self):
        super(TestSnapshot, self).setUp()
        self.container = container.Container.get(self.client, 'an-container')

    def test_rename(self):
        """A snapshot is renamed."""
        snapshot = container.Snapshot(
            _client=self.client, _container=self.container,
            name='an-snapshot')

        snapshot.rename('an-renamed-snapshot', wait=True)

        self.assertEqual('an-renamed-snapshot', snapshot.name)

    def test_delete(self):
        """A snapshot is deleted."""
        snapshot = container.Snapshot(
            _client=self.client, _container=self.container,
            name='an-snapshot')

        snapshot.delete(wait=True)

        # TODO: add an assertion here

    def test_delete_failure(self):
        """If the response indicates delete failure, raise RuntimeError."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'DELETE',
            'url': r'^http://pylxd.test/1.0/containers/(?P<container>.*)/snapshots/(?P<snapshot>.*)$',  # NOQA
        })

        snapshot = container.Snapshot(
            _client=self.client, _container=self.container,
            name='an-snapshot')

        self.assertRaises(RuntimeError, snapshot.delete)
