import json

from pylxd import exceptions, profile
from pylxd.tests import testing


class TestProfile(testing.PyLXDTestCase):
    """Tests for pylxd.profile.Profile."""

    def test_get(self):
        """A profile is fetched."""
        name = 'an-profile'
        an_profile = profile.Profile.get(self.client, name)

        self.assertEqual(name, an_profile.name)

    def test_get_not_found(self):
        """NotFound is raised on unknown profiles."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/profiles/an-profile$',
        })

        self.assertRaises(
            exceptions.NotFound,
            profile.Profile.get, self.client, 'an-profile')

    def test_get_error(self):
        """LXDAPIException is raised on get error."""
        def error(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 500})
        self.add_rule({
            'text': error,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/profiles/an-profile$',
        })

        self.assertRaises(
            exceptions.LXDAPIException,
            profile.Profile.get, self.client, 'an-profile')

    def test_all(self):
        """A list of all profiles is returned."""
        profiles = profile.Profile.all(self.client)

        self.assertEqual(1, len(profiles))

    def test_create(self):
        """A new profile is created."""
        an_profile = profile.Profile.create(
            self.client, name='an-new-profile', config={}, devices={})

        self.assertIsInstance(an_profile, profile.Profile)
        self.assertEqual('an-new-profile', an_profile.name)

    def test_rename(self):
        """Profiles cannot yet be renamed."""
        an_profile = profile.Profile.get(self.client, 'an-profile')

        self.assertRaises(
            NotImplementedError, an_profile.rename, 'an-renamed-profile')

    def test_create_failed(self):
        """CreateFailed is raised when errors occur."""
        def error(request, context):
            context.status_code = 503
            return json.dumps({
                'type': 'error',
                'error': 'An unknown error',
                'error_code': 500})
        self.add_rule({
            'text': error,
            'method': 'POST',
            'url': r'^http://pylxd.test/1.0/profiles$',
        })

        self.assertRaises(
            exceptions.CreateFailed,
            profile.Profile.create, self.client,
            name='an-new-profile', config={})

    def test_update(self):
        """A profile is updated."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = profile.Profile.get(self.client, 'an-profile')

        an_profile.update()

        self.assertEqual({}, an_profile.config)

    def test_update_partial_objects(self):
        """A partially fetched profile can't be pushed."""
        an_profile = self.client.profiles.all()[0]

        self.assertRaises(
            exceptions.ObjectIncomplete,
            an_profile.update)

    def test_fetch(self):
        """A partially fetched profile is made complete."""
        an_profile = self.client.profiles.all()[0]

        an_profile.fetch()

        self.assertEqual('An description', an_profile.description)

    def test_fetch_notfound(self):
        """NotFound is raised on bogus profile fetches."""
        def not_found(request, context):
            context.status_code = 404
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 404})
        self.add_rule({
            'text': not_found,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/profiles/an-profile$',
        })

        an_profile = profile.Profile(name='an-profile', _client=self.client)

        self.assertRaises(exceptions.NotFound, an_profile.fetch)

    def test_fetch_error(self):
        """LXDAPIException is raised on fetch error."""
        def error(request, context):
            context.status_code = 500
            return json.dumps({
                'type': 'error',
                'error': 'Not found',
                'error_code': 500})
        self.add_rule({
            'text': error,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/profiles/an-profile$',
        })

        an_profile = profile.Profile(name='an-profile', _client=self.client)

        self.assertRaises(exceptions.LXDAPIException, an_profile.fetch)

    def test_delete(self):
        """A profile is deleted."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = self.client.profiles.all()[0]

        an_profile.delete()
