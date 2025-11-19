import json
from unittest import mock

from pylxd import exceptions, models
from pylxd.tests import testing


class TestProfile(testing.PyLXDTestCase):
    """Tests for pylxd.models.Profile."""

    def test_get(self):
        """A profile is fetched."""
        name = "an-profile"
        an_profile = models.Profile.get(self.client, name)

        self.assertEqual(name, an_profile.name)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown profiles."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles/an-profile$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Profile.get, self.client, "an-profile"
        )

    def test_get_error(self):
        """LXDAPIException is raised on get error."""

        def error(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles/an-profile$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Profile.get, self.client, "an-profile"
        )

    def test_exists(self):
        name = "an-profile"

        self.assertTrue(models.Profile.exists(self.client, name))

    def test_not_exists(self):
        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles/an-profile$",
            }
        )

        name = "an-profile"

        self.assertFalse(models.Profile.exists(self.client, name))

    def test_all(self):
        """A list of all profiles is returned."""
        profiles = models.Profile.all(self.client)

        self.assertEqual(1, len(profiles))

    def test_create(self):
        """A new profile is created."""
        an_profile = models.Profile.create(
            self.client, name="an-new-profile", config={}, devices={}
        )

        self.assertIsInstance(an_profile, models.Profile)
        self.assertEqual("an-new-profile", an_profile.name)

    def test_rename(self):
        """A profile is renamed."""
        an_profile = models.Profile.get(self.client, "an-profile")

        an_renamed_profile = an_profile.rename("an-renamed-profile")

        self.assertEqual("an-renamed-profile", an_renamed_profile.name)

    def test_update(self):
        """A profile is updated."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = models.Profile.get(self.client, "an-profile")

        an_profile.save()

        self.assertEqual({}, an_profile.config)

    def test_fetch(self):
        """A partially fetched profile is made complete."""
        an_profile = self.client.profiles.all()[0]

        an_profile.sync()

        self.assertEqual("An description", an_profile.description)

    def test_fetch_notfound(self):
        """LXDAPIException is raised on bogus profile fetches."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles/an-profile$",
            }
        )

        an_profile = models.Profile(self.client, name="an-profile")

        self.assertRaises(exceptions.LXDAPIException, an_profile.sync)

    def test_fetch_error(self):
        """LXDAPIException is raised on fetch error."""

        def error(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": error,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles/an-profile$",
            }
        )

        an_profile = models.Profile(self.client, name="an-profile")

        self.assertRaises(exceptions.LXDAPIException, an_profile.sync)

    def test_delete(self):
        """A profile is deleted."""
        # XXX: rockstar (03 Jun 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_profile = self.client.profiles.all()[0]

        an_profile.delete()


class TestProfileAsync(testing.PyLXDTestCase):
    """Tests for async operations in Profile."""

    def setUp(self):
        super().setUp()
        self.mock_wait = mock.patch.object(
            self.client.operations, "wait_for_operation"
        ).start()
        self.addCleanup(mock.patch.stopall)
        self.profile_name = "test-profile"
        self.operation_id = "/1.0/operations/test-op"

    def _mock_async_response(self, method="POST", url_suffix="", operation_id=None):
        """Helper to mock async operation responses."""
        if operation_id is None:
            operation_id = self.operation_id

        base_url = "http://pylxd.test/1.0/profiles"
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

    def _mock_sync_response(self, method="POST", url_suffix="", status_code=200):
        """Helper to mock sync operation responses."""
        base_url = "http://pylxd.test/1.0/profiles"
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": status_code,
                },
                "status_code": status_code,
                "method": method,
                "url": f"^{base_url}{url_suffix}$",
            }
        )

    def _mock_profile_data(
        self, name=None, description=None, config=None, devices=None
    ):
        """Helper to mock profile GET response data."""
        if name is None:
            name = self.profile_name
        if description is None:
            description = f"Test profile {name}"
        if config is None:
            config = {}
        if devices is None:
            devices = {}

        return {
            "name": name,
            "description": description,
            "config": config,
            "devices": devices,
            "used_by": [],
        }

    def _mock_profile_get(self, name=None, **kwargs):
        """Mock GET profile response."""
        profile_data = self._mock_profile_data(name=name, **kwargs)
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": 200,
                    "metadata": profile_data,
                },
                "method": "GET",
                "url": rf"^http://pylxd.test/1.0/profiles/{name or self.profile_name}$",
            }
        )

    def _mock_profiles_list(self, profiles=None):
        """Mock the profiles list response."""
        if profiles is None:
            profiles = [self.profile_name]

        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "status": "Success",
                    "status_code": 200,
                    "metadata": [f"/1.0/profiles/{name}" for name in profiles],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/profiles$",
            }
        )

    def _create_test_profile(self, name=None, **kwargs):
        """Helper to create a test profile instance."""
        if name is None:
            name = self.profile_name
        return models.Profile(self.client, name=name, **kwargs)

    def _assert_async_operation_waited(self, operation_id=None):
        """Assert that an async operation was waited for."""
        if operation_id is None:
            operation_id = self.operation_id
        self.mock_wait.assert_called_once_with(operation_id)

    def _assert_no_async_wait(self):
        """Assert that no async operation was waited for."""
        self.mock_wait.assert_not_called()

    def test_create_async_with_wait(self):
        """Test async profile creation with wait=True"""
        self._mock_async_response()
        self._mock_profile_get()

        profile = models.Profile.create(
            self.client,
            name=self.profile_name,
            config={"limits.cpu": "2"},
            description="Test profile",
            wait=True,
        )

        self._assert_async_operation_waited()
        self.assertEqual(self.profile_name, profile.name)

    def test_create_async_without_wait(self):
        """Test async profile creation with wait=False"""
        self._mock_async_response()
        self._mock_profile_get()

        profile = models.Profile.create(
            self.client, name=self.profile_name, config={"limits.cpu": "2"}, wait=False
        )

        self._assert_no_async_wait()
        self.assertEqual(self.profile_name, profile.name)

    def test_rename_async_with_wait(self):
        """Test async profile rename with wait=True"""
        profile = self._create_test_profile(name="old-profile")

        self._mock_async_response(url_suffix="/old-profile")
        self._mock_profile_get(name="new-profile")

        result = profile.rename("new-profile", wait=True)

        self._assert_async_operation_waited()
        self.assertEqual("new-profile", result.name)

    def test_rename_async_without_wait(self):
        """Test async profile rename with wait=False"""
        profile = self._create_test_profile(name="old-profile")

        self._mock_async_response(url_suffix="/old-profile")
        self._mock_profile_get(name="new-profile")

        result = profile.rename("new-profile", wait=False)

        self._assert_no_async_wait()
        self.assertEqual("new-profile", result.name)

    def test_save_async_with_wait(self):
        """Test async profile save with wait=True"""
        profile = self._create_test_profile(description="Original description")
        profile.description = "Updated description"

        self._mock_async_response(method="PUT", url_suffix=f"/{self.profile_name}")
        self._mock_profile_get(description="Updated description")

        profile.save(wait=True)

        self._assert_async_operation_waited()

    def test_put_async_with_wait(self):
        """Test async profile put with wait=True"""
        profile = self._create_test_profile()

        put_object = {
            "config": {"limits.cpu": "4"},
            "description": "Updated via PUT",
            "devices": {},
        }

        self._mock_async_response(method="PUT", url_suffix=f"/{self.profile_name}")
        self._mock_profile_get(
            description="Updated via PUT", config={"limits.cpu": "4"}
        )

        profile.put(put_object, wait=True)

        self._assert_async_operation_waited()

    def test_patch_async_with_wait(self):
        """Test async profile patch with wait=True"""
        profile = self._create_test_profile()

        patch_object = {"description": "Updated via PATCH"}

        self._mock_async_response(method="PATCH", url_suffix=f"/{self.profile_name}")
        self._mock_profile_get(description="Updated via PATCH")

        profile.patch(patch_object, wait=True)

        self._assert_async_operation_waited()

    def test_delete_async_with_wait(self):
        """Test async profile delete with wait=True"""
        profile = self._create_test_profile()

        self._mock_async_response(method="DELETE", url_suffix=f"/{self.profile_name}")

        profile.delete(wait=True)

        self._assert_async_operation_waited()

    def test_delete_async_without_wait(self):
        """Test async profile delete with wait=False"""
        profile = self._create_test_profile()

        self._mock_async_response(method="DELETE", url_suffix=f"/{self.profile_name}")

        profile.delete(wait=False)

        self._assert_no_async_wait()

    def test_sync_response_handling(self):
        """Test that sync responses work correctly (no waiting)"""
        self._mock_sync_response()
        self._mock_profile_get()

        profile = models.Profile.create(self.client, name=self.profile_name, wait=True)

        self._assert_no_async_wait()
        self.assertEqual(self.profile_name, profile.name)

    def test_multiple_operations_same_test(self):
        """Test multiple async operations in sequence"""
        # First operation - create with wait
        self._mock_async_response(operation_id="/1.0/operations/create-op")
        self._mock_profile_get()

        profile = models.Profile.create(self.client, name=self.profile_name, wait=True)
        self.mock_wait.assert_called_with("/1.0/operations/create-op")

        # Reset mock for second operation
        self.mock_wait.reset_mock()

        # Second operation - rename with wait
        self._mock_async_response(
            method="POST",
            url_suffix=f"/{self.profile_name}",
            operation_id="/1.0/operations/rename-op",
        )
        self._mock_profile_get(name="renamed-profile")

        result = profile.rename("renamed-profile", wait=True)
        self.mock_wait.assert_called_with("/1.0/operations/rename-op")

        # Reset mock for third operation
        self.mock_wait.reset_mock()

        # Third operation - delete without wait
        self._mock_async_response(
            method="DELETE",
            url_suffix="/renamed-profile",
            operation_id="/1.0/operations/delete-op",
        )

        result.delete(wait=False)
        self._assert_no_async_wait()
