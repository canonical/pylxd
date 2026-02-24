import json
from unittest import mock

from pylxd import exceptions, models
from pylxd.tests import testing


class TestProject(testing.PyLXDTestCase):
    """Tests for pylxd.models.Project."""

    def test_get(self):
        """A project is fetched."""
        name = "test-project"
        a_project = models.Project.get(self.client, name)

        self.assertEqual(name, a_project.name)

    def test_get_not_found(self):
        """LXDAPIException is raised on unknown project."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/projects/test-project$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Project.get, self.client, "test-project"
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
                "url": r"^http://pylxd.test/1.0/projects/test-project$",
            }
        )

        self.assertRaises(
            exceptions.LXDAPIException, models.Project.get, self.client, "test-project"
        )

    def test_exists(self):
        name = "test-project"

        self.assertTrue(models.Project.exists(self.client, name))

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
                "url": r"^http://pylxd.test/1.0/projects/test-project$",
            }
        )

        name = "test-project"

        self.assertFalse(models.Project.exists(self.client, name))

    def test_all(self):
        """A list of all projects is returned."""
        projects = models.Project.all(self.client)

        self.assertEqual(1, len(projects))

    def test_create(self):
        """A new project is created."""

        name = "new-project"
        description = "new project is new"
        config = {
            "features.images": "true",
        }
        a_project = models.Project.create(
            self.client, name="new-project", config=config, description=description
        )

        self.assertIsInstance(a_project, models.Project)
        self.assertEqual(name, a_project.name)
        self.assertEqual(config, a_project.config)
        self.assertEqual(description, a_project.description)

    def test_update(self):
        """A project is updated."""
        a_project = models.Project.get(self.client, "test-project")

        a_project.save()

        self.assertEqual({"features.images": "true"}, a_project.config)

    def test_fetch(self):
        """A partially fetched project is made complete."""
        a_project = self.client.projects.all()[0]

        a_project.sync()

        self.assertEqual("new project is new", a_project.description)

    def test_fetch_notfound(self):
        """LXDAPIException is raised on bogus project fetches."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/projects/test-project$",
            }
        )

        a_project = models.Project(self.client, name="test-project")

        self.assertRaises(exceptions.LXDAPIException, a_project.sync)

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
                "url": r"^http://pylxd.test/1.0/projects/test-project$",
            }
        )

        a_project = models.Project(self.client, name="test-project")

        self.assertRaises(exceptions.LXDAPIException, a_project.sync)

    def test_delete(self):
        """A project is deleted."""
        a_project = self.client.projects.all()[0]

        a_project.delete()


class TestProjectAsync(testing.PyLXDTestCase):
    """Tests for async operations in Project."""

    def setUp(self):
        super().setUp()
        self.mock_wait = mock.patch.object(
            self.client.operations, "wait_for_operation"
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _mock_async_delete(self, name="test-project"):
        self.add_rule(
            {
                "json": {
                    "type": "async",
                    "status_code": 202,
                    "operation": "/1.0/operations/test-op",
                },
                "status_code": 202,
                "method": "DELETE",
                "url": rf"^http://pylxd.test/1.0/projects/{name}$",
            }
        )

    def test_delete_async_with_wait(self):
        """Async project delete with wait=True waits for the operation."""
        a_project = models.Project(self.client, name="test-project")
        self._mock_async_delete()

        a_project.delete(wait=True)

        self.mock_wait.assert_called_once_with("/1.0/operations/test-op")

    def test_delete_async_without_wait(self):
        """Async project delete with wait=False does not wait."""
        a_project = models.Project(self.client, name="test-project")
        self._mock_async_delete()

        a_project.delete(wait=False)

        self.mock_wait.assert_not_called()
