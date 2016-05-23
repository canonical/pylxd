from pylxd import container
from pylxd.exceptions import ContainerCreationFailure
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
        name = 'an-missing-container'

        self.assertRaises(
            NameError, container.Container.get, self.client, name)

    def test_create(self):
        """A new container is created."""
        config = {'name': 'an-new-container'}

        an_new_container = container.Container.create(
            self.client, config, wait=True)

        self.assertEqual(config['name'], an_new_container.name)

    def test_create_failure(self):
        """Container creation API responds with an error."""
        config = {'name': 'fake-fail'}

        with self.assertRaises(ContainerCreationFailure) as e:
            container.Container.create(self.client, config, wait=True)

        # Check that we have the response object
        self.assertEqual(e.exception.response.status_code, 400)

    def test_reload(self):
        """A reload updates the properties of a container."""
        an_container = container.Container(
            name='an-container', _client=self.client)

        an_container.reload()

        self.assertTrue(an_container.ephemeral)

    def test_reload_not_found(self):
        """NameError is raised on a 404 for updating container."""
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
