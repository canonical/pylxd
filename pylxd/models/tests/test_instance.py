import contextlib
import json
import os
import shutil
import tempfile
from unittest import mock
from urllib.parse import quote as url_quote

import requests

from pylxd import exceptions, models
from pylxd.tests import testing


class TestInstance(testing.PyLXDTestCase):
    """Tests for pylxd.models.Instance."""

    def test_all(self):
        """A list of all instances are returned."""
        instances = models.Instance.all(self.client)

        self.assertEqual(1, len(instances))

    def test_get(self):
        """Return a instance."""
        name = "an-instance"

        an_instance = models.Instance.get(self.client, name)

        self.assertEqual(name, an_instance.name)

    def test_get_not_found(self):
        """LXDAPIException is raised when the instance doesn't exist."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances/an-missing-instance$",
            }
        )

        name = "an-missing-instance"

        self.assertRaises(
            exceptions.LXDAPIException, models.Instance.get, self.client, name
        )

    def test_get_error(self):
        """LXDAPIException is raised when the LXD API errors."""

        def not_found(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 500}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances/an-missing-instance$",
            }
        )

        name = "an-missing-instance"

        self.assertRaises(
            exceptions.LXDAPIException, models.Instance.get, self.client, name
        )

    def test_create(self):
        """A new instance is created."""
        config = {"name": "an-new-instance"}

        an_new_instance = models.Instance.create(self.client, config, wait=True)

        self.assertEqual(config["name"], an_new_instance.name)

    def test_create_remote_location(self):
        """A new instance is created at target."""
        config = {"name": "an-new-remote-instance"}

        # the server must be in a cluster for the location to be set
        self.client.host_info["environment"]["server_clustered"] = True

        an_new_remote_instance = models.Instance.create(
            self.client, config, wait=True, target="an-remote"
        )

        self.assertEqual(config["name"], an_new_remote_instance.name)
        self.assertEqual("an-remote", an_new_remote_instance.location)

    def test_create_location_none(self):
        config = {"name": "an-new-remote-instance"}

        instance = models.Instance.create(self.client, config, wait=True)

        self.assertIsNone(instance.location)

    def test_exists(self):
        """A instance exists."""
        name = "an-instance"

        self.assertTrue(models.Instance.exists(self.client, name))

    def test_not_exists(self):
        """A instance exists."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances/an-missing-instance$",
            }
        )

        name = "an-missing-instance"

        self.assertFalse(models.Instance.exists(self.client, name))

    def test_fetch(self):
        """A sync updates the properties of a instance."""
        an_instance = models.Instance(self.client, name="an-instance")

        an_instance.sync()

        self.assertTrue(an_instance.ephemeral)

    def test_fetch_not_found(self):
        """LXDAPIException is raised on a 404 for updating instance."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances/an-missing-instance$",
            }
        )

        an_instance = models.Instance(self.client, name="an-missing-instance")

        self.assertRaises(exceptions.LXDAPIException, an_instance.sync)

    def test_fetch_error(self):
        """LXDAPIException is raised on error."""

        def not_found(request, context):
            context.status_code = 500
            return json.dumps(
                {"type": "error", "error": "An bad error", "error_code": 500}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances/an-missing-instance$",
            }
        )

        an_instance = models.Instance(self.client, name="an-missing-instance")

        self.assertRaises(exceptions.LXDAPIException, an_instance.sync)

    def test_update(self):
        """A instance is updated."""
        an_instance = models.Instance(self.client, name="an-instance")
        an_instance.architecture = 1
        an_instance.config = {}
        an_instance.created_at = 1
        an_instance.devices = {}
        an_instance.ephemeral = 1
        an_instance.expanded_config = {}
        an_instance.expanded_devices = {}
        an_instance.profiles = 1
        an_instance.status = 1

        an_instance.save(wait=True)

        self.assertTrue(an_instance.ephemeral)

    def test_rename(self):
        an_instance = models.Instance(self.client, name="an-instance")

        an_instance.rename("an-renamed-instance", wait=True)

        self.assertEqual("an-renamed-instance", an_instance.name)

    def test_delete(self):
        """A instance is deleted."""
        # XXX: rockstar (21 May 2016) - This just executes
        # a code path. There should be an assertion here, but
        # it's not clear how to assert that, just yet.
        an_instance = models.Instance(self.client, name="an-instance")

        an_instance.delete(wait=True)

    @mock.patch("pylxd.models.instance._StdinWebsocket")
    @mock.patch("pylxd.models.instance._CommandWebsocketClient")
    def test_execute(self, _CommandWebsocketClient, _StdinWebsocket):
        """A command is executed on a instance."""
        fake_websocket = mock.Mock()
        fake_websocket.data = "test\n"
        _StdinWebsocket.return_value = fake_websocket
        _CommandWebsocketClient.return_value = fake_websocket

        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.execute(["echo", "test"])

        self.assertEqual(0, result.exit_code)
        self.assertEqual("test\n", result.stdout)

    @mock.patch("pylxd.models.instance._StdinWebsocket")
    @mock.patch("pylxd.models.instance._CommandWebsocketClient")
    def test_execute_with_env(self, _CommandWebsocketClient, _StdinWebsocket):
        """A command is executed on a instance with custom env variables."""
        fake_websocket = mock.Mock()
        fake_websocket.data = "test\n"
        _StdinWebsocket.return_value = fake_websocket
        _CommandWebsocketClient.return_value = fake_websocket

        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.execute(["echo", "test"], environment={"DISPLAY": ":1"})

        self.assertEqual(0, result.exit_code)
        self.assertEqual("test\n", result.stdout)

    def test_execute_string(self):
        """A command passed as string raises a TypeError."""
        an_instance = models.Instance(self.client, name="an-instance")

        self.assertRaises(TypeError, an_instance.execute, "apt-get update")

    def test_raw_interactive_execute(self):
        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.raw_interactive_execute(["/bin/bash"])

        self.assertEqual(
            result["ws"], "/1.0/operations/operation-abc/websocket?secret=abc"
        )
        self.assertEqual(
            result["control"], "/1.0/operations/operation-abc/websocket?secret=jkl"
        )

    def test_raw_interactive_execute_env(self):
        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.raw_interactive_execute(["/bin/bash"], {"PATH": "/"})

        self.assertEqual(
            result["ws"], "/1.0/operations/operation-abc/websocket?secret=abc"
        )
        self.assertEqual(
            result["control"], "/1.0/operations/operation-abc/websocket?secret=jkl"
        )

    def test_raw_interactive_execute_string(self):
        """A command passed as string raises a TypeError."""
        an_instance = models.Instance(self.client, name="an-instance")

        self.assertRaises(
            TypeError, an_instance.raw_interactive_execute, "apt-get update"
        )

    def test_raw_interactive_execute_options(self):
        """It's possible to pass user, group and cwd arguments to an execute command."""
        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.raw_interactive_execute(
            ["/bin/bash"], user="user", group="group", cwd="/some/path"
        )
        self.assertEqual(
            result["ws"], "/1.0/operations/operation-abc/websocket?secret=abc"
        )
        self.assertEqual(
            result["control"], "/1.0/operations/operation-abc/websocket?secret=jkl"
        )

    def test_migrate(self):
        """A instance is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint="http://pylxd2.test")
        an_instance = models.Instance(self.client, name="an-instance")

        an_migrated_instance = an_instance.migrate(client2)

        self.assertEqual("an-instance", an_migrated_instance.name)
        self.assertEqual(client2, an_migrated_instance.client)

    @mock.patch("pylxd.models.instance.Instance.generate_migration_data")
    def test_migrate_exception_error(self, generate_migration_data):
        """LXDAPIException is raised in case of migration failure"""
        from pylxd.client import Client
        from pylxd.exceptions import LXDAPIException

        def generate_exception(*args, **kwargs):
            response = mock.Mock()
            response.status_code = 400
            raise LXDAPIException(response)

        generate_migration_data.side_effect = generate_exception

        an_instance = models.Instance(self.client, name="an-instance")

        client2 = Client(endpoint="http://pylxd2.test")
        self.assertRaises(LXDAPIException, an_instance.migrate, client2)

    @mock.patch("pylxd.models.instance.Instance.generate_migration_data")
    def test_migrate_exception_running(self, generate_migration_data):
        """Migrated instance already running on destination"""
        from pylxd.client import Client
        from pylxd.exceptions import LXDAPIException

        client2 = Client(endpoint="http://pylxd2.test")
        an_instance = models.Instance(self.client, name="an-instance")
        an_instance.status_code = 103

        def generate_exception(*args, **kwargs):
            response = mock.Mock()
            response.status_code = 103
            raise LXDAPIException(response)

        generate_migration_data.side_effect = generate_exception

        an_migrated_instance = an_instance.migrate(client2, live=True)

        self.assertEqual("an-instance", an_migrated_instance.name)
        self.assertEqual(client2, an_migrated_instance.client)
        generate_migration_data.assert_called_once_with(True)

    def test_migrate_started(self):
        """A instance is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint="http://pylxd2.test")
        an_instance = models.Instance.get(self.client, name="an-instance")
        an_instance.status_code = 103

        an_migrated_instance = an_instance.migrate(client2)

        self.assertEqual("an-instance", an_migrated_instance.name)
        self.assertEqual(client2, an_migrated_instance.client)

    def test_migrate_stopped(self):
        """A instance is migrated."""
        from pylxd.client import Client

        client2 = Client(endpoint="http://pylxd2.test")
        an_instance = models.Instance.get(self.client, name="an-instance")
        an_instance.status_code = 102

        an_migrated_instance = an_instance.migrate(client2)

        self.assertEqual("an-instance", an_migrated_instance.name)
        self.assertEqual(client2, an_migrated_instance.client)

    @mock.patch("pylxd.client._APINode.get")
    def test_migrate_local_client(self, get):
        """Migration from local clients is not supported."""
        # Mock out the _APINode for the local instance.
        response = mock.Mock()
        response.json.return_value = {"metadata": {"fake": "response"}}
        response.status_code = 200
        get.return_value = response

        from pylxd.client import Client

        client2 = Client(endpoint="http+unix://pylxd2.test")
        an_instance = models.Instance(client2, name="an-instance")

        self.assertRaises(ValueError, an_instance.migrate, self.client)

    def test_publish(self):
        """Instances can be published."""
        self.add_rule(
            {
                "text": json.dumps(
                    {
                        "type": "sync",
                        "metadata": {
                            "id": "operation-abc",
                            "metadata": {
                                "fingerprint": (
                                    "e3b0c44298fc1c149afbf4c8996fb92427"
                                    "ae41e4649b934ca495991b7852b855"
                                )
                            },
                        },
                    }
                ),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/operations/operation-abc$",
            }
        )

        an_instance = models.Instance(self.client, name="an-instance")
        # Hack to get around mocked data
        an_instance.type = "container"

        image = an_instance.publish(wait=True)

        self.assertEqual(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            image.fingerprint,
        )

    def test_restore_snapshot(self):
        """Snapshots can be restored"""
        an_instance = models.Instance(self.client, name="an-instance")
        an_instance.restore_snapshot("thing")


class TestInstanceState(testing.PyLXDTestCase):
    """Tests for pylxd.models.InstanceState."""

    def test_get(self):
        """Return a instance."""
        name = "an-instance"

        an_instance = models.Instance.get(self.client, name)
        state = an_instance.state()

        self.assertEqual("Running", state.status)
        self.assertEqual(103, state.status_code)

    def test_start(self):
        """A instance is started."""
        an_instance = models.Instance.get(self.client, "an-instance")

        an_instance.start(wait=True)

    def test_stop(self):
        """A instance is stopped."""
        an_instance = models.Instance.get(self.client, "an-instance")

        an_instance.stop()

    def test_restart(self):
        """A instance is restarted."""
        an_instance = models.Instance.get(self.client, "an-instance")

        an_instance.restart()

    def test_freeze(self):
        """A instance is suspended."""
        an_instance = models.Instance.get(self.client, "an-instance")

        an_instance.freeze()

    def test_unfreeze(self):
        """A instance is resumed."""
        an_instance = models.Instance.get(self.client, "an-instance")

        an_instance.unfreeze()


class TestInstanceSnapshots(testing.PyLXDTestCase):
    """Tests for pylxd.models.Instance.snapshots."""

    def setUp(self):
        super().setUp()
        self.instance = models.Instance.get(self.client, "an-instance")

    def test_get(self):
        """Return a specific snapshot."""
        snapshot = self.instance.snapshots.get("an-snapshot")

        self.assertEqual("an-snapshot", snapshot.name)

    def test_all(self):
        """Return all snapshots."""
        snapshots = self.instance.snapshots.all()

        self.assertEqual(1, len(snapshots))
        self.assertEqual("an-snapshot", snapshots[0].name)
        self.assertEqual(self.client, snapshots[0].client)
        self.assertEqual(self.instance, snapshots[0].instance)

    def test_create(self):
        """Create a snapshot."""
        snapshot = self.instance.snapshots.create(
            "an-snapshot", stateful=True, wait=True
        )

        self.assertEqual("an-snapshot", snapshot.name)


class TestSnapshot(testing.PyLXDTestCase):
    """Tests for pylxd.models.Snapshot."""

    def setUp(self):
        super().setUp()
        self.instance = models.Instance.get(self.client, "an-instance")

    def test_rename(self):
        """A snapshot is renamed."""
        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )

        snapshot.rename("an-renamed-snapshot", wait=True)

        self.assertEqual("an-renamed-snapshot", snapshot.name)

    def test_delete(self):
        """A snapshot is deleted."""
        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )

        snapshot.delete(wait=True)

        # TODO: add an assertion here

    def test_delete_failure(self):
        """If the response indicates delete failure, raise an exception."""

        def not_found(request, context):
            context.status_code = 404
            return json.dumps(
                {"type": "error", "error": "Not found", "error_code": 404}
            )

        self.add_rule(
            {
                "text": not_found,
                "method": "DELETE",
                "url": (
                    r"^http://pylxd.test/1.0/instances/"
                    "an-instance/snapshots/an-snapshot$"
                ),
            }
        )

        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )

        self.assertRaises(exceptions.LXDAPIException, snapshot.delete)

    def test_publish(self):
        """Snapshots can be published."""
        self.add_rule(
            {
                "text": json.dumps(
                    {
                        "type": "sync",
                        "metadata": {
                            "id": "operation-abc",
                            "metadata": {
                                "fingerprint": (
                                    "e3b0c44298fc1c149afbf4c8996fb92427"
                                    "ae41e4649b934ca495991b7852b855"
                                )
                            },
                        },
                    }
                ),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/operations/operation-abc$",
            }
        )

        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )

        image = snapshot.publish(wait=True)

        self.assertEqual(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            image.fingerprint,
        )

    def test_restore_snapshot(self):
        """Snapshots can be restored from the snapshot object"""
        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )
        snapshot.restore(wait=True)


class TestFiles(testing.PyLXDTestCase):
    """Tests for pylxd.models.Instance.files."""

    def setUp(self):
        super().setUp()
        self.instance = models.Instance.get(self.client, "an-instance")

    def test_put_delete(self):
        """A file is put on the instance and then deleted"""
        # we are mocked, so delete should initially not be available
        self.assertEqual(False, self.instance.files.delete_available())
        self.assertRaises(
            exceptions.LXDAPIExtensionNotAvailable,
            self.instance.files.delete,
            "/some/file",
        )
        # Now insert delete
        self.add_rule(
            {
                "text": json.dumps(
                    {
                        "type": "sync",
                        "metadata": {
                            "auth": "trusted",
                            "environment": {
                                "certificate": "an-pem-cert",
                            },
                            "api_extensions": ["file_delete"],
                        },
                    }
                ),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0$",
            }
        )

        # Update hostinfo
        self.client.host_info = self.client.api.get().json()["metadata"]

        self.assertEqual(True, self.instance.files.delete_available())

        # mock out the delete rule:
        self.add_rule(
            {
                "method": "DELETE",
                "url": (
                    r"^http://pylxd.test/1.0/instances/an-instance/files"
                    r"\?path=%2Fsome%2Ffile$"
                ),
            }
        )
        self.instance.files.delete("/some/file")

        # now check that an error (non 200) causes an exception
        def responder(request, context):
            context.status_code = 404

        self.add_rule(
            {
                "text": responder,
                "method": "DELETE",
                "url": (
                    r"^http://pylxd.test/1.0/instances/an-instance/files"
                    r"\?path=%2Fsome%2Ffile%2Fnot%2Ffound$"
                ),
            }
        )
        with self.assertRaises(exceptions.LXDAPIException):
            self.instance.files.delete("/some/file/not/found")

    def test_put_mode_uid_gid(self):
        """Should be able to set the mode, uid and gid of a file"""
        # fix up the default POST rule to allow us to see the posted vars
        _capture = {}

        def capture(request, context):
            _capture["headers"] = getattr(request._request, "headers")
            context.status_code = 200

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": (
                    r"^http://pylxd.test/1.0/instances/an-instance/files"
                    r"\?path=%2Ftmp%2Fputted$"
                ),
            }
        )

        data = "The quick brown fox"
        # start with an octal mode
        self.instance.files.put("/tmp/putted", data, mode=0o123, uid=1, gid=2)
        headers = _capture["headers"]
        self.assertEqual(headers["X-LXD-mode"], "0123")
        self.assertEqual(headers["X-LXD-uid"], "1")
        self.assertEqual(headers["X-LXD-gid"], "2")
        # use a str mode this type
        self.instance.files.put("/tmp/putted", data, mode="456")
        headers = _capture["headers"]
        self.assertEqual(headers["X-LXD-mode"], "0456")
        # check that mode='0644' also works (i.e. already has 0 prefix)
        self.instance.files.put("/tmp/putted", data, mode="0644")
        headers = _capture["headers"]
        self.assertEqual(headers["X-LXD-mode"], "0644")
        # check that assertion is raised
        with self.assertRaises(ValueError):
            self.instance.files.put("/tmp/putted", data, mode=object)

    def test_mk_dir(self):
        """Tests pushing an empty directory"""
        _capture = {}

        def capture(request, context):
            _capture["headers"] = getattr(request._request, "headers")
            context.status_code = 200

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": (
                    r"^http://pylxd.test/1.0/instances/an-instance/files"
                    r"\?path=%2Ftmp%2Fputted$"
                ),
            }
        )

        self.instance.files.mk_dir("/tmp/putted", mode=0o123, uid=1, gid=2)
        headers = _capture["headers"]
        self.assertEqual(headers["X-LXD-type"], "directory")
        self.assertEqual(headers["X-LXD-mode"], "0123")
        self.assertEqual(headers["X-LXD-uid"], "1")
        self.assertEqual(headers["X-LXD-gid"], "2")
        # check that assertion is raised
        with self.assertRaises(ValueError):
            self.instance.files.mk_dir("/tmp/putted", mode=object)

        response = mock.Mock()
        response.status_code = 404

        with mock.patch("pylxd.client._APINode.post", response):
            with self.assertRaises(exceptions.LXDAPIException):
                self.instance.files.mk_dir("/tmp/putted")

    def test_recursive_put(self):
        @contextlib.contextmanager
        def tempdir(prefix="tmp"):
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
            with open(path, "w") as f:
                f.write(content)

        _captures = []

        def capture(request, context):
            _captures.append(
                {
                    "headers": getattr(request._request, "headers"),
                    "body": request._request.body,
                }
            )
            context.status_code = 200

        with tempdir() as _dir:
            base = r"^http://pylxd.test/1.0/instances/" r"an-instance/files\?path="
            rules = [
                {
                    "text": capture,
                    "method": "POST",
                    "url": base + url_quote("target", safe="") + "$",
                },
                {
                    "text": capture,
                    "method": "POST",
                    "url": base + url_quote("target/dir", safe="") + "$",
                },
                {
                    "text": capture,
                    "method": "POST",
                    "url": base + url_quote("target/file1", safe="") + "$",
                },
                {
                    "text": capture,
                    "method": "POST",
                    "url": base + url_quote("target/dir/file2", safe="") + "$",
                },
            ]
            self.add_rules(rules)

            create_file(_dir, "file1", "This is file1")
            create_file(_dir, "dir/file2", "This is file2")

            self.instance.files.recursive_put(_dir, "./target/")

            self.assertEqual(_captures[0]["headers"]["X-LXD-type"], "directory")
            self.assertEqual(_captures[1]["body"], b"This is file1")
            self.assertEqual(_captures[2]["headers"]["X-LXD-type"], "directory")
            self.assertEqual(_captures[3]["body"], b"This is file2")

    def test_get(self):
        """A file is retrieved from the instance."""
        data = self.instance.files.get("/tmp/getted")

        self.assertEqual(b"This is a getted file", data)

    def test_recursive_get(self):
        """A folder is retrieved recursively from the instance"""
        response = requests.models.Response()
        response.status_code = 200
        response.headers["X-LXD-type"] = "directory"
        response._content = json.dumps({"metadata": ["file1", "file2"]})

        response1 = requests.models.Response()
        response1.status_code = 200
        response1.headers["X-LXD-type"] = "file"
        response1._content = "This is file1"

        response2 = requests.models.Response()
        response2.status_code = 200
        response2.headers["X-LXD-type"] = "file"
        response2._content = "This is file2"

        return_values = [response, response1, response2]

        with mock.patch("pylxd.client._APINode.get") as get_mocked:
            get_mocked.side_effect = return_values
            with mock.patch("os.mkdir") as mkdir_mocked:
                mock_open = mock.mock_open()
                with mock.patch("pylxd.models.instance.open", mock_open):
                    self.instance.files.recursive_get("/tmp/getted", "/tmp")
                    assert mkdir_mocked.call_count == 1
                    assert mock_open.call_count == 2

    def test_get_not_found(self):
        """LXDAPIException is raised on bogus filenames."""

        def not_found(request, context):
            context.status_code = 500

        rule = {
            "text": not_found,
            "method": "GET",
            "url": (
                r"^http://pylxd.test/1.0/instances/an-instance/files"
                r"\?path=%2Ftmp%2Fgetted$"
            ),
        }
        self.add_rule(rule)

        self.assertRaises(
            exceptions.LXDAPIException, self.instance.files.get, "/tmp/getted"
        )

    def test_get_error(self):
        """LXDAPIException is raised on error."""

        def not_found(request, context):
            context.status_code = 503

        rule = {
            "text": not_found,
            "method": "GET",
            "url": (
                r"^http://pylxd.test/1.0/instances/an-instance/files"
                r"\?path=%2Ftmp%2Fgetted$"
            ),
        }
        self.add_rule(rule)

        self.assertRaises(
            exceptions.LXDAPIException, self.instance.files.get, "/tmp/getted"
        )

    # for bug/281 -- getting an empty json file is interpreted as an API
    # get rather than a raw get.
    def test_get_json_file(self):
        data = self.instance.files.get("/tmp/json-get")
        self.assertEqual(b'{"some": "value"}', data)
