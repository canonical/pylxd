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

    def test_all_with_fields_uses_selective_recursion(self):
        """When the extension is present and fields is given, the selective
        recursion URL (recursion=2;fields=...) is used."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": [
                        {
                            "name": "an-instance",
                            "status": "Running",
                            "status_code": 103,
                            "state": {"disk": {}},
                        }
                    ],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances\?recursion=2%3Bfields%3Dstate\.disk$",
            }
        )

        instances = models.Instance.all(self.client, recursion=2, fields=["state.disk"])

        self.assertEqual(1, len(instances))
        self.assertEqual("an-instance", instances[0].name)

    def test_all_with_fields_multiple_uses_selective_recursion(self):
        """Multiple fields are comma-joined in the selective recursion URL."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": [
                        {
                            "name": "an-instance",
                            "status": "Running",
                            "status_code": 103,
                            "state": {"disk": {}, "network": {}},
                        }
                    ],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances\?recursion=2%3Bfields%3Dstate\.disk%2Cstate\.network$",
            }
        )

        instances = models.Instance.all(
            self.client, recursion=2, fields=["state.disk", "state.network"]
        )

        self.assertEqual(1, len(instances))
        self.assertEqual("an-instance", instances[0].name)

    def test_all_with_fields_empty_suppresses_state(self):
        """An empty fields list produces recursion=2;fields= (no state sub-fields)."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": [
                        {
                            "name": "an-instance",
                            "status": "Running",
                            "status_code": 103,
                        }
                    ],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances\?recursion=2%3Bfields%3D$",
            }
        )

        instances = models.Instance.all(self.client, recursion=2, fields=[])

        self.assertEqual(1, len(instances))
        self.assertEqual("an-instance", instances[0].name)

    def test_all_with_fields_falls_back_without_extension(self):
        """When the extension is absent, fields is ignored and plain recursion=2 is used."""
        # Extension is NOT added → has_api_extension returns False
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": [
                        {
                            "name": "an-instance",
                            "status": "Running",
                            "status_code": 103,
                        }
                    ],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances\?recursion=2$",
            }
        )

        instances = models.Instance.all(self.client, recursion=2, fields=["state.disk"])

        self.assertEqual(1, len(instances))
        self.assertEqual("an-instance", instances[0].name)

    def test_all_with_fields_ignored_for_recursion_1(self):
        """fields is silently ignored when recursion is not 2."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": [
                        {
                            "name": "an-instance",
                            "status": "Running",
                            "status_code": 103,
                        }
                    ],
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/instances\?recursion=1$",
            }
        )

        instances = models.Instance.all(self.client, recursion=1, fields=["state.disk"])

        self.assertEqual(1, len(instances))
        self.assertEqual("an-instance", instances[0].name)

    def test_all_with_fields_str_raises_type_error(self):
        """Passing a bare string for fields raises TypeError (string is iterable of chars)."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])

        with self.assertRaises(TypeError):
            models.Instance.all(self.client, recursion=2, fields="state.disk")

    def test_all_with_fields_bytes_raises_type_error(self):
        """Passing bytes for fields raises TypeError."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])

        with self.assertRaises(TypeError):
            models.Instance.all(self.client, recursion=2, fields=b"state.disk")

    def test_all_with_fields_non_string_element_raises_type_error(self):
        """Passing an iterable containing a non-string element raises TypeError."""
        testing.add_api_extension_helper(self, ["instances_state_selective_recursion"])

        with self.assertRaises(TypeError):
            models.Instance.all(self.client, recursion=2, fields=["state.disk", 42])

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
                "url": r"^http://pylxd.test/1.0/instances/a-missing-instance$",
            }
        )

        name = "a-missing-instance"

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
                "url": r"^http://pylxd.test/1.0/instances/a-missing-instance$",
            }
        )

        name = "a-missing-instance"

        self.assertRaises(
            exceptions.LXDAPIException, models.Instance.get, self.client, name
        )

    def test_create(self):
        """A new instance is created."""
        # parametrization (native parametrize doesn't work with unittest.TestCase, so we do it manually)
        for name in ("an-new-instance", None):
            for wait in (True, False):
                with self.subTest(name=name, wait=wait):
                    config = {"name": name} if name else {}

                    an_new_instance = models.Instance.create(
                        self.client, config, wait=wait
                    )

                    if name:
                        self.assertEqual(config["name"], an_new_instance.name)
                    else:
                        # Creating an instance without a name should still work (a random name is assigned).
                        self.assertEqual("an-instance-generated", an_new_instance.name)

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

    def test_create_does_not_inject_type(self):
        """Instance.create() with _instance_type=None does not add 'type' to the payload."""
        posted_json = {}

        def capture(request, context):
            posted_json.update(json.loads(request.body))
            context.status_code = 202
            return json.dumps(
                {
                    "type": "async",
                    "operation": "/1.0/operations/operation-abc?project=default",
                }
            )

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/instances$",
            }
        )
        models.Instance.create(self.client, {"name": "an-new-instance"})
        self.assertNotIn("type", posted_json)

    def test_create_container_injects_type(self):
        """Container.create() injects type='container' into the POST payload."""
        posted_json = {}

        def capture(request, context):
            posted_json.update(json.loads(request.body))
            context.status_code = 202
            return json.dumps(
                {
                    "type": "async",
                    "operation": "/1.0/operations/operation-abc?project=default",
                }
            )

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/instances$",
            }
        )
        models.Container.create(self.client, {"name": "an-new-instance"})
        self.assertEqual("container", posted_json["type"])

    def test_create_virtual_machine_injects_type(self):
        """VirtualMachine.create() injects type='virtual-machine' into the POST payload."""
        posted_json = {}

        def capture(request, context):
            posted_json.update(json.loads(request.body))
            context.status_code = 202
            return json.dumps(
                {
                    "type": "async",
                    "operation": "/1.0/operations/operation-abc?project=default",
                }
            )

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/instances$",
            }
        )
        models.VirtualMachine.create(self.client, {"name": "an-new-instance"})
        self.assertEqual("virtual-machine", posted_json["type"])

    def test_create_preserves_caller_type(self):
        """Container.create() does not overwrite a 'type' already in the caller's config."""
        posted_json = {}
        original_config = {"name": "an-new-instance", "type": "virtual-machine"}

        def capture(request, context):
            posted_json.update(json.loads(request.body))
            context.status_code = 202
            return json.dumps(
                {
                    "type": "async",
                    "operation": "/1.0/operations/operation-abc?project=default",
                }
            )

        self.add_rule(
            {
                "text": capture,
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/instances$",
            }
        )
        models.Container.create(self.client, original_config)
        self.assertEqual("virtual-machine", posted_json["type"])

    def test_create_does_not_mutate_caller_config(self):
        """Container.create() does not mutate the caller's config dict."""
        config = {"name": "an-new-instance"}
        models.Container.create(self.client, config)
        self.assertNotIn("type", config)

    def test_exists(self):
        """A instance exists."""
        name = "an-instance"

        # The mock response contains an unknown attribute; ensure the
        # module-level seen-warning set is reset so the warning is emitted
        # and can be asserted without depending on test ordering.
        with mock.patch("pylxd.models._model._seen_attribute_warnings", new=set()):
            with self.assertWarns(UserWarning):
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
                "url": r"^http://pylxd.test/1.0/instances/a-missing-instance$",
            }
        )

        name = "a-missing-instance"

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
                "url": r"^http://pylxd.test/1.0/instances/a-missing-instance$",
            }
        )

        an_instance = models.Instance(self.client, name="a-missing-instance")

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
                "url": r"^http://pylxd.test/1.0/instances/a-missing-instance$",
            }
        )

        an_instance = models.Instance(self.client, name="a-missing-instance")

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

    def test_save_twice_sends_current_volatile_keys(self):
        """A second save sends the volatile keys LXD set on the first (#569)."""
        url = "http://pylxd.test/1.0/instances/an-instance"
        metadata = self.client.api.instances["an-instance"].get().json()["metadata"]

        def serve(config):
            self.add_rule(
                {
                    "json": {
                        "type": "sync",
                        "metadata": {**metadata, "config": config},
                    },
                    "method": "GET",
                    "url": rf"^{url}$",
                }
            )

        serve({"volatile.idmap.next": "old"})
        an_instance = models.Instance.get(self.client, "an-instance")
        an_instance.config["raw.idmap"] = "uid 1000 1000"
        # LXD recomputes volatile.idmap.next when raw.idmap changes.
        serve({"raw.idmap": "uid 1000 1000", "volatile.idmap.next": "new"})

        an_instance.save(wait=True)
        an_instance.save(wait=True)

        put = self.last_matching_request("PUT", url)
        self.assertEqual(
            {"raw.idmap": "uid 1000 1000", "volatile.idmap.next": "new"},
            put.json()["config"],
        )

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
    def test_execute_uses_client_ssl_options(
        self, _CommandWebsocketClient, _StdinWebsocket
    ):
        """Websockets are created using the client's ssl_options."""
        fake_websocket = mock.Mock()
        fake_websocket.data = "test\n"
        self.client.ssl_options = {"certfile": "/foo", "keyfile": "/bar"}
        _StdinWebsocket.return_value = fake_websocket
        _CommandWebsocketClient.return_value = fake_websocket

        an_instance = models.Instance(self.client, name="an-instance")

        result = an_instance.execute(["echo", "test"])

        self.assertEqual(
            _StdinWebsocket.call_args.kwargs["ssl_options"],
            {"certfile": "/foo", "keyfile": "/bar"},
        )
        self.assertEqual(
            _CommandWebsocketClient.call_args.kwargs["ssl_options"],
            {"certfile": "/foo", "keyfile": "/bar"},
        )

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

    def test_web_socket_manager_joins_before_stop(self):
        """web_socket_manager joins a running thread before calling stop()."""
        import threading

        from pylxd import managers

        events = []
        entered = threading.Event()

        class FakeManager(threading.Thread):
            def __init__(self):
                super().__init__()
                self.running = False

            def run(self):
                self.running = True
                entered.set()
                while self.running:
                    threading.Event().wait(0.01)
                events.append("thread-exiting")

            def stop(self):
                events.append(("stop", self.is_alive()))

        fake_manager = FakeManager()
        with managers.web_socket_manager(fake_manager) as mgr:
            mgr.start()
            self.assertTrue(entered.wait(timeout=2))

        self.assertFalse(fake_manager.is_alive())
        self.assertEqual(["thread-exiting", ("stop", False)], events)

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
        history_start = len(self.requests_mock.request_history)

        an_migrated_instance = an_instance.migrate(client2)

        self.assertEqual("an-instance", an_migrated_instance.name)
        self.assertEqual(client2, an_migrated_instance.client)

        requests_made = [
            (r.method, r.url)
            for r in self.requests_mock.request_history[history_start:]
        ]
        dest_wait = ("GET", "http://pylxd2.test/1.0/operations/operation-abc/wait")
        src_delete = ("DELETE", "http://pylxd.test/1.0/instances/an-instance")
        self.assertIn(dest_wait, requests_made)
        self.assertIn(src_delete, requests_made)
        self.assertLess(requests_made.index(dest_wait), requests_made.index(src_delete))

    def test_migrate_does_not_delete_source_if_destination_fails(self):
        """Source instance is preserved when destination creation fails."""
        from pylxd.client import Client
        from pylxd.exceptions import LXDAPIException

        self.add_rule(
            {
                "json": {"type": "error", "error": "migration failed"},
                "status_code": 500,
                "method": "GET",
                "url": r"^http://pylxd2.test/1.0/operations/operation-abc/wait$",
            }
        )
        client2 = Client(endpoint="http://pylxd2.test")
        an_instance = models.Instance(self.client, name="an-instance")
        history_start = len(self.requests_mock.request_history)

        with self.assertRaises(LXDAPIException):
            an_instance.migrate(client2)

        requests_made = [
            (r.method, r.url)
            for r in self.requests_mock.request_history[history_start:]
        ]
        self.assertNotIn(
            ("DELETE", "http://pylxd.test/1.0/instances/an-instance"), requests_made
        )

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

    def test_generate_migration_data(self):
        """Migration data uses the LXD API keys ephemeral and profiles."""
        an_instance = models.Instance.get(self.client, name="an-instance")

        data = an_instance.generate_migration_data()

        self.assertEqual(an_instance.ephemeral, data["ephemeral"])
        self.assertEqual(an_instance.profiles, data["profiles"])
        self.assertNotIn("epehemeral", data)
        self.assertNotIn("default", data)

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

    @mock.patch("pylxd.client._APINode.put")
    def test_restore_snapshot(self, put):
        """Snapshots can be restored"""
        response = mock.MagicMock(status_code=202)
        put.return_value = response

        an_instance = models.Instance(self.client, name="an-instance")
        an_instance.restore_snapshot("thing")

        put.assert_called_once_with(json={"restore": "thing", "stateful": False})

    @mock.patch("pylxd.client._APINode.put")
    def test_restore_snapshot_stateful(self, put):
        """Snapshots can be restored"""
        response = mock.Mock()
        response.json.return_value = {}
        response.status_code = 202
        put.return_value = response

        an_instance = models.Instance(self.client, name="an-instance")
        an_instance.restore_snapshot("thing", stateful=True)

        put.assert_called_once_with(json={"restore": "thing", "stateful": True})

    def test_eq_same_name_no_project(self):
        """Two instances with same name and no project are equal."""
        a = models.Instance(self.client, name="an-instance")
        b = models.Instance(self.client, name="an-instance")
        self.assertEqual(a, b)

    def test_eq_same_name_same_project(self):
        """Two instances with same name and project are equal."""
        a = models.Instance(self.client, name="an-instance", project="myproj")
        b = models.Instance(self.client, name="an-instance", project="myproj")
        self.assertEqual(a, b)

    def test_eq_different_project(self):
        """Two instances with same name but different projects are not equal."""
        a = models.Instance(self.client, name="an-instance", project="p1")
        b = models.Instance(self.client, name="an-instance", project="p2")
        self.assertNotEqual(a, b)

    def test_eq_does_not_trigger_sync(self):
        """__eq__ must not call sync() when project is unset."""
        a = models.Instance(self.client, name="an-instance")
        b = models.Instance(self.client, name="an-instance")
        with mock.patch.object(models.Instance, "sync") as mock_sync:
            result = a == b
            self.assertTrue(result)
            mock_sync.assert_not_called()


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

    @mock.patch("pylxd.models.Instance.restore_snapshot")
    def test_restore_snapshot(self, restore_snapshot):
        """Snapshots can be restored from the snapshot object"""
        response = mock.MagicMock(status_code=202)
        restore_snapshot.return_value = response

        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot"
        )
        snapshot.restore(wait=True)
        restore_snapshot.assert_called_once_with("an-snapshot", True, stateful=False)

    @mock.patch("pylxd.models.Instance.restore_snapshot")
    def test_restore_snapshot_stateful(self, restore_snapshot):
        """Stateful Snapshots can be restored from the snapshot object"""
        response = mock.MagicMock(status_code=202)
        restore_snapshot.return_value = response

        snapshot = models.Snapshot(
            self.client, instance=self.instance, name="an-snapshot", stateful=True
        )
        snapshot.restore(wait=False)
        restore_snapshot.assert_called_once_with("an-snapshot", False, stateful=True)


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

        # Update host_info
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
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
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

    def test_recursive_put_symlinks(self):
        """File, broken, and directory symlinks are uploaded with X-LXD-type: symlink."""
        captured = {}

        def capture(request, context):
            path = request.qs["path"][0]
            captured[path] = {
                "headers": dict(request._request.headers),
                "body": request._request.body,
            }
            context.status_code = 200

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "subdir"))
            with open(os.path.join(tmpdir, "file1"), "w") as f:
                f.write("hello")
            os.symlink("file1", os.path.join(tmpdir, "file_link"))
            os.symlink("/nonexistent/target", os.path.join(tmpdir, "broken_link"))
            os.symlink("subdir", os.path.join(tmpdir, "dir_link"))

            self.add_rule(
                {
                    "text": capture,
                    "method": "POST",
                    "url": r"^http://pylxd.test/1.0/instances/an-instance/files\?path=",
                }
            )

            self.instance.files.recursive_put(tmpdir, "target")

        self.assertEqual(captured["target"]["headers"]["X-LXD-type"], "directory")
        self.assertEqual(
            captured["target/subdir"]["headers"]["X-LXD-type"], "directory"
        )
        self.assertEqual(captured["target/file1"]["body"], b"hello")
        self.assertEqual(
            captured["target/file_link"]["headers"]["X-LXD-type"], "symlink"
        )
        self.assertEqual(captured["target/file_link"]["body"], b"file1")
        self.assertEqual(
            captured["target/broken_link"]["headers"]["X-LXD-type"], "symlink"
        )
        self.assertEqual(captured["target/broken_link"]["body"], b"/nonexistent/target")
        self.assertEqual(
            captured["target/dir_link"]["headers"]["X-LXD-type"], "symlink"
        )
        self.assertEqual(captured["target/dir_link"]["body"], b"subdir")

    def test_get(self):
        """A file is retrieved from the instance."""
        data = self.instance.files.get("/tmp/getted")

        self.assertEqual(b"This is a getted file", data)

    def test_recursive_get(self):
        """A folder is retrieved recursively from the instance"""
        response = requests.models.Response()
        response.status_code = 200
        response.headers["X-LXD-type"] = "directory"
        response.headers["X-LXD-mode"] = "750"
        response._content = json.dumps({"metadata": ["file1", "subdir"]}).encode(
            "utf-8"
        )

        response1 = requests.models.Response()
        response1.status_code = 200
        response1.headers["X-LXD-type"] = "file"
        response1.headers["X-LXD-mode"] = "762"
        response1._content = b"This is file1"

        response_subdir = requests.models.Response()
        response_subdir.status_code = 200
        response_subdir.headers["X-LXD-type"] = "directory"
        response_subdir.headers["X-LXD-mode"] = "750"
        response_subdir._content = json.dumps({"metadata": ["file2"]}).encode("utf-8")

        response2 = requests.models.Response()
        response2.status_code = 200
        response2.headers["X-LXD-type"] = "file"
        response2.headers["X-LXD-mode"] = "744"
        response2._content = b"This is file2"

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch("pylxd.client._APINode.get") as get_mocked,
        ):
            get_mocked.side_effect = [response, response1, response_subdir, response2]
            dst = os.path.join(tmpdir, "out")
            os.makedirs(os.path.join(dst, "subdir"))

            self.instance.files.recursive_get("/tmp/getted", dst)

            with open(os.path.join(dst, "file1"), "rb") as f:
                self.assertEqual(b"This is file1", f.read())
            with open(os.path.join(dst, "subdir", "file2"), "rb") as f:
                self.assertEqual(b"This is file2", f.read())

    def test_recursive_get_sanitizes_traversal_entries(self):
        """Path traversal entries in directory listings are skipped."""
        response = requests.models.Response()
        response.status_code = 200
        response.headers["X-LXD-type"] = "directory"
        response.headers["X-LXD-mode"] = "750"
        response._content = json.dumps(
            {"metadata": ["safe_file", "..", ".", "/etc/passwd", "../evil"]}
        ).encode("utf-8")

        response1 = requests.models.Response()
        response1.status_code = 200
        response1.headers["X-LXD-type"] = "file"
        response1.headers["X-LXD-mode"] = "644"
        response1._content = b"safe content"

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch("pylxd.client._APINode.get") as get_mocked,
        ):
            get_mocked.side_effect = [response, response1]
            dst = os.path.join(tmpdir, "local")

            self.instance.files.recursive_get("/tmp/dir", dst)

            self.assertEqual(["safe_file"], os.listdir(dst))
            with open(os.path.join(dst, "safe_file"), "rb") as f:
                self.assertEqual(b"safe content", f.read())
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "evil")))

    def test_recursive_get_rejects_symlink_subdir(self):
        """Existing symlink subdirectories in the destination are not followed."""
        root_resp = requests.models.Response()
        root_resp.status_code = 200
        root_resp.headers["X-LXD-type"] = "directory"
        root_resp.headers["X-LXD-mode"] = "750"
        root_resp._content = json.dumps({"metadata": ["subdir"]}).encode("utf-8")

        sub_resp = requests.models.Response()
        sub_resp.status_code = 200
        sub_resp.headers["X-LXD-type"] = "directory"
        sub_resp.headers["X-LXD-mode"] = "750"
        sub_resp._content = json.dumps({"metadata": ["pwned"]}).encode("utf-8")

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch("pylxd.client._APINode.get") as get_mocked,
        ):
            outside = os.path.join(tmpdir, "outside")
            dst = os.path.join(tmpdir, "dst")
            os.makedirs(outside)
            os.makedirs(dst)
            os.symlink(outside, os.path.join(dst, "subdir"))

            get_mocked.side_effect = [root_resp, sub_resp]
            with self.assertRaises(OSError):
                self.instance.files.recursive_get("/tmp/dir", dst)
            self.assertEqual([], os.listdir(outside))

    def test_recursive_get_rejects_symlink_file(self):
        """Existing symlink files in the destination are not followed."""
        root_resp = requests.models.Response()
        root_resp.status_code = 200
        root_resp.headers["X-LXD-type"] = "directory"
        root_resp.headers["X-LXD-mode"] = "750"
        root_resp._content = json.dumps({"metadata": ["file1"]}).encode("utf-8")

        file_resp = requests.models.Response()
        file_resp.status_code = 200
        file_resp.headers["X-LXD-type"] = "file"
        file_resp.headers["X-LXD-mode"] = "644"
        file_resp._content = b"overwritten"

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch("pylxd.client._APINode.get") as get_mocked,
        ):
            outside_file = os.path.join(tmpdir, "outside.txt")
            with open(outside_file, "wb") as f:
                f.write(b"original")
            dst = os.path.join(tmpdir, "dst")
            os.makedirs(dst)
            os.symlink(outside_file, os.path.join(dst, "file1"))

            get_mocked.side_effect = [root_resp, file_resp]
            with self.assertRaises(OSError):
                self.instance.files.recursive_get("/tmp/dir", dst)
            with open(outside_file, "rb") as f:
                self.assertEqual(b"original", f.read())

    def test_recursive_get_rejects_symlink_root(self):
        """A symlinked top-level destination directory is rejected."""
        root_resp = requests.models.Response()
        root_resp.status_code = 200
        root_resp.headers["X-LXD-type"] = "directory"
        root_resp.headers["X-LXD-mode"] = "750"
        root_resp._content = json.dumps({"metadata": ["file1"]}).encode("utf-8")

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch("pylxd.client._APINode.get") as get_mocked,
        ):
            outside = os.path.join(tmpdir, "outside")
            os.makedirs(outside)
            dst_link = os.path.join(tmpdir, "dst_link")
            os.symlink(outside, dst_link)

            get_mocked.side_effect = [root_resp]
            with self.assertRaises(OSError):
                self.instance.files.recursive_get("/tmp/dir", dst_link + os.path.sep)
            self.assertEqual([], os.listdir(outside))

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


class TestSnapshotEquality(testing.PyLXDTestCase):
    """Tests for Snapshot equality semantics."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.instance = models.Instance.get(self.client, "an-instance")

    def test_equal_snapshots_same_name_and_instance(self):
        """Two snapshots with same name and instance are equal."""
        snap1 = models.Snapshot(self.client, name="snap1", instance=self.instance)
        snap2 = models.Snapshot(self.client, name="snap1", instance=self.instance)

        self.assertEqual(snap1, snap2)

    def test_unequal_snapshots_different_name(self):
        """Two snapshots with different names are not equal."""
        snap1 = models.Snapshot(self.client, name="snap1", instance=self.instance)
        snap2 = models.Snapshot(self.client, name="snap2", instance=self.instance)

        self.assertNotEqual(snap1, snap2)

    def test_unequal_snapshots_different_instance(self):
        """Two snapshots with different instances are not equal."""
        instance2 = models.Instance(self.client, name="another-instance")
        snap1 = models.Snapshot(self.client, name="snap1", instance=self.instance)
        snap2 = models.Snapshot(self.client, name="snap1", instance=instance2)

        self.assertNotEqual(snap1, snap2)

    def test_not_equal_to_unrelated_type(self):
        """Snapshot compared to other types returns NotImplemented."""
        snap = models.Snapshot(self.client, name="snap1", instance=self.instance)

        # Comparison with other types should return NotImplemented (which makes != True)
        self.assertNotEqual(snap, "string")
        self.assertNotEqual(snap, 123)
        self.assertNotEqual(snap, None)
