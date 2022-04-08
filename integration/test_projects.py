# Copyright (c) 2020 Canonical Ltd
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
import pylxd
from integration.testing import IntegrationTestCase
from pylxd import exceptions


class BaseTestProject(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        try:
            pylxd.Client("https://127.0.0.1:8443/", project="test-project")
        except exceptions.ClientConnectionFailed as e:
            message = str(e)
            if message == "Remote server doesn't handle projects":
                self.skipTest(message)
            raise


class TestProjects(BaseTestProject):
    """Tests for `Client.projects.`"""

    def test_get(self):
        """A project is fetched by name."""
        name = self.create_project()
        self.addCleanup(self.delete_project, name)

        project = self.client.projects.get(name)

        self.assertEqual(name, project.name)

    def test_all(self):
        """All projects are fetched."""
        name = self.create_project()
        self.addCleanup(self.delete_project, name)

        projects = self.client.projects.all()

        self.assertIn(name, [project.name for project in projects])

    def test_create(self):
        """A project is created."""
        name = "an-project"
        description = "project description"
        config = {
            "features.images": "true",
            "features.profiles": "false",
        }
        project = self.client.projects.create(name, description, config)
        self.addCleanup(self.delete_project, name)

        self.assertEqual(name, project.name)
        self.assertEqual(description, project.description)
        for key, value in config.items():
            self.assertEqual(project.config[key], value)


class TestProject(BaseTestProject):
    """Tests for `Project`."""

    def setUp(self):
        super().setUp()
        name = self.create_project()
        self.project = self.client.projects.get(name)

    def tearDown(self):
        super().tearDown()
        self.delete_project(self.project.name)

    def test_save(self):
        """A project is updated."""
        new_description = "Updated description"
        self.project.description = new_description
        self.project.save()

        project = self.client.projects.get(self.project.name)
        self.assertEqual(new_description, project.description)

    def test_rename(self):
        """A project is renamed."""
        name = "a-other-project"
        self.addCleanup(self.delete_project, name)

        self.project.rename(name)
        project = self.client.projects.get(name)

        self.assertEqual(name, project.name)

    def test_delete(self):
        """A project is deleted."""
        self.project.delete()

        self.assertRaises(
            exceptions.LXDAPIException, self.client.projects.get, self.project.name
        )
