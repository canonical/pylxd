# Copyright (c) 2016 Canonical Ltd
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
import unittest

from integration.testing import IntegrationTestCase
from pylxd import exceptions


class TestContainers(IntegrationTestCase):
    """Tests for `Client.containers`."""

    def test_get(self):
        """A container is fetched by name."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        container = self.client.containers.get(name)

        self.assertEqual(name, container.name)

    def test_all(self):
        """A list of all containers is returned."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        containers = self.client.containers.all()

        self.assertIn(name, [c.name for c in containers])

    def test_create(self):
        """Creates and returns a new container."""
        _, alias = self.create_image()
        config = {
            "name": "an-container",
            "architecture": "2",
            "profiles": ["default"],
            "ephemeral": True,
            "config": {"limits.cpu": "2"},
            "source": {"type": "image", "alias": alias},
        }
        self.addCleanup(self.delete_container, config["name"])

        container = self.client.containers.create(config, wait=True)

        self.assertEqual(config["name"], container.name)


class TestContainer(IntegrationTestCase):
    """Tests for Client.Container."""

    def setUp(self):
        super(TestContainer, self).setUp()
        name = self.create_container()
        self.container = self.client.containers.get(name)

    def tearDown(self):
        super(TestContainer, self).tearDown()
        self.delete_container(self.container.name)

    def test_save(self):
        """The container is updated to a new config."""
        self.container.config["limits.cpu"] = "1"
        self.container.save(wait=True)

        self.assertEqual("1", self.container.config["limits.cpu"])
        container = self.client.containers.get(self.container.name)
        self.assertEqual("1", container.config["limits.cpu"])

    def test_rename(self):
        """The container is renamed."""
        name = "an-renamed-container"
        self.container.rename(name, wait=True)

        self.assertEqual(name, self.container.name)
        container = self.client.containers.get(name)
        self.assertEqual(name, container.name)

    def test_delete(self):
        """The container is deleted."""
        self.container.delete(wait=True)

        self.assertRaises(
            exceptions.LXDAPIException, self.client.containers.get, self.container.name
        )

    def test_start_stop(self):
        """The container is started and then stopped."""
        # NOTE: rockstar (15 Feb 2016) - I don't care for the
        # multiple assertions here, but it's a okay-ish way
        # to test what we need.
        self.container.start(wait=True)

        self.assertEqual("Running", self.container.status)
        container = self.client.containers.get(self.container.name)
        self.assertEqual("Running", container.status)

        self.container.stop(wait=True)

        self.assertEqual("Stopped", self.container.status)
        container = self.client.containers.get(self.container.name)
        self.assertEqual("Stopped", container.status)

    def test_snapshot(self):
        """A container snapshot is made, renamed, and deleted."""
        # NOTE: rockstar (15 Feb 2016) - Once again, multiple things
        # asserted in the same test.
        name = "an-snapshot"
        snapshot = self.container.snapshots.create(name, wait=True)

        self.assertEqual([name], [s.name for s in self.container.snapshots.all()])

        new_name = "an-other-snapshot"
        snapshot.rename(new_name, wait=True)

        self.assertEqual([new_name], [s.name for s in self.container.snapshots.all()])

        snapshot.delete(wait=True)

        self.assertEqual([], self.container.snapshots.all())

    def test_put_get_file(self):
        """A file is written to the container and then read."""
        filepath = "/tmp/an_file"
        data = b"abcdef"

        # raises an exception if this fails.
        self.container.files.put(filepath, data)

        contents = self.container.files.get(filepath)

        self.assertEqual(data, contents)

    def test_execute(self):
        """A command is executed on the container."""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)

        result = self.container.execute(["echo", "test"])

        self.assertEqual(0, result.exit_code)
        self.assertEqual("test\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_execute_no_buffer(self):
        """A command is executed on the container without buffering the output."""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)
        buffer = []

        result = self.container.execute(["echo", "test"], stdout_handler=buffer.append)

        self.assertEqual(0, result.exit_code)
        self.assertEqual("", result.stdout)
        self.assertEqual("", result.stderr)
        self.assertEqual("test\n", "".join(buffer))

    def test_execute_no_decode(self):
        """A command is executed on the container that isn't utf-8 decodable"""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)

        result = self.container.execute(["printf", "\\xff"], decode=None)

        self.assertEqual(0, result.exit_code)
        self.assertEqual(b"\xff", result.stdout)
        self.assertEqual(b"", result.stderr)

    def test_execute_force_decode(self):
        """A command is executed and force output to ascii"""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)

        result = self.container.execute(
            ["printf", "qu\\xe9"], decode=True, encoding="latin1"
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual("qué", result.stdout)
        self.assertEqual("", result.stderr)

    def test_execute_pipes(self):
        """A command receives data from stdin and write to stdout handler"""
        self.container.start(wait=True)
        self.addCleanup(self.container.stop, wait=True)
        test_msg = "Hello world!\n"
        stdout_msgs = []

        def stdout_handler(msg):
            stdout_msgs.append(msg)

        result = self.container.execute(
            ["cat", "-"], stdin_payload=test_msg, stdout_handler=stdout_handler
        )

        self.assertEqual(0, result.exit_code)
        # if a handler is supplied then there is no stdout in result
        self.assertEqual("", result.stdout)
        self.assertEqual("", result.stderr)
        self.assertEqual(stdout_msgs, [test_msg])

    def test_publish(self):
        """A container is published."""
        # Hack to get around mocked data
        self.container.type = "container"
        image = self.container.publish(wait=True)

        self.assertIn(
            image.fingerprint, [i.fingerprint for i in self.client.images.all()]
        )

    # COMMENT gabrik - 29/08/2018:
    # This test is commented because CRIU does NOT work
    # in LXD inside LXD

    @unittest.skip("This test is broken as it assumes particular network")
    def test_migrate_running(self):
        """A running container is migrated."""
        from pylxd.client import Client

        first_host = "https://10.0.3.111:8443/"
        second_host = "https://10.0.3.222:8443/"

        client1 = Client(endpoint=first_host, verify=False)
        client1.authenticate("password")

        client2 = Client(endpoint=second_host, verify=False)
        client2.authenticate("password")
        an_container = client1.containers.get(self.container.name)
        an_container.start(wait=True)
        an_container.sync()
        an_migrated_container = an_container.migrate(client2, wait=True)

        self.assertEqual(an_container.name, an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)

    @unittest.skip("This test is broken as it assumes particular network")
    def test_migrate_local_client(self):
        """Raise ValueError, cannot migrate from local connection"""
        from pylxd.client import Client

        second_host = "https://10.0.3.222:8443/"
        client2 = Client(endpoint=second_host, verify=False)
        client2.authenticate("password")

        self.assertRaises(ValueError, self.container.migrate, client2)

    @unittest.skip("This test is broken as it assumes particular network")
    def test_migrate_stopped(self):
        """A stopped container is migrated."""
        from pylxd.client import Client

        first_host = "https://10.0.3.111:8443/"
        second_host = "https://10.0.3.222:8443/"

        client1 = Client(endpoint=first_host, verify=False)
        client1.authenticate("password")

        client2 = Client(endpoint=second_host, verify=False)
        client2.authenticate("password")
        an_container = client1.containers.get(self.container.name)
        an_migrated_container = an_container.migrate(client2, wait=True)

        self.assertEqual(an_container.name, an_migrated_container.name)
        self.assertEqual(client2, an_migrated_container.client)
