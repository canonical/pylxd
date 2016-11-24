import json

from pylxd import exceptions, models
from pylxd.tests import testing


class TestProfile(testing.PyLXDTestCase):
    """Tests for pylxd.models.Profile."""

    def test_get(self):
        """A profile is fetched."""
        name = 'an-profile'
        an_profile = models.Profile.get(self.client, name)

        self.assertEqual(name, an_profile.name)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown profiles."""
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
            exceptions.LXDAPIException,
            models.Profile.get, self.client, 'an-profile')

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
            models.Profile.get, self.client, 'an-profile')

    def test_exists(self):
        name = 'an-profile'

        self.assertTrue(models.Profile.exists(self.client, name))

    def test_not_exists(self):
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

        name = 'an-profile'

        self.assertFalse(models.Profile.exists(self.client, name))

    def test_all(self):
        """A list of all profiles is returned."""
        profiles = models.Profile.all(self.client)

        self.assertEqual(1, len(profiles))

    def test_create(self):
        """A new profile is created."""
        an_profile = models.Profile.create(
            self.client, name='an-new-profile', config={}, devices={})

        self.assertIsInstance(an_profile, models.Profile)
        self.assertEqual('an-new-profile', an_profile.name)

    def test_rename(self):
        """A profile is renamed."""
        an_profile = models.Profile.get(self.client, 'an-profile')

        an_renamed_profile = an_profile.rename('an-renamed-profile')

        self.assertEqual('an-renamed-profile', an_renamed_profile.name)

    def test_update(self):
        """A profile is updated."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = models.Profile.get(self.client, 'an-profile')

        an_profile.save()

        self.assertEqual({}, an_profile.config)

    def test_fetch(self):
        """A partially fetched profile is made complete."""
        an_profile = self.client.profiles.all()[0]

        an_profile.sync()

        self.assertEqual('An description', an_profile.description)

    def test_fetch_notfound(self):
        """LXDAPIException is raised on bogus profile fetches."""
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

        an_profile = models.Profile(self.client, name='an-profile')

        self.assertRaises(exceptions.LXDAPIException, an_profile.sync)

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

        an_profile = models.Profile(self.client, name='an-profile')

        self.assertRaises(exceptions.LXDAPIException, an_profile.sync)

    def test_delete(self):
        """A profile is deleted."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = self.client.profiles.all()[0]

        an_profile.delete()
