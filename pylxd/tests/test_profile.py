from pylxd import profile
from pylxd.tests import testing


class TestProfile(testing.PyLXDTestCase):
    """Tests for pylxd.profile.Profile."""

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
